#!/usr/bin/env python3
"""Prep a photo for ASCII conversion: remove background, boost local contrast, flatten onto white.

usage: python scripts/prep_photo.py [photo]   (default: https://github.com/altafshaikh.png)
writes: source-prepped.png (grayscale, subject cropped, white background)
"""
import io
import sys
from pathlib import Path

import cv2
import numpy as np
import requests
from PIL import Image
from rembg import remove  # first run downloads its model (~1 GB, cached in ~/.u2net or ~/.rembg)

ROOT = Path(__file__).resolve().parent.parent
AVATAR = "https://github.com/altafshaikh.png"
OUT = ROOT / "source-prepped.png"
ASPECT = 1.03  # width / height of the ASCII grid (100 cols x 53 rows of 6.02 x 11 px cells)


def load(src):
    if src.startswith("http"):
        r = requests.get(src, timeout=30)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content))
    return Image.open(src)


def main():
    img = load(sys.argv[1] if len(sys.argv) > 1 else AVATAR).convert("RGB")
    cut = remove(img)  # RGBA, background alpha -> 0
    alpha = np.array(cut)[:, :, 3]

    # CLAHE on the luminance gives a flat-lit face real highlights and shadows.
    gray = cv2.cvtColor(np.array(cut.convert("RGB")), cv2.COLOR_RGB2GRAY)
    gray = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray)

    # Composite onto white so the background maps to the blank end of the ramp.
    a = alpha.astype(np.float32) / 255.0
    flat = (gray * a + 255 * (1 - a)).astype(np.uint8)

    # Crop to the subject, padded out to the grid's aspect so nothing is stretched.
    ys, xs = np.where(alpha > 32)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    h, w = y1 - y0, x1 - x0
    if w / h < ASPECT:
        w = int(h * ASPECT)
    else:
        h = int(w / ASPECT)
    cy, cx = (y0 + y1) // 2, (x0 + x1) // 2
    padded = np.full((flat.shape[0] + 2 * h, flat.shape[1] + 2 * w), 255, np.uint8)
    padded[h:h + flat.shape[0], w:w + flat.shape[1]] = flat
    top, left = h + cy - h // 2, w + cx - w // 2
    canvas = Image.fromarray(padded[top:top + h, left:left + w])
    canvas.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
