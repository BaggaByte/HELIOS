from fastapi import APIRouter, UploadFile, File, HTTPException, Path
from fastapi.responses import FileResponse
import logging
import os
import uuid

from helios.infrastructure.storage import StorageManager
from helios.infrastructure.vector_store import VectorStore

logger = logging.getLogger(__name__)
router = APIRouter()

_storage = StorageManager()
_vector_store: VectorStore | None = None


def _get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


@router.post("/upload", summary="Upload a file to the project context")
async def upload_file(
    project_id: str = Path(...),
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    try:
        content = await file.read()
        saved_path = await _storage.save_file(file.filename, content)

        try:
            content_str = content.decode("utf-8")
        except UnicodeDecodeError:
            content_str = content.decode("latin-1")

        vs = _get_vector_store()
        doc_id = str(uuid.uuid4())
        vs.add_finding(
            id=doc_id,
            text=f"Project: {project_id}\nFile: {file.filename}\n\n{content_str}",
            metadata={"filename": file.filename, "type": "uploaded_file", "project_id": project_id},
        )

        return {
            "id": doc_id,
            "filename": file.filename,
            "status": "stored and indexed",
            "size_bytes": len(content),
            "path": saved_path,
        }
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", summary="List uploaded files for a project")
async def list_files(project_id: str = Path(...)):
    """Returns files indexed in the vector store for this project."""
    try:
        vs = _get_vector_store()
        results = vs.search_findings(query=f"project:{project_id}", n_results=100)
        files = []
        if results and results.get("metadatas"):
            for meta in results["metadatas"][0]:
                if meta.get("project_id") == project_id and meta.get("type") == "uploaded_file":
                    files.append({"filename": meta.get("filename"), "project_id": project_id})
        return {"files": files}
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))
