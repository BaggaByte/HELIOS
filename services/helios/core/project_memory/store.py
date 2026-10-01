import logging
from typing import Any

logger = logging.getLogger(__name__)

# MVP: In-memory store for project context.
# In a real implementation, this would be backed by the database.
_memory_store: dict[str, dict[str, Any]] = {}


def get_project_context(project_id: str) -> dict[str, Any]:
    """Retrieve the memory context for a given project."""
    if project_id not in _memory_store:
        _memory_store[project_id] = {
            "summary": "This is a new penetration test project.",
            "completed_actions": [],
            "known_technologies": set(),
            "key_findings": [],
        }
    return _memory_store[project_id]


def add_completed_action(project_id: str, action: str):
    """Log an action that the AI or user has completed."""
    ctx = get_project_context(project_id)
    if action not in ctx["completed_actions"]:
        ctx["completed_actions"].append(action)


def add_known_technology(project_id: str, tech: str):
    """Add a discovered technology to the project context."""
    ctx = get_project_context(project_id)
    ctx["known_technologies"].add(tech)


def add_key_finding(project_id: str, finding_summary: str):
    """Add a high-level summary of a finding."""
    ctx = get_project_context(project_id)
    ctx["key_findings"].append(finding_summary)


def update_summary(project_id: str, new_summary: str):
    """Update the high-level project summary."""
    ctx = get_project_context(project_id)
    ctx["summary"] = new_summary
