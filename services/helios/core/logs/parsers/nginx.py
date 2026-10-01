import logging
import re
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Nginx default combined log format
# Example: 192.168.1.100 - - [11/Oct/2023:14:32:01 +0000] "GET /admin HTTP/1.1" 404 153 "-" "curl/7.68.0"
NGINX_COMBINED_REGEX = re.compile(
    r"(?P<ip>\S+) \S+ (?P<user>\S+) \[(?P<timestamp>[^\]]+)\] "
    r'"(?P<method>\S+) (?P<request>[^\s]+) (?P<protocol>[^"]+)" '
    r"(?P<status>\d{3}) (?P<size>\S+) "
    r'"(?P<referrer>[^"]*)" "(?P<user_agent>[^"]*)"'
)


def parse_nginx_log_line(line: str) -> dict[str, Any] | None:
    match = NGINX_COMBINED_REGEX.match(line)
    if not match:
        return None

    data = match.groupdict()

    try:
        dt = datetime.strptime(data["timestamp"], "%d/%b/%Y:%H:%M:%S %z")
    except ValueError:
        dt = datetime.now()

    status = int(data["status"])
    severity = "info"

    # Detect common web attacks
    req = data["request"].lower()
    user_agent = data["user_agent"].lower()

    # Path traversal, SQLi, LFI, common exploit scanners
    dangerous_patterns = [
        "../",
        "..%2f",
        "%2e%2e%2f",  # Traversal
        "union select",
        "1=1",
        "drop table",  # SQLi
        "etc/passwd",
        "cmd.exe",
        "/bin/sh",  # LFI / RCE
        "jndi:ldap",  # Log4j
        "nmap",
        "sqlmap",
        "nikto",
        "zgrab",  # Scanners
    ]

    if any(p in req for p in dangerous_patterns) or any(
        p in user_agent for p in dangerous_patterns
    ):
        severity = "high"
    elif status >= 500:
        severity = "medium"
    elif status == 401 or status == 403:
        # Access denied could be brute force or discovery
        severity = "medium"

    return {
        "timestamp": dt,
        "source": "nginx",
        "event_type": "http_access",
        "severity": severity,
        "message": line.strip(),
        "source_ip": data["ip"],
        "dest_ip": None,
        "metadata": {
            "method": data["method"],
            "request": data["request"],
            "status": status,
            "user_agent": data["user_agent"],
            "referrer": data["referrer"],
        },
    }
