-- CEFR vocab + frequency moved to an in-memory dict loaded from `app/scripts/data/cefr_vocab.csv` at app startup. Static reference data doesn't need to live in Postgres, and dropping the tables eliminates the seed step + the JOINs against them in stats queries.

DROP TABLE IF EXISTS cefr_frequency;
DROP TABLE IF EXISTS cefr_vocab;
