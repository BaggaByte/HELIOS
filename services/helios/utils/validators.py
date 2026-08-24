"""
Input validation helpers.

HELIOS ingests user-supplied targets (IPs, CIDRs, domains, URLs), tool output
files, and file uploads. Every one of those needs to be validated before it
touches a subprocess (nmap/masscan/ffuf wrappers), the database, or the
project's defined scope. Previously this module was an empty stub and no
other file in the codebase filled the gap — there was no centralised
validation anywhere in a tool whose entire job is to be trustworthy about
what it scanned and reported.
"""

from __future__ import annotations

import ipaddress
import re
import uuid
from typing import Optional
from urllib.parse import urlparse

# RFC-1035-ish hostname/domain label validation
_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
    r"[a-zA-Z]{2,63}$"
)

_HASH_LENGTHS = {32: "md5", 40: "sha1", 64: "sha256", 128: "sha512"}


def is_valid_ip(value: str) -> bool:
    """True if `value` is a valid IPv4 or IPv6 address."""
    try:
        ipaddress.ip_address(value)
        return True
    except (ValueError, TypeError):
        return False


def is_valid_cidr(value: str) -> bool:
    """True if `value` is a valid IPv4 or IPv6 network in CIDR notation."""
    try:
        ipaddress.ip_network(value, strict=False)
        return True
    except (ValueError, TypeError):
        return False


def is_valid_port(value) -> bool:
    """True if `value` is an integer (or numeric string) in [1, 65535]."""
    try:
        port = int(value)
    except (TypeError, ValueError):
        return False
    return 1 <= port <= 65535


def is_valid_domain(value: str) -> bool:
    """True if `value` looks like a syntactically valid DNS domain name."""
    if not value or len(value) > 253:
        return False
    return bool(_DOMAIN_RE.match(value.rstrip(".")))


def is_valid_url(value: str, allowed_schemes: Optional[set[str]] = None) -> bool:
    """
    True if `value` parses as an absolute URL with an allowed scheme
    (defaults to http/https) and a non-empty host.
    """
    allowed_schemes = allowed_schemes or {"http", "https"}
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in allowed_schemes and bool(parsed.netloc)


def is_valid_uuid(value: str) -> bool:
    """True if `value` is a syntactically valid UUID (any version)."""
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def detect_hash_type(value: str) -> Optional[str]:
    """
    Return 'md5' / 'sha1' / 'sha256' / 'sha512' if `value` looks like a hex
    digest of that length, else None. Length-based only — not a guarantee
    the value is a *real* hash, just that it's shaped like one.
    """
    if not value or not re.fullmatch(r"[a-fA-F0-9]+", value):
        return None
    return _HASH_LENGTHS.get(len(value))


def is_valid_hash(value: str, algo: Optional[str] = None) -> bool:
    """True if `value` is a valid hex digest, optionally of a specific algo."""
    detected = detect_hash_type(value)
    if detected is None:
        return False
    return detected == algo if algo else True


def is_target_in_scope(target: str, scope_definitions: list[str]) -> bool:
    """
    True if `target` (an IP, hostname, or CIDR) falls within at least one
    entry of `scope_definitions` (each entry itself an IP, CIDR, or domain —
    matching a bare domain also matches its subdomains).

    This is a conservative, best-effort check meant to catch obvious
    out-of-scope mistakes before a scan runs — it is not a substitute for a
    signed rules-of-engagement document.
    """
    if not scope_definitions:
        return False

    target = target.strip().rstrip(".")

    for entry in scope_definitions:
        entry = entry.strip().rstrip(".")
        if not entry or entry == "*":
            return True

        # CIDR scope entry vs IP target
        if is_valid_cidr(entry) and is_valid_ip(target):
            try:
                if ipaddress.ip_address(target) in ipaddress.ip_network(entry, strict=False):
                    return True
            except ValueError:
                continue
            continue

        # Exact IP match
        if is_valid_ip(entry) and target == entry:
            return True

        # Domain match, including subdomains (e.g. scope "example.com"
        # covers target "api.example.com")
        if is_valid_domain(entry):
            if target == entry or target.endswith("." + entry):
                return True

    return False
