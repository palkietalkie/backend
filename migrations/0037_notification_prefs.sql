-- Per-user re-engagement notification preferences + send bookkeeping, in their own table (not columns on `users`) so the core user record stays lean and this stays a separable, extensible concern (room for per-type toggles later). The streak is NOT stored here (derived on demand by compute_day_streak, per 0004); these are the parts the sender can't derive: whether the user wants reminders, the local hour to aim the daily nudge at (early-evening default), and a dedup stamp so the hourly scheduler sends at most one reminder per local day. A user with no row uses the defaults (LEFT JOIN + COALESCE at query time), so a row is written only when they change a setting or we stamp a send. This is not the phone's OS notification permission, APNs enforces that via device-token validity; this is the in-app "do you want practice reminders" preference.
CREATE TABLE notification_prefs (
    user_id             UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    reminders_enabled   BOOLEAN NOT NULL DEFAULT TRUE,
    reminder_hour_local SMALLINT NOT NULL DEFAULT 19 CHECK (reminder_hour_local BETWEEN 0 AND 23),
    last_reminded_on    DATE,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
