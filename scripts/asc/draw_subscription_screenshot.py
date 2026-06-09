from pathlib import Path

from PIL import Image, ImageDraw

from scripts.asc.load_font import load_font

# iPhone 6.7" portrait — current top of Apple's required screenshot sizes.
W, H = 1290, 2796
BG = (16, 16, 24)
ACCENT = (124, 138, 255)
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

    draw.text((96, 320), "Palkie Talkie", fill=ACCENT, font=load_font(120))
    draw.text((96, 480), f"{tier} · {cycle}", fill=TEXT, font=load_font(150))
    draw.text((96, 700), price, fill=SECONDARY, font=load_font(96))

    y = 1080
    for b in bullets:
        draw.ellipse((96, y + 28, 144, y + 76), fill=ACCENT)
        draw.text((180, y), b, fill=TEXT, font=load_font(72))
        y += 160

    draw.text((96, H - 240), "Auto-renewable subscription.", fill=SECONDARY, font=load_font(48))
    draw.text(
        (96, H - 180),
        "Cancel anytime in App Store settings.",
        fill=SECONDARY,
        font=load_font(48),
    )

    img.save(path, format="PNG", optimize=True)
