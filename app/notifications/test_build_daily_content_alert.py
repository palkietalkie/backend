from app.notifications.build_daily_content_alert import build_daily_content_alert


def test_injects_the_headline_as_the_body_arg() -> None:
    alert = build_daily_content_alert("Apple unveils its first foldable iPhone")
    assert alert.title_loc_key == "notif_daily_content_title"
    assert alert.body_loc_key == "notif_daily_content_body"
    assert alert.body_args == ("Apple unveils its first foldable iPhone",)
