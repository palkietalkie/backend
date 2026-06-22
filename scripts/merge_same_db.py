# ruff: noqa: S608 (interpolates table/column identifiers from an internal fixed config, never user input; SQL identifiers can't be bound as params)
import asyncpg


async def merge_same_db(
    conn: asyncpg.Connection, src: str, tgt: str, agg_tables: dict[str, tuple[str, str]]
) -> None:
    """prd -> prd: reassign rows by UPDATE; sum the aggregate tables via ON CONFLICT, then delete the now-merged source rows so a re-run never double-counts.

    agg_tables maps each summed table to (natural key column, recency timestamp column).
    """
    await conn.execute("UPDATE conversation_sessions SET user_id=$2 WHERE user_id=$1", src, tgt)
    await conn.execute("UPDATE session_audio SET user_id=$2 WHERE user_id=$1", src, tgt)
    await conn.execute("UPDATE events SET user_id=$2 WHERE user_id=$1", src, tgt)
    await conn.execute("UPDATE personas SET user_id=$2 WHERE user_id=$1", src, tgt)
    for table, (key, ts) in agg_tables.items():
        await conn.execute(
            f"""INSERT INTO {table} (user_id, {key}, count, {ts})
                SELECT $2, {key}, count, {ts} FROM {table} WHERE user_id=$1
                ON CONFLICT (user_id, {key})
                DO UPDATE SET count={table}.count + EXCLUDED.count,
                             {ts} = GREATEST({table}.{ts}, EXCLUDED.{ts})""",
            src,
            tgt,
        )
        await conn.execute(f"DELETE FROM {table} WHERE user_id=$1", src)
    await conn.execute(
        """INSERT INTO mistakes (id, user_id, original, corrected, category, count, last_seen_at)
           SELECT gen_random_uuid(), $2, original, corrected, category, count, last_seen_at
           FROM mistakes WHERE user_id=$1
           ON CONFLICT (user_id, original, corrected)
           DO UPDATE SET count=mistakes.count + EXCLUDED.count,
                        last_seen_at=GREATEST(mistakes.last_seen_at, EXCLUDED.last_seen_at)""",
        src,
        tgt,
    )
    await conn.execute("DELETE FROM mistakes WHERE user_id=$1", src)
