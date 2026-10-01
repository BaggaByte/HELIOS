from typing import Any

from helios.core.source_code.analyzers.js_analyzer import analyze_js_source


def analyze_node_source(code: str, filename: str = "unknown.js") -> dict[str, Any]:
    # NodeJS inherits all JS vulnerabilities
    res = analyze_js_source(code, filename)
    res["language"] = "node"
    return res
