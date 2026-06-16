import uuid
from dataclasses import dataclass

from app.services.neon.db_conn import DBConn


@dataclass(frozen=True)
class PitchRange:
    # The actual endpoints (lowest and highest F0 observed across sessions), not the span. Both null until on-device pitch detection has reported at least once.
    min_hz: float | None
    max_hz: float | None


async def compute_pitch_range(db: DBConn, user_id: uuid.UUID) -> PitchRange:
    row = await db.fetchrow(
        """SELECT MIN((props->>'min_hz')::float) AS pmin, MAX((props->>'max_hz')::float) AS pmax
           FROM events
           WHERE user_id = $1 AND event_type = 'pitch_range'""",
        user_id,
    )
    if row is None or row["pmin"] is None or row["pmax"] is None:
        return PitchRange(min_hz=None, max_hz=None)
    return PitchRange(min_hz=round(float(row["pmin"]), 1), max_hz=round(float(row["pmax"]), 1))
