"""
Nuclei plugin — real DAST / template-based vulnerability scanner.

Nuclei writes one JSON object per line to stdout when invoked with `-json`.
Each line contains: `template-id`, `info.name`, `info.severity`,
`matched-at`, `extracted-results`, `curl-command`, and more.

Reference: https://docs.projectdiscovery.io/tools/nuclei/running
"""

from __future__ import annotations

import logging
from typing import Any

from helios.plugins.base import BasePlugin, PluginError

logger = logging.getLogger(__name__)

# Nuclei severities that map directly to HELIOS severity levels.
_NUCLEI_SEVERITY_MAP = {
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
    "info": "info",
    "unknown": "info",
}


class NucleiPlugin(BasePlugin):
    """
    Wrapper for Nuclei (https://github.com/projectdiscovery/nuclei).
    Performs template-based DAST scans and ingests the JSON output as findings.
    """

    @property
    def name(self) -> str:
        return "nuclei"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Executes Nuclei for Dynamic Application Security Testing (DAST) scans."

    # ------------------------------------------------------------------

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        target: str = payload.get("target", "").strip()
        if not target:
            raise ValueError("'target' is required for Nuclei scan.")

        if not self.is_available("nuclei"):
            return self._not_available_error()

        # Optional: caller can pass extra args, e.g. ["-t", "cves/"]
        extra_args: list[str] = payload.get("extra_args", [])
        timeout: int = int(payload.get("timeout", 600))  # default 10 min

        cmd = [
            "nuclei",
            "-u",
            target,
            "-json",  # JSON-lines output on stdout
            "-silent",  # suppress banner / progress
            "-no-color",
            "-rate-limit",
            "50",  # be polite during authorised tests
        ] + extra_args

        logger.info(f"[nuclei] Scanning {target!r}  cmd={' '.join(cmd)}")

        try:
            returncode, stdout, stderr = self.run_subprocess(cmd, timeout=timeout)
        except PluginError as exc:
            return self._plugin_error(exc)

        if returncode not in (0, 1):  # nuclei exits 1 when findings exist
            logger.warning(f"[nuclei] Exited with code {returncode}: {stderr[:500]}")

        findings = self._parse_output(stdout)

        return {
            "status": "success",
            "plugin": self.name,
            "version": self.version,
            "target": target,
            "findings_count": len(findings),
            "findings": findings,
            "stderr": stderr[:2000] if stderr else "",
        }

    # ------------------------------------------------------------------

    def _parse_output(self, stdout: str) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        for record in self.parse_jsonlines(stdout):
            info = record.get("info", {})
            severity_raw = info.get("severity", "info")
            severity = _NUCLEI_SEVERITY_MAP.get(severity_raw.lower(), "info")

            findings.append(
                {
                    "title": info.get(
                        "name", record.get("template-id", "Nuclei Finding")
                    ),
                    "description": info.get("description", ""),
                    "severity": severity,
                    "matched_at": record.get("matched-at", ""),
                    "template_id": record.get("template-id", ""),
                    "extracted_results": record.get("extracted-results", []),
                    "tags": info.get("tags", []),
                    "reference": info.get("reference", []),
                    "cwe_id": None,
                    "status": "observed",
                    "source": "nuclei",
                }
            )
        return findings
