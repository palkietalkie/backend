from typing import Any

from aioapns import NotificationRequest, PushType
from aioapns.exceptions import ConnectionClosed as APNsConnectionClosed
from aioapns.exceptions import ConnectionError as APNsConnectionError
from aioapns.exceptions import MaxAttemptsExceeded as APNsMaxAttemptsExceeded

from app.services.apple_push.get_client import get_client
from app.services.apple_push.localized_alert import LocalizedAlert
from app.services.apple_push.push_result import PushResult


async def send_push(token: str, alert: LocalizedAlert, badge: int | None = None) -> PushResult:
    """Send one APNs alert push. The single push sender.

    `alert` localizes on the device via loc-keys (the user reads it in their device language, the convention for the OS notification center where these appear). The sender serializes the typed alert into the `aps.alert` shape so callers never hand-build the hyphenated APNs keys. `badge` sets the app-icon count when a notification type wants one (left unset for reminders, which aren't a countable-unread concept)."""
    aps_alert: dict[str, str | list[str]] = {
        "title-loc-key": alert.title_loc_key,
        "loc-key": alert.body_loc_key,
    }
    if alert.body_args:
        aps_alert["loc-args"] = list(alert.body_args)
    aps: dict[str, Any] = {"alert": aps_alert, "sound": "default"}
    if badge is not None:
        aps["badge"] = badge
    request = NotificationRequest(
        device_token=token,
        message={"aps": aps},
        push_type=PushType.ALERT,
    )
    try:
        response = await get_client().send_notification(request)
    except (
        APNsConnectionClosed,
        APNsConnectionError,
        APNsMaxAttemptsExceeded,
        OSError,
        TimeoutError,
    ) as e:
        return PushResult(token=token, ok=False, reason=str(e))

    if response.is_successful:
        return PushResult(token=token, ok=True)
    return PushResult(token=token, ok=False, reason=response.description)
