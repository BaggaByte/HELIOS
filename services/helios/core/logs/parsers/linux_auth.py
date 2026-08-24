import re
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Sample auth.log line:
# Oct 11 14:32:01 server sshd[12345]: Failed password for invalid user admin from 192.168.1.100 port 45678 ssh2
AUTH_REGEX = re.compile(
    r'(?P<month>[A-Z][a-z]{2})\s+(?P<day>\d+)\s+(?P<time>\d{2}:\d{2}:\d{2})\s+'
    r'(?P<hostname>\S+)\s+(?P<process>\w+)\[(?P<pid>\d+)\]:\s+(?P<message>.*)'
)

# Detect SSH brute force attempts
FAILED_LOGIN_REGEX = re.compile(
    r'Failed password for (?:invalid user )?(?P<user>\S+) from (?P<ip>[0-9a-fA-F\.:]+) port (?P<port>\d+)'
)

def parse_auth_log_line(line: str) -> Optional[Dict[str, Any]]:
    match = AUTH_REGEX.match(line)
    if not match:
        return None
        
    data = match.groupdict()
    
    # Auth.log usually doesn't have a year, assume current year
    current_year = datetime.now().year
    timestamp_str = f"{current_year} {data['month']} {data['day']} {data['time']}"
    
    try:
        dt = datetime.strptime(timestamp_str, "%Y %b %d %H:%M:%S")
    except ValueError:
        dt = datetime.now()
        
    severity = "info"
    source_ip = None
    event_type = "auth_event"
    metadata = {
        "process": data['process'],
        "pid": data['pid'],
        "hostname": data['hostname']
    }
    
    # Check for specific security events
    msg = data['message']
    
    failed_match = FAILED_LOGIN_REGEX.search(msg)
    if failed_match:
        severity = "medium"
        event_type = "failed_login"
        source_ip = failed_match.group("ip")
        metadata["target_user"] = failed_match.group("user")
        metadata["src_port"] = failed_match.group("port")
        
    elif "Accepted password" in msg or "Accepted publickey" in msg:
        severity = "info"
        event_type = "successful_login"
        # Extract IP roughly
        ip_match = re.search(r'from ([0-9a-fA-F\.:]+) port', msg)
        if ip_match:
            source_ip = ip_match.group(1)

    return {
        "timestamp": dt,
        "source": "linux_auth",
        "event_type": event_type,
        "severity": severity,
        "message": line.strip(),
        "source_ip": source_ip,
        "dest_ip": None, # Local machine
        "metadata": metadata
    }
