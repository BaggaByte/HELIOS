import logging

from fastapi import APIRouter, File, HTTPException, Path, UploadFile
from pydantic import BaseModel

from helios.core.js_intel.extractor import analyze_js

logger = logging.getLogger(__name__)
router = APIRouter()


class AnalyzeRequest(BaseModel):
    code: str


@router.post(
    "/analyze", summary="Analyse raw JavaScript for endpoints, tokens, and secrets"
)
async def analyze_js_endpoint(
    project_id: str = Path(...),
    request: AnalyzeRequest,
):
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="JS code cannot be empty")
    try:
        return analyze_js(request.code)
    except Exception as e:
        logger.error(f"JS analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analyze-file", summary="Analyse an uploaded JavaScript file")
async def analyze_js_file(
    project_id: str = Path(...),
    file: UploadFile = File(...),
):
    if not (file.filename or "").endswith(".js"):
        raise HTTPException(
            status_code=400, detail="File must be a JavaScript (.js) file"
        )
    try:
        content = await file.read()
        code_str = content.decode("utf-8", errors="ignore")
        return analyze_js(code_str)
    except Exception as e:
        logger.error(f"JS file analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
