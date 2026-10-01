#!/usr/bin/env python3
"""Scrape the public contribution calendar — no token — into data/contributions.json.

usage: python scripts/fetch_contributions.py [username]
reads: https://github.com/users/<username>/contributions (the fragment the profile page itself uses)
writes: data/contributions.json — days, total, current/longest streak, best day, monthly totals
"""
import json
import re
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"
USER = sys.argv[1] if len(sys.argv) > 1 else "altafshaikh"
COUNT = re.compile(r"^(No|\d[\d,]*) contributions? on")


def fetch(user):
    r = requests.get(f"https://github.com/users/{user}/contributions", timeout=30,
                     headers={"User-Agent": "profile-art-refresh"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tips = {t.get("for"): t.get_text(strip=True) for t in soup.select("tool-tip[for]")}
    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        m = COUNT.match(tips.get(td.get("id"), ""))
        if not m:
            raise SystemExit(f"error: no count for {td['data-date']} — the calendar markup changed")
        n = 0 if m.group(1) == "No" else int(m.group(1).replace(",", ""))
        days.append({"date": td["data-date"], "count": n, "level": int(td.get("data-level", 0))})
    if not days:
        raise SystemExit("error: no calendar cells found — the calendar markup changed")
    return sorted(days, key=lambda d: d["date"])


def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)
    # Today not having a contribution yet does not break the current streak.
    tail = days[:-1] if days[-1]["count"] == 0 else days
    current = 0
    for d in reversed(tail):
        if not d["count"]:
            break
        current += 1
    return current, longest


def main():
    days = fetch(USER)
    current, longest = streaks(days)
    best = max(days, key=lambda d: d["count"])
    monthly = OrderedDict()
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]
    data = {
        "user": USER,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"from": days[0]["date"], "to": days[-1]["date"]},
        "total": sum(d["count"] for d in days),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly,
        "days": days,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1) + "\n")
    print(f"{OUT}: {data['total']} contributions, {len(days)} days, streak {current}/{longest}")


if __name__ == "__main__":
    main()
