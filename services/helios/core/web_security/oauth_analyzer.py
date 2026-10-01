from typing import Dict, Any, List
from urllib.parse import urlparse, parse_qs


def analyze_oauth_request(
    url: str, params: Dict[str, str] = None
) -> List[Dict[str, Any]]:
    findings = []

    if not params:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        params = {k: v[0] for k, v in params.items()}

    response_type = params.get("response_type", "").lower()

    if response_type == "token":
        findings.append(
            {
                "title": "OAuth Implicit Flow Used",
                "description": "The OAuth flow uses response_type=token (Implicit Flow), which exposes access tokens in the URL fragment. It is highly recommended to use the Authorization Code flow with PKCE instead.",
                "severity": "high",
                "confidence": "high",
                "cwe_id": "CWE-312",
            }
        )

    if "state" not in params:
        findings.append(
            {
                "title": "OAuth Missing State Parameter",
                "description": "The OAuth request does not include a 'state' parameter, making the flow vulnerable to Cross-Site Request Forgery (CSRF).",
                "severity": "high",
                "confidence": "high",
                "cwe_id": "CWE-352",
            }
        )

    return findings
