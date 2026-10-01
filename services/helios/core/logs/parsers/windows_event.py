import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any


def parse_windows_event_xml(xml_line: str) -> dict[str, Any] | None:
    try:
        root = ET.fromstring(xml_line)
        event_data = {}
        for data in root.findall(".//EventData/Data"):
            name = data.get("Name")
            if name:
                event_data[name] = data.text

        system = root.find(".//System")
        event_id = system.findtext("EventID") if system is not None else None

        severity = "info"
        if event_id in ["4624", "4625"]:  # Logon events
            logon_type = event_data.get("LogonType")
            if event_id == "4625":
                severity = "medium"  # Failed logon
            if logon_type == "10":  # RDP
                severity = "high" if event_id == "4625" else "medium"

        if event_id == "4720":  # User created
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
            "source": "windows_event",
            "event_type": f"Windows_Event_{event_id}",
            "severity": severity,
            "message": f"Windows Event {event_id}",
            "source_ip": event_data.get("IpAddress"),
            "dest_ip": None,
            "metadata": event_data,
        }
    except Exception:
        return None
