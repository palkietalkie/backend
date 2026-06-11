"""Print a diagnostic dump of a session's recorded audio: peak / RMS, per-second strip chart, and a WAV written to /tmp.

Use to confirm whether the iOS mic captured real user speech or only the AI's own speaker bleed (failed AEC produces a continuous loud track during stretches the user was silent).

Run: `cd backend && uv run scripts/neon/dump_session_audio.py [session_id] [--model]`. With no session id, picks the latest session. `--model` pulls the AI's raw PCM16 output (the audio that arrived from OpenAI Realtime BEFORE iOS playback DSP touched it) instead of the mic recording.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402

from app.services.neon.get_neon_pool import get_neon_pool  # noqa: E402
from scripts.neon.decode_audio_bytes import decode_audio_bytes  # noqa: E402
from scripts.neon.fetch_latest_session import fetch_latest_session  # noqa: E402
from scripts.neon.fetch_session_audio import fetch_session_audio  # noqa: E402
from scripts.neon.print_rms_track import print_rms_track  # noqa: E402


async def main() -> None:
    args = [a for a in sys.argv[1:] if a not in ("--model",)]
    source = "model" if "--model" in sys.argv else "mic"
    pool = await get_neon_pool()
    async with pool.acquire() as db:
        if args:
            session_id = uuid.UUID(args[0])
            print(f"session: {session_id} source={source} (from CLI arg)")
        else:
            s = await fetch_latest_session(db)
            if s is None:
                sys.exit("no conversation_sessions rows")
            session_id = s["id"]
            print(
                f"session: {session_id} source={source} started={s['started_at']} dur={s['duration_seconds']}s (latest)"
            )

        row = await fetch_session_audio(db, session_id, source=source)
        if row is None:
            sys.exit(f"no {source} audio for session {session_id}")
        raw, format_label = row
        print(f"format claimed: {format_label}  bytes_stored={len(raw)}")
        print(f"first 8 bytes:  {raw[:8].hex()}")

        audio, sr = decode_audio_bytes(raw)
        dur = len(audio) / sr
        peak = float(np.max(np.abs(audio)))
        rms = float(np.sqrt((audio**2).mean()))
        print(
            f"\ndecoded: sr={sr}Hz dur={dur:.2f}s samples={len(audio)}  "
            f"peak={20 * np.log10(peak + 1e-12):.1f} dB  rms={20 * np.log10(rms + 1e-12):.1f} dB"
        )

        out = Path(f"/tmp/session_{session_id}_{source}.wav")  # noqa: S108 — dev-only diagnostic dump, not production code
        sf.write(out, (audio * 32767).astype(np.int16), sr, format="WAV", subtype="PCM_16")
        print(f"wrote {out}")

        print_rms_track(audio, sr)


if __name__ == "__main__":
    asyncio.run(main())
