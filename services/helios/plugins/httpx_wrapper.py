"""
Httpx plugin — fast HTTP probing and technology fingerprinting.

httpx outputs one JSON object per line when invoked with `-json`.
Common fields: url, title, status-code, tech, webserver, content-length,
               cdn, ip, tls (struct), hashes, etc.

Reference: https://docs.projectdiscovery.io/tools/httpx/running
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from helios.plugins.base import BasePlugin, PluginError

logger = logging.getLogger(__name__)


class HttpxPlugin(BasePlugin):
    """
    Wrapper for httpx (https://github.com/projectdiscovery/httpx).
    Probes HTTP endpoints, extracts status codes, titles, and technologies.
    """

    @property
    def name(self) -> str:
        return "httpx"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Probes HTTP endpoints and fingerprints web technologies using httpx."

    # ------------------------------------------------------------------

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target: str = payload.get("target", "").strip()
        if not target:
            raise ValueError("'target' URL or host is required for httpx.")

        if not self.is_available("httpx"):
            return self._not_available_error()

        timeout: int = int(payload.get("timeout", 120))

        cmd = [
            "httpx",
            "-u",
            target,
            "-json",
            "-silent",
            "-title",
            "-tech-detect",
            "-status-code",
            "-content-length",
            "-web-server",
            "-no-color",
            "-timeout",
            "10",  # per-request timeout in seconds
        ]

        logger.info(f"[httpx] Probing {target!r}")

        try:
            returncode, stdout, stderr = self.run_subprocess(cmd, timeout=timeout)
        except PluginError as exc:
            return self._plugin_error(exc)

        probes = self._parse_output(stdout)

        return {
            "status": "success",
            "plugin": self.name,
            "version": self.version,
            "target": target,
            "findings_count": len(probes),
            "probes": probes,
        }

    # ------------------------------------------------------------------

    def _parse_output(self, stdout: str) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for record in self.parse_jsonlines(stdout):
            results.append(
                {
                    "url": record.get("url", ""),
                    "status_code": record.get("status-code", 0),
                    "title": record.get("title", ""),
                    "webserver": record.get("webserver", ""),
                    "content_length": record.get("content-length", 0),
                    "technologies": record.get("tech", []),
                    "ip": record.get("host", ""),
                    "cdn": record.get("cdn", False),
                    "tls": record.get("tls", {}),
                }
            )
        return results
