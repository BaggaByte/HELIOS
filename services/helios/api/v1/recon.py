from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, status, Path, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import uuid

from helios.infrastructure.database import get_db_session
from helios.models.project import Project
from helios.models.host import Host
from helios.models.service import Service
from helios.core.recon.parsers.nmap import parse_nmap_xml
from helios.core.knowledge_graph.builder import sync_host_with_services

logger = logging.getLogger(__name__)
router = APIRouter()


# ──────────────────────────────────────────────────────────────
# Pydantic Schemas
# ──────────────────────────────────────────────────────────────

class ServiceOut(BaseModel):
    id: str
    port: int
    protocol: str
    state: str
    name: Optional[str] = None
    product: Optional[str] = None
    version: Optional[str] = None
    extrainfo: Optional[str] = None
    banner: Optional[str] = None
    tunnel: Optional[str] = None
    cpe: List[str] = []
    scripts: Dict[str, str] = {}

    model_config = ConfigDict(from_attributes=True)


class HostOut(BaseModel):
    id: str
    ip: str
    ipv6: Optional[str] = None
    mac: Optional[str] = None
    vendor: Optional[str] = None
    hostname: Optional[str] = None
    hostnames: List[str] = []
    os: Optional[str] = None
    os_accuracy: Optional[int] = None
    os_family: Optional[str] = None
    os_gen: Optional[str] = None
    os_cpe: List[str] = []
    distance: Optional[int] = None
    uptime: Optional[int] = None
    lastboot: Optional[str] = None
    services: List[ServiceOut] = []
    host_scripts: Dict[str, str] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class IngestSummary(BaseModel):
    status: str = "success"
    project_id: str
    project_name: str
    hosts_created: int
    hosts_updated: int
    services_created: int
    services_updated: int
    total_hosts_in_file: int
    message: str


class HostListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    hosts: List[HostOut]


class PluginExecuteRequest(BaseModel):
    payload: Dict[str, Any]


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

async def get_project_or_404(project_id: str, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


def _safe_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)[:512]


def _serialize_host(h: Host) -> HostOut:
    return HostOut(
        id=str(h.id),
        ip=h.ip,
        ipv6=getattr(h, "ipv6", None),
        mac=getattr(h, "mac", None),
        vendor=getattr(h, "vendor", None),
        hostname=h.hostname,
        hostnames=getattr(h, "hostnames", None) or [],
        os=h.os,
        os_accuracy=getattr(h, "os_accuracy", None),
        os_family=getattr(h, "os_family", None),
        os_gen=getattr(h, "os_gen", None),
        os_cpe=getattr(h, "os_cpe", None) or [],
        distance=getattr(h, "distance", None),
        uptime=getattr(h, "uptime", None),
        lastboot=getattr(h, "lastboot", None),
        host_scripts=getattr(h, "host_scripts", None) or {},
        created_at=getattr(h, "created_at", None),
        updated_at=getattr(h, "updated_at", None),
        services=[
            ServiceOut(
                id=str(s.id),
                port=s.port,
                protocol=s.protocol,
                state=s.state or "open",
                name=s.name,
                product=getattr(s, "product", None),
                version=s.version,
                extrainfo=getattr(s, "extrainfo", None),
                banner=getattr(s, "banner", None),
                tunnel=getattr(s, "tunnel", None),
                cpe=getattr(s, "cpe", None) or [],
                scripts=getattr(s, "scripts", None) or {},
            )
            for s in h.services
        ],
    )


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────

@router.post(
    "/ingest/nmap",
    response_model=IngestSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Nmap XML scan results",
)
async def ingest_nmap(
    project_id: str = Path(...),
    file: UploadFile = File(..., description="Nmap XML output file"),
    only_open: bool = Query(True, description="Only ingest hosts that have open ports"),
    replace_services: bool = Query(False, description="Delete existing services before inserting"),
    db: AsyncSession = Depends(get_db_session),
):
    if not file.filename or not file.filename.lower().endswith(".xml"):
        raise HTTPException(status_code=400, detail="File must have a .xml extension")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        hosts_data = parse_nmap_xml(content, only_open=only_open)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid Nmap XML: {e}")
    except Exception:
        logger.exception("Unexpected error parsing Nmap XML")
        raise HTTPException(status_code=500, detail="Failed to parse Nmap XML")

    if not hosts_data:
        return IngestSummary(
            project_id=str(project_id),
            project_name="",
            hosts_created=0, hosts_updated=0,
            services_created=0, services_updated=0,
            total_hosts_in_file=0,
            message="No live hosts with open ports found in the scan",
        )

    project = await get_project_or_404(project_id, db)
    hosts_created = hosts_updated = services_created = services_updated = 0

    affected_host_ids: set[str] = set()

    try:
        for host_info in hosts_data:
            ip = host_info.get("ip")
            if not ip:
                continue

            result = await db.execute(
                select(Host).where(and_(Host.project_id == project.id, Host.ip == ip))
            )
            host = result.scalars().first()

            primary_hostname = None
            hostnames = host_info.get("hostnames") or []
            if hostnames:
                primary_hostname = hostnames[0]
            elif host_info.get("hostname"):
                primary_hostname = host_info["hostname"]

            if not host:
                host = Host(
                    project_id=project.id,
                    ip=ip,
                    ipv6=host_info.get("ipv6"),
                    mac=host_info.get("mac"),
                    vendor=_safe_str(host_info.get("vendor")),
                    hostname=primary_hostname,
                    hostnames=hostnames,
                    os=_safe_str(host_info.get("os")),
                    os_accuracy=host_info.get("os_accuracy"),
                    os_family=_safe_str(host_info.get("os_family")),
                    os_gen=_safe_str(host_info.get("os_gen")),
                    os_cpe=host_info.get("os_cpe") or [],
                    distance=host_info.get("distance"),
                    uptime=host_info.get("uptime"),
                    lastboot=_safe_str(host_info.get("lastboot")),
                    host_scripts=host_info.get("host_scripts") or {},
                )
                db.add(host)
                hosts_created += 1
            else:
                host.ipv6 = host_info.get("ipv6") or host.ipv6
                host.mac = host_info.get("mac") or host.mac
                host.vendor = _safe_str(host_info.get("vendor")) or host.vendor
                if primary_hostname:
                    host.hostname = primary_hostname
                if hostnames:
                    host.hostnames = hostnames
                if host_info.get("os"):
                    host.os = _safe_str(host_info["os"])
                    host.os_accuracy = host_info.get("os_accuracy")
                    host.os_family = _safe_str(host_info.get("os_family"))
                    host.os_gen = _safe_str(host_info.get("os_gen"))
                    host.os_cpe = host_info.get("os_cpe") or host.os_cpe
                host.distance = host_info.get("distance") or host.distance
                host.uptime = host_info.get("uptime") or host.uptime
                host.lastboot = _safe_str(host_info.get("lastboot")) or host.lastboot
                if host_info.get("host_scripts"):
                    host.host_scripts = {**(host.host_scripts or {}), **host_info["host_scripts"]}
                hosts_updated += 1

            await db.flush()
            affected_host_ids.add(host.id)

            if replace_services:
                await db.execute(delete(Service).where(Service.host_id == host.id))
                await db.flush()

            for svc_info in host_info.get("services", []):
                port = svc_info.get("port")
                protocol = svc_info.get("protocol", "tcp")
                if port is None:
                    continue

                result = await db.execute(
                    select(Service).where(
                        and_(
                            Service.host_id == host.id,
                            Service.port == port,
                            Service.protocol == protocol,
                        )
                    )
                )
                service = result.scalars().first()
                version_str = svc_info.get("version_string") or svc_info.get("version")

                if not service:
                    service = Service(
                        host_id=host.id,
                        port=port,
                        protocol=protocol,
                        state=svc_info.get("state", "open"),
                        name=_safe_str(svc_info.get("name")),
                        product=_safe_str(svc_info.get("product")),
                        version=_safe_str(version_str),
                        extrainfo=_safe_str(svc_info.get("extrainfo")),
                        banner=_safe_str(svc_info.get("banner")),
                        tunnel=_safe_str(svc_info.get("tunnel")),
                        cpe=svc_info.get("cpe") or [],
                        scripts=svc_info.get("scripts") or {},
                    )
                    db.add(service)
                    services_created += 1
                else:
                    service.state = svc_info.get("state", service.state)
                    if svc_info.get("name"):
                        service.name = _safe_str(svc_info["name"])
                    if svc_info.get("product"):
                        service.product = _safe_str(svc_info["product"])
                    if version_str:
                        service.version = _safe_str(version_str)
                    if svc_info.get("extrainfo"):
                        service.extrainfo = _safe_str(svc_info["extrainfo"])
                    if svc_info.get("banner"):
                        service.banner = _safe_str(svc_info["banner"])
                    if svc_info.get("tunnel"):
                        service.tunnel = _safe_str(svc_info["tunnel"])
                    if svc_info.get("cpe"):
                        service.cpe = svc_info["cpe"]
                    if svc_info.get("scripts"):
                        service.scripts = {**(service.scripts or {}), **svc_info["scripts"]}
                    services_updated += 1

        await db.commit()

        # Best-effort knowledge graph sync — never let a graph-sync problem
        # take down a successful ingest. Re-fetch with services eager-loaded
        # since ORM relationship state after commit isn't reliable to reuse.
        try:
            if affected_host_ids:
                synced_hosts = (
                    await db.execute(
                        select(Host)
                        .where(Host.id.in_(affected_host_ids))
                        .options(selectinload(Host.services))
                    )
                ).scalars().all()
                for h in synced_hosts:
                    await sync_host_with_services(db, project.id, h)
                await db.commit()
        except Exception:
            logger.exception("Knowledge graph sync failed after Nmap ingest (non-fatal)")
            await db.rollback()

        msg = (
            f"Ingested into project '{project.name}': "
            f"{hosts_created} new hosts, {hosts_updated} updated, "
            f"{services_created} new services, {services_updated} updated."
        )
        logger.info(msg)

        return IngestSummary(
            project_id=str(project.id),
            project_name=project.name,
            hosts_created=hosts_created,
            hosts_updated=hosts_updated,
            services_created=services_created,
            services_updated=services_updated,
            total_hosts_in_file=len(hosts_data),
            message=msg,
        )

    except Exception as e:
        await db.rollback()
        logger.exception("Failed to ingest Nmap data")
        raise HTTPException(status_code=500, detail=f"Database error during ingest: {str(e)}")


@router.get("/hosts", response_model=HostListResponse, summary="List hosts with filtering & pagination")
async def get_hosts(
    project_id: str = Path(...),
    ip: Optional[str] = Query(None),
    hostname: Optional[str] = Query(None),
    os: Optional[str] = Query(None),
    port: Optional[int] = Query(None),
    service: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db_session),
):
    project = await get_project_or_404(project_id, db)

    stmt = (
        select(Host)
        .where(Host.project_id == project.id)
        .options(selectinload(Host.services))
    )

    if ip:
        stmt = stmt.where(Host.ip == ip)
    if hostname:
        stmt = stmt.where(Host.hostname.ilike(f"%{hostname}%"))
    if os:
        stmt = stmt.where(Host.os.ilike(f"%{os}%"))
    if port is not None or service:
        stmt = stmt.join(Service)
        if port is not None:
            stmt = stmt.where(Service.port == port, Service.state == "open")
        if service:
            stmt = stmt.where(Service.name.ilike(f"%{service}%"), Service.state == "open")
        stmt = stmt.distinct()

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(Host.ip).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    hosts = result.scalars().unique().all()

    return HostListResponse(
        total=total,
        page=page,
        page_size=page_size,
        hosts=[_serialize_host(h) for h in hosts],
    )


@router.get("/hosts/{host_id}", response_model=HostOut, summary="Get a single host by ID")
async def get_host(
    project_id: str = Path(...),
    host_id: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Host)
        .where(Host.id == host_id, Host.project_id == project_id)
        .options(selectinload(Host.services))
    )
    host = result.scalars().first()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    return _serialize_host(host)


@router.delete("/hosts/{host_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a host")
async def delete_host(
    project_id: str = Path(...),
    host_id: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Host).where(Host.id == host_id, Host.project_id == project_id)
    )
    host = result.scalars().first()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    await db.delete(host)
    await db.commit()
    return None


@router.post("/plugins/{plugin_name}", summary="Execute a recon plugin in the background")
def execute_recon_plugin(
    project_id: str = Path(...),
    plugin_name: str = Path(...),
    request: PluginExecuteRequest = ...,
    background_tasks: BackgroundTasks = ...,
):
    from helios.infrastructure.plugin_registry import plugin_registry

    plugin_registry.load_all()
    plugin = plugin_registry.get_plugin(plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found")

    async def run_and_persist():
        try:
            # We must create a new session for the background task
            from helios.infrastructure.database import async_session_maker
            from helios.models.finding import Finding
            from helios.models.host import Host
            from sqlalchemy.future import select
            
            result = plugin.execute(request.payload)
            if "error" in result:
                logger.error(f"Plugin {plugin_name} error: {result['error']}")
                return

            parsed_data = result.get("parsed_data", {})
            
            async with async_session_maker() as db:
                if "findings" in parsed_data:
                    for f_data in parsed_data["findings"]:
                        finding = Finding(
                            project_id=project_id,
                            title=f_data.get("title", "Unknown"),
                            description=f_data.get("description", ""),
                            severity=f_data.get("severity", "INFO"),
                            confidence=f_data.get("confidence", "HIGH"),
                            cwe_id=f_data.get("cwe_id"),
                            cvss_score=f_data.get("cvss_score"),
                            cvss_vector=f_data.get("cvss_metrics"),
                            remediation=f_data.get("remediation"),
                            references_json=f_data.get("references", [])
                        )
                        db.add(finding)
                
                if "subdomains" in parsed_data:
                    for s_data in parsed_data["subdomains"]:
                        host_name = s_data.get("host")
                        if host_name:
                            # Create or update host
                            h_res = await db.execute(select(Host).where(Host.project_id == project_id, Host.hostname == host_name))
                            host = h_res.scalars().first()
                            if not host:
                                host = Host(project_id=project_id, ip=s_data.get("ip") or "", hostname=host_name, hostnames=[host_name])
                                db.add(host)
                
                if "directories" in parsed_data:
                    for d_data in parsed_data["directories"]:
                        finding = Finding(
                            project_id=project_id,
                            title=f"Endpoint Discovered: {d_data.get('path')}",
                            description=f"Status: {d_data.get('status', 'unknown')}",
                            severity="INFO",
                            confidence="HIGH"
                        )
                        db.add(finding)
                        
                if "hosts" in parsed_data:
                    from helios.models.service import Service
                    for h_data in parsed_data["hosts"]:
                        ip = h_data.get("ip")
                        if not ip:
                            continue
                        # Create or update host
                        h_res = await db.execute(select(Host).where(Host.project_id == project_id, Host.ip == ip))
                        host = h_res.scalars().first()
                        if not host:
                            host = Host(project_id=project_id, ip=ip)
                            db.add(host)
                            await db.flush() # Need host.id
                            
                        for p_data in h_data.get("ports", []):
                            port = p_data.get("port")
                            protocol = p_data.get("protocol", "tcp")
                            s_res = await db.execute(select(Service).where(Service.host_id == host.id, Service.port == port, Service.protocol == protocol))
                            service = s_res.scalars().first()
                            if not service:
                                service = Service(
                                    host_id=host.id,
                                    port=port,
                                    protocol=protocol,
                                    state=p_data.get("state", "open"),
                                    service=p_data.get("service"),
                                    product=p_data.get("product"),
                                    banner=p_data.get("banner"),
                                    extrainfo=p_data.get("extrainfo")
                                )
                                db.add(service)
                        
                await db.commit()
                logger.info(f"Plugin {plugin_name} completed and persisted data.")
                
        except Exception as e:
            logger.error(f"Background task for {plugin_name} failed: {e}")

    try:
        background_tasks.add_task(run_and_persist)
        return {
            "plugin": plugin_name,
            "version": plugin.version,
            "result": {"status": "started", "message": "Scan started in background"},
        }
    except Exception as e:
        logger.error(f"Plugin {plugin_name} failed to schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))
