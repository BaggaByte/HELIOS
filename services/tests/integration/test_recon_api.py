"""
Integration tests for the /api/v1/projects/{id}/recon endpoints.

Each test is fully self-contained: creates its own project and ingests
data within the same async function so the DB session stays consistent.
"""

import pytest
from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _xml_file(filename: str):
    path = FIXTURES / filename
    return ("file", (filename, path.read_bytes(), "application/xml"))


async def _make_project(client, name: str = "Recon Test") -> str:
    r = await client.post(
        "/api/v1/projects",
        json={"name": name, "scope": "10.0.0.0/8, 192.168.0.0/16"},
    )
    assert r.status_code == 201
    return r.json()["id"]


# ── Nmap ingestion ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ingest_basic_nmap(client):
    pid = await _make_project(client)
    r = await client.post(
        f"/api/v1/projects/{pid}/recon/ingest/nmap",
        files=[_xml_file("nmap_basic.xml")],
    )
    assert r.status_code == 201
    body = r.json()
    assert body["hosts_created"] == 1
    assert body["services_created"] == 2  # port 22 + 80 (443 is closed)
    assert body["total_hosts_in_file"] == 1


@pytest.mark.asyncio
async def test_ingest_multi_host_nmap(client):
    pid = await _make_project(client)
    r = await client.post(
        f"/api/v1/projects/{pid}/recon/ingest/nmap",
        files=[_xml_file("nmap_multi_host.xml")],
    )
    assert r.status_code == 201
    body = r.json()
    assert body["hosts_created"] == 2   # down host excluded
    assert body["services_created"] == 5  # 2 + 3


@pytest.mark.asyncio
async def test_ingest_empty_scan(client):
    pid = await _make_project(client)
    r = await client.post(
        f"/api/v1/projects/{pid}/recon/ingest/nmap",
        files=[_xml_file("nmap_empty.xml")],
    )
    assert r.status_code == 201
    assert r.json()["hosts_created"] == 0


@pytest.mark.asyncio
async def test_non_xml_file_rejected(client):
    pid = await _make_project(client)
    r = await client.post(
        f"/api/v1/projects/{pid}/recon/ingest/nmap",
        files=[("file", ("scan.txt", b"not xml", "text/plain"))],
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_invalid_xml_rejected(client):
    pid = await _make_project(client)
    r = await client.post(
        f"/api/v1/projects/{pid}/recon/ingest/nmap",
        files=[("file", ("scan.xml", b"<broken xml", "application/xml"))],
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_ingest_into_nonexistent_project_returns_404(client):
    r = await client.post(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000/recon/ingest/nmap",
        files=[_xml_file("nmap_basic.xml")],
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_upsert_does_not_duplicate_hosts(client):
    pid = await _make_project(client)
    for _ in range(2):
        await client.post(
            f"/api/v1/projects/{pid}/recon/ingest/nmap",
            files=[_xml_file("nmap_basic.xml")],
        )
    r = await client.get(f"/api/v1/projects/{pid}/recon/hosts")
    assert r.status_code == 200
    assert r.json()["total"] == 1


# ── Host listing & filtering ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_hosts_returns_all(client):
    pid = await _make_project(client)
    await client.post(
        f"/api/v1/projects/{pid}/recon/ingest/nmap",
        files=[_xml_file("nmap_multi_host.xml")],
    )
    r = await client.get(f"/api/v1/projects/{pid}/recon/hosts")
    assert r.status_code == 200
    assert r.json()["total"] == 2


@pytest.mark.asyncio
async def test_host_list_pagination(client):
    pid = await _make_project(client)
    await client.post(
        f"/api/v1/projects/{pid}/recon/ingest/nmap",
        files=[_xml_file("nmap_multi_host.xml")],
    )
    r = await client.get(f"/api/v1/projects/{pid}/recon/hosts?page=1&page_size=1")
    body = r.json()
    assert len(body["hosts"]) == 1
    assert body["total"] == 2


@pytest.mark.asyncio
async def test_filter_by_ip(client):
    pid = await _make_project(client)
    await client.post(
        f"/api/v1/projects/{pid}/recon/ingest/nmap",
        files=[_xml_file("nmap_multi_host.xml")],
    )
    r = await client.get(f"/api/v1/projects/{pid}/recon/hosts?ip=192.168.1.1")
    body = r.json()
    assert body["total"] == 1
    assert body["hosts"][0]["ip"] == "192.168.1.1"


@pytest.mark.asyncio
async def test_filter_by_port(client):
    pid = await _make_project(client)
    await client.post(
        f"/api/v1/projects/{pid}/recon/ingest/nmap",
        files=[_xml_file("nmap_multi_host.xml")],
    )
    r = await client.get(f"/api/v1/projects/{pid}/recon/hosts?port=3389")
    body = r.json()
    assert body["total"] == 1
    assert body["hosts"][0]["ip"] == "192.168.1.1"


@pytest.mark.asyncio
async def test_get_single_host(client):
    pid = await _make_project(client)
    await client.post(
        f"/api/v1/projects/{pid}/recon/ingest/nmap",
        files=[_xml_file("nmap_basic.xml")],
    )
    hosts = (await client.get(f"/api/v1/projects/{pid}/recon/hosts")).json()["hosts"]
    hid = hosts[0]["id"]

    r = await client.get(f"/api/v1/projects/{pid}/recon/hosts/{hid}")
    assert r.status_code == 200
    assert r.json()["id"] == hid


@pytest.mark.asyncio
async def test_get_host_wrong_project_returns_404(client):
    pid = await _make_project(client)
    await client.post(
        f"/api/v1/projects/{pid}/recon/ingest/nmap",
        files=[_xml_file("nmap_basic.xml")],
    )
    hosts = (await client.get(f"/api/v1/projects/{pid}/recon/hosts")).json()["hosts"]
    hid = hosts[0]["id"]

    other_pid = "00000000-0000-0000-0000-000000000001"
    r = await client.get(f"/api/v1/projects/{other_pid}/recon/hosts/{hid}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_host(client):
    pid = await _make_project(client)
    await client.post(
        f"/api/v1/projects/{pid}/recon/ingest/nmap",
        files=[_xml_file("nmap_multi_host.xml")],
    )
    hosts = (await client.get(f"/api/v1/projects/{pid}/recon/hosts")).json()["hosts"]
    hid = hosts[0]["id"]

    r = await client.delete(f"/api/v1/projects/{pid}/recon/hosts/{hid}")
    assert r.status_code == 204

    r = await client.get(f"/api/v1/projects/{pid}/recon/hosts")
    assert r.json()["total"] == 1
