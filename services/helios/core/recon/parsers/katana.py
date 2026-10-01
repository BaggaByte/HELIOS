import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def parse_katana(content: str) -> dict[str, Any]:
    """
    Parses Katana JSONL output.
    Returns a list of discovered URLs/endpoints.
    """
    results = {"directories": []}

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        try:
            data = json.loads(line)
            # Katana includes request/response info in JSON format
            req = data.get("request", {})
            resp = data.get("response", {})

            url = req.get("endpoint", "")
            if not url:
                continue

            status = str(resp.get("status_code", ""))

            results["directories"].append(
                {"path": url, "status": status, "method": req.get("method", "")}
            )
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Katana JSON line: {e}")
            continue

    return results
