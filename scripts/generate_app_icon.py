"""Generate the SMCR Staff AI app icon -- pure Python, no image-library dependency.

Produces flat-design PNGs (for the PWA manifest / favicon) and a multi-size
.ico (for the desktop shortcut), all from a single procedural drawing: a dark
navy tile, a red bottom stripe, and a white upward chevron -- the dashboard's
own palette (#0d1014 / #b21f2d / #eef2f6), not a reproduction of any official
service emblem.

Run once to (re)generate the checked-in assets:
    uv run python scripts/generate_app_icon.py
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PNG_DIR = REPO_ROOT / "app" / "static" / "dashboard" / "icons"
ICO_PATH = REPO_ROOT / "scripts" / "assets" / "smcr-staff-ai.ico"

BG = (0x0D, 0x10, 0x14, 255)  # dashboard background
BORDER = (0x31, 0x38, 0x44, 255)  # dashboard panel border
MARK = (0xEE, 0xF2, 0xF6, 255)  # dashboard primary text (chevron)
ACCENT = (0xB2, 0x1F, 0x2D, 255)  # dashboard "critical/Marine red" accent

PNG_SIZES = (16, 32, 192, 512)
ICO_SIZES = (16, 32, 48, 256)


def render(size: int) -> list[tuple[int, int, int, int]]:
    """Return a flat list of RGBA pixels (row-major) for a size x size icon."""
    px: list[tuple[int, int, int, int]] = [BG] * (size * size)
    border_px = max(1, round(size * 0.03))

    cx = size / 2
    apex_y = size * 0.26
    base_y = size * 0.60
    half_span = size * 0.28
    thickness = max(1.4, size * 0.10)

    stripe_top = size * 0.74
    stripe_bottom = size * 0.90

    for y in range(size):
        on_border_row = y < border_px or y >= size - border_px
        for x in range(size):
            on_border_col = x < border_px or x >= size - border_px
            if on_border_row or on_border_col:
                px[y * size + x] = BORDER
                continue

            color = BG
            if apex_y <= y <= base_y:
                t = (y - apex_y) / (base_y - apex_y)
                arm_offset = t * half_span
                left_center = cx - arm_offset
                right_center = cx + arm_offset
                if abs(x - left_center) <= thickness / 2 or abs(x - right_center) <= thickness / 2:
                    color = MARK
            if color == BG and stripe_top <= y <= stripe_bottom:
                color = ACCENT
            px[y * size + x] = color
    return px


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))


def encode_png(size: int, pixels: list[tuple[int, int, int, int]]) -> bytes:
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)  # 8-bit RGBA, no interlace
    raw = bytearray()
    for y in range(size):
        raw.append(0)  # filter type: None
        for x in range(size):
            raw.extend(pixels[y * size + x])
    idat = zlib.compress(bytes(raw), level=9)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", idat)
        + _png_chunk(b"IEND", b"")
    )


def encode_ico(images: list[bytes], sizes: tuple[int, ...]) -> bytes:
    count = len(images)
    header = struct.pack("<HHH", 0, 1, count)
    entries = bytearray()
    offset = 6 + 16 * count
    for size, data in zip(sizes, images, strict=True):
        dim = size if size < 256 else 0  # 0 means 256 per the ICO spec
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    return header + bytes(entries) + b"".join(images)


def main() -> None:
    PNG_DIR.mkdir(parents=True, exist_ok=True)
    ICO_PATH.parent.mkdir(parents=True, exist_ok=True)

    for size in PNG_SIZES:
        png_bytes = encode_png(size, render(size))
        out = PNG_DIR / f"icon-{size}.png"
        out.write_bytes(png_bytes)
        print(f"wrote {out} ({len(png_bytes)} bytes)")

    ico_images = [encode_png(size, render(size)) for size in ICO_SIZES]
    ico_bytes = encode_ico(ico_images, ICO_SIZES)
    ICO_PATH.write_bytes(ico_bytes)
    print(f"wrote {ICO_PATH} ({len(ico_bytes)} bytes)")


if __name__ == "__main__":
    main()
