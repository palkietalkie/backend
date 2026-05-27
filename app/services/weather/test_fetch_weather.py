"""Open-Meteo client tests. httpx is mocked via respx."""

import httpx
import respx

from app.services.weather.fetch_weather import fetch_weather

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


@respx.mock
async def test_fetch_weather_happy_path() -> None:
    respx.get(OPEN_METEO_URL).mock(
        return_value=httpx.Response(
            200,
            json={"current": {"temperature_2m": 18.3, "weather_code": 3, "is_day": 1}},
        )
    )
    snap = await fetch_weather(37.7749, -122.4194)
    assert snap is not None
    assert snap.temperature_c == 18.3
    assert snap.label == "overcast"
    assert snap.is_day is True


@respx.mock
async def test_fetch_weather_unknown_code_falls_back_to_label() -> None:
    respx.get(OPEN_METEO_URL).mock(
        return_value=httpx.Response(
            200,
            json={"current": {"temperature_2m": 7.0, "weather_code": 999, "is_day": 0}},
        )
    )
    snap = await fetch_weather(0.0, 0.0)
    assert snap is not None
    assert snap.label == "unknown weather"
    assert snap.is_day is False


@respx.mock
async def test_fetch_weather_returns_none_when_current_missing() -> None:
    respx.get(OPEN_METEO_URL).mock(return_value=httpx.Response(200, json={}))
    assert await fetch_weather(0.0, 0.0) is None


@respx.mock
async def test_fetch_weather_returns_none_on_validation_error() -> None:
    # `temperature_2m` missing from the inner block — Pydantic rejects, caller gets None.
    respx.get(OPEN_METEO_URL).mock(
        return_value=httpx.Response(200, json={"current": {"is_day": 1}})
    )
    assert await fetch_weather(0.0, 0.0) is None


@respx.mock
async def test_fetch_weather_returns_none_on_http_error() -> None:
    respx.get(OPEN_METEO_URL).mock(return_value=httpx.Response(503, text="upstream down"))
    assert await fetch_weather(0.0, 0.0) is None
