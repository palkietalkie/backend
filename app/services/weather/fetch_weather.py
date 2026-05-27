"""Open-Meteo client. No API key required.

Returns the current temperature, weather code, and a short human label for prompt injection.
"""

from dataclasses import dataclass

import httpx
from pydantic import BaseModel, ValidationError

# Compact subset of the WMO weather codes Open-Meteo returns.
_WEATHER_CODE_LABELS: dict[int, str] = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "freezing fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    61: "light rain",
    63: "moderate rain",
    65: "heavy rain",
    71: "light snow",
    73: "moderate snow",
    75: "heavy snow",
    80: "rain showers",
    81: "heavy rain showers",
    82: "violent rain showers",
    95: "thunderstorm",
    96: "thunderstorm with hail",
    99: "severe thunderstorm with hail",
}


@dataclass(frozen=True)
class WeatherSnapshot:
    temperature_c: float
    label: str
    is_day: bool


class _CurrentBlock(BaseModel):
    temperature_2m: float
    weather_code: int = 0
    is_day: int = 1


class _ForecastResponse(BaseModel):
    current: _CurrentBlock | None = None


async def fetch_weather(lat: float, lon: float) -> WeatherSnapshot | None:
    url = "https://api.open-meteo.com/v1/forecast"
    params: dict[str, str | float] = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weather_code,is_day",
        "timezone": "auto",
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            payload = _ForecastResponse.model_validate(resp.json())
    except httpx.HTTPError, ValueError, ValidationError:
        return None

    current = payload.current
    if current is None:
        return None
    return WeatherSnapshot(
        temperature_c=current.temperature_2m,
        label=_WEATHER_CODE_LABELS.get(current.weather_code, "unknown weather"),
        is_day=bool(current.is_day),
    )
