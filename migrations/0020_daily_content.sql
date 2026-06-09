CREATE TABLE daily_content (
    day DATE PRIMARY KEY,
    news JSONB NOT NULL DEFAULT '[]'::jsonb,
    sports JSONB NOT NULL DEFAULT '[]'::jsonb,
    quizzes JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
