"""
ffuf plugin — fast web fuzzer for directory and parameter discovery.

ffuf writes structured JSON to a file when invoked with `-of json -o <path>`.
The root key `results` contains an array of hit objects.

Reference: https://github.com/ffuf/ffuf
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List

from helios.plugins.base import BasePlugin, PluginError

logger = logging.getLogger(__name__)


class FfufPlugin(BasePlugin):
    """
    Wrapper for ffuf (https://github.com/ffuf/ffuf).
    Fuzzes web URLs for hidden paths, parameters, and virtual hosts.
    Requires a wordlist file to be specified in the payload.
    """

    @property
    def name(self) -> str:
        return "ffuf"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Executes ffuf for web directory and parameter fuzzing."

    # ------------------------------------------------------------------

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target: str = payload.get("target", "").strip()
        wordlist: str = payload.get("wordlist", "").strip()

        if not target:
            raise ValueError("'target' URL with FUZZ keyword is required for ffuf.")
        if not wordlist:
            raise ValueError("'wordlist' path is required for ffuf.")
        if "FUZZ" not in target:
            # Auto-append FUZZ at end of URL for directory fuzzing
            target = target.rstrip("/") + "/FUZZ"

        if not self.is_available("ffuf"):
            return self._not_available_error()

        timeout: int = int(payload.get("timeout", 300))
        filter_codes: str = payload.get("filter_codes", "")   # e.g. "404,301"
        match_codes: str = payload.get("match_codes", "")      # e.g. "200,302"
        rate: int = int(payload.get("rate", 150))

        output_file = self.temp_json_output_file(suffix=".json")
        try:
            cmd = [
                "ffuf",
                "-u", target,
                "-w", wordlist,
                "-of", "json",
                "-o", output_file,
                "-rate", str(rate),
                "-t", "50",          # threads
                "-s",                # silent (no banner)
            ]
            if filter_codes:
                cmd += ["-fc", filter_codes]
            if match_codes:
                cmd += ["-mc", match_codes]

            logger.info(f"[ffuf] Fuzzing {target!r} wordlist={wordlist!r}")

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
        for r in data.get("results", []):
            hits.append({
                "url": r.get("url", ""),
                "status": r.get("status", 0),
                "length": r.get("length", 0),
                "words": r.get("words", 0),
                "lines": r.get("lines", 0),
                "redirectlocation": r.get("redirectlocation", ""),
                "input": r.get("input", {}),
            })
        return hits
