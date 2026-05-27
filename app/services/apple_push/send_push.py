from aioapns import NotificationRequest, PushType
from aioapns.exceptions import ConnectionClosed as APNsConnectionClosed
from aioapns.exceptions import ConnectionError as APNsConnectionError
from aioapns.exceptions import MaxAttemptsExceeded as APNsMaxAttemptsExceeded

from app.services.apple_push.get_client import get_client
from app.services.apple_push.push_result import PushResult


async def send_push(
    token: str,
    title: str,
    body: str,
    badge: int | None = None,
) -> PushResult:
    request = NotificationRequest(
        device_token=token,
        message={
            "aps": {
                "alert": {"title": title, "body": body},
                "sound": "default",
                **({"badge": badge} if badge is not None else {}),
            }
        },
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
