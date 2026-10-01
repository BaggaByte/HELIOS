import asyncio
import time
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helios.config import get_settings
from helios.infrastructure.database import get_db_session
from helios.models.project import Project
from helios.models.user import User

router = APIRouter()
_setup_lock = asyncio.Lock()
LEGACY_SYSTEM_USER_IDS = (
    "00000000-0000-0000-0000-000000000000",
    "legacy_migration_placeholder",
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
ph = PasswordHasher()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


def get_password_hash(password: str) -> str:
    return ph.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    settings = get_settings()
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=1440)  # 24h
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") == "ws-ticket":
            raise credentials_exception
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


async def require_project_access(
    project_id: str = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Project:
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.created_by != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this project"
        )

    return project


failed_attempts: dict[str, list[float]] = defaultdict(list)


@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db_session),
):
    now = time.time()
    user_key = form_data.username

    # Clean up old attempts (older than 5 minutes)
    attempts = [t for t in failed_attempts[user_key] if now - t < 300]
    failed_attempts[user_key] = attempts

    if len(attempts) >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please wait 5 minutes.",
        )

    stmt = select(User).where(User.username == form_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.password_hash):
        failed_attempts[user_key].append(now)
        await asyncio.sleep(1)  # Constant delay
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Reset attempts on success
    if user_key in failed_attempts:
        del failed_attempts[user_key]

    access_token_expires = timedelta(minutes=1440)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


class SetupRequest(BaseModel):
    username: str = "admin"
    password: str
    scope: str


@router.post("/setup")
async def initial_setup(req: SetupRequest, db: AsyncSession = Depends(get_db_session)):
    """First-run admin setup and legacy project claiming."""
    # Basic validation
    if len(req.username) < 3:
        raise HTTPException(
            status_code=400, detail="Username must be at least 3 characters"
        )
    if len(req.password) < 8:
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters"
        )

    from helios.api.v1.projects import ProjectCreate

    try:
        scope = ProjectCreate.validate_scope_entries(req.scope)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not scope:
        raise HTTPException(
            status_code=400,
            detail="An explicit, restricted network scope must be provided.",
        )

    async with _setup_lock:
        # Check for real users (ignore the migration placeholder)
        result = await db.execute(
            select(User).where(User.id.notin_(LEGACY_SYSTEM_USER_IDS)).limit(1)
        )
        if result.scalars().first() is not None:
            raise HTTPException(status_code=400, detail="Setup already complete")

        # 1. Create admin user (race-safe via unique constraint on username)
        from sqlalchemy.exc import IntegrityError

        user = User(
            username=req.username,
            password_hash=get_password_hash(req.password),
            role="admin",
        )
        db.add(user)
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=400, detail="Setup already complete or username taken"
            )

        # 2. Claim legacy projects
        proj_result = await db.execute(
            select(Project).where(Project.created_by.in_(LEGACY_SYSTEM_USER_IDS))
        )
        orphaned = proj_result.scalars().all()
        for p in orphaned:
            p.created_by = user.id

        # 3. Create default project if none exist
        def_proj_result = await db.execute(select(Project).limit(1))
        if not def_proj_result.scalars().first():
            default_proj = Project(
                id="default-project-id",
                name="Default Workspace",
                scope=scope,
                status="active",
                created_by=user.id,
            )
            db.add(default_proj)

        await db.commit()

    access_token = create_access_token(data={"sub": user.username})
    return {"status": "success", "access_token": access_token}


@router.post("/ws-ticket")
async def create_ws_ticket(current_user: Annotated[User, Depends(get_current_user)]):
    ticket_expires = timedelta(seconds=30)
    ticket = create_access_token(
        data={"sub": current_user.username, "type": "ws-ticket"},
        expires_delta=ticket_expires,
    )
    return {"ticket": ticket}


@router.get("/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
    }
