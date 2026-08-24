from typing import Dict, Any, List

def map_event_to_mitre(event_data: Dict[str, Any]) -> List[str]:
    """
    Returns a list of MITRE ATT&CK tactic IDs based on heuristics.
    """
    tactics = []
    
    msg = str(event_data.get("message", "")).lower()
    metadata_str = str(event_data.get("metadata", {})).lower()
    event_type = str(event_data.get("event_type", "")).lower()
    
    # Execution
    if "powershell" in msg or "cmd.exe" in msg or "bash" in msg or "sh -c" in msg:
        tactics.append("TA0002") 
        
    # Credential Access
    if "failed password" in msg or "failed login" in msg or "eventid_4625" in event_type:
        tactics.append("TA0006")
        
    # Discovery
    if "nmap" in metadata_str or "nikto" in metadata_str or "whoami" in msg:
        tactics.append("TA0007")
        
    # Privilege Escalation
    if "sudo" in msg or "eventid_4720" in event_type:
        tactics.append("TA0004")
        
    # Initial Access
    if "exploit" in metadata_str or "sqli" in msg or "traversal" in msg:
        tactics.append("TA0001")
        
    return list(set(tactics))
