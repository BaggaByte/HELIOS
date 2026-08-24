from typing import List, Dict, Any

def calculate_project_risk(findings: List[Any]) -> Dict[str, Any]:
    """
    Calculates the overall project risk based on findings.
    """
    if not findings:
        return {
            "level": "Low",
            "score": 0.0,
            "counts": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        }
        
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    max_score = 0.0
    total_score = 0.0
    
    for f in findings:
        sev = f.severity.lower() if f.severity else "info"
        if sev in counts:
            counts[sev] += 1
            
        score = float(f.cvss_score) if f.cvss_score else 0.0
        max_score = max(max_score, score)
        total_score += score
        
    # Simple logic for overall level
    if counts["critical"] > 0:
        level = "Critical"
    elif counts["high"] > 0:
        level = "High"
    elif counts["medium"] > 0:
        level = "Medium"
    else:
        level = "Low"
        
    avg_score = total_score / len(findings) if findings else 0.0
        
    return {
        "level": level,
        "max_cvss": round(max_score, 1),
        "avg_cvss": round(avg_score, 1),
        "counts": counts
    }
