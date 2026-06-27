from app.notifications.milestone.build_milestone_alert import build_milestone_alert


def test_carries_streak_to_milestone_loc_keys() -> None:
    alert = build_milestone_alert(30)
    assert alert.title_loc_key == "notif_milestone_title"
    assert alert.body_loc_key == "notif_milestone_body"
    assert alert.body_args == ("30",)
