import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any


def parse_sysmon_xml_log(xml_line: str) -> dict[str, Any] | None:
    try:
        root = ET.fromstring(xml_line)
        event_data = {}
        for data in root.findall(".//Data"):
            name = data.get("Name")
            if name:
                event_data[name] = data.text

        system = root.find(".//System")
        event_id = system.findtext("EventID") if system is not None else None

        severity = "info"
        if event_id == "1":  # Process Creation
            cmdline = event_data.get("CommandLine", "").lower()
            if "powershell" in cmdline and ("-enc" in cmdline or "hidden" in cmdline):
                severity = "high"

        dt = datetime.now()
        time_created = system.find(".//TimeCreated") if system is not None else None
        if time_created is not None and time_created.get("SystemTime"):
            try:
                dt = datetime.fromisoformat(
                    time_created.get("SystemTime").replace("Z", "+00:00")
                )
            except:
                pass

        return {
            "timestamp": dt,
            "source": "sysmon",
            "event_type": f"EventID_{event_id}",
            "severity": severity,
            "message": f"Sysmon Event {event_id}",
            "source_ip": event_data.get("SourceIp"),
            "dest_ip": event_data.get("DestinationIp"),
            "metadata": event_data,
        }
    except Exception:
        return None
