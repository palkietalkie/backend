# The `kind` column values in notification_log. The "should I send?" check and the post-send stamp must use the SAME string per family, or dedup silently breaks and the user gets doubles, so both sides import these constants instead of repeating literals.
# notification_log.per_kind_key holds a DIFFERENT thing per kind (the column name can't say what, its meaning is per-kind), so each kind documents its key's meaning here, next to the kind, the one place it's actually true:
DAILY_REMINDER = (
    "daily_reminder"  # per_kind_key = user's local date 'YYYY-MM-DD'; one nudge per local day
)
STREAK_WARNING = (
    "streak_warning"  # per_kind_key = user's local date 'YYYY-MM-DD'; one warning per local day
)
MILESTONE = "milestone"  # per_kind_key = the streak length reached as text, e.g. '30'; one celebration per milestone
