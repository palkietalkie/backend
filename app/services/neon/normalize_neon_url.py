"""Make a Neon connection string consumable by asyncpg.

The URL Neon hands you (dashboard / NEON_DATABASE_URL) is in libpq/psycopg2 form: it carries `sslmode=require` + `channel_binding=require` query params and may wear a SQLAlchemy `postgresql+asyncpg://` scheme suffix. asyncpg.connect understands none of these — it spells TLS as `ssl=`, not `sslmode=`, and rejects the driver-suffixed scheme — so create_pool would raise on the raw URL. Stripping them here lets the same env var feed both asyncpg and any psycopg2 / SQLAlchemy tooling that shares it.
"""

from urllib.parse import urlsplit, urlunsplit

_PSYCOPG2_ONLY_PARAMS = ("sslmode=", "channel_binding=")


def normalize_neon_url(url: str) -> str:
    # Strip SQLAlchemy "+asyncpg" driver suffix and Neon-style psycopg2 query params that asyncpg doesn't understand. TLS is still negotiated automatically when the host requires it.
    if url.startswith("postgresql+asyncpg://"):
        url = "postgresql://" + url[len("postgresql+asyncpg://") :]
    parts = urlsplit(url)
    if parts.query:
        kept = [kv for kv in parts.query.split("&") if not kv.startswith(_PSYCOPG2_ONLY_PARAMS)]
        url = urlunsplit(parts._replace(query="&".join(kept)))
    return url
