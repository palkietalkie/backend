"""Fetch a public web page and return the readable article text for the realtime model to weave into conversation.

Best-effort: any failure (bad URL, timeout, blocked host) returns "" so a tool call never stalls the live audio. The SSRF guard (is_blocked_host) and the readability extraction (extract_readable_html) live in their own modules; this orchestrates fetch + extract.
"""

from urllib.parse import urlparse

import httpx

from app.services.http.extract_readable_html import extract_readable_html
from app.services.http.is_blocked_host import is_blocked_host


async def fetch_url_text(url: str, *, max_chars: int = 2500) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or is_blocked_host(parsed.hostname or ""):
        return ""
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (PalkieTalkie/1.0)"})
        resp.raise_for_status()
        raw = resp.text
    except Exception:
        return ""
    return extract_readable_html(raw)[:max_chars]
