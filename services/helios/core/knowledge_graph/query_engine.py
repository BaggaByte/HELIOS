from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List

from helios.models.project import Project
from helios.models.knowledge_node import KnowledgeNode
from helios.models.knowledge_edge import KnowledgeEdge
import uuid

async def seed_mock_graph_if_empty(db: AsyncSession, project_id: uuid.UUID):
    """Seeds the knowledge graph with some demo data if it's empty."""
    # Check if empty
    result = await db.execute(select(KnowledgeNode).filter_by(project_id=project_id).limit(1))
    first = result.scalars().first()
    if first:
        return # Already populated
        
    # Create Nodes
    n_host1 = KnowledgeNode(project_id=project_id, entity_type="host", label="192.168.1.100", identity_key="ip:192.168.1.100", properties={"os": "Linux"})
    n_host2 = KnowledgeNode(project_id=project_id, entity_type="host", label="10.0.0.5", identity_key="ip:10.0.0.5", properties={"os": "Windows"})
    n_service = KnowledgeNode(project_id=project_id, entity_type="service", label="PostgreSQL (5432)", identity_key="svc:192.168.1.100:5432", properties={"port": 5432, "state": "open"})
    n_vuln = KnowledgeNode(project_id=project_id, entity_type="vulnerability", label="CVE-2023-XXXXX (SQLi)", identity_key="vuln:CVE-2023-XXXXX", properties={"severity": "Critical"})
    n_malware = KnowledgeNode(project_id=project_id, entity_type="malware", label="dropped_shell.exe", identity_key="malware:dropped_shell", properties={"hash": "abc123def456"})
    n_user = KnowledgeNode(project_id=project_id, entity_type="user", label="admin", identity_key="user:admin", properties={"privilege": "high"})
    
    db.add_all([n_host1, n_host2, n_service, n_vuln, n_malware, n_user])
    await db.flush() # To get IDs
    
    # Create Edges
    edges = [
        KnowledgeEdge(project_id=project_id, source_id=n_host1.id, target_id=n_service.id, relation_type="HOSTS_SERVICE"),
        KnowledgeEdge(project_id=project_id, source_id=n_service.id, target_id=n_vuln.id, relation_type="HAS_VULNERABILITY"),
        KnowledgeEdge(project_id=project_id, source_id=n_malware.id, target_id=n_vuln.id, relation_type="EXPLOITS"),
        KnowledgeEdge(project_id=project_id, source_id=n_host2.id, target_id=n_host1.id, relation_type="CONNECTS_TO", properties={"protocol": "SSH"}),
        KnowledgeEdge(project_id=project_id, source_id=n_user.id, target_id=n_host2.id, relation_type="COMPROMISED")
    ]
    
    db.add_all(edges)
    await db.commit()

async def get_graph_data(db: AsyncSession) -> Dict[str, Any]:
    """Retrieves all nodes and edges formatted for React Flow."""
    result = await db.execute(select(Project).filter_by(name="Default Project"))
    project = result.scalars().first()
    
    if not project:
        project = Project(name="Default Project", description="Default workspace", scope="*")
        db.add(project)
        await db.commit()
        await db.refresh(project)
        
    await seed_mock_graph_if_empty(db, project.id)
    
    # Fetch all nodes
    nodes_res = await db.execute(select(KnowledgeNode).filter_by(project_id=project.id))
    db_nodes = nodes_res.scalars().all()
    
    # Fetch all edges
    edges_res = await db.execute(select(KnowledgeEdge).filter_by(project_id=project.id))
    db_edges = edges_res.scalars().all()
    
    # Format for React Flow
    rf_nodes = []
    # Basic auto-layout positioning (very simple scatter for now)
    import random
    
    for n in db_nodes:
        rf_nodes.append({
            "id": str(n.id),
            "type": "customNode", # We will define a generic custom node on frontend
            "position": {"x": random.randint(100, 800), "y": random.randint(100, 600)},
            "data": {
                "label": n.label,
                "type": n.entity_type,
                "properties": n.properties
            }
        })
        
    rf_edges = []
    for e in db_edges:
        rf_edges.append({
            "id": str(e.id),
            "source": str(e.source_id),
            "target": str(e.target_id),
            "label": e.relation_type,
            "animated": True, # Make relations look cool
            "type": "smoothstep"
        })
        
    return {
        "nodes": rf_nodes,
        "edges": rf_edges
    }
