# /// script
# requires-python = ">=3.12"
# dependencies = ["pillow>=10"]
# ///
"""Frame the raw simulator captures into captioned App Store screenshots, into a git-tracked, dated, device-stamped dir.

Raw captures come from `ios/scripts/capture-screenshots.sh` (ephemeral, under ios/build/, gitignored). The framed output is a submission asset, so it's versioned under `scripts/asc/app_screenshots/<timestamp>_<device>/` — the dir name records WHEN and on WHICH device the set was produced, so a reviewer can tell which build a listing's screenshots came from. `upload_app_screenshots.py` uploads the newest such dir.

Run: `cd backend && uv run scripts/asc/frame_app_screenshots.py` (after capture-screenshots.sh)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.asc.constants import APP_SCREENSHOTS_DIR  # noqa: E402
from scripts.asc.frame_screenshot import frame_screenshot  # noqa: E402

# Headlines per screen (filename order = App Store display order).
CAPTIONS = {
    "01-talk": "A tutor who starts the conversation",
    "02-persona": "Pick a personality you'll love",
    "03-stats": "Watch your fluency add up",
    "04-topics": "Always something to talk about",
    "05-mistakes": "See the mistakes you keep making",
    "06-phrases": "Build a bank of natural phrases",
    "07-cefr": "Track your vocabulary by level",
    "08-profile": "An AI that remembers you",
    "09-history": "Every conversation, saved",
}
RAW_DIR = Path(__file__).resolve().parents[3] / "ios" / "build" / "screenshots" / "shots"
# 6.9" iPhone — the device the capture script targets; recorded in the output dir name.
DEVICE = "iphone-17-pro-max-6.9"


def frame_app_screenshots() -> None:
    # Device is the dir; filenames are stable (no date) and overwritten each run — git history records when each set changed, so a date in the name is redundant.
    out = APP_SCREENSHOTS_DIR / DEVICE
    out.mkdir(parents=True, exist_ok=True)
    framed = 0
    for name, caption in CAPTIONS.items():
        raw = RAW_DIR / f"{name}.png"
        if not raw.exists():
            print(f"[frame] skip {name}: no raw capture (screen not reached this run)")
            continue
        frame_screenshot(raw, caption, out / f"{name}.png")
        print(f"[frame] {DEVICE}/{name}.png")
        framed += 1
    if framed == 0:
        sys.exit("no raw captures found — run ios/scripts/capture-screenshots.sh first")
    print(f"[frame] {framed} framed in {out}")


if __name__ == "__main__":
    frame_app_screenshots()
