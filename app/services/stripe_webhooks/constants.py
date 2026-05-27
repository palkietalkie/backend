SOURCE = "stripe"

ACTIVE_STATUSES: frozenset[str] = frozenset({"active", "trialing", "past_due"})
