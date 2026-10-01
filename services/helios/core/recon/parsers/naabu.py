import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def parse_naabu(content: str) -> Dict[str, Any]:
    """
    Parses Naabu JSONL output.
    Returns structured host and port data.
    """
    results = {"hosts": []}

    hosts_map = {}

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        try:
            data = json.loads(line)
            ip = data.get("ip")
            if not ip:
                continue

            if ip not in hosts_map:
                hosts_map[ip] = {
                    "ip": ip,
                    "hostnames": [data.get("host")]
                    if data.get("host") and data.get("host") != ip
                    else [],
                    "ports": [],
                }

            port = data.get("port")
            if port:
                hosts_map[ip]["ports"].append(
                    {
                        "port": port,
                        "protocol": "tcp",  # Naabu defaults to tcp
                        "state": "open",
                        "service": "unknown",
                    }
                )
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Naabu JSON line: {e}")
            continue

    results["hosts"] = list(hosts_map.values())
    return results
