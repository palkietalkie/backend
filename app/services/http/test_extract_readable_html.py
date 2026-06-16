from app.services.http.extract_readable_html import extract_readable_html

_ARTICLE_HTML = (
    "<html><head><title>Game recap</title>"
    "<style>.byline{color:#999}</style>"
    "<script>var tracker='SECRET_TRACKER';sendBeacon();</script>"
    "</head><body>"
    "<h1>Knicks stunned the Celtics</h1>"
    "<p>Jalen Brunson dropped 39 &amp; the defense held in the 4th.</p>"
    "<script>analytics('pageview');</script>"
    "</body></html>"
)


def test_returns_readable_text_stripping_tags_scripts_styles() -> None:
    text = extract_readable_html(_ARTICLE_HTML)
    # The model must actually receive the article prose, with HTML entities decoded to real characters.
    assert "Knicks stunned the Celtics" in text
    assert "Jalen Brunson dropped 39 & the defense held in the 4th." in text
    # Script/style payloads are content poison, they must never reach the model.
    assert "SECRET_TRACKER" not in text
    assert "analytics" not in text
    assert "color:#999" not in text
    # No raw markup survives the strip.
    assert "<" not in text and ">" not in text


_PAGE_WITH_CHROME = (
    "<html><head><title>Recap</title></head><body>"
    "<header><a href='/'>HomeAboutSubscribe</a></header>"
    "<nav>Politics Business Sports Sign in</nav>"
    "<aside>RELATED: 10 things you missed. Newsletter signup.</aside>"
    "<main><article>"
    "<h1>Knicks stunned the Celtics</h1>"
    "<p>Brunson dropped 39 and the defense held in the 4th.</p>"
    "<p>The bench gave them 22 crucial points.</p>"
    "</article></main>"
    "<footer>Copyright 2026. Privacy. Terms. Cookie settings.</footer>"
    "</body></html>"
)


def test_drops_boilerplate_and_scopes_to_article() -> None:
    text = extract_readable_html(_PAGE_WITH_CHROME)
    # The article body survives.
    assert "Knicks stunned the Celtics" in text
    assert "Brunson dropped 39 and the defense held in the 4th." in text
    assert "The bench gave them 22 crucial points." in text
    # Nav / header / footer / sidebar chrome is gone, not just tag-stripped into the text.
    assert "Subscribe" not in text
    assert "Sign in" not in text
    assert "Newsletter signup" not in text
    assert "Cookie settings" not in text
    assert "Privacy" not in text


def test_keeps_longest_article_region() -> None:
    # A feed page with a teaser <article> then the real one: the real (longer) story wins, not the stub.
    body = (
        "<body><article>Teaser stub.</article>"
        "<article><p>" + ("the full report continues " * 30) + "</p></article></body>"
    )
    text = extract_readable_html(body)
    assert "the full report continues" in text
    assert "Teaser stub" not in text
