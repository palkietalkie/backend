-- Multi-target-accents. Replace the single-value `target_accent VARCHAR(32)` with `target_accents TEXT[]` so users can
-- pick e.g. ['US general', 'UK RP', 'Australian'] and the conversation prompt rolls one at random per session.
-- Existing single-value rows migrate into a length-1 array; nulls stay nulls.

ALTER TABLE users
    ADD COLUMN target_accents TEXT[];

UPDATE users
   SET target_accents = ARRAY[target_accent]
 WHERE target_accent IS NOT NULL;

ALTER TABLE users
    DROP COLUMN target_accent;
