from typing import Dict, Any
from helios.core.js_intel.deobfuscator import beautify_js
from helios.core.js_intel.endpoint_finder import find_endpoints
from helios.core.js_intel.token_extractor import extract_tokens

def analyze_js(raw_js: str) -> Dict[str, Any]:
    """
    Main orchestration function for JavaScript static analysis.
    """
    beautified_code = beautify_js(raw_js)
    
    endpoints = find_endpoints(beautified_code)
    tokens = extract_tokens(beautified_code)
    
    return {
        "status": "success",
        "beautified_code": beautified_code,
        "findings": {
            "endpoints": endpoints,
            "tokens": tokens
        }
    }
