"""fetch_url_text orchestration: scheme/host short-circuit, HTTP errors, truncation, and live real-page fetches.

The pure HTML extraction is covered in test_extract_readable_html; the SSRF host check in test_is_blocked_host.
"""

import httpx
import pytest

from app.services.http.fetch_url_text import fetch_url_text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    ["ftp://example.com/x", "http://localhost/x", "http://127.0.0.1/admin", "file:///etc/passwd"],
)
async def test_unsafe_urls_return_empty_without_fetching(url: str) -> None:
    # Blocked scheme/host returns "" before any httpx call (no network needed).
    assert await fetch_url_text(url) == ""


def _install_fake_fetch(monkeypatch: pytest.MonkeyPatch, *, body: str, status: int = 200) -> None:
    # fetch_url_text builds its own httpx.AsyncClient with no injectable transport, so swap the class for a fake that returns canned HTML without a network call.
    class _FakeClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        async def __aenter__(self) -> _FakeClient:
            return self

        async def __aexit__(self, *exc: object) -> bool:
            return False

        async def get(self, url: str, headers: dict[str, str] | None = None) -> httpx.Response:
            return httpx.Response(status, text=body, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "AsyncClient", _FakeClient)


@pytest.mark.asyncio
async def test_truncates_to_max_chars(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_fetch(monkeypatch, body="<p>" + ("word " * 5000) + "</p>")
    text = await fetch_url_text("https://news.example.com/long", max_chars=300)
    assert len(text) == 300


@pytest.mark.asyncio
async def test_http_error_status_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    # A 5xx raises in raise_for_status, gets caught, and returns "" so a tool call never stalls live audio.
    _install_fake_fetch(monkeypatch, body="<p>nope</p>", status=500)
    assert await fetch_url_text("https://news.example.com/err") == ""


# Live pages across several real sites (not a toy placeholder): an encyclopedia article and real news. Each skips (not fails) if unreachable/bot-blocked so CI stays deterministic. keyword is asserted where the page's content is stable.
_REAL_PAGES = [
    ("https://en.wikipedia.org/wiki/Espresso", "espresso"),
    ("https://en.wikipedia.org/wiki/Mount_Fuji", "fuji"),
    ("https://www.bbc.com/news", None),
    ("https://apnews.com/hub/business", None),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("url,keyword", _REAL_PAGES)
async def test_real_pages_extract_substantial_text(url: str, keyword: str | None) -> None:
    text = await fetch_url_text(url, max_chars=8000)
    if len(text) < 300:
        pytest.skip(f"unreachable or bot-blocked: {url} ({len(text)} chars)")
    if keyword is not None:
        assert keyword in text.lower()


@pytest.mark.asyncio
async def test_real_wikipedia_strips_site_chrome() -> None:
    text = await fetch_url_text("https://en.wikipedia.org/wiki/Espresso", max_chars=8000)
    if len(text) < 300:
        pytest.skip("wikipedia unreachable")
    # Heavy site chrome must NOT leak into the model's context.
    for chrome in ("Jump to content", "Main menu", "Personal tools", "Log in", "Privacy policy"):
        assert chrome not in text, f"chrome leaked: {chrome}"
