import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Basic regex heuristics for dangerous PHP sinks
PHP_SINKS = {
    r"\beval\s*\(": "Execution of arbitrary code via eval()",
    r"\bsystem\s*\(": "Command execution via system()",
    r"\bshell_exec\s*\(": "Command execution via shell_exec()",
    r"\bpassthru\s*\(": "Command execution via passthru()",
    r"\bexec\s*\(": "Command execution via exec()",
    r"`.*`": "Command execution via backticks (`)",
    r"\$\_GET\s*\[": "Direct use of untrusted user input ($_GET). Potential XSS/Injection.",
    r"\$\_POST\s*\[": "Direct use of untrusted user input ($_POST). Potential XSS/Injection.",
    r"\$\_REQUEST\s*\[": "Direct use of untrusted user input ($_REQUEST). Potential XSS/Injection.",
}


def analyze_php_source(code: str, filename: str = "unknown.php") -> dict[str, Any]:
    """
    Parses PHP source code using regex heuristics to find vulnerabilities.
    """
    findings = []

    lines = code.split("\n")
    for i, line in enumerate(lines):
        line_num = i + 1
        # Skip commented lines roughly
        if line.strip().startswith("//") or line.strip().startswith("#"):
            continue

        for pattern, description in PHP_SINKS.items():
            if re.search(pattern, line):
                # Distinguish between input variables (INFO/MEDIUM) and command injection (HIGH)
                severity = "HIGH"
                if "$_" in pattern:
                    severity = "MEDIUM"

                findings.append(
                    {
                        "type": "VULNERABILITY",
                        "severity": severity,
                        "line": line_num,
                        "description": description,
                    }
                )

    return {"language": "php", "filename": filename, "security_findings": findings}
