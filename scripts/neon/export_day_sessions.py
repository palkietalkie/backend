"""Export a day's conversation sessions (audio + transcripts) to a local folder for manual review.

Distinct from dump_session_audio.py (a single-session AEC diagnostic that prints RMS/peak/strip-chart to /tmp): this is a batch export of EVERY session in a Pacific-time day, both tracks (mic = the user's voice, model = the tutor's), plus each session's transcript, named by user + PT timestamp so the founder can sit and listen back to learn customers.

Run: `cd backend && uv run scripts/neon/export_day_sessions.py --prd [YYYY-MM-DD] [--out DIR]`
Default date is yesterday (Pacific day). Default out is ios/recordings/<date> (gitignored). The mic track is absent for any session whose best-effort iOS upload didn't land.
"""

from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import asyncpg  # noqa: E402
import soundfile as sf  # noqa: E402

from app.services.neon.normalize_neon_url import normalize_neon_url  # noqa: E402
from scripts.neon.decode_audio_bytes import decode_audio_bytes  # noqa: E402
from scripts.neon.fetch_session_audio import fetch_session_audio  # noqa: E402
from scripts.neon.fetch_session_transcripts import fetch_session_transcripts  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]


def read_database_url(prd: bool) -> str:
    # prd lives in .env.production (kept out of the regular .env on purpose); dev in .env. Read the file directly: get_settings()/get_neon_pool only ever see the dev .env, so they can't reach prd.
    env_file = REPO_ROOT / "backend" / (".env.production" if prd else ".env")
    for line in env_file.read_text().splitlines():
        if line.startswith("NEON_DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(f"NEON_DATABASE_URL not found in {env_file}")


def safe(name: str) -> str:
    return re.sub(r"[^\w .-]", "_", name).strip()


async def main() -> None:
    flags = set(sys.argv[1:])
    prd = "--prd" in flags
    out_idx = sys.argv.index("--out") if "--out" in sys.argv else -1
    out_override = sys.argv[out_idx + 1] if out_idx >= 0 else None
    date_args = [
        a
        for i, a in enumerate(sys.argv[1:], 1)
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", a) and i != out_idx + 1
    ]
    day = date_args[0] if date_args else None

    pool = await asyncpg.create_pool(
        normalize_neon_url(read_database_url(prd)), min_size=1, max_size=4
    )
    assert pool is not None
    try:
        async with pool.acquire() as db:
            day_label = await db.fetchval(
                "SELECT COALESCE($1::date, (now() AT TIME ZONE 'America/Los_Angeles')::date - 1)::text",
                day,
            )
            out = (
                Path(out_override) if out_override else REPO_ROOT / "ios" / "recordings" / day_label
            )
            out.mkdir(parents=True, exist_ok=True)
            sessions = await db.fetch(
                """SELECT s.id,
                          COALESCE(u.preferred_name, u.email, u.id::text) AS user_name,
                          to_char(s.started_at AT TIME ZONE 'America/Los_Angeles','YYYY-MM-DD HH24MISS') AS started_pt,
                          s.duration_seconds AS dur
                   FROM conversation_sessions s
                   JOIN users u ON u.id = s.user_id
                   WHERE (s.started_at AT TIME ZONE 'America/Los_Angeles')::date
                         = COALESCE($1::date, (now() AT TIME ZONE 'America/Los_Angeles')::date - 1)
                   ORDER BY s.started_at""",
                day,
            )
            n_audio = n_txt = 0
            for s in sessions:
                base = f"{safe(s['user_name'])} {s['started_pt']} PT"
                turns = await fetch_session_transcripts(db, s["id"])
                if turns:
                    lines = [f"{base}  (session {s['id']}, dur={s['dur']}s)\n"]
                    for t in turns:
                        who = "USER" if t["speaker"] == "user" else "TUTOR"
                        stamp = t["started_at"].strftime("%H:%M:%S")
                        lines.append(f"[{stamp}] {who}: {t['text']}")
                    (out / f"{base}.txt").write_text("\n".join(lines) + "\n")
                    n_txt += 1
                for src in ("mic", "model"):
                    got = await fetch_session_audio(db, s["id"], source=src)
                    if got is None:
                        continue
                    audio, sr = decode_audio_bytes(got[0])
                    sf.write(str(out / f"{base} {src}.wav"), audio, sr)
                    n_audio += 1
                    print(f"  wrote {base} {src}.wav  ({len(audio) / sr:.1f}s @ {sr}Hz)")
            print(f"\nDONE ({day_label}): {n_audio} audio files, {n_txt} transcripts -> {out}")
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
