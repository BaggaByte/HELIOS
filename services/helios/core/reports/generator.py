from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import uuid

from helios.models.project import Project
from helios.models.finding import Finding
from helios.core.reports.risk_calculator import calculate_project_risk
from helios.core.reports.formatters.markdown import generate_markdown_report

async def generate_report(db: AsyncSession, project_id: uuid.UUID, include_ai_summary: bool = False) -> str:
    """
    Orchestrates the report generation process.
    """
    # 1. Fetch Project
    result = await db.execute(select(Project).filter_by(id=project_id))
    project = result.scalars().first()
    
    if not project:
        raise ValueError("Project not found.")
        
    # 2. Fetch Findings with Evidence
    result = await db.execute(
        select(Finding)
        .filter_by(project_id=project_id)
        .options(selectinload(Finding.evidence))
        .order_by(Finding.severity.desc()) # Order by severity (needs custom sort ideally, but this is simple)
    )
    findings = result.scalars().all()
    
    # Sort findings properly: Critical > High > Medium > Low > Info
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    findings = sorted(findings, key=lambda f: severity_order.get(f.severity.lower() if f.severity else "info", 5))
    
    # 3. Calculate Risk
    risk_data = calculate_project_risk(findings)
    
    # 4. Generate AI Summary (Mocked for now, would call ChatEngine)
    ai_summary = ""
    if include_ai_summary:
        ai_summary = (
            "**AI Executive Summary:**\n"
            f"Based on the analysis of {len(findings)} findings, the overall risk posture is considered **{risk_data['level']}**. "
            "Immediate attention is required for the critical vulnerabilities identified in the core application logic."
        )
        
    # 5. Format to Markdown
    report_md = generate_markdown_report(project, findings, risk_data, ai_summary)
    
    return report_md
