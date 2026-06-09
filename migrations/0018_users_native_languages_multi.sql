-- Switch native_language from single VARCHAR to a TEXT[] array. Existing single values become single-element arrays. Required (NOT NULL) with default empty array — Pydantic enforces ≥1 entry at the API boundary.
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS native_languages TEXT[] NOT NULL DEFAULT '{}';

UPDATE users
SET native_languages = ARRAY[native_language]
WHERE native_language IS NOT NULL AND native_languages = '{}';

ALTER TABLE users DROP COLUMN IF EXISTS native_language;
