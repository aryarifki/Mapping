#!/usr/bin/env python3
"""Flatten the JSON samples into tidy CSV files under data/csv/.

Only samples whose payload is a list of flat objects (or a dict with a list under
"data"/"place") can be tabulated; anything else is skipped, not guessed at.

Usage: python3 scripts/export_csv.py
"""

from __future__ import annotations

import csv
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data/csv")


def rows_of(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "place"):
            node = payload.get(key)
            if isinstance(node, list):
                return node
            if isinstance(node, dict):
                return [node]
    return []


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    written = 0
    for path in sorted(glob.glob(os.path.join(ROOT, "samples/*/*.json"))):
        if path.endswith(".meta.json"):
            continue
        try:
            payload = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        rows = rows_of(payload)
        rows = [r for r in rows if isinstance(r, dict)]
        if not rows:
            continue
        # Union of keys, preserving first-seen order.
        cols = list(dict.fromkeys(k for r in rows for k in r))
        site = os.path.basename(os.path.dirname(path))
        stem = os.path.basename(path).replace(".json", "")
        dest = os.path.join(OUT, f"{site}__{stem}.csv")
        with open(dest, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        written += 1
        print(f"  {len(rows):>5} rows x {len(cols):>2} cols -> data/csv/{site}__{stem}.csv")
    print(f"\n{written} CSV written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
