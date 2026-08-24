import logging
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

PARSER_MAP = {
    "apache": parse_apache_log_line,
    "nginx": parse_nginx_log_line,
    "suricata": parse_suricata_fast_log,
    "linux_auth": parse_auth_log_line,
    "docker": parse_docker_log,
    "kubernetes": parse_kubernetes_log,
    "sysmon": parse_sysmon_xml_log,
    "windows_event": parse_windows_event_xml,
    "zeek": parse_zeek_json_log,
}

def parse_log_file(content: str, log_type: str) -> List[Dict[str, Any]]:
    """
    Parses a log file line by line based on the given log type.
    Returns a list of dictionaries suitable for creating LogEvent instances.
    """
    parser_func = PARSER_MAP.get(log_type.lower())
    if not parser_func:
        raise ValueError(f"Unsupported log type: {log_type}. Supported: {list(PARSER_MAP.keys())}")
        
    events = []
    lines = content.splitlines()
    
    for line in lines:
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
