from app.services.apple_push.localized_alert import LocalizedAlert


def build_streak_warning_alert(streak: int) -> LocalizedAlert:
    """The push for the streak-warning nudge (#2): a late-evening "your N-day streak ends tonight" for a streak-holder who hasn't practiced yet today. Kept separate from the daily-nudge content (build_reminder_alert) because it's its own notification type with its own trigger, not a value choose_reminder ever returns."""
    return LocalizedAlert(
        title_loc_key="notif_streak_warning_title",
        body_loc_key="notif_streak_warning_body",
        body_args=(str(streak),),
    )
