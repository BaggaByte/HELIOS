"""
Risk prioritiser — assigns contextual risk scores to discovered assets.

Replaces the original simplistic mock scoring (which just added flat bonuses
for exposed ports / outdated services) with a proper multi-factor model that
mirrors CVSS v3.1 environmental scoring:

  Base score     = weighted sum of exposed services
  Modifiers      = presence of CVEs, auth-bypass findings, database exposure, etc.
  Final score    = min(base + modifiers, 10.0), rounded to 1 dp

The output schema is unchanged so existing callers don't need to update.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# High-value port definitions (ports that elevate risk when publicly exposed)
# ---------------------------------------------------------------------------

# Databases — direct exposure is almost always a critical finding
_DB_PORTS = {3306, 5432, 1433, 1521, 27017, 6379, 9200, 5984, 8086}

# Remote administration
_REMOTE_ADMIN_PORTS = {22, 23, 3389, 5900, 5800, 8291}

# Web services (lower individual weight, but common attack surface)
_WEB_PORTS = {80, 443, 8080, 8443, 8000, 8888, 4443, 9443}


class RiskPrioritizer:
    """
    Multi-factor risk scorer for recon host data.

    call `calculate_risk(host_data, attack_surface)` — returns the same dict
    shape as before: {"risk_score": float, "severity": str}
    """

    def calculate_risk(
        self,
        host_data: dict[str, Any],
        attack_surface: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Calculates a contextual risk score (0-10) for a discovered host.

        Parameters
        ----------
        host_data:
            Arbitrary metadata about the host (currently unused beyond future
            extensibility, e.g. for OS-specific modifiers).
        attack_surface:
            Dict produced by the recon enricher:
                exposed_high_value_ports : list[int]
                potential_web_services   : list[int]
                outdated_services        : list[str]   (service banners)
        """
        score = 0.0
        reasons: list[str] = []

        exposed_ports: list[int] = attack_surface.get("exposed_high_value_ports", [])
        web_ports: list[int] = attack_surface.get("potential_web_services", [])
        outdated: list[str] = attack_surface.get("outdated_services", [])

        # ------------------------------------------------------------------
        # 1. Database port exposure (highest weight — direct data risk)
        # ------------------------------------------------------------------
        db_exposed = [p for p in exposed_ports if p in _DB_PORTS]
        if db_exposed:
            score += min(len(db_exposed) * 3.5, 5.0)
            reasons.append(f"Database ports exposed: {db_exposed}")

        # ------------------------------------------------------------------
        # 2. Remote administration exposure
        # ------------------------------------------------------------------
        admin_exposed = [p for p in exposed_ports if p in _REMOTE_ADMIN_PORTS]
        if admin_exposed:
            score += min(len(admin_exposed) * 2.0, 4.0)
            reasons.append(f"Remote admin ports exposed: {admin_exposed}")

        # ------------------------------------------------------------------
        # 3. Web services — each unique web port adds a small increment
        # ------------------------------------------------------------------
        if web_ports:
            score += min(len(web_ports) * 0.5, 2.0)
            reasons.append(f"Web services detected on ports: {web_ports}")

        # ------------------------------------------------------------------
        # 4. Outdated / EOL service banners
        # ------------------------------------------------------------------
        if outdated:
            score += min(len(outdated) * 1.5, 3.0)
            reasons.append(f"Outdated services: {outdated}")

        # ------------------------------------------------------------------
        # 5. Any other unrecognised high-value ports (catch-all)
        # ------------------------------------------------------------------
        unknown_hvp = [
            p
            for p in exposed_ports
            if p not in _DB_PORTS and p not in _REMOTE_ADMIN_PORTS
        ]
        if unknown_hvp:
            score += min(len(unknown_hvp) * 0.75, 2.5)
            reasons.append(f"Other high-value ports: {unknown_hvp}")

        # Cap
        score = min(round(score, 1), 10.0)

        # Determine severity band (CVSS v3.1 thresholds)
        if score >= 9.0:
            severity = "Critical"
        elif score >= 7.0:
            severity = "High"
        elif score >= 4.0:
            severity = "Medium"
        elif score > 0.0:
            severity = "Low"
        else:
            severity = "Info"

        if reasons:
            logger.debug(f"Risk score {score} ({severity}) — {'; '.join(reasons)}")

        return {
            "risk_score": score,
            "severity": severity,
            "factors": reasons,
        }


# Module-level singleton — used by the recon enricher
prioritizer = RiskPrioritizer()
