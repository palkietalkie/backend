"""Local stub for neo4j 6.x.

The upstream lib's ``AsyncDriver.session`` and ``AsyncGraphDatabase.driver`` use a runtime fallback signature with ``**config`` typed as Unknown when pyright doesn't follow the TYPE_CHECKING branch through the lib's re-exports. We narrow the surface to the methods this codebase actually calls so pyright sees fully typed signatures.

Only the surface this codebase touches is modeled — extend when new calls land.
"""

from collections.abc import AsyncIterator
from types import TracebackType
from typing import Any

class Record:
    def __getitem__(self, key: str) -> Any: ...
    def get(self, key: str, default: Any = ...) -> Any: ...
    def keys(self) -> list[str]: ...

class AsyncResult:
    def __aiter__(self) -> AsyncIterator[Record]: ...
    async def consume(self) -> Any: ...

class AsyncTransaction:
    async def run(self, query: str, /, **kwargs: Any) -> AsyncResult: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...

class AsyncSession:
    async def __aenter__(self) -> AsyncSession: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...
    async def run(self, query: str, /, **kwargs: Any) -> AsyncResult: ...
    async def close(self) -> None: ...

class AsyncDriver:
    def session(self) -> AsyncSession: ...
    async def close(self) -> None: ...
    async def verify_connectivity(self) -> None: ...

class AsyncGraphDatabase:
    @staticmethod
    def driver(
        uri: str,
        *,
        auth: tuple[str, str] | None = ...,
        liveness_check_timeout: float = ...,
        max_connection_lifetime: float = ...,
        connection_acquisition_timeout: float = ...,
    ) -> AsyncDriver: ...

class Auth:
    def __init__(self, scheme: str, principal: str, credentials: str) -> None: ...

# Re-export commonly-imported names so user-code's `from neo4j import X` continues to resolve.
__all__ = [
    "AsyncDriver",
    "AsyncGraphDatabase",
    "AsyncResult",
    "AsyncSession",
    "AsyncTransaction",
    "Auth",
    "Record",
]
