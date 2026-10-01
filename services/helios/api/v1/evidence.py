from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Path
from fastapi.responses import FileResponse, Response
from helios.infrastructure.encryption import EncryptionManager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import logging
import os

from helios.infrastructure.database import get_db_session
from helios.core.evidence.manager import save_evidence_file
from helios.core.evidence.validator import verify_evidence
from helios.models.evidence import Evidence
from helios.models.finding import Finding
from helios.models.project import Project

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_project_or_404(project_id: str, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


async def get_or_create_stub_finding(
    project_id: uuid.UUID, db: AsyncSession
) -> uuid.UUID:
    """Return the first finding for this project, or create a stub if none exist."""
    result = await db.execute(
        select(Finding).where(Finding.project_id == project_id).limit(1)
    )
    finding = result.scalars().first()
    if not finding:
        finding = Finding(
            project_id=project_id,
            title="Uncategorised Evidence",
            description="Auto-created stub for evidence uploaded without a specific finding.",
            severity="info",
            confidence="low",
        )
        db.add(finding)
        await db.flush()
    return finding.id


@router.post("/upload", summary="Upload an evidence file")
async def upload_evidence(
    project_id: str = Path(...),
    file: UploadFile = File(...),
    description: str = Form(None),
    type: str = Form("screenshot"),
    finding_id: str = Form(None),
    db: AsyncSession = Depends(get_db_session),
):
    """Uploads evidence, calculates SHA-256 hash, saves to disk, creates DB record."""
    await get_project_or_404(project_id, db)

    try:
        if finding_id:
            fid = uuid.UUID(finding_id)
            result = await db.execute(
                select(Finding).where(
                    Finding.id == fid, Finding.project_id == project_id
                )
            )
            if not result.scalars().first():
                raise HTTPException(
                    status_code=404, detail="Finding not found in this project"
                )
        else:
            fid = await get_or_create_stub_finding(project_id, db)

        saved_info = await save_evidence_file(file)

        evidence = Evidence(
            finding_id=fid,
            type=type,
            description=description,
            file_path=saved_info["file_path"],
            file_hash=saved_info["file_hash"],
            metadata_json={"original_filename": saved_info["original_filename"]},
        )
        db.add(evidence)
        await db.commit()
        await db.refresh(evidence)

        # Log to the chain of custody ledger
        try:
            from helios.core.evidence.chain_of_custody import ChainOfCustody

            coc = ChainOfCustody()
            coc.log_evidence(
                evidence_id=str(evidence.id),
                action="UPLOAD",
                details={
                    "file_hash": evidence.file_hash,
                    "finding_id": str(fid),
                    "original_filename": saved_info["original_filename"],
                },
            )
        except Exception as e:
            logger.error(f"Chain of custody logging failed for {evidence.id}: {e}")
            await db.delete(evidence)
            await db.commit()
            if os.path.exists(saved_info["file_path"]):
                os.remove(saved_info["file_path"])
            raise HTTPException(
                status_code=500,
                detail="Failed to secure evidence in chain of custody ledger",
            )

        return {
            "status": "success",
            "data": {
                "id": str(evidence.id),
                "file_hash": evidence.file_hash,
                "file_path": evidence.file_path,
                "created_at": evidence.created_at,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload evidence: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail="Internal server error during evidence upload"
        )


@router.get("/", summary="List all evidence for a project")
async def list_evidence(
    project_id: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    await get_project_or_404(project_id, db)

    # Join through finding to scope by project
    result = await db.execute(
        select(Evidence)
        .join(Finding, Evidence.finding_id == Finding.id)
        .where(Finding.project_id == project_id)
        .order_by(Evidence.created_at.desc())
    )
    evidences = result.scalars().all()

    return {
        "status": "success",
        "data": [
            {
                "id": str(e.id),
                "finding_id": str(e.finding_id),
                "type": e.type,
                "description": e.description,
                "file_hash": e.file_hash,
                "original_filename": (e.metadata_json or {}).get(
                    "original_filename", ""
                ),
                "created_at": e.created_at,
            }
            for e in evidences
        ],
    }


@router.get("/{evidence_id}/download", summary="Download raw evidence file")
async def download_evidence(
    project_id: str = Path(...),
    evidence_id: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Evidence)
        .join(Finding, Evidence.finding_id == Finding.id)
        .where(Evidence.id == evidence_id, Finding.project_id == project_id)
    )
    evidence = result.scalars().first()

    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    if not evidence.file_path or not os.path.exists(evidence.file_path):
        raise HTTPException(status_code=404, detail="Evidence file not found on disk")

    try:
        with open(evidence.file_path, "rb") as f:
            encrypted_data = f.read()
        enc_manager = EncryptionManager()
        plaintext = enc_manager.decrypt_data(encrypted_data)
    except Exception as e:
        logger.error(f"Failed to decrypt evidence {evidence_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to read or decrypt evidence file"
        )

    filename = (evidence.metadata_json or {}).get("original_filename", "evidence.bin")

    return Response(
        content=plaintext,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{evidence_id}/verify", summary="Verify evidence chain-of-custody")
async def verify_evidence_integrity(
    project_id: str = Path(...),
    evidence_id: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Evidence)
        .join(Finding, Evidence.finding_id == Finding.id)
        .where(Evidence.id == evidence_id, Finding.project_id == project_id)
    )
    evidence = result.scalars().first()

    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    if not evidence.file_path:
        raise HTTPException(status_code=400, detail="Evidence has no file attached")

    verification = verify_evidence(evidence.file_path, evidence.file_hash)

    # Also verify the ledger integrity
    try:
        from helios.core.evidence.chain_of_custody import ChainOfCustody

        coc = ChainOfCustody(create_if_missing=False)
        ledger_valid = coc.verify_ledger()

        events = coc.get_evidence_events(evidence_id)
        has_upload = any(
            e.get("action") == "UPLOAD"
            and e.get("details", {}).get("file_hash") == evidence.file_hash
            for e in events
        )

        verification["ledger_valid"] = ledger_valid

        if not ledger_valid:
            verification["valid"] = False
            verification["error"] = (
                "Chain of custody ledger verification failed (corrupted or missing)."
            )
        elif not has_upload:
            verification["valid"] = False
            verification["error"] = (
                "Evidence was not found in the verified chain of custody ledger."
            )
    except Exception as e:
        logger.error(f"Ledger verification failed: {e}")
        verification["ledger_valid"] = False
        verification["valid"] = False
        verification["error"] = "Internal error verifying chain of custody."

    return {"status": "success", "data": verification}


@router.delete("/{evidence_id}", status_code=204, summary="Delete evidence")
async def delete_evidence(
    project_id: str = Path(...),
    evidence_id: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Evidence)
        .join(Finding, Evidence.finding_id == Finding.id)
        .where(Evidence.id == evidence_id, Finding.project_id == project_id)
    )
    evidence = result.scalars().first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    if evidence.file_path and os.path.exists(evidence.file_path):
        try:
            os.remove(evidence.file_path)
        except OSError as e:
            logger.warning(f"Could not delete evidence file: {e}")

    await db.delete(evidence)
    await db.commit()
    return None
