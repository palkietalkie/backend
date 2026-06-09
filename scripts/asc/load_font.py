from pathlib import Path

from PIL import ImageFont


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a system TrueType font at `size`, falling back to Pillow's default bitmap font.

    Tries SF (Apple), Helvetica, Arial in order — whichever the host has installed. On macOS SF Pro is the right pick for screenshots that match Apple's review aesthetics; on Linux build machines we'd fall through to the default bitmap, which is ugly but lets the script keep running.
    """
    for path in (
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ):
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default(size)
