ALTER TABLE users
    ADD COLUMN IF NOT EXISTS explanation_language VARCHAR(64);
