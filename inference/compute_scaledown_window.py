"""Per-environment Modal scaledown window. Read by voice_app.py at module-load time.

Anything that isn't prd ("main") gets the 2s Modal floor so dev / unknown envs default to cheap;
prd holds a 2-min warm pool so the second user in a row doesn't eat a cold start.

Bundled into the Modal container image at /root/compute_scaledown_window.py via voice_image.py.
"""

from __future__ import annotations


def compute_scaledown_window(modal_env: str | None) -> int:
    return 120 if modal_env == "main" else 2
