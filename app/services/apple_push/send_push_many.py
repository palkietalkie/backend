import asyncio

from app.services.apple_push.push_result import PushResult
from app.services.apple_push.send_push import send_push


async def send_push_many(
    tokens: list[str],
    title: str,
    body: str,
    badge: int | None = None,
) -> list[PushResult]:
    return list(await asyncio.gather(*(send_push(t, title, body, badge) for t in tokens)))
