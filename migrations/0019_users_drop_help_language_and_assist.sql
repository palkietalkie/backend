-- Simplification: Satsuki's case (native=Japanese, target=Spanish, wanting English-base explanations) is solvable by making native_languages multi-select — she sets ["Japanese", "English"] and the AI uses whichever helps faster when she's stuck. The separate help_language column and the on/off toggle become redundant.
ALTER TABLE users DROP COLUMN IF EXISTS help_language;
ALTER TABLE users DROP COLUMN IF EXISTS allow_native_language_assist;
