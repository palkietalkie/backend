from app.services.apple_push.localized_alert import LocalizedAlert


def build_milestone_alert(streak: int) -> LocalizedAlert:
    """The celebration push when a streak hits a milestone: an "N-day streak!" with the streak count filled in."""
    return LocalizedAlert(
        title_loc_key="notif_milestone_title",
        body_loc_key="notif_milestone_body",
        body_args=(str(streak),),
    )
