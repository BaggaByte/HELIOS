import re
from typing import Dict, Any, List


def run_pattern_matcher(
    code: str, language: str, filename: str, rules: Dict[str, str]
) -> Dict[str, Any]:
    findings = []
    lines = code.split("\n")
    for i, line in enumerate(lines):
        for pattern, description in rules.items():
            if re.search(pattern, line):
                findings.append(
                    {
                        "type": "VULNERABILITY",
                        "severity": "HIGH",
                        "line": i + 1,
                        "description": description,
                    }
                )

    return {"language": language, "filename": filename, "security_findings": findings}
