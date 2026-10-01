import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def parse_gau(content: str) -> dict[str, Any]:
    """
    Parses GAU JSON output.
    Returns a list of discovered URLs.
    """
    results = {"directories": []}

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        try:
            data = json.loads(line)
            if "url" in data:
                results["directories"].append(
                    {
                        "path": data["url"],
                        "status": "unknown",  # GAU just finds URLs, doesn't always ping them
                    }
                )
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse GAU JSON line: {e}")
            continue

    return results
