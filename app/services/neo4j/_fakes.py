"""Shared fake driver / session / record helpers for the per-function neo4j tests."""

from collections.abc import AsyncIterator
from typing import Any


class FakeRecord:
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def __getitem__(self, key: str) -> Any:
        return self._data[key]


class FakeResult:
    def __init__(self, records: list[dict[str, Any]]) -> None:
        self._records = [FakeRecord(r) for r in records]

    def __aiter__(self) -> AsyncIterator[FakeRecord]:
        async def _gen() -> AsyncIterator[FakeRecord]:
            for r in self._records:
                yield r

        return _gen()


class FakeSession:
    def __init__(self) -> None:
        self.queries: list[tuple[str, dict[str, Any]]] = []
        self._responses: list[FakeResult] = []

    def enqueue(self, records: list[dict[str, Any]]) -> None:
        self._responses.append(FakeResult(records))

    async def run(self, query: str, **params: Any) -> FakeResult:
        self.queries.append((query, params))
        if self._responses:
            return self._responses.pop(0)
        return FakeResult([])

    async def __aenter__(self) -> FakeSession:
        return self

    async def __aexit__(self, *_exc: Any) -> None:
        return None


class FakeDriver:
    def __init__(self) -> None:
        self.fake_session = FakeSession()

    def session(self) -> FakeSession:
        return self.fake_session

    async def close(self) -> None:
        return None
