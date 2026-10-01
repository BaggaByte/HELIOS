import re
from typing import List, Dict

PATTERNS = {
    "JWT": r"ey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
    "AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "Stripe Key": r"[rsp]k_live_[0-9a-zA-Z]{24}",
    "Google API Key": r"AIza[0-9A-Za-z-_]{35}",
    "Generic Secret": r"(?i)(?:api_key|secret|token|password)[\s]*[:=][\s]*[\"']([a-zA-Z0-9\-_]{16,})[\"']",
}


def extract_tokens(js_code: str) -> List[Dict[str, str]]:
    """
    Scans JS code for high-value secrets, API keys, and tokens.
    """
    found = []

    for type_name, pattern in PATTERNS.items():
        matches = re.finditer(pattern, js_code)
        for match in matches:
            # For Generic Secret, we want the capture group (the actual token)
            value = match.group(1) if len(match.groups()) > 0 else match.group(0)

            found.append({"type": type_name, "value": value})

    # Deduplicate
    unique = {f"{item['type']}:{item['value']}": item for item in found}
    return list(unique.values())
