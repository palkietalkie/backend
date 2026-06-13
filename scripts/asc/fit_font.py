from PIL import ImageDraw, ImageFont

from scripts.asc.load_font import load_font


def fit_font(
    draw: ImageDraw.ImageDraw, text: str, max_size: int, max_width: int
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Largest font (<= max_size px) at which `text` renders within `max_width` on one line.

    A fixed font size clips long headings (e.g. "Individual · Monthly") at the canvas edge, so step down 4px at a time until the measured width fits. The 24px floor keeps text legible if nothing fits.
    """
    for size in range(max_size, 23, -4):
        font = load_font(size)
        if draw.textlength(text, font=font) <= max_width:
            return font
    return load_font(24)
