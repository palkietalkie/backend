from app.services.apple_push.localized_alert import LocalizedAlert


def build_daily_content_alert(headline: str) -> LocalizedAlert:
    """The morning content nudge: references TODAY'S actual top headline ("Did you catch this? <headline>") instead of a generic "topics are ready", so it reads like a person, not a system announcement.

    The headline is the real English news the user will practice on, so it stays English even under a localized UI, the fixed copy localizes, the headline rides in as the arg."""
    return LocalizedAlert(
        title_loc_key="notif_daily_content_title",
        body_loc_key="notif_daily_content_body",
        body_args=(headline,),
    )
