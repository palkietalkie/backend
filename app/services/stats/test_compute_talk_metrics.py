import uuid
from datetime import UTC, datetime

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow
from app.services.stats.compute_talk_metrics import compute_talk_metrics


async def test_none_when_no_transcripts(db: DBConn, fake_user: UserRow) -> None:
    metrics = await compute_talk_metrics(db, fake_user["id"], 0)
    assert metrics.user_talk_pct is None
    assert metrics.speaking_rate_wpm is None


async def test_talk_share_and_speaking_rate(db: DBConn, fake_user: UserRow) -> None:
    session_id = uuid.uuid4()
    await db.execute(
        """INSERT INTO conversation_sessions (id, user_id, started_at, duration_seconds)
           VALUES ($1, $2, NOW(), 60)""",
        session_id,
        fake_user["id"],
    )
    now = datetime.now(UTC)
    # 49 chars / 10 words of user text, 49 chars of persona text => exactly 50% user talk.
    user_text = "one two three four five six seven eight nine ten "
    assert len(user_text) == 49
    await db.execute(
        """INSERT INTO transcripts (session_id, speaker, text, started_at, ended_at)
           VALUES ($1, 'user', $2, $3, $3)""",
        session_id,
        user_text,
        now,
    )
    await db.execute(
        """INSERT INTO transcripts (session_id, speaker, text, started_at, ended_at)
           VALUES ($1, 'persona', $2, $3, $3)""",
        session_id,
        "y" * 49,
        now,
    )
    metrics = await compute_talk_metrics(db, fake_user["id"], 60)
    assert metrics.user_talk_pct == 0.5
    # user_talk_seconds = 60 * 0.5 = 30s = 0.5 min; 10 words / 0.5 = 20 wpm.
    assert metrics.speaking_rate_wpm == 20.0
