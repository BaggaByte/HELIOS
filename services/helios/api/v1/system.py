from fastapi import APIRouter
from pydantic import BaseModel
import psutil
import platform
from typing import Dict, Any

from helios.config import get_settings
from helios.infrastructure.openvino_runtime import OpenVINORuntime

router = APIRouter()
settings = get_settings()

class SystemHealth(BaseModel):
    status: str
    version: str
    npu_available: bool

@router.get("/health", response_model=SystemHealth)
async def health_check():
    """Basic health check endpoint."""
    runtime = OpenVINORuntime()
    return SystemHealth(
        status="healthy",
        version=settings.APP_VERSION,
        npu_available=runtime.is_npu_available()
    )

@router.get("/status")
async def system_status() -> Dict[str, Any]:
    """Detailed system status including memory, CPU, and NPU."""
    runtime = OpenVINORuntime()
    
    # Get basic memory info
    mem = psutil.virtual_memory()
    
    return {
        "os": platform.system(),
        "release": platform.release(),
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory": {
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent": mem.percent
        },
        "openvino": runtime.get_status()
    }

@router.get("/settings")
async def get_system_settings() -> Dict[str, Any]:
    """Return public system settings."""
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "debug_mode": settings.DEBUG,
        "ov_device": settings.OV_DEVICE,
        "ov_model_path": settings.OV_MODEL_PATH,
    }
