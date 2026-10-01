import html
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Data models
# ──────────────────────────────────────────────────────────────


@dataclass
class Instance:
    uri: str
    method: str = "GET"
    param: str | None = None
    attack: str | None = None
    evidence: str | None = None
    otherinfo: str | None = None

    @property
    def summary(self) -> str:
        parts = [f"{self.method} {self.uri}"]
        if self.param:
            parts.append(f"(param: {self.param})")
        if self.attack:
            parts.append(f"[attack: {self.attack[:80]}]")
        return " ".join(parts)


@dataclass
class Finding:
    title: str
    plugin_id: str | None = None
    alert_ref: str | None = None
    severity: str = "info"  # info | low | medium | high | critical
    risk_code: int = 0
    confidence: str = "low"  # low | medium | high | confirmed
    confidence_code: int = 1
    description: str = ""
    solution: str = ""
    otherinfo: str = ""
    reference: list[str] = field(default_factory=list)
    cwe_id: str | None = None
    wasc_id: str | None = None
    source_id: str | None = None

    # Target context
    site_name: str | None = None
    host: str | None = None
    port: int | None = None
    ssl: bool | None = None

    # Instances (evidence)
    instances: list[Instance] = field(default_factory=list)
    instance_count: int = 0

    # Derived helpers
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Convenience fields for downstream consumers
        d["impact"] = self.instances[0].summary if self.instances else ""
        d["references_json"] = self.reference
        d["remediation"] = self.solution
        d["target_host"] = self.host
        d["target_port"] = self.port
        return d


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

RISK_MAP = {
    "0": ("info", 0),
    "1": ("low", 1),
    "2": ("medium", 2),
    "3": ("high", 3),
    "4": ("critical", 4),  # some ZAP versions / plugins use 4
}

CONFIDENCE_MAP = {
    "0": ("false_positive", 0),
    "1": ("low", 1),
    "2": ("medium", 2),
    "3": ("high", 3),
    "4": ("confirmed", 4),
}

_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"[ \t]+")
_MULTI_NL_RE = re.compile(r"\n{3,}")


def _clean_text(text: str | None) -> str:
    """Strip HTML tags, unescape entities, normalise whitespace."""
    if not text:
        return ""
    text = html.unescape(text)
    text = _TAG_RE.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _WHITESPACE_RE.sub(" ", text)
    text = _MULTI_NL_RE.sub("\n\n", text)
    return text.strip()


def _parse_references(raw: str | None) -> list[str]:
    if not raw:
        return []
    # ZAP frequently embeds <p>…</p> or just newlines / <br>
    cleaned = (
        raw.replace("<p>", "\n")
        .replace("</p>", "\n")
        .replace("<br>", "\n")
        .replace("<br/>", "\n")
    )
    cleaned = _TAG_RE.sub("", cleaned)
    refs = []
    for line in cleaned.splitlines():
        line = line.strip()
        if line and line not in refs:
            refs.append(line)
    return refs


def _safe_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _extract_tags(alert_elem: ET.Element) -> list[str]:
    """Pull <tag> elements if present (newer ZAP reports)."""
    tags = []
    for tag in alert_elem.findall(".//tag"):
        # Some exports use <tag><tag>name</tag></tag>, others just text
        name = tag.findtext("tag") or tag.text
        if name:
            tags.append(name.strip())
    return tags


# ──────────────────────────────────────────────────────────────
# Main parser
# ──────────────────────────────────────────────────────────────


def parse_zap_xml(
    xml_content: bytes | str,
    *,
    min_risk: int = 0,
    min_confidence: int = 1,
    include_false_positives: bool = False,
    max_instances_per_alert: int = 50,
) -> list[dict[str, Any]]:
    """
    Advanced OWASP ZAP XML report parser.

    Parameters
    ----------
    xml_content :
        Raw XML bytes or string.
    min_risk :
        Minimum risk code to keep (0=Info … 3/4=High/Critical).
    min_confidence :
        Minimum confidence code (1=Low … 3=High / 4=Confirmed).
    include_false_positives :
        Keep alerts marked as false positive (confidence 0).
    max_instances_per_alert :
        Cap the number of evidence instances stored per finding.

    Returns
    -------
    List[Dict[str, Any]]
        List of finding dictionaries (JSON-serialisable).
    """
    if isinstance(xml_content, str):
        xml_content = xml_content.encode("utf-8", errors="replace")

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        logger.error("ZAP XML parse error: %s", e)
        raise ValueError(f"Invalid ZAP XML: {e}") from e

    # Optional report-level metadata
    report_meta = {
        "generated": root.get("generated"),
        "version": root.get("version") or root.findtext(".//version"),
        "program_name": root.findtext(".//programName") or "OWASP ZAP",
    }

    findings: list[Finding] = []

    # Support both classic <OWASPZAPReport><site>… and some flat exports
    sites = root.findall(".//site")
    if not sites:
        # Fallback: treat the whole document as a single site
        sites = [root]

    for site in sites:
        site_name = site.get("name") or site.get("host")
        host = site.get("host")
        port = _safe_int(site.get("port"))
        ssl = site.get("ssl")
        if ssl is not None:
            ssl = ssl.lower() in ("true", "1", "yes")

        # If host missing, try to derive from site name / first URI later
        if not host and site_name:
            try:
                parsed = urlparse(
                    site_name if "://" in site_name else f"https://{site_name}"
                )
                host = parsed.hostname
                if port is None and parsed.port:
                    port = parsed.port
            except Exception:
                pass

        for alert in site.findall(".//alertitem"):
            # ── Core fields ──────────────────────────────────
            title = alert.findtext("name") or alert.findtext("alert") or "Unknown Alert"
            title = _clean_text(title)

            plugin_id = alert.findtext("pluginid")
            alert_ref = alert.findtext("alertRef") or alert.findtext("alertref")

            risk_code_raw = alert.findtext("riskcode") or "0"
            severity, risk_code = RISK_MAP.get(risk_code_raw, ("info", 0))

            conf_code_raw = alert.findtext("confidence") or "1"
            confidence, conf_code = CONFIDENCE_MAP.get(conf_code_raw, ("low", 1))

            # Filtering
            if risk_code < min_risk:
                continue
            if conf_code == 0 and not include_false_positives:
                continue
            if conf_code < min_confidence and conf_code != 0:
                continue

            description = _clean_text(alert.findtext("desc"))
            solution = _clean_text(alert.findtext("solution"))
            otherinfo = _clean_text(alert.findtext("otherinfo"))
            references = _parse_references(alert.findtext("reference"))

            cwe_id = alert.findtext("cweid") or None
            if cwe_id == "0" or cwe_id == "-1":
                cwe_id = None
            wasc_id = alert.findtext("wascid") or None
            if wasc_id == "0" or wasc_id == "-1":
                wasc_id = None
            source_id = alert.findtext("sourceid")

            tags = _extract_tags(alert)

            # ── Instances ────────────────────────────────────
            instances: list[Instance] = []
            instances_elem = alert.find("instances")
            if instances_elem is not None:
                for inst in instances_elem.findall("instance")[
                    :max_instances_per_alert
                ]:
                    uri = inst.findtext("uri") or ""
                    method = (inst.findtext("method") or "GET").upper()
                    param = inst.findtext("param") or None
                    attack = inst.findtext("attack") or None
                    evidence = inst.findtext("evidence") or None
                    other = inst.findtext("otherinfo") or None

                    instances.append(
                        Instance(
                            uri=uri.strip(),
                            method=method,
                            param=param.strip() if param else None,
                            attack=_clean_text(attack) if attack else None,
                            evidence=_clean_text(evidence) if evidence else None,
                            otherinfo=_clean_text(other) if other else None,
                        )
                    )

            # Count attribute is sometimes present
            count_attr = alert.findtext("count")
            instance_count = _safe_int(count_attr) or len(instances)

            # If we still don't have a host, try first URI
            if not host and instances:
                try:
                    parsed = urlparse(instances[0].uri)
                    host = parsed.hostname
                    if port is None and parsed.port:
                        port = parsed.port
                except Exception:
                    pass

            finding = Finding(
                title=title,
                plugin_id=plugin_id,
                alert_ref=alert_ref,
                severity=severity,
                risk_code=risk_code,
                confidence=confidence,
                confidence_code=conf_code,
                description=description,
                solution=solution,
                otherinfo=otherinfo,
                reference=references,
                cwe_id=cwe_id,
                wasc_id=wasc_id,
                source_id=source_id,
                site_name=site_name,
                host=host,
                port=port,
                ssl=ssl,
                instances=instances,
                instance_count=instance_count,
                tags=tags,
            )
            findings.append(finding)

    logger.info(
        "Parsed %d ZAP finding(s) (min_risk=%d, min_confidence=%d)",
        len(findings),
        min_risk,
        min_confidence,
    )

    # Return plain dicts for compatibility with existing ingest code
    result = [f.to_dict() for f in findings]

    # Attach lightweight report metadata on the first item (optional)
    if result and any(report_meta.values()):
        result[0]["_report_meta"] = {k: v for k, v in report_meta.items() if v}

    return result


# ──────────────────────────────────────────────────────────────
# Convenience helpers
# ──────────────────────────────────────────────────────────────


def filter_findings(
    findings: list[dict[str, Any]],
    *,
    severity: str | None = None,
    min_risk: int | None = None,
    host: str | None = None,
    cwe_id: str | None = None,
    plugin_id: str | None = None,
) -> list[dict[str, Any]]:
    """Simple post-filter helper."""
    out = findings
    if severity:
        out = [f for f in out if f.get("severity") == severity.lower()]
    if min_risk is not None:
        out = [f for f in out if f.get("risk_code", 0) >= min_risk]
    if host:
        out = [f for f in out if f.get("host") == host or f.get("target_host") == host]
    if cwe_id:
        out = [f for f in out if f.get("cwe_id") == str(cwe_id)]
    if plugin_id:
        out = [f for f in out if f.get("plugin_id") == str(plugin_id)]
    return out


def group_by_host(findings: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group findings by target host."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for f in findings:
        key = f.get("host") or f.get("target_host") or "unknown"
        groups.setdefault(key, []).append(f)
    return groups


def severity_counts(findings: list[dict[str, Any]]) -> dict[str, int]:
    """Return {severity: count}."""
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        sev = f.get("severity", "info")
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def pretty_print_findings(findings: list[dict[str, Any]], limit: int = 20) -> None:
    """Human-readable summary for debugging."""
    counts = severity_counts(findings)
    print(f"Total findings: {len(findings)}  |  {counts}")
    for i, f in enumerate(findings[:limit], 1):
        inst = f.get("instances") or []
        sample = inst[0]["uri"] if inst else "-"
        print(
            f"{i:3}. [{f.get('severity', '?'):8}] {f.get('title', '')[:70]}"
            f"  → {f.get('host') or '?'}  ({len(inst)} instance(s))  {sample[:60]}"
        )
    if len(findings) > limit:
        print(f"… and {len(findings) - limit} more")
