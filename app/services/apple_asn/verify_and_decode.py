from app.services.apple_asn._sdk import VerificationException
from app.services.apple_asn._verifier_protocol import VerifierProtocol
from app.services.apple_asn.coerce_to_dict import coerce_to_dict
from app.services.apple_asn.exceptions import InvalidSignatureError


def verify_and_decode(verifier: VerifierProtocol, signed_payload: str) -> tuple[object, str | None]:
    try:
        notification_obj = verifier.verify_and_decode_notification(signed_payload)
    except VerificationException as e:
        raise InvalidSignatureError(f"Apple JWS verification failed: {e}") from e
    notification = coerce_to_dict(notification_obj)
    raw_type = (
        getattr(notification_obj, "rawNotificationType", None)
        or notification.get("rawNotificationType")
        or notification.get("notificationType")
    )
    return notification_obj, raw_type if raw_type is None else str(raw_type)
