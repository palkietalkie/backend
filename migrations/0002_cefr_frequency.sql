CREATE TABLE cefr_frequency (
    lemma  VARCHAR(64) PRIMARY KEY,
    rank   INTEGER NOT NULL
);
CREATE INDEX ix_cefr_frequency_rank ON cefr_frequency(rank);
