import uuid

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow
from app.services.stats.compute_affinity import compute_affinity


async def _record(db: DBConn, user_id: uuid.UUID, **counts: int) -> None:
    props = {"session_id": str(uuid.uuid4())} | counts
    await db.execute(
        """INSERT INTO events (user_id, event_type, ts, props)
           VALUES ($1, 'ai_emotion', NOW(), $2)""",
        user_id,
        props,
    )


async def test_zero_when_no_reactions(db: DBConn, fake_user: UserRow) -> None:
    assert await compute_affinity(db, fake_user["id"]) == 0


async def test_normalized_favorability_with_penalty(db: DBConn, fake_user: UserRow) -> None:
    # Session 1: 2 laughs + 1 cheer + 1 sigh. Session 2: 1 gasp + 1 groan.
    await _record(db, fake_user["id"], laugh=2, cheer=1, sigh=1)
    await _record(db, fake_user["id"], gasp=1, groan=1)
    # earned = 3*2 + 2*1 + 1*1 = 9; penalty = 2*1 + 2*1 = 4. round(100*(9-4)/13) = 38.
    assert await compute_affinity(db, fake_user["id"]) == 38


async def test_all_negative_floors_at_minus_100(db: DBConn, fake_user: UserRow) -> None:
    await _record(db, fake_user["id"], sigh=2, groan=1)
    # earned = 0; penalty = 6. round(100*(0-6)/6) = -100.
    assert await compute_affinity(db, fake_user["id"]) == -100


async def test_all_positive_caps_at_100(db: DBConn, fake_user: UserRow) -> None:
    await _record(db, fake_user["id"], laugh=5, cheer=2, gasp=1)
    # No penalties: earned - penalty == earned + penalty, so the ratio is exactly +100.
    assert await compute_affinity(db, fake_user["id"]) == 100
