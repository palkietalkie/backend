# /// script
# requires-python = ">=3.12"
# dependencies = ["pillow>=10.4"]
# ///
"""Render a 1290x2796 placeholder PNG per subscription using each product's `screenshot_bullets`.

Orchestrator only — `load_font` (font fallback) and `draw_subscription_screenshot` (the actual Pillow draw calls) are the sibling files that do the work. These PNGs are placeholders so we can finish wiring everything end-to-end; replace with real Subscription-screen captures before App Review (or accept the likely rejection and iterate).

Output: `backend/secrets/iap_screenshots/<asc_id>.png` (gitignored alongside the .p8 keys).

Run: `cd backend && uv run scripts/asc/generate_iap_screenshots.py`"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.iap.subscriptions_list import SUBSCRIPTIONS  # noqa: E402
from scripts.asc.draw_subscription_screenshot import draw_subscription_screenshot  # noqa: E402

OUT_DIR = Path(__file__).resolve().parents[2] / "secrets" / "iap_screenshots"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for s in SUBSCRIPTIONS:
        path = OUT_DIR / f"{s.asc_id}.png"
        price_label = f"${s.target_usd_price} / {s.cycle.lower()[:-2]}"
        draw_subscription_screenshot(path, s.tier, s.cycle, price_label, s.screenshot_bullets)
        print(f"[png] {path.relative_to(OUT_DIR.parents[1])} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
