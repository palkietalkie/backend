ALTER TABLE users
    ADD COLUMN IF NOT EXISTS tutor_speaking_speed VARCHAR(20) NOT NULL DEFAULT 'normal';
