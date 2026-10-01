import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def parse_amass(content: str) -> Dict[str, Any]:
    """
    Parses Amass JSON output.
    Returns a list of discovered subdomains.
    """
    results = {"subdomains": []}

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        try:
            data = json.loads(line)
            if "name" in data:
                results["subdomains"].append({"host": data["name"], "source": "amass"})
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Amass JSON line: {e}")
            continue

    return results
