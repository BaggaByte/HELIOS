import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def parse_whatweb(content: str) -> Dict[str, Any]:
    """
    Parses WhatWeb JSON output.
    Returns structured host and web service data.
    """
    results = {
        "hosts": []
    }
    
    try:
        data = json.loads(content)
        for item in data:
            target = item.get("target", "")
            if not target:
                continue
                
            ip = item.get("ip") or target.replace("https://", "").replace("http://", "").split(":")[0]
            
            plugins = item.get("plugins", {})
            tech_list = list(plugins.keys())
            
            title = ""
            if "Title" in plugins and "string" in plugins["Title"]:
                title = plugins["Title"]["string"][0]
                
            web_server = ""
            if "HTTPServer" in plugins and "string" in plugins["HTTPServer"]:
                web_server = plugins["HTTPServer"]["string"][0]
                
            port = 80
            if target.startswith("https://"):
                port = 443
            elif ":" in target.replace("https://", "").replace("http://", ""):
                try:
                    port = int(target.split(":")[-1].split("/")[0])
                except:
                    pass
            
            banner = f"Title: {title}\n"
            if web_server:
                banner += f"Web Server: {web_server}\n"
            if tech_list:
                banner += f"Tech Stack: {', '.join(tech_list)}"
                
            results["hosts"].append({
                "ip": ip,
                "hostnames": [],
                "ports": [{
                    "port": port,
                    "protocol": "tcp",
                    "state": "open",
                    "service": "https" if target.startswith("https") else "http",
                    "product": web_server,
                    "banner": banner,
                    "extrainfo": f"Status: {item.get('http_status', 'unknown')}"
                }]
            })
            
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse WhatWeb JSON: {e}")
        
    return results