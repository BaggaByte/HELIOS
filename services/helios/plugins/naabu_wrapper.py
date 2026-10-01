"""
Naabu plugin — fast port scanner from ProjectDiscovery.

Naabu outputs JSON-lines when invoked with `-json`:
  { "ip": "1.2.3.4", "port": 80, "protocol": "tcp" }

Reference: https://docs.projectdiscovery.io/tools/naabu/running
"""

from __future__ import annotations

import logging
from typing import Any

from helios.plugins.base import BasePlugin, PluginError

logger = logging.getLogger(__name__)


class NaabuPlugin(BasePlugin):
    """
    Wrapper for Naabu (https://github.com/projectdiscovery/naabu).
    Fast SYN/CONNECT port scanner optimised for large address spaces.
    """

    @property
    def name(self) -> str:
        return "naabu"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Executes Naabu for fast TCP/UDP port scanning."

    # ------------------------------------------------------------------

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        target: str = payload.get("target", "").strip()
        if not target:
            raise ValueError("'target' IP/CIDR/domain is required for Naabu.")

        if not self.is_available("naabu"):
            return self._not_available_error()

        ports: str = payload.get("ports", "top-1000")  # naabu accepts top-N or ranges
        timeout: int = int(payload.get("timeout", 300))
        rate: int = int(payload.get("rate", 1000))

        cmd = [
            "naabu",
            "-host",
            target,
            "-json",
            "-silent",
            "-rate",
            str(rate),
            "-no-color",
        ]

        # ports can be "top-1000", "80,443", or "1-65535"
        if ports.startswith("top-"):
            cmd += ["-top-ports", ports[4:]]
        else:
            cmd += ["-p", ports]

        logger.info(f"[naabu] Scanning {target!r} ports={ports}")

        try:
            returncode, stdout, stderr = self.run_subprocess(cmd, timeout=timeout)
        except PluginError as exc:
            return self._plugin_error(exc)

        open_ports = self._parse_output(stdout)

        return {
            "status": "success",
            "plugin": self.name,
            "version": self.version,
            "target": target,
            "findings_count": len(open_ports),
            "open_ports": open_ports,
        }

    # ------------------------------------------------------------------

    def _parse_output(self, stdout: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for record in self.parse_jsonlines(stdout):
            results.append(
                {
                    "ip": record.get("ip", ""),
                    "port": record.get("port", 0),
                    "protocol": record.get("protocol", "tcp"),
                }
            )
        return results
