# /// script
# requires-python = ">=3.12"
# ///
"""Render the App Privacy declaration as a click-by-click checklist for the ASC dashboard.

Apple exposes no API for the privacy nutrition label (see `app/asc/app_privacy.py`), so this is the closest to automation possible: it reads the SSoT and prints exactly what to select under App Store Connect → App Privacy, so the one-time manual entry is a transcription with no judgment left to the moment.

Run: `cd backend && uv run scripts/asc/print_app_privacy.py`"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.asc.app_privacy import APP_PRIVACY  # noqa: E402


def print_app_privacy() -> None:
    print("App Store Connect → App Privacy. Set 'Data is collected'. Then add each row below:\n")
    for row in APP_PRIVACY:
        linked = "Linked to the user" if row.linked_to_identity else "Not linked to the user"
        tracking = "Used for tracking" if row.used_for_tracking else "Not used for tracking"
        print(f"• {row.category} → {row.data_type}")
        print(f"    Purposes: {', '.join(row.purposes)}")
        print(f"    {linked}; {tracking}")
    print(f"\n{len(APP_PRIVACY)} data types. Publish when done.")


if __name__ == "__main__":
    print_app_privacy()
