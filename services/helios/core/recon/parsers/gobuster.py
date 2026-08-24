import json
from typing import Dict, Any, List

def parse_gobuster(content: str) -> Dict[str, Any]:
    """
    Parses Gobuster standard output or JSON output.
    Returns standard HELIOS recon format.
    """
    results = {
        "directories": []
    }
    
    # Try JSON parsing first (if gobuster was run with json out)
    try:
        data = json.loads(content)
        # Gobuster JSON format handling logic would go here
        # For now, we return empty as MVP
    except json.JSONDecodeError:
        # Fallback to text parsing
        lines = content.splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("="):
                continue
            if line.startswith("/"):
                # e.g., "/admin (Status: 200) [Size: 1234]"
                parts = line.split()
                if len(parts) >= 3 and parts[1].startswith("(Status:"):
                    path = parts[0]
                    status = parts[2].strip(")")
                    results["directories"].append({
                        "path": path,
                        "status": status
                    })
                    
    return results
