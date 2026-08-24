"""
Knowledge graph builder — synchronises real project data (Hosts, Services,
Findings) into the KnowledgeNode / KnowledgeEdge tables so the graph view
reflects the actual state of a project instead of demo data.

This replaces `query_engine.py`, which is now removed. That file seeded
hardcoded mock nodes (a fake "CVE-2023-XXXXX" vulnerability, a fake
"dropped_shell.exe", fake hosts at 192.168.1.100/10.0.0.5) into any project
whose graph was empty, and constructed KnowledgeNode/KnowledgeEdge with
keyword arguments (`entity_type`, `identity_key`, `relation_type`) that don't
exist on the actual models (`type`, `label`, `relation`) — so it would have
raised a TypeError the moment anything called it. Nothing did: it was never
imported by any route or service, so it sat in the repo as dead, broken code.

The real, working CRUD graph API (`api/v1/knowledge_graph.py`) already uses
the correct field names — what was missing was anything to *populate* it
automatically from recon/finding data. That's what this module does.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helios.models.knowledge_edge import KnowledgeEdge
from helios.models.knowledge_node import KnowledgeNode


async def _find_node_by_key(
    db: AsyncSession, project_id: str, node_type: str, key: str
) -> Optional[KnowledgeNode]:
    """
    Look up an existing node by its caller-assigned `_key` (stored in
    `properties`). SQLite's JSON support varies across builds, so this
    filters in Python rather than relying on json_extract in the query —
    fine at project-graph scale (hundreds, not millions, of nodes).
    """
    result = await db.execute(
        select(KnowledgeNode).where(
            KnowledgeNode.project_id == project_id,
            KnowledgeNode.type == node_type,
        )
    )
    for node in result.scalars().all():
        if (node.properties or {}).get("_key") == key:
            return node
    return None


async def upsert_node(
    db: AsyncSession,
    project_id: str,
    node_type: str,
    label: str,
    key: str,
    properties: Optional[Dict[str, Any]] = None,
) -> KnowledgeNode:
    """
    Idempotently create-or-update a knowledge graph node.

    `key` is a deterministic identity string chosen by the caller (e.g.
    "host:<host_id>", "finding:<finding_id>") so repeated syncs update the
    same node instead of creating duplicates.
    """
    props = dict(properties or {})
    props["_key"] = key

    node = await _find_node_by_key(db, project_id, node_type, key)
    if node:
        node.label = label
        node.properties = {**(node.properties or {}), **props}
    else:
        node = KnowledgeNode(
            project_id=project_id,
            type=node_type,
            label=label,
            properties=props,
        )
        db.add(node)
    await db.flush()
    return node


async def upsert_edge(
    db: AsyncSession,
    project_id: str,
    source: KnowledgeNode,
    target: KnowledgeNode,
    relation: str,
    properties: Optional[Dict[str, Any]] = None,
    confidence: float = 1.0,
) -> KnowledgeEdge:
    """Idempotently create-or-update an edge between two existing nodes."""
    result = await db.execute(
        select(KnowledgeEdge).where(
            KnowledgeEdge.project_id == project_id,
            KnowledgeEdge.source_id == source.id,
            KnowledgeEdge.target_id == target.id,
            KnowledgeEdge.relation == relation,
        )
    )
    edge = result.scalars().first()
    if edge:
        if properties:
            edge.properties = {**(edge.properties or {}), **properties}
        edge.confidence = confidence
    else:
        edge = KnowledgeEdge(
            project_id=project_id,
            source_id=source.id,
            target_id=target.id,
            relation=relation,
            properties=properties or {},
            confidence=confidence,
        )
        db.add(edge)
    await db.flush()
    return edge


async def sync_host(db: AsyncSession, project_id: str, host) -> KnowledgeNode:
    """Upsert a Host row as a graph node."""
    return await upsert_node(
        db, project_id,
        node_type="host",
        label=host.hostname or host.ip,
        key=f"host:{host.id}",
        properties={"ip": host.ip, "os": host.os, "ref_id": host.id},
    )


async def sync_service(
    db: AsyncSession, project_id: str, host_node: KnowledgeNode, service
) -> KnowledgeNode:
    """Upsert a Service row as a node, linked to its host via HOSTS_SERVICE."""
    label = f"{service.name or service.protocol}/{service.port}"
    if service.product:
        label += f" ({service.product} {service.version or ''})".rstrip()

    service_node = await upsert_node(
        db, project_id,
        node_type="service",
        label=label,
        key=f"service:{service.id}",
        properties={
            "port": service.port,
            "protocol": service.protocol,
            "state": service.state,
            "ref_id": service.id,
        },
    )
    await upsert_edge(db, project_id, host_node, service_node, relation="HOSTS_SERVICE")
    return service_node


async def sync_finding(
    db: AsyncSession,
    project_id: str,
    finding,
    service_node: Optional[KnowledgeNode] = None,
) -> KnowledgeNode:
    """Upsert a Finding row as a node, linked to its service via HAS_FINDING."""
    finding_node = await upsert_node(
        db, project_id,
        node_type="finding",
        label=finding.title,
        key=f"finding:{finding.id}",
        properties={
            "severity": finding.severity,
            "cvss_score": float(finding.cvss_score) if finding.cvss_score is not None else None,
            "cwe_id": finding.cwe_id,
            "ref_id": finding.id,
        },
    )
    if service_node is not None:
        await upsert_edge(
            db, project_id, service_node, finding_node,
            relation="HAS_FINDING",
            properties={"severity": finding.severity},
        )
    return finding_node


async def sync_host_with_services(db: AsyncSession, project_id: str, host) -> KnowledgeNode:
    """Convenience: sync a host and every service currently loaded on it."""
    host_node = await sync_host(db, project_id, host)
    for service in getattr(host, "services", None) or []:
        await sync_service(db, project_id, host_node, service)
    return host_node
