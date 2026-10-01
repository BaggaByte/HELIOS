from typing import Dict, Any
from helios.core.source_code.pattern_matcher import run_pattern_matcher

CSHARP_RULES = {
    r"Process\.Start\(": "Potential command injection via Process.Start().",
    r"SqlCommand\(": "Potential SQL injection if inputs are unparameterized.",
    r"MD5\.Create\(": "Use of weak cryptographic algorithm (MD5).",
    r"BinaryFormatter\.Deserialize\(": "Insecure deserialization via BinaryFormatter.",
}


def analyze_csharp_source(code: str, filename: str = "unknown.cs") -> Dict[str, Any]:
    return run_pattern_matcher(code, "csharp", filename, CSHARP_RULES)
