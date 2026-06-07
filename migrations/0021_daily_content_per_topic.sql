-- Rebuild daily_content to store one row per (day, topic). Topics grow and change over time (politics, business, sports, quizzes, … and more later) and a column-per-topic shape would force a migration every time. Generic (day, topic, items) keeps schema stable; topic identifiers are code-defined slugs.
DROP TABLE daily_content;
CREATE TABLE daily_content (
    day DATE NOT NULL,
    topic TEXT NOT NULL,
    items JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (day, topic)
);
