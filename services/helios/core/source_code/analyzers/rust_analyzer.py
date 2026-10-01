from typing import Dict, Any
from helios.core.source_code.pattern_matcher import run_pattern_matcher

RUST_RULES = {
    r"\bunsafe\s*\{": "Use of unsafe block. Memory safety guarantees are disabled here.",
    r"Command::new\(": "Potential command injection via std::process::Command.",
    r"reqwest::get\(": "Potential Server-Side Request Forgery (SSRF) if URL is user-controlled.",
}


def analyze_rust_source(code: str, filename: str = "unknown.rs") -> Dict[str, Any]:
    return run_pattern_matcher(code, "rust", filename, RUST_RULES)
