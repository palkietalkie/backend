"""Print the next TestFlight build number — one more than the highest already on App Store Connect.

Replaces release.sh's old `git rev-list --count HEAD` scheme, which jumped (1 → 26) the moment commit count diverged from upload count. Apple only requires the number to increase, but a clean +1 off the real high-water mark is easier to reason about and can't collide. ASC is the source of truth for "what's already uploaded", so derive it from there, not from git.

Run: `python -m scripts.asc.next_build_number`
"""

import httpx

from scripts.asc.find_app_id import find_app_id
from scripts.asc.get_asc_client import get_asc_client


def compute_next_build_number(versions: list[str | None]) -> int:
    """max(existing build numbers) + 1, ignoring any non-integer leftovers from older schemes. Empty (first ever upload) → 1."""
    nums: list[int] = []
    for v in versions:
        if v is None:
            continue
        try:
            nums.append(int(v))  # build numbers are plain integers under this scheme
        except ValueError:
            continue
    return max(nums) + 1 if nums else 1


def next_build_number(client: httpx.Client) -> int:
    app_id = find_app_id(client)
    # 200 is far above any realistic build count before this is revisited; all builds count toward the high-water mark, across every version string.
    r = client.get(f"/v1/builds?filter[app]={app_id}&limit=200&fields[builds]=version")
    r.raise_for_status()
    return compute_next_build_number(
        [b["attributes"].get("version") for b in r.json().get("data", [])]
    )


def main() -> None:
    with get_asc_client() as client:
        print(next_build_number(client))


if __name__ == "__main__":
    main()
