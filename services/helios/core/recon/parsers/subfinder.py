import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def parse_subfinder(content: str) -> dict[str, Any]:
    """
    Parses Subfinder JSON output (JSON lines).
    Returns a list of discovered subdomains.
    """
    results = {"subdomains": []}

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        try:
            data = json.loads(line)
            if "host" in data:
                results["subdomains"].append(
                    {"host": data["host"], "source": data.get("source", "subfinder")}
                )
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Subfinder JSON line: {e}")
            continue

    return results
