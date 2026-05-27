CREATE TABLE users (
    id                       UUID PRIMARY KEY,
    clerk_user_id            VARCHAR(128) NOT NULL,
    email                    VARCHAR(320),
    premium                  BOOLEAN NOT NULL DEFAULT FALSE,
    premium_ends_at          TIMESTAMPTZ,
    free_minutes_used_today  INTEGER NOT NULL DEFAULT 0,
    free_minutes_reset_at    TIMESTAMPTZ,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    display_name             VARCHAR(120),
    native_language          VARCHAR(32),
    target_accent            VARCHAR(32),
    cefr_level               VARCHAR(4),
    goals                    TEXT,
    location_city            VARCHAR(120),
    timezone                 VARCHAR(64)
);
CREATE UNIQUE INDEX ix_users_clerk_user_id ON users(clerk_user_id);
CREATE        INDEX ix_users_email          ON users(email);

CREATE TABLE personas (
    id                   UUID PRIMARY KEY,
    name                 VARCHAR(120) NOT NULL,
    voice_id             VARCHAR(64)  NOT NULL,
    text_prompt_template TEXT NOT NULL,
    user_id              UUID REFERENCES users(id) ON DELETE CASCADE,
    is_preset            BOOLEAN NOT NULL DEFAULT FALSE,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_personas_user_id ON personas(user_id);

CREATE TABLE conversation_sessions (
    id                UUID PRIMARY KEY,
    user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    persona_id        UUID REFERENCES personas(id) ON DELETE SET NULL,
    started_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at          TIMESTAMPTZ,
    duration_seconds  INTEGER
);
CREATE INDEX ix_sessions_user_id ON conversation_sessions(user_id);

CREATE TABLE transcripts (
    id         BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    role       VARCHAR(16) NOT NULL,
    text       TEXT NOT NULL,
    ts         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_transcripts_session_id ON transcripts(session_id);

CREATE TABLE word_freq (
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lemma        VARCHAR(64) NOT NULL,
    count        INTEGER NOT NULL DEFAULT 0,
    last_used_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, lemma)
);

CREATE TABLE phrase_freq (
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    phrase       VARCHAR(255) NOT NULL,
    count        INTEGER NOT NULL DEFAULT 0,
    last_used_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, phrase)
);

CREATE TABLE mistakes (
    id            UUID PRIMARY KEY,
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original      TEXT NOT NULL,
    corrected     TEXT NOT NULL,
    category      VARCHAR(32) NOT NULL,
    count         INTEGER NOT NULL DEFAULT 1,
    last_seen_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_mistake_user_text UNIQUE (user_id, original, corrected)
);
CREATE INDEX ix_mistakes_user_id ON mistakes(user_id);

CREATE TABLE cefr_vocab (
    lemma VARCHAR(64) PRIMARY KEY,
    level VARCHAR(4)  NOT NULL
);
CREATE INDEX ix_cefr_vocab_level ON cefr_vocab(level);

CREATE TABLE events (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    event_type  VARCHAR(64) NOT NULL,
    ts          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    props       JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX ix_events_user_id    ON events(user_id);
CREATE INDEX ix_events_event_type ON events(event_type);
CREATE INDEX ix_events_ts         ON events(ts);

CREATE TABLE device_tokens (
    id          UUID PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    apns_token  VARCHAR(255) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_device_user_token UNIQUE (user_id, apns_token)
);
CREATE INDEX ix_device_tokens_user_id ON device_tokens(user_id);

CREATE TABLE calendar_tokens (
    id             UUID PRIMARY KEY,
    user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider       VARCHAR(32) NOT NULL,
    access_token   TEXT NOT NULL,
    refresh_token  TEXT,
    expires_at     TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_calendar_user_provider UNIQUE (user_id, provider)
);
CREATE INDEX ix_calendar_tokens_user_id ON calendar_tokens(user_id);
