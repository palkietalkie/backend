-- Self-reported CEFR level is a weak signal vs. computed coverage from word_freq × cefr_vocab. Drop the column; the Stats screen has the real data from transcripts.

ALTER TABLE users DROP COLUMN cefr_level;
