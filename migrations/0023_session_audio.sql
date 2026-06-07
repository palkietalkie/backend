-- Raw session audio retained for 14 days for debugging, abuse/safety review, and training (the latter gated by users.product_improvement_consent at read time, not write time — we keep the data and decide use later).
--
-- BYTEA, not object storage: a ~10-minute conversation at 24kHz/PCM16 gzipped is ~1–5 MB. At expected scale, the 14-day window means rows turn over quickly; we don't need S3 / R2 / Fly Volume infra for v1. Move to object storage if rows ever exceed ~50 MB or the Neon db hits storage limits.
--
-- ON DELETE CASCADE from conversation_sessions: when a user deletes a session or their account, the audio row goes automatically alongside transcripts. Same shape as the transcripts ↔ conversation_sessions link.

CREATE TABLE session_audio (
    session_id   UUID PRIMARY KEY REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    audio        BYTEA NOT NULL,
    bytes        BIGINT NOT NULL,
    -- Mime of the bytes we received. Today: "audio/wav" gzipped, written as "audio/wav+gzip". Tomorrow: maybe FLAC. Stored so a future cron / debug tool knows how to decode without guessing.
    format       TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at   TIMESTAMPTZ NOT NULL
);

CREATE INDEX session_audio_expires_at ON session_audio (expires_at);
CREATE INDEX session_audio_user_id    ON session_audio (user_id);
