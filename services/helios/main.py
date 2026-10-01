import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from helios.config import get_settings
from helios.api.v1 import (
    chat, files, recon, web_security, source_code,
    logs, malware, knowledge_graph, evidence,
    reports, js_intel, system, projects, search,
)
from helios.core.chat.engine import ChatEngine
from helios.infrastructure.database import init_db

settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──────────────────────────────────────────────────────────────
    logger.info("🚀 Starting HELIOS Backend...")
    await init_db()
    logger.info("📦 Database initialised.")

    app.state.chat_engine = ChatEngine()
    status = app.state.chat_engine.get_status()
    logger.info(f"✅ AI Runtime Status: {status}")

    yield

    # ── SHUTDOWN ─────────────────────────────────────────────────────────────
    logger.info("🛑 Shutting down HELIOS Backend...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="HELIOS Offensive Security AI Copilot API",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

cors_origins = settings.CORS_ORIGINS

from starlette.middleware.base import BaseHTTPMiddleware

class ContentLengthLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length is not None:
            if int(content_length) > settings.MAX_UPLOAD_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"Payload too large. Maximum allowed size is {settings.MAX_UPLOAD_SIZE} bytes."}
                )
        return await call_next(request)

app.add_middleware(ContentLengthLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "error": str(exc) if settings.DEBUG else "An unexpected error occurred.",
        },
    )


from fastapi import Depends
from helios.api.v1.auth import router as auth_router, get_current_user, require_project_access

# ── Non-project-scoped routes ────────────────────────────────────────────────
app.include_router(auth_router,     prefix="/api/v1/auth",     tags=["auth"])
app.include_router(system.router,   prefix="/api/v1/system",   tags=["system"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"], dependencies=[Depends(get_current_user)])

# Chat has its own WebSocket endpoint — kept flat so ws:// URLs stay simple
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])

# ── Project-scoped routes  (/api/v1/projects/{project_id}/...) ───────────────
_P = "/api/v1/projects/{project_id}"
_D = [Depends(require_project_access)]

app.include_router(recon.router,           prefix=f"{_P}/recon",           tags=["recon"], dependencies=_D)
app.include_router(web_security.router,    prefix=f"{_P}/web-security",    tags=["web-security"], dependencies=_D)
app.include_router(source_code.router,     prefix=f"{_P}/source-code",     tags=["source-code"], dependencies=_D)
app.include_router(logs.router,            prefix=f"{_P}/logs",            tags=["logs"], dependencies=_D)
app.include_router(malware.router,         prefix=f"{_P}/malware",         tags=["malware"], dependencies=_D)
app.include_router(knowledge_graph.router, prefix=f"{_P}/graph",           tags=["knowledge-graph"], dependencies=_D)
app.include_router(evidence.router,        prefix=f"{_P}/evidence",        tags=["evidence"], dependencies=_D)
app.include_router(reports.router,         prefix=f"{_P}/reports",         tags=["reports"], dependencies=_D)
app.include_router(js_intel.router,        prefix=f"{_P}/js-intel",        tags=["js-intel"], dependencies=_D)
app.include_router(files.router,           prefix=f"{_P}/files",           tags=["files"], dependencies=_D)
app.include_router(search.router,          prefix=f"{_P}/search",          tags=["search"], dependencies=_D)

if __name__ == "__main__":
    import uvicorn
    import sys
    
    # Check if running as packaged executable
    if getattr(sys, 'frozen', False):
        logger.info("Starting bundled FastAPI app...")
        uvicorn.run(app, host="127.0.0.1", port=8000)
    else:
        logger.info("Running from source. Use 'uvicorn helios.main:app' or 'uv run fastapi dev helios/main.py' to start.")
