from fastapi import APIRouter, Query, HTTPException, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional
import uuid

from helios.infrastructure.database import get_db_session
from helios.models.project import Project
from helios.models.finding import Finding
from helios.models.host import Host

router = APIRouter()


async def get_project_or_404(project_id: str, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("", summary="Full-text search across project findings and hosts")
async def global_search(
    project_id: str = Path(...),
    q: str = Query(..., min_length=2, description="Search query"),
    type: Optional[str] = Query(None, description="Filter: finding | host"),
    db: AsyncSession = Depends(get_db_session),
):
    await get_project_or_404(project_id, db)

    results = []

    # Search findings
    if not type or type == "finding":
        stmt = (
            select(Finding)
            .where(
                Finding.project_id == project_id,
                or_(
                    Finding.title.ilike(f"%{q}%"),
                    Finding.description.ilike(f"%{q}%"),
                ),
            )
            .limit(20)
        )
        f_result = await db.execute(stmt)
        for f in f_result.scalars().all():
            results.append(
                {
                    "id": str(f.id),
                    "type": "finding",
                    "title": f.title,
                    "snippet": (f.description or "")[:200],
                    "severity": f.severity,
                    "url": f"/projects/{project_id}/findings/{f.id}",
                }
            )

    # Search hosts
    if not type or type == "host":
        stmt = (
            select(Host)
            .where(
                Host.project_id == project_id,
                or_(
                    Host.ip.ilike(f"%{q}%"),
                    Host.hostname.ilike(f"%{q}%"),
                    Host.os.ilike(f"%{q}%"),
                ),
            )
            .limit(20)
        )
        h_result = await db.execute(stmt)
        for h in h_result.scalars().all():
            results.append(
                {
                    "id": str(h.id),
                    "type": "host",
                    "title": h.hostname or h.ip,
                    "snippet": f"IP: {h.ip}, OS: {h.os or 'unknown'}",
                    "url": f"/projects/{project_id}/recon/hosts/{h.id}",
                }
            )

    return {
        "query": q,
        "project_id": str(project_id),
        "results": results,
        "total": len(results),
    }
