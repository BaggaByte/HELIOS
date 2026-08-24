"""
Sanitisation helpers.

Two distinct concerns live here:

1. Making untrusted strings *safe to display* (log lines, tool banners, HTTP
   response bodies) — stripping ANSI/control characters so a malicious
   target can't inject terminal escape sequences or corrupt the UI.
2. Making untrusted strings *safe to use as subprocess arguments or file
   paths* — HELIOS shells out to nmap/masscan/ffuf/gobuster/etc. with
   user-supplied targets, so argument quoting matters.

This module was previously an empty stub; none of the plugin wrappers or
ingestion routes had a shared, tested place to do this.
"""

from __future__ import annotations

import re
import shlex
import unicodedata

# ANSI escape sequences (colour codes, cursor movement, etc.)
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
# C0/C1 control characters except tab/newline/carriage-return
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences (colour codes, cursor control) from text."""
    if not text:
        return text
    return _ANSI_RE.sub("", text)


def strip_control_chars(text: str) -> str:
    """Remove non-printable control characters, keeping tab/newline/CR."""
    if not text:
        return text
    return _CONTROL_RE.sub("", text)


def sanitize_display_text(text: str, max_length: int | None = None) -> str:
    """
    Make untrusted text (tool output, HTTP banners, log lines) safe to render
    in the UI: strips ANSI escapes and control characters, normalises unicode,
    and optionally truncates.
    """
    if not text:
        return ""
    text = strip_ansi(text)
    text = strip_control_chars(text)
    text = unicodedata.normalize("NFC", text)
    if max_length is not None and len(text) > max_length:
        text = text[:max_length] + "…"
    return text


def sanitize_filename(name: str, fallback: str = "unnamed") -> str:
    """
    Strip path separators and other filesystem-hostile characters from a
    user-supplied filename. Prevents path traversal (`../../etc/passwd`) and
    null-byte tricks when saving uploaded evidence/reports to disk.
    """
    if not name:
        return fallback

    name = name.replace("\x00", "")
    name = name.split("/")[-1].split("\\")[-1]  # strip any directory component
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", name).strip(" .")

    return name or fallback


def sanitize_shell_arg(value: str) -> str:
    """
    Quote a single value for safe inclusion in a shell command line.
    Plugin wrappers should build argument *lists* for subprocess.run and
    avoid shell=True entirely wherever possible — this exists as a defensive
    fallback for the cases where a value must be logged/replayed as a shell
    string (e.g. showing the user the exact command that was run).
    """
    return shlex.quote(value)


def truncate(text: str, max_length: int, suffix: str = "…") -> str:
    """Truncate `text` to `max_length` characters, appending `suffix` if cut."""
    if text is None:
        return ""
    if len(text) <= max_length:
        return text
    return text[: max(0, max_length - len(suffix))] + suffix
