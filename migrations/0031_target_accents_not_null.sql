-- target_accents was added (0024) as a bare TEXT[] — nullable, no default — unlike its sibling native_languages (0018: TEXT[] NOT NULL DEFAULT '{}'). The asymmetry forced `or []` coercion at every read site and a nullable generated type. "No accents chosen" is the empty array, never NULL; make the two columns consistent.

UPDATE users SET target_accents = '{}' WHERE target_accents IS NULL;
ALTER TABLE users ALTER COLUMN target_accents SET DEFAULT '{}';
ALTER TABLE users ALTER COLUMN target_accents SET NOT NULL;
