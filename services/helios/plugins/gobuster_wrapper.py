"""
Gobuster plugin — directory / vhost / DNS brute-forcing.

Gobuster does not natively output JSON, so we parse its stdout line-by-line.
Each hit line looks like:
  /admin                (Status: 200) [Size: 1234]

Reference: https://github.com/OJ/gobuster
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

from helios.plugins.base import BasePlugin, PluginError

logger = logging.getLogger(__name__)

# Regex for the standard "dir" mode output line
_LINE_RE = re.compile(
    r"^(?P<path>\S+)\s+\(Status:\s*(?P<status>\d+)\)(?:\s+\[Size:\s*(?P<size>\d+)\])?",
    re.IGNORECASE,
)


class GobusterPlugin(BasePlugin):
    """
    Wrapper for gobuster (https://github.com/OJ/gobuster).
    Brute-forces directories / DNS subdomains / virtual hosts.
    """

    @property
    def name(self) -> str:
        return "gobuster"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Executes Gobuster for directory and vhost brute-forcing."

    # ------------------------------------------------------------------

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target: str = payload.get("target", "").strip()
        wordlist: str = payload.get("wordlist", "").strip()
        mode: str = payload.get("mode", "dir")    # dir | dns | vhost

        if not target:
            raise ValueError("'target' URL is required for Gobuster.")
        if not wordlist:
            raise ValueError("'wordlist' path is required for Gobuster.")

        if not self.is_available("gobuster"):
            return self._not_available_error()

        timeout: int = int(payload.get("timeout", 300))
        threads: int = int(payload.get("threads", 25))
        status_codes: str = payload.get("status_codes", "200,204,301,302,307,401,403")

        cmd = [
            "gobuster", mode,
            "-u", target,
            "-w", wordlist,
            "-t", str(threads),
            "--no-error",
            "-q",           # quiet — suppress banner
        ]
        if mode == "dir":
            cmd += ["-s", status_codes]

        logger.info(f"[gobuster] mode={mode} target={target!r}")

        try:
            returncode, stdout, stderr = self.run_subprocess(cmd, timeout=timeout)
        except PluginError as exc:
            return self._plugin_error(exc)

        hits = self._parse_output(stdout, mode)

        return {
            "status": "success",
            "plugin": self.name,
            "version": self.version,
            "target": target,
            "mode": mode,
            "findings_count": len(hits),
            "hits": hits,
        }

    # ------------------------------------------------------------------

    def _parse_output(self, stdout: str, mode: str) -> List[Dict[str, Any]]:
        hits: List[Dict[str, Any]] = []
        for line in stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("=") or line.startswith("//"):
                continue

            if mode == "dir":
                m = _LINE_RE.match(line)
                if m:
                    hits.append({
                        "path": m.group("path"),
                        "status_code": int(m.group("status") or 0),
                        "size": int(m.group("size") or 0) if m.group("size") else None,
                    })
            else:
                # DNS / vhost mode — lines are just the discovered host/domain
                hits.append({"host": line})

        return hits
