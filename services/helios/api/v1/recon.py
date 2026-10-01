import asyncio
import logging
import re
from datetime import datetime
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Path,
    Query,
    UploadFile,
    status,
)
from pydantic import BaseModel, ConfigDict
from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from helios.core.knowledge_graph.builder import sync_host_with_services
from helios.core.recon.parsers.nmap import parse_nmap_xml
from helios.infrastructure.database import get_db_session
from helios.models.host import Host
from helios.models.project import Project
from helios.models.service import Service
from helios.utils.validators import is_target_in_scope

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
    name: str | None = None
    product: str | None = None
    version: str | None = None
    extrainfo: str | None = None
    banner: str | None = None
    tunnel: str | None = None
    cpe: list[str] = []
    scripts: dict[str, str] = {}

    model_config = ConfigDict(from_attributes=True)


class HostOut(BaseModel):
    id: str
    ip: str
    ipv6: str | None = None
    mac: str | None = None
    vendor: str | None = None
    hostname: str | None = None
    hostnames: list[str] = []
    os: str | None = None
    os_accuracy: int | None = None
    os_family: str | None = None
    os_gen: str | None = None
    os_cpe: list[str] = []
    distance: int | None = None
    uptime: int | None = None
    lastboot: str | None = None
    services: list[ServiceOut] = []
    host_scripts: dict[str, str] = {}
    created_at: datetime | None = None
    updated_at: datetime | None = None

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
    hosts: list[HostOut]


class PluginExecuteRequest(BaseModel):
    payload: dict[str, Any]


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────


async def get_project_or_404(project_id: str, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


def _safe_str(value: Any) -> str | None:
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
    replace_services: bool = Query(
        False, description="Delete existing services before inserting"
    ),
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

    project = await get_project_or_404(project_id, db)
    scope_entries = [
        entry.strip()
        for entry in re.split(r"[,;\n]+", project.scope or "")
        if entry.strip()
    ]
    exclusions = [
        entry.strip()
        for entry in re.split(r"[,;\n]+", project.out_of_scope or "")
        if entry.strip()
    ]
    out_of_scope_hosts = [
        host.get("ip")
        for host in hosts_data
        if host.get("ip")
        and (
            not scope_entries
            or "*" in scope_entries
            or not is_target_in_scope(host["ip"], scope_entries)
            or any(is_target_in_scope(host["ip"], [entry]) for entry in exclusions)
        )
    ]
    if out_of_scope_hosts:
        raise HTTPException(
            status_code=403,
            detail=f"Nmap report contains hosts outside this project's authorized scope: {', '.join(out_of_scope_hosts[:10])}",
        )

    if not hosts_data:
        return IngestSummary(
            project_id=str(project_id),
            project_name="",
            hosts_created=0,
            hosts_updated=0,
            services_created=0,
            services_updated=0,
            total_hosts_in_file=0,
            message="No live hosts with open ports found in the scan",
        )

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
                    host.host_scripts = {
                        **(host.host_scripts or {}),
                        **host_info["host_scripts"],
                    }
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
                        service.scripts = {
                            **(service.scripts or {}),
                            **svc_info["scripts"],
                        }
                    services_updated += 1

        await db.commit()

        # Best-effort knowledge graph sync — never let a graph-sync problem
        # take down a successful ingest. Re-fetch with services eager-loaded
        # since ORM relationship state after commit isn't reliable to reuse.
        try:
            if affected_host_ids:
                synced_hosts = (
                    (
                        await db.execute(
                            select(Host)
                            .where(Host.id.in_(affected_host_ids))
                            .options(selectinload(Host.services))
                        )
                    )
                    .scalars()
                    .all()
                )
                for h in synced_hosts:
                    await sync_host_with_services(db, project.id, h)
                await db.commit()
        except Exception:
            logger.exception(
                "Knowledge graph sync failed after Nmap ingest (non-fatal)"
            )
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

    except Exception:
        await db.rollback()
        logger.exception("Failed to ingest Nmap data")
        raise HTTPException(status_code=500, detail="Database error during ingest")


@router.get(
    "/hosts",
    response_model=HostListResponse,
    summary="List hosts with filtering & pagination",
)
async def get_hosts(
    project_id: str = Path(...),
    ip: str | None = Query(None),
    hostname: str | None = Query(None),
    os: str | None = Query(None),
    port: int | None = Query(None),
    service: str | None = Query(None),
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
            stmt = stmt.where(
                Service.name.ilike(f"%{service}%"), Service.state == "open"
            )
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


@router.get(
    "/hosts/{host_id}", response_model=HostOut, summary="Get a single host by ID"
)
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


@router.delete(
    "/hosts/{host_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a host"
)
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


# ── Plugin routing constants ──────────────────────────────────────────────────

# Host-discovery plugins: output is persisted to Host/Service DB tables.
_HOST_DISCOVERY_PLUGINS = {"nmap"}

# Recon plugins: output returned as structured JSON only.
# (Disabled for first release until persistence and scope logic is implemented for each).
_RECON_PLUGINS = set()

_ALL_SUPPORTED_PLUGINS = _HOST_DISCOVERY_PLUGINS | _RECON_PLUGINS


@router.get("/plugins", summary="List all available recon plugins")
async def list_recon_plugins():
    """Returns all registered plugins and whether their binary is reachable."""
    import shutil

    from helios.infrastructure.plugin_registry import plugin_registry

    plugin_registry.load_all()
    plugins_out = []
    for name in sorted(_ALL_SUPPORTED_PLUGINS):
        plugin = plugin_registry.get_plugin(name)
        if plugin:
            plugins_out.append(
                {
                    "name": plugin.name,
                    "version": plugin.version,
                    "description": plugin.description,
                    "available": shutil.which(plugin.name) is not None,
                    "category": "host_discovery"
                    if name in _HOST_DISCOVERY_PLUGINS
                    else "recon",
                }
            )
    return {"plugins": plugins_out}


@router.post(
    "/plugins/{plugin_name}",
    summary="Execute a recon plugin against an in-scope target",
)
async def execute_recon_plugin(
    project_id: str = Path(...),
    plugin_name: str = Path(...),
    request: PluginExecuteRequest = ...,
    db: AsyncSession = Depends(get_db_session),
):
    from helios.infrastructure.plugin_registry import plugin_registry

    project = await get_project_or_404(project_id, db)
    plugin_name_lower = plugin_name.lower()

    if plugin_name_lower not in _ALL_SUPPORTED_PLUGINS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Unknown plugin '{plugin_name}'. "
                f"Supported: {sorted(_ALL_SUPPORTED_PLUGINS)}"
            ),
        )

    target = str(request.payload.get("target", "")).strip()
    if not target or any(char in target for char in "\r\n\x00"):
        raise HTTPException(
            status_code=400,
            detail="Provide one IP address or domain as the scan target.",
        )

    # Scanning is permitted only when both the submitted target and project
    # scope are explicit. A target may be a single host, never a free-form flag.
    scope_entries = [
        entry.strip()
        for entry in re.split(r"[,;\n]+", project.scope or "")
        if entry.strip()
    ]
    if (
        not scope_entries
        or "*" in scope_entries
        or not is_target_in_scope(target, scope_entries)
    ):
        raise HTTPException(
            status_code=403,
            detail="Target is not within this project's authorized scope.",
        )
    if any(
        is_target_in_scope(target, [entry])
        for entry in re.split(r"[,;\n]+", project.out_of_scope or "")
        if entry.strip()
    ):
        raise HTTPException(
            status_code=403,
            detail="Target is explicitly excluded by this project's scope.",
        )

    plugin_registry.load_all()
    plugin = plugin_registry.get_plugin(plugin_name_lower)
    if not plugin:
        raise HTTPException(
            status_code=404, detail=f"Plugin '{plugin_name}' not found in registry"
        )

    try:
        # Build execution payload.
        # Nmap: locked-down args, no user-supplied flags.
        # All other plugins: pass the full validated payload.
        if plugin_name_lower == "nmap":
            exec_payload = {"target": target, "args": "-sV --top-ports 100"}
        else:
            exec_payload = {**request.payload, "target": target}

        result = await asyncio.to_thread(plugin.execute, exec_payload)

        if result.get("status") == "error":
            raise HTTPException(
                status_code=502, detail=result.get("error", "Plugin execution failed")
            )

        # ── nmap: persist Host/Service rows to the database ──────────────────
        if plugin_name_lower in _HOST_DISCOVERY_PLUGINS:
            hosts_created = hosts_updated = services_created = services_updated = 0
            affected_host_ids: set[str] = set()

            for host_data in result.get("hosts", []):
                ip = host_data.get("ip")
                if not ip:
                    continue
                host_result = await db.execute(
                    select(Host).where(Host.project_id == project.id, Host.ip == ip)
                )
                host = host_result.scalars().first()
                if host is None:
                    host = Host(
                        project_id=project.id,
                        ip=ip,
                        hostname=host_data.get("hostname"),
                        hostnames=[host_data["hostname"]]
                        if host_data.get("hostname")
                        else [],
                    )
                    db.add(host)
                    hosts_created += 1
                else:
                    if host_data.get("hostname"):
                        host.hostname = host_data["hostname"]
                    hosts_updated += 1
                await db.flush()
                affected_host_ids.add(host.id)

                for service_data in host_data.get("ports", []):
                    port = service_data.get("port")
                    protocol = service_data.get("protocol") or "tcp"
                    if not port:
                        continue
                    svc_result = await db.execute(
                        select(Service).where(
                            Service.host_id == host.id,
                            Service.port == port,
                            Service.protocol == protocol,
                        )
                    )
                    service = svc_result.scalars().first()
                    values = {
                        "name": service_data.get("service"),
                        "product": service_data.get("product"),
                        "version": service_data.get("version"),
                        "extrainfo": service_data.get("extrainfo"),
                        "state": "open",
                    }
                    if service is None:
                        db.add(
                            Service(
                                host_id=host.id, port=port, protocol=protocol, **values
                            )
                        )
                        services_created += 1
                    else:
                        for key, value in values.items():
                            if value is not None:
                                setattr(service, key, value)
                        services_updated += 1

            await db.commit()

            try:
                if affected_host_ids:
                    synced_hosts = (
                        (
                            await db.execute(
                                select(Host)
                                .where(Host.id.in_(affected_host_ids))
                                .options(selectinload(Host.services))
                            )
                        )
                        .scalars()
                        .all()
                    )
                    for host in synced_hosts:
                        await sync_host_with_services(db, project.id, host)
                    await db.commit()
            except Exception:
                logger.exception("Knowledge graph sync failed after scan (non-fatal)")
                await db.rollback()

            return {
                "plugin": plugin_name,
                "version": plugin.version,
                "result": {
                    "status": "completed",
                    "hosts_found": len(result.get("hosts", [])),
                    "hosts_created": hosts_created,
                    "hosts_updated": hosts_updated,
                    "services_created": services_created,
                    "services_updated": services_updated,
                },
            }

        # ── All other recon plugins: return structured JSON result directly ──
        return {
            "plugin": plugin_name,
            "version": plugin.version,
            "result": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Plugin {plugin_name} execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error during plugin execution"
        )
