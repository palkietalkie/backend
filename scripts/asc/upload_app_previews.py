# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.28", "pyjwt[crypto]>=2.9"]
# ///
"""Upload the App Preview video(s) in scripts/asc/app_previews/ to the en-US version listing.

Apple's 6.9"/6.7" iPhone preview slot is `IPHONE_67` (it accepts our 1320x2868 H.264 capture). For each .mp4 (filename order = display order) we run Apple's 3-step asset upload: reserve -> PUT bytes -> commit with md5. Idempotent: existing previews in the set are deleted first, so a re-run replaces rather than appends. Apple then transcodes asynchronously — the asset shows as processing in App Store Connect for a few minutes after this exits.

Produce the .mp4 first: `ios/scripts/capture-screenshots.sh` records `ios/build/screenshots/preview-raw.mov` (video-only — the sim records no audio). Apple's transcoder REJECTS an audio-less or mono preview with `MOV_RESAVE_STEREO`, so the trim MUST mux in a stereo track. Trim a 15-30s segment into `app_previews/<device>/` with a silent stereo track:

    ffmpeg -ss <start> -i preview-raw.mov -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 \\
      -t <dur> -map 0:v:0 -map 1:a:0 -c:v libx264 -pix_fmt yuv420p -r 30 -c:a aac -shortest \\
      -movflags +faststart app_previews/<device>/preview.mp4

Run: `cd backend && uv run scripts/asc/upload_app_previews.py`"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.asc.commit_app_preview import commit_app_preview  # noqa: E402
from scripts.asc.constants import APP_PREVIEWS_DIR  # noqa: E402
from scripts.asc.find_app_id import find_app_id  # noqa: E402
from scripts.asc.find_editable_version_localization import (  # noqa: E402
    find_editable_version_localization,
)
from scripts.asc.find_or_create_app_preview_set import (  # noqa: E402
    find_or_create_app_preview_set,
)
from scripts.asc.get_asc_client import get_asc_client  # noqa: E402
from scripts.asc.reserve_app_preview import reserve_app_preview  # noqa: E402
from scripts.asc.upload_asset_bytes import upload_asset_bytes  # noqa: E402

# Apple's 6.9"/6.7" iPhone preview slot; accepts 1320x2868.
PREVIEW_TYPE = "IPHONE_67"
LOCALE = "en-US"


def upload_app_previews() -> None:
    # Filenames are stable (overwritten each run); upload the current set in name order.
    videos = sorted(APP_PREVIEWS_DIR.rglob("*.mp4"))
    if not videos:
        sys.exit(
            f"no previews in {APP_PREVIEWS_DIR} — record capture-screenshots.sh then trim a clip into <device>/"
        )
    print(f"[asc] uploading {len(videos)} preview(s)")
    with get_asc_client() as client:
        app_id = find_app_id(client)
        loc = find_editable_version_localization(client, app_id, LOCALE)
        if loc is None:
            sys.exit(
                f"no editable {LOCALE} version localization (is a version in PREPARE_FOR_SUBMISSION?)"
            )
        set_id = find_or_create_app_preview_set(client, str(loc["id"]), PREVIEW_TYPE)

        # Clear existing so a re-run replaces rather than appends.
        existing = client.get(f"/v1/appPreviewSets/{set_id}/appPreviews?limit=50")
        existing.raise_for_status()
        for row in existing.json().get("data", []):
            client.delete(f"/v1/appPreviews/{row['id']}").raise_for_status()

        for video in videos:
            asset = reserve_app_preview(client, set_id, video)
            upload_asset_bytes(video, asset["attributes"]["uploadOperations"])
            commit_app_preview(client, str(asset["id"]), video)
            print(f"[asc] uploaded {video.name}")
    print(f"[asc] {len(videos)} preview(s) uploaded to {PREVIEW_TYPE} (Apple now transcodes async)")


if __name__ == "__main__":
    upload_app_previews()
