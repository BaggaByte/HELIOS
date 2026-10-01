"""
Subfinder plugin — passive subdomain enumeration.

Subfinder outputs one JSON object per line with fields:
  host, source, ip (optional), input.

Reference: https://docs.projectdiscovery.io/tools/subfinder/running
"""

from __future__ import annotations

import logging
from typing import Any

from helios.plugins.base import BasePlugin, PluginError

logger = logging.getLogger(__name__)


class SubfinderPlugin(BasePlugin):
    """
    Wrapper for Subfinder (https://github.com/projectdiscovery/subfinder).
    Enumerates subdomains passively and returns a structured list.
    """

    @property
    def name(self) -> str:
        return "subfinder"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Executes Subfinder for passive subdomain enumeration."

    # ------------------------------------------------------------------

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        target: str = payload.get("target", "").strip()
        if not target:
            raise ValueError("'target' domain is required for Subfinder.")

        if not self.is_available("subfinder"):
            return self._not_available_error()

        timeout: int = int(payload.get("timeout", 300))

        cmd = [
            "subfinder",
            "-d",
            target,
            "-oJ",  # JSON-lines output
            "-silent",
            "-all",  # use all sources (respects ~/.config/subfinder/config.yaml)
        ]

        logger.info(f"[subfinder] Enumerating subdomains for {target!r}")

        try:
            returncode, stdout, stderr = self.run_subprocess(cmd, timeout=timeout)
        except PluginError as exc:
            return self._plugin_error(exc)

        if returncode != 0:
            logger.warning(f"[subfinder] Exited with code {returncode}: {stderr[:500]}")

        subdomains = self._parse_output(stdout)

        return {
            "status": "success",
            "plugin": self.name,
            "version": self.version,
            "target": target,
            "findings_count": len(subdomains),
            "subdomains": subdomains,
        }

    # ------------------------------------------------------------------

    def _parse_output(self, stdout: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for record in self.parse_jsonlines(stdout):
            host = record.get("host") or record.get("input", "")
            if host:
                results.append(
                    {
                        "host": host,
                        "source": record.get("source", ""),
                        "ip": record.get("ip", ""),
                    }
                )
        # Deduplicate by host
        seen = set()
        deduped = []
        for r in results:
            if r["host"] not in seen:
                seen.add(r["host"])
                deduped.append(r)
        return deduped
