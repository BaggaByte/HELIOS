import subprocess
import xml.etree.ElementTree as ET
import logging
import json
from typing import Dict, Any

from helios.plugins.base import BasePlugin

logger = logging.getLogger(__name__)


class NmapPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "nmap"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Wrapper for Nmap network scanner. Parses XML output into structured data."
        )

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes an Nmap scan.
        payload = {
            "target": "127.0.0.1",
            "args": "-sV -p-"  # optional
        }

        Always returns a dict with a "status" key:
          {"status": "success", "hosts": [...]}   — scan ran (zero hosts is valid)
          {"status": "error",   "error": "..."}   — binary missing, exec failed, etc.
        """
        target = payload.get("target")
        if not target:
            return {"status": "error", "error": "Missing 'target' in payload."}

        args = payload.get("args", "-sV --top-ports 100")

        # Build command. Always enforce XML output for parsing
        command = ["nmap", "-oX", "-"] + args.split() + [target]

        logger.info(f"Executing Nmap Plugin: {' '.join(command)}")

        try:
            result = subprocess.run(
                command, capture_output=True, text=True, check=False, timeout=300
            )

            if result.returncode != 0 and not result.stdout.strip():
                return {
                    "status": "error",
                    "error": f"Nmap exited with code {result.returncode}: {result.stderr.strip() or 'no output'}",
                }

            # Parse the XML output
            parsed_data = self._parse_nmap_xml(result.stdout)
            # _parse_nmap_xml already returns {"error": ...} on XML failures —
            # promote those to status=error for consistency.
            if "error" in parsed_data:
                return {"status": "error", "error": parsed_data["error"]}

            return {"status": "success", **parsed_data}

        except FileNotFoundError:
            return {
                "status": "error",
                "error": "Nmap executable not found on system PATH. Install nmap and ensure it is accessible.",
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error": "Nmap scan exceeded the 5-minute limit.",
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _parse_nmap_xml(self, xml_string: str) -> Dict[str, Any]:
        """Parses nmap -oX output into a structured dictionary."""
        if not xml_string.strip().startswith(
            "<?xml"
        ) and not xml_string.strip().startswith("<nmaprun"):
            return {
                "error": f"Nmap did not return valid XML. Output: {xml_string[:200]}"
            }

        try:
            root = ET.fromstring(xml_string)
        except ET.ParseError as e:
            return {
                "error": f"Failed to parse Nmap XML: {e}. Output was: {xml_string[:200]}"
            }

        scan_results = {"hosts": []}

        for host in root.findall("host"):
            # Status
            status = host.find("status")
            if status is not None and status.get("state") != "up":
                continue  # Skip down hosts

            host_data = {"ip": None, "hostname": None, "ports": []}

            # Address
            for address in host.findall("address"):
                if address.get("addrtype") == "ipv4":
                    host_data["ip"] = address.get("addr")

            # Hostnames
            hostnames = host.find("hostnames")
            if hostnames is not None:
                hostname = hostnames.find("hostname")
                if hostname is not None:
                    host_data["hostname"] = hostname.get("name")

            # Ports
            ports = host.find("ports")
            if ports is not None:
                for port_element in ports.findall("port"):
                    state = port_element.find("state")
                    if state is None or state.get("state") != "open":
                        continue  # Only grab open ports

                    port_data = {
                        "port": int(port_element.get("portid")),
                        "protocol": port_element.get("protocol"),
                        "service": "unknown",
                        "product": None,
                        "version": None,
                        "extrainfo": None,
                    }

                    service = port_element.find("service")
                    if service is not None:
                        port_data["service"] = service.get("name", "unknown")
                        port_data["product"] = service.get("product")
                        port_data["version"] = service.get("version")
                        port_data["extrainfo"] = service.get("extrainfo")

                    host_data["ports"].append(port_data)

            if host_data["ip"]:
                scan_results["hosts"].append(host_data)

        return scan_results
