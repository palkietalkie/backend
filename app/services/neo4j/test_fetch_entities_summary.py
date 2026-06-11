import uuid

import pytest

from app.services.neo4j import fetch_entities_summary as fetch_entities_summary_mod
from app.services.neo4j._fakes import FakeDriver
from app.services.neo4j.fetch_entities_summary import fetch_entities_summary


async def test_fetch_entities_summary_formats_descriptors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeDriver()
    fake.fake_session.enqueue(
        [{"name": "Alice", "type": "person"}, {"name": "Tokyo", "type": "place"}]
    )
    monkeypatch.setattr(fetch_entities_summary_mod, "get_neo4j_driver", lambda: fake)
    descriptors = await fetch_entities_summary(uuid.uuid4(), limit=5)
    assert descriptors == ["Alice (person)", "Tokyo (place)"]
