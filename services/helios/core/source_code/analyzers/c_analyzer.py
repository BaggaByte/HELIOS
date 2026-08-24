from typing import Dict, Any
from helios.core.source_code.pattern_matcher import run_pattern_matcher

C_RULES = {
    r'\bgets\s*\(': 'Use of inherently insecure gets() function. Leads to buffer overflows.',
    r'\bstrcpy\s*\(': 'Potential buffer overflow via strcpy(). Consider strncpy().',
    r'\bsprintf\s*\(': 'Potential buffer overflow via sprintf(). Consider snprintf().',
    r'\bsystem\s*\(': 'Potential command injection via system().'
}

def analyze_c_source(code: str, filename: str = "unknown.c") -> Dict[str, Any]:
    return run_pattern_matcher(code, 'c', filename, C_RULES)

def analyze_cpp_source(code: str, filename: str = "unknown.cpp") -> Dict[str, Any]:
    return run_pattern_matcher(code, 'cpp', filename, C_RULES)
