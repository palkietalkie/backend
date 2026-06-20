"""Tests for /auth/announce — the sign-in/up Slack feed. verify_clerk_jwt is monkeypatched; Slack is mocked with respx."""

import uuid
from typing import Any

import httpx
import pytest
import respx
from httpx import AsyncClient

from app.config import get_settings
from app.routers import announce_auth as mod
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


def _enable_prod_slack(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("SLACK_CHANNEL_GTM", "C_TEST")
    get_settings.cache_clear()


def _patch_jwt(monkeypatch: pytest.MonkeyPatch, clerk_id: str, email: str | None) -> None:
    async def _verify(_token: str) -> dict[str, Any]:
        return {"sub": clerk_id, "email": email}

    monkeypatch.setattr(mod, "verify_clerk_jwt", _verify)


async def test_brand_new_user_reads_signed_up(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _ = app_with_overrides
    _enable_prod_slack(monkeypatch)
    _patch_jwt(monkeypatch, f"user_{uuid.uuid4().hex[:8]}", "new@example.test")
    with respx.mock(base_url="https://slack.com") as router:
        route = router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True, "ts": "111.1"})
        )
        resp = await client.post(
            "/auth/announce", headers={"Authorization": "Bearer t"}, json={"method": "Apple"}
        )
    assert resp.status_code == 200
    sent = route.calls.last.request.content.decode()
    assert "signed up with Apple" in sent
    assert "<!channel>" not in sent, "success is a feed entry, not an alert — no mention"
    get_settings.cache_clear()


async def test_preferred_name_and_email_make_a_human_label(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _ = app_with_overrides
    _enable_prod_slack(monkeypatch)
    # JWT carries no email claim → the backend must use the name + email iOS sent, never the opaque clerk id.
    _patch_jwt(monkeypatch, f"user_{uuid.uuid4().hex[:8]}", None)
    with respx.mock(base_url="https://slack.com") as router:
        route = router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True, "ts": "1"})
        )
        resp = await client.post(
            "/auth/announce",
            headers={"Authorization": "Bearer t"},
            json={
                "method": "Apple",
                "preferred_name": "Wes Nishio",
                "email": "wes@palkietalkie.com",
            },
        )
    assert resp.status_code == 200
    sent = route.calls.last.request.content.decode()
    assert "Wes Nishio (wes@palkietalkie.com) signed up with Apple" in sent
    assert "user_" not in sent, "with a name we must never fall back to the opaque clerk id"
    get_settings.cache_clear()


async def test_returning_user_reads_signed_in(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch, db: DBConn
) -> None:
    client, _ = app_with_overrides
    clerk_id = f"user_{uuid.uuid4().hex[:8]}"
    await db.execute(
        "INSERT INTO users (id, clerk_user_id, email) VALUES ($1, $2, $3)",
        uuid.uuid4(),
        clerk_id,
        "e@example.test",
    )
    _enable_prod_slack(monkeypatch)
    _patch_jwt(monkeypatch, clerk_id, "e@example.test")
    with respx.mock(base_url="https://slack.com") as router:
        route = router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True, "ts": "1"})
        )
        resp = await client.post(
            "/auth/announce", headers={"Authorization": "Bearer t"}, json={"method": "Google"}
        )
    assert resp.status_code == 200
    assert "signed in with Google" in route.calls.last.request.content.decode()
    get_settings.cache_clear()


async def test_pending_email_posts_thread_parent_and_returns_ts(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _ = app_with_overrides
    _enable_prod_slack(monkeypatch)
    with respx.mock(base_url="https://slack.com") as router:
        route = router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True, "ts": "999.9"})
        )
        resp = await client.post(
            "/auth/announce",
            json={"method": "Email", "outcome": "requested", "pending_email": "wes@gitauto.ai"},
        )
    assert resp.status_code == 200
    assert resp.json()["thread_ts"] == "999.9", "parent ts is returned so verify can reply under it"
    sent = route.calls.last.request.content.decode()
    assert "requested an email sign-in code" in sent
    assert "wes@gitauto.ai" in sent
    get_settings.cache_clear()


async def test_email_verify_replies_in_the_same_thread(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _ = app_with_overrides
    _enable_prod_slack(monkeypatch)
    _patch_jwt(monkeypatch, f"user_{uuid.uuid4().hex[:8]}", "wes@gitauto.ai")
    with respx.mock(base_url="https://slack.com") as router:
        route = router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True, "ts": "2"})
        )
        resp = await client.post(
            "/auth/announce",
            headers={"Authorization": "Bearer t"},
            json={"method": "Email", "thread_ts": "999.9"},
        )
    assert resp.status_code == 200
    sent = route.calls.last.request.content.decode()
    assert "signed up with Email" in sent
    assert "999.9" in sent  # posted as a reply under the "code requested" parent
    get_settings.cache_clear()


async def test_failed_attempt_posts_warning_without_jwt(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    # A failed auth has no session/JWT, so the endpoint must NOT require auth and still report the failure.
    client, _ = app_with_overrides
    _enable_prod_slack(monkeypatch)
    with respx.mock(base_url="https://slack.com") as router:
        route = router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True, "ts": "3"})
        )
        resp = await client.post(
            "/auth/announce",
            json={
                "method": "Email",
                "outcome": "failed",
                "pending_email": "wes@gitauto.ai",
                "reason": "missing requirements",
                "thread_ts": "999.9",
            },
        )
    assert resp.status_code == 200
    sent = route.calls.last.request.content.decode()
    assert "<!channel>" in sent, "a failed sign-in must ping the channel"
    assert "failed to sign in with Email" in sent
    assert "missing requirements" in sent
    assert "wes@gitauto.ai" in sent
    assert "999.9" in sent  # threaded under the "code requested" parent
    get_settings.cache_clear()


async def test_rich_diagnostic_reason_is_accepted_but_abuse_is_bounded(
    app_with_overrides: tuple[AsyncClient, UserRow],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # The iOS `diagnoseAuthError` chain (underlying-error + Clerk fields) runs ~1-2k chars — far past the old 500 cap. If the cap 422s it, we lose the only window into a failure we can't reproduce. But the field is unauthenticated, so a hard bound must remain.
    client, _ = app_with_overrides
    _enable_prod_slack(monkeypatch)
    rich = (
        "com.apple.AuthenticationServices.AuthorizationError#1000: The operation couldn't be completed. "
        "← AKAuthenticationError#-7026: iCloud account not available " + "x" * 1500
    )
    assert 500 < len(rich) <= 1800
    with respx.mock(base_url="https://slack.com") as router:
        route = router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True, "ts": "5"})
        )
        with caplog.at_level("WARNING"):
            resp = await client.post(
                "/auth/announce", json={"method": "Apple", "outcome": "failed", "reason": rich}
            )
    assert resp.status_code == 200, "a real diagnostic must not be rejected and lost"
    assert "AKAuthenticationError#-7026" in route.calls.last.request.content.decode()
    # The backend's own log — not just Slack — must carry the diagnostic, since Slack is an alert surface, not a queryable log store.
    assert any(
        "sign-in failed" in r.message and "AKAuthenticationError#-7026" in r.getMessage()
        for r in caplog.records
    )

    # Past the bound, Pydantic rejects — the open endpoint can't be a megabyte sink.
    resp = await client.post(
        "/auth/announce", json={"method": "Apple", "outcome": "failed", "reason": "z" * 2001}
    )
    assert resp.status_code == 422
    get_settings.cache_clear()


async def test_failed_oauth_without_email_reads_someone(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _ = app_with_overrides
    _enable_prod_slack(monkeypatch)
    with respx.mock(base_url="https://slack.com") as router:
        route = router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True, "ts": "4"})
        )
        resp = await client.post(
            "/auth/announce", json={"method": "Google", "outcome": "failed", "reason": "cancelled"}
        )
    assert resp.status_code == 200
    sent = route.calls.last.request.content.decode()
    assert "Someone failed to sign in with Google" in sent
    assert "cancelled" in sent
    get_settings.cache_clear()
