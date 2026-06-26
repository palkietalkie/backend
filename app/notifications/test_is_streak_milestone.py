from app.notifications.is_streak_milestone import is_streak_milestone


def test_recognizes_early_calendar_milestones() -> None:
    for streak in (7, 14, 30, 60, 90, 180):
        assert is_streak_milestone(streak)


def test_celebrates_every_yearly_anniversary_with_no_ceiling() -> None:
    for streak in (365, 730, 1095, 3650):
        assert is_streak_milestone(streak)


def test_celebrates_every_round_500_mark() -> None:
    for streak in (500, 1000, 1500, 2000):
        assert is_streak_milestone(streak)


def test_non_milestones_are_not() -> None:
    # Includes the arbitrary round numbers we deliberately dropped (50, 100, 200) and near-misses of the yearly/500 marks.
    for streak in (0, 1, 6, 8, 13, 29, 50, 100, 200, 364, 366, 499, 729):
        assert not is_streak_milestone(streak)
