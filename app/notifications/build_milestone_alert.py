from app.services.apple_push.localized_alert import LocalizedAlert


def build_milestone_alert(streak: int) -> LocalizedAlert:
    """The celebration push when a streak hits a milestone (#3): "%lld-day streak!"."""
    return LocalizedAlert(
        title_loc_key="notif_milestone_title",
        body_loc_key="notif_milestone_body",
        body_args=(str(streak),),
    )
