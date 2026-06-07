from pathlib import Path
from typing import Any

import httpx


def upload_screenshot_bytes(png: Path, operations: list[dict[str, Any]]) -> None:
    """Step 2 of Apple's 3-step screenshot upload: PUT the file bytes per `uploadOperations`.

    Apple usually returns a single operation but the contract supports many — large files get sliced into ranges and uploaded with `offset` + `length` per op, with the operation's `requestHeaders` (presigned auth, content-type) attached verbatim.
    """
    body = png.read_bytes()
    with httpx.Client(timeout=120.0) as raw:
        for op in operations:
            headers = {h["name"]: h["value"] for h in op.get("requestHeaders", [])}
            r = raw.request(
                op["method"],
                op["url"],
                headers=headers,
                content=body[op["offset"] : op["offset"] + op["length"]],
            )
            r.raise_for_status()
