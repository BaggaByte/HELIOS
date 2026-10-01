"""
Nikto plugin — web server vulnerability scanner.

Nikto supports JSON output via `-Format json -output <path>`.
The JSON contains an `vulnerabilities` array with objects including
`id`, `OSVDB`, `method`, `url`, `msg`.

Reference: https://cirt.net/Nikto2 / https://github.com/sullo/nikto
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from helios.plugins.base import BasePlugin, PluginError

logger = logging.getLogger(__name__)


class NiktoPlugin(BasePlugin):
    """
    Wrapper for Nikto (https://github.com/sullo/nikto).
    Scans web servers for known vulnerabilities, misconfigurations, and dangerous files.
    """

    @property
    def name(self) -> str:
        return "nikto"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Executes Nikto for web server vulnerability scanning."

    # ------------------------------------------------------------------

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        target: str = payload.get("target", "").strip()
        if not target:
            raise ValueError("'target' URL or host is required for Nikto.")

        if not self.is_available("nikto"):
            return self._not_available_error()

        timeout: int = int(payload.get("timeout", 600))
        port: str = str(payload.get("port", ""))

        output_file = self.temp_json_output_file(suffix=".json")
        try:
            cmd = [
                "nikto",
                "-h",
                target,
                "-Format",
                "json",
                "-output",
                output_file,
                "-nointeractive",
            ]
            if port:
                cmd += ["-p", port]

            logger.info(f"[nikto] Scanning {target!r}")

            try:
                returncode, stdout, stderr = self.run_subprocess(cmd, timeout=timeout)
            except PluginError as exc:
                return self._plugin_error(exc)

            vulnerabilities = self._parse_output_file(output_file)

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
            "findings_count": len(vulnerabilities),
            "findings": vulnerabilities,
        }

    # ------------------------------------------------------------------

    def _parse_output_file(self, path: str) -> list[dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            return []

        results: list[dict[str, Any]] = []
        # Nikto JSON can be wrapped in a host list
        hosts = data if isinstance(data, list) else [data]
        for host in hosts:
            for vuln in host.get("vulnerabilities", []):
                results.append(
                    {
                        "title": vuln.get("msg", "Nikto Finding"),
                        "url": vuln.get("url", ""),
                        "method": vuln.get("method", "GET"),
                        "nikto_id": vuln.get("id", ""),
                        "osvdb": vuln.get("OSVDB", ""),
                        "severity": "medium",  # Nikto doesn't report CVSS; treat as medium
                        "status": "observed",
                        "source": "nikto",
                    }
                )
        return results
