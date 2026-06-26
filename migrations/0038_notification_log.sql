-- One append-only dedup log for EVERY notification type, so adding a new type is a new `kind` string in code, never a new column (the column-per-type churn this replaces). `kind` is the notification family ('daily_reminder', 'streak_warning', 'milestone', ...); `per_kind_key` is whatever makes "already sent" unique for that kind, a local date 'YYYY-MM-DD' for the once-per-day nudges, the streak number for a once-per-milestone celebration. The (user_id, kind, per_kind_key) primary key makes "should I send?" a cheap NOT EXISTS and the stamp an idempotent INSERT ... ON CONFLICT DO NOTHING (a scheduler restart re-running a tick can't double-send).
CREATE TABLE notification_log (
    user_id   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind      TEXT NOT NULL,
    per_kind_key TEXT NOT NULL,
    sent_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, kind, per_kind_key)
);

-- The daily reminder now dedups in notification_log like every other type, so notification_prefs.last_reminded_on (added in 0037) is superseded. Forward-only drop: 0037 stays as it was applied, this single migration reconciles both dev (already has the column) and a fresh prod (gets it from 0037, dropped here).
ALTER TABLE notification_prefs DROP COLUMN last_reminded_on;
