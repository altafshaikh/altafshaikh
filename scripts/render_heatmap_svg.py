#!/usr/bin/env python3
"""Render data/contributions.json as an animated 53x7 contribution heatmap.

usage: python scripts/render_heatmap_svg.py   (STATIC=1 for a frozen frame)
reads: data/contributions.json   writes: contrib-heatmap.svg
"""
import json
import os
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "data" / "contributions.json", ROOT / "contrib-heatmap.svg"
STATIC = os.environ.get("STATIC") == "1"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]  # none -> neon top end
BG, FG, DIM = "#0d1117", "#c9d1d9", "#8b949e"
W = 860
CELL, GAP = 11, 3
STEP = CELL + GAP
TOP = 40
DIAG_DELAY = 0.025  # seconds per diagonal (week + weekday)


def level(day, top):
    """GitHub's 0-4 level, plus a level 5 for the days at the very top of the year."""
    if day["count"] and day["count"] >= top:
        return 5
    return min(day["level"], 4)


def main():
    data = json.loads(SRC.read_text())
    days = data["days"]
    nonzero = sorted(d["count"] for d in days if d["count"])
    top = nonzero[int(len(nonzero) * 0.95)] if nonzero else 1

    first = date.fromisoformat(days[0]["date"])
    first -= timedelta(days=(first.weekday() + 1) % 7)  # weeks start on Sunday, like GitHub's
    weeks = (date.fromisoformat(days[-1]["date"]) - first).days // 7 + 1
    grid_h = 7 * STEP
    left = (W - weeks * STEP) // 2 + 12  # centred, nudged right for the weekday labels
    h = TOP + grid_h + 62

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}">',
        "<style>",
        "text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}",
    ]
    if not STATIC:
        out.append(".c{opacity:0;transform:translateY(-6px);animation:drop .4s ease-out forwards}")
        out.append("@keyframes drop{to{opacity:1;transform:translateY(0)}}")
        out += [f".d{k}{{animation-delay:{k * DIAG_DELAY:.3f}s}}" for k in range(weeks + 7)]
        out.append(".f{opacity:0;animation:drop .5s ease-out forwards;animation-delay:%.2fs}" % ((weeks + 7) * DIAG_DELAY))
    out += ["</style>", f'<rect width="100%" height="100%" rx="10" fill="{BG}"/>']

    # Month labels above the first week that starts in each month.
    seen = set()
    for wk in range(weeks):
        d = first + timedelta(weeks=wk)
        if d.month not in seen and d.day <= 7 and wk < weeks - 1:
            seen.add(d.month)
            out.append(f'<text x="{left + wk * STEP}" y="{TOP - 10}" font-size="11" fill="{DIM}">{d:%b}</text>')
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="{left - 36}" y="{TOP + row * STEP + CELL - 2}" font-size="10" fill="{DIM}">{name}</text>')

    for d in days:
        dt = date.fromisoformat(d["date"])
        wk, row = (dt - first).days // 7, (dt.weekday() + 1) % 7
        cls = "" if STATIC else f' class="c d{wk + row}"'
        tip = f'{d["count"]} contribution{"" if d["count"] == 1 else "s"} on {d["date"]}'
        out.append(
            f'<rect{cls} x="{left + wk * STEP}" y="{TOP + row * STEP}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{PALETTE[level(d, top)]}"><title>{tip}</title></rect>'
        )

    # Footer: stats on the left, Less -> More legend on the right.
    fy = TOP + grid_h + 26
    best = date.fromisoformat(data["best_day"]["date"])
    stats = (
        f'<tspan fill="{FG}" font-weight="bold">{data["total"]:,}</tspan> contributions in the last year'
        f'  ·  streak <tspan fill="{FG}">{data["current_streak"]}d</tspan>'
        f' (best <tspan fill="{FG}">{data["longest_streak"]}d</tspan>)'
        f'  ·  best day <tspan fill="{FG}">{data["best_day"]["count"]}</tspan> on {best:%b} {best.day}'
    )
    fcls = "" if STATIC else ' class="f"'
    out.append(f'<g{fcls}><text x="{left}" y="{fy}" font-size="12" fill="{DIM}" xml:space="preserve">{stats}</text>')
    lx = left + weeks * STEP - GAP - len(PALETTE) * STEP - 34
    out.append(f'<text x="{lx - 34}" y="{fy + 20}" font-size="11" fill="{DIM}">Less</text>')
    for k, c in enumerate(PALETTE):
        out.append(f'<rect x="{lx + k * STEP}" y="{fy + 10}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c}"/>')
    out.append(f'<text x="{lx + len(PALETTE) * STEP + 4}" y="{fy + 20}" font-size="11" fill="{DIM}">More</text></g>')
    out.append(
        f'<text x="{left}" y="{fy + 20}" font-size="10" fill="{DIM}" opacity="0.7">'
        f'updated {data["fetched_at"][:10]} · github.com/{data["user"]}</text>'
    )
    out.append("</svg>")
    OUT.write_text("\n".join(out) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
