"""Print the TestFlight build + beta-review status for the Palkie Talkie app.

Run: cd backend && uv run python -m scripts.asc.fetch_build_status
(The ASC key id / issuer id are constants in scripts/asc/constants.py; the only secret is the .p8 at backend/secrets/apple_asc_api.p8.)
"""

from typing import Any

from scripts.asc.constants import APP_ID
from scripts.asc.get_asc_client import get_asc_client


def fetch_build_status() -> None:
    with get_asc_client() as client:
        resp = client.get(
            "/v1/builds",
            params={
                "filter[app]": APP_ID,
                "include": "betaAppReviewSubmission",
                "sort": "-version",
                "limit": "5",
            },
        )
        resp.raise_for_status()
        body = resp.json()
        review_states = {
            item["id"]: item["attributes"].get("betaReviewState")
            for item in body.get("included", [])
            if item["type"] == "betaAppReviewSubmissions"
        }
        for build in body["data"]:
            attrs: dict[str, Any] = build["attributes"]
            relationships: dict[str, Any] = build.get("relationships", {})
            submission: dict[str, Any] = relationships.get("betaAppReviewSubmission") or {}
            rel: dict[str, Any] | None = submission.get("data")
            review = review_states.get(rel["id"]) if rel else "not submitted"
            print(
                f"build {attrs.get('version')} | processing: {attrs.get('processingState')} | "
                f"beta review: {review}"
            )


if __name__ == "__main__":
    fetch_build_status()
