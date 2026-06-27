"""Tests for Settings + the computed personaplex_ws_base / cors_origins properties.

Default-port elision (omit `:443` on wss, `:80` on ws) is the load-bearing behavior because PersonaPlex's own client rejects URLs with the explicit default port."""

from pathlib import Path

import pytest

from app.config import Settings, get_settings


def test_cors_origins_list_splits_csv_and_strips() -> None:
    s = Settings(cors_origins="http://a.test, http://b.test ,  http://c.test")
    assert s.cors_origins_list == ["http://a.test", "http://b.test", "http://c.test"]


def test_cors_origins_list_drops_empty_segments() -> None:
    assert Settings(cors_origins=",,http://x.test,").cors_origins_list == ["http://x.test"]


def test_personaplex_ws_base_drops_default_443_for_wss() -> None:
    s = Settings(personaplex_scheme="wss", personaplex_host="ppx.test", personaplex_port=443)
    assert s.personaplex_ws_base == "wss://ppx.test"


def test_personaplex_ws_base_drops_default_80_for_ws() -> None:
    s = Settings(personaplex_scheme="ws", personaplex_host="ppx.test", personaplex_port=80)
    assert s.personaplex_ws_base == "ws://ppx.test"


def test_personaplex_ws_base_keeps_non_default_port() -> None:
    s = Settings(personaplex_scheme="wss", personaplex_host="ppx.test", personaplex_port=8443)
    assert s.personaplex_ws_base == "wss://ppx.test:8443"


def test_personaplex_ws_url_is_alias_for_ws_base() -> None:
    s = Settings(personaplex_scheme="wss", personaplex_host="ppx.test", personaplex_port=8443)
    assert s.personaplex_ws_url == s.personaplex_ws_base


def test_apple_bundle_id_is_not_a_settings_field() -> None:
    # Bundle id is a non-secret constant (app/apple_identifiers.py), deliberately NOT env-loaded Settings.
    assert "apple_bundle_id" not in Settings.model_fields


def test_clerk_secret_key_loads_from_env_and_defaults_empty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # The Apple-signin profile backfill is gated on this key; it must map to the CLERK_SECRET_KEY env var and default empty (so an unset env skips the backfill rather than crashing). chdir to a dir without a .env so only the real env var is read.
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CLERK_SECRET_KEY", raising=False)
    assert Settings().clerk_secret_key == ""
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_abc")
    assert Settings().clerk_secret_key == "sk_test_abc"


def test_get_settings_is_cached(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # lru_cache(maxsize=1) means two calls return the same instance.
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    try:
        a = get_settings()
        b = get_settings()
        assert a is b
    finally:
        get_settings.cache_clear()
