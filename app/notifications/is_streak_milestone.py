# Philosophy: celebrate the user as often as there is a real reason to. Generosity drives the habit loop, so the milestones are three overlapping, deliberately dense tracks with NO ceiling.
# Early calendar marks while the habit is most fragile.
_EARLY_MILESTONES = frozenset({7, 14, 30, 60, 90, 180})  # 1wk, 2wk, ~1mo, ~2mo, ~3mo, ~half-year
# Every yearly anniversary, forever.
_DAYS_PER_YEAR = 365
# Every round 500-day mark. Kicks in at 500 (a round number only feels earned once it is big, 50/100/200 read as noise this early), then 1000, 1500, ...
_ROUND_MILESTONE = 500


def is_streak_milestone(streak: int) -> bool:
    """Whether this streak length is a celebration milestone."""
    if streak in _EARLY_MILESTONES:
        return True
    if streak >= _DAYS_PER_YEAR and streak % _DAYS_PER_YEAR == 0:
        return True
    return streak >= _ROUND_MILESTONE and streak % _ROUND_MILESTONE == 0
