from typing import Any


def analyze_saml_response(xml_data: str) -> list[dict[str, Any]]:
    findings = []
    xml_lower = xml_data.lower()

    if "signature" not in xml_lower:
        findings.append(
            {
                "title": "SAML Missing Signature",
                "description": "The SAML response or assertion is missing a digital signature, allowing an attacker to tamper with the contents.",
                "severity": "critical",
                "confidence": "high",
                "cwe_id": "CWE-347",
            }
        )

    if "rsa-sha1" in xml_lower or "rsa-md5" in xml_lower:
        findings.append(
            {
                "title": "SAML Insecure Signature Algorithm",
                "description": "The SAML signature uses a weak hashing algorithm (e.g., SHA-1 or MD5), which is susceptible to collision attacks.",
                "severity": "high",
                "confidence": "high",
                "cwe_id": "CWE-327",
            }
        )

    return findings
