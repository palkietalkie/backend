"""Pull the readable ARTICLE text out of raw HTML.

Dependency-light on purpose: the project ships only httpx (no bs4/trafilatura), so a readability heuristic in stdlib regex does the boilerplate removal a proper extractor would: drop non-content blocks (scripts, nav, header, footer, sidebars, forms), scope to the page's <article>/<main> region when it marks one, then strip the remaining tags. Far less menu/ad/cookie-banner noise than a blind tag-strip.
"""

import html
import re

# Blocks whose INNER TEXT is chrome, not article content: remove tag + contents outright.
_DROP_BLOCKS = re.compile(
    r"<(script|style|noscript|template|nav|header|footer|aside|form|figure|svg)\b[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)
# The semantic main-content region. A page may mark several (teaser <article>s in a feed); we keep the longest.
_MAIN_REGION = re.compile(r"<(article|main)\b[^>]*>(.*?)</\1>", re.IGNORECASE | re.DOTALL)
_TAGS = re.compile(r"<[^>]+>")
_INLINE_WS = re.compile(r"[ \t\r\f\v]+")
_BLANK_LINES = re.compile(r"\n\s*\n+")


def extract_readable_html(raw: str) -> str:
    body = _DROP_BLOCKS.sub(" ", raw)
    # Prefer the marked article/main region. Longest match wins so a feed of teaser <article>s yields the real story, not the first stub.
    regions = [m.group(2) for m in _MAIN_REGION.finditer(body)]
    if regions:
        body = max(regions, key=len)
    text = _TAGS.sub(" ", body)
    text = html.unescape(text)
    text = _INLINE_WS.sub(" ", text)
    return _BLANK_LINES.sub("\n\n", text).strip()
