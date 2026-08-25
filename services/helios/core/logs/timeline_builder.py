import logging
import re
from typing import List, Dict, Any, Callable
from helios.core.logs.parsers.apache import parse_apache_log_line
from helios.core.logs.parsers.suricata import parse_suricata_fast_log
from helios.core.logs.parsers.nginx import parse_nginx_log_line
from helios.core.logs.parsers.linux_auth import parse_auth_log_line
from helios.core.logs.parsers.docker import parse_docker_log
from helios.core.logs.parsers.kubernetes import parse_kubernetes_log
from helios.core.logs.parsers.sysmon import parse_sysmon_xml_log
from helios.core.logs.parsers.windows_event import parse_windows_event_xml
from helios.core.logs.parsers.zeek import parse_zeek_json_log

logger = logging.getLogger(__name__)

# Line-oriented formats: one complete record per line (plain text or JSONL).
PARSER_MAP = {
    "apache": parse_apache_log_line,
    "nginx": parse_nginx_log_line,
    "suricata": parse_suricata_fast_log,
    "linux_auth": parse_auth_log_line,
    "docker": parse_docker_log,
    "kubernetes": parse_kubernetes_log,
    "zeek": parse_zeek_json_log,
}

# XML-document formats: Sysmon and Windows Event Log exports are XML, not
# line-oriented — a real export is either one <Event>...</Event> per line
# (EVTX exported with -RenderedXml in "raw" mode) or a pretty-printed,
# multi-line <Events>...</Events> document containing many <Event> children.
# Splitting on newline and feeding each line to ET.fromstring() breaks the
# second (much more common) case: every fragment is invalid XML on its own,
# ET.fromstring() raises, the per-line try/except in parse_log_file()
# swallows it, and the user silently gets an empty timeline with no error.
XML_EVENT_PARSERS: Dict[str, Callable[[str], Any]] = {
    "sysmon": parse_sysmon_xml_log,
    "windows_event": parse_windows_event_xml,
}


def _split_xml_events(content: str) -> List[str]:
    """
    Split a Sysmon/Windows Event XML export into individual <Event>...</Event>
    documents, regardless of whether the export is one event per line or a
    single pretty-printed multi-line <Events>...</Events> document.
    """
    content = content.strip()
    if not content:
        return []

    # Match each <Event ...>...</Event> block specifically — not the
    # <Events> wrapper tag itself, which is a prefix match trap for a naive
    # "<Event" substring search (it would swallow the wrapper's opening tag
    # into the first captured "event").
    events = re.findall(r"<Event\b[^>]*>.*?</Event>", content, re.DOTALL)
    if events:
        return events

    # Fallback: already one complete <Event>...</Event> per line, or some
    # other single-record-per-line layout the parser itself can handle.
    return [line.strip() for line in content.splitlines() if line.strip()]


def parse_log_file(content: str, log_type: str) -> List[Dict[str, Any]]:
    """
    Parses a log file into a list of dictionaries suitable for creating
    LogEvent instances. Dispatches on `log_type`: line-oriented formats are
    split on newline; XML event formats (Sysmon, Windows Event) are split
    into individual <Event> documents first, since they aren't line-oriented.
    """
    log_type = log_type.lower()

    if log_type in XML_EVENT_PARSERS:
        parser_func = XML_EVENT_PARSERS[log_type]
        events = []
        for event_xml in _split_xml_events(content):
            try:
                parsed = parser_func(event_xml)
                if parsed:
                    events.append(parsed)
            except Exception as e:
                logger.warning(f"Failed to parse {log_type} event: {e}")
        return events

    parser_func = PARSER_MAP.get(log_type)
    if not parser_func:
        supported = list(PARSER_MAP.keys()) + list(XML_EVENT_PARSERS.keys())
        raise ValueError(f"Unsupported log type: {log_type}. Supported: {supported}")

    events = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parsed = parser_func(line)
            if parsed:
                events.append(parsed)
        except Exception as e:
            logger.warning(f"Failed to parse log line [{line}]: {e}")

    return events
