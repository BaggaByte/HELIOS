import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def parse_dnsx(content: str) -> Dict[str, Any]:
    """
    Parses DNSx JSON output.
    Returns a list of resolved subdomains.
    """
    results = {
        "subdomains": []
    }
    
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
            
        try:
            data = json.loads(line)
            if "host" in data:
                # Use a records for IP if available
                ip = data.get("a", [""])[0] if data.get("a") else ""
                results["subdomains"].append({
                    "host": data["host"],
                    "ip": ip,
                    "source": "dnsx"
                })
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse DNSx JSON line: {e}")
            continue
            
    return results