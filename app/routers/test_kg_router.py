"""/kg router tests (GET fetch + DELETE soft-delete).

Combined into one uniquely-named file because pytest (no __init__.py in this tree) can't collect two test modules with the same basename, and `fetch_kg.py` / `remove_kg_entity.py` already exist under `app/services/neo4j/` with their own tests.
"""

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


async def test_remove_entity_soft_deletes_and_returns_204(
    app_with_overrides: tuple[AsyncClient, UserRow],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.routers import remove_kg_entity as remove_mod

    captured: dict[str, Any] = {}

    async def _remove(user_id: Any, name: str) -> None:
        captured["user_id"] = user_id
        captured["name"] = name

    monkeypatch.setattr(remove_mod, "remove_kg_entity_from_neo4j", _remove)
    client, user = app_with_overrides
    resp = await client.delete("/kg/Wrong%20Person")
    assert resp.status_code == 204
    assert captured["name"] == "Wrong Person"
    assert captured["user_id"] == user["id"]


async def test_remove_entity_returns_503_on_failure(
    app_with_overrides: tuple[AsyncClient, UserRow],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.routers import remove_kg_entity as remove_mod

    async def _boom(_user_id: Any, _name: str) -> None:
        raise RuntimeError("aura down")

    monkeypatch.setattr(remove_mod, "remove_kg_entity_from_neo4j", _boom)
    client, _ = app_with_overrides
    resp = await client.delete("/kg/Foo")
    assert resp.status_code == 503
