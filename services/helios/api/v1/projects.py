from fastapi import APIRouter, HTTPException, Depends, Path, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from datetime import datetime
import uuid

from helios.infrastructure.database import get_db_session
from helios.models.project import Project

router = APIRouter()


# ──────────────────────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    scope: str
    out_of_scope: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ProjectUpdateScope(BaseModel):
    scope: str
    out_of_scope: Optional[str] = None


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

@router.get("", response_model=List[ProjectResponse], summary="List all projects")
async def list_projects(db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    projects = result.scalars().all()
    return [ProjectResponse.from_orm(p) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, summary="Create a project")
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db_session),
):
    new_project = Project(
        name=project.name,
        description=project.description,
        scope=project.scope,
        out_of_scope=project.out_of_scope,
        status="active",
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    return ProjectResponse.from_orm(new_project)


@router.get("/{project_id}", response_model=ProjectResponse, summary="Get a project")
async def get_project(
    project_id: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.from_orm(project)


@router.put("/{project_id}", response_model=ProjectResponse, summary="Update a project")
async def update_project(
    project_id: str = Path(...),
    body: ProjectUpdate = ...,
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
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
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()
    return None


@router.post("/{project_id}/scope", response_model=ProjectResponse, summary="Update project scope")
async def update_project_scope(
    project_id: str = Path(...),
    scope_update: ProjectUpdateScope = ...,
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.scope = scope_update.scope
    if scope_update.out_of_scope is not None:
        project.out_of_scope = scope_update.out_of_scope

    await db.commit()
    await db.refresh(project)
    return ProjectResponse.from_orm(project)
