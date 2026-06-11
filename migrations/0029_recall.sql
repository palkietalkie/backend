-- Conversational keyword-recall support.
--
-- Full-text index so the keyword-recall tool (search_transcripts) stays fast as transcripts grow. GIN over an English tsvector of the turn text.
-- (Session summaries for semantic recall live only in Pinecone — the embedding store keeps the summary text alongside the vector, and it's re-derivable from these transcripts, so no Postgres copy is needed.)
CREATE INDEX IF NOT EXISTS ix_transcripts_text_fts
    ON transcripts USING GIN (to_tsvector('english', text));
