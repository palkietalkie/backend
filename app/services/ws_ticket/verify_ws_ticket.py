import hmac
import time

from app.services.ws_ticket.constants import VERSION
from app.services.ws_ticket.sign_payload import sign_payload
from app.services.ws_ticket.ticket_error import TicketError


def verify_ws_ticket(ticket: str) -> dict[str, str | int]:
    # Verify signature + expiry. Returns claims dict on success, raises on failure.
    parts = ticket.split(".")
    if len(parts) != 4 or parts[0] != VERSION:
        raise TicketError("malformed ticket")
    version, user_id, expiry_str, sig = parts
    try:
        expiry = int(expiry_str)
    except ValueError as exc:
        raise TicketError("bad expiry") from exc
    payload = f"{version}.{user_id}.{expiry}"
    expected = sign_payload(payload)
    if not hmac.compare_digest(sig, expected):
        raise TicketError("bad signature")
    if time.time() > expiry:
        raise TicketError("expired")
    return {"user_id": user_id, "expiry": expiry}
