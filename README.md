# mapping-ksei-idx

Pemetaan endpoint JSON publik milik tiga sistem pasar modal Indonesia:

| Sistem | Host | Status recon |
|---|---|---|
| **KSEI** (Kustodian Sentral Efek Indonesia) | `www.ksei.co.id` | 31 endpoint aktif, tanpa WAF |
| **AKSes / SID** (portal investor) | `akses.ksei.co.id` | 6 endpoint publik + 328 rute terdaftar |
| **IDX** (Bursa Efek Indonesia) | `www.idx.co.id` | di belakang Cloudflare, lihat catatan |

> **Temuan penting:** `https://sid.ksei.co.id` — host yang disebut di brief — **tidak ada**
> di DNS (NXDOMAIN). Tidak ada subdomain `sid`. Data SID/investor sebenarnya disajikan
> lewat `www.ksei.co.id/api/investor_demographic/*` dan portal `akses.ksei.co.id`.
> Detail di [`notes.md`](notes.md).

---

## Isi repo

```
.
├── README.md                  # dokumen ini
├── ENDPOINTS.md               # tabel lengkap semua endpoint + status
├── notes.md                   # temuan, pola header, endpoint terproteksi
├── docs/
│   ├── ksei_endpoints.md      # blok detail per endpoint KSEI
│   ├── sid_endpoints.md       # blok detail per endpoint AKSes/SID
│   └── idx_endpoints.md       # blok detail per endpoint IDX
├── samples/                   # respons mentah, apa adanya (tidak diedit)
│   ├── ksei/  sid/  idx/
├── data/
│   ├── ksei_endpoints.json    # manifest hasil scan (sumber kebenaran docs)
│   ├── sid_endpoints.json
│   ├── idx_endpoints.json
│   ├── idx_dead_endpoints.json
│   └── csv/                   # flatten tabel -> CSV
└── scripts/
    ├── common.py              # helper HTTP (retry, backoff, header profile)
    ├── fetch_ksei.py
    ├── fetch_sid.py
    ├── fetch_idx.py
    ├── build_docs.py          # regenerasi ENDPOINTS.md + docs/ dari manifest
    └── export_csv.py          # samples/*.json -> data/csv/*.csv
```

Setiap sample punya sidecar `<nama>.json.meta.json` berisi URL persis, parameter,
timestamp scan, dan status HTTP — jadi setiap angka di dokumentasi bisa diaudit.

---

## Cara pakai

Tidak ada dependency pihak ketiga. Python 3.10+ saja (modul `urllib`).

```bash
python3 scripts/fetch_ksei.py     # ~15 detik, tanpa WAF
python3 scripts/fetch_sid.py      # ~20 detik
python3 scripts/fetch_idx.py      # LAMBAT: 6 detik/req + backoff Cloudflare
python3 scripts/build_docs.py     # regenerasi ENDPOINTS.md + docs/
python3 scripts/export_csv.py     # samples -> data/csv/
```

Ambil satu endpoint saja (hasil di-merge ke manifest, bukan menimpa):

```bash
python3 scripts/fetch_ksei.py --only K07
```

Contoh membaca data:

```python
import json
d = json.load(open("samples/ksei/K07__investor-sid-sid-growths.json"))
for row in d["data"]:
    print(row["month"], row["asset_local"])
```

---

## Pola akses yang ditemukan

**KSEI / AKSes** — nginx + Varnish, tanpa WAF. Cukup `User-Agent` wajar. Untuk
`/api/*` **wajib** `Accept: application/json`; tanpa itu balasannya
`405 {"message":"Backend accept only json communication."}`. Tidak ada token,
signature, atau API key.

**IDX** — Cloudflare. Tiga syarat agar dapat JSON tanpa headless browser:

1. Header browser lengkap **termasuk** `Sec-Fetch-Dest`, `Sec-Fetch-Mode`,
   `Sec-Fetch-Site`. Tanpa ketiganya → halaman `Just a moment...` (HTTP 403).
2. **Transport yang tepat.** Header identik pun, `curl` dapat 200 sementara
   Python `urllib`/`requests` dapat 403 — Cloudflare mem-fingerprint handshake
   TLS/ALPN, dan hanya curl yang bernegosiasi HTTP/2 seperti browser. Karena itu
   `fetch_idx.py` memanggil curl sebagai subprocess.
3. Sabar. IDX membatasi laju sangat agresif; burst belasan request membuat IP
   diblokir beberapa menit. Collector memakai jeda 8 detik.

Playwright **tidak diperlukan** untuk ketiga situs. Ini berbeda dari dugaan awal
di brief — lihat [`notes.md`](notes.md) untuk bukti header per header.

---

## Etika & batasan

Repo ini berisi **pemetaan endpoint publik dan contoh respons**, bukan alat
serangan dan bukan data pribadi.

- Hanya endpoint yang dapat diakses **tanpa autentikasi** yang diambil. Rute yang
  butuh login (portofolio investor, area emiten, back-office) **dicatat namanya
  saja** dan tidak pernah dipanggil.
- Tidak ada kredensial, cookie sesi, token, atau data identitas investor
  perseorangan di repo ini. Data demografi bersifat **agregat per wilayah**.
- Semua request memakai jeda (rate limit) dan `User-Agent` yang jujur. Tidak ada
  upaya melewati autentikasi, menebak kredensial, atau mengakali pembatasan akses
  selain menyesuaikan header agar setara browser biasa.
- Sebelum memakai untuk produksi, **baca Terms of Service** masing-masing situs
  dan pertimbangkan izin tertulis. Endpoint internal dapat berubah atau ditutup
  tanpa pemberitahuan; skema di sini mencerminkan kondisi saat tanggal scan.
- Data pasar modal yang disajikan IDX/KSEI adalah informasi publik, tetapi
  redistribusi masif dapat melanggar ketentuan lisensi data bursa.

Gunakan untuk riset, jurnalisme data, atau integrasi internal yang sah.
