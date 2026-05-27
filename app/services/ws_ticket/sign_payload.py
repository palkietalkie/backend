import base64
import hashlib
import hmac

from app.services.ws_ticket.load_secret import load_secret


def sign_payload(payload: str) -> str:
    sig = hmac.new(load_secret(), payload.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).rstrip(b"=").decode("ascii")
