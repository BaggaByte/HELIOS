"""
CVSS v3.1 base score calculator.

`Finding.cvss_vector` / `Finding.cvss_score` exist on the model and are
displayed in reports, but nothing in the codebase actually computed a score
from a vector string — callers either had to hardcode a number or leave it
blank. This implements the official CVSS v3.1 base-score algorithm
(FIRST.org spec) so a vector like
"CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H" resolves to 9.8 / Critical.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Dict

# ── Metric weight tables (CVSS v3.1 spec) ────────────────────────────────────

_AV = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2}
_AC = {"L": 0.77, "H": 0.44}
_PR_UNCHANGED = {"N": 0.85, "L": 0.62, "H": 0.27}
_PR_CHANGED = {"N": 0.85, "L": 0.68, "H": 0.5}
_UI = {"N": 0.85, "R": 0.62}
_CIA = {"N": 0.0, "L": 0.22, "H": 0.56}

_REQUIRED_METRICS = ("AV", "AC", "PR", "UI", "S", "C", "I", "A")

_SEVERITY_BANDS = (
    (0.0, 0.0, "None"),
    (0.1, 3.9, "Low"),
    (4.0, 6.9, "Medium"),
    (7.0, 8.9, "High"),
    (9.0, 10.0, "Critical"),
)


@dataclass
class CVSSResult:
    base_score: float
    severity: str
    vector: str


def _roundup(value: float) -> float:
    """CVSS spec's specific 'round up to 1 decimal' function."""
    int_value = round(value * 100000)
    if int_value % 10000 == 0:
        return int_value / 100000
    return (math.floor(int_value / 10000) + 1) / 10.0


def parse_vector(vector: str) -> Dict[str, str]:
    """Parse a 'CVSS:3.1/AV:N/AC:L/...' vector string into a metric dict."""
    if not vector:
        raise ValueError("Empty CVSS vector")

    vector = vector.strip()
    if vector.startswith("CVSS:3.1/") or vector.startswith("CVSS:3.0/"):
        vector = vector.split("/", 1)[1]
    elif vector.startswith("CVSS:"):
        raise ValueError(f"Unsupported CVSS version in vector: {vector!r}")

    metrics: Dict[str, str] = {}
    for part in vector.split("/"):
        if not part:
            continue
        if ":" not in part:
            raise ValueError(f"Malformed CVSS metric segment: {part!r}")
        key, value = part.split(":", 1)
        metrics[key] = value

    missing = [m for m in _REQUIRED_METRICS if m not in metrics]
    if missing:
        raise ValueError(f"CVSS vector missing required metric(s): {', '.join(missing)}")

    return metrics


def severity_from_score(score: float) -> str:
    """Map a 0.0–10.0 base score to its CVSS qualitative severity rating."""
    for low, high, label in _SEVERITY_BANDS:
        if low <= score <= high:
            return label
    raise ValueError(f"Score out of range: {score}")


def calculate_base_score(vector: str) -> CVSSResult:
    """Compute the CVSS v3.1 base score and severity rating from a vector string."""
    m = parse_vector(vector)

    scope_changed = m["S"] == "C"
    pr_table = _PR_CHANGED if scope_changed else _PR_UNCHANGED

    try:
        av = _AV[m["AV"]]
        ac = _AC[m["AC"]]
        pr = pr_table[m["PR"]]
        ui = _UI[m["UI"]]
        c = _CIA[m["C"]]
        i = _CIA[m["I"]]
        a = _CIA[m["A"]]
    except KeyError as e:
        raise ValueError(f"Invalid CVSS metric value: {e}")

    iss = 1 - ((1 - c) * (1 - i) * (1 - a))

    if scope_changed:
        impact = 7.52 * (iss - 0.029) - 3.25 * ((iss - 0.02) ** 15)
    else:
        impact = 6.42 * iss

    exploitability = 8.22 * av * ac * pr * ui

    if impact <= 0:
        base_score = 0.0
    elif scope_changed:
        base_score = _roundup(min(1.08 * (impact + exploitability), 10))
    else:
        base_score = _roundup(min(impact + exploitability, 10))

    base_score = round(base_score, 1)
    return CVSSResult(base_score=base_score, severity=severity_from_score(base_score), vector=vector)
