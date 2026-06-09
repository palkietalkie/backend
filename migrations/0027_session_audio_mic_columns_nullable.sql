-- Both audio tracks must be independently insertable now that the model-audio upload endpoint can land before (or without) the mic upload. Originally `audio / bytes / format` were NOT NULL because there was only one track per row.

ALTER TABLE session_audio
    ALTER COLUMN mic_audio        DROP NOT NULL,
    ALTER COLUMN mic_audio_bytes  DROP NOT NULL,
    ALTER COLUMN mic_audio_format DROP NOT NULL;
