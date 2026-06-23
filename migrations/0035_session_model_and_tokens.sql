-- Per-session inference model + token usage, the raw inputs for real unit economics.
--
-- model is set at session start (we know which realtime model we minted). input/output tokens are reported by iOS at session end from OpenAI's response.done usage events, since iOS holds the realtime WS and the backend never sees that traffic. All nullable: pre-existing rows have none, and a session that ends without a usage report (crash, background kill) keeps NULL rather than a wrong 0.
ALTER TABLE conversation_sessions ADD COLUMN IF NOT EXISTS model text;
ALTER TABLE conversation_sessions ADD COLUMN IF NOT EXISTS input_tokens bigint;
ALTER TABLE conversation_sessions ADD COLUMN IF NOT EXISTS output_tokens bigint;
