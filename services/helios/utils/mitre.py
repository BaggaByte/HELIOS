"""
MITRE ATT&CK lookup helpers.

`Finding.capec_id` and the log-intel pipeline (blueprint §"MITRE Mapping")
both assume some way to go from a technique ID to a human-readable
tactic/name, and from a common CWE to a plausible ATT&CK technique. This is
a small, curated offline table covering the techniques HELIOS's own tooling
actually surfaces (network recon, web exploitation, credential access,
lateral movement) — it is deliberately not a full mirror of the ATT&CK STIX
bundle (that's several MB of data and a licensing/update burden this
local-first, offline tool shouldn't take on for a partial feature). It's
built to be trivially extended: add rows to `TECHNIQUES` / `CWE_TO_TECHNIQUE`.
"""

from __future__ import annotations

from typing import Dict, List, Optional, TypedDict


class Technique(TypedDict):
    id: str
    name: str
    tactic: str


TECHNIQUES: Dict[str, Technique] = {
    "T1595": {"id": "T1595", "name": "Active Scanning", "tactic": "Reconnaissance"},
    "T1590": {"id": "T1590", "name": "Gather Victim Network Information", "tactic": "Reconnaissance"},
    "T1592": {"id": "T1592", "name": "Gather Victim Host Information", "tactic": "Reconnaissance"},
    "T1589": {"id": "T1589", "name": "Gather Victim Identity Information", "tactic": "Reconnaissance"},
    "T1190": {"id": "T1190", "name": "Exploit Public-Facing Application", "tactic": "Initial Access"},
    "T1133": {"id": "T1133", "name": "External Remote Services", "tactic": "Initial Access"},
    "T1078": {"id": "T1078", "name": "Valid Accounts", "tactic": "Initial Access"},
    "T1110": {"id": "T1110", "name": "Brute Force", "tactic": "Credential Access"},
    "T1552": {"id": "T1552", "name": "Unsecured Credentials", "tactic": "Credential Access"},
    "T1555": {"id": "T1555", "name": "Credentials from Password Stores", "tactic": "Credential Access"},
    "T1212": {"id": "T1212", "name": "Exploitation for Credential Access", "tactic": "Credential Access"},
    "T1059": {"id": "T1059", "name": "Command and Scripting Interpreter", "tactic": "Execution"},
    "T1203": {"id": "T1203", "name": "Exploitation for Client Execution", "tactic": "Execution"},
    "T1068": {"id": "T1068", "name": "Exploitation for Privilege Escalation", "tactic": "Privilege Escalation"},
    "T1210": {"id": "T1210", "name": "Exploitation of Remote Services", "tactic": "Lateral Movement"},
    "T1021": {"id": "T1021", "name": "Remote Services", "tactic": "Lateral Movement"},
    "T1005": {"id": "T1005", "name": "Data from Local System", "tactic": "Collection"},
    "T1041": {"id": "T1041", "name": "Exfiltration Over C2 Channel", "tactic": "Exfiltration"},
    "T1071": {"id": "T1071", "name": "Application Layer Protocol", "tactic": "Command and Control"},
}

# Best-effort CWE -> likely ATT&CK technique mapping, for auto-tagging
# findings that already carry a CWE ID (e.g. from the secret-detector or a
# ZAP import) with a plausible ATT&CK technique.
CWE_TO_TECHNIQUE: Dict[str, str] = {
    "CWE-798": "T1552",  # Use of Hard-coded Credentials
    "CWE-522": "T1552",  # Insufficiently Protected Credentials
    "CWE-259": "T1552",  # Use of Hard-coded Password
    "CWE-89": "T1190",   # SQL Injection
    "CWE-78": "T1190",   # OS Command Injection
    "CWE-79": "T1189",   # Cross-Site Scripting -> Drive-by Compromise family (best-effort)
    "CWE-306": "T1078",  # Missing Authentication for Critical Function
    "CWE-287": "T1078",  # Improper Authentication
    "CWE-284": "T1068",  # Improper Access Control
    "CWE-269": "T1068",  # Improper Privilege Management
}


def get_technique(technique_id: str) -> Optional[Technique]:
    """Look up a technique by its ATT&CK ID (e.g. 'T1190'). None if unknown."""
    return TECHNIQUES.get(technique_id.upper())


def technique_for_cwe(cwe_id: Optional[str]) -> Optional[Technique]:
    """Best-effort: map a CWE ID (e.g. 'CWE-89') to a likely ATT&CK technique."""
    if not cwe_id:
        return None
    technique_id = CWE_TO_TECHNIQUE.get(cwe_id.upper())
    return TECHNIQUES.get(technique_id) if technique_id else None


def list_tactics() -> List[str]:
    """Return the distinct tactic names covered by the local technique table."""
    seen: List[str] = []
    for t in TECHNIQUES.values():
        if t["tactic"] not in seen:
            seen.append(t["tactic"])
    return seen
