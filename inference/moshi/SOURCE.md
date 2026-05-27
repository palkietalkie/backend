# Vendored: NVIDIA/personaplex/moshi

Upstream: https://github.com/NVIDIA/personaplex
Branch: main
Commit: 3428dfd95309a7f3c84fd93259ded0f810d1ff91
Date: 2026-03-02
License: MIT (see LICENSE.moshi, LICENSE.audiocraft)

Only the inner `moshi/` Python package is vendored — upstream's `client/` (web reference) and `Dockerfile` (local-GPU reference) aren't used; Palkie Talkie ships its own iOS client and Modal image. Upstream's `pyproject.toml` / `MANIFEST.in` / `setup.cfg` are also dropped: deps are listed explicitly in `inference/voice_image.py` and the package is dropped into `/root/moshi/` directly (no `uv pip install` of a local distribution).

## Why vendored

Upstream is not actively maintained (~22 commits total, all in release week Jan 2026, last code change Jan 24, 2026, last commit a README fix Mar 2, 2026). We need to modify `server.py` for audio loudness, lifecycle, and error surfacing. Vendoring makes those modifications normal git diffs in this repo.

## Local modifications

All edits live as ordinary git diffs against the upstream snapshot:

- Strip module-level `with torch.no_grad(): main()` (caused double-server boot on import).
- `opus_loop`: tolerate `pcm is None` from sphn before checking shape.
- `opus_loop`: wrap `main_pcm[0,0]` with `palkie_loudness(...)` and `.detach().numpy()`.
- Append `palkie_loudness` helper + constants (PALKIE_TARGET_PEAK=0.85, PALKIE_MAX_GAIN=8.0, PALKIE_CEILING=0.95) at module bottom.
- Wrap `opus_reader.append_bytes(payload)` in try/except to surface decode errors.
- `opus_loop`: inactivity timeout — close WS after PALKIE_INACTIVITY_TIMEOUT_S (60s) without any PCM chunk exceeding PALKIE_VOICE_RMS_THRESHOLD (0.01). Stops the A100 from billing through "mic on, user backgrounded the app" cases that left dev sessions running 8-12 min.
- Reflow upstream MIT license header (NVIDIA + Kyutai) to one-sentence-per-line to satisfy our hard-wrap-comment linter. Text is verbatim; only line breaks changed.

## Re-syncing from upstream

```bash
# 1. Fetch upstream
cd /tmp && git clone https://github.com/NVIDIA/personaplex.git
# 2. Diff our copy against the new upstream
diff -r /tmp/personaplex/moshi backend/inference/moshi
# 3. Merge changes by hand; update Commit + Date above
# 4. If upstream's pyproject.toml changed deps, mirror the change in backend/inference/voice_image.py
```
