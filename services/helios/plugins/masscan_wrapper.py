"""
Masscan plugin — ultra-fast TCP/UDP port scanner.

Masscan outputs JSON when invoked with `-oJ -`, but it writes a non-standard
JSON array without a proper closing bracket on stdout.  We use a temp file
(`-oJ <path>`) and parse the file after the scan completes, which is the
recommended approach.

Reference: https://github.com/robertdavidgraham/masscan
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List

from helios.plugins.base import BasePlugin, PluginError

logger = logging.getLogger(__name__)


class MasscanPlugin(BasePlugin):
    """
    Wrapper for masscan (https://github.com/robertdavidgraham/masscan).
    Fast stateless port scanner; complements nmap for initial discovery.

    NOTE: masscan typically requires root/Administrator privileges or
    raw-socket capability to send SYN packets.
    """

    @property
    def name(self) -> str:
        return "masscan"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Executes Masscan for fast TCP/UDP port scanning."

    # ------------------------------------------------------------------

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target: str = payload.get("target", "").strip()
        if not target:
            raise ValueError("'target' IP/CIDR is required for Masscan.")

        if not self.is_available("masscan"):
            return self._not_available_error()

        ports: str = payload.get("ports", "0-65535")
        rate: int = int(payload.get("rate", 1000))  # packets/sec — keep low
        timeout: int = int(payload.get("timeout", 600))

        output_file = self.temp_json_output_file(suffix=".json")
        try:
            cmd = [
                "masscan",
                target,
                "-p",
                ports,
                "--rate",
                str(rate),
                "-oJ",
                output_file,
            ]

            logger.info(f"[masscan] Scanning {target!r} ports={ports} rate={rate}")

            try:
                returncode, stdout, stderr = self.run_subprocess(cmd, timeout=timeout)
            except PluginError as exc:
                return self._plugin_error(exc)

            if returncode != 0:
                logger.warning(
                    f"[masscan] Exited with code {returncode}: {stderr[:500]}"
                )

            open_ports = self._parse_output_file(output_file)

        finally:
            try:
                os.unlink(output_file)
            except OSError:
                pass

        return {
            "status": "success",
            "plugin": self.name,
            "version": self.version,
            "target": target,
            "findings_count": len(open_ports),
            "open_ports": open_ports,
        }

    # ------------------------------------------------------------------

    def _parse_output_file(self, path: str) -> List[Dict[str, Any]]:
        """
        Masscan JSON output looks like:
          { "ip": "1.2.3.4", "timestamp": "...", "ports": [{"port":80,"proto":"tcp","status":"open",...}] }
          ...  (one JSON object per line, NOT a valid JSON array)
        """
        results: List[Dict[str, Any]] = []
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                raw = fh.read()
        except OSError:
            return results

        for record in self.parse_jsonlines(raw):
            ip = record.get("ip", "")
            for port_info in record.get("ports", []):
                results.append(
                    {
                        "ip": ip,
                        "port": port_info.get("port", 0),
                        "protocol": port_info.get("proto", "tcp"),
                        "status": port_info.get("status", "open"),
                        "timestamp": record.get("timestamp", ""),
                    }
                )
        return results
