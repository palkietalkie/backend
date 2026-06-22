-- Tag each conversation session with the target language it was practiced in.
--
-- Recall feeds the tail of a user's recent sessions (with the same persona) back into the prompt. Without a per-session language, switching target language pulls the old-language history into the new session and the tutor keeps speaking the old language. Nullable on purpose: pre-existing rows have an unknown language and recall excludes them rather than guess.
ALTER TABLE conversation_sessions ADD COLUMN IF NOT EXISTS target_language text;
