import xml.etree.ElementTree as ET
from typing import Any


def parse_burp_xml(xml_content: str) -> list[dict[str, Any]]:
    """
    Parses a Burp Suite XML report and extracts issues.
    """
    findings = []
    try:
        root = ET.fromstring(xml_content)
        for issue in root.findall(".//issue"):
            title = issue.findtext("name", default="Unknown Burp Issue")
            desc = issue.findtext("issueDetail", default="")
            severity_text = issue.findtext("severity", default="Information").lower()
            confidence = issue.findtext("confidence", default="Certain").lower()
            remediation = issue.findtext("remediationBackground", default="")

            # Map Burp severity to our format
            severity = "info"
            if severity_text in ["high", "medium", "low"]:
                severity = severity_text

            findings.append(
                {
                    "title": title,
                    "description": desc,
                    "severity": severity,
                    "confidence": confidence,
                    "remediation": remediation,
                    "status": "observed",
                    "cwe_id": None,
                }
            )
    except Exception:
        pass
    return findings
