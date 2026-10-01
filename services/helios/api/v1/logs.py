from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Depends,
    Form,
    Path,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
import logging
from typing import Optional

from helios.infrastructure.database import get_db_session
from helios.models.project import Project
from helios.models.log_event import LogEvent
from helios.core.logs.timeline_builder import parse_log_file

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_project_or_404(project_id, db: AsyncSession) -> Project:
    import uuid

    pid = project_id
    result = await db.execute(select(Project).where(Project.id == pid))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


@router.post("/ingest", summary="Ingest and parse a log file into the timeline")
async def ingest_logs(
    project_id: str = Path(...),
    log_type: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
):
    project = await get_project_or_404(project_id, db)

    content_bytes = await file.read()
    try:
        content = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content = content_bytes.decode("latin-1")

    try:
        events_data = parse_log_file(content, log_type)
    except Exception as e:
        logger.error(f"Failed to parse log file: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse log: {e}")

    try:
        new_events = []
        for e_data in events_data:
            event = LogEvent(
                project_id=project.id,
                timestamp=e_data["timestamp"],
                source=e_data["source"],
                event_type=e_data["event_type"],
                severity=e_data["severity"],
                message=e_data["message"],
                source_ip=e_data.get("source_ip"),
                dest_ip=e_data.get("dest_ip"),
                metadata_=e_data.get("metadata", {}),
            )
            db.add(event)
            new_events.append(event)

        await db.commit()

        return {
            "status": "success",
            "message": f"Ingested {len(new_events)} log events.",
            "event_count": len(new_events),
        }
    except Exception as e:
        logger.error(f"Failed to save log events: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/timeline", summary="Retrieve log events in chronological order")
async def get_timeline(
    project_id: str = Path(...),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    severity: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
):
    project = await get_project_or_404(project_id, db)

    query = select(LogEvent).where(LogEvent.project_id == project.id)
    if severity:
        query = query.where(LogEvent.severity == severity)
    if source:
        query = query.where(LogEvent.source == source)

    # Total count
    count_stmt = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    query = (
        query.order_by(desc(LogEvent.timestamp)).offset((page - 1) * limit).limit(limit)
    )
    events_result = await db.execute(query)
    events = events_result.scalars().all()

    return {
        "events": [
            {
                "id": str(e.id),
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "source": e.source,
                "event_type": e.event_type,
                "severity": e.severity,
                "message": e.message,
                "source_ip": e.source_ip,
                "dest_ip": e.dest_ip,
                "metadata": e.metadata_,
            }
            for e in events
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }
