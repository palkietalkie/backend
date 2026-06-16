import uuid

from app.services.neon.db_conn import DBConn

# Per-reaction weights that combine into Affinity: positives earn it (a genuine laugh is the strongest signal, a gasp the weakest), negatives penalize it (a sigh or groan means the tutor got bored or let down). iOS owns which categories exist (it does the detection); this owns what they're worth. Tunable here without an app update.
AFFINITY_WEIGHTS = {"laugh": 3, "cheer": 2, "gasp": 1, "sigh": -2, "groan": -2}


async def compute_affinity(db: DBConn, user_id: uuid.UUID) -> int:
    """Affinity on a -100 (the tutor only ever reacted negatively) to +100 (only positively) scale, 0 is neutral.

    A favorability RATIO, not a running total, so it reflects how warm the tutor got with this user rather than how many sessions they logged. 0 when there are no reactions yet. The per-session per-category breakdown stays in the `events` table as the saved record we also mine internally for struggling users.
    """
    row = await db.fetchrow(
        """SELECT
             COALESCE(SUM((props->>'laugh')::int), 0)::int AS laugh,
             COALESCE(SUM((props->>'cheer')::int), 0)::int AS cheer,
             COALESCE(SUM((props->>'gasp')::int), 0)::int AS gasp,
             COALESCE(SUM((props->>'sigh')::int), 0)::int AS sigh,
             COALESCE(SUM((props->>'groan')::int), 0)::int AS groan
           FROM events
           WHERE user_id = $1 AND event_type = 'ai_emotion'""",
        user_id,
    )
    if row is None:
        return 0
    earned = sum(w * int(row[c]) for c, w in AFFINITY_WEIGHTS.items() if w > 0)
    penalty = sum(-w * int(row[c]) for c, w in AFFINITY_WEIGHTS.items() if w < 0)
    total = earned + penalty
    if total <= 0:
        return 0
    return round(100 * (earned - penalty) / total)
