import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def parse_nikto(content: str) -> Dict[str, Any]:
    """
    Parses Nikto JSON output.
    Returns structured vulnerability findings.
    """
    results = {
        "findings": []
    }
    
    try:
        data = json.loads(content)
        
        for vulnerability in data.get("vulnerabilities", []):
            results["findings"].append({
                "title": vulnerability.get("id", "Nikto Finding"),
                "description": vulnerability.get("msg", ""),
                "severity": "MEDIUM", # Nikto doesn't give a clear severity, default to Medium
                "confidence": "LOW", # Nikto is known for false positives
                "host": data.get("host", ""),
                "method": vulnerability.get("method", ""),
                "url": vulnerability.get("url", ""),
            })
            
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse Nikto JSON: {e}")
        
    return results