#!/usr/bin/env python3
"""Collect the public market-data endpoints of www.idx.co.id.

IDX sits behind Cloudflare and needs three separate things to cooperate:

1. A realistic browser header set, *including* Sec-Fetch-Dest/Mode/Site.
   Without them Cloudflare serves its "Just a moment..." challenge (HTTP 403).
2. Patience -- IDX rate-limits aggressively and a burst flags the IP for minutes.
3. **curl as the transport, not urllib.**

Point 3 is the non-obvious one and it cost the most time. With byte-identical
headers, `curl` gets HTTP 200 while Python's `urllib` gets the challenge:
Cloudflare fingerprints the TLS/HTTP2 handshake, and urllib speaks HTTP/1.1
with an OpenSSL ClientHello that does not look like a browser. Since curl
negotiates HTTP/2 via ALPN, it passes. So this collector shells out to curl and
parses its `-w` output. Every other collector in this repo uses urllib, because
KSEI/AKSes do not care.

Path note: the site's own front end calls /primary/<Controller>/<Action>; the
ASP.NET back end answers 302 -> /404.html when an action does not exist, which
is how the dead candidates below were identified.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import IDX_HEADERS, save, status_label, write_json, Result  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = "https://www.idx.co.id"
PACE = 6.0  # seconds between requests; lower values re-trigger the Cloudflare block

ENDPOINTS = [
    ("I01", "/primary/StockData/GetSecuritiesStock",
     {"start": "0", "length": "9999", "language": "id"},
     "Full listed-securities master: code, name, listing date, shares, board", "listing"),
    ("I02", "/primary/ListedCompany/GetCompanyProfiles",
     {"start": "0", "length": "9999", "language": "id"},
     "Issuer profiles: address, sector, sub-sector, listing board, website", "listing"),
    ("I03", "/primary/ListedCompany/GetCompanyProfilesDetail",
     {"KodeEmiten": "BBCA", "language": "id"},
     "Single-issuer detail: management, commissioners, shareholders, subsidiaries", "listing"),
    ("I04", "/primary/TradingSummary/GetStockSummary",
     {"start": "0", "length": "9999", "language": "id"},
     "Daily trading summary per stock: open/high/low/close, volume, value, freq", "market-data"),
    ("I05", "/primary/TradingSummary/GetIndexSummary",
     {"start": "0", "length": "9999", "language": "id"},
     "Index summary (IHSG and friends): previous/current, change, volume, value", "market-data"),
    ("I06", "/primary/TradingSummary/GetBrokerSummary",
     {"start": "0", "length": "9999", "language": "id"},
     "Broker summary: top buy/sell brokers per stock", "market-data"),
    ("I07", "/primary/ListedCompany/GetAnnouncement",
     {"start": "0", "length": "5", "pagesize": "5", "language": "id"},
     "Issuer announcements / keterbukaan informasi feed (237k records; pagesize is "
     "the parameter that actually paginates -- length is ignored)", "disclosure"),
]

# Probed and confirmed absent (302 -> /404.html?aspxerrorpath=/api/...).
# Recorded so nobody re-probes them from scratch.
DEAD = [
    ("/primary/StockData/GetStockSummary", "wrong controller; use TradingSummary/GetStockSummary"),
    ("/primary/StockData/GetIndexList", "no such action"),
    ("/primary/StockData/GetStockTrade", "no such action"),
    ("/primary/StockData/GetDailyTrading", "no such action"),
    ("/primary/StockData/GetBrokerSummary", "wrong controller; use TradingSummary/GetBrokerSummary"),
    ("/primary/StockData/GetTradeSummary", "no such action"),
    ("/primary/TradingSummary/GetIndexList", "no such action"),
    ("/primary/TradingSummary/GetSectoralSummary", "no such action"),
    ("/primary/ListedCompany/GetDividend", "no such action"),
    ("/primary/ListedCompany/GetCompanyDividend", "no such action"),
    ("/primary/ListedCompany/GetStockSplit", "no such action"),
    ("/primary/Dividend/GetDividend", "no such action"),
    ("/primary/Home/GetHome", "no such action"),
]


def curl_get(url: str, headers: dict, timeout: int = 40) -> Result:
    """One request through curl; returns a Result with the raw body."""
    fd, tmp = tempfile.mkstemp(suffix=".body")
    os.close(fd)
    args = [
        "curl", "-sS", "--compressed", "--max-time", str(timeout),
        "-o", tmp, "-w", "%{http_code}\t%{content_type}\t%{time_total}",
    ]
    for key, value in headers.items():
        args += ["-H", f"{key}: {value}"]
    args.append(url)

    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout + 15)
        meta = (proc.stdout or "").split("\t")
        status = int(meta[0]) if meta and meta[0].isdigit() else 0
        ctype = meta[1] if len(meta) > 1 else ""
        elapsed = float(meta[2]) if len(meta) > 2 and meta[2].replace(".", "", 1).isdigit() else 0.0
        with open(tmp, "rb") as fh:
            body = fh.read()
        err = proc.stderr.strip() or None if status == 0 else None
        return Result(url, status, body, ctype, elapsed, error=err)
    except Exception as exc:
        return Result(url, 0, b"", "", 0.0, error=str(exc))
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="fetch a single endpoint id, e.g. I04")
    ap.add_argument("--pace", type=float, default=PACE,
                    help="seconds to sleep before each request")
    args = ap.parse_args()

    scanned_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []

    for eid, path, params, desc, category in ENDPOINTS:
        if args.only and args.only != eid:
            continue

        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{HOST}{path}?{query}"
        print(f"[{eid}] GET {path} pace={args.pace}s")

        import time
        time.sleep(args.pace)
        res = curl_get(url, IDX_HEADERS)
        state = status_label(res)
        sample = f"samples/idx/{eid}__{path.rstrip('/').split('/')[-1]}.json"

        if res.status == 200 and res.is_json:
            n = save(res, os.path.join(ROOT, sample), meta={
                "id": eid, "url": url, "status": res.status, "scanned_at": scanned_at,
                "description": desc, "category": category, "params": params,
            })
            print(f"      active  {n} bytes -> {sample}")
            sample_rel = sample
        else:
            sample_rel = None
            note = "Cloudflare challenge" if res.is_challenge else res.error or ""
            print(f"      {state}  {note}")

        fields = []
        if res.status == 200 and res.is_json:
            try:
                payload = res.json()
                node = payload.get("data") if isinstance(payload, dict) else payload
                if isinstance(node, list) and node and isinstance(node[0], dict):
                    fields = list(node[0].keys())
            except Exception:
                pass

        rows.append({
            "id": eid, "host": "www.idx.co.id", "path": path, "method": "GET",
            "params": params, "description": desc, "category": category,
            "status": state, "http": res.status, "bytes": len(res.body),
            "fields": fields, "sample": sample_rel, "scanned_at": scanned_at,
        })

    manifest = os.path.join(ROOT, "data/idx_endpoints.json")
    if args.only and os.path.exists(manifest):
        with open(manifest, encoding="utf-8") as fh:
            merged = {r["id"]: r for r in json.load(fh)}
        for row in rows:
            merged[row["id"]] = row
        rows = sorted(merged.values(), key=lambda r: r["id"])

    write_json(manifest, rows)
    write_json(os.path.join(ROOT, "data/idx_dead_endpoints.json"),
               [{"path": p, "note": n} for p, n in DEAD])
    ok = sum(1 for r in rows if r["status"] == "active")
    print(f"\n{ok} active / {len(rows)} documented -> data/idx_endpoints.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
