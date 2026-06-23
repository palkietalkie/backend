"""Tests for POST /conversation/start.

External dependencies that need stubbing per provider: - ``fetch_entities_summary`` (Neo4j) — it's ``@fallback``-decorated so it returns ``[]`` on any failure, but the real driver still tries to dial bolt://localhost; we monkeypatch it to a no-op for determinism/speed. - ``fetch_weather`` (Open-Meteo) — only called when lat/lon are supplied; we stub it out to avoid a live HTTP call. - ``mint_openai_session`` (OpenAI Realtime) — for the openai-provider path we stub it; the test patches the symbol in the start_conversation module."""

import uuid

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.config import get_settings
from app.personas.presets.preset_list import PRESETS
from app.routers.conversation import resolve_free_cap as resolve_mod
from app.routers.conversation import start_conversation as start_mod
from app.services.neo4j import fetch_entities_summary as entities_mod
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def _stub_externals(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _empty_entities(_uid: uuid.UUID, limit: int = 20) -> list[str]:
        return []

    async def _no_events(*_args: object, **_kwargs: object) -> list[object]:
        return []

    monkeypatch.setattr(start_mod, "fetch_entities_summary", _empty_entities)
    monkeypatch.setattr(start_mod, "fetch_todays_events", _no_events)


@pytest.fixture
def personaplex_provider(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("INFERENCE_PROVIDER", "personaplex")
    monkeypatch.setenv("WS_TICKET_SECRET", "test-ws-ticket-secret")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def openai_provider(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("INFERENCE_PROVIDER", "openai")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


async def test_start_with_preset_persona_personaplex_path(
    app_with_overrides: tuple[AsyncClient, UserRow],
    monkeypatch: pytest.MonkeyPatch,
    personaplex_provider: None,
) -> None:
    await _stub_externals(monkeypatch)
    client, _ = app_with_overrides
    preset = PRESETS[0]
    resp = await client.post("/conversation/start", json={"persona_id": str(preset.id)})
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "personaplex"
    assert body["ephemeral_token"] is None
    assert body["ws_url"].startswith("wss://")
    assert body["voice_id"]
    # Fresh free user, no prior usage: the tighter daily window is what's left, so iOS counts down from it.
    from app.routers.entitlement.constants import FREE_MINUTES_PER_DAY

    assert body["free_seconds_remaining"] == FREE_MINUTES_PER_DAY * 60
    assert body["free_limit_kind"] == "daily"


async def test_start_premium_user_has_unlimited_free_seconds(
    app_with_overrides: tuple[AsyncClient, UserRow],
    monkeypatch: pytest.MonkeyPatch,
    personaplex_provider: None,
    db: DBConn,
) -> None:
    await _stub_externals(monkeypatch)
    client, user = app_with_overrides
    await db.execute("UPDATE users SET premium = TRUE WHERE id = $1", user["id"])
    resp = await client.post("/conversation/start", json={"persona_id": str(PRESETS[0].id)})
    assert resp.status_code == 200
    # Premium = no cap, so iOS never starts a countdown.
    body = resp.json()
    assert body["free_seconds_remaining"] is None
    assert body["free_limit_kind"] is None


async def test_start_with_unknown_persona_returns_404(
    app_with_overrides: tuple[AsyncClient, UserRow],
    monkeypatch: pytest.MonkeyPatch,
    personaplex_provider: None,
) -> None:
    await _stub_externals(monkeypatch)
    client, _ = app_with_overrides
    resp = await client.post("/conversation/start", json={"persona_id": str(uuid.uuid4())})
    assert resp.status_code == 404


async def test_start_with_custom_persona_works(
    app_with_overrides: tuple[AsyncClient, UserRow],
    db: DBConn,
    monkeypatch: pytest.MonkeyPatch,
    personaplex_provider: None,
) -> None:
    await _stub_externals(monkeypatch)
    client, user = app_with_overrides
    persona_id = uuid.uuid4()
    await db.execute(
        """INSERT INTO personas (
               id, name, description, voice_id, role, age, background,
               vocabulary_register, conversational_style, topical_preferences,
               is_public, user_id
           ) VALUES ($1, 'Custom', '', 'NATM1', NULL, NULL, NULL, NULL, NULL, NULL, FALSE, $2)""",
        persona_id,
        user["id"],
    )
    resp = await client.post("/conversation/start", json={"persona_id": str(persona_id)})
    assert resp.status_code == 200
    assert resp.json()["voice_id"] == "NATM1"


async def test_start_with_private_custom_persona_owned_by_other_user_returns_403(
    app_with_overrides: tuple[AsyncClient, UserRow],
    db: DBConn,
    monkeypatch: pytest.MonkeyPatch,
    personaplex_provider: None,
) -> None:
    await _stub_externals(monkeypatch)
    client, _ = app_with_overrides
    other_id = uuid.uuid4()
    await db.execute(
        "INSERT INTO users (id, clerk_user_id, premium) VALUES ($1, $2, FALSE)",
        other_id,
        f"u_other_{other_id.hex[:8]}",
    )
    persona_id = uuid.uuid4()
    await db.execute(
        """INSERT INTO personas (
               id, name, description, voice_id, role, age, background,
               vocabulary_register, conversational_style, topical_preferences,
               is_public, user_id
           ) VALUES ($1, 'Theirs', '', 'NATM1', NULL, NULL, NULL, NULL, NULL, NULL, FALSE, $2)""",
        persona_id,
        other_id,
    )
    resp = await client.post("/conversation/start", json={"persona_id": str(persona_id)})
    assert resp.status_code == 403


async def test_start_writes_conversation_start_event(
    app_with_overrides: tuple[AsyncClient, UserRow],
    db: DBConn,
    monkeypatch: pytest.MonkeyPatch,
    personaplex_provider: None,
) -> None:
    await _stub_externals(monkeypatch)
    client, user = app_with_overrides
    preset = PRESETS[0]
    resp = await client.post("/conversation/start", json={"persona_id": str(preset.id)})
    assert resp.status_code == 200
    events = await db.fetch(
        "SELECT event_type FROM events WHERE user_id = $1 AND event_type = 'conversation_start'",
        user["id"],
    )
    assert len(events) == 1


async def test_start_openai_path_returns_ephemeral_token(
    app_with_overrides: tuple[AsyncClient, UserRow],
    db: DBConn,
    monkeypatch: pytest.MonkeyPatch,
    openai_provider: None,
) -> None:
    await _stub_externals(monkeypatch)

    from app.services.openai.constants import OpenAIVoiceId
    from app.services.openai.mint_openai_session import OpenAISession

    async def _fake_mint(
        *, text_prompt: str, voice_id: OpenAIVoiceId, is_premium: bool = False
    ) -> OpenAISession:
        return OpenAISession(
            ws_url="wss://api.openai.com/v1/realtime?model=gpt-realtime-mini",
            ephemeral_token="ek_test_token",
            voice_id=voice_id,
            model="gpt-realtime",
        )

    monkeypatch.setattr(start_mod, "mint_openai_session", _fake_mint)
    client, user = app_with_overrides
    # Create a persona with a known OpenAI voice id.
    persona_id = uuid.uuid4()
    await db.execute(
        """INSERT INTO personas (
               id, name, description, voice_id, role, age, background,
               vocabulary_register, conversational_style, topical_preferences,
               is_public, user_id
           ) VALUES ($1, 'OAI', '', 'ash', NULL, NULL, NULL, NULL, NULL, NULL, FALSE, $2)""",
        persona_id,
        user["id"],
    )
    resp = await client.post("/conversation/start", json={"persona_id": str(persona_id)})
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "openai"
    assert body["ephemeral_token"] == "ek_test_token"
    assert body["voice_id"] == "ash"

    # The session records the realtime model so cost analysis survives a future per-tier model split.
    from app.services.openai.constants import OPENAI_REALTIME_MODEL_PAID

    row = await db.fetchrow(
        "SELECT model FROM conversation_sessions WHERE id = $1", uuid.UUID(body["session_id"])
    )
    assert row is not None
    assert row["model"] == OPENAI_REALTIME_MODEL_PAID


async def test_start_openai_rejects_unknown_openai_voice(
    app_with_overrides: tuple[AsyncClient, UserRow],
    db: DBConn,
    monkeypatch: pytest.MonkeyPatch,
    openai_provider: None,
) -> None:
    await _stub_externals(monkeypatch)
    client, user = app_with_overrides
    # A persona with a personaplex voice id won't satisfy the openai enum.
    persona_id = uuid.uuid4()
    await db.execute(
        """INSERT INTO personas (
               id, name, description, voice_id, role, age, background,
               vocabulary_register, conversational_style, topical_preferences,
               is_public, user_id
           ) VALUES ($1, 'WrongVoice', '', 'NATM1', NULL, NULL, NULL, NULL, NULL, NULL, FALSE, $2)""",
        persona_id,
        user["id"],
    )
    resp = await client.post("/conversation/start", json={"persona_id": str(persona_id)})
    assert resp.status_code == 400


async def test_start_with_topic_override_threads_into_prompt(
    app_with_overrides: tuple[AsyncClient, UserRow],
    monkeypatch: pytest.MonkeyPatch,
    personaplex_provider: None,
) -> None:
    await _stub_externals(monkeypatch)
    client, _ = app_with_overrides
    preset = PRESETS[0]
    resp = await client.post(
        "/conversation/start",
        json={"persona_id": str(preset.id), "topic_override": "Today: tennis"},
    )
    assert resp.status_code == 200
    assert "Today: tennis" in resp.json()["text_prompt"]


async def test_start_topic_mode_uses_random_catalog_voice_personaplex(
    app_with_overrides: tuple[AsyncClient, UserRow],
    monkeypatch: pytest.MonkeyPatch,
    personaplex_provider: None,
) -> None:
    # Topic sessions drop the persona, so the voice must come from the provider's catalog, not the persona row.
    from app.personas.voices.personaplex_voices import PERSONAPLEX_VOICES

    await _stub_externals(monkeypatch)
    client, _ = app_with_overrides
    preset = PRESETS[0]
    resp = await client.post(
        "/conversation/start",
        json={"persona_id": str(preset.id), "topic_override": "Today: the Mars rover"},
    )
    assert resp.status_code == 200
    assert resp.json()["voice_id"] in {v.id for v in PERSONAPLEX_VOICES}


async def test_start_topic_mode_swaps_in_valid_openai_voice(
    app_with_overrides: tuple[AsyncClient, UserRow],
    db: DBConn,
    monkeypatch: pytest.MonkeyPatch,
    openai_provider: None,
) -> None:
    # A persona carrying a personaplex voice ('NATM1') normally 400s on the OpenAI path (see the rejects test). In topic mode we discard the persona voice and pick a random OpenAI-catalog voice, so the same request now succeeds.
    from app.personas.voices.openai_voices import OPENAI_VOICES
    from app.services.openai.constants import OpenAIVoiceId
    from app.services.openai.mint_openai_session import OpenAISession

    async def _fake_mint(
        *, text_prompt: str, voice_id: OpenAIVoiceId, is_premium: bool = False
    ) -> OpenAISession:
        return OpenAISession(
            ws_url="wss://api.openai.com/v1/realtime?model=gpt-realtime-mini",
            ephemeral_token="ek_test_token",
            voice_id=voice_id,
            model="gpt-realtime",
        )

    monkeypatch.setattr(start_mod, "mint_openai_session", _fake_mint)
    await _stub_externals(monkeypatch)
    client, user = app_with_overrides
    persona_id = uuid.uuid4()
    await db.execute(
        """INSERT INTO personas (
               id, name, description, voice_id, role, age, background,
               vocabulary_register, conversational_style, topical_preferences,
               is_public, user_id
           ) VALUES ($1, 'WrongVoice', '', 'NATM1', NULL, NULL, NULL, NULL, NULL, NULL, FALSE, $2)""",
        persona_id,
        user["id"],
    )
    resp = await client.post(
        "/conversation/start",
        json={"persona_id": str(persona_id), "topic_override": "Today: jazz history"},
    )
    assert resp.status_code == 200
    assert resp.json()["voice_id"] in {v.id for v in OPENAI_VOICES}


async def test_start_with_weather_lat_lon_uses_stub(
    app_with_overrides: tuple[AsyncClient, UserRow],
    monkeypatch: pytest.MonkeyPatch,
    personaplex_provider: None,
) -> None:
    await _stub_externals(monkeypatch)

    from app.services.weather.fetch_weather import WeatherSnapshot

    called: dict[str, float] = {}

    async def _fake_weather(lat: float, lon: float) -> WeatherSnapshot:
        called["lat"] = lat
        called["lon"] = lon
        return WeatherSnapshot(temperature_c=21.5, label="clear sky", is_day=True)

    monkeypatch.setattr(start_mod, "fetch_weather", _fake_weather)
    client, _ = app_with_overrides
    preset = PRESETS[0]
    resp = await client.post(
        "/conversation/start",
        json={"persona_id": str(preset.id), "lat": 37.7, "lon": -122.4},
    )
    assert resp.status_code == 200
    assert called == {"lat": 37.7, "lon": -122.4}
    # The weather label gets embedded in the prompt's "Their context" section.
    assert "clear sky" in resp.json()["text_prompt"]


async def test_start_rejects_free_user_who_hit_daily_limit(
    app_with_overrides: tuple[AsyncClient, UserRow],
    monkeypatch: pytest.MonkeyPatch,
    personaplex_provider: None,
) -> None:
    """Free user who's already used FREE_MINUTES_PER_DAY minutes today gets 402, with daily-window phrasing in the detail."""
    await _stub_externals(monkeypatch)

    async def _hit_daily(_user: UserRow, _db: DBConn) -> int:
        return 600  # 10 minutes exactly — equals the daily cap

    async def _no_week_use(_user: UserRow, _db: DBConn) -> int:
        return 0

    monkeypatch.setattr(resolve_mod, "sum_seconds_used_today", _hit_daily)
    monkeypatch.setattr(resolve_mod, "sum_seconds_used_this_week", _no_week_use)
    client, _ = app_with_overrides
    preset = PRESETS[0]
    resp = await client.post("/conversation/start", json={"persona_id": str(preset.id)})
    assert resp.status_code == 402
    assert "daily" in resp.json()["detail"].lower()


async def test_start_rejects_free_user_who_hit_weekly_limit(
    app_with_overrides: tuple[AsyncClient, UserRow],
    monkeypatch: pytest.MonkeyPatch,
    personaplex_provider: None,
) -> None:
    """Free user under daily cap but at weekly cap still gets 402, with weekly phrasing."""
    await _stub_externals(monkeypatch)

    async def _no_day_use(_user: UserRow, _db: DBConn) -> int:
        return 0

    async def _hit_week(_user: UserRow, _db: DBConn) -> int:
        return 1800  # 30 minutes — equals the weekly cap

    monkeypatch.setattr(resolve_mod, "sum_seconds_used_today", _no_day_use)
    monkeypatch.setattr(resolve_mod, "sum_seconds_used_this_week", _hit_week)
    client, _ = app_with_overrides
    preset = PRESETS[0]
    resp = await client.post("/conversation/start", json={"persona_id": str(preset.id)})
    assert resp.status_code == 402
    assert "weekly" in resp.json()["detail"].lower()


async def test_start_premium_user_bypasses_free_caps(
    app_with_overrides: tuple[AsyncClient, UserRow],
    monkeypatch: pytest.MonkeyPatch,
    db: DBConn,
    personaplex_provider: None,
) -> None:
    """A premium user with usage well over both caps still starts a session."""
    await _stub_externals(monkeypatch)

    client, user = app_with_overrides
    await db.execute(
        "UPDATE users SET premium = TRUE, premium_ends_at = NULL WHERE id = $1",
        user["id"],
    )

    async def _huge_use(_u: UserRow, _d: DBConn) -> int:
        return 99999

    monkeypatch.setattr(resolve_mod, "sum_seconds_used_today", _huge_use)
    monkeypatch.setattr(resolve_mod, "sum_seconds_used_this_week", _huge_use)
    preset = PRESETS[0]
    resp = await client.post("/conversation/start", json={"persona_id": str(preset.id)})
    assert resp.status_code == 200


async def test_start_succeeds_when_kg_dependency_fails(
    app_with_overrides: tuple[AsyncClient, UserRow],
    monkeypatch: pytest.MonkeyPatch,
    personaplex_provider: None,
) -> None:
    # KG / weather / calendar / recall are optional prompt context: a failing or dead dependency must NOT break the Talk View. Failing the Neo4j layer underneath the REAL (@fallback-decorated) fetch_entities_summary proves the resilience holds end-to-end — the route still returns 200 without KG, rather than 500ing as it did when a non-GqlError propagated.
    async def _no_events(*_args: object, **_kwargs: object) -> list[object]:
        return []

    def _broken_driver() -> object:
        raise RuntimeError("AuraDB connection defunct")

    monkeypatch.setattr(entities_mod, "get_neo4j_driver", _broken_driver)
    monkeypatch.setattr(start_mod, "fetch_todays_events", _no_events)
    client, _ = app_with_overrides
    preset = PRESETS[0]
    resp = await client.post("/conversation/start", json={"persona_id": str(preset.id)})
    assert resp.status_code == 200


def test_topic_override_carries_full_story_but_caps_length() -> None:
    pid = uuid.uuid4()
    # Was capped at 500 (truncated news to a headline); now the full article body fits.
    start_mod.StartRequest(persona_id=pid, topic_override="x" * 8000)
    with pytest.raises(ValidationError):
        start_mod.StartRequest(persona_id=pid, topic_override="x" * 8001)


def test_start_response_provider_is_constrained_to_known_values() -> None:
    # The provider field is a Literal, not a free str: the backend can only emit "openai"/"personaplex", so iOS's `if openai else personaplex` branch can never silently route an unexpected value to PersonaPlex. A bad value is a validation error at the source. model_validate (which takes Any) lets the test feed an off-list value to prove the Literal rejects it at runtime.
    def build(provider: str) -> start_mod.StartResponse:
        return start_mod.StartResponse.model_validate(
            {
                "session_id": uuid.uuid4(),
                "text_prompt": "",
                "voice_id": "ash",
                "ws_url": "wss://x",
                "provider": provider,
            }
        )

    assert build("openai").provider == "openai"
    assert build("personaplex").provider == "personaplex"
    with pytest.raises(ValidationError):
        build("gemini")
