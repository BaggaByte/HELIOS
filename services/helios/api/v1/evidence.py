from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Path
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import logging
import os
import asyncio

from helios.infrastructure.database import get_db_session
from helios.core.evidence.manager import save_evidence_file
from helios.core.evidence.validator import verify_evidence
from helios.core.evidence.chain_of_custody import ChainOfCustody
from helios.models.evidence import Evidence
from helios.models.finding import Finding
from helios.models.project import Project

logger = logging.getLogger(__name__)
router = APIRouter()

# One ledger, alongside the evidence files themselves (see
# core/evidence/manager.py's EVIDENCE_DIR convention). ChainOfCustody does
# blocking file I/O, so every call below runs through asyncio.to_thread to
# avoid stalling the event loop.
_custody = ChainOfCustody(ledger_path=".helios_storage/evidence_ledger.jsonl")


async def get_project_or_404(project_id: str, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


async def get_or_create_stub_finding(project_id: uuid.UUID, db: AsyncSession) -> uuid.UUID:
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


@router.get("/custody/verify-ledger", summary="Verify the integrity of the evidence chain-of-custody ledger")
async def verify_custody_ledger():
    """
    Checks the hash chain of the append-only custody ledger (upload / verify /
    delete actions across all evidence). True means no entry has been altered
    or removed since it was written.
    """
    is_valid = await asyncio.to_thread(_custody.verify_ledger)
    return {"status": "success", "data": {"ledger_intact": is_valid}}


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
                select(Finding).where(Finding.id == fid, Finding.project_id == project_id)
            )
            if not result.scalars().first():
                raise HTTPException(status_code=404, detail="Finding not found in this project")
        else:
            fid = await get_or_create_stub_finding(project_id, db)

        saved_info = await asyncio.to_thread(save_evidence_file, file)

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

        await asyncio.to_thread(
            _custody.log_evidence,
            str(evidence.id),
            "UPLOAD",
            {
                "finding_id": str(fid),
                "file_hash": evidence.file_hash,
                "original_filename": saved_info["original_filename"],
            },
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
        raise HTTPException(status_code=500, detail=str(e))


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
                "original_filename": (e.metadata_json or {}).get("original_filename", ""),
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

    return FileResponse(
        evidence.file_path,
        filename=(evidence.metadata_json or {}).get("original_filename", "evidence.bin"),
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

    await asyncio.to_thread(
        _custody.log_evidence,
        str(evidence.id),
        "VERIFY",
        {"result": verification.get("status", verification.get("valid"))},
    )

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

    finding_id = evidence.finding_id  # capture before the row is gone / object expires
    await db.delete(evidence)
    await db.commit()

    await asyncio.to_thread(
        _custody.log_evidence,
        str(evidence_id),
        "DELETE",
        {"finding_id": str(finding_id)},
    )

    return None
