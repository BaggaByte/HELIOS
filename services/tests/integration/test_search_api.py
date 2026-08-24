"""
Integration tests for the /api/v1/projects/{id}/search endpoint.
"""

import pytest


async def _make_project(client, name: str = "Search Test") -> str:
    r = await client.post(
        "/api/v1/projects",
        json={"name": name, "scope": "10.0.0.0/8"},
    )
    assert r.status_code == 201
    return r.json()["id"]


@pytest.mark.asyncio
async def test_search_requires_min_two_chars(client):
    pid = await _make_project(client)
    r = await client.get(f"/api/v1/projects/{pid}/search?q=a")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_empty_search_returns_no_results(client):
    pid = await _make_project(client)
    r = await client.get(f"/api/v1/projects/{pid}/search?q=nonexistent999")
    assert r.status_code == 200
    body = r.json()
    assert body["results"] == []
    assert body["total"] == 0


@pytest.mark.asyncio
async def test_search_nonexistent_project_returns_404(client):
    r = await client.get(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000/search?q=test"
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_search_response_structure(client):
    pid = await _make_project(client)
    r = await client.get(f"/api/v1/projects/{pid}/search?q=acme")
    assert r.status_code == 200
    body = r.json()
    for key in ("query", "project_id", "results", "total"):
        assert key in body
    assert body["project_id"] == pid


@pytest.mark.asyncio
async def test_type_filter_accepted(client):
    pid = await _make_project(client)
    r = await client.get(f"/api/v1/projects/{pid}/search?q=test&type=finding")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_search_scope_is_project_isolated(client):
    """Findings from project A should not appear in project B's search."""
    pid_a = await _make_project(client, "Project A")
    pid_b = await _make_project(client, "Project B")

    r = await client.get(f"/api/v1/projects/{pid_b}/search?q=Project")
    assert r.status_code == 200
    for result in r.json()["results"]:
        # No results should reference project A's ID
        assert pid_a not in result.get("url", "")
