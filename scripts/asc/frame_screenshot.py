from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from scripts.asc.fit_font import fit_font

# iPhone 6.9" portrait — Apple's required screenshot size; raw simulator captures are already this.
W, H = 1320, 2868
MARGIN = 96
# BrandCoral accent + dark canvas, matching draw_subscription_screenshot.py so the whole listing reads as one set.
BG = (16, 16, 24)
ACCENT = (255, 107, 71)
TEXT = (240, 240, 245)
# The framed device capture sits just below the headline + rule (no big empty band between them).
CAPTION_TOP = 150
DEVICE_TOP = 410
DEVICE_WIDTH = 1080
CORNER_RADIUS = 56


def _round_corners(shot: Image.Image, radius: int) -> Image.Image:
    """Apply rounded corners so the inset capture reads as a device, not a pasted rectangle."""
    mask = Image.new("L", shot.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, shot.width, shot.height), radius, fill=255)
    shot.putalpha(mask)
    return shot


def frame_screenshot(raw_png: Path, caption: str, out_png: Path) -> None:
    """Composite a raw 1320x2868 device capture into a captioned marketing frame of the same size.

    A two-line headline sits at the top on the brand-dark canvas; the capture is scaled to DEVICE_WIDTH, rounded, given a soft drop shadow, and centered below. Same canvas + accent as the IAP screenshots so the App Store listing looks like one designed set.
    """
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)

    font = fit_font(draw, caption, 92, W - 2 * MARGIN)
    draw.text((W // 2, CAPTION_TOP), caption, fill=TEXT, font=font, anchor="ma")
    draw.line((MARGIN, CAPTION_TOP + 170, W - MARGIN, CAPTION_TOP + 170), fill=ACCENT, width=8)

    shot = Image.open(raw_png).convert("RGBA")
    scale = DEVICE_WIDTH / shot.width
    shot = shot.resize((DEVICE_WIDTH, round(shot.height * scale)), Image.Resampling.LANCZOS)
    shot = _round_corners(shot, CORNER_RADIUS)
    x = (W - DEVICE_WIDTH) // 2

    # Soft drop shadow: a blurred black rounded rect behind the capture lifts it off the flat canvas.
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle(
        (x, DEVICE_TOP + 24, x + DEVICE_WIDTH, DEVICE_TOP + 24 + shot.height),
        CORNER_RADIUS,
        fill=(0, 0, 0, 140),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(40))
    canvas.paste(Image.alpha_composite(canvas.convert("RGBA"), shadow).convert("RGB"))
    canvas.paste(shot, (x, DEVICE_TOP), shot)

    canvas.save(out_png, format="PNG", optimize=True)
