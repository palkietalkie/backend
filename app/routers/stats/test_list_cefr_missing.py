"""Behavioral tests for GET /stats/cefr (list_cefr_missing)."""

from httpx import AsyncClient

from app.services.cefr_vocab._data import BY_LEVEL, SORTED_BY_RANK
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def test_returns_missing_words_sorted_by_rank(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/stats/cefr", params={"limit": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 5
    # Response shape matches the iOS CEFRWord decodable (id, word, frequencyRank, used).
    assert [item["word"] for item in body] == [lemma for lemma, _ in SORTED_BY_RANK[:5]]
    assert [item["frequency_rank"] for item in body] == [1, 2, 3, 4, 5]
    assert all(item["used"] is False for item in body)
    assert all(item["id"] == item["word"] for item in body)


async def test_respects_limit(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    body = (await client.get("/stats/cefr", params={"limit": 3})).json()
    assert len(body) == 3


async def test_used_words_are_excluded(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    # The single most common CEFR word — seed it as "used" and confirm it drops out of the missing list.
    top_lemma = SORTED_BY_RANK[0][0]
    await db.execute(
        "INSERT INTO word_freq (user_id, lemma, count) VALUES ($1, $2, 1)",
        user["id"],
        top_lemma,
    )
    body = (await client.get("/stats/cefr", params={"limit": 5})).json()
    returned = [item["word"] for item in body]
    assert top_lemma not in returned
    # The slot it vacated is filled by the next-ranked word, keeping the page full.
    assert len(body) == 5
    assert body[0]["word"] == SORTED_BY_RANK[1][0]


async def test_level_filter_returns_only_that_level(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    body = (await client.get("/stats/cefr", params={"level": "A2", "limit": 10})).json()
    assert body, "expected A2 words to exist in the reference set"
    expected = [lemma for lemma, _rank in BY_LEVEL["A2"][:10]]
    assert [item["word"] for item in body] == expected


async def test_level_filter_excludes_used_words_within_level(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    first_a1 = BY_LEVEL["A1"][0][0]
    await db.execute(
        "INSERT INTO word_freq (user_id, lemma, count) VALUES ($1, $2, 1)",
        user["id"],
        first_a1,
    )
    body = (await client.get("/stats/cefr", params={"level": "A1", "limit": 10})).json()
    words = [item["word"] for item in body]
    assert first_a1 not in words
    a1_lemmas = {lemma for lemma, _rank in BY_LEVEL["A1"]}
    assert all(word in a1_lemmas for word in words)


async def test_rejects_invalid_level(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/stats/cefr", params={"level": "Z9"})
    assert resp.status_code == 422
