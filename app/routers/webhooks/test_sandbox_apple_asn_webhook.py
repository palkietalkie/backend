"""Live integration test: Apple's App Store Server API fires a real TEST notification at the dev backend.

Uses ``request-a-test-notification`` + ``Get Test Notification Status`` to verify Apple actually signed and delivered a JWS to ``palkietalkie-api-dev.fly.dev/webhooks/apple/asn`` and our handler acknowledged it. Only the ``TEST`` notification type is triggerable via this API — SUBSCRIBED / REVOKE / EXPIRED still require real sandbox-account purchases on TestFlight.

Skipped automatically unless every required env var is set. Marked ``live`` so normal pytest stays hermetic and CI opts in via ``pytest -m live``.

Reads env (loaded from ``backend/.env``): APPLE_STOREKIT_ISSUER_ID    issuer UUID from App Store Connect → Users and Access → Keys APPLE_STOREKIT_KEY_ID       key ID from the same screen APPLE_STOREKIT_PRIVATE_KEY  PEM-formatted contents of the downloaded ``.p8`` APPLE_BUNDLE_ID        com.palkietalkie.app APPLE_STOREKIT_ENVIRONMENT  ``Sandbox`` or ``Production`` (default ``Sandbox``)

Apple's webhook endpoint URL is configured per-app in App Store Connect; the test does not set it."""

import asyncio
import os
import time
from pathlib import Path

import jwt
import pytest
from pydantic import BaseModel, ValidationError

_P8_PATH = Path(__file__).resolve().parents[3] / "secrets" / "apple_storekit_api.p8"


def _load_apple_storekit_pem() -> str:
    """Return PEM string. Prefer the .p8 file (always well-formed) over the env var (often \\n-escaped in .env)."""
    if _P8_PATH.exists():
        return _P8_PATH.read_text()
    raw = os.environ.get("APPLE_STOREKIT_PRIVATE_KEY", "")
    return raw.replace("\\n", "\n")


pytestmark = [pytest.mark.sandbox, pytest.mark.asyncio]


class _SendAttempt(BaseModel):
    sendAttemptResult: str | None = None  # noqa: N815 — matches Apple's camelCase wire field


class _TestNotificationStatus(BaseModel):
    sendAttempts: list[_SendAttempt] = []  # noqa: N815 — matches Apple's wire field


REQUIRED_ENV = (
    "APPLE_STOREKIT_ISSUER_ID",
    "APPLE_STOREKIT_KEY_ID",
    "APPLE_BUNDLE_ID",
)

SANDBOX_BASE = "https://api.storekit-sandbox.itunes.apple.com"
PRODUCTION_BASE = "https://api.storekit.itunes.apple.com"


def _require_env() -> None:
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        pytest.fail(f"live test requires env vars (set in backend/.env): {', '.join(missing)}")
    if not _P8_PATH.exists() and not os.environ.get("APPLE_STOREKIT_PRIVATE_KEY"):
        pytest.fail(
            f"live test requires {_P8_PATH} OR APPLE_STOREKIT_PRIVATE_KEY env var (set in backend/.env)"
        )


def _mint_app_store_connect_jwt() -> str:
    issuer = os.environ["APPLE_STOREKIT_ISSUER_ID"]
    key_id = os.environ["APPLE_STOREKIT_KEY_ID"]
    private_key = _load_apple_storekit_pem()
    bundle_id = os.environ["APPLE_BUNDLE_ID"]
    now = int(time.time())
    return jwt.encode(
        {
            "iss": issuer,
            "iat": now,
            # Apple caps lifetime at 60 min for App Store Server API. 20 min keeps us safely under.
            "exp": now + 20 * 60,
            "aud": "appstoreconnect-v1",
            "bid": bundle_id,
        },
        private_key,
        algorithm="ES256",
        headers={"alg": "ES256", "kid": key_id, "typ": "JWT"},
    )


async def test_real_apple_test_notification_round_trips() -> None:
    _require_env()
    import httpx

    base = (
        PRODUCTION_BASE
        if os.environ.get("APPLE_STOREKIT_ENVIRONMENT", "Sandbox") == "Production"
        else SANDBOX_BASE
    )
    token = _mint_app_store_connect_jwt()
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Ask Apple to send our backend a TEST notification. Apple signs it with its real CA chain.
        request_resp = await client.post(f"{base}/inApps/v1/notifications/test", headers=headers)
        assert request_resp.status_code == 200, request_resp.text
        test_token = request_resp.json()["testNotificationToken"]
        assert test_token

        # Poll Apple's status endpoint. Delivery is usually sub-second but can spike to ~30s.
        deadline = asyncio.get_event_loop().time() + 90
        final_status: str | None = None
        last_body: dict[str, object] = {}
        while asyncio.get_event_loop().time() < deadline:
            status_resp = await client.get(
                f"{base}/inApps/v1/notifications/test/{test_token}", headers=headers
            )
            if status_resp.status_code == 200:
                last_body = status_resp.json()
                try:
                    parsed = _TestNotificationStatus.model_validate(last_body)
                except ValidationError:
                    parsed = _TestNotificationStatus()
                if parsed.sendAttempts:
                    final_status = parsed.sendAttempts[-1].sendAttemptResult
                    if final_status:
                        break
            await asyncio.sleep(2)

    assert final_status == "SUCCESS", (
        f"Apple did not record a SUCCESS delivery within 90s; last status body: {last_body}"
    )
