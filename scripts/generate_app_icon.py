"""Generate the SMCR Staff AI app icons -- pure Python, no image-library dependency.

The identity artwork is scripts/assets/crt-icon-source.png (a 512x512 render of
a retro CRT monitor displaying a matrix-rain emblem, supplied by the project
owner). CRT detail does not survive taskbar/favicon sizes, so this emits
different artwork per size -- the standard multi-resolution icon approach:

- 512/256/192 px: the CRT art as-is (PWA install icon, Explorer large icons)
- 48 px:         the CRT art cropped to just the screen (bezel dropped)
- 32/16 px:      a procedural phosphor-green chevron mark in the CRT art's own
                 sampled palette (taskbar, favicon, Explorer small icons)

Run once to (re)generate the checked-in assets:
    uv run python scripts/generate_app_icon.py
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_PNG = REPO_ROOT / "scripts" / "assets" / "crt-icon-source.png"
PNG_DIR = REPO_ROOT / "app" / "static" / "dashboard" / "icons"
ICO_PATH = REPO_ROOT / "scripts" / "assets" / "smcr-staff-ai.ico"

Pixels = list[tuple[int, int, int, int]]


# ---------------------------------------------------------------------------
# Minimal PNG decode (8-bit RGB/RGBA, non-interlaced -- what the source uses)
# ---------------------------------------------------------------------------

def decode_png(path: Path) -> tuple[int, int, Pixels]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"{path} is not a PNG.")
    pos = 8
    width = height = 0
    colortype = -1
    idat = bytearray()
    while pos + 8 <= len(data):
        length = int.from_bytes(data[pos : pos + 4], "big")
        tag = data[pos + 4 : pos + 8]
        chunk = data[pos + 8 : pos + 8 + length]
        if tag == b"IHDR":
            width, height = struct.unpack(">II", chunk[:8])
            bitdepth, colortype, _, _, interlace = chunk[8:13]
            if bitdepth != 8 or colortype not in (2, 6) or interlace != 0:
                raise SystemExit(
                    f"{path}: only 8-bit RGB/RGBA non-interlaced PNG is supported "
                    f"(got bitdepth={bitdepth}, colortype={colortype}, interlace={interlace})."
                )
        elif tag == b"IDAT":
            idat += chunk
        elif tag == b"IEND":
            break
        pos += 12 + length

    raw = zlib.decompress(bytes(idat))
    channels = 3 if colortype == 2 else 4
    stride = width * channels
    pixels: Pixels = []
    prev = bytearray(stride)
    offset = 0
    for _ in range(height):
        ftype = raw[offset]
        offset += 1
        line = bytearray(raw[offset : offset + stride])
        offset += stride
        _unfilter(ftype, line, prev, channels)
        for x in range(width):
            i = x * channels
            r, g, b = line[i], line[i + 1], line[i + 2]
            a = line[i + 3] if channels == 4 else 255
            pixels.append((r, g, b, a))
        prev = line
    return width, height, pixels


def _unfilter(ftype: int, line: bytearray, prev: bytearray, channels: int) -> None:
    n = len(line)
    if ftype == 0:
        return
    if ftype == 1:  # Sub
        for i in range(channels, n):
            line[i] = (line[i] + line[i - channels]) & 0xFF
    elif ftype == 2:  # Up
        for i in range(n):
            line[i] = (line[i] + prev[i]) & 0xFF
    elif ftype == 3:  # Average
        for i in range(n):
            left = line[i - channels] if i >= channels else 0
            line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
    elif ftype == 4:  # Paeth
        for i in range(n):
            left = line[i - channels] if i >= channels else 0
            up = prev[i]
            up_left = prev[i - channels] if i >= channels else 0
            p = left + up - up_left
            pa, pb, pc = abs(p - left), abs(p - up), abs(p - up_left)
            if pa <= pb and pa <= pc:
                predictor = left
            elif pb <= pc:
                predictor = up
            else:
                predictor = up_left
            line[i] = (line[i] + predictor) & 0xFF
    else:
        raise SystemExit(f"Unsupported PNG filter type {ftype}.")


# ---------------------------------------------------------------------------
# Area-average resample + crop
# ---------------------------------------------------------------------------

def resample(pixels: Pixels, src_w: int, src_h: int, dst_w: int, dst_h: int) -> Pixels:
    """Box-filter downscale with fractional pixel coverage (good for shrinking)."""
    out: Pixels = []
    x_ratio = src_w / dst_w
    y_ratio = src_h / dst_h
    for dy in range(dst_h):
        y0, y1 = dy * y_ratio, (dy + 1) * y_ratio
        for dx in range(dst_w):
            x0, x1 = dx * x_ratio, (dx + 1) * x_ratio
            acc = [0.0, 0.0, 0.0, 0.0]
            total = 0.0
            sy = int(y0)
            while sy < y1 and sy < src_h:
                cover_y = min(sy + 1, y1) - max(sy, y0)
                sx = int(x0)
                while sx < x1 and sx < src_w:
                    cover = cover_y * (min(sx + 1, x1) - max(sx, x0))
                    p = pixels[sy * src_w + sx]
                    for c in range(4):
                        acc[c] += p[c] * cover
                    total += cover
                    sx += 1
                sy += 1
            out.append(tuple(min(255, max(0, round(acc[c] / total))) for c in range(4)))
    return out


def gain(pixels: Pixels, factor: float) -> Pixels:
    """Brightness gain. The emblem is sparse bright glyphs on black, so a
    box-filtered downscale averages it toward black; boosting after the
    resample keeps small sizes reading as a glowing mark, not a smudge."""
    return [tuple(min(255, round(c * factor)) for c in p[:3]) + (255,) for p in pixels]  # type: ignore[misc]


def crop(pixels: Pixels, src_w: int, box: tuple[int, int, int, int]) -> tuple[int, int, Pixels]:
    x0, y0, x1, y1 = box
    out: Pixels = []
    for y in range(y0, y1):
        row = pixels[y * src_w + x0 : y * src_w + x1]
        out.extend(row)
    return x1 - x0, y1 - y0, out


def detect_screen_box(pixels: Pixels, w: int, h: int) -> tuple[int, int, int, int]:
    """Find the green phosphor screen inside the CRT bezel.

    The monitor case (bezel, nameplate, shadows) is rendered in warm tones --
    red exceeds green everywhere on it -- while the screen is neutral-black to
    phosphor-green, so green >= red. Classify by that channel relationship
    rather than brightness, which fails on this art's dark bezel. Detected
    (not hardcoded) so a re-rendered source still crops correctly.
    """
    def is_screen(p: tuple[int, int, int, int]) -> bool:
        return p[1] >= p[0]

    def screen_fraction_row(y: int) -> float:
        row = pixels[y * w + w // 4 : y * w + 3 * w // 4]
        return sum(1 for p in row if is_screen(p)) / len(row)

    def screen_fraction_col(x: int) -> float:
        col = [pixels[y * w + x] for y in range(h // 4, 3 * h // 4)]
        return sum(1 for p in col if is_screen(p)) / len(col)

    rows = [y for y in range(h) if screen_fraction_row(y) > 0.7]
    cols = [x for x in range(w) if screen_fraction_col(x) > 0.7]
    if not rows or not cols:
        raise SystemExit("Could not find the CRT screen region in the source image.")
    inset = max(2, w // 50)  # step past the screen's soft glass edge
    return (min(cols) + inset, min(rows) + inset, max(cols) - inset, max(rows) - inset)


def sample_palette(pixels: Pixels) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    """Pull (screen_black, phosphor_green) from the art so the small-size
    procedural mark stays in the same family as the CRT render."""
    greens = [p for p in pixels if p[1] > 140 and p[1] > p[0] * 1.6 and p[1] > p[2] * 1.6]
    greens.sort(key=lambda p: p[1], reverse=True)
    top = greens[: max(1, len(greens) // 10)]
    green = tuple(sum(p[c] for p in top) // len(top) for c in range(3)) + (255,)
    darks = sorted(pixels, key=lambda p: p[0] + p[1] + p[2])[: len(pixels) // 20]
    dark = tuple(sum(p[c] for p in darks) // len(darks) for c in range(3)) + (255,)
    return dark, green  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Procedural small-size mark (phosphor chevron in the sampled CRT palette)
# ---------------------------------------------------------------------------

def render_mark(size: int, dark: tuple[int, int, int, int], green: tuple[int, int, int, int]) -> Pixels:
    dim_green = tuple(c // 3 for c in green[:3]) + (255,)
    px: Pixels = [dark] * (size * size)
    border_px = max(1, round(size * 0.06))

    cx = size / 2
    apex_y = size * 0.20
    base_y = size * 0.62
    half_span = size * 0.30
    thickness = max(1.4, size * 0.12)
    stripe_top = size * 0.76
    stripe_bottom = size * 0.88

    for y in range(size):
        on_border_row = y < border_px or y >= size - border_px
        for x in range(size):
            if on_border_row or x < border_px or x >= size - border_px:
                px[y * size + x] = dim_green
                continue
            color = dark
            if apex_y <= y <= base_y:
                t = (y - apex_y) / (base_y - apex_y)
                arm = t * half_span
                if abs(x - (cx - arm)) <= thickness / 2 or abs(x - (cx + arm)) <= thickness / 2:
                    color = green
            if color == dark and stripe_top <= y <= stripe_bottom:
                color = dim_green
            px[y * size + x] = color
    return px


# ---------------------------------------------------------------------------
# PNG / ICO encoding (unchanged approach: stdlib only, deterministic)
# ---------------------------------------------------------------------------

def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))


def encode_png(width: int, height: int, pixels: Pixels) -> bytes:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)  # 8-bit RGBA
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter: None
        for x in range(width):
            raw.extend(pixels[y * width + x])
    idat = zlib.compress(bytes(raw), level=9)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", idat)
        + _png_chunk(b"IEND", b"")
    )


def encode_ico(images: list[bytes], sizes: list[int]) -> bytes:
    count = len(images)
    header = struct.pack("<HHH", 0, 1, count)
    entries = bytearray()
    offset = 6 + 16 * count
    for size, data in zip(sizes, images, strict=True):
        dim = size if size < 256 else 0  # 0 means 256 per the ICO spec
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    return header + bytes(entries) + b"".join(images)


# ---------------------------------------------------------------------------

def main() -> None:
    if not SOURCE_PNG.exists():
        raise SystemExit(f"Missing source artwork: {SOURCE_PNG}")
    src_w, src_h, src = decode_png(SOURCE_PNG)
    dark, green = sample_palette(src)
    screen_w, screen_h, screen = crop(src, src_w, detect_screen_box(src, src_w, src_h))

    PNG_DIR.mkdir(parents=True, exist_ok=True)
    ICO_PATH.parent.mkdir(parents=True, exist_ok=True)

    outputs: dict[str, tuple[int, Pixels]] = {
        "icon-512.png": (512, resample(src, src_w, src_h, 512, 512)),
        "icon-192.png": (192, resample(src, src_w, src_h, 192, 192)),
        "icon-32.png": (32, render_mark(32, dark, green)),
        "icon-16.png": (16, render_mark(16, dark, green)),
    }
    for name, (size, pixels) in outputs.items():
        out = PNG_DIR / name
        out.write_bytes(encode_png(size, size, pixels))
        print(f"wrote {out}")

    ico_variants: list[tuple[int, Pixels]] = [
        (16, render_mark(16, dark, green)),
        (32, render_mark(32, dark, green)),
        (48, gain(resample(screen, screen_w, screen_h, 48, 48), 2.8)),
        (256, resample(src, src_w, src_h, 256, 256)),
    ]
    ico_bytes = encode_ico(
        [encode_png(size, size, pixels) for size, pixels in ico_variants],
        [size for size, _ in ico_variants],
    )
    ICO_PATH.write_bytes(ico_bytes)
    print(f"wrote {ICO_PATH} ({len(ico_bytes)} bytes)")


if __name__ == "__main__":
    main()
