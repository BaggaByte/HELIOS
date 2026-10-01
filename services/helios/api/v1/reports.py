from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import logging

from helios.infrastructure.database import get_db_session
from helios.core.reports.generator import generate_report
from helios.models.project import Project

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_project_or_404(project_id: str, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


@router.post("/generate", summary="Generate a Markdown report for the project")
async def create_report(
    project_id: str = Path(...),
    include_ai_summary: bool = False,
    db: AsyncSession = Depends(get_db_session),
):
    await get_project_or_404(project_id, db)

    try:
        markdown_content = await generate_report(db, project_id, include_ai_summary)
        return {
            "status": "success",
            "data": {"markdown": markdown_content},
        }
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/generate/download",
    response_class=PlainTextResponse,
    summary="Download report as plain text",
)
async def download_report(
    project_id: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    await get_project_or_404(project_id, db)

    try:
        markdown_content = await generate_report(
            db, project_id, include_ai_summary=False
        )
        return PlainTextResponse(content=markdown_content, media_type="text/markdown")
    except Exception as e:
        logger.error(f"Failed to download report: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
