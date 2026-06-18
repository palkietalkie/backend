-- Account deletion is a soft flag, never a hard purge: the user row stays so total-user counts and historical analytics remain intact. A non-null deleted_at means the account is gone from the user's perspective (all API access is rejected) while the row is retained.
ALTER TABLE users ADD COLUMN deleted_at timestamptz;
