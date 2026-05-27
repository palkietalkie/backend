from app.services.apple_asn.constants import APPLE_NOTIFICATION_TO_STATE


def decide_state(notification_type: str | None) -> tuple[str, bool] | None:
    # ``None`` means we choose to ignore that notification type.
    if not notification_type:
        return None
    return APPLE_NOTIFICATION_TO_STATE.get(notification_type)
