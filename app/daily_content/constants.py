# Topics rendered on the Today screen, in display order. Adding a new topic = append a slug here, add a fetcher, add an xcstring entry on iOS for the localized section header. No migration required.
TOPICS: tuple[str, ...] = ("politics", "business", "sports", "quizzes")

# Topics that are timeless rather than time-sensitive (quizzes — not tied to today's news). For these, the router doesn't return today's row directly; instead it aggregates the entire historical pool and samples deterministically with today's date as the RNG seed. New items still accumulate via the daily scheduler, but users see a rotating cut, not just "what got generated today."
POOL_TOPICS: frozenset[str] = frozenset({"quizzes"})

POOL_SAMPLE_SIZE = 10
