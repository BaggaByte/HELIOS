import json
from typing import Any


def parse_masscan(content: str) -> dict[str, Any]:
    """
    Parses Masscan JSON output.
    Returns standard HELIOS recon format.
    """
    results = {"hosts": []}

    try:
        data = json.loads(content)
        for host in data:
            host_dict = {"ip": host.get("ip"), "ports": []}

            for port_info in host.get("ports", []):
                host_dict["ports"].append(
                    {
                        "port": port_info.get("port"),
                        "protocol": port_info.get("proto"),
                        "state": port_info.get("status"),
                        "service": port_info.get("service", {}).get("name", "unknown"),
                    }
                )

            results["hosts"].append(host_dict)

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid Masscan JSON format: {e}")

    return results
