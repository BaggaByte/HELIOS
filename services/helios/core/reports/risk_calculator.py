from typing import List, Dict, Any


# Severity weights used for the composite risk score (CVSS v3-aligned).
# The score is a weighted combination of finding severity distribution and
# the maximum individual CVSS score observed.
_SEVERITY_WEIGHTS = {
    "critical": 10.0,
    "high": 7.0,
    "medium": 4.0,
    "low": 1.5,
    "info": 0.0,
}


def calculate_project_risk(findings: List[Any]) -> Dict[str, Any]:
    """
    Calculate the overall project risk from a list of Finding ORM objects.

    Returns a dict that always includes:
      - score     : float 0–10  (composite risk score, *always* present)
      - level     : str         ("Critical" | "High" | "Medium" | "Low")
      - max_cvss  : float       (highest individual CVSS score)
      - avg_cvss  : float       (mean CVSS score across all findings)
      - counts    : dict        (per-severity finding counts)

    Score methodology
    ─────────────────
    1. Start from the maximum CVSS score observed (max_cvss, range 0–10).
    2. Add a severity-distribution bonus (capped at +2.0) that grows with the
       number and severity of additional findings beyond the worst one.
    3. Clamp the result to [0.0, 10.0] and round to one decimal place.

    This means:
    - A single Critical (CVSS 9.8) scores ≈ 9.8.
    - Multiple Highs with no CVSS data score based on their weight sum.
    - Zero findings always scores 0.0.
    """
    if not findings:
        return {
            "level": "Low",
            "score": 0.0,
            "max_cvss": 0.0,
            "avg_cvss": 0.0,
            "counts": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
        }

    counts: Dict[str, int] = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
    }
    max_cvss = 0.0
    total_cvss = 0.0
    cvss_count = 0

    for f in findings:
        sev = (f.severity or "info").lower()
        if sev in counts:
            counts[sev] += 1
        else:
            counts["info"] += 1

        if f.cvss_score is not None:
            cvss = float(f.cvss_score)
            max_cvss = max(max_cvss, cvss)
            total_cvss += cvss
            cvss_count += 1

    avg_cvss = total_cvss / cvss_count if cvss_count else 0.0

    # ── Composite score ────────────────────────────────────────────────────
    # Base = maximum CVSS observed. When no CVSS data is present, estimate
    # from the worst observed severity using the weight table.
    if max_cvss > 0.0:
        base_score = max_cvss
    else:
        # Infer from severity distribution
        worst_sev = next(
            (s for s in ("critical", "high", "medium", "low", "info") if counts[s] > 0),
            "info",
        )
        base_score = _SEVERITY_WEIGHTS[worst_sev]

    # Distribution bonus: sum of weights of all findings beyond the first,
    # scaled so that 10 additional highs add at most +2.0 to the score.
    weight_sum = sum(_SEVERITY_WEIGHTS.get(s, 0.0) * n for s, n in counts.items())
    # Subtract the single heaviest finding already counted in base_score
    heaviest_weight = _SEVERITY_WEIGHTS.get(
        next(
            (s for s in ("critical", "high", "medium", "low", "info") if counts[s] > 0),
            "info",
        ),
        0.0,
    )
    distribution_bonus = min((weight_sum - heaviest_weight) / 50.0 * 2.0, 2.0)

    score = min(base_score + distribution_bonus, 10.0)
    score = round(score, 1)

    # ── Risk level ─────────────────────────────────────────────────────────
    if counts["critical"] > 0 or score >= 9.0:
        level = "Critical"
    elif counts["high"] > 0 or score >= 7.0:
        level = "High"
    elif counts["medium"] > 0 or score >= 4.0:
        level = "Medium"
    else:
        level = "Low"

    return {
        "level": level,
        "score": score,
        "max_cvss": round(max_cvss, 1),
        "avg_cvss": round(avg_cvss, 1),
        "counts": counts,
    }
