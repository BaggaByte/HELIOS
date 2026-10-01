"""
MITRE ATT&CK lookup helpers.

`get_technique_info()` previously returned only an ID and a guessed URL for
*any* input string, with a docstring admitting it was mock data — it never
validated the technique actually exists, and gave no name or tactic. This
keeps the existing MITRE_TACTICS table and function names, and adds a real
(if intentionally small, curated, offline) technique table plus a CWE ->
technique mapping, so findings that carry a CWE ID can be tagged with a
plausible ATT&CK technique instead of a dead lookup.

This is deliberately not a full mirror of the ATT&CK STIX bundle (that's
several MB and an update/licensing burden this local-first, offline tool
shouldn't take on for a partial feature) — it covers the techniques HELIOS's
own tooling actually surfaces. Extend TECHNIQUES / CWE_TO_TECHNIQUE as
coverage grows.
"""

from __future__ import annotations

from typing import Dict, Optional, TypedDict

MITRE_TACTICS = {
    "TA0001": "Initial Access",
    "TA0002": "Execution",
    "TA0003": "Persistence",
    "TA0004": "Privilege Escalation",
    "TA0005": "Defense Evasion",
    "TA0006": "Credential Access",
    "TA0007": "Discovery",
    "TA0008": "Lateral Movement",
    "TA0009": "Collection",
    "TA0010": "Exfiltration",
    "TA0011": "Command and Control",
    "TA0040": "Impact",
}


class Technique(TypedDict):
    id: str
    name: str
    tactic: str


TECHNIQUES: Dict[str, Technique] = {
    "T1595": {"id": "T1595", "name": "Active Scanning", "tactic": "Reconnaissance"},
    "T1590": {
        "id": "T1590",
        "name": "Gather Victim Network Information",
        "tactic": "Reconnaissance",
    },
    "T1592": {
        "id": "T1592",
        "name": "Gather Victim Host Information",
        "tactic": "Reconnaissance",
    },
    "T1589": {
        "id": "T1589",
        "name": "Gather Victim Identity Information",
        "tactic": "Reconnaissance",
    },
    "T1190": {
        "id": "T1190",
        "name": "Exploit Public-Facing Application",
        "tactic": "Initial Access",
    },
    "T1189": {"id": "T1189", "name": "Drive-by Compromise", "tactic": "Initial Access"},
    "T1133": {
        "id": "T1133",
        "name": "External Remote Services",
        "tactic": "Initial Access",
    },
    "T1078": {"id": "T1078", "name": "Valid Accounts", "tactic": "Initial Access"},
    "T1110": {"id": "T1110", "name": "Brute Force", "tactic": "Credential Access"},
    "T1552": {
        "id": "T1552",
        "name": "Unsecured Credentials",
        "tactic": "Credential Access",
    },
    "T1555": {
        "id": "T1555",
        "name": "Credentials from Password Stores",
        "tactic": "Credential Access",
    },
    "T1212": {
        "id": "T1212",
        "name": "Exploitation for Credential Access",
        "tactic": "Credential Access",
    },
    "T1059": {
        "id": "T1059",
        "name": "Command and Scripting Interpreter",
        "tactic": "Execution",
    },
    "T1203": {
        "id": "T1203",
        "name": "Exploitation for Client Execution",
        "tactic": "Execution",
    },
    "T1068": {
        "id": "T1068",
        "name": "Exploitation for Privilege Escalation",
        "tactic": "Privilege Escalation",
    },
    "T1210": {
        "id": "T1210",
        "name": "Exploitation of Remote Services",
        "tactic": "Lateral Movement",
    },
    "T1021": {"id": "T1021", "name": "Remote Services", "tactic": "Lateral Movement"},
    "T1005": {"id": "T1005", "name": "Data from Local System", "tactic": "Collection"},
    "T1041": {
        "id": "T1041",
        "name": "Exfiltration Over C2 Channel",
        "tactic": "Exfiltration",
    },
    "T1071": {
        "id": "T1071",
        "name": "Application Layer Protocol",
        "tactic": "Command and Control",
    },
}

# Best-effort CWE -> likely ATT&CK technique mapping, covering the CWEs
# HELIOS's own analyzers (secret detector, JWT/OAuth/SAML/OpenAPI analyzers,
# ZAP/Burp import) actually produce.
CWE_TO_TECHNIQUE: Dict[str, str] = {
    "CWE-798": "T1552",  # Use of Hard-coded Credentials
    "CWE-522": "T1552",  # Insufficiently Protected Credentials
    "CWE-259": "T1552",  # Use of Hard-coded Password
    "CWE-312": "T1552",  # Cleartext Storage of Sensitive Information
    "CWE-89": "T1190",  # SQL Injection
    "CWE-78": "T1190",  # OS Command Injection
    "CWE-352": "T1190",  # CSRF
    "CWE-693": "T1190",  # Protection Mechanism Failure (e.g. insecure HTTP methods)
    "CWE-79": "T1189",  # Cross-Site Scripting
    "CWE-306": "T1078",  # Missing Authentication for Critical Function
    "CWE-287": "T1078",  # Improper Authentication
    "CWE-347": "T1078",  # Improper Verification of Cryptographic Signature (forged SAML assertion)
    "CWE-285": "T1078",  # Improper Authorization
    "CWE-284": "T1068",  # Improper Access Control
    "CWE-269": "T1068",  # Improper Privilege Management
}


def get_tactic_name(tactic_id: str) -> str:
    """Returns the human-readable name of a MITRE ATT&CK tactic ID."""
    return MITRE_TACTICS.get(tactic_id.upper(), "Unknown Tactic")


def get_technique_info(technique_id: str) -> dict:
    """
    Returns real info for a MITRE ATT&CK technique ID from the local table
    (name, tactic, canonical URL), or a minimal record with `"known": False`
    if the ID isn't in the local table — never a guessed name.
    """
    technique_id = technique_id.upper()
    technique = TECHNIQUES.get(technique_id)
    if technique:
        return {
            "id": technique_id,
            "name": technique["name"],
            "tactic": technique["tactic"],
            "url": f"https://attack.mitre.org/techniques/{technique_id}",
            "known": True,
        }
    return {
        "id": technique_id,
        "url": f"https://attack.mitre.org/techniques/{technique_id}",
        "known": False,
    }


def technique_for_cwe(cwe_id: Optional[str]) -> Optional[Technique]:
    """Best-effort: map a CWE ID (e.g. 'CWE-89') to a likely ATT&CK technique."""
    if not cwe_id:
        return None
    technique_id = CWE_TO_TECHNIQUE.get(cwe_id.upper())
    return TECHNIQUES.get(technique_id) if technique_id else None
