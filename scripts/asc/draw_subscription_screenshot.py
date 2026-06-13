from pathlib import Path

from PIL import Image, ImageDraw

from scripts.asc.fit_font import fit_font
from scripts.asc.load_font import load_font

# iPhone 6.7" portrait — current top of Apple's required screenshot sizes.
W, H = 1290, 2796
MARGIN = 96
USABLE_WIDTH = W - 2 * MARGIN
BG = (16, 16, 24)
# BrandCoral — the app's accent (ios Assets.xcassets/BrandCoral.colorset, sRGB 1.0/0.420/0.278).
ACCENT = (255, 107, 71)
TEXT = (240, 240, 245)
SECONDARY = (170, 175, 195)


def draw_subscription_screenshot(
    path: Path, tier: str, cycle: str, price: str, bullets: tuple[str, ...]
) -> None:
    """Render a single 1290x2796 placeholder PNG for one subscription.

    Layout: brand wordmark at top, `Tier · Cycle` heading, price line, bullet list with accent dots, "Auto-renewable" + "Cancel anytime" footnotes. Colors are flat hex (not Apple HIG) — these are placeholders so we can satisfy ASC's "screenshot required" check; real screenshots from the iOS simulator will replace them before App Review.
    """
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    heading = f"{tier} · {cycle}"
    draw.text((MARGIN, 320), "Palkie Talkie", fill=ACCENT, font=load_font(120))
    draw.text((MARGIN, 480), heading, fill=TEXT, font=fit_font(draw, heading, 150, USABLE_WIDTH))
    draw.text((MARGIN, 700), price, fill=SECONDARY, font=load_font(96))

    y = 1080
    for b in bullets:
        draw.ellipse((MARGIN, y + 28, 144, y + 76), fill=ACCENT)
        draw.text((180, y), b, fill=TEXT, font=fit_font(draw, b, 72, USABLE_WIDTH))
        y += 160

    draw.text((MARGIN, H - 240), "Auto-renewable subscription.", fill=SECONDARY, font=load_font(48))
    draw.text(
        (MARGIN, H - 180),
        "Cancel anytime in App Store settings.",
        fill=SECONDARY,
        font=load_font(48),
    )

    img.save(path, format="PNG", optimize=True)
