from app.notifications.reminder.build_reminder_push import build_reminder_alert
from app.notifications.reminder.choose_reminder import ReminderKind


def test_keep_streak_carries_the_streak_count_as_an_arg() -> None:
    alert = build_reminder_alert(ReminderKind.KEEP_STREAK, streak=5)
    assert alert.title_loc_key == "notif_keep_streak_title"
    assert alert.body_loc_key == "notif_keep_streak_body"
    assert alert.body_args == ("5",)  # strings on the wire; the catalog %lld renders it


def test_comeback_and_practice_are_static_no_args() -> None:
    for kind in (ReminderKind.COMEBACK, ReminderKind.PRACTICE):
        alert = build_reminder_alert(kind, streak=0)
        assert alert.body_args == ()
        assert alert.title_loc_key.startswith("notif_")
        assert alert.body_loc_key.startswith("notif_")


def test_every_kind_maps_to_distinct_keys() -> None:
    bodies = {build_reminder_alert(kind, 1).body_loc_key for kind in ReminderKind}
    assert len(bodies) == len(list(ReminderKind))
