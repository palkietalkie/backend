"""Print the most recent conversation session + its transcript turns.

Diagnostic for echo-loop / self-talk bugs. Inspect at a glance whether the user actually spoke (real-looking turns) or the rows under speaker=user are OpenAI Whisper transcribing the AI's own speaker bleed (one-word fragments at the same second the persona was talking).

Run from the backend project venv (uses the full app dep tree, including pydantic + asyncpg): `cd backend && uv run scripts/neon/dump_latest_session.py`
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.services.neon.get_neon_pool import get_neon_pool  # noqa: E402
from scripts.neon.fetch_latest_session import fetch_latest_session  # noqa: E402
from scripts.neon.fetch_session_transcripts import fetch_session_transcripts  # noqa: E402


async def main() -> None:
    pool = await get_neon_pool()
    async with pool.acquire() as db:
        session = await fetch_latest_session(db)
        if session is None:
            print("no conversation_sessions rows")
            return
        print(
            f"session: id={session['id']} started={session['started_at']} "
            f"ended={session['ended_at']} dur={session['duration_seconds']}s"
        )
        print(f"  user_id={session['user_id']} persona_id={session['persona_id']}")
        print()
        turns = await fetch_session_transcripts(db, session["id"])
        print(f"{len(turns)} transcript turns:")
        for t in turns:
            text = t["text"][:200] + ("…" if len(t["text"]) > 200 else "")
            print(f"  [{t['started_at'].strftime('%H:%M:%S.%f')[:-3]}] {t['speaker']:>7}: {text}")


if __name__ == "__main__":
    asyncio.run(main())
