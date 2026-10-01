import json
from typing import Any

import yaml


def analyze_openapi_spec(spec_content: str) -> list[dict[str, Any]]:
    findings = []
    try:
        if spec_content.strip().startswith("{"):
            spec = json.loads(spec_content)
        else:
            spec = yaml.safe_load(spec_content)
    except Exception:
        return findings

    paths = spec.get("paths", {})
    if not isinstance(paths, dict):
        return findings

    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue

        for method, details in methods.items():
            if method.lower() in ["trace", "track"]:
                findings.append(
                    {
                        "title": f"Insecure HTTP Method in OpenAPI: {method.upper()}",
                        "description": f"The endpoint {path} supports {method.upper()}, which can lead to Cross-Site Tracing (XST).",
                        "severity": "medium",
                        "confidence": "high",
                        "cwe_id": "CWE-693",
                    }
                )

            # Check for lack of security definitions on sensitive paths
            if isinstance(details, dict):
                if "security" not in details and "security" not in spec:
                    findings.append(
                        {
                            "title": f"Unauthenticated Endpoint in OpenAPI: {path}",
                            "description": f"The endpoint {path} ({method.upper()}) does not specify any security requirements.",
                            "severity": "high",
                            "confidence": "medium",
                            "cwe_id": "CWE-285",
                        }
                    )

    return findings
