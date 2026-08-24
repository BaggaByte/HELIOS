from typing import Any, List, Dict
from datetime import datetime

def generate_markdown_report(project: Any, findings: List[Any], risk_data: Dict[str, Any], ai_summary: str = "") -> str:
    """Generates a comprehensive Markdown report from project data."""
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    
    # 1. Title Page & Header
    md = f"# Penetration Testing Report\n\n"
    md += f"**Project Name:** {project.name}\n"
    md += f"**Date:** {date_str}\n"
    md += f"**Overall Risk Rating:** {risk_data['level']}\n\n"
    md += "---\n\n"
    
    # 2. Executive Summary (AI Generated if available)
    md += "## 1. Executive Summary\n\n"
    if ai_summary:
        md += f"{ai_summary}\n\n"
    else:
        md += f"This report details the findings from the security assessment of {project.name}. "
        md += f"A total of {len(findings)} vulnerabilities were discovered, with a maximum CVSS score of {risk_data.get('max_cvss', 'N/A')}.\n\n"
        
    # 3. Scope
    md += "## 2. Project Scope\n\n"
    md += f"{project.scope}\n\n"
    if hasattr(project, 'out_of_scope') and project.out_of_scope:
        md += f"**Out of Scope:**\n{project.out_of_scope}\n\n"
        
    # 4. Findings Summary
    md += "## 3. Findings Summary\n\n"
    md += "| Severity | Count |\n|---|---|\n"
    for sev in ["critical", "high", "medium", "low", "info"]:
        md += f"| {sev.capitalize()} | {risk_data['counts'].get(sev, 0)} |\n"
    md += "\n"
    
    # 5. Technical Details
    md += "## 4. Technical Findings\n\n"
    if not findings:
        md += "No vulnerabilities were identified during this assessment.\n\n"
    else:
        for idx, f in enumerate(findings, 1):
            sev_color = "🔴" if f.severity == "critical" else "🟠" if f.severity == "high" else "🟡" if f.severity == "medium" else "🔵"
            md += f"### {idx}. {sev_color} {f.title}\n\n"
            md += f"**Severity:** {f.severity.capitalize()} | **Confidence:** {f.confidence.capitalize()} | **CVSS:** {f.cvss_score or 'N/A'}\n\n"
            
            md += f"#### Description\n{f.description}\n\n"
            
            if hasattr(f, 'impact') and f.impact:
                md += f"#### Impact\n{f.impact}\n\n"
                
            if hasattr(f, 'remediation') and f.remediation:
                md += f"#### Remediation\n{f.remediation}\n\n"
                
            # Note: Evidence linking would go here, but since evidence is stored locally
            # we'll just note if evidence exists.
            if hasattr(f, 'evidence') and f.evidence:
                md += f"#### Evidence\n"
                md += f"*Attached {len(f.evidence)} evidence items.*\n\n"
                
            md += "---\n\n"
            
    # 6. Appendix
    md += "## 5. Appendix\n\n"
    md += "Report generated automatically by HELIOS Offensive Security Engine.\n"
    
    return md
