"""Lock the heading auto-fit. Regression: "Individual · Monthly" rendered at a fixed font size overflowed the 1290px canvas and was clipped at the right edge. fit_font must shrink any heading until it fits within the given width."""

from PIL import Image, ImageDraw

from scripts.asc.fit_font import fit_font
from scripts.asc.load_font import load_font

WIDTH = 1098  # USABLE_WIDTH from draw_subscription_screenshot (1290 canvas − 2×96 margin).


def _draw() -> ImageDraw.ImageDraw:
    return ImageDraw.Draw(Image.new("RGB", (1290, 100)))


def test_longest_heading_fits_within_width() -> None:
    draw = _draw()
    # The widest tier-cycle combination — the one that was clipped before the fix.
    heading = "Individual · Monthly"
    font = fit_font(draw, heading, 150, WIDTH)
    assert draw.textlength(heading, font=font) <= WIDTH


def test_short_heading_keeps_max_size() -> None:
    draw = _draw()
    # A heading that already fits should not be shrunk: same rendered width as the max-size font.
    fitted = fit_font(draw, "Family", 150, WIDTH)
    at_max = load_font(150)
    assert draw.textlength("Family", font=fitted) == draw.textlength("Family", font=at_max)
