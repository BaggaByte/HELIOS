"""
Katana plugin — next-generation web crawler.

Katana outputs one JSON object per line with:
  timestamp, request (method, endpoint, source, ...), response (status_code, headers, ...)

Reference: https://docs.projectdiscovery.io/tools/katana/running
"""

from __future__ import annotations

import logging
from typing import Any

from helios.plugins.base import BasePlugin, PluginError

logger = logging.getLogger(__name__)


class KatanaPlugin(BasePlugin):
    """
    Wrapper for Katana (https://github.com/projectdiscovery/katana).
    Crawls a web application and maps its URL space.
    """

    @property
    def name(self) -> str:
        return "katana"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Executes Katana for web crawling and URL endpoint discovery."

    # ------------------------------------------------------------------

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        target: str = payload.get("target", "").strip()
        if not target:
            raise ValueError("'target' URL is required for Katana.")

        if not self.is_available("katana"):
            return self._not_available_error()

        timeout: int = int(payload.get("timeout", 300))
        depth: int = int(payload.get("depth", 3))
        js_crawl: bool = payload.get("js_crawl", True)

        cmd = [
            "katana",
            "-u",
            target,
            "-json",
            "-silent",
            "-d",
            str(depth),
            "-no-color",
            "-timeout",
            "10",  # per-request timeout (seconds)
            "-rate-limit",
            "50",
        ]
        if js_crawl:
            cmd.append("-js-crawl")

        logger.info(f"[katana] Crawling {target!r} depth={depth}")

        try:
            returncode, stdout, stderr = self.run_subprocess(cmd, timeout=timeout)
        except PluginError as exc:
            return self._plugin_error(exc)

        endpoints = self._parse_output(stdout)

        return {
            "status": "success",
            "plugin": self.name,
            "version": self.version,
            "target": target,
            "findings_count": len(endpoints),
            "endpoints": endpoints,
        }

    # ------------------------------------------------------------------

    def _parse_output(self, stdout: str) -> list[dict[str, Any]]:
        endpoints: list[dict[str, Any]] = []
        seen: set = set()
        for record in self.parse_jsonlines(stdout):
            req = record.get("request", {})
            resp = record.get("response", {})
            endpoint = req.get("endpoint", "")
            if endpoint and endpoint not in seen:
                seen.add(endpoint)
                endpoints.append(
                    {
                        "endpoint": endpoint,
                        "method": req.get("method", "GET"),
                        "source": req.get("source", ""),
                        "status_code": resp.get("status_code", 0),
                        "content_type": resp.get("headers", {}).get("content-type", ""),
                    }
                )
        return endpoints
