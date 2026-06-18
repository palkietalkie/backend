from pathlib import Path

from PIL import Image

from scripts.asc.frame_screenshot import H, W, frame_screenshot


def test_output_is_exact_6_9_inch_size(tmp_path: Path) -> None:
    # Apple rejects an App Store screenshot that isn't exactly the slot's pixel size; the frame must preserve it.
    raw = tmp_path / "raw.png"
    Image.new("RGB", (W, H), (10, 20, 30)).save(raw)
    out = tmp_path / "framed.png"

    frame_screenshot(raw, "Talk to real personalities", out)

    with Image.open(out) as img:
        assert img.size == (W, H)
        assert img.format == "PNG"


def test_handles_a_raw_capture_of_different_pixel_size(tmp_path: Path) -> None:
    # A capture from a non-6.9" device is scaled to fit; the canvas stays the required size regardless.
    raw = tmp_path / "raw.png"
    Image.new("RGB", (1170, 2532), (0, 0, 0)).save(raw)
    out = tmp_path / "framed.png"

    frame_screenshot(raw, "Short", out)

    with Image.open(out) as img:
        assert img.size == (W, H)
