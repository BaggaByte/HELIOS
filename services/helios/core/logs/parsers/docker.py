import json
from datetime import datetime
from typing import Dict, Any, Optional


def parse_docker_log(line: str) -> Optional[Dict[str, Any]]:
    try:
        data = json.loads(line)
        timestamp = data.get("time") or data.get("timestamp")
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except:
            dt = datetime.now()

        log_stream = data.get("stream", "stdout")
        log_msg = data.get("log", line)

        severity = "info"
        if "error" in log_msg.lower() or "fatal" in log_msg.lower():
            severity = "high"

        if "exec" in log_msg and ("bash" in log_msg or "sh" in log_msg):
            severity = "medium"

        return {
            "timestamp": dt,
            "source": "docker",
            "event_type": "container_log",
            "severity": severity,
            "message": log_msg.strip(),
            "source_ip": None,
            "dest_ip": None,
            "metadata": {
                "stream": log_stream,
                "container_id": data.get("container_id", "unknown"),
            },
        }
    except Exception:
        return None
