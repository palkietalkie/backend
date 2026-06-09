from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.config import get_settings
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
from app.services.neon.get_db import get_db
from app.services.slack.post_message import post_message

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/apple/asn", status_code=status.HTTP_200_OK)
async def handle_apple_asn_webhook(
    request: Request,
    db: DBConn = Depends(get_db),
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
    await post_message(
        get_settings().slack_channel_gtm,
        f":apple: *apple_asn.{raw_type.lower()}* — user `{clerk_user_id}` decision=`{decision}`",
    )
    return {"ok": "true"}
