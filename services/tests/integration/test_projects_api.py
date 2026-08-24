"""
Integration tests for the /api/v1/projects CRUD endpoints.

Each test is fully self-contained — it creates any data it needs within
the same function so the in-memory DB session stays consistent.
"""

import pytest


@pytest.mark.asyncio
async def test_list_projects_empty(client):
    r = await client.get("/api/v1/projects")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_create_project_returns_201(client):
    r = await client.post(
        "/api/v1/projects",
        json={"name": "ACME Corp Pentest", "scope": "*.acme.com"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "ACME Corp Pentest"
    assert data["scope"] == "*.acme.com"
    assert data["status"] == "active"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_project_with_out_of_scope(client):
    r = await client.post(
        "/api/v1/projects",
        json={
            "name": "Full Pentest",
            "scope": "*.acme.com",
            "out_of_scope": "payments.acme.com",
        },
    )
    assert r.status_code == 201
    assert r.json()["out_of_scope"] == "payments.acme.com"


@pytest.mark.asyncio
async def test_create_project_missing_scope_fails(client):
    r = await client.post("/api/v1/projects", json={"name": "No Scope"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_get_project_by_id(client):
    create = await client.post(
        "/api/v1/projects",
        json={"name": "Get Test", "scope": "10.0.0.0/8"},
    )
    assert create.status_code == 201
    pid = create.json()["id"]

    r = await client.get(f"/api/v1/projects/{pid}")
    assert r.status_code == 200
    assert r.json()["id"] == pid


@pytest.mark.asyncio
async def test_get_nonexistent_project_returns_404(client):
    r = await client.get("/api/v1/projects/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_project(client):
    create = await client.post(
        "/api/v1/projects",
        json={"name": "Original Name", "scope": "10.0.0.0/8"},
    )
    pid = create.json()["id"]

    r = await client.put(f"/api/v1/projects/{pid}", json={"name": "Updated Name"})
    assert r.status_code == 200
    assert r.json()["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_update_scope(client):
    create = await client.post(
        "/api/v1/projects",
        json={"name": "Scope Test", "scope": "10.0.0.0/8"},
    )
    pid = create.json()["id"]

    r = await client.post(
        f"/api/v1/projects/{pid}/scope",
        json={"scope": "192.168.0.0/16", "out_of_scope": "192.168.1.0/24"},
    )
    assert r.status_code == 200
    assert r.json()["scope"] == "192.168.0.0/16"
    assert r.json()["out_of_scope"] == "192.168.1.0/24"


@pytest.mark.asyncio
async def test_delete_project(client):
    create = await client.post(
        "/api/v1/projects",
        json={"name": "Delete Me", "scope": "10.0.0.0/8"},
    )
    pid = create.json()["id"]

    r = await client.delete(f"/api/v1/projects/{pid}")
    assert r.status_code == 204

    r = await client.get(f"/api/v1/projects/{pid}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_projects_after_creates(client):
    await client.post("/api/v1/projects", json={"name": "P1", "scope": "1.1.1.0/24"})
    await client.post("/api/v1/projects", json={"name": "P2", "scope": "2.2.2.0/24"})

    r = await client.get("/api/v1/projects")
    assert r.status_code == 200
    names = [p["name"] for p in r.json()]
    assert "P1" in names
    assert "P2" in names
