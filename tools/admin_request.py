#!/usr/bin/env python3
"""Act on the "Start a new semester" form (admin/new-semester.json, edited in Pages CMS).

Run by .github/workflows/site.yml on every push. If "start" is true it rolls the term over with
tools/site.py (current/ -> archive/<old id>/, empty new current/) and switches "start" back off, so a
second save never archives twice. Standard library only.
"""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQ = ROOT / "admin" / "new-semester.json"
SHORT = {"tr": "TR", "mwf": "MWF", "mw": "MW", "online": "Online"}
LONG = {"tr": "Tuesday & Thursday", "mwf": "Monday, Wednesday & Friday", "mw": "Monday & Wednesday", "online": "Online"}


def main():
    if not REQ.exists():
        return 0
    r = json.loads(REQ.read_text(encoding="utf8"))
    if not r.get("start"):
        print("new semester: not requested")
        return 0
    season, year, days = str(r.get("season", "")).lower(), int(r.get("year") or 0), str(r.get("schedule", "")).lower()
    r["start"] = False                      # switch off first: a failed run must not retry on every later save
    REQ.write_text(json.dumps(r, indent=2) + "\n", encoding="utf8")
    if season not in ("spring", "summer", "fall") or not 2026 <= year <= 2040 or days not in SHORT:
        print(f"new semester: the form is incomplete ({season!r}, {year!r}, {days!r}); nothing changed", file=sys.stderr)
        return 1
    new_id, term = f"{season}-{year}-{days}", f"{season.title()} {year}"
    current = json.loads((ROOT / "site.json").read_text(encoding="utf8"))["current"]["id"]
    if new_id == current:
        print(f"new semester: {term} is already the current semester; nothing changed", file=sys.stderr)
        return 1
    return subprocess.run([sys.executable, str(ROOT / "tools/site.py"), "rollover", new_id, term, SHORT[days], LONG[days]], cwd=ROOT).returncode


if __name__ == "__main__":
    sys.exit(main())
