"""
Unit tests for JavaScript intelligence extraction.

Covers endpoint_finder, token_extractor, and the top-level analyze_js orchestrator.
"""

import pytest
from helios.core.js_intel.endpoint_finder import find_endpoints
from helios.core.js_intel.token_extractor import extract_tokens
from helios.core.js_intel.extractor import analyze_js


# ── Endpoint finder ───────────────────────────────────────────────────────────


class TestEndpointFinder:
    def test_finds_absolute_url(self):
        js = 'fetch("https://api.example.com/v1/users");'
        endpoints = find_endpoints(js)
        assert any("api.example.com" in e for e in endpoints)

    def test_finds_relative_path(self):
        js = 'axios.get("/api/v1/projects");'
        endpoints = find_endpoints(js)
        assert any("/api/v1/projects" in e for e in endpoints)

    def test_finds_multiple_endpoints(self):
        js = """
            const BASE = "https://api.example.com";
            fetch("/api/users");
            fetch("/api/findings");
        """
        endpoints = find_endpoints(js)
        assert len(endpoints) >= 2

    def test_returns_unique_endpoints(self):
        js = 'fetch("/api/v1/data"); fetch("/api/v1/data");'
        endpoints = find_endpoints(js)
        assert endpoints.count("/api/v1/data") <= 1

    def test_empty_js_returns_empty(self):
        assert find_endpoints("") == []

    def test_no_false_positives_on_html_tags(self):
        js = "// </div> </span> </a>"
        endpoints = find_endpoints(js)
        # HTML tags that are explicitly filtered should not appear
        for ep in endpoints:
            assert ep not in ["/div", "/span", "/a"]


# ── Token extractor ───────────────────────────────────────────────────────────


class TestTokenExtractor:
    def test_finds_aws_key(self):
        js = 'const key = "AKIAIOSFODNN7EXAMPLE";'
        tokens = extract_tokens(js)
        aws = [t for t in tokens if t["type"] == "AWS Access Key"]
        assert len(aws) == 1
        assert aws[0]["value"] == "AKIAIOSFODNN7EXAMPLE"

    def test_finds_jwt(self):
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        js = f'localStorage.setItem("token", "{jwt}");'
        tokens = extract_tokens(js)
        jwt_tokens = [t for t in tokens if t["type"] == "JWT"]
        assert len(jwt_tokens) >= 1

    def test_finds_stripe_key(self):
        js = 'const stripe = Stripe("pk_live_abcdefghij1234567890abcd");'
        tokens = extract_tokens(js)
        stripe = [t for t in tokens if t["type"] == "Stripe Key"]
        assert len(stripe) == 1

    def test_finds_generic_secret(self):
        js = "const api_key = 'supersecrettoken12345678';"
        tokens = extract_tokens(js)
        generic = [t for t in tokens if t["type"] == "Generic Secret"]
        assert len(generic) >= 1

    def test_empty_js_returns_empty(self):
        assert extract_tokens("") == []

    def test_no_false_positive_on_safe_code(self):
        js = "function add(a, b) { return a + b; }"
        tokens = extract_tokens(js)
        assert tokens == []

    def test_deduplication(self):
        """Same key appearing twice should only appear once."""
        js = 'const a = "AKIAIOSFODNN7EXAMPLE";\nconst b = "AKIAIOSFODNN7EXAMPLE";\n'
        tokens = extract_tokens(js)
        aws = [t for t in tokens if t["type"] == "AWS Access Key"]
        assert len(aws) == 1

    def test_token_has_type_and_value_fields(self):
        js = 'const k = "AKIAIOSFODNN7EXAMPLE";'
        tokens = extract_tokens(js)
        assert len(tokens) > 0
        for t in tokens:
            assert "type" in t
            assert "value" in t


# ── Orchestrator ─────────────────────────────────────────────────────────────


class TestAnalyzeJs:
    def test_returns_success_status(self):
        result = analyze_js("const x = 1;")
        assert result["status"] == "success"

    def test_returns_findings_structure(self):
        result = analyze_js("const x = 1;")
        assert "findings" in result
        assert "endpoints" in result["findings"]
        assert "tokens" in result["findings"]

    def test_returns_beautified_code(self):
        result = analyze_js("const x=1;const y=2;")
        assert "beautified_code" in result

    def test_full_analysis_with_secrets_and_endpoints(self):
        js = """
            const apiKey = "AKIAIOSFODNN7EXAMPLE";
            fetch("/api/v1/users");
            fetch("https://api.example.com/data");
        """
        result = analyze_js(js)
        assert result["status"] == "success"
        assert len(result["findings"]["tokens"]) >= 1
        assert len(result["findings"]["endpoints"]) >= 1
