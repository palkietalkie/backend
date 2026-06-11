from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.config import get_settings
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.slack.post_message import post_message
from app.services.stripe_webhooks.dispatch_event import dispatch_event
from app.services.stripe_webhooks.invalid_signature_error import InvalidSignatureError
from app.services.stripe_webhooks.verify_event import verify_event

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe", status_code=status.HTTP_200_OK)
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    db: DBConn = Depends(get_neon_connection),
) -> dict[str, str]:
    settings = get_settings()
    body = await request.body()
    try:
        event = verify_event(
            payload=body,
            signature=stripe_signature,
            secret=settings.stripe_webhook_secret,
        )
    except InvalidSignatureError as e:
        raise HTTPException(status_code=400, detail=f"invalid signature: {e}") from e

    reason = await dispatch_event(db, event)
    await post_message(
        settings.slack_channel_gtm,
        f":credit_card: *stripe.{event['type']}* — reason=`{reason}`",
    )
    if reason != "applied":
        return {"ok": "true", "reason": reason}
    return {"ok": "true"}
