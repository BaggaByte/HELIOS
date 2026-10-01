import re
from typing import List, Dict, Any

IOC_PATTERNS = {
    "ipv4": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
    "md5": r"\b[a-fA-F0-9]{32}\b",
    "sha1": r"\b[a-fA-F0-9]{40}\b",
    "sha256": r"\b[a-fA-F0-9]{64}\b",
    "url": r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+",
}


def extract_iocs(text: str) -> Dict[str, List[str]]:
    iocs = {"ipv4": [], "md5": [], "sha1": [], "sha256": [], "url": []}

    for ioc_type, pattern in IOC_PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            iocs[ioc_type] = list(set(matches))

    return {k: v for k, v in iocs.items() if v}
