from enum import Enum

# Not practiced in this many local days → switch the nudge from streak-keeping to winback.
COMEBACK_AFTER_DAYS = 2


class ReminderKind(Enum):
    # Streak alive: "keep your N-day streak going, practice today". Doubles as the streak-at-risk nudge.
    KEEP_STREAK = "keep_streak"
    # Lapsed for a couple days: "we miss you".
    COMEBACK = "comeback"
    # No active streak: a plain "time to practice".
    PRACTICE = "practice"


def choose_reminder(
    streak: int, days_since_practice: int | None, practiced_today: bool
) -> ReminderKind | None:
    """Which re-engagement push to send a user at their reminder hour, or None to stay quiet.

    Pure so the policy is unit-testable; the scheduler supplies the per-user facts (streak from compute_day_streak, last-practice + practiced-today from session history)."""
    if practiced_today:
        # They already showed up today; nudging now would just annoy.
        return None
    if days_since_practice is not None and days_since_practice >= COMEBACK_AFTER_DAYS:
        return ReminderKind.COMEBACK
    if streak > 0:
        return ReminderKind.KEEP_STREAK
    return ReminderKind.PRACTICE
