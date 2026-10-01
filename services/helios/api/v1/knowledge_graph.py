import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helios.infrastructure.database import get_db_session
from helios.models.knowledge_edge import KnowledgeEdge
from helios.models.knowledge_node import KnowledgeNode
from helios.models.project import Project

logger = logging.getLogger(__name__)
router = APIRouter()


# ──────────────────────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────────────────────


class NodeCreate(BaseModel):
    type: str
    label: str
    properties: dict[str, Any] = {}


class EdgeCreate(BaseModel):
    source_id: str
    target_id: str
    relation: str
    properties: dict[str, Any] = {}
    confidence: float = 1.0


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────


async def get_project_or_404(project_id: str, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────


@router.get("/", summary="Retrieve full knowledge graph for a project")
async def get_full_graph(
    project_id: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    await get_project_or_404(project_id, db)

    nodes_result = await db.execute(
        select(KnowledgeNode).where(KnowledgeNode.project_id == project_id)
    )
    nodes = nodes_result.scalars().all()

    edges_result = await db.execute(
        select(KnowledgeEdge).where(KnowledgeEdge.project_id == project_id)
    )
    edges = edges_result.scalars().all()

    return {
        "status": "success",
        "data": {
            "nodes": [
                {
                    "id": str(n.id),
                    "type": n.type,
                    "label": n.label,
                    "properties": n.properties or {},
                }
                for n in nodes
            ],
            "edges": [
                {
                    "id": str(e.id),
                    "source": str(e.source_id),
                    "target": str(e.target_id),
                    "relation": e.relation,
                    "properties": e.properties or {},
                    "confidence": float(e.confidence)
                    if e.confidence is not None
                    else 1.0,
                }
                for e in edges
            ],
        },
    }


@router.post(
    "/nodes",
    status_code=status.HTTP_201_CREATED,
    summary="Create a knowledge graph node",
)
async def create_node(
    project_id: str = Path(...),
    body: NodeCreate,
    db: AsyncSession = Depends(get_db_session),
):
    await get_project_or_404(project_id, db)

    node = KnowledgeNode(
        project_id=project_id,
        type=body.type,
        label=body.label,
        properties=body.properties,
    )
    db.add(node)
    await db.commit()
    await db.refresh(node)

    return {
        "status": "success",
        "data": {"id": str(node.id), "type": node.type, "label": node.label},
    }


@router.post(
    "/edges",
    status_code=status.HTTP_201_CREATED,
    summary="Create a knowledge graph edge",
)
async def create_edge(
    project_id: str = Path(...),
    body: EdgeCreate,
    db: AsyncSession = Depends(get_db_session),
):
    await get_project_or_404(project_id, db)

    src = uuid.UUID(body.source_id)
    tgt = uuid.UUID(body.target_id)

    for node_id in (src, tgt):
        r = await db.execute(
            select(KnowledgeNode).where(
                KnowledgeNode.id == node_id,
                KnowledgeNode.project_id == project_id,
            )
        )
        if not r.scalars().first():
            raise HTTPException(
                status_code=404, detail=f"Node {node_id} not found in project"
            )

    edge = KnowledgeEdge(
        project_id=project_id,
        source_id=src,
        target_id=tgt,
        relation=body.relation,
        properties=body.properties,
        confidence=body.confidence,
    )
    db.add(edge)
    await db.commit()
    await db.refresh(edge)

    return {
        "status": "success",
        "data": {"id": str(edge.id), "relation": edge.relation},
    }


@router.get("/neighbors/{node_id}", summary="Get all neighbours of a node")
async def get_neighbors(
    project_id: str = Path(...),
    node_id: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    await get_project_or_404(project_id, db)

    edges_result = await db.execute(
        select(KnowledgeEdge).where(
            KnowledgeEdge.project_id == project_id,
            (KnowledgeEdge.source_id == node_id) | (KnowledgeEdge.target_id == node_id),
        )
    )
    edges = edges_result.scalars().all()

    neighbour_ids = set()
    for e in edges:
        neighbour_ids.add(e.source_id)
        neighbour_ids.add(e.target_id)
    neighbour_ids.discard(node_id)

    nodes_result = await db.execute(
        select(KnowledgeNode).where(
            KnowledgeNode.id.in_(neighbour_ids),
            KnowledgeNode.project_id == project_id,
        )
    )
    nodes = nodes_result.scalars().all()

    return {
        "status": "success",
        "data": {
            "nodes": [
                {"id": str(n.id), "type": n.type, "label": n.label} for n in nodes
            ],
            "edges": [
                {
                    "id": str(e.id),
                    "source": str(e.source_id),
                    "target": str(e.target_id),
                    "relation": e.relation,
                }
                for e in edges
            ],
        },
    }


@router.delete(
    "/nodes/{node_id}", status_code=204, summary="Delete a node and its edges"
)
async def delete_node(
    project_id: str = Path(...),
    node_id: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(KnowledgeNode).where(
            KnowledgeNode.id == node_id,
            KnowledgeNode.project_id == project_id,
        )
    )
    node = result.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    await db.delete(node)
    await db.commit()
