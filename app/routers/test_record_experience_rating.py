"""Experience-rating endpoint contract tests.

The rating is a typed, constrained column (1-5) in its own table, not a jsonb event: the DB rejects out-of-range values and the API rejects them before that. A comment is collected from every rating, happy or not. Production posts a live Slack ping; dev (which shares Slack creds) must not."""

import httpx
import pytest
import respx
from httpx import AsyncClient

from app.config import get_settings
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def test_persists_rating_with_comment(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    resp = await client.post("/ratings", json={"rating": 4, "comment": "love the personas"})
    assert resp.status_code == 204

    rows = await db.fetch(
        "SELECT rating, comment FROM experience_ratings WHERE user_id = $1", user["id"]
    )
    assert len(rows) == 1
    assert rows[0]["rating"] == 4
    assert rows[0]["comment"] == "love the personas"


async def test_persists_rating_without_comment(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    resp = await client.post("/ratings", json={"rating": 5})
    assert resp.status_code == 204

    row = await db.fetchrow(
        "SELECT rating, comment FROM experience_ratings WHERE user_id = $1", user["id"]
    )
    assert row is not None
    assert row["rating"] == 5
    assert row["comment"] is None


@pytest.mark.parametrize("bad_rating", [0, 6, -1, 100])
async def test_rejects_out_of_range_rating(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn, bad_rating: int
) -> None:
    # The 1-5 contract is enforced at the API edge (Pydantic) so a malformed client never reaches the DB CHECK.
    client, user = app_with_overrides
    resp = await client.post("/ratings", json={"rating": bad_rating})
    assert resp.status_code == 422

    count = await db.fetchval(
        "SELECT COUNT(*) FROM experience_ratings WHERE user_id = $1", user["id"]
    )
    assert count == 0


async def test_slacks_rating_in_production_with_comment(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("SLACK_CHANNEL_GTM", "C_TEST")
    get_settings.cache_clear()

    client, _ = app_with_overrides
    with respx.mock(base_url="https://slack.com") as router:
        route = router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        resp = await client.post("/ratings", json={"rating": 2, "comment": "tutor too fast"})
        assert resp.status_code == 204
    assert route.called
    body = route.calls.last.request.content.decode()
    assert "2/5" in body
    assert "tutor too fast" in body
    assert "C_TEST" in body
    get_settings.cache_clear()


async def test_skips_slack_in_dev_environment(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    # Dev shares Slack creds with prd; without the env gate every connected-device test would ping the prd channel.
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("SLACK_CHANNEL_GTM", "C_TEST")
    get_settings.cache_clear()

    client, _ = app_with_overrides
    with respx.mock(base_url="https://slack.com", assert_all_called=False) as router:
        route = router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        resp = await client.post("/ratings", json={"rating": 5, "comment": "great"})
        assert resp.status_code == 204
    assert not route.called, "dev env must not Slack the prd channel"
    get_settings.cache_clear()
