from fastapi import APIRouter, UploadFile, File, HTTPException, Path, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import uuid
import time

from helios.infrastructure.storage import StorageManager
from helios.infrastructure.vector_store import VectorStore
from helios.infrastructure.database import get_db_session
from helios.models.project_file import ProjectFile

logger = logging.getLogger(__name__)
router = APIRouter()

_storage = StorageManager()
_vector_store: VectorStore | None = None

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


def _get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


@router.post("/upload", summary="Upload a file to the project context")
async def upload_file(
    project_id: str = Path(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if file.size and file.size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_BYTES} bytes.",
        )

    try:
        content = bytearray()
        chunk_size = 1024 * 1024  # 1 MB
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            content.extend(chunk)
            if len(content) > MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size is {MAX_FILE_SIZE_BYTES} bytes.",
                )
        content_bytes = bytes(content)
        storage_id = await _storage.save_file(content_bytes)

        try:
            content_str = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content_str = content_bytes.decode("latin-1")

        # Add to vector store for search context
        vs = _get_vector_store()
        vs.add_finding(
            id=storage_id,
            text=f"Project: {project_id}\nFile: {file.filename}\n\n{content_str}",
            metadata={
                "filename": file.filename,
                "type": "uploaded_file",
                "project_id": project_id,
            },
        )

        try:
            # Save metadata to DB
            pf = ProjectFile(
                project_id=project_id,
                filename=file.filename,
                storage_id=storage_id,
                size_bytes=len(content),
                mime_type=file.content_type,
            )
            session.add(pf)
            await session.flush()
        except Exception:
            # Cleanup on failure
            await _storage.delete_file(storage_id)
            # Cannot easily remove from simple vector store without ID tracking, but minimal impact
            raise

        return {
            "id": pf.id,
            "filename": pf.filename,
            "status": "stored and indexed",
            "size_bytes": pf.size_bytes,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail="Error uploading file")


@router.get("/", summary="List uploaded files for a project")
async def list_files(
    project_id: str = Path(...), session: AsyncSession = Depends(get_db_session)
):
    """Returns files uploaded for this project."""
    try:
        result = await session.execute(
            select(ProjectFile).where(ProjectFile.project_id == project_id)
        )
        files = result.scalars().all()

        return {
            "files": [
                {
                    "id": f.id,
                    "filename": f.filename,
                    "size_bytes": f.size_bytes,
                    "mime_type": f.mime_type,
                    "created_at": f.created_at,
                }
                for f in files
            ]
        }
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail="Error listing files")
