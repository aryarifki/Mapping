#!/usr/bin/env python3
"""Collect every known public JSON endpoint of www.ksei.co.id.

Usage:
    python3 scripts/fetch_ksei.py            # fetch all, save samples + status manifest
    python3 scripts/fetch_ksei.py --only K07 # fetch a single endpoint

Samples are written verbatim to samples/ksei/<id>__<slug>.json and a machine
readable result table lands in data/ksei_endpoints.json.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import urllib.parse
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import KSEI_HEADERS, get, save, status_label, write_json  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = "https://www.ksei.co.id"

# A "monthYear" label is what /api/investor_demographic/sid_growths and
# /api/investor_demographic/mutual_assets validate their filter against.
# Indonesian values are sent through locale=id, English through locale=en.
MONTH_EN = "October 2026"

# id, path, params, human description, data category
ENDPOINTS = [
    ("K01", "/api/settings", {"locale": "id"}, "Site-wide settings key/value bundle", "site-meta"),
    ("K02", "/api/menus", {"locale": "id"}, "Full CMS navigation tree", "site-meta"),
    ("K03", "/api/banners", {"locale": "id"}, "Homepage banner carousel", "site-meta"),
    ("K04", "/api/seo_metas", {"locale": "id"}, "Per-page SEO metadata", "site-meta"),
    ("K05", "/api/board_types", {"locale": "id"}, "IDX board classification (Utama/Pengembangan/Ekonomi Baru)", "reference"),
    ("K06", "/api/investor_demographic/sid_growths/types", {"locale": "id"}, "Enumerates the four SID investor-count series", "investor/sid"),
    ("K07", "/api/investor_demographic/sid_growths",
     {"locale": "en", "filter[type]": "Number of Capital Market Investors", "filter[three_years_data]": MONTH_EN},
     "SID investor-count growth, 3-year window for one series", "investor/sid"),
    ("K08", "/api/investor_demographic/domestic_investors", {"locale": "id"}, "Domestic vs foreign investor composition", "investor/sid"),
    ("K09", "/api/investor_demographic/individual/age", {"locale": "id"}, "Individual investor count by age band", "investor/sid"),
    ("K10", "/api/investor_demographic/individual/education", {"locale": "id"}, "Individual investor count by education level", "investor/sid"),
    ("K11", "/api/investor_demographic/individual/gender", {"locale": "id"}, "Individual investor count by gender", "investor/sid"),
    ("K12", "/api/investor_demographic/individual/income", {"locale": "id"}, "Individual investor count by income band", "investor/sid"),
    ("K13", "/api/investor_demographic/individual/job_demographics", {"locale": "id"}, "Individual investor count by occupation", "investor/sid"),
    ("K14", "/api/investor_demographic/mutual_assets",
     {"locale": "en", "filter[four_years_data]": MONTH_EN},
     "Mutual fund product count and AUM, 4-year window", "investor/sid"),
    ("K15", "/api/securities_ownerships", {"locale": "id"}, "Securities ownership breakdown (local vs foreign)", "ownership"),
    ("K16", "/api/static_stocks", {"locale": "id"}, "Monthly static securities master files (zip download links)", "bulk-download"),
    ("K17", "/api/sro", {"locale": "id"}, "SRO / self-regulatory organisation reference data", "reference"),
    ("K18", "/api/account_managements", {"locale": "id"}, "Sub-account administration statistics", "account"),
    ("K19", "/api/account_managements/categories", {"locale": "id"}, "Categories used by account_managements", "reference"),
    ("K20", "/api/graph/aktiva_graphs/assets", {"locale": "id", "sort": "month"}, "Custody assets: total/foreign/local (IDR tn)", "graph"),
    ("K21", "/api/graph/aktiva_graphs/bonds", {"locale": "id", "sort": "month"}, "Custody bonds series", "graph"),
    ("K22", "/api/graph/aktiva_graphs/shares", {"locale": "id", "sort": "month"}, "Custody shares series", "graph"),
    ("K23", "/api/graph/aktiva_graphs/sub_account", {"locale": "id", "sort": "month"}, "Sub-account count series", "graph"),
    ("K24", "/api/graph/cbest_graphs/customer", {"locale": "id"}, "C-BEST participant customer composition", "graph"),
    ("K25", "/api/graph/cbest_graphs/instrument_information", {"locale": "id"}, "C-BEST instrument mix", "graph"),
    ("K26", "/api/graph/overbooking_graphs/value", {"locale": "id", "sort": "month"}, "Overbooking value, FOP vs VP", "graph"),
    ("K27", "/api/graph/overbooking_graphs/volume", {"locale": "id", "sort": "month"}, "Overbooking volume", "graph"),
    ("K28", "/api/graph/overbooking_graphs/frequency", {"locale": "id", "sort": "month"}, "Overbooking frequency (DFOP/DVP)", "graph"),
    ("K29", "/api/graph/overbooking_graphs/cnf", {"locale": "id", "sort": "month"}, "CNF settlement series", "graph"),
    ("K30", "/api/graph/overbooking_graphs/sectrs", {"locale": "id", "sort": "month"}, "SECTRS series", "graph"),
    ("K31", "/api/graph/overbooking_graphs/bts", {"locale": "id", "sort": "month"}, "BTS series", "graph"),
]

# Documented because they exist and are referenced by the SPA, but they are
# authenticated session endpoints -- recorded, never scraped for data.
AUTH_ENDPOINTS = [
    ("K32", "GET", "/api/auth/user", "Current session user (cookie auth.strategy=local)"),
    ("K33", "POST", "/api/auth/login", "Login handler; requires credentials + session"),
    ("K34", "POST", "/api/auth/logout", "Logout handler"),
]


def slugify(text: str) -> str:
    out = "".join(c if c.isalnum() else "-" for c in text.lower())
    return "-".join(filter(None, out.split("-")))[:60]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="fetch a single endpoint id, e.g. K07")
    args = ap.parse_args()

    scanned_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []

    for eid, path, params, desc, category in ENDPOINTS:
        if args.only and args.only != eid:
            continue
        url = HOST + path + "?" + urllib.parse.urlencode(params)
        print(f"[{eid}] GET {path}  params={params}")
        res = get(url, KSEI_HEADERS, retries=4, backoff=4)
        state = status_label(res)

        sample = f"samples/ksei/{eid}__{slugify(category + '-' + path.rstrip('/').split('/')[-1])}.json"
        if res.status == 200:
            n = save(res, os.path.join(ROOT, sample), meta={
                "id": eid, "url": url, "status": res.status, "scanned_at": scanned_at,
                "description": desc, "category": category, "params": params,
            })
            print(f"      {state}  {n} bytes -> {sample}")
        else:
            sample = None
            snippet = res.body[:160].decode("utf-8", "replace").replace("\n", " ")
            print(f"      {state}  {snippet}")

        fields = []
        if res.status == 200 and res.is_json:
            try:
                payload = res.json()
                node = payload.get("data") if isinstance(payload, dict) else payload
                if isinstance(node, list) and node and isinstance(node[0], dict):
                    fields = list(node[0].keys())
                elif isinstance(node, dict):
                    fields = list(node.keys())
            except Exception:
                pass

        rows.append({
            "id": eid, "host": "www.ksei.co.id", "path": path, "method": "GET",
            "params": params, "description": desc, "category": category,
            "status": state, "http": res.status, "bytes": len(res.body),
            "fields": fields, "sample": sample, "scanned_at": scanned_at,
        })

    for eid, method, path, desc in AUTH_ENDPOINTS:
        rows.append({
            "id": eid, "host": "www.ksei.co.id", "path": path, "method": method,
            "params": {}, "description": desc, "category": "auth",
            "status": "authenticated", "http": None, "bytes": 0,
            "fields": [], "sample": None, "scanned_at": scanned_at,
        })

    manifest_path = os.path.join(ROOT, "data/ksei_endpoints.json")
    if args.only and os.path.exists(manifest_path):
        # Merge into the existing manifest so a single-endpoint retry does not
        # wipe the results of a full run.
        with open(manifest_path, encoding="utf-8") as fh:
            existing = {r["id"]: r for r in json.load(fh)}
        for row in rows:
            existing[row["id"]] = row
        rows = sorted(existing.values(), key=lambda r: r["id"])

    write_json(manifest_path, rows)
    ok = sum(1 for r in rows if r["status"] == "active")
    print(f"\n{ok} active / {len(rows)} documented -> data/ksei_endpoints.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
