-- Refactor persona system + consent + free-minute counters.
-- - Preset personas move out of the DB into code (`app/personas/presets.py`); only user customs remain in `personas`.
-- - Persona table gains bucket B fields (role, objective, age, background, vocabulary_register, conversational_style, topical_preferences), plus is_public + like_count.
-- - New persona_likes table (unique on user_id + persona_id; persona_id has no FK because preset uuid5 ids aren't in `personas`).
-- - User gains consent fields: per-toggle timestamps (NULL = no consent, non-null = consented at that time) + a separate screen-seen-at gate.
-- - User loses free_minutes_used_today / free_minutes_reset_at — daily quota is now computed on demand from session durations (per-user timezone resets are impossible to denormalize cleanly).
-- - conversation_sessions.persona_id drops its FK because preset uuids don't live in the personas table.

DELETE FROM personas WHERE is_preset = true;

ALTER TABLE conversation_sessions
    DROP CONSTRAINT IF EXISTS conversation_sessions_persona_id_fkey;

ALTER TABLE personas
    DROP COLUMN is_preset,
    DROP COLUMN text_prompt_template,
    ADD COLUMN role                 TEXT,
    ADD COLUMN objective            TEXT,
    ADD COLUMN age                  TEXT,
    ADD COLUMN background           TEXT,
    ADD COLUMN vocabulary_register  TEXT,
    ADD COLUMN conversational_style TEXT,
    ADD COLUMN topical_preferences  TEXT,
    ADD COLUMN is_public            BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN like_count           INTEGER NOT NULL DEFAULT 0,
    ALTER COLUMN user_id            SET NOT NULL;

CREATE TABLE persona_likes (
    id          UUID PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    persona_id  UUID NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_like_user_persona UNIQUE (user_id, persona_id)
);

CREATE INDEX ix_persona_likes_user_id    ON persona_likes(user_id);
CREATE INDEX ix_persona_likes_persona_id ON persona_likes(persona_id);

ALTER TABLE users
    DROP COLUMN free_minutes_used_today,
    DROP COLUMN free_minutes_reset_at,
    ADD COLUMN personalization_consent     TIMESTAMPTZ,
    ADD COLUMN product_improvement_consent TIMESTAMPTZ,
    ADD COLUMN consent_screen_seen_at      TIMESTAMPTZ;
