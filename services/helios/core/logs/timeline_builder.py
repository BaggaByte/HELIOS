import logging
from typing import List, Dict, Any, Callable
from helios.core.logs.parsers.apache import parse_apache_log_line
from helios.core.logs.parsers.suricata import parse_suricata_fast_log

logger = logging.getLogger(__name__)

PARSER_MAP = {
    "apache": parse_apache_log_line,
    "nginx": parse_apache_log_line,  # Shares combined log format usually
    "suricata": parse_suricata_fast_log
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
