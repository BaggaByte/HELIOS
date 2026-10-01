from typing import Dict, Any
from helios.core.source_code.pattern_matcher import run_pattern_matcher

JAVA_RULES = {
    r"Runtime\.getRuntime\(\)\.exec\(": "Potential command injection via Runtime.exec().",
    r"Statement\.executeQuery\(": "Potential SQL injection if inputs are unescaped.",
    r"ObjectInputStream\.readObject\(": "Potential insecure deserialization via readObject().",
    r'MessageDigest\.getInstance\("MD5"\)': "Use of weak cryptographic algorithm (MD5).",
}


def analyze_java_source(code: str, filename: str = "unknown.java") -> Dict[str, Any]:
    return run_pattern_matcher(code, "java", filename, JAVA_RULES)
