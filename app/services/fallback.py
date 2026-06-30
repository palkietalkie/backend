"""Decorator that makes a non-critical enrichment function degrade to a default instead of failing.

KG, calendar, and last-session recall are *context* for the conversation-start prompt — nice to have, never load-bearing. "Return the data, or this fallback value if the source is unavailable" is each function's own contract, so the resilience lives on the function (one decorator) rather than at every call site. On a timeout or any error the wrapped function logs and returns `default`, so a failure or a slow/dead dependency (e.g. a defunct AuraDB connection) degrades to "no context" instead of 500ing or hanging the Talk View.
"""

import asyncio
import functools
import logging
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)

# These run on the conversation-start critical path the iOS client blocks on (15s budget). A healthy enrichment returns in well under a second; this cap only bites when a source is slow or dead, and is short enough that even several degrading in series stay under the client budget.
_DEFAULT_TIMEOUT_SECONDS = 3.0


def fallback[T, D, **P](
    *, default: D, timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T | D]]]:
    # Two type vars on purpose: T is the wrapped function's normal return (inferred when the decorator is applied), D is the fallback's type (inferred from `default`). Keeping them separate stops pyright from pinning the return type to the default — e.g. default=None must not collapse a `str | None` function to `None`. The wrapped result is T | D: the real value, or the default on failure.
    def decorate(fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T | D]]:
        @functools.wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | D:
            try:
                async with asyncio.timeout(timeout_seconds):
                    return await fn(*args, **kwargs)
            except Exception as exc:
                # Broad on purpose: any failure is non-fatal. CancelledError is a BaseException, so genuine request cancellation still propagates rather than being mistaken for a dependency failure.
                logger.warning(
                    "%s degraded to fallback (%s): %r", fn.__name__, type(exc).__name__, exc
                )
                return default

        return wrapper

    return decorate
