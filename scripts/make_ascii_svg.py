#!/usr/bin/env python3
"""Turn source-prepped.png into a monochrome ASCII portrait that prints itself row by row.

usage: python scripts/make_ascii_svg.py   (STATIC=1 for a frozen, fully printed frame)
reads: source-prepped.png   writes: altaf-ascii.svg
"""
import os
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "source-prepped.png", ROOT / "altaf-ascii.svg"

COLS, ROWS = 100, 53
RAMP = " .`:-=+*cs#%@"  # sparse -> dense; index 0 (space) is reserved for the background
CW, LH, FS = 6.02, 11, 10  # cell width, line height, font size
PAD = 16
INK, BG = "#c9d1d9", "#0d1117"
ROW_DELAY, ROW_DUR = 0.045, 0.35  # seconds: stagger between rows, wipe time per row
STATIC = os.environ.get("STATIC") == "1"


def grid():
    full = Image.open(SRC).convert("L")
    px = np.asarray(full.resize((COLS, ROWS), Image.LANCZOS), dtype=np.float32) / 255.0
    # Background = the white the photo was flattened onto. Measured at full resolution and
    # pooled, so the anti-aliased edge does not print as a halo of dense glyphs.
    white = Image.fromarray(((np.asarray(full) > 245) * 255).astype(np.uint8))
    bg = np.asarray(white.resize((COLS, ROWS), Image.BOX), dtype=np.float32) / 255.0 > 0.35
    # Light ink on a dark terminal: bright skin and shirt print dense, dark hair and shadow sparse.
    # Stretch the subject's own range first so the face does not merge into the hair.
    lo, hi = np.percentile(px[~bg], [3, 97])
    tone = np.clip((px - lo) / max(hi - lo, 1e-3), 0, 1) ** 0.9
    idx = (tone * (len(RAMP) - 1)).round().astype(int)
    idx[bg] = 0
    return ["".join(RAMP[i] for i in row).rstrip() for row in idx]


def main():
    rows = grid()
    w, h = COLS * CW + 2 * PAD, ROWS * LH + 2 * PAD
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}">',
        f'<rect width="100%" height="100%" rx="10" fill="{BG}"/>',
        "<defs>",
    ]
    body = []
    for i, line in enumerate(rows):
        if not line.strip():
            continue
        y = PAD + i * LH
        lw = len(line) * CW
        begin = f"{i * ROW_DELAY:.3f}s"
        if STATIC:
            out.append(f'<clipPath id="r{i}"><rect x="{PAD}" y="{y}" width="{lw:.1f}" height="{LH}"/></clipPath>')
        else:
            out.append(
                f'<clipPath id="r{i}"><rect x="{PAD}" y="{y}" width="0" height="{LH}">'
                f'<animate attributeName="width" from="0" to="{lw:.1f}" begin="{begin}" dur="{ROW_DUR}s" fill="freeze"/>'
                "</rect></clipPath>"
            )
        body.append(
            f'<text x="{PAD}" y="{y + LH - 2.5}" clip-path="url(#r{i})" textLength="{lw:.1f}" '
            f'lengthAdjust="spacingAndGlyphs" xml:space="preserve">{escape(line)}</text>'
        )
        if not STATIC:
            # A block cursor rides the wipe edge, then disappears.
            body.append(
                f'<rect x="{PAD}" y="{y + 1}" width="{CW:.2f}" height="{LH - 2}" fill="{INK}" opacity="0">'
                f'<set attributeName="opacity" to="0.9" begin="{begin}"/>'
                f'<animate attributeName="x" from="{PAD}" to="{PAD + lw:.1f}" begin="{begin}" dur="{ROW_DUR}s" fill="freeze"/>'
                f'<set attributeName="opacity" to="0" begin="{i * ROW_DELAY + ROW_DUR:.3f}s"/>'
                "</rect>"
            )
    out.append("</defs>")
    out.append(
        f'<g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="{FS}" fill="{INK}">'
    )
    out += body
    out += ["</g>", "</svg>"]
    OUT.write_text("\n".join(out) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
