from urllib.parse import urlsplit, urlunsplit

_PSYCOPG2_ONLY_PARAMS = ("sslmode=", "channel_binding=")


def normalize_url(url: str) -> str:
    # Strip SQLAlchemy "+asyncpg" driver suffix and Neon-style psycopg2 query params that asyncpg doesn't understand. TLS is still negotiated automatically when the host requires it.
    if url.startswith("postgresql+asyncpg://"):
        url = "postgresql://" + url[len("postgresql+asyncpg://") :]
    parts = urlsplit(url)
    if parts.query:
        kept = [kv for kv in parts.query.split("&") if not kv.startswith(_PSYCOPG2_ONLY_PARAMS)]
        url = urlunsplit(parts._replace(query="&".join(kept)))
    return url
