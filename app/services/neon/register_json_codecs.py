import json

import asyncpg


async def register_json_codecs(conn: asyncpg.Connection) -> None:
    # Register JSONB / JSON codecs so dict[str, Any] roundtrips without surprises.
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )
    await conn.set_type_codec(
        "json",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )
