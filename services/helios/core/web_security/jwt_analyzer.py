import base64
import json
import binascii
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

def _base64url_decode(input_str: str) -> str:
    """Decodes a base64url encoded string, adding padding if necessary."""
    # Add padding
    rem = len(input_str) % 4
    if rem > 0:
        input_str += "=" * (4 - rem)
    # Replace url-safe chars
    input_str = input_str.replace("-", "+").replace("_", "/")
    return base64.b64decode(input_str).decode('utf-8', errors='ignore')

def analyze_jwt(token: str) -> List[Dict[str, Any]]:
    """
    Analyzes a JSON Web Token (JWT) for common security misconfigurations.
    """
    findings = []
    
    parts = token.split(".")
    if len(parts) != 3:
        # Not a standard JWT format
        return findings
        
    header_b64, payload_b64, signature = parts
    
    # 1. Parse Header
    try:
        header_json = _base64url_decode(header_b64)
        header = json.loads(header_json)
    except (binascii.Error, json.JSONDecodeError):
        return findings

    # Check for 'none' algorithm
    alg = str(header.get("alg", "")).lower()
    if alg == "none":
        findings.append({
            "title": "JWT 'none' Algorithm Accepted",
            "description": "The JWT header specifies the 'none' algorithm, which bypasses signature verification if the server accepts it.",
            "severity": "critical",
            "confidence": "high",
            "cwe_id": "CWE-347"
        })
        
    # Check for symmetric algorithm without verifying if a strong secret is used (we can't know offline, but can flag it as informational)
    if alg.startswith("hs"):
        findings.append({
            "title": "JWT Uses Symmetric Signature (HMAC)",
            "description": f"The JWT uses {alg.upper()}. Ensure the signing secret is strong and not easily brute-forced offline.",
            "severity": "info",
            "confidence": "medium",
            "cwe_id": "CWE-326"
        })

    # 2. Parse Payload
    try:
        payload_json = _base64url_decode(payload_b64)
        payload = json.loads(payload_json)
    except (binascii.Error, json.JSONDecodeError):
        return findings

    # Check for missing expiration
    if "exp" not in payload:
        findings.append({
            "title": "JWT Missing Expiration (exp)",
            "description": "The JWT does not contain an 'exp' claim, meaning the token never expires, increasing the risk of token theft.",
            "severity": "medium",
            "confidence": "high",
            "cwe_id": "CWE-613"
        })
        
    # Check for overly sensitive data in payload
    sensitive_keys = ["password", "secret", "ssn", "credit_card", "token"]
    for key in payload.keys():
        if key.lower() in sensitive_keys:
            findings.append({
                "title": f"Sensitive Data in JWT Payload: {key}",
                "description": f"The JWT payload contains a potentially sensitive claim ('{key}'). JWTs are encoded, not encrypted.",
                "severity": "high",
                "confidence": "high",
                "cwe_id": "CWE-312"
            })
            
    return findings
