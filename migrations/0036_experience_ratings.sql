-- In-app "rate your experience" results (1-5 stars + optional free-text comment), promoted out of the generic `events` jsonb sink. As a typed table the DB enforces the 1-5 range and the user FK that a telemetry event can't, and `AVG(rating)` / `WHERE rating <= 2` are direct, indexable queries instead of fragile `(props->>'rating')::int` casts. One row per submission: re-prompting after the re-ask interval is a fresh opinion, so we keep the history rather than upsert.
CREATE TABLE experience_ratings (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating      SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Rating analytics are time-series ("average rating week over week"), so index the axis we'll filter and order on.
CREATE INDEX ix_experience_ratings_created_at ON experience_ratings(created_at);
