#!/usr/bin/env python3
"""
Hand-author a neofetch-style info card SVG that sits beside the ASCII portrait:
a title bar, then colored key/value rows that fade and slide in on a short
stagger, so the panel looks like it is printing next to the portrait.

Keep the content here and NOT in the contribution graph -- the graph already
covers the GitHub stats, so this card is for the story numbers cannot tell.

Dimensions are chosen so the card lands at the same rendered height as the
portrait: the portrait is 840x875 native and is placed at width=370 in the
README (-> 385px tall), so this card is 490x385 native and is placed 1:1.
490 + 370 = 860, which matches the heatmap width above it.

  python scripts/make_info_card.py          # animated
  STATIC=1 python scripts/make_info_card.py # frozen frame for Quick Look
"""
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "info-card.svg")

# ---- content -------------------------------------------------------------
# The whole card is driven by this block. Edit here, re-run, commit.
HOST = "vetle@github"
ROWS = [
    ("Now",   "Flumen Hydro · small-hydro prospecting"),
    ("Also",  "Cerno AS · brand, web and product"),
    ("Stack", "Python · FastAPI · PostGIS · Next.js · TS"),
    ("Focus", "Turning terrain data into buildable sites"),
    ("Loc",   "Grimstad, Norway"),
]

# ---- geometry ------------------------------------------------------------
CANVAS_W = 490
CANVAS_H = 385
PAD = 22
TITLEBAR_H = 30

KEY_X = PAD
VALUE_X = PAD + 62
ROW_H = 30
ROW_TOP = TITLEBAR_H + 74

# ---- palette (matches the portrait + heatmap) ----------------------------
BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#c9d1d9"
ACCENT = "#22d3ee"
GREEN = "#39d353"
GOLD = "#f2cc60"

# neofetch prints a strip of terminal colours under its key/value block
SWATCHES = ["#ff5f56", "#f2cc60", "#39d353", "#22d3ee", "#1f6feb", "#bc8cff", "#c9d1d9"]

# ---- reveal timing (one-shot, then freeze) -------------------------------
# Advance width of one character as an em fraction, measured in-browser for the
# ui-monospace stack -- the prompt cursor sits flush against the text with it.
MONO_ADVANCE = 0.602

STAGGER = 0.14
DUR = 0.42
SLIDE = 10  # px the row travels while fading in

STATIC = bool(os.environ.get("STATIC"))


def row_group(index, body):
    """Wrap a row in a fade + slide-in that plays once and freezes."""
    if STATIC:
        return f"<g>{body}</g>"
    begin = index * STAGGER
    return (
        f'<g opacity="0" transform="translate({SLIDE},0)">'
        f'<animate attributeName="opacity" from="0" to="1" begin="{begin:.3f}s" '
        f'dur="{DUR:.2f}s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" '
        f'from="{SLIDE} 0" to="0 0" begin="{begin:.3f}s" dur="{DUR:.2f}s" '
        f'calcMode="spline" keySplines="0.2 0.8 0.2 1" fill="freeze"/>'
        f"{body}</g>"
    )


def build():
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
        f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="ui-monospace, SFMono-Regular, '
        f'Menlo, Consolas, monospace">',
        '<defs>'
        f'<linearGradient id="cbg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
        f'</linearGradient></defs>',
        f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="url(#cbg)"/>',
        f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{CANVAS_H-1}" rx="12" '
        f'fill="none" stroke="{FRAME}" stroke-width="1"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
    parts.append(f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
                 f'text-anchor="middle">{html.escape(HOST)}: ~$ neofetch</text>')

    idx = 0

    # neofetch header: user@host, then a rule the width of that string
    head_y = TITLEBAR_H + 36
    parts.append(row_group(idx, (
        f'<text x="{PAD}" y="{head_y}" font-size="15" font-weight="700" fill="{GREEN}">'
        f'{html.escape(HOST)}</text>'
    )))
    idx += 1
    parts.append(row_group(idx, (
        f'<line x1="{PAD}" y1="{head_y + 10}" x2="{PAD + 9 * len(HOST)}" y2="{head_y + 10}" '
        f'stroke="{MUTED}" stroke-opacity="0.6"/>'
    )))
    idx += 1

    for i, (key, value) in enumerate(ROWS):
        y = ROW_TOP + i * ROW_H
        parts.append(row_group(idx, (
            f'<text x="{KEY_X}" y="{y}" font-size="13" font-weight="700" fill="{ACCENT}">'
            f'{html.escape(key)}</text>'
            f'<text x="{VALUE_X}" y="{y}" font-size="13" fill="{INK}">{html.escape(value)}</text>'
        )))
        idx += 1

    # terminal colour strip, the way real neofetch signs off
    sw_y = ROW_TOP + len(ROWS) * ROW_H + 26
    sw_w, sw_h, sw_gap = 26, 13, 5
    swatch = []
    for si, color in enumerate(SWATCHES):
        swatch.append(f'<rect x="{PAD + si*(sw_w+sw_gap)}" y="{sw_y}" width="{sw_w}" '
                      f'height="{sw_h}" rx="2.5" fill="{color}"/>')
    parts.append(row_group(idx, "".join(swatch)))
    idx += 1

    # prompt with a blinking cursor, anchored to the bottom of the panel
    prompt_y = CANVAS_H - PAD - 4
    prompt_text = f"{HOST}:~$ "
    # STATIC gets a printed underscore; the animated card gets a blinking block
    # instead, so the two never render on top of each other.
    caret = f'<tspan fill="{GOLD}">_</tspan>' if STATIC else ""
    parts.append(row_group(idx, (
        f'<text x="{PAD}" y="{prompt_y}" font-size="13" fill="{MUTED}">'
        f'{html.escape(HOST)}:~$ {caret}</text>'
    )))

    if not STATIC:
        cursor_x = PAD + len(prompt_text) * 13 * MONO_ADVANCE
        blink_begin = idx * STAGGER
        parts.append(
            f'<rect x="{cursor_x}" y="{prompt_y - 11}" width="8" height="14" fill="{INK}" opacity="0">'
            f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
            f'dur="1s" begin="{blink_begin:.3f}s" repeatCount="indefinite"/></rect>'
        )

    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    svg = build()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote", OUT, len(svg), "bytes;", CANVAS_W, "x", CANVAS_H,
          "(STATIC)" if STATIC else "(animated)")
