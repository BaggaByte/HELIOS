import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def parse_dirsearch(content: str) -> Dict[str, Any]:
    """
    Parses Dirsearch JSON output.
    Returns a list of discovered directories/files.
    """
    results = {
        "directories": []
    }
    
    try:
        data = json.loads(content)
        # Dirsearch outputs a dict where keys are URLs (targets) and values are lists of findings
        for target_url, findings in data.items():
            if isinstance(findings, list):
                for item in findings:
                    results["directories"].append({
                        "path": item.get("path"),
                        "status": item.get("status"),
                        "content_length": item.get("content-length"),
                        "redirect": item.get("redirect")
                    })
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse Dirsearch JSON: {e}")
        
    return results