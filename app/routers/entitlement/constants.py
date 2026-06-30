from datetime import timedelta

# Free-plan caps. Both limits apply — a user hitting EITHER stops them until the corresponding window rolls over. Numbers are likely to be tuned; keep them in this file so the change is one-liner. Day window = user-local midnight; week window = user-local Monday 00:00.
FREE_MINUTES_PER_DAY = 10
FREE_MINUTES_PER_WEEK = 30

# First-month free trial: a brand-new user gets uncapped, premium-equivalent access for this long from signup, so the daily/weekly caps don't bite while they're still deciding if the app is for them (the "ask people to try it, then they hit 10 min in one sitting" problem). 30 days, not a calendar month, to dodge month-length edge cases. Derived purely from users.created_at — it expires on its own, no trial column or cron.
FREE_TRIAL_DURATION = timedelta(days=30)
