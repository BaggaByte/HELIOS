from typing import Any

from helios.core.source_code.analyzers.c_analyzer import (
    analyze_cpp_source as _analyze_cpp_source,
)


def analyze_cpp_source(code: str, filename: str = "unknown.cpp") -> dict[str, Any]:
    return _analyze_cpp_source(code, filename)
