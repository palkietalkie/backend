"""Submit an uploaded build for external TestFlight (Beta App) Review — the resubmit step `release.sh` does NOT do.

`release.sh` only uploads the .ipa; getting it in front of external reviewers/testers is three more ASC calls (add to the external group, then create the review submission). This script is that step, idempotent enough to re-run: it picks the build (newest VALID, or `--version N`), adds it to every external beta group, and submits it for review, treating an already-submitted build as success rather than an error.

Run: `python -m scripts.asc.submit_build_for_beta_review [--version 26]`
"""

import argparse
import sys
from typing import Any

import httpx

from scripts.asc.find_app_id import find_app_id
from scripts.asc.get_asc_client import get_asc_client


def select_build(builds: list[dict[str, Any]], version: str | None) -> dict[str, Any]:
    """Pick the build to submit: the requested `--version`, else the newest one Apple has finished processing (state VALID). A build that isn't VALID yet can't be submitted, so it's never a candidate."""
    valid = [b for b in builds if b["attributes"].get("processingState") == "VALID"]
    if version is not None:
        match = [b for b in valid if b["attributes"].get("version") == version]
        if not match:
            sys.exit(
                f"FAIL: build {version} not found in a VALID (processed) state. Available VALID: {[b['attributes']['version'] for b in valid] or 'none'}"
            )
        return match[0]
    if not valid:
        sys.exit("FAIL: no VALID build to submit — wait for Apple processing to finish.")
    # builds come back newest-first (sort=-uploadedDate), so the first VALID is the latest.
    return valid[0]


def submit_build_for_beta_review(client: httpx.Client, *, version: str | None = None) -> None:
    app_id = find_app_id(client)

    builds = client.get(
        f"/v1/builds?filter[app]={app_id}&sort=-uploadedDate&limit=20"
        "&fields[builds]=version,processingState",
    )
    builds.raise_for_status()
    build = select_build(builds.json().get("data", []), version)
    build_id, build_version = build["id"], build["attributes"]["version"]
    print(f"[submit] build 1.0({build_version}) ({build_id})")

    groups = client.get(f"/v1/apps/{app_id}/betaGroups?fields[betaGroups]=name,isInternalGroup")
    groups.raise_for_status()
    external = [
        g for g in groups.json().get("data", []) if not g["attributes"].get("isInternalGroup")
    ]
    if not external:
        sys.exit("FAIL: no external beta group exists — create one in TestFlight first.")
    for g in external:
        # Adding an already-present build returns 204 too, so this is safe to re-run.
        r = client.post(
            f"/v1/betaGroups/{g['id']}/relationships/builds",
            json={"data": [{"type": "builds", "id": build_id}]},
        )
        r.raise_for_status()
        print(f"[submit] added to external group {g['attributes']['name']!r}")

    # Check for an existing submission first: re-submitting a build that's already submitted/in-review/approved returns an opaque 422 (INVALID_QC_STATE), so detect the real "already done" case up front rather than guessing from the error.
    existing = client.get(
        f"/v1/builds/{build_id}/betaAppReviewSubmission"
        "?fields[betaAppReviewSubmissions]=betaReviewState",
    )
    existing.raise_for_status()
    prior = existing.json().get("data")
    if prior:
        print(
            f"[submit] build 1.0({build_version}) already in beta review: {prior['attributes'].get('betaReviewState')} — nothing to do."
        )
        return

    r = client.post(
        "/v1/betaAppReviewSubmissions",
        json={
            "data": {
                "type": "betaAppReviewSubmissions",
                "relationships": {"build": {"data": {"type": "builds", "id": build_id}}},
            }
        },
    )
    r.raise_for_status()
    state = r.json().get("data", {}).get("attributes", {}).get("betaReviewState")
    print(f"[submit] submitted for Beta App Review → {state}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version", default=None, help="build number to submit (default: newest VALID)"
    )
    args = parser.parse_args()
    with get_asc_client() as client:
        submit_build_for_beta_review(client, version=args.version)


if __name__ == "__main__":
    main()
