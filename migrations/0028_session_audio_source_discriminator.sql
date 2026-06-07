-- Replace the wide-row design (mic_audio* + model_audio* columns) with a `source` discriminator. One row per (session_id, source). Adding new audio sources later (e.g. raw-pre-AEC mic, speaker-tap recording) becomes another `source` value, not another migration to bolt on more columns.

-- Drop the model_audio* columns — they were only added in 0025 and have no data yet.
ALTER TABLE session_audio
    DROP COLUMN model_audio,
    DROP COLUMN model_audio_bytes,
    DROP COLUMN model_audio_format;

-- Rename the mic_audio* columns back to neutral names; the `source` column now carries what kind they are.
ALTER TABLE session_audio RENAME COLUMN mic_audio        TO audio;
ALTER TABLE session_audio RENAME COLUMN mic_audio_bytes  TO bytes;
ALTER TABLE session_audio RENAME COLUMN mic_audio_format TO format;

-- The neutral columns are populated for every row of every source; restore NOT NULL now that the split-row workaround from 0027 is gone.
ALTER TABLE session_audio
    ALTER COLUMN audio  SET NOT NULL,
    ALTER COLUMN bytes  SET NOT NULL,
    ALTER COLUMN format SET NOT NULL;

-- The discriminator. Existing rows are mic recordings; default backfills them. Enum'd via CHECK so a typo'd INSERT fails loudly instead of polluting the data.
ALTER TABLE session_audio
    ADD COLUMN source TEXT NOT NULL DEFAULT 'mic'
    CHECK (source IN ('mic', 'model'));

-- Drop the per-session unique constraint; multiple sources can coexist for one session.
ALTER TABLE session_audio DROP CONSTRAINT session_audio_pkey;
ALTER TABLE session_audio ADD PRIMARY KEY (session_id, source);

-- Remove the default once the backfill is done. Every future INSERT must specify the source explicitly.
ALTER TABLE session_audio ALTER COLUMN source DROP DEFAULT;
