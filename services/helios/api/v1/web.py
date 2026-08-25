from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any, Dict, List, Optional
import logging
import uuid

from helios.infrastructure.database import get_db_session
from helios.models.project import Project
from helios.models.finding import Finding
from helios.core.web_security.parsers.zap import parse_zap_xml
from helios.core.web_security.jwt_analyzer import analyze_jwt
from helios.core.web_security.http_analyzer import analyze_http_response
from helios.core.web_security.oauth_analyzer import analyze_oauth_request
from helios.core.web_security.saml_analyzer import analyze_saml_response
from helios.core.web_security.graphql_analyzer import analyze_graphql_schema
from helios.core.web_security.openapi_analyzer import analyze_openapi_spec
from helios.core.web_security.burp_parser import parse_burp_xml
from helios.core.knowledge_graph.builder import sync_finding
from helios.utils.cvss_calculator import calculate_cvss3_base_score
from helios.utils.mitre_attack import technique_for_cwe
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

class JWTAnalyzeRequest(BaseModel):
    token: str

class HTTPAnalyzeRequest(BaseModel):
    headers: dict
    url: str = ""

class OAuthAnalyzeRequest(BaseModel):
    url: str
    params: Optional[Dict[str, str]] = None

class SAMLAnalyzeRequest(BaseModel):
    xml_data: str

class GraphQLAnalyzeRequest(BaseModel):
    graphql_schema: str

class OpenAPIAnalyzeRequest(BaseModel):
    spec_content: str


async def get_project_or_404(project_id: str, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


async def _persist_findings(
    db: AsyncSession, project: Project, findings_data: List[Dict[str, Any]]
) -> List[Finding]:
    """
    Shared persistence path for every web-security analyzer/importer in this
    router: dedup by (project, title), create-or-update the Finding row, and
    best-effort sync the result into the knowledge graph. Centralising this
    means every analyzer gets graph sync and consistent error handling for
    free instead of each endpoint re-implementing (and occasionally
    forgetting) the same dozen lines.
    """
    touched: List[Finding] = []

    for f_data in findings_data:
        # Derive a real CVSS score if the analyzer supplied a vector, and
        # tag a likely ATT&CK technique off the CWE — both best-effort, both
        # skipped silently if the data isn't there rather than guessed.
        cvss_vector = f_data.get("cvss_vector")
        cvss_score = f_data.get("cvss_score")
        if cvss_vector and cvss_score is None:
            computed = calculate_cvss3_base_score(cvss_vector)
            cvss_score = computed if computed > 0 else None

        technique = technique_for_cwe(f_data.get("cwe_id"))
        attack_note = (
            f"\n\n**Likely ATT&CK technique**: {technique['id']} — {technique['name']} ({technique['tactic']})"
            if technique else ""
        )

        result = await db.execute(
            select(Finding).where(
                Finding.project_id == project.id,
                Finding.title == f_data["title"],
            )
        )
        existing = result.scalars().first()

        if existing:
            existing.description = f_data.get("description", existing.description) + attack_note
            existing.severity = f_data.get("severity", existing.severity)
            existing.confidence = f_data.get("confidence", existing.confidence)
            existing.remediation = f_data.get("remediation", existing.remediation)
            existing.impact = f_data.get("impact", existing.impact)
            existing.references_json = f_data.get("references_json", existing.references_json)
            if cvss_vector:
                existing.cvss_vector = cvss_vector
            if cvss_score is not None:
                existing.cvss_score = cvss_score
            touched.append(existing)
        else:
            finding = Finding(
                project_id=project.id,
                title=f_data["title"],
                description=f_data.get("description", "") + attack_note,
                severity=f_data.get("severity", "info"),
                confidence=f_data.get("confidence", "low"),
                status=f_data.get("status", "observed"),
                cwe_id=f_data.get("cwe_id"),
                cvss_vector=cvss_vector,
                cvss_score=cvss_score,
                remediation=f_data.get("remediation"),
                impact=f_data.get("impact"),
                references_json=f_data.get("references_json", []),
            )
            db.add(finding)
            touched.append(finding)

    await db.commit()

    try:
        for finding in touched:
            await sync_finding(db, project.id, finding)
        await db.commit()
    except Exception:
        logger.exception("Knowledge graph sync failed (non-fatal)")
        await db.rollback()

    return touched


@router.post("/ingest/zap", summary="Import an OWASP ZAP XML report")
async def ingest_zap(
    project_id: str = Path(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
):
    if not (file.filename or "").endswith(".xml"):
        raise HTTPException(status_code=400, detail="Must be an XML file")

    project = await get_project_or_404(project_id, db)
    content = await file.read()

    try:
        findings_data = parse_zap_xml(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse ZAP XML: {e}")

    try:
        findings_data = parse_zap_xml(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse ZAP XML: {e}")

    # Fold the target host/port into the description, same as before, before handing off.
    for f_data in findings_data:
        if f_data.get("target_host"):
            f_data["description"] = (
                f"**Target**: {f_data['target_host']}:{f_data.get('target_port', '')}\n\n"
                + f_data["description"]
            )

    try:
        touched = await _persist_findings(db, project, findings_data)
        return {
            "status": "success",
            "message": f"Ingested {len(touched)} findings from ZAP scan.",
        }
    except Exception as e:
        logger.error(f"Failed to ingest ZAP data: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/burp", summary="Import a Burp Suite XML report")
async def ingest_burp(
    project_id: str = Path(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
):
    if not (file.filename or "").endswith(".xml"):
        raise HTTPException(status_code=400, detail="Must be an XML file")

    project = await get_project_or_404(project_id, db)
    content = (await file.read()).decode("utf-8", errors="replace")

    findings_data = parse_burp_xml(content)
    if not findings_data:
        raise HTTPException(status_code=400, detail="No issues found or failed to parse Burp XML")

    try:
        touched = await _persist_findings(db, project, findings_data)
        return {
            "status": "success",
            "message": f"Ingested {len(touched)} findings from Burp scan.",
        }
    except Exception as e:
        logger.error(f"Failed to ingest Burp data: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/jwt", summary="Analyze a JWT for security issues")
async def analyze_jwt_endpoint(
    project_id: str = Path(...),
    request: JWTAnalyzeRequest = ...,
    db: AsyncSession = Depends(get_db_session),
):
    project = await get_project_or_404(project_id, db)
    findings = analyze_jwt(request.token)
    touched = await _persist_findings(db, project, findings)
    return {"status": "success", "findings": findings, "new_findings_count": len(touched)}


@router.post("/analyze/http", summary="Analyze HTTP headers for security issues")
async def analyze_http_endpoint(
    project_id: str = Path(...),
    request: HTTPAnalyzeRequest = ...,
    db: AsyncSession = Depends(get_db_session),
):
    project = await get_project_or_404(project_id, db)
    findings = analyze_http_response(request.headers, request.url)
    touched = await _persist_findings(db, project, findings)
    return {"status": "success", "findings": findings, "new_findings_count": len(touched)}


@router.post("/analyze/oauth", summary="Analyze an OAuth authorization request for security issues")
async def analyze_oauth_endpoint(
    project_id: str = Path(...),
    request: OAuthAnalyzeRequest = ...,
    db: AsyncSession = Depends(get_db_session),
):
    project = await get_project_or_404(project_id, db)
    findings = analyze_oauth_request(request.url, request.params)
    touched = await _persist_findings(db, project, findings)
    return {"status": "success", "findings": findings, "new_findings_count": len(touched)}


@router.post("/analyze/saml", summary="Analyze a SAML response for security issues")
async def analyze_saml_endpoint(
    project_id: str = Path(...),
    request: SAMLAnalyzeRequest = ...,
    db: AsyncSession = Depends(get_db_session),
):
    project = await get_project_or_404(project_id, db)
    findings = analyze_saml_response(request.xml_data)
    touched = await _persist_findings(db, project, findings)
    return {"status": "success", "findings": findings, "new_findings_count": len(touched)}


@router.post("/analyze/graphql", summary="Analyze a GraphQL introspection response for security issues")
async def analyze_graphql_endpoint(
    project_id: str = Path(...),
    request: GraphQLAnalyzeRequest = ...,
    db: AsyncSession = Depends(get_db_session),
):
    project = await get_project_or_404(project_id, db)
    findings = analyze_graphql_schema(request.graphql_schema)
    touched = await _persist_findings(db, project, findings)
    return {"status": "success", "findings": findings, "new_findings_count": len(touched)}


@router.post("/analyze/openapi", summary="Analyze an OpenAPI/Swagger spec for security issues")
async def analyze_openapi_endpoint(
    project_id: str = Path(...),
    request: OpenAPIAnalyzeRequest = ...,
    db: AsyncSession = Depends(get_db_session),
):
    project = await get_project_or_404(project_id, db)
    findings = analyze_openapi_spec(request.spec_content)
    touched = await _persist_findings(db, project, findings)
    return {"status": "success", "findings": findings, "new_findings_count": len(touched)}


@router.get("/findings", summary="List all web security findings for a project")
async def get_findings(
    project_id: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    await get_project_or_404(project_id, db)

    result = await db.execute(
        select(Finding)
        .where(Finding.project_id == project_id)
        .order_by(Finding.created_at.desc())
    )
    findings = result.scalars().all()

    return [
        {
            "id": str(f.id),
            "title": f.title,
            "description": f.description,
            "severity": f.severity,
            "confidence": f.confidence,
            "status": f.status,
            "cwe_id": f.cwe_id,
            "remediation": f.remediation,
            "impact": f.impact,
            "references": f.references_json,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in findings
    ]


@router.delete("/findings/{finding_id}", status_code=204, summary="Delete a finding")
async def delete_finding(
    project_id: str = Path(...),
    finding_id: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Finding).where(
            Finding.id == finding_id,
            Finding.project_id == project_id,
        )
    )
    finding = result.scalars().first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    await db.delete(finding)
    await db.commit()
    return None
