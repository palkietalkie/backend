import time

from app.services.ws_ticket.constants import DEFAULT_TTL_SECONDS, VERSION
from app.services.ws_ticket.sign_payload import sign_payload


def mint_ws_ticket(user_id: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> str:
    expiry = int(time.time()) + ttl_seconds
    payload = f"{VERSION}.{user_id}.{expiry}"
    return f"{payload}.{sign_payload(payload)}"
