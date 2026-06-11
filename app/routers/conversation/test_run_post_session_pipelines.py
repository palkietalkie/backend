"""Tests for run_post_session_pipelines — verify failure isolation."""

import logging
import uuid

import pytest

from app.routers.conversation import run_post_session_pipelines as mod


async def test_failing_pipeline_logs_but_keeps_going(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    calls: list[str] = []

    async def _ok(_session: uuid.UUID, _user: uuid.UUID, _db: object) -> int:
        calls.append("ok")
        return 0

    async def _boom(_session: uuid.UUID, _user: uuid.UUID, _db: object) -> int:
        calls.append("boom")
        raise RuntimeError("kg upstream down")

    # Stub the four pipelines + the pool acquirer.
    monkeypatch.setattr(mod, "run_transcript_analysis", _ok)
    monkeypatch.setattr(mod, "run_phrase_extraction", _ok)
    monkeypatch.setattr(mod, "run_mistake_detection", _boom)
    monkeypatch.setattr(mod, "run_kg_extraction", _ok)

    class _FakePoolCtx:
        async def __aenter__(self) -> object:
            return object()

        async def __aexit__(self, *_exc: object) -> None:
            return None

    class _FakePool:
        def acquire(self) -> _FakePoolCtx:
            return _FakePoolCtx()

    async def _get_neon_pool() -> _FakePool:
        return _FakePool()

    monkeypatch.setattr(mod, "get_neon_pool", _get_neon_pool)
    with caplog.at_level(logging.ERROR):
        await mod.run_post_session_pipelines(uuid.uuid4(), uuid.uuid4())

    assert calls == ["ok", "ok", "boom", "ok"]
    assert any(
        "post-session pipeline mistake_detection failed" in rec.message for rec in caplog.records
    )
