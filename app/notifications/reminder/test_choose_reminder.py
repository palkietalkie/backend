from app.notifications.reminder.choose_reminder import ReminderKind, choose_reminder


def test_practiced_today_sends_nothing() -> None:
    # Already showed up today → no nudge, regardless of streak.
    assert choose_reminder(streak=5, days_since_practice=0, practiced_today=True) is None


def test_active_streak_not_practiced_today_keeps_streak() -> None:
    assert (
        choose_reminder(streak=5, days_since_practice=1, practiced_today=False)
        == ReminderKind.KEEP_STREAK
    )


def test_lapsed_two_days_is_comeback() -> None:
    assert (
        choose_reminder(streak=0, days_since_practice=2, practiced_today=False)
        == ReminderKind.COMEBACK
    )


def test_long_lapse_is_comeback_even_with_a_stale_streak_value() -> None:
    # days_since_practice drives the lapse decision, not the streak number.
    assert (
        choose_reminder(streak=3, days_since_practice=9, practiced_today=False)
        == ReminderKind.COMEBACK
    )


def test_no_streak_no_recent_practice_is_generic_practice() -> None:
    assert (
        choose_reminder(streak=0, days_since_practice=1, practiced_today=False)
        == ReminderKind.PRACTICE
    )


def test_never_practiced_is_generic_practice() -> None:
    assert (
        choose_reminder(streak=0, days_since_practice=None, practiced_today=False)
        == ReminderKind.PRACTICE
    )
