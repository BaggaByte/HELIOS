"""
Shared pytest fixtures for the HELIOS test suite.

Environment variables are patched via a pytest plugin (conftest-level) BEFORE
any helios module is imported. The key is that os.environ must be set before
pydantic-settings reads the .env file.

Uses an in-memory SQLite database so tests are:
  - Isolated (fresh DB per test function)
  - Fast (no disk I/O)
  - Side-effect-free (never touch helios.db)
"""

import os

# ── MUST happen before any helios import ────────────────────────────────────
# Override .env values with test-safe defaults
os.environ["SECRET_KEY"] = "test-secret-key-that-is-definitely-32-chars-long!!"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DEBUG"] = "True"
os.environ["OV_MODEL_PATH"] = "../models/phi4_mini_int4_ov"
os.environ["OV_DEVICE"] = "CPU"
os.environ["CHROMA_PERSIST_DIR"] = "/tmp/helios_test_chroma"
os.environ["CORS_ORIGINS"] = '["http://localhost:5173","tauri://localhost"]'
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["CELERY_BROKER_URL"] = "redis://localhost:6379/1"

# ── Now safe to import helios ────────────────────────────────────────────────
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Invalidate the lru_cache so it re-reads our patched env vars
from helios.config import get_settings

get_settings.cache_clear()

from helios.main import app
from helios.models.base import Base
from helios.models import (  # noqa: F401 — register metadata
    User,
    Project,
    Host,
    Service,
    Finding,
    Evidence,
    Target,
    Note,
    KnowledgeNode,
    KnowledgeEdge,
    LogEvent,
)
from helios.infrastructure.database import get_db_session


# ── Event loop ────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── In-memory database engine ─────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    session_factory = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


# ── HTTP test client ──────────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="function")
async def client(db_session, test_user):
    """
    AsyncClient wired to the FastAPI app with:
    - Test DB session injected via dependency override
    - Chat engine stubbed to avoid loading the LLM
    - JWT authentication injected
    """
    from helios.api.v1.auth import create_access_token

    async def _override_db():
        yield db_session

    app.dependency_overrides[get_db_session] = _override_db

    # Stub the chat engine so startup doesn't try to load a 2 GB model
    class _MockChatEngine:
        def get_status(self):
            return {"engine": "mock", "runtime_status": {"loaded": False}}

    app.state.chat_engine = _MockChatEngine()

    token = create_access_token(data={"sub": test_user.username})

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Shared fixtures ───────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create and persist a test user."""
    from helios.models.user import User as UserModel

    u = UserModel(username="test_user", password_hash="hash")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def project(db_session, test_user):
    """Create and persist a test project, return the ORM project object."""
    from helios.models.project import Project as ProjectModel

    p = ProjectModel(
        name="Test Project",
        description="Automated test project",
        scope="10.0.0.0/8",
        created_by=test_user.id,
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    return p
