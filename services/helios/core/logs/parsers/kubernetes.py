import json
from datetime import datetime
from typing import Dict, Any, Optional

def parse_kubernetes_log(line: str) -> Optional[Dict[str, Any]]:
    try:
        data = json.loads(line)
        if "requestURI" not in data and "verb" not in data:
            return None
            
        timestamp_str = data.get("requestReceivedTimestamp")
        try:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except:
            dt = datetime.now()
            
        user = data.get("user", {}).get("username", "unknown")
        verb = data.get("verb", "unknown")
        resource = data.get("objectRef", {}).get("resource", "unknown")
        
        severity = "info"
        if verb in ["create", "delete", "patch"] and resource in ["secrets", "rolebindings", "clusterrolebindings", "pods/exec"]:
            severity = "high"
            
        return {
            "timestamp": dt,
            "source": "kubernetes",
            "event_type": f"k8s_audit_{verb}",
            "severity": severity,
            "message": f"K8s {verb} on {resource} by {user}",
            "source_ip": data.get("sourceIPs", [None])[0],
            "dest_ip": None,
            "metadata": data
        }
    except Exception:
        return None
