"""
dnsx plugin — fast DNS resolver and brute-forcer.

dnsx outputs one JSON object per line in `-json` mode:
  host, resolver, a, cname, mx, ns, txt, aaaa, ptr, soa, axfr, caa

Reference: https://docs.projectdiscovery.io/tools/dnsx/running
"""

from __future__ import annotations

import logging
from typing import Any

from helios.plugins.base import BasePlugin, PluginError

logger = logging.getLogger(__name__)


class DnsxPlugin(BasePlugin):
    """
    Wrapper for dnsx (https://github.com/projectdiscovery/dnsx).
    Bulk DNS resolution and subdomain bruteforce with structured output.
    """

    @property
    def name(self) -> str:
        return "dnsx"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Executes dnsx for DNS resolution, record enumeration, and brute-forcing."
        )

    # ------------------------------------------------------------------

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        target: str = payload.get("target", "").strip()
        if not target:
            raise ValueError("'target' domain or host is required for dnsx.")

        if not self.is_available("dnsx"):
            return self._not_available_error()

        timeout: int = int(payload.get("timeout", 120))
        wordlist: str = payload.get("wordlist", "")
        record_types: str = payload.get("record_types", "a,cname,mx,ns,txt")

        cmd = [
            "dnsx",
            "-d",
            target,
            "-json",
            "-silent",
            "-resp",  # include response in output
        ]
        # Add record type flags
        for rt in record_types.split(","):
            rt = rt.strip().lower()
            if rt:
                cmd += [f"-{rt}"]

        if wordlist:
            cmd += ["-w", wordlist]

        logger.info(f"[dnsx] Resolving {target!r} record_types={record_types}")

        try:
            returncode, stdout, stderr = self.run_subprocess(cmd, timeout=timeout)
        except PluginError as exc:
            return self._plugin_error(exc)

        records = self._parse_output(stdout)

        return {
            "status": "success",
            "plugin": self.name,
            "version": self.version,
            "target": target,
            "findings_count": len(records),
            "records": records,
        }

    # ------------------------------------------------------------------

    def _parse_output(self, stdout: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for record in self.parse_jsonlines(stdout):
            results.append(
                {
                    "host": record.get("host", ""),
                    "resolver": record.get("resolver", ""),
                    "a": record.get("a", []),
                    "aaaa": record.get("aaaa", []),
                    "cname": record.get("cname", []),
                    "mx": record.get("mx", []),
                    "ns": record.get("ns", []),
                    "txt": record.get("txt", []),
                    "ptr": record.get("ptr", []),
                }
            )
        return results
