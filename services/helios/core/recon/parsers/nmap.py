import xml.etree.ElementTree as ET
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Service:
    port: int
    protocol: str
    state: str = "open"
    name: Optional[str] = None
    product: Optional[str] = None
    version: Optional[str] = None
    extrainfo: Optional[str] = None
    tunnel: Optional[str] = None          # e.g. ssl
    method: Optional[str] = None          # e.g. probed
    conf: Optional[int] = None            # confidence
    cpe: List[str] = field(default_factory=list)
    scripts: Dict[str, str] = field(default_factory=dict)  # script_id -> output
    banner: Optional[str] = None

    @property
    def version_string(self) -> str:
        parts = [p for p in (self.product, self.version, self.extrainfo) if p]
        return " ".join(parts).strip()


@dataclass
class Host:
    ip: str
    ipv6: Optional[str] = None
    mac: Optional[str] = None
    vendor: Optional[str] = None
    hostnames: List[str] = field(default_factory=list)
    status: str = "up"
    reason: Optional[str] = None
    os: Optional[str] = None
    os_accuracy: Optional[int] = None
    os_family: Optional[str] = None
    os_gen: Optional[str] = None
    os_cpe: List[str] = field(default_factory=list)
    services: List[Service] = field(default_factory=list)
    host_scripts: Dict[str, str] = field(default_factory=dict)  # host-level scripts
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    distance: Optional[int] = None          # hop distance
    uptime: Optional[int] = None            # seconds
    lastboot: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _safe_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _parse_timestamp(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(int(ts))
    except (ValueError, TypeError, OSError):
        return None


def parse_nmap_xml(
    xml_content: Union[bytes, str],
    *,
    include_closed: bool = False,
    include_filtered: bool = False,
    only_open: bool = True,
) -> List[Dict[str, Any]]:
    """
    Advanced Nmap XML parser.

    Parameters
    ----------
    xml_content : bytes | str
        Raw Nmap XML output.
    include_closed : bool
        Include ports in 'closed' state.
    include_filtered : bool
        Include ports in 'filtered' / 'open|filtered' states.
    only_open : bool
        If True (default), only return hosts that have at least one open port.
        Set to False to include up hosts with no open ports.

    Returns
    -------
    List[Dict[str, Any]]
        List of host dictionaries (JSON-serializable).
    """
    if isinstance(xml_content, str):
        xml_content = xml_content.encode("utf-8", errors="replace")

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        logger.error("XML parse error: %s", e)
        raise ValueError(f"Invalid Nmap XML: {e}") from e

    # Optional: scan metadata
    scan_info = {
        "scanner": root.get("scanner"),
        "args": root.get("args"),
        "start": _parse_timestamp(root.get("start")),
        "version": root.get("version"),
        "xmloutputversion": root.get("xmloutputversion"),
    }

    hosts: List[Host] = []

    for host_elem in root.findall("host"):
        # ----- Status -----
        status_elem = host_elem.find("status")
        if status_elem is None:
            continue
        state = status_elem.get("state", "unknown")
        if state != "up":
            continue

        # ----- Addresses -----
        ipv4 = None
        ipv6 = None
        mac = None
        vendor = None

        for addr in host_elem.findall("address"):
            addrtype = addr.get("addrtype")
            addr_val = addr.get("addr")
            if addrtype == "ipv4":
                ipv4 = addr_val
            elif addrtype == "ipv6":
                ipv6 = addr_val
            elif addrtype == "mac":
                mac = addr_val
                vendor = addr.get("vendor")

        if not ipv4 and not ipv6:
            continue  # no usable address

        primary_ip = ipv4 or ipv6

        # ----- Hostnames -----
        hostnames: List[str] = []
        hostnames_elem = host_elem.find("hostnames")
        if hostnames_elem is not None:
            for hn in hostnames_elem.findall("hostname"):
                name = hn.get("name")
                if name:
                    hostnames.append(name)

        # ----- OS detection -----
        os_name = None
        os_accuracy = None
        os_family = None
        os_gen = None
        os_cpe: List[str] = []

        os_elem = host_elem.find("os")
        if os_elem is not None:
            # Prefer the highest-accuracy osmatch
            best_match = None
            best_acc = -1
            for match in os_elem.findall("osmatch"):
                acc = _safe_int(match.get("accuracy")) or 0
                if acc > best_acc:
                    best_acc = acc
                    best_match = match

            if best_match is not None:
                os_name = best_match.get("name")
                os_accuracy = best_acc

                # First osclass under the best match
                osclass = best_match.find("osclass")
                if osclass is not None:
                    os_family = osclass.get("osfamily")
                    os_gen = osclass.get("osgen")
                    for cpe in osclass.findall("cpe"):
                        if cpe.text:
                            os_cpe.append(cpe.text)

            # Fallback: any cpe under <os>
            if not os_cpe:
                for cpe in os_elem.findall(".//cpe"):
                    if cpe.text:
                        os_cpe.append(cpe.text)

        # ----- Times & distance -----
        start_time = _parse_timestamp(host_elem.get("starttime"))
        end_time = _parse_timestamp(host_elem.get("endtime"))

        distance = None
        dist_elem = host_elem.find("distance")
        if dist_elem is not None:
            distance = _safe_int(dist_elem.get("value"))

        uptime = None
        lastboot = None
        uptime_elem = host_elem.find("uptime")
        if uptime_elem is not None:
            uptime = _safe_int(uptime_elem.get("seconds"))
            lastboot = uptime_elem.get("lastboot")

        # ----- Ports / Services -----
        services: List[Service] = []
        ports_elem = host_elem.find("ports")
        if ports_elem is not None:
            for port_elem in ports_elem.findall("port"):
                state_elem = port_elem.find("state")
                if state_elem is None:
                    continue

                port_state = state_elem.get("state", "unknown")

                if only_open and port_state != "open":
                    if not (include_closed and port_state == "closed"):
                        if not (include_filtered and "filtered" in port_state):
                            continue

                try:
                    portid = int(port_elem.get("portid", 0))
                except (ValueError, TypeError):
                    continue

                protocol = port_elem.get("protocol", "tcp")

                svc = Service(
                    port=portid,
                    protocol=protocol,
                    state=port_state,
                )

                # Service details
                service_elem = port_elem.find("service")
                if service_elem is not None:
                    svc.name = service_elem.get("name")
                    svc.product = service_elem.get("product")
                    svc.version = service_elem.get("version")
                    svc.extrainfo = service_elem.get("extrainfo")
                    svc.tunnel = service_elem.get("tunnel")
                    svc.method = service_elem.get("method")
                    svc.conf = _safe_int(service_elem.get("conf"))

                    for cpe in service_elem.findall("cpe"):
                        if cpe.text:
                            svc.cpe.append(cpe.text)

                # Scripts (including banner)
                for script in port_elem.findall("script"):
                    script_id = script.get("id")
                    output = script.get("output")
                    if script_id and output is not None:
                        svc.scripts[script_id] = output
                        if script_id == "banner":
                            svc.banner = output

                services.append(svc)

        # ----- Host-level scripts -----
        host_scripts: Dict[str, str] = {}
        hostscript_elem = host_elem.find("hostscript")
        if hostscript_elem is not None:
            for script in hostscript_elem.findall("script"):
                sid = script.get("id")
                out = script.get("output")
                if sid and out is not None:
                    host_scripts[sid] = out

        # Skip hosts with no open ports if requested
        if only_open and not any(s.state == "open" for s in services):
            continue

        host = Host(
            ip=primary_ip,
            ipv6=ipv6 if ipv4 else None,  # only store secondary if we have both
            mac=mac,
            vendor=vendor,
            hostnames=hostnames,
            status=state,
            reason=status_elem.get("reason"),
            os=os_name,
            os_accuracy=os_accuracy,
            os_family=os_family,
            os_gen=os_gen,
            os_cpe=os_cpe,
            services=services,
            host_scripts=host_scripts,
            start_time=start_time,
            end_time=end_time,
            distance=distance,
            uptime=uptime,
            lastboot=lastboot,
        )
        hosts.append(host)

    # Convert to plain dicts for backward compatibility
    result = [h.to_dict() for h in hosts]

    # Attach scan metadata as a special key on the first host or return separately
    # (kept simple – caller can ignore)
    if result and scan_info.get("args"):
        result[0]["_scan_info"] = {
            k: (v.isoformat() if isinstance(v, datetime) else v)
            for k, v in scan_info.items()
            if v is not None
        }

    logger.info("Parsed %d live host(s) from Nmap XML", len(result))
    return result


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def get_open_ports(hosts: List[Dict[str, Any]]) -> Dict[str, List[int]]:
    """Return {ip: [open_ports]} mapping."""
    return {
        h["ip"]: [s["port"] for s in h.get("services", []) if s.get("state") == "open"]
        for h in hosts
    }


def filter_by_service(hosts: List[Dict[str, Any]], service_name: str) -> List[Dict[str, Any]]:
    """Return only hosts that have a given service name open."""
    service_name = service_name.lower()
    filtered = []
    for h in hosts:
        matching = [
            s for s in h.get("services", [])
            if s.get("state") == "open" and (s.get("name") or "").lower() == service_name
        ]
        if matching:
            new_h = h.copy()
            new_h["services"] = matching
            filtered.append(new_h)
    return filtered


def pretty_print_hosts(hosts: List[Dict[str, Any]]) -> None:
    """Simple human-readable summary."""
    for h in hosts:
        print(f"\n[{h['ip']}]  {', '.join(h.get('hostnames') or ['-'])}")
        if h.get("os"):
            acc = f" ({h['os_accuracy']}%)" if h.get("os_accuracy") else ""
            print(f"  OS: {h['os']}{acc}")
        for s in h.get("services", []):
            if s.get("state") != "open":
                continue
            ver = s.get("version_string") or s.get("version") or ""
            banner = f"  | {s['banner'][:60]}…" if s.get("banner") else ""
            print(f"  {s['port']}/{s['protocol']:4}  {s.get('name') or '':12}  {ver}{banner}")