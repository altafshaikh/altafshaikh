#!/usr/bin/env python3
"""Hand-author a neofetch-style info card that prints itself line by line.

usage: python scripts/make_info_card.py   (STATIC=1 for a frozen frame, e.g. for Quick Look)
writes: info-card.svg
"""
import os
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

W = 632  # shown at 490 px; height is tuned so the card lines up with the 370 px portrait beside it
BG, BAR, FG, DIM = "#0d1117", "#161b22", "#c9d1d9", "#8b949e"
KEY, ACCENT = "#39d353", "#58a6ff"

# (key, value) rows; a None key is a blank spacer, a key with value "" is a section heading.
ROWS = [
    ("Now", "Backend Engineer @ Contentstack"),
    ("Team", "Content Delivery API (CDA)"),
    ("Stack", "Python · TypeScript · Node.js"),
    ("", "NestJS · Next.js · Django"),
    (None, None),
    ("Highlights", ""),
    ("›", "content-factory / TeachMeBro"),
    ("›", "AI agents"),
    (None, None),
    ("Into", "Cyber security · Open source · Teaching"),
    (None, None),
    ("Twitter", "@ialtafshaikh"),
    ("LinkedIn", "in/ialtafshaikh"),
    ("Instagram", "@ialtafshaikh"),
]
SWATCH = ["#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0", "#58a6ff", "#bc8cff", "#f778ba"]

PAD, TOP, LH, FS = 28, 70, 21, 14
KEY_W = 128
STEP, DUR = 0.12, 0.45  # seconds between lines, fade/slide time


def line(i, inner):
    """One printed line: fades in and slides from the left, staggered by its index."""
    if STATIC:
        return f"<g>{inner}</g>"
    return f'<g class="l" style="animation-delay:{0.4 + i * STEP:.2f}s">{inner}</g>'


def main():
    h = TOP + (len(ROWS) + 3) * LH + PAD
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}">',
        "<style>",
        ".l{opacity:0;transform:translateX(-12px);animation:in %.2fs ease-out forwards}" % DUR,
        "@keyframes in{to{opacity:1;transform:translateX(0)}}",
        "</style>",
        f'<rect width="100%" height="100%" rx="10" fill="{BG}"/>',
        f'<path d="M0 10a10 10 0 0 1 10-10h{W - 20}a10 10 0 0 1 10 10v22H0z" fill="{BAR}"/>',
    ]
    for j, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        out.append(f'<circle cx="{18 + j * 18}" cy="16" r="5.5" fill="{c}"/>')
    out.append(
        f'<g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="{FS}" fill="{FG}">'
    )
    out.append(f'<text x="{W / 2}" y="21" text-anchor="middle" font-size="12" fill="{DIM}">altaf@github: ~ — neofetch</text>')

    n = 0
    y = TOP - 14
    out.append(line(n, f'<text x="{PAD}" y="{y}"><tspan fill="{KEY}" font-weight="bold">altaf</tspan>'
                       f'<tspan fill="{DIM}">@</tspan><tspan fill="{KEY}" font-weight="bold">github</tspan></text>'))
    n += 1
    y += 16
    out.append(line(n, f'<text x="{PAD}" y="{y}" fill="{DIM}">{"-" * 28}</text>'))
    y += 12
    for key, val in ROWS:
        y += LH
        n += 1
        if key is None:
            continue
        if val == "":
            out.append(line(n, f'<text x="{PAD}" y="{y}" fill="{KEY}" font-weight="bold">{escape(key)}</text>'))
        elif key == "›":
            out.append(line(n, f'<text x="{PAD + 12}" y="{y}"><tspan fill="{ACCENT}">›</tspan><tspan dx="9">{escape(val)}</tspan></text>'))
        else:
            k = f'<tspan fill="{KEY}" font-weight="bold">{escape(key)}</tspan>' if key else ""
            out.append(line(n, f'<text x="{PAD}" y="{y}">{k}<tspan x="{PAD + KEY_W}">{escape(val)}</tspan></text>'))
    y += LH + 6
    n += 1
    blocks = "".join(f'<rect x="{PAD + k * 30}" y="{y}" width="26" height="14" rx="2" fill="{c}"/>' for k, c in enumerate(SWATCH))
    out.append(line(n, blocks))
    out += ["</g>", "</svg>"]
    OUT.write_text("\n".join(out) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
