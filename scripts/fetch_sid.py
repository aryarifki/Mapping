#!/usr/bin/env python3
"""Collect the public endpoints of the KSEI investor portal (AKSes).

Finding, and it matters: https://sid.ksei.co.id -- the host named in the brief --
does not resolve in DNS (NXDOMAIN, checked against 1.1.1.1 and the system
resolver). There is no "SID" subdomain. The investor/SID data actually lives at:

  * https://akses.ksei.co.id   "AKSes" (Acuan Kepemilikan Saham) investor portal.
      A React SPA that calls same-origin paths under /service/<...>, which nginx
      proxies to a Spring Boot back end mounted at /api/v1/<...> (visible in the
      error payloads: "path":"/api/v1/demografi/investor").
  * https://www.ksei.co.id/api/investor_demographic/*  -- the same SID statistics
      as server-rendered JSON (see fetch_ksei.py).

The SPA bundle (main.<hash>.js) references 328 distinct "service/..." routes.
Only a small subset is anonymous; the rest sit behind the investor login
(orchid/myportofolio/myaccount prefixes) and are recorded but never called.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import get, save, status_label, write_json  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = "https://akses.ksei.co.id"

# AKSes sits behind the same nginx as www.ksei.co.id: no WAF, plain UA is enough.
# The SPA always sends Origin/Referer; mirroring that keeps behaviour identical.
AKSES_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
    "Origin": HOST,
    "Referer": HOST + "/",
}

# id, method, path, params, description, category
ENDPOINTS = [
    ("S01", "GET", "/service/informasi-saham/daftar-saham", {},
     "Full listed-securities snapshot with reference prices", "market-data"),
    ("S02", "GET", "/service/demografis/gender", {"id": ""},
     "SID investor demographics by province/city split by gender (empty id = national)", "investor/sid"),
    ("S03", "GET", "/service/demografis/detil-data", {},
     "Per-region investor counts with lat/long, for map rendering", "investor/sid"),
    ("S04", "GET", "/service/demografi/master/place", {},
     "Dukcapil region master: province + city codes used by every demografi filter", "reference"),
    ("S05", "GET", "/service/demografis/updated-at", {"lang": "id"},
     "Timestamp of the last demographics refresh", "investor/sid"),
    ("S06", "GET", "/service/aksi-korporasi/news/landing/periode/current-year", {},
     "Current corporate-action year marker", "corporate-action"),
    ("S07", "POST", "/service/demografis/occupation", {"city": "", "province": ""},
     "Investor occupation breakdown, filterable by city/province", "investor/sid"),
    ("S08", "GET", "/service/demografi/age", {"city": "", "province": ""},
     "Investor age-band breakdown, filterable by city/province", "investor/sid"),
    ("S09", "GET", "/service/demografi/investor", {"city": "", "province": ""},
     "Investor type breakdown (individual/corporate/...)", "investor/sid"),
]

# Routes present in the bundle but gated behind the investor login.
AUTH_ONLY = [
    ("A01", "/service/orchid/", 93, "Investor portfolio/sub-account service (login required)"),
    ("A02", "/service/myportofolio/", 48, "Investor portfolio views (login required)"),
    ("A03", "/service/myaccount/", 25, "Investor account settings (login required)"),
    ("A04", "/service/emiten-area/", 16, "Issuer-area reporting (issuer login required)"),
    ("A05", "/service/admin-mgt/", 11, "Back-office administration (staff login required)"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="fetch a single endpoint id, e.g. S02")
    args = ap.parse_args()

    scanned_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []

    for eid, method, path, params, desc, category in ENDPOINTS:
        if args.only and args.only != eid:
            continue
        url = HOST + path + ("?" + urllib.parse.urlencode(params) if params else "")
        print(f"[{eid}] {method} {path}  params={params}")
        res = get(url, AKSES_HEADERS, retries=3, backoff=6, pace=1.0,
                  method=method, body={} if method == "POST" else None)
        state = status_label(res)
        sample = f"samples/sid/{eid}__{path.rstrip('/').split('/')[-1]}.json"

        if res.status == 200 and res.body.lstrip()[:1] not in (b"", b"<"):
            n = save(res, os.path.join(ROOT, sample), meta={
                "id": eid, "url": url, "status": res.status, "scanned_at": scanned_at,
                "description": desc, "category": category, "params": params, "method": method,
            })
            print(f"      active  {n} bytes -> {sample}")
        else:
            sample = None
            print(f"      {state}  {res.body[:120].decode('utf-8', 'replace')!r}")

        rows.append({
            "id": eid, "host": "akses.ksei.co.id", "path": path, "method": method,
            "params": params, "description": desc, "category": category,
            "status": state, "http": res.status, "bytes": len(res.body),
            "sample": sample if res.status == 200 else None, "scanned_at": scanned_at,
        })

    for eid, prefix, count, note in AUTH_ONLY:
        rows.append({
            "id": eid, "host": "akses.ksei.co.id", "path": prefix, "method": "GET",
            "params": {}, "description": f"{note} ({count} routes in bundle)",
            "category": "authenticated", "status": "authenticated", "http": None,
            "bytes": 0, "sample": None, "scanned_at": scanned_at,
        })

    manifest = os.path.join(ROOT, "data/sid_endpoints.json")
    if args.only and os.path.exists(manifest):
        with open(manifest, encoding="utf-8") as fh:
            merged = {r["id"]: r for r in json.load(fh)}
        for row in rows:
            merged[row["id"]] = row
        rows = sorted(merged.values(), key=lambda r: r["id"])

    write_json(manifest, rows)
    ok = sum(1 for r in rows if r["status"] == "active")
    print(f"\n{ok} active / {len(rows)} documented -> data/sid_endpoints.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
