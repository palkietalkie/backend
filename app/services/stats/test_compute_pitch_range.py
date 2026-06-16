from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow
from app.services.stats.compute_pitch_range import compute_pitch_range


async def test_none_when_no_events(db: DBConn, fake_user: UserRow) -> None:
    pitch = await compute_pitch_range(db, fake_user["id"])
    assert pitch.min_hz is None
    assert pitch.max_hz is None


async def test_returns_widest_endpoints_across_events(db: DBConn, fake_user: UserRow) -> None:
    for lo, hi in ((90.0, 200.0), (80.0, 220.0)):
        await db.execute(
            """INSERT INTO events (user_id, event_type, ts, props)
               VALUES ($1, 'pitch_range', NOW(), $2)""",
            fake_user["id"],
            {"min_hz": lo, "max_hz": hi},
        )
    pitch = await compute_pitch_range(db, fake_user["id"])
    # The actual endpoints, not the span: lowest 80, highest 220.
    assert pitch.min_hz == 80.0
    assert pitch.max_hz == 220.0
