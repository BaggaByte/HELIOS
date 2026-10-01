"""
Dirsearch plugin — web path discovery / directory enumeration.

Dirsearch supports JSON output via `--format=json --output=<path>`.
The JSON schema contains a `results` dict keyed by URL, each value
being a list of hit objects with `status`, `redirect`, `length`.

Reference: https://github.com/maurosoria/dirsearch
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List

from helios.plugins.base import BasePlugin, PluginError

logger = logging.getLogger(__name__)


class DirsearchPlugin(BasePlugin):
    """
    Wrapper for dirsearch (https://github.com/maurosoria/dirsearch).
    Enumerates web paths using a configurable wordlist.
    """

    @property
    def name(self) -> str:
        return "dirsearch"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Executes Dirsearch for web directory enumeration."

    # ------------------------------------------------------------------

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target: str = payload.get("target", "").strip()
        if not target:
            raise ValueError("'target' URL is required for Dirsearch.")

        if not self.is_available("dirsearch"):
            return self._not_available_error()

        wordlist: str = payload.get("wordlist", "")
        extensions: str = payload.get(
            "extensions", "php,asp,aspx,jsp,html,js,json,txt,xml,bak,old"
        )
        threads: int = int(payload.get("threads", 25))
        timeout: int = int(payload.get("timeout", 300))

        output_file = self.temp_json_output_file(suffix=".json")
        try:
            cmd = [
                "dirsearch",
                "-u",
                target,
                "-e",
                extensions,
                "-t",
                str(threads),
                "--format=json",
                f"--output={output_file}",
                "--quiet",
                "--no-color",
            ]
            if wordlist:
                cmd += ["-w", wordlist]

            logger.info(f"[dirsearch] Scanning {target!r}")

            try:
                returncode, stdout, stderr = self.run_subprocess(cmd, timeout=timeout)
            except PluginError as exc:
                return self._plugin_error(exc)

            hits = self._parse_output_file(output_file)

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
            "findings_count": len(hits),
            "hits": hits,
        }

    # ------------------------------------------------------------------

    def _parse_output_file(self, path: str) -> List[Dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            return []

        hits: List[Dict[str, Any]] = []
        results = data.get("results", {})
        # results may be a dict of {url: [hit, ...]} or a flat list
        if isinstance(results, dict):
            for url, items in results.items():
                for item in items if isinstance(items, list) else [items]:
                    hits.append(
                        {
                            "url": item.get("url", url),
                            "status_code": item.get("status", 0),
                            "redirect": item.get("redirect", ""),
                            "content_length": item.get(
                                "content-length", item.get("length", 0)
                            ),
                        }
                    )
        elif isinstance(results, list):
            for item in results:
                hits.append(
                    {
                        "url": item.get("url", ""),
                        "status_code": item.get("status", 0),
                        "redirect": item.get("redirect", ""),
                        "content_length": item.get(
                            "content-length", item.get("length", 0)
                        ),
                    }
                )
        return hits
