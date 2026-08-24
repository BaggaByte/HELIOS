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
    "TA0040": "Impact"
}

def get_tactic_name(tactic_id: str) -> str:
    """Returns the human-readable name of a MITRE ATT&CK tactic ID."""
    return MITRE_TACTICS.get(tactic_id.upper(), "Unknown Tactic")

def get_technique_info(technique_id: str) -> dict:
    """Returns mock info for a MITRE ATT&CK technique."""
    return {
        "id": technique_id.upper(),
        "url": f"https://attack.mitre.org/techniques/{technique_id.upper()}"
    }
