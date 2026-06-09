"""Daily cron: delete expired session_audio rows.

Runs in-process via lifespan, same pattern as `run_daily_content_scheduler`. One DELETE statement per day is more than enough — session_audio rows TTL out in 14 days and we don't need to be precise about the cleanup hour.

DELETE only — no separate object-storage purge step. The audio bytes live in the table itself (BYTEA column), so deleting the row reclaims the bytes (after the next autovacuum). If we move to object storage later, this is where the object delete goes.
"""

import asyncio
import logging
from datetime import UTC, datetime, time, timedelta

from app.services.neon.db_conn import DBConn
from app.services.neon.get_pool import get_pool

logger = logging.getLogger(__name__)

# 07:00 UTC, an hour after the daily_content refresh at 06:00 UTC. No conflict needed (different table), but staggered so log lines from the two schedulers don't interleave during the same wall-clock minute.
PRUNE_HOUR_UTC = 7


async def prune_expired_audio_once(conn: DBConn | None = None) -> int:
    """Single pass. Returns the row count deleted. Pass `conn` to reuse a caller's connection (tests use the transaction-bound fixture); otherwise we acquire one from the pool."""
    if conn is not None:
        result = await conn.execute("DELETE FROM session_audio WHERE expires_at < NOW()")
    else:
        pool = await get_pool()
        async with pool.acquire() as acquired:
            result = await acquired.execute("DELETE FROM session_audio WHERE expires_at < NOW()")
    # asyncpg returns the command tag, e.g. "DELETE 7" — pull the count.
    try:
        deleted = int(result.split()[-1])
    except ValueError:
        deleted = 0
    except IndexError:
        deleted = 0
    if deleted:
        logger.info("session_audio prune deleted %d expired rows", deleted)
    return deleted


async def run_prune_expired_audio_scheduler() -> None:
    """Forever-loop: sleep until next 07:00 UTC, run one prune pass, repeat."""
    # Startup catch-up — if the server was down at 07:00, run now so we don't sit on stale rows for another full day.
    try:
        await prune_expired_audio_once()
    except Exception:
        logger.exception("session_audio prune startup catch-up failed")

    while True:
        now = datetime.now(UTC)
        target = datetime.combine(now.date(), time(PRUNE_HOUR_UTC, 0), tzinfo=UTC)
        if target <= now:
            target += timedelta(days=1)
        sleep_seconds = (target - now).total_seconds()
        logger.info(
            "session_audio prune next run at %s (in %.0fs)", target.isoformat(), sleep_seconds
        )
        await asyncio.sleep(sleep_seconds)
        try:
            await prune_expired_audio_once()
        except Exception:
            logger.exception("session_audio prune scheduled run failed")
