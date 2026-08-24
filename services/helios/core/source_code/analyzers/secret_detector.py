import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Basic regex rules for secret detection
SECRET_RULES = [
    {
        "id": "aws-access-key",
        "title": "AWS Access Key ID",
        "regex": re.compile(r"(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}"),
        "severity": "critical"
    },
    {
        "id": "generic-api-key",
        "title": "Generic API Key / Token",
        "regex": re.compile(r"(?i)(?:api_key|apikey|secret|token|password|passwd|pwd)[\s:=]+['\"]([a-zA-Z0-9_=\-]{16,64})['\"]"),
        "severity": "high"
    },
    {
        "id": "private-key",
        "title": "Asymmetric Private Key",
        "regex": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        "severity": "critical"
    },
    {
        "id": "jwt-token",
        "title": "JSON Web Token (JWT)",
        "regex": re.compile(r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}"),
        "severity": "medium"
    }
]

def scan_text(content: str, filename: str) -> List[Dict[str, Any]]:
    """Scans text content line-by-line for secrets based on regex rules."""
    findings = []
    lines = content.splitlines()
    
    for i, line in enumerate(lines):
        for rule in SECRET_RULES:
            matches = rule["regex"].finditer(line)
            for match in matches:
                # Capture surrounding context (e.g. up to 50 chars around)
                start_idx = max(0, match.start() - 50)
                end_idx = min(len(line), match.end() + 50)
                snippet = line[start_idx:end_idx].strip()
                
                findings.append({
                    "title": rule["title"],
                    "description": f"Found potential {rule['title']} in file `{filename}` on line {i+1}.",
                    "severity": rule["severity"],
                    "confidence": "medium",
                    "cwe_id": "CWE-798", # Use of Hard-coded Credentials
                    "impact": f"{filename}:{i+1}",
                    "line_number": i + 1,
                    "match": match.group(0),
                    "snippet": snippet
                })
                
    return findings
