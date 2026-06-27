from app.notifications.reminder.choose_reminder import ReminderKind
from app.services.apple_push.localized_alert import LocalizedAlert

# Each kind maps to a (title, body) pair of catalog keys. APNs localizes them on the device: these keys must exist in ios/PalkieTalkie/Localizable.xcstrings, and iOS renders them in the user's device language at delivery.
_LOC_KEYS: dict[ReminderKind, tuple[str, str]] = {
    ReminderKind.KEEP_STREAK: ("notif_keep_streak_title", "notif_keep_streak_body"),
    ReminderKind.COMEBACK: ("notif_comeback_title", "notif_comeback_body"),
    ReminderKind.PRACTICE: ("notif_practice_title", "notif_practice_body"),
}


def build_reminder_alert(kind: ReminderKind, streak: int) -> LocalizedAlert:
    """The localized alert for a re-engagement push. Only KEEP_STREAK takes an arg (the streak count fills `%lld` in its body); the others are static."""
    title_key, body_key = _LOC_KEYS[kind]
    args = (str(streak),) if kind is ReminderKind.KEEP_STREAK else ()
    return LocalizedAlert(title_loc_key=title_key, body_loc_key=body_key, body_args=args)
