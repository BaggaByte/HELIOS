import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def parse_httpx(content: str) -> Dict[str, Any]:
    """
    Parses HTTPx JSONL output.
    Returns structured host and web service data.
    """
    results = {
        "hosts": []
    }
    
    hosts_map = {}
    
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
            
        try:
            data = json.loads(line)
            
            ip = data.get("host") # HTTPx host is often IP if run directly against IPs
            if not ip:
                ip = data.get("url", "").replace("https://", "").replace("http://", "").split(":")[0]
                
            if not ip:
                continue
                
            if ip not in hosts_map:
                hosts_map[ip] = {
                    "ip": ip,
                    "hostnames": [],
                    "ports": []
                }
                
            port = data.get("port")
            if port:
                try:
                    port = int(port)
                except ValueError:
                    port = 80
                    
                tech = data.get("tech", [])
                web_server = data.get("webserver", "")
                title = data.get("title", "")
                
                banner = f"Title: {title}\n"
                if web_server:
                    banner += f"Web Server: {web_server}\n"
                if tech:
                    banner += f"Tech Stack: {', '.join(tech)}"
                
                service_info = {
                    "port": port,
                    "protocol": "tcp",
                    "state": "open",
                    "service": "http" if data.get("scheme") == "http" else "https",
                    "product": web_server,
                    "banner": banner,
                    "extrainfo": f"Status: {data.get('status_code', 'unknown')}"
                }
                hosts_map[ip]["ports"].append(service_info)
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse HTTPx JSON line: {e}")
            continue
            
    results["hosts"] = list(hosts_map.values())
    return results