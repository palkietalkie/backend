"""Print TestFlight tester bug reports (beta feedback) for the Palkie Talkie app.

Testers submit feedback from inside the TestFlight app: a screenshot + comment, or a crash with an optional note. Apple lists these off the APP relationship (the top-level collection and the per-build relationship both reject the request), so this reads both feedback kinds and prints each submission: build, device/OS, the comment, and the screenshot URL. Apple anonymizes the tester on feedback, so there's no name to show.

Run: cd backend && uv run python -m scripts.asc.fetch_testflight_feedback
(ASC key id / issuer id are constants in scripts/asc/constants.py; the only secret is the .p8 at backend/secrets/apple_asc_api.p8.)
"""

import httpx
from pydantic import BaseModel, Field

from scripts.asc.constants import APP_ID
from scripts.asc.get_asc_client import get_asc_client

_FEEDBACK_KINDS = (
    ("betaFeedbackScreenshotSubmissions", "feedback"),
    ("betaFeedbackCrashSubmissions", "crash"),
)


class _ImageAsset(BaseModel):
    template_url: str | None = Field(default=None, alias="templateUrl")


class _Screenshot(BaseModel):
    image_asset: _ImageAsset | None = Field(default=None, alias="imageAsset")
    url: str | None = None


class Attrs(BaseModel):
    created_date: str | None = Field(default=None, alias="createdDate")
    device_model: str | None = Field(default=None, alias="deviceModel")
    os_version: str | None = Field(default=None, alias="osVersion")
    comment: str | None = None
    feedback_text: str | None = Field(default=None, alias="feedbackText")
    screenshots: list[_Screenshot] = []


class _RelData(BaseModel):
    id: str | None = None


class _BuildRel(BaseModel):
    data: _RelData | None = None


class _Relationships(BaseModel):
    build: _BuildRel | None = None


class Submission(BaseModel):
    id: str
    attributes: Attrs = Field(default_factory=Attrs)
    relationships: _Relationships | None = None


class _BuildAttrs(BaseModel):
    version: str | None = None


class _Included(BaseModel):
    id: str
    type: str
    attributes: _BuildAttrs = Field(default_factory=_BuildAttrs)


class _Response(BaseModel):
    data: list[Submission] = []
    included: list[_Included] = []


class _CrashLogAttrs(BaseModel):
    log_text: str | None = Field(default=None, alias="logText")


class _CrashLogData(BaseModel):
    attributes: _CrashLogAttrs = Field(default_factory=_CrashLogAttrs)


class _CrashLogResponse(BaseModel):
    data: _CrashLogData = Field(default_factory=_CrashLogData)


def build_version_of(submission: Submission, versions: dict[str, str | None]) -> str:
    rel = submission.relationships
    build_id = rel.build.data.id if rel and rel.build and rel.build.data else None
    return versions.get(build_id or "") or "?"


def fetch_crash_log_lines(client: httpx.Client, submission_id: str) -> list[str]:
    resp = client.get(f"/v1/betaFeedbackCrashSubmissions/{submission_id}/crashLog")
    if resp.status_code != 200:
        return []
    log = _CrashLogResponse.model_validate(resp.json())
    return summarize_crash_log(log.data.attributes.log_text or "")


def summarize_crash_log(log_text: str) -> list[str]:
    # The full symbolicated log runs ~200 lines; surface only what locates the bug: the exception/termination lines and our own (PalkieTalkie) stack frames, which name the file + line that threw.
    lines: list[str] = []
    for line in log_text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("Exception Type:", "Termination Reason:", "Triggered by Thread:")):
            lines.append(stripped)
    app_frames = [
        line.strip()
        for line in log_text.splitlines()
        if "PalkieTalkie" in line and ".swift:" in line
    ]
    # The first app frame in the exception backtrace is the throw site; a couple more give the call path.
    seen: set[str] = set()
    for frame in app_frames:
        signature = frame.split("0x")[-1]
        if signature in seen:
            continue
        seen.add(signature)
        lines.append(frame)
        if len(seen) >= 4:
            break
    return lines


def fetch_testflight_feedback() -> None:
    with get_asc_client() as client:
        for kind, label in _FEEDBACK_KINDS:
            resp = client.get(
                f"/v1/apps/{APP_ID}/{kind}",
                params={"include": "build", "sort": "-createdDate", "limit": "100"},
            )
            if resp.status_code != 200:
                print(f"{kind}: HTTP {resp.status_code}: {resp.text[:200]}")
                continue
            parsed = _Response.model_validate(resp.json())
            versions = {
                inc.id: inc.attributes.version for inc in parsed.included if inc.type == "builds"
            }
            print(f"=== {label}: {len(parsed.data)} ===")
            for sub in parsed.data:
                a = sub.attributes
                version = build_version_of(sub, versions)
                print(
                    f"[{label}] build {version} | {(a.created_date or '')[:16]} | "
                    f"{a.device_model} iOS {a.os_version}"
                )
                comment = a.comment or a.feedback_text
                if comment:
                    print(f"    {comment}")
                for shot in a.screenshots:
                    url = (shot.image_asset.template_url if shot.image_asset else None) or shot.url
                    if url:
                        print(f"    screenshot: {url}")
                if label == "crash":
                    for summary_line in fetch_crash_log_lines(client, sub.id):
                        print(f"    {summary_line}")


if __name__ == "__main__":
    fetch_testflight_feedback()
