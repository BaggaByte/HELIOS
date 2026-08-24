import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class AttackSurfaceAnalyzer:
    """
    Analyzes raw parsed recon data (hosts, ports, services) and identifies
    the potential attack surface (e.g., exposed admin panels, vulnerable versions).
    """
    
    def __init__(self):
        self.high_value_ports = {21, 22, 23, 139, 445, 1433, 3306, 3389, 5432, 5900, 6379}
        
    def analyze_host(self, host_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes a single host dictionary and tags interesting features.
        """
        attack_surface = {
            "exposed_high_value_ports": [],
            "potential_web_services": [],
            "outdated_services": []
        }
        
        ports = host_data.get("ports", [])
        for port_info in ports:
            port_num = port_info.get("port")
            service = port_info.get("service", "").lower()
            
            # 1. High value ports
            if port_num in self.high_value_ports:
                attack_surface["exposed_high_value_ports"].append(port_num)
                
            # 2. Web services
            if "http" in service or port_num in [80, 443, 8080, 8443]:
                attack_surface["potential_web_services"].append(port_num)
                
            # 3. Very basic outdated heuristics (MVP)
            version = port_info.get("version", "").lower()
            if "apache 2.2" in version or "iis 6" in version or "openssh 4" in version:
                attack_surface["outdated_services"].append(f"{service} ({version})")
                
        return attack_surface
        
analyzer = AttackSurfaceAnalyzer()
