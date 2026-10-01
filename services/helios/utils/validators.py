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
        ip = ipaddress.ip_address(value)
        if ip.is_unspecified:
            return False
        return True
    except (ValueError, TypeError):
        return False


def is_valid_cidr(value: str) -> bool:
    """True if `value` is a valid IPv4 or IPv6 network in CIDR notation."""
    try:
        net = ipaddress.ip_network(value, strict=False)
        if net.prefixlen == 0:
            return False
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
    """True if `value` looks like a syntactically valid DNS domain name (including wildcards)."""
    if not value or len(value) > 253:
        return False
    
    # Strip optional leading wildcard
    if value.startswith("*."):
        value = value[2:]
        
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


def _normalize_domain(domain: str) -> str:
    """Strip leading wildcards and dots for consistent matching."""
    domain = domain.strip().rstrip(".")
    if domain.startswith("*."):
        domain = domain[2:]
    elif domain.startswith("*"):
        domain = domain[1:]
    return domain


def is_target_in_scope(target: str, scope_definitions: list[str]) -> bool:
    """
    True if `target` (an IP, hostname, or CIDR) falls within at least one
    entry of `scope_definitions`.

    Validates both the literal target string and (if the target is a hostname)
    its resolved IP address against the scope definitions to prevent DNS bypass.
    """
    if not scope_definitions:
        return False

    target = target.strip().rstrip(".")
    if not target:
        return False

    # 1. Gather all IPs the target resolves to (if it's a domain)
    target_ips = set()
    if is_valid_ip(target):
        target_ips.add(target)
    else:
        import socket
        try:
            # We resolve it to ensure we check the actual destination IP
            target_ips.add(socket.gethostbyname(target))
        except socket.gaierror:
            pass # Unresolvable, we will just check the domain name itself

    # Normalize scope entries upfront
    scope_cidrs = []
    scope_ips = set()
    scope_domains = set()

    for entry in scope_definitions:
        entry = entry.strip().rstrip(".")
        if not entry or entry == "*":
            return True
            
        if is_valid_cidr(entry):
            try:
                scope_cidrs.append(ipaddress.ip_network(entry, strict=False))
            except ValueError:
                pass
        elif is_valid_ip(entry):
            scope_ips.add(entry)
        else:
            scope_domains.add(_normalize_domain(entry))

    # 2. Check literal domain match (e.g. target="api.example.com" vs scope="*.example.com")
    if not is_valid_ip(target):
        for scope_domain in scope_domains:
            if target == scope_domain or target.endswith("." + scope_domain):
                return True

    # 3. Check resolved IP(s) against allowed IPs and CIDRs
    for ip_str in target_ips:
        if ip_str in scope_ips:
            return True
            
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            for network in scope_cidrs:
                if ip_obj in network:
                    return True
        except ValueError:
            continue

    return False
