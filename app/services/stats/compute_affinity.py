import math
import uuid

from app.services.neon.db_conn import DBConn

# Per-reaction weights that build Affinity: positives grow it (a genuine laugh is the strongest signal, a gasp the weakest), negatives set it back (a sigh or groan means the tutor got bored or let down). iOS owns which categories exist (it does the detection); this owns what they're worth. Tunable here without an app update.
AFFINITY_WEIGHTS = {"laugh": 3, "cheer": 2, "gasp": 1, "sigh": -2, "groan": -2}

# How fast Affinity moves away from 0 as net reactions pile up (in weighted-reaction units). At |net| == SCALE the score is ~±46, at 2×SCALE ~±76, at 3×SCALE ~±90: a gradual approach to either pole, never a jump off one reaction. Larger = slower. This replaced an earlier ratio+floor design that could read ±100 off a single detection.
AFFINITY_SCALE = 50


async def compute_affinity(db: DBConn, user_id: uuid.UUID) -> int:
    """Affinity on a -100 (the tutor consistently reacted coldly, the bond soured) to +100 (genuinely close) scale, 0 is neutral/strangers.

    Models a real relationship: it STARTS AT 0 and moves GRADUALLY in either direction as the tutor reacts over time — warmly (laughs, cheers, gasps) toward +100, coldly (sighs, groans) toward -100. Not a ratio — a single reaction can't swing it to an extreme; tanh saturation means it asymptotically approaches a pole only as consistent history accumulates. Symmetric, so it can genuinely go negative when the tutor keeps reacting badly. The per-session per-category breakdown stays in the `events` table as the saved record we also mine internally for struggling users.
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
    net = sum(w * int(row[c]) for c, w in AFFINITY_WEIGHTS.items())
    return round(100 * math.tanh(net / AFFINITY_SCALE))
