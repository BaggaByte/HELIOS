from fastapi import APIRouter, HTTPException, Depends, Path, status
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from datetime import datetime
import uuid

from helios.infrastructure.database import get_db_session
from helios.models.project import Project
from helios.utils.validators import is_valid_cidr, is_valid_domain, is_valid_ip

router = APIRouter()


# ──────────────────────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    scope: str
    out_of_scope: Optional[str] = None

    @field_validator("name", "scope")
    @classmethod
    def require_nonempty_value(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty")
        return value

    @field_validator("scope", "out_of_scope")
    @classmethod
    def validate_scope_entries(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not value.strip():
            return None if value is None else ""
        entries = [entry.strip() for entry in value.replace(";", ",").replace("\n", ",").split(",") if entry.strip()]
        invalid = [entry for entry in entries if not (is_valid_ip(entry) or is_valid_cidr(entry) or is_valid_domain(entry))]
        if invalid:
            raise ValueError(f"Scope entries must be IP addresses, CIDRs, or domains: {', '.join(invalid)}")
        return ", ".join(entries)


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ProjectUpdateScope(BaseModel):
    scope: str
    out_of_scope: Optional[str] = None

    @field_validator("scope", "out_of_scope")
    @classmethod
    def validate_scope_entries(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not value.strip():
            return None if value is None else ""
        entries = [entry.strip() for entry in value.replace(";", ",").replace("\n", ",").split(",") if entry.strip()]
        invalid = [entry for entry in entries if not (is_valid_ip(entry) or is_valid_cidr(entry) or is_valid_domain(entry))]
        if invalid:
            raise ValueError(f"Scope entries must be IP addresses, CIDRs, or domains: {', '.join(invalid)}")
        return ", ".join(entries)


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    scope: str
    out_of_scope: Optional[str]
    status: str
    created_at: str

    @classmethod
    def from_orm(cls, p: Project) -> "ProjectResponse":
        return cls(
            id=str(p.id),
            name=p.name,
            description=p.description,
            scope=p.scope,
            out_of_scope=p.out_of_scope,
            status=p.status,
            created_at=p.created_at.isoformat() if p.created_at else datetime.utcnow().isoformat(),
        )


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────

from helios.api.v1.auth import get_current_user
from helios.models.user import User

@router.get("", response_model=List[ProjectResponse], summary="List all projects")
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    result = await db.execute(
        select(Project)
        .where(Project.created_by == current_user.id)
        .order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return [ProjectResponse.from_orm(p) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, summary="Create a project")
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    new_project = Project(
        name=project.name,
        description=project.description,
        scope=project.scope,
        out_of_scope=project.out_of_scope,
        status="active",
        created_by=current_user.id
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    return ProjectResponse.from_orm(new_project)


@router.get("/{project_id}", response_model=ProjectResponse, summary="Get a project")
async def get_project(
    project_id: str = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project or project.created_by != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.from_orm(project)


@router.put("/{project_id}", response_model=ProjectResponse, summary="Update a project")
async def update_project(
    body: ProjectUpdate,
    project_id: str = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project or project.created_by != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    if body.name is not None:
        project.name = body.name
    if body.description is not None:
        project.description = body.description
    if body.status is not None:
        project.status = body.status

    await db.commit()
    await db.refresh(project)
    return ProjectResponse.from_orm(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a project")
async def delete_project(
    project_id: str = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project or project.created_by != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    # Mark as deleting
    project.status = "deleting"
    await db.commit()
    await db.refresh(project)

    # Clean up physical files and vector store entries before deleting DB rows
    import os
    import logging
    from helios.models.evidence import Evidence
    from helios.models.finding import Finding
    from helios.models.project_file import ProjectFile
    from helios.infrastructure.storage import StorageManager
    from helios.infrastructure.vector_store import VectorStore

    cleanup_logger = logging.getLogger(__name__)
    storage = StorageManager()
    
    try:
        vector_store = VectorStore()
    except Exception as e:
        cleanup_logger.error(f"Failed to initialize VectorStore for cleanup: {e}")
        raise HTTPException(status_code=500, detail="Cannot connect to vector store to purge project data. Retry later.")

    # 1. Evidence files (linked through Finding)
    ev_result = await db.execute(
        select(Evidence).join(Finding, Evidence.finding_id == Finding.id)
        .where(Finding.project_id == project_id)
    )
    for ev in ev_result.scalars().all():
        if ev.file_path and os.path.exists(ev.file_path):
            try:
                os.remove(ev.file_path)
            except OSError as e:
                cleanup_logger.error(f"Could not delete evidence file {ev.file_path}: {e}")
                raise HTTPException(status_code=500, detail="Failed to delete an evidence file from disk. Retry later.")

    # 2. Project files and their vector entries
    pf_result = await db.execute(
        select(ProjectFile).where(ProjectFile.project_id == project_id)
    )
    for pf in pf_result.scalars().all():
        try:
            await storage.delete_file(pf.storage_id)
        except Exception as e:
            cleanup_logger.error(f"Could not delete project file {pf.storage_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete a project file from storage. Retry later.")
            
        try:
            vector_store.docs_collection.delete(where={"project_id": project_id})
        except Exception as e:
            cleanup_logger.error(f"Could not delete vector docs for project {project_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to purge project embeddings. Retry later.")
            
    # 3. Finding vector entries
    try:
        vector_store.findings_collection.delete(where={"project_id": project_id})
    except Exception as e:
        cleanup_logger.error(f"Could not delete vector findings for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to purge finding embeddings. Retry later.")

    # Delete project row (which cascades to Findings, Evidence, ProjectFiles if configured)
    await db.delete(project)
    await db.commit()
    return None


@router.post("/{project_id}/scope", response_model=ProjectResponse, summary="Update project scope")
async def update_project_scope(
    scope_update: ProjectUpdateScope,
    project_id: str = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project or project.created_by != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    project.scope = scope_update.scope
    if scope_update.out_of_scope is not None:
        project.out_of_scope = scope_update.out_of_scope

    await db.commit()
    await db.refresh(project)
    return ProjectResponse.from_orm(project)
