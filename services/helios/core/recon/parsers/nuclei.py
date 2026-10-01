import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def parse_nuclei(content: str) -> Dict[str, Any]:
    """
    Parses Nuclei JSONL output.
    Returns structured findings suitable for DB insertion.
    """
    results = {"findings": []}

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        try:
            data = json.loads(line)

            # Map Nuclei fields to HELIOS finding structure
            info = data.get("info", {})
            finding = {
                "title": info.get("name", "Unknown Nuclei Finding"),
                "description": info.get("description", ""),
                "severity": info.get("severity", "info").upper(),
                "confidence": "HIGH",  # Nuclei generally implies high confidence
                "host": data.get("host", ""),
                "matched_at": data.get("matched-at", ""),
                "template_id": data.get("template-id", ""),
                "remediation": info.get("remediation", ""),
                "cwe_id": info.get("classification", {}).get("cwe-id", [])[0]
                if info.get("classification", {}).get("cwe-id")
                else None,
                "cvss_score": info.get("classification", {}).get("cvss-score", 0.0),
                "cvss_metrics": info.get("classification", {}).get("cvss-metrics", ""),
                "references": info.get("reference", []),
            }
            results["findings"].append(finding)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Nuclei JSON line: {e}")
            continue

    return results
