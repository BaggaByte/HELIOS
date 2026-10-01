"""
Abstract base class for all HELIOS security tool plugins.

Provides reusable helpers for:
  - running external binaries via subprocess with timeout and size limits
  - checking whether a binary exists in PATH
  - normalising finding severity strings
  - uniform error-result shape so callers don't need to inspect exception types
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tempfile
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)

# Default execution timeout (seconds). Individual plugins may override.
DEFAULT_TIMEOUT: int = 300  # 5 minutes

# Hard cap on stdout we'll buffer (bytes) — prevents OOM on noisy tools.
MAX_OUTPUT_BYTES: int = 50 * 1024 * 1024  # 50 MB


class PluginError(RuntimeError):
    """Raised when a plugin cannot complete its task."""


class BasePlugin(ABC):
    """Abstract Base Class for all HELIOS plugins."""

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of the plugin (must match the URL slug)."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Semver string for the plugin."""

    @property
    @abstractmethod
    def description(self) -> str:
        """One-line description of what the plugin does."""

    @abstractmethod
    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Main execution entry-point.
        `payload` is the request body passed by the caller.
        Returns a dict with at minimum a `status` key ("success" | "error").
        """

    # ------------------------------------------------------------------
    # Shared helper: binary availability check
    # ------------------------------------------------------------------

    @staticmethod
    def is_available(binary_name: str) -> bool:
        """Return True if *binary_name* can be found in the system PATH."""
        return shutil.which(binary_name) is not None

    # ------------------------------------------------------------------
    # Shared helper: subprocess runner
    # ------------------------------------------------------------------

    @staticmethod
    def run_subprocess(
        cmd: list[str],
        timeout: int = DEFAULT_TIMEOUT,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        input_data: bytes | None = None,
    ) -> tuple[int, str, str]:
        """
        Run *cmd* as a subprocess, capturing stdout/stderr.

        Returns:
            (returncode, stdout_str, stderr_str)

        Raises:
            PluginError: on timeout or if the process cannot be started.
        """
        merged_env = {**os.environ, **(env or {})}
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                timeout=timeout,
                cwd=cwd,
                env=merged_env,
                input=input_data,
            )
            stdout = proc.stdout[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
            stderr = proc.stderr[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
            return proc.returncode, stdout, stderr
        except subprocess.TimeoutExpired:
            raise PluginError(f"Command timed out after {timeout}s: {' '.join(cmd)}")
        except FileNotFoundError:
            raise PluginError(
                f"Binary not found: {cmd[0]!r}. "
                f"Ensure it is installed and available in PATH."
            )
        except Exception as exc:
            raise PluginError(f"Subprocess error: {exc}") from exc

    # ------------------------------------------------------------------
    # Shared helper: temp-file context
    # ------------------------------------------------------------------

    @staticmethod
    def temp_json_output_file(suffix: str = ".json") -> str:
        """
        Create a named temp file for JSON output and return its path.
        The caller is responsible for deleting it (use try/finally).
        """
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        return path

    # ------------------------------------------------------------------
    # Shared helper: JSON-lines parser
    # ------------------------------------------------------------------

    @staticmethod
    def parse_jsonlines(text: str) -> list[dict[str, Any]]:
        """
        Parse a newline-delimited JSON stream (common in Go security tools).
        Silently skips malformed lines.
        """
        results: list[dict[str, Any]] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                logger.debug(f"Skipping non-JSON line: {line[:120]}")
        return results

    # ------------------------------------------------------------------
    # Shared helper: severity normaliser
    # ------------------------------------------------------------------

    _SEVERITY_MAP: dict[str, str] = {
        "critical": "critical",
        "crit": "critical",
        "high": "high",
        "medium": "medium",
        "med": "medium",
        "low": "low",
        "info": "info",
        "informational": "info",
        "unknown": "info",
        "": "info",
    }

    @classmethod
    def normalise_severity(cls, raw: str) -> str:
        """Map tool-specific severity strings to HELIOS severity levels."""
        return cls._SEVERITY_MAP.get((raw or "").lower().strip(), "info")

    # ------------------------------------------------------------------
    # Shared helper: not-available error response
    # ------------------------------------------------------------------

    def _not_available_error(self) -> dict[str, Any]:
        return {
            "status": "error",
            "error": (
                f"'{self.name}' binary is not installed or not in PATH. "
                f"Install it and ensure it is accessible from the command line."
            ),
            "plugin": self.name,
            "version": self.version,
        }

    def _plugin_error(self, exc: Exception) -> dict[str, Any]:
        logger.exception(f"[{self.name}] execution failed: {exc}")
        return {
            "status": "error",
            "error": str(exc),
            "plugin": self.name,
            "version": self.version,
        }
