"""Return ``(audio_bytes, format_label)`` for a session, or None if no row exists."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import asyncpg


async def fetch_session_audio(
    db: asyncpg.Connection, session_id: uuid.UUID, source: str = "mic"
) -> tuple[bytes, str] | None:
    """`source="mic"` returns the iOS mic recording; `source="model"` returns the AI's raw PCM16 output captured before iOS playback DSP touched it."""
    row = await db.fetchrow(
        "SELECT audio, format FROM session_audio WHERE session_id = $1 AND source = $2",
        session_id,
        source,
    )
    if row is None:
        return None
    return bytes(row["audio"]), row["format"]
