from fastapi import APIRouter
from pydantic import BaseModel
import psutil
import platform
from typing import Dict, Any

from helios.config import get_settings
from helios.infrastructure.openvino_runtime import OpenVINORuntime

router = APIRouter()
settings = get_settings()

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from helios.infrastructure.database import get_db_session
from helios.models.user import User
import logging


class SystemHealth(BaseModel):
    status: str
    version: str
    npu_available: bool
    setup_required: bool
    db_connected: bool
    ai_status: str


@router.get("/health", response_model=SystemHealth)
async def health_check(db: AsyncSession = Depends(get_db_session)):
    """Health check endpoint reflecting actual system readiness."""
    runtime = OpenVINORuntime()

    # Check DB
    db_ok = False
    setup_req = True
    try:
        # DB readiness check
        await db.execute(select(1))
        db_ok = True

        # Check if real users exist for setup requirement (ignore the migration placeholder)
        result = await db.execute(
            select(User).where(User.id.notin_(LEGACY_SYSTEM_USER_IDS)).limit(1)
        )
        setup_req = result.scalars().first() is None
    except Exception as e:
        logging.error(f"DB health check failed: {e}")

    ov_status_dict = runtime.get_status()
    ov_status = "ready" if ov_status_dict.get("loaded") else "uninitialized"
    overall_status = "healthy" if db_ok else "degraded"

    return SystemHealth(
        status=overall_status,
        version=settings.APP_VERSION,
        npu_available=runtime.is_npu_available(),
        setup_required=setup_req,
        db_connected=db_ok,
        ai_status=ov_status,
    )


from fastapi import APIRouter, Depends

from helios.api.v1.auth import get_current_user, LEGACY_SYSTEM_USER_IDS


@router.get("/status", dependencies=[Depends(get_current_user)])
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
            "percent": mem.percent,
        },
        "openvino": runtime.get_status(),
    }


@router.get("/settings", dependencies=[Depends(get_current_user)])
async def get_system_settings() -> Dict[str, Any]:
    """Return public system settings."""
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "debug_mode": settings.DEBUG,
        "ov_device": settings.OV_DEVICE,
        "ov_model_path": settings.OV_MODEL_PATH,
    }
