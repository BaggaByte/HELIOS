import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RiskPrioritizer:
    """
    Assigns risk scores and severity levels to discovered assets based on
    exposed services and identified vulnerabilities.
    """
    
    def calculate_risk(self, host_data: Dict[str, Any], attack_surface: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates a mock CVSS-style risk score (0-10) and assigns a severity.
        """
        score = 0.0
        
        # Base scoring heuristics
        if attack_surface.get("exposed_high_value_ports"):
            score += 3.5
            
        if attack_surface.get("outdated_services"):
            score += 4.5
            
        if attack_surface.get("potential_web_services"):
            score += 1.0
            
        # Cap at 10.0
        score = min(score, 10.0)
        
        # Determine Severity
        if score >= 9.0:
            severity = "Critical"
        elif score >= 7.0:
            severity = "High"
        elif score >= 4.0:
            severity = "Medium"
        elif score > 0:
            severity = "Low"
        else:
            severity = "Info"
            
        return {
            "risk_score": round(score, 1),
            "severity": severity
        }

prioritizer = RiskPrioritizer()
