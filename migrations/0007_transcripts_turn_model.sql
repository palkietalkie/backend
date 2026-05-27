-- Reshape transcripts: one row = one TURN, not one stream-emission fragment.
--
-- Why: a chunk (PersonaPlex `\x02 text` frame, OpenAI `response.output_audio_transcript.delta`)
-- is transport noise dictated by the underlying realtime stream — sub-word for PersonaPlex,
-- sub-sentence for OpenAI persona, full utterance for OpenAI user. Three different units in
-- the same table = no meaningful per-row semantics, no natural unique key, noisy stats.
--
-- A TURN is the domain unit: one continuous speech block from one speaker, bounded by speaker
-- switch or end-of-response. iOS aggregates emissions into a turn buffer and POSTs once.
--
-- Schema target:
--   speaker speaker NOT NULL     (was: role VARCHAR(16); 'assistant' rewritten to 'persona')
--   text TEXT NOT NULL
--   started_at TIMESTAMPTZ NOT NULL    (was: ts)
--   ended_at TIMESTAMPTZ NOT NULL      (new)
--   PRIMARY KEY (session_id, speaker, started_at)   (composite; dropped the BIGSERIAL surrogate — REVERTED in 0008)
--
-- Idempotent: this file may run against a fresh DB (role VARCHAR, no speaker enum) OR a
-- partially-migrated DB (speaker enum + speaker column + idempotency_key column from an
-- earlier 0007 draft that targeted per-chunk rows). Every DDL is conditional.

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'speaker') THEN
        CREATE TYPE speaker AS ENUM ('user', 'persona');
    END IF;
END $$;

-- Convert role → speaker if still on the original VARCHAR(16) schema.
DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'transcripts' AND column_name = 'role'
    ) THEN
        UPDATE transcripts SET role = 'persona' WHERE role = 'assistant';
        ALTER TABLE transcripts ALTER COLUMN role TYPE speaker USING role::speaker;
        ALTER TABLE transcripts RENAME COLUMN role TO speaker;
    END IF;
END $$;

-- Drop the idempotency_key column + constraint if a previous 0007 draft already added them.
ALTER TABLE transcripts DROP CONSTRAINT IF EXISTS uq_transcripts_session_idempotency;
ALTER TABLE transcripts DROP CONSTRAINT IF EXISTS uq_transcripts_session_chunk;
ALTER TABLE transcripts DROP COLUMN IF EXISTS idempotency_key;
ALTER TABLE transcripts DROP COLUMN IF EXISTS client_chunk_id;

-- Existing rows are per-emission fragments; can't be cleanly fused into turns (timestamps
-- are emission times, not turn boundaries). TRUNCATE is the only honest path. No real
-- prod data depends on this yet.
TRUNCATE transcripts;

-- Rename ts → started_at if still on the original schema.
DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'transcripts' AND column_name = 'ts'
    ) THEN
        ALTER TABLE transcripts RENAME COLUMN ts TO started_at;
    END IF;
END $$;

ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS ended_at TIMESTAMPTZ;
-- After TRUNCATE there are zero rows, so this UPDATE is a no-op; included for safety when
-- a future run hits a non-truncated state.
UPDATE transcripts SET ended_at = started_at WHERE ended_at IS NULL;
ALTER TABLE transcripts ALTER COLUMN ended_at SET NOT NULL;

-- Drop the BIGSERIAL surrogate; (session_id, speaker, started_at) is the natural PK. (Note: 0008 reverts this — surrogate is added back as PK, natural key becomes a UNIQUE constraint.)
ALTER TABLE transcripts DROP CONSTRAINT IF EXISTS transcripts_pkey;
ALTER TABLE transcripts DROP COLUMN IF EXISTS id;
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'transcripts_pkey'
    ) THEN
        ALTER TABLE transcripts ADD PRIMARY KEY (session_id, speaker, started_at);
    END IF;
END $$;

DROP INDEX IF EXISTS ix_transcripts_session_id;
