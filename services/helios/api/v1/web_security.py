from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import uuid

from helios.infrastructure.database import get_db_session
from helios.models.project import Project
from helios.models.finding import Finding
from helios.core.web_security.parsers.zap import parse_zap_xml
from helios.core.knowledge_graph.builder import sync_finding

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_project_or_404(project_id: str, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


@router.post("/ingest/zap", summary="Import an OWASP ZAP XML report")
async def ingest_zap(
    project_id: str = Path(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
):
    if not (file.filename or "").endswith(".xml"):
        raise HTTPException(status_code=400, detail="Must be an XML file")

    project = await get_project_or_404(project_id, db)
    content = await file.read()

    try:
        findings_data = parse_zap_xml(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse ZAP XML: {e}")

    try:
        new_findings_count = 0
        touched_findings = []
        for f_data in findings_data:
            result = await db.execute(
                select(Finding).where(
                    Finding.project_id == project.id,
                    Finding.title == f_data["title"],
                )
            )
            existing = result.scalars().first()

            full_desc = f_data["description"]
            if f_data.get("target_host"):
                full_desc = (
                    f"**Target**: {f_data['target_host']}:{f_data.get('target_port', '')}\n\n"
                    + full_desc
                )

            if not existing:
                finding = Finding(
                    project_id=project.id,
                    title=f_data["title"],
                    description=full_desc,
                    severity=f_data["severity"],
                    confidence=f_data["confidence"],
                    status="observed",
                    cwe_id=f_data.get("cwe_id"),
                    remediation=f_data.get("remediation"),
                    impact=f_data.get("impact"),
                    references_json=f_data.get("references_json", []),
                )
                db.add(finding)
                touched_findings.append(finding)
                new_findings_count += 1
            else:
                existing.description = full_desc
                existing.severity = f_data["severity"]
                existing.confidence = f_data["confidence"]
                existing.remediation = f_data.get("remediation")
                existing.impact = f_data.get("impact")
                existing.references_json = f_data.get("references_json", [])
                touched_findings.append(existing)

        await db.commit()

        # Best-effort knowledge graph sync — a sync problem should never
        # take down a successful finding import.
        try:
            for finding in touched_findings:
                await sync_finding(db, project.id, finding)
            await db.commit()
        except Exception:
            logger.exception("Knowledge graph sync failed after ZAP ingest (non-fatal)")
            await db.rollback()

        return {
            "status": "success",
            "message": f"Ingested {new_findings_count} new findings from ZAP scan.",
        }
    except Exception as e:
        logger.error(f"Failed to ingest ZAP data: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/findings", summary="List all web security findings for a project")
async def get_findings(
    project_id: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    await get_project_or_404(project_id, db)

    result = await db.execute(
        select(Finding)
        .where(Finding.project_id == project_id)
        .order_by(Finding.created_at.desc())
    )
    findings = result.scalars().all()

    return [
        {
            "id": str(f.id),
            "title": f.title,
            "description": f.description,
            "severity": f.severity,
            "confidence": f.confidence,
            "status": f.status,
            "cwe_id": f.cwe_id,
            "remediation": f.remediation,
            "impact": f.impact,
            "references": f.references_json,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in findings
    ]


@router.delete("/findings/{finding_id}", status_code=204, summary="Delete a finding")
async def delete_finding(
    project_id: str = Path(...),
    finding_id: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Finding).where(
            Finding.id == finding_id,
            Finding.project_id == project_id,
        )
    )
    finding = result.scalars().first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    await db.delete(finding)
    await db.commit()
    return None
