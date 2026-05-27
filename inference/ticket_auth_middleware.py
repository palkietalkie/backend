"""aiohttp middleware for the voice WebSocket.

Single responsibility: gate `/api/chat` on a valid HMAC ticket. Other routes (`/health`) pass through.
"""

from __future__ import annotations

from aiohttp import web
from ws_ticket.ticket_error import TicketError
from ws_ticket.verify_ws_ticket import verify_ws_ticket


@web.middleware
async def ticket_auth_middleware(request, handler):
    """Enforce HMAC ticket auth on the WebSocket path. Other paths pass through."""
    if request.path != "/api/chat":
        return await handler(request)
    ticket = request.query.get("auth_token", "")
    try:
        claims = verify_ws_ticket(ticket)
    except TicketError as exc:
        return web.json_response(
            {"error": "auth_failed", "detail": str(exc)},
            status=401,
        )
    request["ticket_claims"] = claims
    return await handler(request)
