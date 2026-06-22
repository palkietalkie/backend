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


async def test_single_positive_reaction_is_small_not_max(db: DBConn, fake_user: UserRow) -> None:
    # Starts at 0 and grows GRADUALLY — one laugh nudges up, never jumps to 100 (the old ratio did).
    await _record(db, fake_user["id"], laugh=1)
    # net = 3 → round(100*tanh(3/50)) = 6
    assert await compute_affinity(db, fake_user["id"]) == 6


async def test_grows_gradually_with_sustained_positive(db: DBConn, fake_user: UserRow) -> None:
    await _record(db, fake_user["id"], laugh=10)
    # net = 30 → round(100*tanh(30/50)) = 54
    assert await compute_affinity(db, fake_user["id"]) == 54


async def test_goes_negative_when_tutor_is_cold(db: DBConn, fake_user: UserRow) -> None:
    # Affinity must be able to go NEGATIVE, not floor at 0: a tutor that keeps reacting badly sours the bond.
    await _record(db, fake_user["id"], sigh=5)
    # net = -10 → round(100*tanh(-10/50)) = -20
    assert await compute_affinity(db, fake_user["id"]) == -20


async def test_negatives_offset_accumulated_positives(db: DBConn, fake_user: UserRow) -> None:
    await _record(db, fake_user["id"], laugh=10)  # net 30 → 54
    assert await compute_affinity(db, fake_user["id"]) == 54
    await _record(db, fake_user["id"], sigh=5)  # net 30 - 10 = 20 → round(100*tanh(0.4)) = 38
    assert await compute_affinity(db, fake_user["id"]) == 38


async def test_reaches_plus_100_with_overwhelming_positive(db: DBConn, fake_user: UserRow) -> None:
    await _record(db, fake_user["id"], laugh=70)  # net 210 → round(100*tanh(4.2)) = 100
    assert await compute_affinity(db, fake_user["id"]) == 100


async def test_reaches_minus_100_with_overwhelming_negative(db: DBConn, fake_user: UserRow) -> None:
    await _record(db, fake_user["id"], sigh=105)  # net -210 → round(100*tanh(-4.2)) = -100
    assert await compute_affinity(db, fake_user["id"]) == -100
