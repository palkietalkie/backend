"""Tests for POST /personas/{id}/report — UGC moderation (App Store 1.2).

Covers recording a report, idempotency, the guards (preset 403, own 400, private 404), and that list_personas hides a persona once it crosses REPORT_HIDE_THRESHOLD distinct reporters while its creator still sees it."""

import uuid

from httpx import AsyncClient

from app.personas.presets.preset_list import PRESETS
from app.routers.personas.report_persona import REPORT_HIDE_THRESHOLD
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def _seed_persona(
    db: DBConn, user_id: uuid.UUID, *, name: str = "Theirs", is_public: bool = True
) -> uuid.UUID:
    persona_id = uuid.uuid4()
    await db.execute(
        """INSERT INTO personas (
               id, name, description, voice_id, role, age, background,
               vocabulary_register, conversational_style, topical_preferences,
               is_public, user_id
           ) VALUES ($1, $2, '', 'NATM1', NULL, NULL, NULL, NULL, NULL, NULL, $3, $4)""",
        persona_id,
        name,
        is_public,
        user_id,
    )
    return persona_id


async def _seed_user(db: DBConn) -> uuid.UUID:
    uid = uuid.uuid4()
    await db.execute(
        "INSERT INTO users (id, clerk_user_id, premium) VALUES ($1, $2, FALSE)",
        uid,
        f"u_{uid.hex[:8]}",
    )
    return uid


async def _seed_report(db: DBConn, persona_id: uuid.UUID, reporter_id: uuid.UUID) -> None:
    await db.execute(
        "INSERT INTO persona_reports (id, user_id, persona_id) VALUES ($1, $2, $3)",
        uuid.uuid4(),
        reporter_id,
        persona_id,
    )


async def test_report_records_a_row(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _ = app_with_overrides
    persona_id = await _seed_persona(db, await _seed_user(db))
    resp = await client.post(f"/personas/{persona_id}/report", json={"reason": "spam"})
    assert resp.status_code == 204
    assert (
        await db.fetchval("SELECT COUNT(*) FROM persona_reports WHERE persona_id = $1", persona_id)
        == 1
    )


async def test_report_is_idempotent(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _ = app_with_overrides
    persona_id = await _seed_persona(db, await _seed_user(db))
    await client.post(f"/personas/{persona_id}/report")
    await client.post(f"/personas/{persona_id}/report")
    assert (
        await db.fetchval("SELECT COUNT(*) FROM persona_reports WHERE persona_id = $1", persona_id)
        == 1
    )


async def test_cannot_report_preset(app_with_overrides: tuple[AsyncClient, UserRow]) -> None:
    client, _ = app_with_overrides
    resp = await client.post(f"/personas/{PRESETS[0].id}/report")
    assert resp.status_code == 403


async def test_cannot_report_own_persona(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    persona_id = await _seed_persona(db, user["id"])
    resp = await client.post(f"/personas/{persona_id}/report")
    assert resp.status_code == 400


async def test_cannot_report_private_persona(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _ = app_with_overrides
    persona_id = await _seed_persona(db, await _seed_user(db), is_public=False)
    resp = await client.post(f"/personas/{persona_id}/report")
    assert resp.status_code == 404


async def test_reporter_no_longer_sees_persona_they_reported(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _ = app_with_overrides
    persona_id = await _seed_persona(db, await _seed_user(db), name="I Reported This")
    assert "I Reported This" in [p["name"] for p in (await client.get("/personas")).json()]
    await client.post(f"/personas/{persona_id}/report")
    # Gone for me immediately on a single report, well below the global takedown threshold.
    assert "I Reported This" not in [p["name"] for p in (await client.get("/personas")).json()]


async def test_over_reported_persona_is_hidden_from_list(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _ = app_with_overrides
    persona_id = await _seed_persona(db, await _seed_user(db), name="Reported One")
    for _ in range(REPORT_HIDE_THRESHOLD):
        await _seed_report(db, persona_id, await _seed_user(db))
    resp = await client.get("/personas")
    assert "Reported One" not in [p["name"] for p in resp.json()]


async def test_under_threshold_persona_stays_listed(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _ = app_with_overrides
    persona_id = await _seed_persona(db, await _seed_user(db), name="Barely Reported")
    for _ in range(REPORT_HIDE_THRESHOLD - 1):
        await _seed_report(db, persona_id, await _seed_user(db))
    resp = await client.get("/personas")
    assert "Barely Reported" in [p["name"] for p in resp.json()]


async def test_creator_still_sees_own_reported_persona(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    persona_id = await _seed_persona(db, user["id"], name="Mine Reported")
    for _ in range(REPORT_HIDE_THRESHOLD + 1):
        await _seed_report(db, persona_id, await _seed_user(db))
    resp = await client.get("/personas")
    assert "Mine Reported" in [p["name"] for p in resp.json()]
