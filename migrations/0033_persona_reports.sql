-- UGC moderation (App Store Guideline 1.2): users report an objectionable community persona. list_personas hides any public persona with enough distinct reporters from everyone but its creator (the count is checked at list time, so no column on personas to keep in sync). One report per user per persona, mirroring persona_likes.
CREATE TABLE persona_reports (
    id          UUID PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    persona_id  UUID NOT NULL,
    reason      TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_report_user_persona UNIQUE (user_id, persona_id)
);

CREATE INDEX ix_persona_reports_persona_id ON persona_reports(persona_id);
