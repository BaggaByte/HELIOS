"""
Amass plugin — in-depth subdomain enumeration and DNS mapping.

Amass outputs one JSON object per line in `-json` mode, with:
  name, domain, addresses (list), tag, sources (list).

Reference: https://github.com/owasp-amass/amass
"""

from __future__ import annotations

import logging
from typing import Any

from helios.plugins.base import BasePlugin, PluginError

logger = logging.getLogger(__name__)


class AmassPlugin(BasePlugin):
    """
    Wrapper for Amass (https://github.com/owasp-amass/amass).
    Provides active/passive subdomain enumeration with asset discovery.
    """

    @property
    def name(self) -> str:
        return "amass"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Executes Amass for in-depth subdomain enumeration and DNS mapping."

    # ------------------------------------------------------------------

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        target: str = payload.get("target", "").strip()
        if not target:
            raise ValueError("'target' domain is required for Amass.")

        if not self.is_available("amass"):
            return self._not_available_error()

        timeout: int = int(payload.get("timeout", 600))
        passive: bool = payload.get(
            "passive", True
        )  # default to passive — non-intrusive

        cmd = [
            "amass",
            "enum",
            "-d",
            target,
            "-json",
            "-",  # JSON-lines to stdout
        ]
        if passive:
            cmd.append("-passive")

        logger.info(f"[amass] Enumerating {target!r} passive={passive}")

        try:
            returncode, stdout, stderr = self.run_subprocess(cmd, timeout=timeout)
        except PluginError as exc:
            return self._plugin_error(exc)

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
        seen: set = set()
        for record in self.parse_jsonlines(stdout):
            name = record.get("name", "")
            if name and name not in seen:
                seen.add(name)
                results.append(
                    {
                        "name": name,
                        "domain": record.get("domain", ""),
                        "addresses": record.get("addresses", []),
                        "tag": record.get("tag", ""),
                        "sources": record.get("sources", []),
                    }
                )
        return results
