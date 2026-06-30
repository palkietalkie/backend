import uuid

import pytest

from app.services.neo4j import remove_kg_entity as remove_mod
from app.services.neo4j._fakes import FakeDriver
from app.services.neo4j.remove_kg_entity import remove_kg_entity


async def test_remove_soft_deletes_the_named_entity(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeDriver()
    monkeypatch.setattr(remove_mod, "get_neo4j_driver", lambda: fake)
    uid = uuid.uuid4()
    await remove_kg_entity(uid, "Wrong Entity")
    query, params = fake.fake_session.queries[-1]
    # Soft delete: set the tombstone, never DELETE the node (recoverable + sticky against re-extraction).
    assert "SET n.removed_at" in query
    assert "DELETE" not in query.upper()
    assert params == {"uid": str(uid), "name": "Wrong Entity"}
