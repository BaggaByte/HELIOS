from typing import Dict, Any
from helios.core.source_code.analyzers.js_analyzer import analyze_js_source


def analyze_ts_source(code: str, filename: str = "unknown.ts") -> Dict[str, Any]:
    # TypeScript inherits all JS vulnerabilities
    res = analyze_js_source(code, filename)
    res["language"] = "typescript"
    return res
