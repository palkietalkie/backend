class TicketError(Exception):
    # Raised on any verify failure: malformed, bad signature, expired.
    pass
