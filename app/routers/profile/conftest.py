"""Auto-stub Gemma for profile-router tests.

`fetch_profile` calls `guess_name_pronunciation` whenever the user has `display_name` set but `name_pronunciation` blank — which is the default seeded state in `app_with_overrides`. Without this autouse fixture, the basic profile tests hit the real Gemma API with the dummy `test-gemini-key` and fail with 400. Individual tests that exercise the suggestion path explicitly re-monkeypatch with their own deterministic stub.
"""

from __future__ import annotations

import pytest

import app.routers.profile.fetch_profile as fetch_profile_mod
from app.profile.languages import LanguageName


@pytest.fixture(autouse=True)
def stub_guess_name_pronunciation(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _stub(display_name: str, _language: LanguageName) -> str:
        return f"{display_name.upper()}-stub"

    monkeypatch.setattr(fetch_profile_mod, "guess_name_pronunciation", _stub)
