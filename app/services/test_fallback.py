import asyncio

from app.services.fallback import fallback


async def test_returns_value_on_success() -> None:
    @fallback(default=0)
    async def ok() -> int:
        return 42

    assert await ok() == 42


async def test_returns_default_on_error() -> None:
    @fallback(default=-1)
    async def boom() -> int:
        raise RuntimeError("dependency down")

    # Any failure degrades to the default instead of propagating (which would 500 conversation start).
    assert await boom() == -1


async def test_returns_default_on_timeout() -> None:
    @fallback(default=99, timeout_seconds=0.05)
    async def hang() -> int:
        await asyncio.sleep(5)
        return 1

    # A slow/dead dependency (e.g. a defunct AuraDB connection) must be bounded so it can't hang the request past the client budget; the decorator returns the default at the timeout.
    assert await hang() == 99


async def test_cancellation_is_not_swallowed() -> None:
    # CancelledError is a BaseException, so genuine request cancellation must propagate, not be caught and turned into the default.
    @fallback(default=0)
    async def cancel_me() -> int:
        raise asyncio.CancelledError

    try:
        await cancel_me()
    except asyncio.CancelledError:
        return
    raise AssertionError("CancelledError was swallowed")


async def test_none_default_does_not_collapse_optional_return() -> None:
    # default=None must keep a `str | None` function returning its real value on success (the separate D type var, not pinning the return to None); success returns the string, failure the None default.
    @fallback(default=None)
    async def maybe(boom: bool) -> str | None:
        if boom:
            raise RuntimeError
        return "x"

    assert await maybe(False) == "x"
    assert await maybe(True) is None
