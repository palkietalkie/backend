"""Telemetry endpoint contract tests."""


async def test_record_event_persists_row(app_with_overrides, db) -> None:
    client, user = app_with_overrides
    resp = await client.post(
        "/events",
        json={
            "event_type": "cold_start_complete",
            "props": {"duration_ms": 1234, "phase_timings": {"first_audio_ms": 500}},
        },
    )
    assert resp.status_code == 204

    rows = await db.fetch("SELECT id, event_type, props FROM events WHERE user_id = $1", user["id"])
    assert len(rows) == 1
    assert rows[0]["event_type"] == "cold_start_complete"
    assert rows[0]["props"]["duration_ms"] == 1234
    # Regression: BIGINT autoincrement id must be assigned by the DB, not by the route.
    assert isinstance(rows[0]["id"], int)
