#!/usr/bin/env python3
"""Generate ENDPOINTS.md and docs/*.md from the collected manifests.

The manifests in data/ are the single source of truth: every table row here was
produced by an actual request, so the docs cannot drift from the samples.

Run after any of the fetch_*.py collectors:  python3 scripts/build_docs.py
"""

from __future__ import annotations

import json
import os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATUS_ICON = {
    "active": "✅ aktif",
    "needs-params": "⚠️ butuh parameter",
    "authenticated": "🔒 perlu login",
    "forbidden": "⛔ ditolak",
    "waf-challenge": "⛔ WAF challenge",
    "dead": "❌ mati",
    "unreachable": "❌ tak terjangkau",
}

# Where each endpoint family was discovered. Kept as ranges so it stays readable.
KSEI_SOURCE = {
    "site-meta": "bundle `/_nuxt/*.js` halaman https://www.ksei.co.id/id",
    "reference": "bundle `/_nuxt/*.js` halaman https://www.ksei.co.id/id",
    "investor/sid": "https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik",
    "ownership": "https://www.ksei.co.id/id/publikasi/data-dan-statistik/kepemilikan-efek",
    "bulk-download": "https://www.ksei.co.id/id/publikasi/data-dan-statistik/statik-efek",
    "account": "bundle `/_nuxt/*.js` halaman https://www.ksei.co.id/id",
    "graph": "https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik",
    "auth": "bundle `/_nuxt/*.js` halaman https://www.ksei.co.id/id",
}


def load(name):
    path = os.path.join(ROOT, "data", name)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def qs(params) -> str:
    if not params:
        return "—"
    return "&".join(f"`{k}`={v!r}" if v else f"`{k}`=" for k, v in params.items())


def fields_from_sample(sample_rel, limit=16):
    """Derive response fields from the stored sample, not from the manifest.

    Some payloads are a bare object (IDX company detail) rather than
    {"data": [...]}, so deriving here keeps the docs honest for every shape.
    """
    if not sample_rel:
        return []
    path = os.path.join(ROOT, sample_rel)
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
    except Exception:
        return []

    node = payload
    if isinstance(payload, dict) and "data" in payload:
        node = payload["data"]

    if isinstance(node, list):
        if not node:
            return []
        first = node[0]
        if isinstance(first, dict):
            return list(first.keys())[:limit]
        return []
    if isinstance(node, dict):
        return list(node.keys())[:limit]
    return []


def table(rows, source_map=None, show_source=True):
    head = "| # | Host | Path | Method | Parameter | Kategori | Status |"
    sep = "|---|---|---|---|---|---|---|"
    out = [head, sep]
    for r in rows:
        src = source_map.get(r.get("category"), "—") if source_map else "—"
        line = (
            f"| {r['id']} | `{r['host']}` | `{r['path']}` | {r['method']} | {qs(r.get('params'))} "
            f"| {r.get('category', '—')} | {STATUS_ICON.get(r['status'], r['status'])} |"
        )
        out.append(line)
    if show_source and source_map:
        out.append("")
        out.append("<details><summary>Sumber penemuan per kategori</summary>")
        out.append("")
        for cat, src in source_map.items():
            out.append(f"- **{cat}** — {src}")
        out.append("")
        out.append("</details>")
    return "\n".join(out)


def detail(rows, header):
    """Per-endpoint blocks in the format requested by the brief."""
    out = [f"# {header}", ""]
    for r in rows:
        out.append(f"### [{r['id']}] {r['method']} https://{r['host']}{r['path']}")
        out.append("")
        out.append(f"- **Deskripsi**: {r.get('description', '—')}")
        out.append(f"- **Parameter**: {qs(r.get('params'))}")
        fields = ", ".join(f"`{f}`" for f in fields_from_sample(r.get("sample"))) or "—"
        out.append(f"- **Response fields**: {fields}")
        sample = r.get("sample")
        out.append(f"- **Contoh**: {'lihat `' + sample + '`' if sample else 'tidak ada (endpoint tidak mengembalikan data)'}")
        out.append(f"- **Status**: {STATUS_ICON.get(r['status'], r['status'])} (per {r.get('scanned_at', '—')})")
        if r.get("http"):
            out.append(f"- **HTTP**: {r['http']} · **Ukuran**: {r['bytes']} byte")
        out.append(f"- **Sumber ditemukan**: {r.get('source', '—')}")
        out.append("")
        out.append("---")
        out.append("")
    return "\n".join(out)


def main() -> int:
    ksei = load("ksei_endpoints.json")
    sid = load("sid_endpoints.json")
    idx = load("idx_endpoints.json")

    for r in ksei:
        r["source"] = KSEI_SOURCE.get(r.get("category"), "—")
    for r in sid:
        r["source"] = ("bundle `https://akses.ksei.co.id/main.9351f7724eaebe22ca45.js`"
                       if not r.get("category") == "authenticated"
                       else "bundle `main.<hash>.js`, hanya terlihat sebagai rute SPA")
    for r in idx:
        r["source"] = ("https://www.idx.co.id/id/market-data + probe `/primary/`"
                       if r.get("status") != "dead" else "probe `/primary/` (tidak ada)")

    # ---------- ENDPOINTS.md ----------
    lines = [
        "# ENDPOINTS.md",
        "",
        "Daftar lengkap endpoint publik yang berhasil dipetakan dan **diverifikasi dengan",
        "permintaan nyata**. Setiap baris punya contoh respons mentah di `samples/`.",
        "",
        f"**Total didokumentasikan: {len(ksei) + len(sid) + len(idx)}** "
        f"(KSEI {len(ksei)}, AKSes/SID {len(sid)}, IDX {len(idx)})",
        "",
        "Legenda status: ✅ aktif · ⚠️ butuh parameter khusus · 🔒 perlu login · ❌ mati/diblokir",
        "",
        "## Ringkasan per situs",
        "",
        "| Situs | Endpoint didokumentasikan | Aktif |",
        "|---|---|---|",
    ]
    for name, rows in (("KSEI (`www.ksei.co.id`)", ksei),
                       ("AKSes / SID (`akses.ksei.co.id`)", sid),
                       ("IDX (`www.idx.co.id`)", idx)):
        active = sum(1 for r in rows if r["status"] == "active")
        lines.append(f"| {name} | {len(rows)} | {active} |")

    lines += ["", "## KSEI", "", table(ksei, KSEI_SOURCE), "",
              "## AKSes / SID", "", table(sid), "",
              "## IDX", "", table(idx), ""]

    lines += [
        "## Catatan pembacaan",
        "",
        "- Semua endpoint KSEI/AKSes menerima `User-Agent` umum; tidak ada signature, token, atau",
        "  API key. Yang wajib hanya header `Accept: application/json` untuk `/api/*`.",
        "- Endpoint IDX **mewajibkan** header `Sec-Fetch-Dest/Mode/Site`. Tanpa itu Cloudflare",
        "  mengembalikan halaman challenge `Just a moment...` (HTTP 403), bukan JSON.",
        "- IDX membatasi laju secara agresif. Collector memakai jeda 6 detik dan backoff 20–60 detik.",
        "",
        "Detail per situs: [`docs/ksei_endpoints.md`](docs/ksei_endpoints.md) ·",
        "[`docs/sid_endpoints.md`](docs/sid_endpoints.md) ·",
        "[`docs/idx_endpoints.md`](docs/idx_endpoints.md)",
        "",
    ]
    with open(os.path.join(ROOT, "ENDPOINTS.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    # ---------- per-site docs ----------
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    with open(os.path.join(ROOT, "docs/ksei_endpoints.md"), "w", encoding="utf-8") as fh:
        fh.write(detail(ksei, "KSEI — endpoint JSON publik (`www.ksei.co.id`)"))
    with open(os.path.join(ROOT, "docs/sid_endpoints.md"), "w", encoding="utf-8") as fh:
        fh.write(detail(sid, "AKSes / SID — endpoint publik (`akses.ksei.co.id`)"))
    with open(os.path.join(ROOT, "docs/idx_endpoints.md"), "w", encoding="utf-8") as fh:
        fh.write(detail(idx, "IDX — endpoint JSON publik (`www.idx.co.id`)"))

    # ---------- console summary ----------
    for name, rows in (("ksei", ksei), ("sid", sid), ("idx", idx)):
        print(f"{name:5} {dict(Counter(r['status'] for r in rows))} total={len(rows)}")
    print("wrote ENDPOINTS.md + docs/{ksei,sid,idx}_endpoints.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
