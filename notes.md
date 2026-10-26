# Catatan Recon — IDX, KSEI, SID

Tanggal scan: **2026-10-26** (UTC). Semua status di dokumen ini adalah hasil
permintaan nyata pada tanggal tersebut, bukan asumsi.

---

## 1. Temuan utama: `sid.ksei.co.id` tidak ada

Ini hal pertama yang perlu dikoreksi dari brief. Host yang disebut sebagai
"SID (Sistem Informasi Data) — https://sid.ksei.co.id" **tidak resolve**:

```
$ getent hosts sid.ksei.co.id
(kosong)                      # NXDOMAIN
$ getent hosts sid.ksei.id
(kosong)
```

Enumerasi subdomain lewat certificate transparency (crt.sh, `%.ksei.co.id`)
memberi 26 nama, dan **tidak ada satu pun** `sid.*`:

```
akses.ksei.co.id          easy.ksei.co.id           spek.ksei.co.id
aksesng.ksei.co.id        egkenuat.ksei.co.id       www.online.ksei.co.id
cbest.ksei.co.id          investor.ksei.co.id       online.ksei.co.id
drc.cbest.ksei.co.id      s-invest.ksei.co.id       mail.ksei.co.id
drc.s-invest.ksei.co.id   rsaprime1.ksei.co.id      webmail.ksei.co.id
simulation.cbest.ksei.co.id   rsaprime1-dr.ksei.co.id   cpanel.ksei.co.id
simulation.s-invest.ksei.co.id  training.s-invest.ksei.co.id
testing.s-invest.ksei.co.id     ksei.co.id
```

Status host yang relevan (probe HTTPS langsung):

| Host | Hasil | Keterangan |
|---|---|---|
| `akses.ksei.co.id` | **200** | Portal investor AKSes — dipakai sebagai sumber data SID |
| `easy.ksei.co.id` | 200 | eProxy Voting (e-RUPS) |
| `spek.ksei.co.id` | 200 | e-Securities Registration |
| `investor.ksei.co.id` | koneksi gagal | kemungkinan internal-only |
| `s-invest.ksei.co.id` | koneksi gagal | jaringan internal / terfilter |
| `cbest.ksei.co.id` | koneksi gagal | jaringan internal |
| `online.ksei.co.id` | koneksi gagal | proxy lama, mati |
| `sid.ksei.co.id` | **NXDOMAIN** | tidak pernah ada / sudah dihapus |

**Kesimpulan:** "SID" bukan situs terpisah. Data SID (Single Investor
Identification) disajikan di dua tempat:

1. `www.ksei.co.id/api/investor_demographic/*` — statistik agregat, JSON bersih.
2. `akses.ksei.co.id` — portal AKSes, tempat investor melihat SID sendiri
   (butuh login) dan tempat publik melihat demografi investor per wilayah.

---

## 2. Pola proteksi: dugaan WAF di brief tidak sepenuhnya benar

Brief mengantisipasi KSEI **dan** IDX sama-sama di belakang WAF sehingga butuh
Playwright. Hasilnya berbeda per situs.

### KSEI / AKSes — tanpa WAF

```
$ curl -sI https://www.ksei.co.id/id
server: nginx
x-varnish: 39319510
set-cookie: auth.strategy=local; Path=/; Secure; HttpOnly; SameSite=Strict
```

nginx + Varnish, tidak ada Cloudflare/Incapsula. `curl` biasa berhasil pada
percobaan pertama. Satu-satunya syarat: untuk `/api/*` harus minta JSON.

Tanpa `Accept: application/json`:

```json
{"code": 405, "message": "Backend accept only json communication.", "errors": []}
```

Dengan header itu, semua endpoint mengembalikan `200`.

### IDX — Cloudflare, tapi tetap tanpa browser

Endpoint `/_nuxt/*.js` dan halaman HTML **diblokir** (403 `Just a moment...`).
Namun endpoint data `/primary/*` **lolos** bila header browser lengkap.

Yang menentukan bukan `User-Agent` (itu saja tidak cukup), melainkan trio
`Sec-Fetch-*`:

```bash
# GAGAL -> 403 "Just a moment..."
curl -H "Accept: application/json" \
     "https://www.idx.co.id/primary/StockData/GetSecuritiesStock?start=0&length=3"

# BERHASIL -> 200, 962 emiten
curl -H "Accept: application/json, text/plain, */*" \
     -H "Sec-Fetch-Dest: empty" \
     -H "Sec-Fetch-Mode: cors" \
     -H "Sec-Fetch-Site: same-origin" \
     -H "Referer: https://www.idx.co.id/id/market-data" \
     "https://www.idx.co.id/primary/StockData/GetSecuritiesStock?start=0&length=3"
```

Bukti bahwa origin yang menjawab (bukan cache/edge) terlihat di timing header:

```
server-timing: cfCacheStatus;desc="DYNAMIC"
server-timing: cfEdge;dur=4,cfOrigin;dur=390
cf-cache-status: DYNAMIC
```

**Rate limit.** Ini kendala operasional terbesar. Setelah ±10–15 request dalam
hitungan detik, **seluruh** path (termasuk yang tadinya 200) berubah jadi 403,
dan blokir bertahan beberapa menit. Karena itu:

- `fetch_idx.py` memakai `pace=6.0` (jeda 6 detik antar request) dan `backoff`
  20/40/60 detik saat kena challenge.
- Jangan menjalankan beberapa collector IDX paralel dari IP yang sama.

**Playwright tidak dipakai sama sekali** di repo ini. Alasannya bukan karena
tidak tersedia, tetapi karena tidak dibutuhkan: `curl` + header yang benar sudah
cukup. Ini lebih ringan, deterministik, dan tidak memerlukan unduhan browser
±300 MB.

### Jebakan yang paling memakan waktu: fingerprint TLS, bukan header

Header yang **byte-identik** memberi hasil berbeda tergantung library HTTP-nya:

| Transport | Hasil |
|---|---|
| `curl` | **200**, JSON 130 KB |
| Python `urllib` | **403**, halaman `Just a moment...` |

Ini bukan soal header — headernya sama persis. Cloudflare mem-fingerprint
**handshake TLS/ALPN**: curl bernegosiasi HTTP/2 lewat ALPN dengan ClientHello
yang menyerupai browser, sedangkan `urllib` hanya bicara HTTP/1.1 dengan
ClientHello OpenSSL bawaan. Karena itu `fetch_idx.py` **menjalankan curl sebagai
subprocess**, sementara collector KSEI/AKSes tetap memakai `urllib` (keduanya
tidak peduli).

Konsekuensi praktis: kalau ingin mereplikasi hasil IDX, jangan pakai `requests`
atau `httpx` default — keduanya akan kena challenge yang sama seperti `urllib`.
Pakai curl, atau `curl_cffi` / `httpx` dengan impersonasi TLS.


### Konsekuensi: aset JS IDX tidak terjangkau

`/_nuxt/*.js` tetap 403 walaupun header sudah benar (aturan Cloudflare terpisah
untuk aset statis). Efeknya: nama endpoint IDX **tidak bisa** dibaca dari bundle.
Nama-nama di repo ini diperoleh dengan mem-probe `/primary/` dan membaca
redirect error-nya:

```
302 -> /404.html?aspxerrorpath=/api/StockData/GetStockSummary
```

Artinya `/primary/<X>` dipetakan internal ke `/api/<X>`, dan action yang tidak
ada me-redirect ke 404.html. Cara ini yang mengungkap bahwa controller yang
benar untuk ringkasan perdagangan adalah **`TradingSummary`**, bukan `StockData`.

Endpoint yang terbukti **tidak ada** (semua 302) dicatat di
`data/idx_dead_endpoints.json` supaya tidak perlu diprobe ulang:

`StockData/GetStockSummary`, `StockData/GetIndexList`, `StockData/GetStockTrade`,
`StockData/GetDailyTrading`, `StockData/GetBrokerSummary`,
`StockData/GetTradeSummary`, `TradingSummary/GetIndexList`,
`TradingSummary/GetSectoralSummary`, `ListedCompany/GetDividend`,
`ListedCompany/GetCompanyDividend`, `ListedCompany/GetStockSplit`,
`Dividend/GetDividend`, `Home/GetHome`.

Yang **tidak** berhasil ditemukan dan kemungkinan butuh nama lain:
broker summary per saham (yang ada hanya ringkasan global), daftar dividen,
stock split, dan jadwal bursa.

---

## 3. Arsitektur internal yang terungkap

### KSEI = Nuxt 2 + Laravel

- `__NUXT__` dan `data-server-rendered` ada di HTML → Nuxt 2 (SSR).
- Error validasi berformat Laravel: `{"message":"The given data was invalid.","errors":{"filter.type":["The filter.type field is required."]}}`
- Pagination Laravel: `{"data":[...],"links":{...},"meta":{...}}`
- API di-mount relatif di `/api/`, base URL dikonfigurasi sebagai string kosong
  (`BASE_URL:""`) sehingga selalu same-origin.

### AKSes = React (CRA) + Spring Boot

- `manifest.json` + `main.<hash>.js` + `vendors~main.<hash>.js` → Create React App.
- Bundle memakai `S.server + "service/..."`; `S.server` = `window.location.origin`.
  Jadi API-nya **same-origin**: `https://akses.ksei.co.id/service/...`.
- nginx mem-proxy `/service/*` ke back end Spring Boot di `/api/v1/*`. Terlihat
  dari payload error yang membocorkan path internal:

  ```json
  {"status":500,"path":"/api/v1/demografi/investor"}
  ```

- Karena Spring Boot: error 400 untuk parameter wajib yang hilang
  (`MissingServletRequestParameterException`) dan 405 untuk metode salah.

### IDX = Nuxt 2 + ASP.NET

- Nuxt 2 (`__NUXT__`) di front end, ASP.NET di belakang (`Object moved`,
  `aspxerrorpath`).

---

## 4. Kontrak parameter yang tidak terlihat dari nama endpoint

Tiga endpoint KSEI membalas `422` bila dipanggil tanpa parameter. Isi pesan
validasinya membocorkan nama field, dan bundle JS membocorkan **tipe nilainya** —
yang tidak bisa ditebak dari pesan error:

| Endpoint | Parameter wajib | Format nilai |
|---|---|---|
| `/api/investor_demographic/sid_growths` | `filter[type]`, `filter[three_years_data]` | `filter[type]` = **nama seri**, bukan UUID. `filter[three_years_data]` = tanggal format `"October 2026"` (English `monthYear`) |
| `/api/investor_demographic/mutual_assets` | `filter[four_years_data]` | sama: `"October 2026"` |

Jebakan yang sempat memakan waktu:

1. `/api/investor_demographic/sid_growths/types` mengembalikan `key` berupa UUID
   **dan** `name`. Yang dipakai server adalah **`name`**:

   ```js
   v = c.map(t => "string" == typeof t ? t : t.name || t.type || t)
   ```

   Mengirim UUID menghasilkan `503` (bukan 422), karena server gagal memproses.

2. Format tanggal harus `"October 2026"`. `"2026-10"` menghasilkan `503`.
   Lokalisasi juga berpengaruh: `locale=id` mengharapkan `"Oktober 2026"`.

3. Parameter berspasi **harus** di-encode (`urlencode`). Menggabung query string
   manual dengan spasi mentah membuat request gagal sebelum keluar.

Contoh yang benar:

```bash
curl -s -H "Accept: application/json" -G \
  "https://www.ksei.co.id/api/investor_demographic/sid_growths" \
  --data-urlencode "locale=en" \
  --data-urlencode "filter[type]=Number of Capital Market Investors" \
  --data-urlencode "filter[three_years_data]=October 2026"
```

---

## 5. Endpoint yang butuh login (dicatat, tidak dipanggil)

Rute-rute ini ditemukan di bundle AKSes tapi berada di belakang login investor
atau staf. **Tidak pernah** dipanggil oleh collector.

| Prefix | Jumlah rute | Peruntukan |
|---|---|---|
| `/service/orchid/` | 93 | portofolio, sub-rekening, fund separation |
| `/service/myportofolio/` | 48 | tampilan portofolio investor |
| `/service/myaccount/` | 25 | pengaturan akun, keamanan |
| `/service/emiten-area/` | 16 | pelaporan area emiten (login emiten) |
| `/service/admin-mgt/` | 11 | back-office staf KSEI |

Selain itu ada `POST /service/auth/login`, `POST /service/auth/captcha`, dan
alur `forgot-password`/`registration`. Semuanya butuh kredensial atau captcha —
di luar cakupan, tidak disentuh.

Pada KSEI: `GET /api/auth/user`, `POST /api/auth/login`, `POST /api/auth/logout`
— sesi berbasis cookie `auth.strategy=local`.

---

## 6. Endpoint yang tidak stabil

| Endpoint | Gejala | Dugaan |
|---|---|---|
| `akses /service/demografi/investor` | `500` untuk `city=&province=` maupun kode wilayah | data sumber kosong / bug back end |
| `akses /service/demografi/age` | `500` dengan filter, `200` + `data:[]` untuk `province=3100` | data per wilayah tidak terisi |
| `akses /service/demografis/occupation` | `500 RecoverableDataAccessException` (POST) | koneksi DB back end |
| `akses /service/beidatafeed/pusat-informasi/*` | `502 Bad Gateway` dari nginx | layanan upstream mati |
| `ksei /api/static_stocks` | 503 sesekali | cache Varnish miss + origin lambat |

`/service/demografis/gender?id=` (id kosong) justru **berhasil** dan
mengembalikan seluruh dataset nasional (552 wilayah). Jadi untuk demografi
per wilayah, endpoint itu yang paling berguna.

---

## 7. Catatan teknis lingkungan

- **IPv6 tidak berfungsi** di sandbox ini: `getaddrinfo(AF_UNSPEC)` gagal dengan
  `EAI_AGAIN` sementara `AF_INET` berhasil. `scripts/common.py` memaksa IPv4
  agar `urllib` tidak gagal acak.
- `requests` dan `playwright` **tidak terpasang**, jadi seluruh collector memakai
  `urllib` dari stdlib. Tidak perlu `pip install`.
- DNS sempat intermiten (`EAI_AGAIN` sesekali). Collector menganggap status `0`
  sebagai transient dan mengulang.
- `/tmp` di sandbox ini bertipe tmpfs dan **hilang saat reboot**. Simpan hasil
  kerja di luar `/tmp`; repo ini sengaja dibuat di `/root`.

---

## 8. Saran lanjutan

1. **Verifikasi ulang berkala.** Endpoint internal bisa berubah tanpa notice.
   Jalankan `fetch_*.py` lalu `build_docs.py`; diff manifest untuk melihat
   endpoint yang mati.
2. **Jangan scrape agresif.** Untuk IDX, satu request per 6 detik sudah cukup
   untuk menarik seluruh daftar emiten (962 baris sekali request). Tidak ada
   alasan memaginasi.
3. **Alternatif resmi** bila butuh data produksi: IDX menyediakan data pasar
   berlisensi, dan KSEI menerbitkan statistik bulanan resmi dalam bentuk
   zip/xlsx (lihat `K16`/`K15` — endpoint itu mengembalikan tautan
   `storage/Download/*.zip` bertanggal).
4. Untuk data SID per investor (bukan agregat), tidak ada jalur publik. Itu
   memang hanya bisa diakses pemilik SID lewat login AKSes.
