import os

from app.services.ws_ticket.ticket_error import TicketError


def load_secret() -> bytes:
    secret = os.environ.get("WS_TICKET_SECRET")
    if not secret:
        raise TicketError("WS_TICKET_SECRET not configured")
    return secret.encode("utf-8")
