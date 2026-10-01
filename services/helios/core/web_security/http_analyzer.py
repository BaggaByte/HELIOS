from typing import Dict, Any, List
import re
import logging

logger = logging.getLogger(__name__)


def analyze_http_response(
    headers: Dict[str, str], url: str = ""
) -> List[Dict[str, Any]]:
    """
    Analyzes HTTP response headers for security misconfigurations.
    """
    findings = []

    # Normalize headers to lowercase for easy lookup
    headers_lower = {k.lower(): v for k, v in headers.items()}

    # 1. Strict-Transport-Security (HSTS)
    if "strict-transport-security" not in headers_lower and url.startswith("https"):
        findings.append(
            {
                "title": "Missing HTTP Strict Transport Security (HSTS)",
                "description": "The server did not return an HSTS header, allowing man-in-the-middle attacks to strip SSL/TLS protection.",
                "severity": "medium",
                "confidence": "high",
                "cwe_id": "CWE-319",
            }
        )

    # 2. Content-Security-Policy (CSP)
    if "content-security-policy" not in headers_lower:
        findings.append(
            {
                "title": "Missing Content-Security-Policy (CSP)",
                "description": "The server is missing a CSP header, making it easier for attackers to execute Cross-Site Scripting (XSS) attacks.",
                "severity": "low",
                "confidence": "high",
                "cwe_id": "CWE-346",
            }
        )

    # 3. X-Frame-Options
    if (
        "x-frame-options" not in headers_lower
        and "frame-ancestors" not in headers_lower.get("content-security-policy", "")
    ):
        findings.append(
            {
                "title": "Missing Anti-Clickjacking Header",
                "description": "The server does not prevent framing via X-Frame-Options or CSP frame-ancestors, enabling clickjacking attacks.",
                "severity": "medium",
                "confidence": "high",
                "cwe_id": "CWE-1021",
            }
        )

    # 4. Information Disclosure (Server / X-Powered-By)
    server_header = headers_lower.get("server", "")
    if re.search(r"\d", server_header):  # Contains a version number
        findings.append(
            {
                "title": "Server Version Disclosure",
                "description": f"The Server header reveals the version: `{headers.get('Server', server_header)}`.",
                "severity": "info",
                "confidence": "high",
                "cwe_id": "CWE-200",
            }
        )

    if "x-powered-by" in headers_lower:
        findings.append(
            {
                "title": "Technology Stack Disclosure",
                "description": f"The X-Powered-By header reveals backend technologies: `{headers.get('X-Powered-By')}`.",
                "severity": "info",
                "confidence": "high",
                "cwe_id": "CWE-200",
            }
        )

    return findings
