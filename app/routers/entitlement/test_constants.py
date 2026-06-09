"""Lock in the published free-plan caps so an accidental change forces a thread of follow-ups (iOS copy, website pricing, marketing). Pre-launch we never want these drifting silently."""

from app.routers.entitlement.constants import FREE_MINUTES_PER_DAY, FREE_MINUTES_PER_WEEK


def test_free_plan_caps_match_advertised_copy() -> None:
    assert FREE_MINUTES_PER_DAY == 10
    assert FREE_MINUTES_PER_WEEK == 30


def test_day_cap_is_smaller_than_week_cap() -> None:
    assert FREE_MINUTES_PER_DAY <= FREE_MINUTES_PER_WEEK


def test_caps_are_positive_integers() -> None:
    assert isinstance(FREE_MINUTES_PER_DAY, int) and FREE_MINUTES_PER_DAY > 0
    assert isinstance(FREE_MINUTES_PER_WEEK, int) and FREE_MINUTES_PER_WEEK > 0
