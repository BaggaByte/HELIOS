from fastapi import APIRouter, HTTPException, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid
import logging
from datetime import datetime

from helios.infrastructure.database import get_db_session
from helios.models.project import Project
from helios.models.finding import Finding
from helios.core.source_code.analyzers.secret_detector import scan_text
from helios.core.knowledge_graph.builder import sync_finding

logger = logging.getLogger(__name__)
router = APIRouter()


class AnalyzeRequest(BaseModel):
    code: str
    language_hint: str
    filename: str


async def get_project_or_404(project_id: str, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


@router.post("/analyze", summary="Analyse source code for secrets and vulnerabilities")
async def analyze_source_code(
    project_id: str = Path(...),
    request: AnalyzeRequest = ...,
    db: AsyncSession = Depends(get_db_session),
):
    project = await get_project_or_404(project_id, db)

    try:
        findings_data = scan_text(request.code, request.filename)

        security_findings = []
        touched_findings = []
        for f_data in findings_data:
            # Avoid duplicates within the same project scan
            res = await db.execute(
                select(Finding).where(
                    Finding.project_id == project.id,
                    Finding.title == f_data["title"],
                )
            )
            if not res.scalars().first():
                finding = Finding(
                    project_id=project.id,
                    title=f_data["title"],
                    description=f_data["description"],
                    severity=f_data["severity"],
                    confidence=f_data["confidence"],
                    status="observed",
                    cwe_id=f_data.get("cwe_id"),
                    impact=f_data.get("impact"),
                    remediation=(
                        "Remove the hardcoded secret and use environment variables "
                        "or a secure vault (e.g. HashiCorp Vault, AWS Secrets Manager)."
                    ),
                )
                db.add(finding)
                touched_findings.append(finding)

            security_findings.append({
                "type": "VULNERABILITY",
                "severity": f_data["severity"].upper(),
                "line": f_data.get("line_number"),
                "description": f_data["title"],
            })

        await db.commit()

        try:
            for finding in touched_findings:
                await sync_finding(db, project.id, finding)
            await db.commit()
        except Exception:
            logger.exception("Knowledge graph sync failed after source scan (non-fatal)")
            await db.rollback()

        return {
            "id": str(uuid.uuid4()),
            "filename": request.filename,
            "language": request.language_hint,
            "security_findings": security_findings,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to analyse source code: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/findings", summary="List all source-code findings for a project")
async def get_findings(
    project_id: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    await get_project_or_404(project_id, db)

    result = await db.execute(
        select(Finding).where(Finding.project_id == project_id).order_by(Finding.created_at.desc())
    )
    findings = result.scalars().all()

    return [
        {
            "id": str(f.id),
            "title": f.title,
            "severity": f.severity,
            "confidence": f.confidence,
            "status": f.status,
            "cwe_id": f.cwe_id,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in findings
    ]
