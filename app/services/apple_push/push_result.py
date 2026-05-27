from dataclasses import dataclass


@dataclass(frozen=True)
class PushResult:
    token: str
    ok: bool
    reason: str | None = None
