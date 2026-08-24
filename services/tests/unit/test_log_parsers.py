"""
Unit tests for log parsers (Apache combined format and Suricata fast.log).
"""

import pytest
from datetime import datetime

from helios.core.logs.parsers.apache import parse_apache_log_line
from helios.core.logs.parsers.suricata import parse_suricata_fast_log
from helios.core.logs.timeline_builder import parse_log_file


# ── Apache parser ─────────────────────────────────────────────────────────────

APACHE_200 = (
    '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] '
    '"GET /apache_pb.gif HTTP/1.0" 200 2326 '
    '"http://www.example.com/start.html" '
    '"Mozilla/4.0 (compatible; MSIE 5.5; Windows NT 5.1)"'
)

APACHE_404 = (
    '10.0.0.5 - - [15/Jan/2024:08:23:11 +0000] '
    '"GET /admin HTTP/1.1" 404 512 "-" "curl/7.88.1"'
)

APACHE_500 = (
    '10.0.0.5 - - [15/Jan/2024:08:23:12 +0000] '
    '"POST /api/data HTTP/1.1" 500 0 "-" "python-requests/2.31.0"'
)

APACHE_SQLI = (
    '10.0.0.99 - - [15/Jan/2024:09:00:00 +0000] '
    '"GET /search?q=1+UNION+SELECT+1,2,3-- HTTP/1.1" 400 0 "-" "sqlmap/1.7"'
)


class TestApacheParser:
    def test_returns_dict_for_valid_line(self):
        result = parse_apache_log_line(APACHE_200)
        assert result is not None

    def test_returns_none_for_invalid_line(self):
        assert parse_apache_log_line("not a log line") is None
        assert parse_apache_log_line("") is None

    def test_source_ip_extracted(self):
        result = parse_apache_log_line(APACHE_200)
        assert result["source_ip"] == "127.0.0.1"

    def test_timestamp_is_datetime(self):
        result = parse_apache_log_line(APACHE_200)
        assert isinstance(result["timestamp"], datetime)

    def test_source_is_apache(self):
        result = parse_apache_log_line(APACHE_200)
        assert result["source"] == "apache"

    def test_event_type(self):
        result = parse_apache_log_line(APACHE_200)
        assert result["event_type"] == "http_access"

    def test_200_severity_info(self):
        result = parse_apache_log_line(APACHE_200)
        assert result["severity"] == "info"

    def test_500_severity_medium(self):
        result = parse_apache_log_line(APACHE_500)
        assert result["severity"] == "medium"

    def test_404_severity_info(self):
        result = parse_apache_log_line(APACHE_404)
        assert result["severity"] == "info"

    def test_sqli_in_400_gets_high_severity(self):
        result = parse_apache_log_line(APACHE_SQLI)
        assert result["severity"] == "high"

    def test_metadata_contains_method(self):
        result = parse_apache_log_line(APACHE_200)
        assert result["metadata"]["method"] == "GET"

    def test_metadata_contains_status(self):
        result = parse_apache_log_line(APACHE_200)
        assert result["metadata"]["status"] == 200

    def test_metadata_contains_user_agent(self):
        result = parse_apache_log_line(APACHE_200)
        assert "MSIE" in result["metadata"]["user_agent"]


# ── Suricata parser ───────────────────────────────────────────────────────────

SURICATA_P1 = (
    '10/11/2023-14:32:01.123456  [**] [1:2010935:2] '
    'ET EXPLOIT Possible SQL Injection [**] '
    '[Classification: Web Application Attack] [Priority: 1] '
    '{TCP} 192.168.1.100:54321 -> 10.0.0.5:80'
)

SURICATA_P2 = (
    '10/11/2023-14:33:00.000001  [**] [1:2001219:20] '
    'ET SCAN Potential SSH Scan [**] '
    '[Priority: 2] '
    '{TCP} 10.10.10.10:12345 -> 192.168.1.1:22'
)

SURICATA_P3 = (
    '10/11/2023-14:34:00.000001  [**] [1:2009358:3] '
    'ET POLICY PE EXE or DLL Windows file download [**] '
    '[Priority: 3] '
    '{TCP} 172.16.0.5:443 -> 10.0.0.20:49152'
)


class TestSuricataParser:
    def test_returns_dict_for_valid_line(self):
        assert parse_suricata_fast_log(SURICATA_P1) is not None

    def test_returns_none_for_invalid_line(self):
        assert parse_suricata_fast_log("not a suricata line") is None

    def test_source_is_suricata(self):
        result = parse_suricata_fast_log(SURICATA_P1)
        assert result["source"] == "suricata"

    def test_event_type(self):
        result = parse_suricata_fast_log(SURICATA_P1)
        assert result["event_type"] == "ids_alert"

    def test_source_ip(self):
        result = parse_suricata_fast_log(SURICATA_P1)
        assert result["source_ip"] == "192.168.1.100"

    def test_dest_ip(self):
        result = parse_suricata_fast_log(SURICATA_P1)
        assert result["dest_ip"] == "10.0.0.5"

    def test_priority_1_is_high(self):
        result = parse_suricata_fast_log(SURICATA_P1)
        assert result["severity"] == "high"

    def test_priority_2_is_medium(self):
        result = parse_suricata_fast_log(SURICATA_P2)
        assert result["severity"] == "medium"

    def test_priority_3_is_low(self):
        result = parse_suricata_fast_log(SURICATA_P3)
        assert result["severity"] == "low"

    def test_alert_message_in_metadata(self):
        result = parse_suricata_fast_log(SURICATA_P1)
        assert "SQL Injection" in result["metadata"]["alert_msg"]

    def test_classification_in_metadata(self):
        result = parse_suricata_fast_log(SURICATA_P1)
        assert result["metadata"]["classification"] == "Web Application Attack"

    def test_timestamp_is_datetime(self):
        result = parse_suricata_fast_log(SURICATA_P1)
        assert isinstance(result["timestamp"], datetime)


# ── Timeline builder ──────────────────────────────────────────────────────────

class TestTimelineBuilder:
    def test_apache_log_file_parsed(self):
        log_content = "\n".join([APACHE_200, APACHE_404, APACHE_500])
        events = parse_log_file(log_content, "apache")
        assert len(events) == 3

    def test_suricata_log_file_parsed(self):
        log_content = "\n".join([SURICATA_P1, SURICATA_P2])
        events = parse_log_file(log_content, "suricata")
        assert len(events) == 2

    def test_nginx_uses_apache_parser(self):
        """nginx uses the same combined log format."""
        log_content = APACHE_200
        events = parse_log_file(log_content, "nginx")
        assert len(events) == 1

    def test_empty_lines_skipped(self):
        log_content = "\n\n" + APACHE_200 + "\n\n"
        events = parse_log_file(log_content, "apache")
        assert len(events) == 1

    def test_unsupported_type_raises(self):
        with pytest.raises(ValueError, match="Unsupported log type"):
            parse_log_file("some log content", "windows_event")

    def test_invalid_lines_skipped_gracefully(self):
        log_content = "invalid line\n" + APACHE_200 + "\nanother bad line"
        events = parse_log_file(log_content, "apache")
        # Only the valid line should produce an event
        assert len(events) == 1
