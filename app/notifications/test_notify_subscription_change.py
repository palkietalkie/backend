import uuid

import pytest

from app.notifications import notify_subscription_change as mod
from app.notifications.notify_subscription_change import notify_subscription_change
from app.notifications.subscription_transition import SubscriptionTransition
from app.services.apple_push.localized_alert import LocalizedAlert
from app.services.apple_push.push_result import PushResult
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


def _spy_push(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, LocalizedAlert]]:
    sent: list[tuple[str, LocalizedAlert]] = []

    async def _fake(token: str, alert: LocalizedAlert) -> PushResult:
        sent.append((token, alert))
        return PushResult(token=token, ok=True)

    monkeypatch.setattr(mod, "send_push", _fake)
    return sent


async def test_pushes_the_transition_alert_to_each_device(
    db: DBConn, fake_user: UserRow, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent = _spy_push(monkeypatch)
    for tok in ("tok-a", "tok-b"):
        await db.execute(
            "INSERT INTO device_tokens (id, user_id, apns_token) VALUES ($1, $2, $3)",
            uuid.uuid4(),
            fake_user["id"],
            tok,
        )

    count = await notify_subscription_change(
        db, fake_user["clerk_user_id"], SubscriptionTransition.WELCOME
    )

    assert count == 2
    assert {t for t, _ in sent} == {"tok-a", "tok-b"}
    assert sent[0][1].title_loc_key == "notif_sub_welcome_title"


async def test_user_without_a_token_pushes_nothing(
    db: DBConn, fake_user: UserRow, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent = _spy_push(monkeypatch)
    count = await notify_subscription_change(
        db, fake_user["clerk_user_id"], SubscriptionTransition.PAYMENT_FAILED
    )
    assert count == 0
    assert sent == []
