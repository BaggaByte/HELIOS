import re
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Suricata fast.log Format
# Example: 10/11/2023-14:32:01.123456  [**] [1:2010935:2] ET EXPLOIT Possible SQL Injection [**] [Classification: Web Application Attack] [Priority: 1] {TCP} 192.168.1.100:54321 -> 10.0.0.5:80
SURICATA_FAST_REGEX = re.compile(
    r"(?P<timestamp>\d{2}/\d{2}/\d{4}-\d{2}:\d{2}:\d{2}\.\d+)\s+"
    r"\[\*\*\] \[(?P<sig_id>\d+:\d+:\d+)\] (?P<msg>[^\[]+) \[\*\*\]\s*"
    r"(?:\[Classification: (?P<classification>[^\]]+)\]\s*)?"
    r"(?:\[Priority: (?P<priority>\d+)\]\s*)?"
    r"\{(?P<protocol>[^\}]+)\}\s*"
    r"(?P<src_ip>[0-9a-fA-F\.]+):(?P<src_port>\d+) -> "
    r"(?P<dest_ip>[0-9a-fA-F\.]+):(?P<dest_port>\d+)"
)


def parse_suricata_fast_log(line: str) -> Optional[Dict[str, Any]]:
    match = SURICATA_FAST_REGEX.search(line)
    if not match:
        return None

    data = match.groupdict()

    # Parse timestamp e.g. 10/11/2023-14:32:01.123456
    try:
        dt = datetime.strptime(data["timestamp"], "%m/%d/%Y-%H:%M:%S.%f")
    except ValueError:
        try:
            # Maybe DD/MM ? We will assume MM/DD standard
            dt = datetime.strptime(data["timestamp"], "%d/%m/%Y-%H:%M:%S.%f")
        except ValueError:
            dt = datetime.now()  # Fallback

    priority = int(data.get("priority") or 3)
    if priority == 1:
        severity = "high"
    elif priority == 2:
        severity = "medium"
    else:
        severity = "low"

    return {
        "timestamp": dt,
        "source": "suricata",
        "event_type": "ids_alert",
        "severity": severity,
        "message": line.strip(),
        "source_ip": data["src_ip"],
        "dest_ip": data["dest_ip"],
        "metadata": {
            "signature_id": data["sig_id"],
            "alert_msg": data["msg"].strip(),
            "classification": data.get("classification"),
            "protocol": data.get("protocol"),
            "src_port": data.get("src_port"),
            "dest_port": data.get("dest_port"),
        },
    }
