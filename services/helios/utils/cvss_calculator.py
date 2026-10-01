"""
CVSS v3.1 base score calculator.

The previous version of this file computed scores by string-matching a
couple of hardcoded C/I/A substrings and returning a flat 5.0 for anything
that didn't match (its own docstring called it "a simplified mock for
demonstration"). That's not safe for a security tool to surface as a real
score: e.g. "CVSS:3.1/AV:L/AC:H/PR:H/UI:R/S:U/C:L/I:N/A:N" (correct base
score 1.8, Low) matched the "C:L/I:N/A:N" branch and returned 3.3 — wrong
severity band entirely, purely because Attack Vector / Complexity /
Privileges / User Interaction were never looked at.

This implements the actual FIRST.org CVSS v3.1 base-score formula. Same
function names/signatures as before so nothing that already calls this
needs to change.
"""

from __future__ import annotations

import math

# Metric weight tables (CVSS v3.1 spec)
_AV = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2}
_AC = {"L": 0.77, "H": 0.44}
_PR_UNCHANGED = {"N": 0.85, "L": 0.62, "H": 0.27}
_PR_CHANGED = {"N": 0.85, "L": 0.68, "H": 0.5}
_UI = {"N": 0.85, "R": 0.62}
_CIA = {"N": 0.0, "L": 0.22, "H": 0.56}

_REQUIRED_METRICS = ("AV", "AC", "PR", "UI", "S", "C", "I", "A")


def _roundup(value: float) -> float:
    """CVSS spec's specific 'round up to 1 decimal' function."""
    int_value = round(value * 100000)
    if int_value % 10000 == 0:
        return int_value / 100000
    return (math.floor(int_value / 10000) + 1) / 10.0


def _parse_vector(vector: str) -> dict:
    vector = vector.strip()
    if vector.startswith(("CVSS:3.1/", "CVSS:3.0/")):
        vector = vector.split("/", 1)[1]

    metrics = {}
    for part in vector.split("/"):
        if not part or ":" not in part:
            continue
        key, value = part.split(":", 1)
        metrics[key] = value
    return metrics


def calculate_cvss3_base_score(vector: str) -> float:
    """
    Parse a CVSSv3.1 vector string and compute its real base score
    (0.0-10.0) per the FIRST.org specification. Returns 0.0 for a vector
    that isn't CVSS v3, is missing required metrics, or uses an invalid
    metric value — never a guessed/default score.
    """
    if not vector or not vector.startswith("CVSS:3"):
        return 0.0

    metrics = _parse_vector(vector)
    if any(m not in metrics for m in _REQUIRED_METRICS):
        return 0.0

    scope_changed = metrics["S"] == "C"
    pr_table = _PR_CHANGED if scope_changed else _PR_UNCHANGED

    try:
        av = _AV[metrics["AV"]]
        ac = _AC[metrics["AC"]]
        pr = pr_table[metrics["PR"]]
        ui = _UI[metrics["UI"]]
        c = _CIA[metrics["C"]]
        i = _CIA[metrics["I"]]
        a = _CIA[metrics["A"]]
    except KeyError:
        return 0.0

    iss = 1 - ((1 - c) * (1 - i) * (1 - a))

    if scope_changed:
        impact = 7.52 * (iss - 0.029) - 3.25 * ((iss - 0.02) ** 15)
    else:
        impact = 6.42 * iss

    exploitability = 8.22 * av * ac * pr * ui

    if impact <= 0:
        return 0.0
    if scope_changed:
        return round(_roundup(min(1.08 * (impact + exploitability), 10)), 1)
    return round(_roundup(min(impact + exploitability, 10)), 1)


def get_severity_from_score(score: float) -> str:
    """Maps CVSS score to qualitative severity ratings."""
    if score == 0.0:
        return "INFO"
    elif 0.1 <= score <= 3.9:
        return "LOW"
    elif 4.0 <= score <= 6.9:
        return "MEDIUM"
    elif 7.0 <= score <= 8.9:
        return "HIGH"
    elif 9.0 <= score <= 10.0:
        return "CRITICAL"
    return "UNKNOWN"
