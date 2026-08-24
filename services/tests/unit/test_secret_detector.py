"""
Unit tests for the source code secret detector.

Covers:
- AWS access key detection
- Private key header detection
- JWT token detection
- Generic API key / token patterns
- No false positive on safe code
- Multiple findings in one file
- Line number accuracy
"""

import pytest
from helios.core.source_code.analyzers.secret_detector import scan_text


# ── AWS Access Key ────────────────────────────────────────────────────────────

def test_detects_aws_access_key():
    code = 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n'
    findings = scan_text(code, "config.py")
    aws = [f for f in findings if "AWS" in f["title"]]
    assert len(aws) >= 1
    assert aws[0]["severity"] == "critical"
    assert aws[0]["line_number"] == 1


def test_no_false_positive_on_short_string():
    code = 'key = "short"\n'
    findings = scan_text(code, "config.py")
    assert findings == []


# ── Private Key ───────────────────────────────────────────────────────────────

def test_detects_rsa_private_key():
    code = "-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n-----END RSA PRIVATE KEY-----\n"
    findings = scan_text(code, "private.pem")
    pkey = [f for f in findings if "Private Key" in f["title"]]
    assert len(pkey) >= 1
    assert pkey[0]["severity"] == "critical"


def test_detects_ec_private_key():
    code = "-----BEGIN EC PRIVATE KEY-----\nMHQC...\n"
    findings = scan_text(code, "ec.pem")
    pkey = [f for f in findings if "Private Key" in f["title"]]
    assert len(pkey) >= 1


# ── JWT ───────────────────────────────────────────────────────────────────────

def test_detects_jwt_token():
    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    code = f'const token = "{jwt}";\n'
    findings = scan_text(code, "app.js")
    jwt_findings = [f for f in findings if "JWT" in f["title"]]
    assert len(jwt_findings) >= 1
    assert jwt_findings[0]["severity"] == "medium"


# ── Generic API Key ───────────────────────────────────────────────────────────

def test_detects_generic_api_key():
    code = "api_key = 'abcdef1234567890abcdef1234567890'\n"
    findings = scan_text(code, "settings.py")
    generic = [f for f in findings if "API Key" in f["title"] or "Generic" in f["title"]]
    assert len(generic) >= 1


def test_detects_secret_token():
    code = 'token = "supersecrettoken12345678"\n'
    findings = scan_text(code, "auth.py")
    # At least one finding should reference a token
    assert any("token" in f["title"].lower() or "secret" in f["title"].lower() or "API" in f["title"]
               for f in findings)


# ── Line number accuracy ──────────────────────────────────────────────────────

def test_line_number_accuracy():
    code = (
        "# This file has a secret\n"
        "import os\n"
        'AWS_SECRET = "AKIAIOSFODNN7EXAMPLE"\n'  # line 3
        "print('done')\n"
    )
    findings = scan_text(code, "app.py")
    aws = [f for f in findings if "AWS" in f["title"]]
    assert len(aws) >= 1
    assert aws[0]["line_number"] == 3


# ── Multiple findings ─────────────────────────────────────────────────────────

def test_multiple_secrets_in_file():
    code = (
        'key = "AKIAIOSFODNN7EXAMPLE"\n'
        "-----BEGIN RSA PRIVATE KEY-----\n"
    )
    findings = scan_text(code, "secrets.py")
    assert len(findings) >= 2


# ── Finding metadata ──────────────────────────────────────────────────────────

def test_finding_has_required_fields():
    code = 'key = "AKIAIOSFODNN7EXAMPLE"\n'
    findings = scan_text(code, "config.py")
    assert len(findings) > 0
    f = findings[0]
    for field in ("title", "description", "severity", "confidence", "cwe_id", "line_number"):
        assert field in f, f"Missing field: {field}"


def test_cwe_is_798():
    """Hardcoded credentials must be CWE-798."""
    code = 'key = "AKIAIOSFODNN7EXAMPLE"\n'
    findings = scan_text(code, "config.py")
    assert any(f["cwe_id"] == "CWE-798" for f in findings)


# ── No false positives ────────────────────────────────────────────────────────

def test_no_findings_in_clean_code():
    code = (
        "def hello_world():\n"
        "    print('Hello, world!')\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    hello_world()\n"
    )
    findings = scan_text(code, "hello.py")
    assert findings == []


def test_empty_file_returns_empty():
    findings = scan_text("", "empty.py")
    assert findings == []
