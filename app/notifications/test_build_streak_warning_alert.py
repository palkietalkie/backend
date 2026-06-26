from app.notifications.build_streak_warning_alert import build_streak_warning_alert


def test_carries_streak_count_to_streak_warning_loc_keys() -> None:
    alert = build_streak_warning_alert(streak=7)
    assert alert.title_loc_key == "notif_streak_warning_title"
    assert alert.body_loc_key == "notif_streak_warning_body"
    assert alert.body_args == ("7",)
