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
    # With no used words, the missing list is just the top-ranked CEFR words in order.
    expected = [{"lemma": lemma, "level": entry.level} for lemma, entry in SORTED_BY_RANK[:5]]
    assert body == expected


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
    returned = [item["lemma"] for item in body]
    assert top_lemma not in returned
    # The slot it vacated is filled by the next-ranked word, keeping the page full.
    assert len(body) == 5
    assert body[0]["lemma"] == SORTED_BY_RANK[1][0]


async def test_level_filter_returns_only_that_level(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    body = (await client.get("/stats/cefr", params={"level": "A2", "limit": 10})).json()
    assert body, "expected A2 words to exist in the reference set"
    assert all(item["level"] == "A2" for item in body)
    expected = [lemma for lemma, _rank in BY_LEVEL["A2"][:10]]
    assert [item["lemma"] for item in body] == expected


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
    assert first_a1 not in [item["lemma"] for item in body]
    assert all(item["level"] == "A1" for item in body)


async def test_rejects_invalid_level(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/stats/cefr", params={"level": "Z9"})
    assert resp.status_code == 422
