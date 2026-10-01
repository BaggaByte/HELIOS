import re

from helios.core.project_memory.store import get_project_context


def _jaccard_similarity(str1: str, str2: str) -> float:
    """Calculate the Jaccard similarity between two strings based on word tokens."""
    # Tokenize and lowercase
    set1 = set(re.findall(r"\w+", str1.lower()))
    set2 = set(re.findall(r"\w+", str2.lower()))

    if not set1 or not set2:
        return 0.0

    intersection = set1.intersection(set2)
    union = set1.union(set2)

    return len(intersection) / len(union)


def is_duplicate_finding(
    project_id: str, new_finding: str, threshold: float = 0.75
) -> bool:
    """
    Checks if a new finding is too similar to an existing key finding
    in the project memory. Returns True if a duplicate is found.
    """
    ctx = get_project_context(project_id)
    existing_findings: list[str] = ctx.get("key_findings", [])

    for finding in existing_findings:
        similarity = _jaccard_similarity(new_finding, finding)
        if similarity >= threshold:
            return True

    return False
