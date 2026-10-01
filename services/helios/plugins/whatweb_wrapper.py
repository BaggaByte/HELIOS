"""
WhatWeb plugin — web technology fingerprinting.

WhatWeb outputs JSON when invoked with `--log-json=-` (stdout).
Each entry is a JSON object with `target`, `http_status`, `plugins` dict.

Reference: https://github.com/urbanadventurer/WhatWeb
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from helios.plugins.base import BasePlugin, PluginError

logger = logging.getLogger(__name__)


class WhatwebPlugin(BasePlugin):
    """
    Wrapper for WhatWeb (https://github.com/urbanadventurer/WhatWeb).
    Fingerprints web technologies (CMS, frameworks, servers, analytics, etc.).
    """

    @property
    def name(self) -> str:
        return "whatweb"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Executes WhatWeb to fingerprint web technologies."

    # ------------------------------------------------------------------

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target: str = payload.get("target", "").strip()
        if not target:
            raise ValueError("'target' URL is required for WhatWeb.")

        if not self.is_available("whatweb"):
            return self._not_available_error()

        timeout: int = int(payload.get("timeout", 120))
        aggression: int = int(payload.get("aggression", 1))   # 1=passive, 3=aggressive

        cmd = [
            "whatweb",
            target,
            f"--aggression={aggression}",
            "--log-json=-",    # JSON to stdout
            "--quiet",
            "--no-errors",
            "--color=never",
        ]

        logger.info(f"[whatweb] Fingerprinting {target!r} aggression={aggression}")

        try:
            returncode, stdout, stderr = self.run_subprocess(cmd, timeout=timeout)
        except PluginError as exc:
            return self._plugin_error(exc)

        technologies = self._parse_output(stdout)

        return {
            "status": "success",
            "plugin": self.name,
            "version": self.version,
            "target": target,
            "findings_count": len(technologies),
            "technologies": technologies,
        }

    # ------------------------------------------------------------------

    def _parse_output(self, stdout: str) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for record in self.parse_jsonlines(stdout):
            target_url = record.get("target", "")
            http_status = record.get("http_status", 0)
            plugins = record.get("plugins", {})
            tech_names = list(plugins.keys())
            tech_details: List[Dict[str, Any]] = []
            for plugin_name, plugin_data in plugins.items():
                version = ""
                if isinstance(plugin_data, dict):
                    version_list = plugin_data.get("version", [])
                    version = ", ".join(version_list) if version_list else ""
                tech_details.append({
                    "name": plugin_name,
                    "version": version,
                })
            results.append({
                "url": target_url,
                "http_status": http_status,
                "technologies": tech_names,
                "details": tech_details,
            })
        return results
