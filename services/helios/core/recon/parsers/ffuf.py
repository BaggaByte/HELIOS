import json
from typing import Any


def parse_ffuf(content: str) -> dict[str, Any]:
    """
    Parses FFUF JSON output.
    """
    results = {"directories": []}

    try:
        data = json.loads(content)
        for result in data.get("results", []):
            results["directories"].append(
                {
                    "path": result.get("url"),
                    "status": result.get("status"),
                    "length": result.get("length"),
                    "words": result.get("words"),
                    "lines": result.get("lines"),
                }
            )
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid FFUF JSON format: {e}")

    return results
