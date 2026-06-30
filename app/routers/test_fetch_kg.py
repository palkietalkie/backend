"""Knowledge-graph router tests: the read must degrade to an empty graph, never 500, when AuraDB fails. (The slow-cold-start case is handled client-side with a longer /kg timeout, not by bounding the read here, failing fast would just hand an empty graph to a user who has data.)"""

from typing import Any

import pytest
from httpx import AsyncClient

from app.services.neon.rows import UserRow


async def test_kg_returns_empty_when_neo4j_fails(
    app_with_overrides: tuple[AsyncClient, UserRow],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.routers import fetch_kg as kg_mod

    async def _boom(_user_id: Any) -> dict[str, Any]:
        raise RuntimeError("aura down")

    monkeypatch.setattr(kg_mod, "fetch_kg_from_neo4j", _boom)
    client, _ = app_with_overrides
    resp = await client.get("/kg")
    assert resp.status_code == 200
    assert resp.json() == {"nodes": [], "edges": []}


async def test_kg_returns_graph_when_neo4j_succeeds(
    app_with_overrides: tuple[AsyncClient, UserRow],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.routers import fetch_kg as kg_mod

    async def _ok(_user_id: Any) -> dict[str, Any]:
        return {
            "nodes": [{"id": "Naoto", "type": "person", "name": "Naoto", "attrs": {}}],
            "edges": [{"src": "Naoto", "rel": "works_at", "dst": "Kawasaki"}],
        }

    monkeypatch.setattr(kg_mod, "fetch_kg_from_neo4j", _ok)
    client, _ = app_with_overrides
    resp = await client.get("/kg")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["nodes"]) == 1
    assert body["edges"][0]["rel"] == "works_at"
