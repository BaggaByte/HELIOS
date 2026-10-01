"""
RustScan plugin — ultra-fast port scanner (Rust-based).

RustScan by default passes found ports to nmap for service detection.
We run it with `-- -oX -` to capture nmap XML output on stdout and
hand it to the existing nmap XML parser.  Alternatively, with
`--no-nmap`, we get plain port-per-line output that we parse directly.

Reference: https://github.com/RustScan/RustScan
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

from helios.plugins.base import BasePlugin, PluginError

logger = logging.getLogger(__name__)

_PORT_LINE_RE = re.compile(r"^(\d+)$")


class RustscanPlugin(BasePlugin):
    """
    Wrapper for RustScan (https://github.com/RustScan/RustScan).
    Extremely fast open-port discovery followed by optional nmap service detection.
    """

    @property
    def name(self) -> str:
        return "rustscan"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Executes RustScan for ultra-fast port discovery."

    # ------------------------------------------------------------------

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target: str = payload.get("target", "").strip()
        if not target:
            raise ValueError("'target' IP/CIDR is required for RustScan.")

        if not self.is_available("rustscan"):
            return self._not_available_error()

        timeout: int = int(payload.get("timeout", 300))
        batch_size: int = int(payload.get("batch_size", 500))
        ports: str = payload.get("ports", "1-65535")

        # --no-nmap to get clean port list without spawning nmap
        cmd = [
            "rustscan",
            "-a", target,
            "-b", str(batch_size),
            "-r", ports,
            "--no-nmap",
            "--accessible",     # machine-readable output
            "--timeout", "1500",
        ]

        logger.info(f"[rustscan] Scanning {target!r} ports={ports}")

        try:
            returncode, stdout, stderr = self.run_subprocess(cmd, timeout=timeout)
        except PluginError as exc:
            return self._plugin_error(exc)

        open_ports = self._parse_output(stdout, target)

        return {
            "status": "success",
            "plugin": self.name,
            "version": self.version,
            "target": target,
            "findings_count": len(open_ports),
            "open_ports": open_ports,
        }

    # ------------------------------------------------------------------

    def _parse_output(self, stdout: str, target: str) -> List[Dict[str, Any]]:
        """
        RustScan --accessible prints lines like:
          Open 192.168.1.1:80
        or just the port number when scanning a single host.
        """
        results: List[Dict[str, Any]] = []
        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("Open "):
                # "Open <ip>:<port>"
                rest = line[5:]
                if ":" in rest:
                    ip, port_str = rest.rsplit(":", 1)
                    try:
                        results.append({
                            "ip": ip.strip(),
                            "port": int(port_str.strip()),
                            "protocol": "tcp",
                            "status": "open",
                        })
                    except ValueError:
                        pass
            elif _PORT_LINE_RE.match(line):
                results.append({
                    "ip": target,
                    "port": int(line),
                    "protocol": "tcp",
                    "status": "open",
                })
        return results
