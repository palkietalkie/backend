from app.notifications.build_weekly_recap_alert import build_weekly_recap_alert


def test_one_session_with_streak() -> None:
    alert = build_weekly_recap_alert(sessions=1, minutes=8, streak=3)
    assert alert.title_loc_key == "notif_weekly_recap_title"
    assert alert.body_loc_key == "notif_weekly_recap_body_one"
    assert alert.body_args == ("1", "8", "3")  # sessions, minutes, streak (count is a numeral arg)


def test_one_session_without_streak_drops_the_streak_clause() -> None:
    alert = build_weekly_recap_alert(sessions=1, minutes=8, streak=0)
    assert alert.body_loc_key == "notif_weekly_recap_body_one_no_streak"
    assert alert.body_args == ("1", "8")  # sessions, minutes


def test_any_live_streak_is_shown_as_current_state() -> None:
    # The current streak is shown for any value > 0 (framed as present state, "you're on an N-day streak").
    alert = build_weekly_recap_alert(sessions=4, minutes=20, streak=1)
    assert alert.body_loc_key == "notif_weekly_recap_body_other"
    assert alert.body_args == ("4", "20", "1")


def test_lapsed_streak_zero_drops_the_clause() -> None:
    alert = build_weekly_recap_alert(sessions=4, minutes=20, streak=0)
    assert alert.body_loc_key == "notif_weekly_recap_body_other_no_streak"
    assert alert.body_args == ("4", "20")


def test_many_sessions_with_streak() -> None:
    alert = build_weekly_recap_alert(sessions=5, minutes=40, streak=12)
    assert alert.body_loc_key == "notif_weekly_recap_body_other"
    assert alert.body_args == ("5", "40", "12")


def test_many_sessions_without_streak_drops_the_streak_clause() -> None:
    alert = build_weekly_recap_alert(sessions=5, minutes=40, streak=0)
    assert alert.body_loc_key == "notif_weekly_recap_body_other_no_streak"
    assert alert.body_args == ("5", "40")
