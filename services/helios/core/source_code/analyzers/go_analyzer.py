from typing import Any

from helios.core.source_code.pattern_matcher import run_pattern_matcher

GO_RULES = {
    r"exec\.Command\(": "Potential command injection via os/exec.",
    r"http\.Get\(": "Potential Server-Side Request Forgery (SSRF) via unchecked http.Get.",
    r"sql\.Open\(": "Database connection. Verify credentials are not hardcoded.",
    r"tls\.Config\{\s*InsecureSkipVerify:\s*true": "Insecure TLS configuration (InsecureSkipVerify: true).",
}


def analyze_go_source(code: str, filename: str = "unknown.go") -> dict[str, Any]:
    return run_pattern_matcher(code, "go", filename, GO_RULES)
