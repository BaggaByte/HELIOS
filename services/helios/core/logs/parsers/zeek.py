import json
from datetime import datetime
from typing import Any


def parse_zeek_json_log(line: str) -> dict[str, Any] | None:
    try:
        data = json.loads(line)
        ts = data.get("ts")
        if ts is not None:
            dt = datetime.fromtimestamp(ts)
        else:
            dt = datetime.now()

        uid = data.get("uid")
        id_orig_h = data.get("id.orig_h")
        id_resp_h = data.get("id.resp_h")

        # Determine log type based on fields
        log_type = "unknown"
        if "id.orig_p" in data:
            log_type = "conn"
        if "host" in data and "uri" in data:
            log_type = "http"
        if "query" in data and "qtype_name" in data:
            log_type = "dns"

        return {
            "timestamp": dt,
            "source": "zeek",
            "event_type": f"zeek_{log_type}",
            "severity": "info",
            "message": f"Zeek {log_type} connection {uid}",
            "source_ip": id_orig_h,
            "dest_ip": id_resp_h,
            "metadata": data,
        }
    except Exception:
        return None
