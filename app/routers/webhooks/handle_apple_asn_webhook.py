from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.config import get_settings
from app.notifications.subscription.notify_subscription_change import notify_subscription_change
from app.notifications.subscription.transition_for_apple_notification import (
    transition_for_apple_notification,
)
from app.services.apple_asn.apply_decision import apply_decision
from app.services.apple_asn.decide_state import decide_state
from app.services.apple_asn.exceptions import (
    AppleLibraryMissingError,
    InvalidSignatureError,
)
from app.services.apple_asn.extract_transaction_and_renewal import (
    extract_transaction_and_renewal,
)
from app.services.apple_asn.get_verifier import get_verifier
from app.services.apple_asn.parse_expires import parse_expires
from app.services.apple_asn.verify_and_decode import verify_and_decode
from app.services.neon.db_conn import DBConn
from app.services.neon.find_user_by_clerk_id import find_user_by_clerk_id
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.slack.format_user_label import format_user_label
from app.services.slack.post_message import post_message

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/apple/asn", status_code=status.HTTP_200_OK)
async def handle_apple_asn_webhook(
    request: Request,
    db: DBConn = Depends(get_neon_connection),
) -> dict[str, str]:
    payload = await request.json()
    signed_payload = payload.get("signedPayload")
    if not signed_payload:
        raise HTTPException(status_code=400, detail="missing signedPayload")

    try:
        verifier = await get_verifier()
    except AppleLibraryMissingError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    try:
        notification_obj, raw_type = verify_and_decode(verifier, signed_payload)
        txn, renewal = extract_transaction_and_renewal(verifier, notification_obj)
    except InvalidSignatureError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    clerk_user_id = txn.get("appAccountToken") or renewal.get("appAccountToken")
    if not clerk_user_id:
        return {"ok": "true", "reason": "no appAccountToken; cannot map to user"}

    decision = decide_state(raw_type)
    if decision is None or raw_type is None:
        return {"ok": "true", "reason": f"unhandled notification {raw_type}"}

    expires_at = parse_expires(txn, renewal)
    auto_renew = renewal.get("autoRenewStatus")
    await apply_decision(
        db,
        clerk_user_id=str(clerk_user_id),
        decision=decision,
        expires_at=expires_at,
        auto_renew=auto_renew if isinstance(auto_renew, int) else None,
    )
    user = await find_user_by_clerk_id(db, str(clerk_user_id))
    label = format_user_label(user) if user is not None else str(clerk_user_id)
    await post_message(
        get_settings().slack_channel_gtm,
        f":apple: *apple_asn.{raw_type.lower()}* — {label} decision=`{decision}`",
    )
    # Push the lifecycle notification AFTER the entitlement write, so a delivery hiccup can't fail the webhook (Apple would retry and re-apply).
    transition = transition_for_apple_notification(raw_type)
    if transition is not None:
        await notify_subscription_change(db, str(clerk_user_id), transition)
    return {"ok": "true"}
