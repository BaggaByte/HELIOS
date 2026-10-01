"""
gau plugin — Get All URLs, fetch known URLs from multiple passive sources
(Wayback Machine, Common Crawl, URLScan, AlienVault OTX).

gau outputs one URL per line (plain text, not JSON).

Reference: https://github.com/lc/gau
"""

from __future__ import annotations

import logging
from typing import Any

from helios.plugins.base import BasePlugin, PluginError

logger = logging.getLogger(__name__)


class GauPlugin(BasePlugin):
    """
    Wrapper for gau (https://github.com/lc/gau).
    Fetches known historical URLs for a domain from passive sources.
    """

    @property
    def name(self) -> str:
        return "gau"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Fetches known URLs from passive sources (Wayback, CommonCrawl, URLScan) using gau."

    # ------------------------------------------------------------------

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        target: str = payload.get("target", "").strip()
        if not target:
            raise ValueError("'target' domain is required for gau.")

        if not self.is_available("gau"):
            return self._not_available_error()

        timeout: int = int(payload.get("timeout", 300))
        blacklist: str = payload.get(
            "blacklist", "png,jpg,gif,svg,css,woff,woff2,ttf,ico"
        )

        cmd = [
            "gau",
            target,
            "--blacklist",
            blacklist,
            "--threads",
            "5",
        ]

        logger.info(f"[gau] Fetching archived URLs for {target!r}")

        try:
            returncode, stdout, stderr = self.run_subprocess(cmd, timeout=timeout)
        except PluginError as exc:
            return self._plugin_error(exc)

        urls = [u.strip() for u in stdout.splitlines() if u.strip()]
        # Deduplicate
        urls = list(dict.fromkeys(urls))

        return {
            "status": "success",
            "plugin": self.name,
            "version": self.version,
            "target": target,
            "findings_count": len(urls),
            "urls": urls,
        }
