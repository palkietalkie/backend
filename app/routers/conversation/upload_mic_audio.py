"""POST /conversation/{session_id}/audio/mic — receive the deflate-compressed wav of the iOS mic recording (post-acoustic-echo-cancellation user-side audio).

Companion endpoint: `POST /conversation/{id}/audio/model` for the AI's raw PCM16 output captured before iOS playback DSP touched it. Both endpoints write to the same `session_audio` table, distinguished by the `source` column.

Body: raw bytes (Content-Type: audio/wav+deflate). NOT a multipart upload — multipart on FastAPI requires python-multipart and adds 30-50ms of parsing overhead for a single-file payload. Raw body is simpler.

Retention: 14 days. Hard cap: 50 MB per upload.
"""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.resolve_current_user import resolve_current_user
from app.routers.conversation.constants import SESSION_BY_USER_SQL
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/conversation", tags=["conversation"])

MAX_UPLOAD_BYTES = 50 * 1024 * 1024
RETENTION_DAYS = 14
SOURCE = "mic"


@router.post("/{session_id}/audio/mic", status_code=status.HTTP_204_NO_CONTENT)
async def upload_mic_audio(
    session_id: uuid.UUID,
    request: Request,
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
) -> None:
    session_row = await db.fetchrow(SESSION_BY_USER_SQL, session_id, user["id"])
    if session_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")

    audio_bytes = await request.body()
    if not audio_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="empty audio body")
    if len(audio_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"audio body exceeds {MAX_UPLOAD_BYTES} bytes",
        )

    content_type = request.headers.get("content-type", "application/octet-stream")
    now = datetime.now(UTC)
    expires_at = now + timedelta(days=RETENTION_DAYS)

    # Upsert on (session_id, source). Last-write-wins on iOS retry.
    await db.execute(
        """INSERT INTO session_audio (session_id, source, user_id, audio, bytes, format, created_at, expires_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
           ON CONFLICT (session_id, source) DO UPDATE
              SET audio      = EXCLUDED.audio,
                  bytes      = EXCLUDED.bytes,
                  format     = EXCLUDED.format,
                  created_at = EXCLUDED.created_at,
                  expires_at = EXCLUDED.expires_at""",
        session_id,
        SOURCE,
        user["id"],
        audio_bytes,
        len(audio_bytes),
        content_type,
        now,
        expires_at,
    )
