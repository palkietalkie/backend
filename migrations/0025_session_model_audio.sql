-- Capture the AI's raw PCM16 output stream as it arrives from OpenAI Realtime (pre-iOS-playback) so we can diagnose audio truncation that happens between the model and the user's ear. Stored on the same row as the mic recording to keep both tracks aligned by session_id; nullable because not every session ships it (older clients, errors).

ALTER TABLE session_audio
    ADD COLUMN model_audio        BYTEA,
    ADD COLUMN model_audio_bytes  BIGINT,
    ADD COLUMN model_audio_format TEXT;
