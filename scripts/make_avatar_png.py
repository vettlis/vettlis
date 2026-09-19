#!/usr/bin/env python3
"""
Render a COARSE ASCII portrait as a square PNG for use as the GitHub avatar.

This is deliberately not the same art as vetle-ascii.svg. That one is a 100x53
grid built to be read at 840px wide; GitHub shows an avatar at ~260px on the
profile, which would give it 2.6px per character -- mush. So the avatar gets
its own, much coarser grid where each character still occupies several pixels
at display size.

Two things drove the parameters, both measured rather than assumed:
  - Coarse ASCII needs the opposite tone strategy to fine ASCII. At 100x53 you
    can blank the skin and let contours carry the likeness; at 56x31 the
    contours are gone, so the face has to be FILLED and only the background
    left blank. Hence the high white floor.
  - At 40px (comment threads) the downscale averages character density back
    into continuous tone, so it still reads as a face. That is better than a
    coarse grid has any right to look, and it is why 56 columns beats 44.

GitHub avatars must be raster (PNG/JPG/GIF) and are not animated, so there is
no SMIL here -- just a still frame rendered with PIL.

    python scripts/make_avatar_png.py [source-prepped.png] [avatar-ascii.png]
"""
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-prepped.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "avatar-ascii.png")

# Fraction of the prepped image to keep, as (left, top, right, bottom) in 0..1.
# GitHub circle-crops the avatar, so the head is centred and given room rather
# than cropped to the jaw -- a tight crop loses hair and chin to the circle.
CROP = (0.11, 0.02, 0.89, 0.80)

COLS = 56                 # character columns across the avatar
CHAR_ASPECT = 0.55        # glyph advance / line height for the SF Mono stack
CANVAS = 960              # output edge in px (GitHub resamples down from here)

RAMP = " .`:-=+*cs#%@"    # bright(sparse) -> dark(dense)
CONTRAST = 1.35
GAMMA = 1.15
WHITE_FLOOR = 0.90

BG = (13, 17, 23)         # #0d1117, matching the README panels
INK = (201, 209, 218)     # #c9d1d9

FONT_CANDIDATES = [
    "/System/Library/Fonts/SFNSMono.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Monaco.ttf",
]


def load_font(cell_w):
    """Pick the largest size whose glyph advance still fits one cell."""
    path = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)
    if path is None:
        raise SystemExit("no monospace font found; add one to FONT_CANDIDATES")
    size = 4
    best = ImageFont.truetype(path, size)
    while size < 200:
        trial = ImageFont.truetype(path, size + 1)
        advance = trial.getlength("M")
        if advance > cell_w:
            break
        size += 1
        best = trial
    return best, path, size


def main():
    rows = max(1, round(COLS * CHAR_ASPECT))
    cell_w = CANVAS / COLS
    cell_h = CANVAS / rows

    im = Image.open(SRC).convert("L")
    w, h = im.size
    im = im.crop((int(CROP[0] * w), int(CROP[1] * h), int(CROP[2] * w), int(CROP[3] * h)))
    im = ImageEnhance.Contrast(im).enhance(CONTRAST).resize((COLS, rows), Image.LANCZOS)
    px = im.load()

    font, font_path, font_size = load_font(cell_w)
    canvas = Image.new("RGB", (CANVAS, CANVAS), BG)
    draw = ImageDraw.Draw(canvas)

    drawn = 0
    for ry in range(rows):
        for cx in range(COLS):
            lum = (px[cx, ry] / 255.0) ** GAMMA
            if lum >= WHITE_FLOOR:
                continue
            idx = int((1.0 - lum) * (len(RAMP) - 1) + 0.5)
            ch = RAMP[max(0, min(len(RAMP) - 1, idx))]
            if ch == " ":
                continue
            # centre each glyph in its cell so the grid stays exact regardless
            # of the font's own advance and bearings
            box = draw.textbbox((0, 0), ch, font=font)
            gx = cx * cell_w + (cell_w - (box[2] - box[0])) / 2 - box[0]
            gy = ry * cell_h + (cell_h - (box[3] - box[1])) / 2 - box[1]
            draw.text((gx, gy), ch, font=font, fill=INK)
            drawn += 1

    canvas.save(OUT)
    print(f"wrote {OUT}: {CANVAS}x{CANVAS}, grid {COLS}x{rows}, {drawn} glyphs")
    print(f"  font {os.path.basename(font_path)} @ {font_size}px, cell {cell_w:.1f}x{cell_h:.1f}px")
    print(f"  at GitHub sizes: {260/COLS:.1f}px per char on the profile (260px), "
          f"{40/COLS:.2f}px in lists (40px, reads as averaged tone)")


if __name__ == "__main__":
    main()
