import re
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Standard Apache/Nginx Combined Log Format
# Example: 127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326 "http://www.example.com/start.html" "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT 5.1)"
APACHE_COMBINED_REGEX = re.compile(
    r'(?P<ip>\S+) \S+ (?P<user>\S+) \[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<request>[^\s]+) (?P<protocol>[^"]+)" '
    r'(?P<status>\d{3}) (?P<size>\S+) '
    r'"(?P<referrer>[^"]*)" "(?P<user_agent>[^"]*)"'
)

def parse_apache_log_line(line: str) -> Optional[Dict[str, Any]]:
    match = APACHE_COMBINED_REGEX.match(line)
    if not match:
        return None
        
    data = match.groupdict()
    
    # Parse timestamp e.g. 10/Oct/2000:13:55:36 -0700
    try:
        dt = datetime.strptime(data['timestamp'], "%d/%b/%Y:%H:%M:%S %z")
    except ValueError:
        dt = datetime.now() # Fallback
        
    # Basic severity logic for HTTP status
    status = int(data['status'])
    if status >= 500:
        severity = "medium"
    elif status >= 400:
        # Check for common scanners or injection
        req = data['request'].lower()
        if "select" in req or "union" in req or "../" in req or "%00" in req or ".env" in req:
            severity = "high"
        else:
            severity = "info"
    else:
        severity = "info"

    return {
        "timestamp": dt,
        "source": "apache",
        "event_type": "http_access",
        "severity": severity,
        "message": line,
        "source_ip": data['ip'],
        "dest_ip": None, # Usually the server itself
        "metadata": {
            "method": data['method'],
            "request": data['request'],
            "status": status,
            "user_agent": data['user_agent'],
            "referrer": data['referrer']
        }
    }
