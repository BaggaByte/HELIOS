"""
Golden-file unit tests for the Nmap XML parser.

Tests cover:
- Basic single-host parse (open ports, OS, hostname, banner)
- Multi-host parse with one down host filtered correctly
- only_open=True skips closed ports
- Empty / down-only scan returns empty list
- Invalid XML raises ValueError
- Helper utilities: get_open_ports, filter_by_service
"""

import pytest
from pathlib import Path

from helios.core.recon.parsers.nmap import (
    parse_nmap_xml,
    get_open_ports,
    filter_by_service,
)

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _load(filename: str) -> bytes:
    return (FIXTURES / filename).read_bytes()


# ── Single host ───────────────────────────────────────────────────────────────

class TestSingleHost:
    def setup_method(self):
        self.hosts = parse_nmap_xml(_load("nmap_basic.xml"), only_open=True)

    def test_returns_one_host(self):
        assert len(self.hosts) == 1

    def test_ip_address(self):
        assert self.hosts[0]["ip"] == "10.0.0.1"

    def test_mac_and_vendor(self):
        assert self.hosts[0]["mac"] == "AA:BB:CC:DD:EE:FF"
        assert self.hosts[0]["vendor"] == "Acme Corp"

    def test_hostname_parsed(self):
        assert "web01.acme.com" in self.hosts[0]["hostnames"]

    def test_os_detection(self):
        h = self.hosts[0]
        assert "Linux" in (h["os"] or "")
        assert h["os_accuracy"] == 95
        assert h["os_family"] == "Linux"
        assert any("linux" in cpe for cpe in (h["os_cpe"] or []))

    def test_open_ports_only(self):
        """only_open=True — port 443 (closed) must be excluded."""
        ports = {s["port"] for s in self.hosts[0]["services"]}
        assert 22 in ports
        assert 80 in ports
        assert 443 not in ports

    def test_service_details(self):
        ssh = next(s for s in self.hosts[0]["services"] if s["port"] == 22)
        assert ssh["name"] == "ssh"
        assert ssh["product"] == "OpenSSH"
        assert "8.9" in (ssh["version"] or "")

    def test_banner_captured(self):
        ssh = next(s for s in self.hosts[0]["services"] if s["port"] == 22)
        assert ssh["banner"] is not None
        assert "OpenSSH" in ssh["banner"]


class TestSingleHostWithClosed:
    """include_closed=True should add port 443."""

    def test_closed_port_included_when_requested(self):
        hosts = parse_nmap_xml(
            _load("nmap_basic.xml"),
            only_open=False,
            include_closed=True,
        )
        ports = {s["port"] for s in hosts[0]["services"]}
        assert 443 in ports

    def test_closed_port_state_correct(self):
        hosts = parse_nmap_xml(
            _load("nmap_basic.xml"),
            only_open=False,
            include_closed=True,
        )
        port_443 = next(s for s in hosts[0]["services"] if s["port"] == 443)
        assert port_443["state"] == "closed"


# ── Multi-host ────────────────────────────────────────────────────────────────

class TestMultiHost:
    def setup_method(self):
        self.hosts = parse_nmap_xml(_load("nmap_multi_host.xml"), only_open=True)

    def test_only_up_hosts_returned(self):
        """Third host is 'down' — must be excluded."""
        assert len(self.hosts) == 2

    def test_ips_correct(self):
        ips = {h["ip"] for h in self.hosts}
        assert ips == {"192.168.1.1", "192.168.1.2"}

    def test_hostname_on_dc(self):
        dc = next(h for h in self.hosts if h["ip"] == "192.168.1.2")
        assert "dc01.corp.local" in dc["hostnames"]

    def test_rdp_on_first_host(self):
        h1 = next(h for h in self.hosts if h["ip"] == "192.168.1.1")
        ports = {s["port"] for s in h1["services"]}
        assert 3389 in ports

    def test_ad_ports_on_dc(self):
        dc = next(h for h in self.hosts if h["ip"] == "192.168.1.2")
        ports = {s["port"] for s in dc["services"]}
        assert {53, 88, 135}.issubset(ports)


# ── Empty / down-only scan ────────────────────────────────────────────────────

def test_empty_scan_returns_empty_list():
    hosts = parse_nmap_xml(_load("nmap_empty.xml"), only_open=True)
    assert hosts == []


# ── Invalid XML ───────────────────────────────────────────────────────────────

def test_invalid_xml_raises_value_error():
    with pytest.raises(ValueError, match="Invalid Nmap XML"):
        parse_nmap_xml(b"this is not xml at all")


def test_truncated_xml_raises_value_error():
    with pytest.raises(ValueError):
        parse_nmap_xml(b"<nmaprun><host><status state='up'")


# ── String input ─────────────────────────────────────────────────────────────

def test_accepts_string_input():
    xml_str = _load("nmap_basic.xml").decode("utf-8")
    hosts = parse_nmap_xml(xml_str)
    assert len(hosts) == 1


# ── Helper utilities ─────────────────────────────────────────────────────────

class TestHelpers:
    def setup_method(self):
        self.hosts = parse_nmap_xml(_load("nmap_multi_host.xml"), only_open=True)

    def test_get_open_ports(self):
        port_map = get_open_ports(self.hosts)
        assert 22 in port_map["192.168.1.1"]
        assert 3389 in port_map["192.168.1.1"]
        assert 53 in port_map["192.168.1.2"]

    def test_filter_by_service_ssh(self):
        ssh_hosts = filter_by_service(self.hosts, "ssh")
        assert len(ssh_hosts) == 1
        assert ssh_hosts[0]["ip"] == "192.168.1.1"

    def test_filter_by_service_nonexistent(self):
        result = filter_by_service(self.hosts, "ftp")
        assert result == []

    def test_filter_by_service_case_insensitive(self):
        result = filter_by_service(self.hosts, "SSH")
        assert len(result) == 1
