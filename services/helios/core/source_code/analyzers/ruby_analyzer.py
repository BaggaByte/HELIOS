from typing import Any

from helios.core.source_code.pattern_matcher import run_pattern_matcher

RUBY_RULES = {
    r"\beval\s*\(": "Execution of arbitrary code via eval().",
    r"\bexec\s*\(": "Potential command injection via exec().",
    r"system\(": "Potential command injection via system().",
    r"`.*`": "Potential command injection via backticks.",
    r"send\(": "Dynamic method invocation via send(). Can lead to RCE if user-controlled.",
}


def analyze_ruby_source(code: str, filename: str = "unknown.rb") -> dict[str, Any]:
    return run_pattern_matcher(code, "ruby", filename, RUBY_RULES)
