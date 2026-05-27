-- Revert 0007's drop of the BIGSERIAL surrogate. Earlier I unilaterally dropped `id` along
-- with the schema reshape; that wasn't asked for. Restore the surrogate as PK and demote
-- (session_id, speaker, started_at) to a UNIQUE constraint — same enforcement, surrogate
-- back for cheap chronological ordering / joins.

ALTER TABLE transcripts DROP CONSTRAINT IF EXISTS transcripts_pkey;

ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS id BIGSERIAL;
ALTER TABLE transcripts ADD PRIMARY KEY (id);

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_transcripts_session_speaker_started'
    ) THEN
        ALTER TABLE transcripts
            ADD CONSTRAINT uq_transcripts_session_speaker_started
            UNIQUE (session_id, speaker, started_at);
    END IF;
END $$;
