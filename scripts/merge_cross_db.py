# ruff: noqa: S608 (interpolates table/column identifiers from an internal fixed config, never user input; SQL identifiers can't be bound as params)
import uuid

import asyncpg


async def merge_cross_db(
    dev: asyncpg.Connection,
    prd: asyncpg.Connection,
    src: str,
    tgt: str,
    agg_tables: dict[str, tuple[str, str]],
) -> None:
    """dev -> prd: copy rows into the target DB under the target user, remapping session PKs so transcripts/audio still resolve; aggregates are summed into the target.

    agg_tables maps each summed table to (natural key column, recency timestamp column).
    """
    id_map: dict[uuid.UUID, uuid.UUID] = {}
    for r in await dev.fetch(
        "SELECT id, persona_id, started_at, ended_at, duration_seconds FROM conversation_sessions WHERE user_id=$1",
        src,
    ):
        new_id = uuid.uuid4()
        id_map[r["id"]] = new_id
        await prd.execute(
            """INSERT INTO conversation_sessions (id, user_id, persona_id, started_at, ended_at, duration_seconds)
               VALUES ($1,$2,$3,$4,$5,$6)""",
            new_id,
            tgt,
            r["persona_id"],
            r["started_at"],
            r["ended_at"],
            r["duration_seconds"],
        )
    for old_id, new_id in id_map.items():
        for t in await dev.fetch(
            "SELECT speaker, text, started_at, ended_at FROM transcripts WHERE session_id=$1",
            old_id,
        ):
            await prd.execute(
                "INSERT INTO transcripts (session_id, speaker, text, started_at, ended_at) VALUES ($1,$2,$3,$4,$5)",
                new_id,
                t["speaker"],
                t["text"],
                t["started_at"],
                t["ended_at"],
            )
        for a in await dev.fetch(
            "SELECT audio, bytes, format, created_at, expires_at, source FROM session_audio WHERE session_id=$1",
            old_id,
        ):
            await prd.execute(
                """INSERT INTO session_audio (session_id, user_id, audio, bytes, format, created_at, expires_at, source)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8)""",
                new_id,
                tgt,
                a["audio"],
                a["bytes"],
                a["format"],
                a["created_at"],
                a["expires_at"],
                a["source"],
            )
    for e in await dev.fetch("SELECT event_type, ts, props FROM events WHERE user_id=$1", src):
        await prd.execute(
            "INSERT INTO events (user_id, event_type, ts, props) VALUES ($1,$2,$3,$4)",
            tgt,
            e["event_type"],
            e["ts"],
            e["props"],
        )
    for p in await dev.fetch(
        """SELECT name, voice_id, description, role, age, background, vocabulary_register,
                  conversational_style, topical_preferences, is_public, created_at, updated_at
           FROM personas WHERE user_id=$1""",
        src,
    ):
        await prd.execute(
            """INSERT INTO personas (id, user_id, name, voice_id, description, role, age, background,
                                     vocabulary_register, conversational_style, topical_preferences,
                                     is_public, like_count, created_at, updated_at)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,0,$13,$14)""",
            uuid.uuid4(),
            tgt,
            p["name"],
            p["voice_id"],
            p["description"],
            p["role"],
            p["age"],
            p["background"],
            p["vocabulary_register"],
            p["conversational_style"],
            p["topical_preferences"],
            p["is_public"],
            p["created_at"],
            p["updated_at"],
        )
    for table, (key, ts) in agg_tables.items():
        for row in await dev.fetch(f"SELECT {key}, count, {ts} FROM {table} WHERE user_id=$1", src):
            await prd.execute(
                f"""INSERT INTO {table} (user_id, {key}, count, {ts}) VALUES ($1,$2,$3,$4)
                    ON CONFLICT (user_id, {key})
                    DO UPDATE SET count={table}.count + EXCLUDED.count,
                                 {ts}=GREATEST({table}.{ts}, EXCLUDED.{ts})""",
                tgt,
                row[key],
                row["count"],
                row[ts],
            )
    for m in await dev.fetch(
        "SELECT original, corrected, category, count, last_seen_at FROM mistakes WHERE user_id=$1",
        src,
    ):
        await prd.execute(
            """INSERT INTO mistakes (id, user_id, original, corrected, category, count, last_seen_at)
               VALUES (gen_random_uuid(), $1,$2,$3,$4,$5,$6)
               ON CONFLICT (user_id, original, corrected)
               DO UPDATE SET count=mistakes.count + EXCLUDED.count,
                            last_seen_at=GREATEST(mistakes.last_seen_at, EXCLUDED.last_seen_at)""",
            tgt,
            m["original"],
            m["corrected"],
            m["category"],
            m["count"],
            m["last_seen_at"],
        )
