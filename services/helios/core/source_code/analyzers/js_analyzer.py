import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Basic regex heuristics for dangerous JS sinks
JS_SINKS = {
    r'\beval\s*\(': 'Execution of arbitrary code via eval()',
    r'setTimeout\s*\(\s*["\']': 'Potential code execution via setTimeout with string argument',
    r'setInterval\s*\(\s*["\']': 'Potential code execution via setInterval with string argument',
    r'\.innerHTML\s*=': 'DOM-based XSS via innerHTML assignment',
    r'document\.write\s*\(': 'DOM-based XSS via document.write()',
    r'\bFunction\s*\(': 'Code execution via Function constructor'
}

def analyze_js_source(code: str, filename: str = "unknown.js") -> Dict[str, Any]:
    """
    Parses JavaScript source code using regex heuristics to find vulnerabilities.
    """
    findings = []
    
    lines = code.split('\n')
    for i, line in enumerate(lines):
        line_num = i + 1
        for pattern, description in JS_SINKS.items():
            if re.search(pattern, line):
                findings.append({
                    'type': 'VULNERABILITY',
                    'severity': 'HIGH',
                    'line': line_num,
                    'description': description
                })
                
    return {
        'language': 'javascript',
        'filename': filename,
        'security_findings': findings
    }
