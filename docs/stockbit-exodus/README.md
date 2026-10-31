# Referensi API Stockbit Exodus

**Dokumen hasil reverse engineering statis + verifikasi live**

| Item | Nilai |
|---|---|
| Versi dokumen | 1.1 |
| Tanggal | 31 Oktober 2026 |
| Cakupan | `https://exodus.stockbit.com`, `https://exodus.api.stockbit.com` |
| Metode | Analisis bundle Next.js `v3.54.10` (339 chunk JS, ±16 MB) dan `v3.54.5` (306 file JS), capture runtime 25+ halaman, probing live terautentikasi |
| Sumber bukti | 132 respons runtime, 107 path unik, 90+ respons probe tersimpan, modul service yang sudah di-beautify |
| Fokus tambahan | Profil perusahaan, pemegang saham, UBO, komposisi kepemilikan, jumlah pemegang saham, anak perusahaan, katalog konglomerasi |
| Sifat | Read-only. Tidak ada order, trade, posting, komentar, atau mutasi watchlist yang dijalankan |
| Bahasa | Indonesia, dengan nama endpoint/field tetap bahasa Inggris |

> **Peringatan**
> - Dokumen ini **tidak** memuat access token, refresh token, cookie, email, nomor telepon, atau data pribadi pemilik akun.
> - Beberapa endpoint tulis (POST/PUT/DELETE) hanya didokumentasikan dari kode dan **tidak dieksekusi**. Jalankan hanya dengan izin eksplisit.
> - Rate limit yang diamati: **10 request/detik**. Gunakan ≤ 8 req/s dan backoff saat menerima 429.
> - Data contoh diambil pada 23–31 Oktober 2026 dan dapat berubah.

---

## Daftar Isi

- [0. Ringkasan](#0-ringkasan)
- [1. Arsitektur dan matriks host](#1-arsitektur-dan-matriks-host)
- [2. Autentikasi dan sesi](#2-autentikasi-dan-sesi)
- [3. Konvensi umum API](#3-konvensi-umum-api)
- [4. Peta endpoint per domain](#4-peta-endpoint-per-domain)
- [5. Referensi endpoint](#5-referensi-endpoint)
  - [5.1 Auth dan session](#51-auth-dan-session)
  - [5.2 Company / emitten](#52-company--emitten)
  - [5.3 Metadata emiten](#53-metadata-emiten)
  - [5.4 Harga, market, orderbook, chart](#54-harga-market-orderbook-chart)
  - [5.5 Order flow dan broker](#55-order-flow-dan-broker)
  - [5.6 Fundamental dan analyst](#56-fundamental-dan-analyst)
  - [5.7 Corporate action](#57-corporate-action)
  - [5.8 Insider dan shareholder](#58-insider-dan-shareholder)
  - [5.9 Screener](#59-screener)
  - [5.10 Valuation](#510-valuation)
  - [5.11 Watchlist](#511-watchlist)
  - [5.12 Search](#512-search)
  - [5.13 Stream / social](#513-stream--social)
  - [5.14 User, notification, chat, discovery](#514-user-notification-chat-discovery)
  - [5.15 WebSocket](#515-websocket)
  - [5.16 Akademi, paywall, research, badge](#516-akademi-paywall-research-badge)
  - [5.17 Katalog konglomerasi (KONGLO)](#517-katalog-konglomerasi-konglo)
- [6. Enumerasi dan konstanta](#6-enumerasi-dan-konstanta)
- [7. Katalog error](#7-katalog-error)
- [8. Rate limit, header, dan caching](#8-rate-limit-header-dan-caching)
- [9. Endpoint bermasalah dan batasan](#9-endpoint-bermasalah-dan-batasan)
- [10. Contoh klien Python minimal](#10-contoh-klien-python-minimal)
- [11. Catatan pengujian dan lampiran](#11-catatan-pengujian-dan-lampiran)
- [12. Peta cepat menu profil perusahaan dan group konglomerasi](#12-peta-cepat-menu-profil-perusahaan-dan-group-konglomerasi)
- [Lampiran A — Inventaris endpoint](#lampiran-a--inventaris-endpoint-yang-ter-capture)
- [Lampiran B — Checklist penggunaan](#lampiran-b--checklist-penggunaan)
- [Lampiran C — Riwayat dokumen](#lampiran-c--riwayat-dokumen)

---

## 0. Ringkasan

`exodus.stockbit.com` dan `exodus.api.stockbit.com` adalah **backend yang sama**. Keduanya mengembalikan data identik untuk path yang sama; perbedaannya hanya pada header:

| Aspek | `exodus.stockbit.com` | `exodus.api.stockbit.com` |
|---|---|---|
| Dipakai oleh | Web app (`baseURL` client axios) | Client alternatif / gateway publik |
| `Cache-Control` | `no-store` | `public, max-age=1` |
| Header rate limit | Ada | Ada, lebih konsisten terlihat |
| Data | Sama | Sama |
| CORS | `Access-Control-Allow-Origin: https://stockbit.com` | Sama |

API ini adalah **gRPC-gateway** yang mengekspos HTTP/JSON:

```
grpc-metadata-content-type: application/grpc
grpc-metadata-date: Fri, 23 Oct 2026 04:45:44 GMT
```

Respons hampir selalu berbentuk `{ "message": ..., "data": ... }`. Error menggunakan `{ "message": ..., "error_type": ... }`, kadang dengan array `errors`.

**Domain data yang terpetakan:**

| Domain | Prefix | Jumlah endpoint terverifikasi |
|---|---|---|
| Auth/session | `/login/*`, `/logout` | 10 |
| Company/emitten | `/emitten*` | 19 |
| Metadata emiten | `/emitten-metadata/*` | 3 |
| Harga & market | `/company-price-feed/*`, `/orderbook/*`, `/charts/*`, `/chartbit/*` | 18 |
| Order flow & broker | `/order-trade/*`, `/marketdetectors/*`, `/findata-view/marketdetectors/*` | 7 |
| Fundamental & analyst | `/findata-view/company/*`, `/keystats/*`, `/analyst-ratings/*` | 5 |
| Corporate action | `/corpaction/*` | 4 |
| Insider & shareholder | `/insider/*` | 7 |
| Screener | `/screener/*` | 11 |
| Valuation | `/valuation/*` | 8 |
| Watchlist | `/watchlist/*` | 24 |
| Search | `/search` | 1 |
| Stream/social | `/stream/*` | 30+ |
| User/notif/chat | `/user/*`, `/notification/*`, `/chat/*` | 25+ |
| Akademi/paywall | `/academy/*`, `/paywall/*` | 8 |

**Temuan penting:**

1. Access token berumur **24 jam**, refresh token **7 hari**.
2. Refresh token **dirotasi** setiap kali dipakai. Memakai refresh token yang sama dua kali akan gagal. Ini penting untuk SMtracker: hanya satu proses yang boleh melakukan refresh.
3. `credentialStorage` adalah cookie berisi JSON access+refresh; web app dan SMtracker membacanya.
4. Sebagian besar angka harga dikirim sebagai **string**, sedangkan chart mengirim **number**. Nilai agregat sering berbentuk `{raw, formatted}`.
5. Beberapa endpoint memakai nama parameter yang tidak konsisten: `market_board=MARKET_TYPE_REGULER` pada broker activity, `market_type=MARKET_TYPE_REGULAR` pada foreign-domestic, `ids` (lowercase) pada classification company.
6. Endpoint `/emitten/v2/.../info` dan `/fin-items` **rusak** (500) meskipun dipanggil oleh aplikasi web. Yang berfungsi adalah `/emitten/{symbol}/info` dan `/emitten/v2/.../info-type`.
7. `/partnership/*` dilindungi dan mengembalikan **403 Cloudflare HTML**, bukan JSON.
8. Rate limit 10 req/s terlihat dari header `x-rate-limit-limit`; tidak ada dokumentasi resmi.
9. **Satu panggilan `GET /emitten/{symbol}/profile`** memasok hampir seluruh tab profil perusahaan: latar belakang, direksi, pemegang saham ≥1% (lengkap dengan investor ID), jumlah pemegang saham 24 bulan, UBO, anak perusahaan, dan klasifikasi.
10. **Group konglomerasi** punya dua jalur: pencarian insider (`/search` → `/ownership?investor=`) dan katalog KONGLO (`/emitten/catalog` → `/emitten/catalog/{code}/company`). Keduanya tidak selalu berisi himpunan emiten yang sama.
11. Lihat [bagian 12](#12-peta-cepat-menu-profil-perusahaan-dan-group-konglomerasi) untuk peta menu → endpoint yang ringkas.

---

## 1. Arsitektur dan matriks host

### 1.1 Konstanta host dari bundle

Diambil dari modul `10276` (`auth_10276.js`):

| Konstanta | URL | Fungsi |
|---|---|---|
| `_O` | `https://stockbit.com` | Origin web |
| `q7` | `https://exodus.stockbit.com` | **Base URL utama web app** |
| `lP` | `https://exodus.api.stockbit.com` | Alias API/gateway |
| `CT` | `https://api.stockbit.com/v2.5` | REST legacy |
| `kg` | `https://api-sekuritas.stockbit.com` | Registrasi/sekuritas |
| `cu` | `https://carina.stockbit.com` | Carina (trading) |
| `C6` | `https://carina.api.stockbit.com` | Carina API |
| `Cb` | `https://trading.masonline.id` | Masonline |
| `or` | `https://academy.stockbit.com` | Academy |
| `PP` | `https://terminal.stockbit.com` | Terminal |

WebSocket:

| Host | Keterangan |
|---|---|
| `wss://wssocial.stockbit.com?wskey=<key>` | Stream sosial (protobuf biner) |
| `wss://wss-jkt.trading.stockbit.com/ws` | Trading; subprotocol `web`; opsional `?type=chart` |
| `wss://ws-gen.stockbit.com/v1` | General/market socket (belum dipetakan detail) |

### 1.2 Alur request

```
Browser / client
   │  HTTPS + JWT
   ▼
Cloudflare (server: cloudflare)
   │
   ▼
CloudFront (via: ...cloudfront.net, x-amz-cf-pop: SIN3-P3)
   │
   ▼
gRPC-gateway (grpc-metadata-*)
   │
   ▼
Service exodus (JSON)
```

Header yang membuktikan jalur ini:

```
Server: cloudflare
Via: 1.1 723bb817ce69e5e7ddfa4c771dc46bc4.cloudfront.net (CloudFront)
x-amz-cf-id: ...
x-amz-cf-pop: SIN3-P3
x-cache: MISS
CF-Cache-Status: DYNAMIC
grpc-metadata-content-type: application/grpc
sb-request-id: 1-6adae678-1dd897b66dd623253ade7d2d
```

`sb-request-id` berguna untuk troubleshooting; sertakan saat melaporkan error ke Stockbit.

### 1.3 Perbedaan host yang perlu diketahui

- `exodus.stockbit.com` mengembalikan `Cache-Control: no-store`.
- `exodus.api.stockbit.com` mengembalikan `Cache-Control: public, max-age=1` untuk sebagian endpoint.
- Keduanya mengembalikan `Access-Control-Allow-Methods: GET, OPTIONS` dan `Access-Control-Allow-Origin: https://stockbit.com`.
- Untuk endpoint tulis, browserkemungkinan memakai host yang sama; namun CORS `GET, OPTIONS` menunjukkan preflight POST tidak diizinkan dari origin web. Praktiknya, aplikasi web melakukan POST ke `exodus.stockbit.com` dan berhasil (kemungkinan karena `Origin` same-site atau ada pengecualian). Untuk klien non-browser, CORS tidak relevan.

---

## 2. Autentikasi dan sesi

### 2.1 Login web v6 (dipakai Stockbit web & SMtracker)

**Endpoint**

```http
POST https://exodus.stockbit.com/login/v6/username
Content-Type: application/json
Origin: https://stockbit.com
Referer: https://stockbit.com/
```

**Body**

```json
{
  "user": "<email-atau-username>",
  "password": "<password>",
  "recaptcha_token": "<token-recaptcha>",
  "recaptcha_version": "<versi>",
  "player_id": "<player-id-perangkat>"
}
```

**Catatan implementasi dari bundle:**

- Login memakai client `forGuest` dengan `withCredentials: true`.
- Endpoint login termasuk dalam himpunan `CE = {"/login/v6/username", "/login/v6/social"}`; untuk endpoint ini client **tidak** mengirim `Authorization`, tetapi mengirim cookie (`withCredentials`).
- Jika URL memiliki query `force_challenge=1`, client menambahkan header `X-Force-Challenge: true`.
- `player_id` berasal dari cookie/perangkat dan dipakai untuk verifikasi perangkat baru.
- Respons login **tidak** di-capture pada sesi ini (login dilakukan via Playwright). Yang diamati: setelah login berhasil, server menetapkan cookie `credentialStorage` yang berisi access + refresh token, dan aplikasi menyimpan sebagian state di localStorage/Redux Persist.

**Alur perangkat baru**

Jika akun belum mengenal perangkat, Stockbit meminta persetujuan di aplikasi mobile:

```http
POST /login/v6/new-device/verify
```

Payload berisi token verifikasi dari notifikasi aplikasi. Pada sesi pengujian, langkah ini diselesaikan manual oleh pemilik akun (approve device).

**Login sosial**

```http
POST /login/v6/social
```

Body mengikuti penyedia (Google/Apple/Facebook) dan menghasilkan sesi yang sama. Detail body tidak di-capture.

### 2.2 Login alternatif (legacy/server-side)

Endpoint ini ditemukan di modul `21623` dan dipakai untuk alur server-side/legacy:

| Method | Path | Body |
|---|---|---|
| POST | `/login/v3/username/browser` | `{user, password, verification_token, recaptcha_version, player_id}` |
| POST | `/login/v4/facebook` | `{fb_userid, fb_token, player_id}` |
| POST | `/login/v4/google` | `{google_user_id, google_id_token, player_id}` |
| POST | `/login/v4/recovery/init` | `{user}` (inisiasi reset) |
| POST | `/login/v4/recovery/complete` | `{user_id, token, password, confirm_password}` (indikasi) |

> Body recovery diambil dari pola kode; nilai pasti dapat berbeda. Tidak diuji live.

### 2.3 Refresh token

**Endpoint**

```http
POST https://exodus.api.stockbit.com/login/refresh
Authorization: Bearer <refresh_token>
Content-Type: application/json
```

Body **kosong** (`null`). Pada host `exodus.api`, request memakai `withCredentials: true`.

**Respons (200)**

```json
{
  "message": "You have been successfully refresh token",
  "data": {
    "access": {
      "token": "<access_jwt>",
      "expired_at": "2026-10-24T04:21:30Z"
    },
    "refresh": {
      "token": "<refresh_jwt>",
      "expired_at": "2026-10-30T04:21:30Z"
    }
  }
}
```

**Aturan rotasi**

- Refresh token **selalu berubah** setiap refresh.
- Refresh token lama langsung tidak valid.
- Jika dua proses melakukan refresh bersamaan dengan token yang sama, salah satu akan gagal (401).
- Simpan pasangan baru secara atomik sebelum memakai access token baru.

**Masa hidup**

| Token | Lifetime | Contoh `iat` → `exp` |
|---|---|---|
| Access | 24 jam | 2026-10-23T04:21:30Z → 2026-10-24T04:21:30Z |
| Refresh | 168 jam (7 hari) | 2026-10-23T04:21:30Z → 2026-10-30T04:21:30Z |

### 2.4 Struktur JWT

Access token:

```json
{
  "iss": "STOCKBIT",
  "ver": "v1",
  "iat": 1792700490,
  "nbf": 1792700490,
  "exp": 1792786890,
  "jti": "<uuid>",
  "data": {
    "uid": "<user-id>",
    "use": "<username>",
    "ema": "<email>",
    "ful": "<nama>",
    "ses": "<session-id>",
    "dvc": "<device-id>",
    "cou": "<country>"
  }
}
```

Refresh token memiliki claim tambahan `data.typ`.

> Jangan decode JWT di klien publik untuk menampilkan data pribadi. Klaim `ema`, `ful`, dan `use` bersifat sensitif.

### 2.5 Logout

```http
POST https://exodus.stockbit.com/logout
Authorization: Bearer <access_token>
Content-Type: application/json
```

Body `null`. Respons tidak di-capture (tidak dieksekusi agar sesi tidak berakhir). Dari kode, logout dipanggil dengan access token dan kegagalan diabaikan (best-effort).

Client axios **tidak** melakukan refresh-retry untuk `/logout` (dikecualikan secara eksplisit).

### 2.6 Header request

**Wajib untuk endpoint terautentikasi:**

```http
Authorization: Bearer <access_token>
Accept: application/json
Origin: https://stockbit.com
Referer: https://stockbit.com/
User-Agent: Mozilla/5.0 ...
```

**Opsional / khusus:**

| Header | Nilai | Kapan |
|---|---|---|
| `X-AppVersion` | `3.0.0` (contoh) | Watchlist, sebagian endpoint |
| `X-Platform` | `web` | Watchlist, orderbook template |
| `X-Force-Challenge` | `true` | Hanya jika URL punya `force_challenge=1` |
| `Content-Type` | `application/json` | POST/PUT |
| `Authorization-Carina` | `Bearer <access>` | Watchlist portofolio (`isPortfolio=true`) |

**Login/refresh:**

- Login v6: tanpa `Authorization`, tetapi `withCredentials`.
- Refresh: `Authorization: Bearer <refresh_token>`.

### 2.7 Penanganan 401 (dari client axios)

Modul `18755` mengimplementasikan:

1. Response error dicek. Jika status **401** dan URL bukan `/logout`:
   - Ambil refresh token dari storage.
   - Jika `refresh.expired_at` sudah lewat → lempar error (sesi habis).
   - Jika ada proses refresh yang sedang berjalan (`refreshingTokenStatus === "processing"`), request masuk antrean (`refreshAndRetryQueue`).
   - Jika belum, set status `processing`, panggil `/login/refresh`, simpan pasangan token baru, lalu jalankan ulang semua request di antrean.
2. Jika status bukan 401 → error diteruskan.
3. Response body yang memiliki `error_type` **tetap dianggap error** meskipun HTTP 200 (interceptor melempar error).

Implikasi untuk klien:

- Jangan hanya mengecek HTTP status; cek juga `error_type` di body.
- Terapkan single-flight refresh (mutex) agar tidak terjadi double refresh.
- Simpan refresh token baru sebelum retry.

### 2.8 Cookie `credentialStorage`

- Nama: `credentialStorage`
- Isi: JSON URL-encoded dengan struktur `{ state: { access: {...}, refresh: {...}, ... }, version: ... }`
- Dipakai oleh web app dan SMtracker untuk membaca token.
- **Jangan** menyalin cookie ini ke log, issue, atau repository.
- Cookie dapat diakses oleh JavaScript (bukan HttpOnly) karena web app membacanya; ini meningkatkan risiko XSS. Untuk klien otomatis, lebih aman menyimpan token di file dengan permission `0600`.

### 2.9 Alur login yang terbukti

1. Jalankan browser (Playwright) dengan konteks bersih.
2. Buka halaman login Stockbit.
3. Isi email/username dan password dari environment.
4. Jika muncul prompt perangkat baru, pemilik akun menyetujui di aplikasi mobile.
5. Setelah redirect, baca cookie `credentialStorage`.
6. Ekstrak `access.token` dan `refresh.token`.
7. Verifikasi dengan `GET /emitten/BBCA/info` → 200.
8. Untuk menghindari rotasi tak terduga, **jangan** membiarkan browser melakukan refresh lagi. Tutup browser atau gunakan token secara eksklusif.

Pada sesi ini, langkah 1–7 berhasil. Token access terakhir valid sampai `2026-10-24T04:21:30Z`.

---

## 3. Konvensi umum API

### 3.1 Envelope respons

Sukses:

```json
{
  "message": "Successfully retrieved company data",
  "data": { }
}
```

Error:

```json
{
  "message": "Silahkan Periksa permintaan",
  "error_type": "INVALID_PARAMETER",
  "errors": [
    { "key": "Page", "error": "Page wajib diisi" }
  ]
}
```

Beberapa endpoint mengembalikan bentuk khusus:

| Endpoint | Bentuk |
|---|---|
| `/emitten/classification` | `data` berupa array |
| `/corpaction` | `data` berupa objek peta aksi korporasi |
| `/corpaction/{action}` | `data` berupa array/objek sesuai aksi |
| `/charts/{symbol}/daily` | `data` berisi `prices`, `timeframe`, dll. |
| `/chartbit/{symbol}/price/daily` | `data.chartbit` berupa array OHLCV |
| `/login/refresh` | `data.access`, `data.refresh` |
| `/logout` | tidak di-capture |

### 3.2 Error dan `error_type`

Nilai `error_type` yang diamati:

| `error_type` | HTTP | Arti |
|---|---|---|
| `INVALID_PARAMETER` | 400 | Parameter kurang/salah; lihat `errors[]` |
| `UNAUTHORIZED` | 401 | Token tidak ada/kedaluwarsa |
| `FORBIDDEN` | 403 | Tidak berhak (paywall/partnership) |
| `NOT_FOUND` | 404 | Resource tidak ditemukan |
| `SYSTEM_ERROR` | 500 | Kesalahan server |

Beberapa 404 mengembalikan `{"message":"Unrecognized Command"}` **tanpa** `error_type`. Jangan mengandalkan `error_type` selalu ada.

### 3.3 Pagination

Tiga pola:

1. **Page/limit** — `?page=1&limit=50`. Umumnya `page` dimulai dari **1**.
   - Pengecualian: `/search` memakai `page=0`.
2. **Cursor** — `last_stream_id`, `last_reply`, `offset`, `cursor`.
3. **Tanpa pagination** — endpoint mengembalikan seluruh data (mis. `/screener/templates`).

Contoh objek pagination:

```json
{
  "pagination": {
    "is_last_page": true,
    "next_cursor": "",
    "total": 31,
    "page": 1,
    "limit": 100
  }
}
```

Beberapa endpoint memakai `is_more`, `has_more`, atau `total`. Selalu periksa tipe dan keberadaan field sebelum melakukan loop.

### 3.4 Tipe data dan format angka

| Pola | Contoh | Dipakai di |
|---|---|---|
| String angka | `"price": "5125"` | `/emitten/{sym}/info`, orderbook, running trade |
| Number | `"average": 5201.142` | market detector, chart |
| `{raw, formatted}` | `{"raw": 512500, "formatted": "512.5K"}` | running trade value, market summary |
| Persen string | `"-0.97000"` | `/emitten/trending`, hotlist |
| Persen number | `-0.97` | `/emitten/{sym}/info` |
| String tanggal | `"23 Oct 2026"`, `"2026-10-22"`, `"2026-10-23 11:31:19"` | info, market time |
| Unix detik | `1792688400` | chartbit |

Satuan:

- Harga: rupiah per saham.
- Volume: lembar (bukan lot), kecuali field `lot`.
- Nilai: rupiah.
- `formatted` memakai suffix `K`, `M`, `B`, `T`.

### 3.5 Parameter array

Tiga format ditemukan; jangan menyamakan semuanya:

| Format | Contoh | Dipakai di |
|---|---|---|
| Bracket index | `symbol[0]=BBCA&symbol[1]=BBRI` | `/company-price-feed/prices/close` (hasil serialisasi qs default) |
| Repeat | `boards=A&boards=B` | `/company-price-feed/prices/{sym}/market` |
| Repeat | `symbols=BBCA&symbols=BBRI` | `/order-trade/running-trade` |
| Repeat | `category_types=...&category_types=...` | `/watchlist`, `/watchlist/favorite` |
| Repeat | `features=...&features=...` | `/paywall/eligibility/check` |
| Koma / bracket | bervariasi | beberapa endpoint lain |

Untuk endpoint baru, cek dulu: jika respons hanya berisi satu item padahal dikirim banyak, kemungkinan format array salah.

### 3.6 Rate limit

Header yang diamati pada setiap respons `exodus.api`:

```http
x-rate-limit-limit: 10
x-rate-limit-remaining: 8
x-rate-limit-reset: 0
```

Interpretasi:

- Kuota: **10 request per detik** per token/IP (belum dipastikan unitnya).
- `x-rate-limit-reset: 0` kemungkinan berarti reset berjalan kontinu (sliding window), bukan epoch.
- Setelah 2 request berurutan, `remaining` menjadi 8.

Rekomendasi:

- Maksimal **8 req/s** untuk operasi baca berurutan.
- Untuk fan-out banyak simbol, gunakan batch (mis. `symbol[0]...symbol[n]` pada `/prices/close`) daripada satu request per simbol.
- Saat 429: hormati `Retry-After` jika ada; jika tidak, backoff eksponensial 1s, 2s, 4s.

### 3.7 CORS dan header keamanan

Respons `exodus.stockbit.com` (GET):

```http
Access-Control-Allow-Origin: https://stockbit.com
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type, X-AppVersion, X-Force-Challenge, X-Platform
Access-Control-Expose-Headers: Content-Length
Vary: Origin
Strict-Transport-Security: max-age=63072000; includeSubDomains
X-Content-Type-Options: nosniff
Permissions-Policy: geolocation=(), camera=(), microphone=()
Cache-Control: no-store
```

Implikasi:

- Hanya origin `https://stockbit.com` yang diizinkan membaca respons secara cross-origin.
- Metode yang diizinkan untuk CORS: `GET, OPTIONS`. Untuk POST dari browser, preflight dapat gagal; klien non-browser tidak terpengaruh.
- Tidak ada `Content-Security-Policy` pada respons API.

### 3.8 Caching

- `exodus.stockbit.com`: `no-store` → jangan mengandalkan cache HTTP.
- `exodus.api.stockbit.com`: `public, max-age=1` pada sebagian respons → cache maksimal 1 detik.
- `CF-Cache-Status: DYNAMIC` → tidak di-cache di Cloudflare.
- Untuk data harga, cache internal 1–5 detik sudah cukup; jangan polling lebih cepat dari 1 detik per simbol.

### 3.9 idempotensi dan endpoint tulis

- Sebagian besar endpoint tulis tidak memiliki idempotency key.
- Risiko duplikasi jika retry otomatis: posting stream, follow, watchlist add, order.
- **Jangan** melakukan retry otomatis untuk POST/PUT/DELETE kecuali endpoint tersebut diketahui idempoten.
- Dokumen ini menandai endpoint tulis dengan ✍️ dan tidak menjalankannya.

---

## 4. Peta endpoint per domain

Tabel ringkas path dan status. Legenda:

| Simbol | Arti |
|---|---|
| ✅ | Terverifikasi live, HTTP 200, body JSON valid |
| 🟡 | Terverifikasi sebagian / parameter terbatas / hasil kosong |
| ⛔ | Diamati gagal (400/403/404/500) |
| 📄 | Hanya ditemukan di kode, belum diuji |
| ✍️ | Endpoint tulis, tidak dieksekusi |

### 4.1 Auth

| Method | Path | Status |
|---|---|---|
| POST | `/login/v6/username` | ✅ (via Playwright) |
| POST | `/login/v6/social` | 📄 |
| POST | `/login/v6/new-device/verify` | ✅ (manual) |
| POST | `/login/v3/username/browser` | 📄 |
| POST | `/login/v4/facebook` | 📄 |
| POST | `/login/v4/google` | 📄 |
| POST | `/login/v4/recovery/init` | 📄 |
| POST | `/login/v4/recovery/complete` | 📄 |
| POST | `/login/refresh` | ✅ |
| POST | `/logout` | 📄 |

### 4.2 Company / emitten

| Method | Path | Status |
|---|---|---|
| GET | `/emitten/{symbol}/info` | ✅ |
| GET | `/emitten/IHSG/info` | ✅ |
| GET | `/emitten/non-login/{symbol}/info` | ✅ |
| GET | `/emitten/v2/{exchange}/{symbol}/info-type` | ✅ |
| GET | `/emitten/v2/{exchange}/{symbol}/info` | ⛔ 500 |
| GET | `/emitten/v2/{exchange}/{symbol}/fin-items` | ⛔ 500 |
| GET | `/emitten/non-login/v2/{exchange}/{symbol}/info` | ⛔ 500 |
| GET | `/emitten/non-login/v2/{exchange}/{symbol}/fin-items` | ⛔ 500 |
| GET | `/partnership/emitten/v2/{exchange}/{symbol}/info` | ⛔ 403 |
| GET | `/emitten/{symbol}/profile` | ✅ |
| GET | `/emitten/{symbol}/contact` | ✅ (data kosong) |
| GET | `/emitten/trending` | ✅ |
| GET | `/emitten/hotlist/{topgainer\|toploser\|mostactive}` | ✅ |
| GET | `/emitten/classification` | ✅ |
| GET | `/emitten/classification/company` | ✅ (`ids`, lowercase) |
| GET | `/emitten/indexes/special-board` | ✅ |
| GET | `/emitten-metadata/subsidiary/{symbol}` | ✅ |
| POST | `/emitten-metadata/shareholders/token` | ✅ |
| GET | `/emitten-metadata/shareholders/{symbol}/chart` | ✅ (token khusus) |
| GET | `/emitten/catalog` | ✅ |
| GET | `/emitten/catalog/{catalog_code}/company` | ✅ |
| GET | `/partnership/charts/{symbol}` | ⛔ 403 |

Catatan:

- `/emitten/{symbol}/profile` adalah satu panggilan yang memasok hampir seluruh tab profil perusahaan (lihat [5.2.5](#525-get-emittensymbolprofile)).
- `/emitten/catalog` tanpa filter mengembalikan katalog `CATALOG_TYPE_SUBINDUSTRY`; gunakan `catalog_type=CATALOG_TYPE_KONGLO` untuk daftar grup konglomerasi (lihat [5.17](#517-katalog-konglomerasi-konglo)).

### 4.3 Harga, market, chart

| Method | Path | Status |
|---|---|---|
| GET | `/company-price-feed/prices/close` | ✅ |
| GET | `/company-price-feed/prices/{symbol}/market` | 🟡 hanya indeks |
| GET | `/company-price-feed/price-performance/{symbol}` | ✅ |
| GET | `/company-price-feed/seasonality/{symbol}` | ✅ |
| GET | `/company-price-feed/market-time` | ✅ |
| GET | `/company-price-feed/market-time/session` | ✅ |
| GET | `/orderbook/companies/{symbol}` | ✅ |
| GET | `/company-price-feed/v2/orderbook/companies/{symbol}` | ✅ |
| GET | `/company-price-feed/v2/orderbook/template/{id}` | 🟡 butuh id valid |
| GET | `/charts/{symbol}/daily` | ✅ |
| GET | `/charts/{symbol}` | 🟡 `prices` kosong |
| GET | `/chartbit/{symbol}/price/daily` | ✅ |
| GET | `/chartbit/{symbol}/price/intraday` | ✅ |
| GET | `/chartbit/charts` | ✅ |
| GET | `/chartbit/charts/{id}` | ✅ |
| GET | `/chartbit/studies` | ✅ |
| GET | `/chartbit/chart-drawings` | ✅ |
| GET | `/chartbit/search` | ⛔ 404 |

### 4.4 Order flow / broker

| Method | Path | Status |
|---|---|---|
| GET | `/order-trade/broker/top` | ✅ |
| GET | `/order-trade/broker/activity` | ✅ |
| GET | `/order-trade/broker/activity-chart` | ✅ |
| GET | `/order-trade/trade-book` | ✅ |
| GET | `/order-trade/running-trade` | ✅ |
| GET | `/order-trade/running-trade/group` | ✅ |
| GET | `/marketdetectors/{symbol}` | ✅ |
| GET | `/findata-view/marketdetectors/brokers` | ✅ |

### 4.5 Fundamental / analyst

| Method | Path | Status |
|---|---|---|
| GET | `/findata-view/company/financial` | ✅ |
| GET | `/keystats/ratio/v1/{symbol}` | ✅ |
| GET | `/findata-view/foreign-domestic/v1/chart-data/{symbol}` | ✅ |
| GET | `/analyst-ratings/{symbol}` | ✅ |
| GET | `/analyst-ratings/{symbol}/consensus` | ✅ |

### 4.6 Corporate action

| Method | Path | Status |
|---|---|---|
| GET | `/corpaction` | ✅ |
| GET | `/corpaction/{action}` | ✅ |
| GET | `/corpaction/{symbol}` | ✅ |
| GET | `/corpaction/{symbol}/stock_conversion` | ✅ |

### 4.7 Insider / shareholder

| Method | Path | Status |
|---|---|---|
| GET | `/insider/company/majorholder` | ✅ |
| GET | `/insider/shareholding/composition/companies/{symbol}` | ✅ (`view` ALL/SCRIPPLESS) |
| GET | `/insider/shareholding/ubo/companies/{symbol}` | ✅ |
| GET | `/insider/ubo` | ✅ (`investor_id`) |
| GET | `/insider/shareholding/companies/{company_id}` | ✅ (butuh company ID numerik) |
| GET | `/insider/shareholding/investors/{investor_id}` | ✅ (butuh investor ID) |
| GET | `/insider/shareholding/network` | ✅ (butuh `root_id` + `root_type`) |

### 4.8 Screener / valuation / watchlist / search

| Method | Path | Status |
|---|---|---|
| GET | `/screener/templates` | ✅ |
| GET | `/screener/preset` | ✅ |
| GET | `/screener/templates/{id}` | ✅ |
| GET | `/screener/universe` | ✅ |
| GET | `/screener/favorites` | ✅ |
| GET | `/screener/metric` | ✅ |
| GET | `/screener/finitem-watchlist` | ✅ |
| POST | `/screener/templates` | ✍️ |
| POST | `/screener/favorites` | ✍️ |
| DELETE | `/screener/favorites/{id}` | ✍️ |
| DELETE | `/screener/templates/{id}` | ✍️ |
| GET | `/valuation/all/templates` | ✅ |
| GET | `/valuation/metrics/lists` | ✅ |
| GET | `/valuation/{id}` | 📄 |
| POST | `/valuation` | ✍️ |
| PUT | `/valuation/{id}` | ✍️ |
| DELETE | `/valuation/{id}` | ✍️ |
| POST | `/valuation/company/{symbol}` | ✍️ |
| GET | `/valuation/company/{symbol}/metrics` | 📄 |
| GET | `/watchlist` | ✅ |
| GET | `/watchlist/favorite` | ✅ |
| GET | `/watchlist/{id}` | ✅ |
| GET | `/watchlist/{id}/symbols` | 📄 |
| GET | `/watchlist/company/{id}/followers` | 📄 |
| GET | `/watchlist/company/follower-info` | ✅ |
| GET | `/watchlist/suggestion/company` | 📄 |
| GET | `/watchlist/metric` | ✅ |
| GET | `/watchlist/search/company` | ✅ |
| POST/PUT/DELETE | `/watchlist*` (lihat 5.11) | ✍️ |
| GET | `/search` | ✅ |

### 4.9 Stream

| Method | Path | Status |
|---|---|---|
| GET | `/stream/v3` | ✅ |
| GET | `/stream/v3/symbol/{symbol}` | ✅ |
| GET | `/stream/v3/symbol/{symbol}/pinned` | ✅ |
| POST | `/stream/v3/trending` | ✅ (read via POST) |
| POST | `/stream/v3/user/{username}` | ✅ (read via POST) |
| POST | `/stream/v3/post/{id}` | ✅ (read via POST) |
| POST | `/stream/v3/conversation/{id}` | ✅ (read via POST) |
| POST | `/stream/v3/conversation/comments` | ✅ (read via POST) |
| GET | `/stream/likers/{id}` | ✅ |
| GET | `/stream/reactions` | ✅ |
| GET | `/stream/non-login/symbol/{symbol}` | ✅ |
| GET | `/stream/non-login/post/{id}` | ✅ |
| GET | `/stream/non-login/user/{username}` | ✅ |
| GET | `/stream/announcement/{id}` | 📄 |
| POST | `/stream/like/{id}`, `/stream/unlike/{id}` | ✍️ |
| POST | `/stream/v3` (write) | ✍️ |

### 4.10 User / notification / chat / misc

| Method | Path | Status |
|---|---|---|
| GET | `/user/profile` | ✅ |
| GET | `/user/profile/{username}` | ✅ |
| GET | `/user-setting/configurations` | ✅ |
| GET | `/user/v2/discovery/trending` | ✅ |
| GET | `/notification/count/unread` | ✅ |
| GET | `/notification/v3/settings` | ✅ |
| GET | `/chat/v2/rooms/unread/count` | ✅ |
| GET | `/verified-badge/user/{id}` | ✅ |
| GET | `/auth/websocket/key` | ✅ |
| GET | `/live-stream/event` | ✅ |
| GET | `/research/indicator/new` | ✅ |
| GET | `/paywall/eligibility/check` | ✅ |
| POST | `/paywall/counter/increment` | ✅ (dipicu web app) |
| GET | `/academy/unboxing` | ✅ |
| POST | `/academy/v2/module` | ✅ (dipicu web app) |
| GET | `/academy/lessons/last-read` | ✅ |
| POST | `/academy/tokens/new` | ✅ (dipicu web app) |
| GET | `/remisier/referral/status` | ⛔ 404 |

> **Catatan etika:** Beberapa POST di atas (`/paywall/counter/increment`, `/academy/v2/module`, `/academy/tokens/new`) terekam karena aplikasi web sendiri memanggilnya saat halaman dibuka. Tidak ada aksi trading atau sosial yang dilakukan secara sengaja.

---

## 5. Referensi endpoint

Bagian ini mengelompokkan endpoint berdasarkan domain. Untuk setiap endpoint penting disertakan parameter, bentuk respons, dan catatan hasil pengujian. Semua path relatif terhadap `https://exodus.stockbit.com` atau `https://exodus.api.stockbit.com` (identik).

Header minimum untuk endpoint terautentikasi:

```http
Authorization: Bearer <access_token>
Accept: application/json
Origin: https://stockbit.com
Referer: https://stockbit.com/
User-Agent: Mozilla/5.0 ...
```

### 5.1 Auth dan session

| Method | Path | Auth | Keterangan |
|---|---|---|---|
| POST | `/login/v6/username` | — | Login web utama |
| POST | `/login/v6/social` | — | Login sosial |
| POST | `/login/v6/new-device/verify` | — | Verifikasi perangkat baru |
| POST | `/login/v3/username/browser` | — | Login legacy/server-side |
| POST | `/login/v4/facebook` | — | Login Facebook |
| POST | `/login/v4/google` | — | Login Google |
| POST | `/login/v4/recovery/init` | — | Mulai reset password |
| POST | `/login/v4/recovery/complete` | — | Selesaikan reset password |
| POST | `/login/refresh` | refresh | Rotasi access+refresh |
| POST | `/logout` | access | Logout best-effort |

Detail request/response ada di [bagian 2](#2-autentikasi-dan-sesi).

**Catatan:**

- Login endpoint memakai `withCredentials` dan **tidak** mengirim `Authorization`.
- `player_id` wajib ada pada login v6; nilainya berasal dari perangkat.
- `recaptcha_token` dan `recaptcha_version` wajib untuk login web; tanpa itu kemungkinan besar ditolak.
- Respons login tidak di-capture. Yang diamati: cookie `credentialStorage` dan sesi valid.

### 5.2 Company / emitten

#### 5.2.1 `GET /emitten/{symbol}/info`

Informasi ringkas emiten/index.

**Parameter**

| Nama | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `symbol` | path | ya | Kode saham (`BBCA`) atau indeks (`IHSG`) |
| `with_sub_industry` | bool | tidak | `true` menambahkan sub-industri |

**Respons 200**

```json
{
  "message": "Successfully retrieved company data",
  "data": {
    "id": "54",
    "symbol": "BBCA",
    "symbol_2": "BBCA",
    "symbol_3": "BBCA",
    "name": "Bank Central Asia Tbk.",
    "exchange": "IDX",
    "country": "ID",
    "sector": "Keuangan",
    "sub_sector": "Bank",
    "status": "STATUS_ACTIVE",
    "date": "23 Oct 2026",
    "price": "5125",
    "previous": "5175",
    "change": "-50.00",
    "percentage": -0.97,
    "average": "177716748.00",
    "aum": "",
    "indexes": ["TRADINGLIMIT", "ECONOMIC30", "DAYTRADE", "LQ45", "IHSG"],
    "orderbook": { "bid": { }, "offer": { } },
    "sentiment": {
      "start_value": "0",
      "end_value": "0",
      "period": "1D",
      "value": "0"
    },
    "prices": [],
    "followed": 0,
    "followers": 0
  }
}
```

**Catatan:**

- `price`, `previous`, `change`, `average` adalah **string**.
- `percentage` adalah **number** (`-0.97`), berbeda dengan `/emitten/trending` yang memakai string (`"-0.97000"`).
- `orderbook` berisi ringkasan bid/offer (bukan array penuh). Untuk orderbook lengkap gunakan endpoint di 5.4.
- `prices` biasanya kosong; data harga diambil dari endpoint prices/chart.
- `IHSG` dapat dipanggil dengan path yang sama: `/emitten/IHSG/info`.

**Status:** ✅ 200.

#### 5.2.2 `GET /emitten/non-login/{symbol}/info`

Sama seperti di atas, tetapi **tidak memerlukan token**. Diuji tanpa header `Authorization` → 200.

```http
GET /emitten/non-login/BBCA/info
```

**Status:** ✅ 200, body identik dengan `/emitten/{symbol}/info`.

Berguna untuk fallback saat token habis, tetapi tetap hormati rate limit.

#### 5.2.3 `GET /emitten/v2/{exchange}/{symbol}/info-type`

Menentukan tipe entitas dan versi API yang harus dipakai.

```json
{
  "message": "Successfully retrieved company info type",
  "data": {
    "info_type": "COMPANY_INFO_TYPE_EMITTEN",
    "api_version": "COMPANY_INFO_API_VERSION_V1"
  }
}
```

Nilai `info_type` yang ditemukan di enum:

- `COMPANY_INFO_TYPE_UNSPECIFIED`
- `COMPANY_INFO_TYPE_EMITTEN`
- `COMPANY_INFO_TYPE_CRYPTO`
- `COMPANY_INFO_TYPE_ETF_GOLD`
- `COMPANY_INFO_TYPE_FR`
- `COMPANY_INFO_TYPE_TOKENIZED_STOCK`

`api_version`: `COMPANY_INFO_API_VERSION_UNSPECIFIED`, `COMPANY_INFO_API_VERSION_V1`.

**Status:** ✅ 200 (`/emitten/v2/IDX/BBCA/info-type`).

#### 5.2.4 Endpoint v2 yang rusak

| Endpoint | Status | Body |
|---|---|---|
| `GET /emitten/v2/IDX/{symbol}/info` | 500 | `{"message":"Failed to get emitten info","error_type":"SYSTEM_ERROR"}` |
| `GET /emitten/v2/IDX/{symbol}/fin-items` | 500 | `{"message":"Failed to get emitten info","error_type":"SYSTEM_ERROR"}` |
| `GET /emitten/non-login/v2/IDX/{symbol}/info` | 500 | sama |
| `GET /emitten/non-login/v2/IDX/{symbol}/fin-items` | 500 | sama |
| `GET /partnership/emitten/v2/IDX/{symbol}/info` | 403 | HTML Cloudflare |

Diuji untuk `BBCA` dan `IDX`/`1`; semuanya gagal. Aplikasi web masih memanggil endpoint ini, jadi kemungkinan besar ada bug server atau endpoint hanya aktif untuk tipe entitas tertentu (crypto/ETF).

**Gunakan** `/emitten/{symbol}/info` atau `/emitten/non-login/{symbol}/info` sebagai gantinya.

#### 5.2.5 `GET /emitten/{symbol}/profile`

Profil perusahaan lengkap (halaman "Profil" di web). Satu panggilan ini memasok hampir seluruh tab: latar belakang, sejarah, direksi, pemegang saham, jumlah pemegang saham, UBO, anak perusahaan, dan klasifikasi.

**Parameter**

| Nama | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `symbol` | path | ya | Kode saham (`BBCA`, `CUAN`, `BRPT`) |

**Respons 200 — field level atas:**

```
address, background, history, key_executive, secretary, shareholder,
subsidiary, profile, fee, asset_allocation, shareholder_reksa, pdf,
shareholder_numbers, badges, top_holdings,
shareholder_director_commissioner, listing_information, beneficiary,
shareholder_one_percent, classification
```

| Field | Bentuk | Isi |
|---|---|---|
| `background` | string | Deskripsi singkat perusahaan (sering menyebut anak perusahaan) |
| `history` | object | `amount`, `board`, `date`, `price`, `registrar`, `shares`, `underwriters[]`, `administrative_bureau`, `free_float` |
| `key_executive` | object | Grup jabatan: `president_director`, `director[]`, `president_commissioner`, `commissioner[]`, `independent_commissioner[]`, `vice_president[]`, dst. Tiap item `{id, key, lastupdate, value}` |
| `address` | array | `office`, `phone`, `fax`, `email[]`, `website`, `npwp`, `value` (HTML), `lastupdate` |
| `secretary` | array | `{id, key, lastupdate, value}`; `value` adalah **string JSON** berisi `name`, `phone`, `email` |
| `shareholder` | array | Pemegang saham + agregat pasar; lihat catatan di bawah |
| `shareholder_one_percent` | object | `{shareholder[], last_updated}`; daftar pemegang saham ≥1% dengan ID investor |
| `shareholder_director_commissioner` | array | Kepemilikan direksi/komisaris; bentuk sama dengan `shareholder`, `badges` berisi `komisaris`/`direksi` |
| `shareholder_numbers` | array | Deret waktu jumlah pemegang saham (lihat di bawah) |
| `beneficiary` | array | `[{name}]` — nama Ultimate Beneficial Owner menurut emiten |
| `subsidiary` | array | `{company, percentage, types, value}` — ringkasan anak perusahaan |
| `profile` | object | Field khusus reksa dana/ETF: `fund_type`, `fund_manager`, `custodian_bank`, `risk_level`, `aum`, `maxdrawdown`, `cagr5year`, `expense_ratio`, `average_yield` |
| `listing_information` | object | `exercise_*`, `expire_date`, `listing_date`, `foreign_percentage`, `local_percentage`, `number_of_securities`, `total_shares` |
| `classification` | object | `sector`, `sub_sector`, `industry`, `sub_industry`; tiap item `{id, name, symbol}` |
| `fee`, `asset_allocation`, `shareholder_reksa`, `pdf`, `top_holdings` | array | Sering kosong untuk saham biasa; terisi untuk produk reksa dana |

**`shareholder_numbers[]`:**

```json
{
  "shareholder_date": "30 Sep 2026",
  "total_share": "759,569",
  "change": -7712,
  "change_formatted": "(-7,712)",
  "change_value": "-7712"
}
```

- Diurutkan dari terbaru ke terlama.
- BBCA mengembalikan **24 bulan** data; nilai terbaru 759.569 pemegang saham per 30 Sep 2026.
- `total_share` adalah **string berformat ribuan**, bukan angka mentah; `change` numerik.

**Tiga field pemegang saham yang berbeda:**

| Field | Cakupan | `id` | Contoh |
|---|---|---|---|
| `shareholder` | Pemegang saham pengendali + agregat (`MASYARAKAT NON WARKAT`, `MASYARAKAT WARKAT`, `SAHAM TREASURY`) | `"0"` (tidak dapat dipakai) | `DWIMURIA INVESTAMA ANDALAN` 54.942% |
| `shareholder_one_percent` | Pemegang saham individual ≥1%, angka mentah presisi | **investor ID** (mis. `8911`, `8991`) | `PRAJOGO PANGESTU` 80.42% di CUAN |
| `beneficiary` | Nama UBO menurut emiten | — | `ROBERT BUDI HARTONO` |

- `shareholder[].percentage` memakai denominator total saham (termasuk agregat), sehingga totalnya mendekati 100%.
- `shareholder_one_percent[].value` berupa string dengan pemisah koma (`"67,729,950,000"`), sedangkan `shareholder[].value` sudah diformat (`"67.73 B"`).
- `shareholder_one_percent[].id` dapat langsung dipakai sebagai `investor_id` pada [`GET /insider/ubo`](#587-get-insideruboinvestor_idinvestor_id) dan [`GET /insider/shareholding/investors/{investor_id}`](#585-get-insidershareholdinginvestorsinvestor_id).

**Catatan:**

- `listing_information` untuk BBCA berisi nol/kosong meskipun saham sudah lama tercatat; jangan pakai sebagai sumber tanggal IPO. Gunakan `history.listing_date`/`history.date` bila perlu.
- `profile` kosong secara makna untuk saham biasa (hanya relevan untuk reksa dana/ETF).
- **Jangan** menampilkan email/telepon perusahaan sebagai data pribadi; itu data publik perusahaan, tetapi tetap tidak dimasukkan ke contoh di dokumen ini.
- `subsidiary` di sini **berbeda** dari [`/emitten-metadata/subsidiary/{symbol}`](#531-get-emitten-metadatasubsidiarysymbol): yang ini ringkas (`company`, `types`, `percentage`, `value`), yang lain memuat `total_assets`, `business_type`, `location`, dan periode laporan.

**Status:** ✅ 200 (diverifikasi untuk BBCA, CUAN, BRPT).

#### 5.2.6 `GET /emitten/{symbol}/contact`

Data kontak emiten.

**Respons 200 untuk BBCA:**

```json
{ "message": "Successfully retrieved company contact data", "data": [] }
```

Data kosong meskipun profil berisi kontak; kemungkinan endpoint ini hanya terisi untuk sebagian emiten. **Status:** ✅ 200 (kosong).

#### 5.2.7 `GET /emitten/trending`

Daftar saham yang sedang trending.

**Respons 200 — array item:**

```json
{
  "change": "+52",
  "symbol": "BUVA",
  "percent": "16.56000",
  "name": "Bukit Uluwatu Villa Tbk.",
  "last": "366",
  "symbol_2": "BUVA",
  "symbol_3": "BUVA",
  "company_id": "105",
  "notation": [],
  "uma": false,
  "tradeable": 1,
  "country": "ID",
  "type": "Saham",
  "corp_action": {
    "active": true,
    "icon": "https://assets.stockbit.com/images/corp_action_event_icon.svg",
    "text": "Perusahaan Memiliki Corporate Action",
    "detail": null
  },
  "isexist": 0,
  "status": "STATUS_ACTIVE",
  "icon_url": "https://assets.stockbit.com/logos/companies/BUVA.png",
  "is_following": false,
  "formatted_price": "",
  "is_exists": false,
  "previous": "314",
  "day_trade_info": { "is_show_multiplier": false, "multiplier": "0" },
  "trading_limit_info": { "is_trading_limit": false, "haircut_percentage": "" },
  "margin_info": { "is_margin_trading": false, "percentage": "", "percentage_raw": 0 }
}
```

**Status:** ✅ 200.

#### 5.2.8 `GET /emitten/hotlist/{type}`

**Path parameter**

| Nilai | Arti |
|---|---|
| `topgainer` | Kenaikan terbesar |
| `toploser` | Penurunan terbesar |
| `mostactive` | Volume/nilai terbesar |

**Query:** `limit` (default 10).

**Respons:** array item dengan struktur hampir sama dengan `/emitten/trending` (field `change`, `percent`, `last`, `previous`, `company_id`, `corp_action`, `day_trade_info`, `trading_limit_info`, `margin_info`).

**Status:** ✅ 200 untuk ketiga tipe.

#### 5.2.9 `GET /emitten/classification`

Taksonomi sektor/papan/indeks.

| Query | Hasil |
|---|---|
| tanpa parameter | 22 sektor level 1 (Barang Konsumen Primer, Kesehatan, Keuangan, ...) |
| `?id=88` | 47 indeks (IHSG, LQ45, JII, MBX, ...) |
| `?id=89` | 5 papan pencatatan (Ekonomi Baru, FCA, Papan Utama, Papan Pengembangan, Papan Akselerasi) |

**Item:**

```json
{
  "id": 1,
  "name": "Barang Konsumen Primer",
  "level": 1,
  "parent_id": 0,
  "symbol": "Non-Cyclical",
  "total_company": 133
}
```

**Status:** ✅ 200.

#### 5.2.10 `GET /emitten/classification/company`

Daftar konstituen untuk sekelompok klasifikasi.

**Parameter**

| Nama | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `ids` | repeat, **lowercase** | ya | ID dari `/emitten/classification` |

Contoh:

```http
GET /emitten/classification/company?ids=1&ids=3
```

**Respons 200**

```json
{
  "message": "Successfully retrieved companies",
  "data": [
    {
      "id": 1,
      "level": 1,
      "companies": [
        {
          "avgvolume": "35102900180.00",
          "change": "+58.84",
          "company_id": "467",
          "country": "ID",
          "followed": 0,
          "followers": 1128289,
          "isexist": 0,
          "last": "5125",
          "name": "Bank Central Asia Tbk.",
          "percent": "-0.97",
          "previous": "5175",
          "sector": "Keuangan",
          "subsector": "Bank",
          "symbol": "BBCA",
          "icon_url": "...",
          "status": "STATUS_ACTIVE"
        }
      ],
      "pagination": { "is_last_page": true, "total": 133 }
    }
  ]
}
```

**Catatan penting:**

- Nama parameter **`ids` huruf kecil**. `?IDs=88` → 400 `"IDs wajib diisi"`; `?id=88` → 400 juga.
- `ids=88` mengembalikan 52 entitas yang sebagian besar adalah **indeks** (IHSG, LQ45, ...), bukan saham.
- `ids=1` mengembalikan 133 saham sektor Barang Konsumen Primer.
- `ids=89` mengembalikan 0 companies (papan).

**Status:** ✅ 200.

#### 5.2.11 `GET /emitten/indexes/special-board`

Daftar papan khusus/indeks spesial.

```json
{
  "message": "Successfully retrieved special board catalog",
  "data": {
    "special_board": [
      { "parent_id": 88, "id": 1000004658, "symbol": "DAYTRADE", "name": "Day Trade" }
    ]
  }
}
```

**Status:** ✅ 200.

### 5.3 Metadata emiten

#### 5.3.1 `GET /emitten-metadata/subsidiary/{symbol}`

Daftar anak perusahaan beserta total aset dan periode laporan.

**Parameter**

| Nama | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `symbol` | path | ya | Kode saham (`BBCA`) |

**Respons 200 — field level atas:**

```
subsidiaries[], currency, last_updated_period, unit
```

Contoh (BBCA):

```json
{
  "message": "Successfully retrieved subsidiary data",
  "data": {
    "subsidiaries": [
      {
        "company_name": "PT Bank Digital BCA",
        "business_type": "Perbankan",
        "location": "Jakarta",
        "commercial_year": "1965",
        "total_assets": "20,769,582",
        "percentage": "100.00",
        "id": 0,
        "operational_status": "",
        "period": "",
        "raw": null
      }
    ],
    "currency": "CURRENCY_IDR",
    "last_updated_period": "Q3 2026",
    "unit": "UNIT_MILLION"
  }
}
```

| Field | Keterangan |
|---|---|
| `total_assets` | String berformat ribuan; **skalakan dengan `unit`** (`UNIT_MILLION` → juta rupiah) |
| `percentage` | Persentase kepemilikan, string (`"100.00"`, `"90.00"`) |
| `business_type` | Bidang usaha anak perusahaan; bisa sangat panjang dan tidak konsisten kapitalisasinya |
| `commercial_year` | Tahun komersial, bukan tahun pendirian yang tervalidasi |
| `operational_status`, `period`, `id`, `raw` | Umumnya kosong/`0`/`null` pada build ini |

**Catatan penting:**

- Endpoint ini **bukan** pengganti `profile.subsidiary`. Jumlah dan isinya berbeda: BBCA mengembalikan 7 baris di sini, sedangkan `profile.subsidiary` berisi 9 baris dengan bentuk `{company, percentage, types, value}`.
- `value` pada `profile.subsidiary` memakai skala yang tidak diberi label; jangan campur dengan `total_assets` di endpoint ini.
- Untuk daftar anak perusahaan yang dipakai UI profil, `profile.subsidiary` yang dirender; endpoint ini dipakai untuk tabel "Anak Perusahaan" dengan total aset.

**Status:** ✅ 200 (diverifikasi untuk BBCA).

#### 5.3.2 `POST /emitten-metadata/shareholders/token`

Mengeluarkan token **khusus** untuk endpoint chart shareholder. Token ini berbeda dari access token biasa.

**Request:** body kosong.

**Respons:**

```json
{
  "message": "...",
  "data": { "value": "<token>" }
}
```

Token bersifat sementara; jangan disimpan lama. **Status:** ✅ 200 (dipanggil otomatis oleh halaman).

#### 5.3.3 `GET /emitten-metadata/shareholders/{symbol}/chart`

Grafik **Holding Composition** — komposisi kepemilikan **scripless** dari waktu ke waktu, dipecah menurut Local/Foreign (tab `all`) atau menurut kategori investor (tab `local`/`foreign`).

**Parameter**

| Nama | Wajib | Nilai |
|---|---|---|
| `symbol` | ya | Kode saham; client mengirimnya di path **dan** query |
| `value_year` | ya | `6`, `12`, `24`, `36` |
| `shareholder_type` | ya | `all`, `local`, `foreign` (huruf kecil, case-sensitive) |
| `date` | tidak | `YYYY-MM-DD`; mengembalikan **satu snapshot** pada tanggal itu, bukan deret waktu |

Nilai `scripless`, `scrip`, `ALL`, atau `LOCAL` **tidak valid**: server membalas 200 tetapi `legend` kosong (kegagalan senyap). Validasi sendiri di client.

**Header khusus:**

```http
Authorization: <token dari POST /emitten-metadata/shareholders/token>
```

Bukan `Bearer <access_token>`. Token dikirim apa adanya.

**Contoh:**

```http
GET /emitten-metadata/shareholders/BBCA/chart?symbol=BBCA&shareholder_type=all&value_year=12
```

**Respons 200 — field level atas:**

```
last_update, timeframe, legend, summary, first_available_date, last_available_date
```

`timeframe` selalu memuat empat pilihan, terlepas dari `value_year` yang diminta:

```json
[ { "year": "6 Bulan", "value": 6 }, { "year": "1 Tahun", "value": 12 },
  { "year": "2 Tahun", "value": 24 }, { "year": "3 Tahun", "value": 36 } ]
```

`legend[]`:

```json
{
  "color": "#8228BD",
  "item_name": "Local",
  "chart_data": [
    {
      "date": "Sep 25",
      "value": 21.889303,
      "unix_date": "1759165200",
      "shares": { "raw": "11481747656", "formatted": "11.48B" }
    }
  ]
}
```

`summary[]`:

```json
{
  "date": "Sep 25",
  "unix_date": "1759165200",
  "shares": { "raw": "52453691120", "formatted": "52.45B" },
  "percentage": { "raw": 100, "formatted": "100.00%" }
}
```

**Semantik angka:**

- Denominator seluruh grafik adalah **total saham scripless**, bukan total saham beredar. Untuk BBCA: 52,45 B scripless dari 123,28 B total saham.
- `shareholder_type=all` → dua seri: `Local` dan `Foreign`; `summary` adalah total scripless per bulan (100%).
- `shareholder_type=local`/`foreign` → sembilan seri kategori investor (`Perusahaan`, `Individual`, `Bank`, `Sekuritas`, `Reksadana`, `Asuransi`, `Dana Pensiun`, `Yayasan`, `Lainnya`); `summary` adalah total kelompok tersebut per bulan.
- `value` pada `chart_data` adalah persentase terhadap total scripless; `summary[].percentage` untuk `local`/`foreign` juga terhadap total scripless (bukan terhadap kelompoknya).
- `date` mengembalikan satu titik (`summary` panjang 1, `chart_data` panjang 1) — berguna untuk snapshot historis.

**Status:** ✅ 200 (BBCA: 13 titik untuk 12 bulan; `first_available_date` 2019-03).

**Respons 200 — field level atas:**

```
last_update, timeframe, legend, summary, first_available_date, last_available_date
```

`timeframe`:

```json
[ { "year": "6 Bulan", "value": 6 }, { "year": "1 Tahun", "value": 12 } ]
```

Nilai lain mengikuti pola `{year, value}`.

`legend`:

```json
{
  "color": "#8228BD",
  "item_name": "Local",
  "chart_data": [
    {
      "date": "Sep 25",
      "value": 21.889303,
      "unix_date": "1759165200",
      "shares": { "raw": "11481747656", "formatted": "11.48B" }
    }
  ]
}
```

`summary`:

```json
{
  "date": "Sep 25",
  "unix_date": "1759165200",
  "shares": { "raw": "52453691120", "formatted": "52.45B" },
  "percentage": { "raw": 100, "formatted": "100.00%" }
}
```

**Status:** ✅ 200.

#### 5.3.4 `GET /partnership/charts/{symbol}`

Endpoint chart versi partnership/guest. Untuk `BBCA` mengembalikan **403 HTML Cloudflare**, bukan JSON.

**Status:** ⛔ 403 (paywall/partner restriction). Jangan diandalkan.

### 5.4 Harga, market, orderbook, chart

#### 5.4.1 `GET /company-price-feed/prices/close`

Harga close terakhir (minutely) untuk banyak simbol sekaligus.

**Parameter**

| Nama | Wajib | Keterangan |
|---|---|---|
| `interval` | ya | `1` (menit) — nilai lain belum diuji |
| `symbol` atau `symbol[]` | ya | Bisa satu string atau array |

Dua bentuk yang diterima:

```http
GET /company-price-feed/prices/close?interval=1&symbol=BBCA
GET /company-price-feed/prices/close?interval=1&symbol[0]=BBCA&symbol[1]=BBRI
```

**Respons 200**

```json
{
  "message": "Successfully retrieved minutely prices",
  "data": [
    { "symbol": "BBCA", "prices": ["11300", "11350", "11275", "..."] }
  ]
}
```

**Catatan:**

- `prices` adalah array **string** angka, bukan objek.
- Dengan `interval=1`, satu simbol dapat berisi ±151 titik (satu sesi berjalan).
- Untuk batch, gunakan format bracket (`symbol[0]`, `symbol[1]`, ...) seperti yang dipakai web.
- Tidak ada field timestamp per titik; urutan mengikuti waktu.

**Status:** ✅ 200.

#### 5.4.2 `GET /company-price-feed/prices/{symbol}/market`

Ringkasan market per board.

**Parameter**

| Nama | Wajib | Keterangan |
|---|---|---|
| `date` | tidak | `YYYY-MM-DD`; web selalu mengirim |
| `boards` | tidak | Repeat: `MARKET_BOARD_ALL`, `MARKET_BOARD_REGULER`, `MARKET_BOARD_TUNAI`, `MARKET_BOARD_NEGO`; web selalu mengirim |

**Respons 200 (IHSG)**

```json
{
  "message": "Successfully retrieved market prices",
  "data": {
    "symbol": "IHSG",
    "date": "2026-10-23",
    "is_open_market": true,
    "markets": [
      {
        "board": "MARKET_BOARD_REGULER",
        "previous": { "raw": "5387.905", "formatted": "5,387.91" },
        "lastprice": { "raw": "5446.741", "formatted": "5,446.74" },
        "change": { "raw": "58.836", "formatted": "58.84" },
        "percentage_change": { "raw": "1.0920014", "formatted": "1.09" },
        "frequency": { "raw": "1056720", "formatted": "1.06M" },
        "volume": { "raw": "20867540600", "formatted": "20.87B" },
        "value": { "raw": "7286208022300", "formatted": "7.29T" },
        "open": { "raw": "5397.337", "formatted": "5,397.34" },
        "high": { "raw": "5452.774", "formatted": "5,452.77" },
        "low": { "raw": "5366.294", "formatted": "5,366.29" }
      }
    ]
  }
}
```

**Catatan penting:** untuk saham individual (mis. `BBCA`), endpoint ini mengembalikan `symbol`, `date`, dan `markets` **kosong**:

```json
{"message":"Successfully retrieved market prices","data":{"symbol":"","date":"","is_open_market":false,"markets":[]}}
```

Jadi praktis **hanya berguna untuk indeks** (`IHSG`). Untuk saham gunakan `/company-price-feed/price-performance/{symbol}` atau chart.

**Status:** ✅ 200 (IHSG), 🟡 kosong untuk saham.

#### 5.4.3 `GET /company-price-feed/price-performance/{symbol}`

Performa harga untuk 10 timeframe.

**Respons 200**

```json
{
  "message": "Successfully get price performance data",
  "data": {
    "prices": [
      {
        "close": { "raw": 5125, "formatted": "5,125" },
        "high": { "raw": 5225, "formatted": "5,225" },
        "low": { "raw": 5050, "formatted": "5,050" },
        "percentage": { "raw": -0.9661836, "formatted": "(-0.97%)" },
        "timeframe": "1D"
      }
    ]
  }
}
```

**Timeframe yang dikembalikan (urutan):**

```
1D, 1W, 1M, 3M, 6M, YTD, 1Y, 3Y, 5Y, 10Y
```

**Status:** ✅ 200.

#### 5.4.4 `GET /company-price-feed/seasonality/{symbol}`

Analisis musiman per bulan.

**Parameter**

| Nama | Wajib | Keterangan |
|---|---|---|
| `year` | ya | Tahun acuan, mis. `2026` |
| `back_year` | ya | Jumlah tahun ke belakang, mis. `5` |

**Respons 200 — field:**

```
price_change, up, down, total_months, avg, prob, default_last_year
```

`price_change` berupa array baris:

```json
{
  "row": 2026,
  "columns": [
    { "name": "Year", "value": "-36.53", "color": "#E70000" },
    { "name": "Oct", "value": "-15.64", "color": "#E70000" },
    { "name": "Sep", "value": "-6.18", "color": "#C20D0D" }
  ]
}
```

`up`, `down`, `total_months`, `avg`, `prob` masing-masing:

```json
{
  "columns": [
    { "name": "Jan", "value": "2", "color": "#FFFFFF" },
    { "name": "Feb", "value": "3", "color": "#FFFFFF" }
  ]
}
```

**Status:** ✅ 200.

#### 5.4.5 `GET /company-price-feed/market-time`

Status sesi pasar.

```json
{
  "message": "Successfully get market time data",
  "data": {
    "datetime": "2026-10-23 11:31:19",
    "detail": {
      "fca": {
        "session": 2,
        "state_name": "STATE_NAME_BREAK",
        "is_last_session": false,
        "is_end_of_day": false,
        "state_start_time": "11:30:00",
        "state_end_time": "13:59:59",
        "time_left": { "raw": 8920, "formatted": "2 jam 28 menit 40 detik" },
        "suspend_info": ""
      },
      "regular": { }
    }
  }
}
```

`state_name` yang ditemukan: `STATE_NAME_BREAK`, dan enum sesi `SESSION_TYPE_SESSION_1..5`, `SESSION_TYPE_MARKET_BREAK`, `SESSION_TYPE_POST_CLOSING`, `SESSION_TYPE_MARKET_CLOSE`. Fase: `SESSION_PHASE_ORDER_COLLECTION`, `SESSION_PHASE_RANDOM_CLOSING`, `SESSION_PHASE_ORDER_MATCHING`.

**Status:** ✅ 200.

#### 5.4.6 `GET /company-price-feed/market-time/session`

Sama seperti `market-time`, fokus pada detail sesi. Respons yang diamati identik secara struktur.

**Status:** ✅ 200.

#### 5.4.7 `GET /orderbook/companies/{symbol}` (v1)

Orderbook ringkas 10 level.

**Respons 200 — field level atas:**

```
average, bid, change, close, country, domestic, down, exchange, fbuy, fnet,
foreign, frequency, fsell, high, id, lastprice, low, offer, open,
percentage_change, previous, status, symbol, symbol_2, symbol_3, tradable,
unchanged, up, value, volume, corp_action, notation, uma, has_foreign_bs,
iepiev, market_data, name, icon_url, ara, arb, company_type,
total_bid_offer, next_ara, next_arb, autoreject_time_left_in_sec, ...
```

`bid` dan `offer` adalah **objek** dengan kunci `price1..price10`, `que_num1..que_num10`, `volume1..volume10` (bukan array). Jumlah level aktual bisa kurang dari 10.

```text
"bid": {
  "price1": "5100", "que_num1": "312", "volume1": "1315900",
  "price2": "5075", "que_num2": "399", "volume2": "3046700"
}
```

**Status:** ✅ 200.

#### 5.4.8 `GET /company-price-feed/v2/orderbook/companies/{symbol}` (v2)

Orderbook lengkap (semua level) plus data foreign/domestic.

**Respons 200 — field level atas:**

```
ara, arb, auto_reject_estimation, autoreject_time_left_in_sec, average,
bid, change, close, company_type, corp_action, country, domestic, down,
exchange, fbuy, fnet, foreign, frequency, fsell, has_foreign_bs, high,
icon_url, id, iepiev, lastprice, low, market_data, name, next_ara, next_arb,
notation, offer, open, orderbook_active_feature_mobile, percentage_change,
previous, status, symbol, symbol_2, symbol_3, total_bid_offer, tradable,
uma, unchanged, up, value, volume
```

`bid[]` / `offer[]`:

```json
{
  "price": "5100",
  "que_num": "322",
  "volume": "1323000",
  "change_percentage": ""
}
```

**Status:** ✅ 200.

#### 5.4.9 `GET /company-price-feed/v2/orderbook/template/{id}`

Orderbook untuk daftar kustom (watchlist orderbook).

- `GET /orderbook` → daftar template (dari kode).
- `GET /company-price-feed/v2/orderbook/template/{id}` → isi template.
- Header `x-platform: web` / `X-Platform: web`.

**Status:** 🟡 `id=1` → 404 `{"message":"Id tidak ditemukan","error_type":"NOT_FOUND"}`. Butuh ID template yang valid.

#### 5.4.10 `GET /charts/{symbol}/daily`

Chart OHLC/line.

**Parameter**

| Nama | Wajib | Nilai |
|---|---|---|
| `timeframe` | ya | lihat tabel di bawah |
| `from` | tidak | Tanggal awal |
| `to` | tidak | Tanggal akhir |
| `interval` | tidak | Interval menit |
| `chart_type` | tidak | Tipe chart |
| `is_include_previous_historical` | tidak | `true` untuk YTD/1W (dari kode) |

**Timeframe yang diuji (semua 200):**

| Timeframe | Jumlah `prices` (BBCA, 23 Okt 2026) | Catatan |
|---|---|---|
| `today` | 151 | Intraday menit |
| `1d` | 350 | |
| `1w` | 28 | |
| `1m` | 23 | |
| `3m` | 65 | |
| `6m` | 193 | |
| `1y` | 240 | |
| `3y` | 714 | |
| `5y` | 1200 | |
| `10y` | 193 | Granularitas lebih kasar |
| `ytd` | 193 | |
| `max` | 193 | |

**Respons 200 — field level atas:**

```
cagr, change, drawdown, markingpoint, percentage, prices, timeframe,
xaxisopt, previous, line_weight, previous_timeframe_price, chart_type,
interval_in_minutes, allowed_chart_type, max_candles
```

`prices[]`:

```json
{
  "date": "0",
  "formatted_date": "2026-10-23 08:58:00",
  "xlabel": "0",
  "value": "5175",
  "percentage": "0.00",
  "change": 0,
  "open": "",
  "high": "",
  "low": "",
  "volume": ""
}
```

**Status:** ✅ 200.

#### 5.4.11 `GET /charts/{symbol}` (v2)

Versi lama/alternatif dari chart.

**Parameter:** `timeframe`.

**Perilaku yang diamati untuk BBCA:**

| Timeframe | Status | `prices` |
|---|---|---|
| `1d`, `1m`, `1y`, `3y`, `5y`, `ytd` | 200 | kosong (`[]`) |
| `today`, `1w`, `6m`, `10y`, `max` | 400 | — |

Jadi endpoint ini **mengembalikan 200 tetapi dataset kosong** untuk BBCA. Kemungkinan deprecated atau memerlukan parameter tambahan.

**Status:** 🟡 tidak berguna untuk data historis saat ini.

#### 5.4.12 `GET /chartbit/{symbol}/price/daily`

OHLCV harian dari Chartbit.

**Parameter**

| Nama | Wajib | Keterangan |
|---|---|---|
| `from` | ya | `YYYY-MM-DD` |
| `to` | ya | `YYYY-MM-DD` |
| `limit` | ya | `0` = semua |

Contoh:

```http
GET /chartbit/BBCA/price/daily?from=2026-10-23&to=2025-08-01&limit=0
```

**Respons 200 — field:**

```
chartbit[], allow_decimal, last_data, previous_timestamp
```

`chartbit[]`:

```json
{
  "date": "2026-10-23",
  "unixdate": 1792688400,
  "open": 5175,
  "high": 5225,
  "low": 5050,
  "close": 5125,
  "volume": 239850000,
  "foreignbuy": 386010572500,
  "foreignsell": 1007434722500,
  "frequency": 34649,
  "foreignflow": -60348686760010,
  "soxclose": 631784631250000,
  "dividend": 0,
  "value": 1232026395000,
  "shareoutstanding": 123275050000,
  "freq_analyzer": 5.765906661567511,
  "lot": 2398500
}
```

**Catatan:**

- `from` lebih besar dari `to` pada contoh (dipakai terbalik); server tetap mengembalikan data.
- 297 baris untuk rentang ±1 tahun.
- `foreignflow` dan `soxclose` terlihat tidak wajar (bug data); jangan dipakai tanpa validasi.

**Status:** ✅ 200.

#### 5.4.13 `GET /chartbit/{symbol}/price/intraday`

**Parameter**

| Nama | Wajib | Keterangan |
|---|---|---|
| `from` | ya | Unix detik |
| `to` | ya | Unix detik |
| `limit` | ya | `0` |

**Respons:**

```json
{
  "allow_decimal": 0,
  "chartbit": [
    {
      "close": 5125,
      "datetime": "2026-10-23 11:29:00",
      "foreign_buy": 0,
      "foreign_sell": 0,
      "frequency": "116",
      "high": 5125,
      "low": 5100,
      "open": 5125,
      "symbol": "BBCA",
      "unix_timestamp": "1792729740",
      "value": 3036767500,
      "volume": "592600",
      "lot": 5926
    }
  ]
}
```

**Status:** ✅ 200.

#### 5.4.14 Chartbit lain

| Endpoint | Keterangan | Status |
|---|---|---|
| `GET /chartbit/charts` | Daftar layout chart tersimpan | ✅ 200 |
| `GET /chartbit/charts/{id}` | Isi layout | ✅ 200 |
| `GET /chartbit/studies` | Daftar studi/indikator | ✅ 200 |
| `GET /chartbit/chart-drawings?chart_id=&layout_id=&symbol=` | Gambar/garis chart | ✅ 200 |
| `GET /chartbit/search` | Pencarian chartbit | ⛔ 404 |

`/chartbit/charts/{id}` mengembalikan `data.content` berupa **string base64 dari file ZIP** (`UEsDBA...` = header ZIP). Isi ZIP adalah `layout.json`.

### 5.5 Order flow dan broker

#### 5.5.1 `GET /order-trade/broker/top`

Peringkat broker.

**Parameter**

| Nama | Nilai |
|---|---|
| `sort` | `TB_SORT_BY_TOTAL_VALUE` (dipakai web), `TB_SORT_BY_CODE` |
| `order` | `ORDER_BY_DESC`, `ORDER_BY_ASC` |
| `period` | lihat enum `TB_PERIOD_*` di bagian 6 |
| `market_type` | `MARKET_TYPE_ALL`, `MARKET_TYPE_REGULER`, `MARKET_TYPE_TUNAI`, `MARKET_TYPE_NEGO` |
| `eod_only` | `true`/`false` |

> Enum `TB_SORT_BY_*` di bundle hanya berisi dua nilai (`TOTAL_VALUE`, `CODE`). Nilai sort lain mungkin diterima server, tetapi tidak terverifikasi. Gunakan `TOTAL_VALUE` untuk peringkat nilai transaksi.

**Respons 200 — field:**

```
date: { from, to, idx }, list[], is_mid_day, is_break_time
```

`list[]`:

```json
{
  "code": "AK",
  "name": "UBS Sekuritas Indonesia",
  "investor_type": "INVESTOR_TYPE_UNSPECIFIED",
  "total_value": "4713589987040",
  "net_value": "13596698300",
  "buy_value": "2363593342670",
  "sell_value": "2349996644370",
  "total_volume": "6157926702",
  "total_frequency": "384681",
  "group": "BROKER_GROUP_FOREIGN"
}
```

**Status:** ✅ 200.

#### 5.5.2 `GET /order-trade/broker/activity`

Aktivitas broker per saham.

**Parameter**

| Nama | Wajib | Nilai |
|---|---|---|
| `broker_code` | ya | `XL`, `AK`, ... |
| `limit` | ya | mis. `50` |
| `page` | ya | `1` |
| `transaction_type` | ya | `TRANSACTION_TYPE_NET` |
| `market_board` | ya | **`MARKET_TYPE_REGULER`** (perhatikan: memakai enum MARKET_TYPE, bukan MARKET_BOARD) |
| `investor_type` | ya | `INVESTOR_TYPE_ALL` |
| `period` | ya | `RT_PERIOD_LAST_1_DAY`, ... |

**Respons 200 — field:**

```
broker_activity_transaction: { brokers_buy[], brokers_sell[] },
from, to, broker_code, broker_name
```

`brokers_buy[]`:

```json
{
  "stock_code": "BBCA",
  "broker_code": "XL",
  "type": "BROKER_TYPE_LOCAL",
  "date": "2026-10-22",
  "value": 58424012500,
  "lot": 112270,
  "avg_price": 5199.558726328699,
  "freq": 13811,
  "company_detail": {
    "icon_url": "...",
    "corpaction": { "active": false, "icon": "...", "text": "..." },
    "notation": []
  },
  "nval_trend": []
}
```

**Status:** ✅ 200.

#### 5.5.3 `GET /order-trade/broker/activity-chart`

Grafik aktivitas broker per menit.

**Parameter**

| Nama | Wajib | Nilai |
|---|---|---|
| `period` | ya | `RT_PERIOD_LAST_1_DAY` |
| `brokers_code` | ya | **plural** `brokers_code`, mis. `XL` |
| `investor_type` | ya | `INVESTOR_TYPE_ALL` |
| `market_board` | ya | `BOARD_TYPE_REGULAR` |

**Respons 200 — field:**

```
from, to, data_last_updated, chart_data[], date_session_info,
broker_code, broker_name
```

`chart_data[]`:

```json
{
  "type": "TYPE_CHART_VALUE",
  "symbols": ["BBCA", "BRIS", "VKTR", "BMRI", "BBRI", "SINI"],
  "charts": [
    {
      "symbol": "BBRI",
      "chart": [
        {
          "date": "2026-10-22",
          "time": "09:00",
          "value": { "raw": "-5254066000", "formatted": "(5.3B)" },
          "datetime_label": "09:00"
        }
      ]
    }
  ]
}
```

**Status:** ✅ 200.

#### 5.5.4 `GET /order-trade/trade-book`

Trade book per harga/waktu.

**Parameter**

| Nama | Wajib | Nilai |
|---|---|---|
| `symbol` | ya | `BBCA` |
| `group_by` | **ya** | `GROUP_BY_PRICE`, `GROUP_BY_TIME` (nilai lain dari enum) |
| `limit` | ya | `50` |
| `page` | ya | `1` |

Tanpa `group_by` → 400 `{"message":"Group by is required"}`.

**Respons 200 — field:**

```
book[], market_hour_steps, book_total, is_show_pre_post, is_fca_stock,
date, previous_price, from, to, first_available_date
```

`book[]`:

```json
{
  "price": "5,225",
  "buy": {
    "lot": "5,836",
    "frequency": "84",
    "percentage": "100%",
    "value": "3.05B",
    "value_percentage": "100%",
    "value_raw": 3049310000
  },
  "sell": {
    "lot": "-",
    "frequency": "-",
    "percentage": "0%",
    "value": "-",
    "value_percentage": "0%",
    "value_raw": 0
  },
  "time": "",
  "pre_open": { },
  "post_close": { }
}
```

**Status:** ✅ 200.

#### 5.5.5 `GET /order-trade/running-trade`

Running trade (tape).

**Parameter**

| Nama | Wajib | Keterangan |
|---|---|---|
| `symbols` | ya | Repeat, mis. `symbols=BBCA&symbols=BBRI` |
| `sort` | ya | `DESC` / `ASC` |
| `limit` | ya | `80` |
| `order_by` | ya | `RUNNING_TRADE_ORDER_BY_TIME` (nilai lain dari enum) |

**Respons 200 — field `data.running_trade[]`:**

```json
{
  "id": "0",
  "time": "11:29:56",
  "action": "buy",
  "code": "BBCA",
  "price": "5,125",
  "change": "-0.97%",
  "lot": "1",
  "is_broker_exists": false,
  "buyer": "",
  "seller": "",
  "trade_number": "1064116",
  "buyer_type": "BROKER_TYPE_UNSPECIFIED",
  "seller_type": "BROKER_TYPE_UNSPECIFIED",
  "market_board": "RG",
  "buy_order_number": "0",
  "sell_order_number": "0",
  "group_order_number": "0",
  "value": { "raw": 512500, "formatted": "512.5K" }
}
```

**Status:** ✅ 200.

#### 5.5.6 `GET /order-trade/running-trade/group`

Running trade yang dikelompokkan per order.

**Parameter**

| Nama | Wajib | Keterangan |
|---|---|---|
| `symbols` | ya | Repeat |
| `order_by` | **ya** | `RUNNING_TRADE_ORDER_BY_TIME` |
| `sort` | ya | `DESC` |
| `limit` | ya | `20` |

Tanpa `order_by` → 400 `{"message":"OrderBy wajib diisi"}`.

**Respons 200 — field:**

```
total, running_trade_group[], date, single_order
```

`running_trade_group[]`:

```json
{
  "id": "102832747",
  "order_number": "5276326",
  "action": "RUNNING_TRADE_ACTION_TYPE_BUY",
  "group_action": "RUNNING_TRADE_ACTION_TYPE_BUY",
  "time": "16:25:20",
  "trade_number": "2102713",
  "code": "BBCA",
  "market_board": "NG",
  "price": { "raw": "5175", "formatted": "5,175" },
  "change": { "raw": -1.8957345971563981, "formatted": "-1.90%" },
  "lot": { "raw": 0.94, "formatted": "0.94" },
  "freq": { "raw": "1", "formatted": "1" },
  "is_broker_exists": true,
  "buyer": [ { "broker_code": "AK [F]", "broker_type": "BROKER_TYPE_FOREIGN" } ],
  "seller": [ ]
}
```

**Status:** ✅ 200.

#### 5.5.7 `GET /marketdetectors/{symbol}`

Bandar detector + ringkasan broker.

**Parameter**

| Nama | Nilai |
|---|---|
| `transaction_type` | `TRANSACTION_TYPE_NET` |
| `market_board` | `MARKET_BOARD_REGULER` |
| `investor_type` | `INVESTOR_TYPE_ALL` |
| `limit` | `25` |
| `period` | `BROKER_SUMMARY_PERIOD_LATEST`, ... |

**Respons 200 — field:**

```
bandar_detector, broker_summary, from, to
```

`bandar_detector`:

```json
{
  "average": 5201.142,
  "avg": { "accdist": "Big Dist", "amount": -189622580000, "percent": -30.803362, "vol": -364578.72 },
  "avg5": { "accdist": "Big Dist", "amount": -168999260000, "percent": -27.453192, "vol": -324927.2 },
  "broker_accdist": "Dist",
  "number_broker_buysell": 36,
  "top1": { "accdist": "Normal Dist", "amount": -78581980000, "percent": -12.7653, "vol": -151086 }
}
```

`broker_summary`:

```json
{
  "symbol": "BBCA",
  "brokers_buy": [
    {
      "blot": "429183",
      "blotv": "4.99712e+07",
      "bval": "2.23186585e+11",
      "bvalv": "2.5995577e+11",
      "netbs_broker_code": "SQ",
      "netbs_buy_avg_price": "5202.11181640625",
      "netbs_date": "20261022",
      "netbs_stock_code": "BBCA",
      "type": "Lokal",
      "freq": "4110"
    }
  ],
  "brokers_sell": []
}
```

**Catatan:** angka `blotv`, `bval`, `bvalv` memakai notasi ilmiah string; konversi ke `float` sebelum diolah.

**Status:** ✅ 200.

#### 5.5.8 `GET /findata-view/marketdetectors/brokers`

Daftar **master broker** (untuk filter/dropdown), bukan ringkasan transaksi.

**Parameter:** `page` (wajib), `limit`, serta parameter periode/transaksi yang diabaikan.

**Respons 200 — `data[]`:**

```json
{
  "id": 110,
  "code": "AD",
  "name": "Sukadana Prima Sekuritas",
  "permission": "Penjamin Emisi Efek, Perantara Pedagang Efek",
  "group": "Lokal",
  "color": "#7924c3",
  "membership_type": "MEMBERSHIP_TYPE_EXCHANGE_MEMBER"
}
```

**Status:** ✅ 200. Tanpa `page` kemungkinan 400 (page wajib).

### 5.6 Fundamental dan analyst

#### 5.6.1 `GET /findata-view/company/financial`

Laporan keuangan.

**Parameter**

| Nama | Wajib | Nilai yang diuji | Keterangan |
|---|---|---|---|
| `symbol` | ya | `BBCA` | |
| `data_type` | ya | `1` | Hanya `1` yang diterima; `2`/`3` → 400 |
| `report_type` | ya | `1`, `2` | `1` = laporan utama; `2` = rasio |
| `statement_type` | ya | `1`, `2`, `3` | Memengaruhi periode/statement default |

**Respons 200 — field:**

```
currency, default_currency, html_report, rounding_value, data_tables
```

`data_tables`:

```json
{
  "periods": [],
  "accounts": [],
  "max_show_level": 2
}
```

**Temuan penting:**

- `periods` dan `accounts` **selalu kosong** pada pengujian; data sebenarnya ada di `html_report` (HTML server-rendered, 200 KB–1 MB).
- `html_report` berisi tabel dengan `totalPeriods` (mis. 74 kuartal) dan seluruh angka.
- `data_type=2` dan `3` → 400 `"Your request is invalid"`.
- `report_type=2` menghasilkan konten rasio (mis. `LT Debt/Total Assets (Quarter)`).
- `statement_type=1` dan `3` menampilkan periode kuartalan (`Q1 2008 ...`), `statement_type=2` menampilkan periode tahunan (`12M 2008 ...`). Mapping pasti tidak didokumentasikan; verifikasi dengan konten HTML.

**Ukuran respons:** 228 KB (st=2) hingga 1 MB (rt=2). Cache hasilnya, jangan panggil berulang.

**Status:** ✅ 200.

#### 5.6.2 `GET /keystats/ratio/v1/{symbol}`

Key statistics dan rasio.

**Parameter:** `year_limit` (mis. `10`).

**Respons 200 — field:**

```
closure_fin_items_results, financial_year_parent, stats, info,
dividend_group, financial_report_currency
```

`closure_fin_items_results[]`:

```json
{
  "fin_name_results": [
    {
      "fitem": { "id": "12148", "name": "Current PE Ratio (Annualised)", "value": "10.70" },
      "hidden_graph_ico": false,
      "is_new_update": false
    }
  ]
}
```

`dividend_group`:

```json
{
  "fitem_id": ["21507", "21509", "21508"],
  "dividend_year_values": [
    {
      "period": 2026,
      "dividend": "25.00",
      "ex_date": "31 Aug 26",
      "payment_date": "16 Sep 26"
    }
  ]
}
```

**Status:** ✅ 200.

#### 5.6.3 `GET /findata-view/foreign-domestic/v1/chart-data/{symbol}`

Aliran dana asing vs domestik.

**Parameter**

| Nama | Nilai |
|---|---|
| `market_type` | `MARKET_TYPE_REGULAR` (perhatikan: `REGULAR`, bukan `REGULER`) |
| `period` | `PERIOD_RANGE_1D` (nilai lain belum diuji) |

**Respons 200 — field:**

```
summary, value, volume, frequency, last_updated, from, to
```

`summary`:

```json
{
  "date_range": "22 Oct 2026",
  "foreign_buy": { "label": "F Buy", "value": { "raw": 386010572500, "formatted": "386.01 B" } },
  "foreign_sell": { "label": "F Sell", "value": { "raw": 1007434722500, "formatted": "1.01 T" } },
  "net_foreign": { "label": "Net Foreign Sell (Regular)", "value": { "raw": -621424150000, "formatted": "-621.42 B" } },
  "domestic_buy": { "label": "D Buy", "value": { "raw": 1105206450000, "formatted": "1.11 T" } },
  "domestic_sell": { "label": "D Sell", "value": { "raw": 0, "formatted": "" } }
}
```

**Status:** ✅ 200.

#### 5.6.4 `GET /analyst-ratings/{symbol}`

Ringkasan rating analis.

```json
{
  "message": "Successfully retrieved analyst ratings data",
  "data": {
    "price_target": {
      "best_target": 8051,
      "best_low_target": 5900,
      "best_high_target": 10100,
      "current_price": 5125
    },
    "recommendation": "Buy",
    "total_buy": 35,
    "total_sell": 0,
    "total_hold": 2,
    "total_analyst": 37,
    "last_updated": "19 Oct 26"
  }
}
```

**Status:** ✅ 200.

#### 5.6.5 `GET /analyst-ratings/{symbol}/consensus`

Konsensus estimasi analis.

```json
{
  "message": "Successfully retrieved analyst consensus data",
  "data": [
    {
      "name": "Revenue",
      "items": [
        { "year": 2025, "is_estimate": false, "value": "118,573 B", "raw_value": 0 },
        { "year": 2026, "is_estimate": true, "value": "117,181 B", "raw_value": 0 }
      ]
    },
    {
      "name": "Op. Profit",
      "items": [ ]
    }
  ]
}
```

**Catatan:** `raw_value` bernilai 0 untuk semua item yang diamati; gunakan `value` yang sudah diformat.

**Status:** ✅ 200.

### 5.7 Corporate action

#### 5.7.1 `GET /corpaction`

Aksi korporasi **hari ini**, dikelompokkan per tipe.

**Respons 200 — `data` adalah objek dengan kunci:**

```
bonus, dividend, economic, ipo, pubex, rightissue, rups,
stock_reverse, stocksplit, tender, warrant, stock_dividend
```

Masing-masing berisi array item. Item `dividend`:

```json
{
  "company_id": "54",
  "company_symbol": "BBCA",
  "corp_action_active": false,
  "dividend_cumdate": "2026-08-28",
  "dividend_exdate": "2026-08-31",
  "dividend_paydate": "2026-09-16",
  "dividend_recdate": "2026-09-01",
  "dividend_value": "25",
  "dividend_value_formatted": "Rp 25",
  "dividend_currency": "CURRENCY_IDR"
}
```

**Status:** ✅ 200.

#### 5.7.2 `GET /corpaction/{action}`

Aksi korporasi per tipe.

**Nilai `action`:** `dividend`, `bonus`, `economic`, `ipo`, `pubex`, `rightissue`, `rups`, `stock_reverse`, `stocksplit`, `tender`, `warrant`, `stock_dividend`.

**Query:** `symbol`, `limit`, `page`.

Contoh:

```http
GET /corpaction/dividend?symbol=BBCA&limit=30
```

**Respons:**

```json
{
  "message": "Successfully retrieved dividend data",
  "data": {
    "dividend": [ { "company_symbol": "BBCA", "dividend_value": "25" } ],
    "today": false
  }
}
```

Item `dividend` memiliki field lain (tanggal, datahash, dan sebagainya) yang dihilangkan di contoh.

**Status:** ✅ 200.

#### 5.7.3 `GET /corpaction/{symbol}`

Semua aksi korporasi untuk satu saham.

**Query:** `limit`, `page`.

**Respons:** array item dengan `action_type` dan `action_info`:

```json
{
  "action_type": "dividend",
  "action_info": {
    "dividend": {
      "company_symbol": "BBCA",
      "dividend_exdate": "2026-08-31",
      "dividend_paydate": "2026-09-16",
      "dividend_value": "25",
      "dividend_value_formatted": "Rp 25"
    }
  }
}
```

**Status:** ✅ 200.

#### 5.7.4 `GET /corpaction/{symbol}/stock_conversion`

Konversi saham (mis. reverse stock).

**Query:** `page`, `limit`.

**Respons:**

```json
{ "message": "...", "data": { "conversion": [] } }
```

Untuk BBCA kosong. **Status:** ✅ 200.

### 5.8 Insider dan shareholder

#### 5.8.1 `GET /insider/company/majorholder`

Perubahan kepemilikan pemegang saham besar.

**Parameter**

| Nama | Wajib | Keterangan |
|---|---|---|
| `symbol` | ya | `BBCA` |
| `insider` | tidak | Nama insider |
| `date_start` | tidak | `YYYY-MM-DD` |
| `date_end` | tidak | `YYYY-MM-DD` |
| `page` | tidak | Default kosong; web mengirim `1` |

**Respons 200 — field:**

```
is_more, movement[]
```

`movement[]`:

```json
{
  "id": "1000000439",
  "name": "HENDRA TANUMIHARDJA",
  "symbol": "BBCA",
  "date": "25 Mar 26",
  "previous": { "value": "193,206", "percentage": "0.0002", "formatted_value": "" },
  "current": { "value": "341,139", "percentage": "0.0003", "formatted_value": "" },
  "changes": { "value": "+147,933", "percentage": "+0.0001", "formatted_value": "147,933" },
  "marker": "",
  "is_posted": false,
  "cmh_id": "0",
  "nationality": "NATIONALITY_TYPE_LOCAL",
  "action_type": "ACTION_TYPE_BUY",
  "data_source": { "label": "Sumber: IDX", "type": "SOURCE_TYPE_IDX" },
  "price_formatted": "6,982",
  "broker_detail": { "code": "", "group": "BROKER_GROUP_UNSPECIFIED" },
  "badges": []
}
```

**Status:** ✅ 200.

#### 5.8.2 `GET /insider/shareholding/composition/companies/{symbol}`

Komposisi kepemilikan per periode — sumber pie chart **Composition** dengan dua tab: **All** dan **Scripless**.

**Parameter**

| Nama | Wajib | Nilai |
|---|---|---|
| `symbol` | path | Kode saham (`BBCA`) |
| `period_start` | tidak | `YYYY-MM-DD`; tanpa ini hanya periode terbaru yang dikembalikan |
| `period_end` | tidak | `YYYY-MM-DD` |
| `view` | tidak | `SHAREHOLDERS_COMPOSITION_VIEW_ALL` (default) atau `SHAREHOLDERS_COMPOSITION_VIEW_SCRIPPLESS` |

Nilai `view` lain (mis. `scripless`) → 400 `INVALID_PARAMETER`.

**Respons 200 — field:**

```
periods[], first_available_date, last_available_date, view
```

`periods[]`:

```json
{
  "report_date": "2026-09-30",
  "previous_report_date": "2026-08-31",
  "total_shares": { "raw": "123275050000", "formatted": "123.28B" },
  "total_scrip": { "raw": "70821358880", "formatted": "70.82B" },
  "total_scripless": { "raw": "52453691120", "formatted": "52.45B" },
  "scrip_percentage": { "raw": 57.45, "formatted": "57.45%" },
  "scripless_percentage": { "raw": 42.55, "formatted": "42.55%" },
  "compositions": [
    {
      "label": "DWIMURIA INVESTAMA ANDALAN",
      "shares": { "raw": "67729950000", "formatted": "67.73B" },
      "percentage": { "raw": 54.94213954891927, "formatted": "54.94%" },
      "colors": { "light": "#0BA16B", "dark": "#0BA16B" },
      "previous_shares": { "raw": "67729950000", "formatted": "67.73B" },
      "previous_percentage": { "raw": 54.94213954891927, "formatted": "54.94%" }
    }
  ]
}
```

**Perbedaan `view`:**

| View | Isi `compositions[]` | Denominator | Jumlah persentase |
|---|---|---|---|
| `..._VIEW_ALL` | Pemegang saham **bernama yang memiliki saham scrip** + kategori agregat scripless | `total_shares` | ~100% (99,58% untuk BBCA) |
| `..._VIEW_SCRIPPLESS` | Hanya kategori agregat kepemilikan scripless | `total_scripless` | 100% |

- `ALL` untuk BBCA: 38 label — 3 pemegang scrip bernama (DWIMURIA 54,94%, TRICIPTA 1,07%, CATURGUWIRATNA 1,02%) + kategori agregat.
- `ANTHONI SALIM` (1,15%) **tidak muncul** di view `ALL` karena seluruh kepemilikannya scripless; ia hanya tampil di `shareholder_one_percent` dan view `SCRIPPLESS`.
- `SCRIPPLESS` untuk BBCA: kategori (`Mutual Funds`, `Individual`, `Pension Funds`, `Insurance`, `Exchange Traded Funds`, `Sovereign Wealth Fund`, `Bank`, `Central Bank`, `Trustee Bank`, `Corporate`, `Partnership`, `Government`, `Foundation`, `Securities Company`, dst.).
- `colors.light`/`colors.dark` dipakai UI untuk pie chart; nilainya dapat berulang antar-label.

**Rentang periode:**

- `period_start` + `period_end` mengembalikan satu objek per bulan (mis. 8 periode untuk setahun), diurutkan dari terlama ke terbaru.
- Tanpa rentang, hanya periode terbaru yang dikembalikan.

> **Bug data yang teramati (v3.54.10):** saat memakai rentang, periode **Jul–Sep 2026** mengembalikan `total_shares.raw = "1"`, `total_scrip` negatif, dan persentase `ALL` membengkak tidak wajar (total 12 triliun %). `view=SCRIPPLESS` pada periode yang sama tetap benar karena memakai `total_scripless` sebagai denominator. Untuk snapshot terbaru, panggil **tanpa** `period_start`/`period_end`.

**Status:** ✅ 200 (BBCA, kedua view; rentang 8 periode diuji).

#### 5.8.3 `GET /insider/shareholding/ubo/companies/{symbol}`

Ultimate Beneficial Owner **per emiten** — dipakai halaman profil untuk blok "UBO".

**Parameter**

| Nama | Wajib | Keterangan |
|---|---|---|
| `symbol` | path | Kode saham (`BBCA`, `CUAN`) |

**Respons 200 — field:**

```
company_symbol, to_report_date, from_report_date, owners[]
```

`owners[]`:

```json
{
  "name": "ROBERT BUDI HARTONO",
  "ownership_percentage": {
    "to": { "raw": 55, "formatted": "55.00%" },
    "from": { "raw": 55, "formatted": "55.00%" }
  },
  "subholdings": [
    {
      "name": "PT DWIMURIA INVESTAMA ANDALAN",
      "ownership_percentage": {
        "to": { "raw": 55, "formatted": "55.00%" },
        "from": { "raw": 55, "formatted": "55.00%" }
      }
    }
  ]
}
```

- `to` = `to_report_date`, `from` = `from_report_date` (bulan sebelumnya). Berguna untuk melihat perubahan bulanan.
- `subholdings[]` adalah jalur kepemilikan perantara (mis. BCA → DWIMURIA → Robert Budi Hartono).
- CUAN mengembalikan satu owner `PRAJOGO PANGESTU` 80.42% tanpa subholding; BBCA mengembalikan `ROBERT BUDI HARTONO` 55% via `PT DWIMURIA INVESTAMA ANDALAN`.

**Status:** ✅ 200 (BBCA, CUAN).

#### 5.8.4 `GET /insider/shareholding/companies/{company_id}`

Daftar pemegang saham **langsung** untuk satu perusahaan — sumber tab "Pemegang Saham".

**Parameter**

| Nama | Wajib | Keterangan |
|---|---|---|
| `company_id` | path | **Company ID numerik**, bukan symbol. BBCA=`54`, BRPT=`93`, CUAN=`1000003994` |

Cara mendapatkan ID: [`GET /emitten/{symbol}/info`](#521-get-emittensymbolinfo) → `data.id`.

**Respons 200 — field:**

```
id, symbol, name, icon_url, report_date,
holders[], grand_total, first_available_date, last_available_date
```

`holders[]`:

```json
{
  "id": "129757",
  "company": null,
  "investor": {
    "id": 8911,
    "name": "DWIMURIA INVESTAMA ANDALAN",
    "investor_type": { "raw": "CP", "formatted": "CP" },
    "location": { "raw": "L", "formatted": "Local" },
    "nationality": { "raw": "", "formatted": "-" },
    "domicile": { "raw": "INDONESIA", "formatted": "INDONESIA" },
    "investor_classification": { "raw": "Corporate", "formatted": "Corporate" }
  },
  "shareholding": {
    "scripless": { "raw": "0", "formatted": "0.00" },
    "scrip": { "raw": "67729950000", "formatted": "67.73 B" },
    "total_shares": { "raw": "67729950000", "formatted": "67.73 B" },
    "percentage": { "raw": 54.94, "formatted": "54.94%" },
    "value": { "raw": "435706635272625", "formatted": "435.71 T" }
  },
  "previous_shareholding": { "...": "bentuk sama dengan shareholding" },
  "change": {
    "total_shares": { "raw": "0", "formatted": "-" },
    "percentage": { "raw": 0, "formatted": "-" },
    "scrip": { "absolute": { "raw": "0", "formatted": "-" }, "percentage": { "raw": 0, "formatted": "-" } },
    "scripless": { "absolute": { "raw": "0", "formatted": "-" }, "percentage": { "raw": 0, "formatted": "-" } }
  },
  "report_date": "30 Sep 26"
}
```

`grand_total`:

```json
{
  "percentage": { "raw": 58.18, "formatted": "58.18%" },
  "total_shares": { "raw": "71721256835", "formatted": "71.72 B" },
  "scrip": { "raw": "70304950000", "formatted": "70.30 B" },
  "scripless": { "raw": "1416306835", "formatted": "1.42 B" },
  "value": { "raw": "435706635272625", "formatted": "435.71 T" },
  "change": { "raw": "0", "formatted": "" }
}
```

**Catatan:**

- `grand_total` adalah **jumlah holder yang dikembalikan**, bukan kapitalisasi penuh. Untuk BBCA hanya 58,18% karena holder <1% tidak masuk daftar.
- `company` selalu `null` di sisi holder; perusahaan ada di level respons.
- `investor.id` dapat dipakai untuk [`/insider/shareholding/investors/{investor_id}`](#585-get-insidershareholdinginvestorsinvestor_id) dan [`/insider/ubo`](#587-get-insideruboinvestor_idinvestor_id).
- `report_date` memakai format pendek (`30 Sep 26`), berbeda dari endpoint composition yang memakai `YYYY-MM-DD`.

**Error:**

- Symbol (`/companies/BBCA`) → 400 `{"message":"Invalid company id","error_type":"INVALID_PARAMETER"}`.
- Investor ID (`/companies/8991`) → 404 `{"message":"Company not found","error_type":"NOT_FOUND"}`.

**Status:** ✅ 200 (BBCA `54`, BRPT `93`, CUAN `1000003994`).

#### 5.8.5 `GET /insider/shareholding/investors/{investor_id}`

Detail kepemilikan **langsung** satu investor di semua emiten.

**Parameter**

| Nama | Wajib | Keterangan |
|---|---|---|
| `investor_id` | path | ID investor (mis. `8991` = Prajogo Pangestu) |
| `report_date` | tidak | `YYYY-MM-DD`; tanpa ini memakai laporan terbaru |
| `previous_report_date` | tidak | `YYYY-MM-DD`; untuk blok `previous_shareholding` |

**Respons 200 — field:**

```
id, name, type, location, nationality, domicile, report_date,
holdings[], classification, first_available_date, last_available_date, grand_total
```

`holdings[]`:

```json
{
  "id": "130912",
  "company": {
    "id": 1000003994,
    "symbol": "CUAN",
    "name": "Petrindo Jaya Kreasi Tbk.",
    "icon_url": "https://assets.stockbit.com/logos/companies/CUAN.png"
  },
  "investor": null,
  "report_date": "30 Sep 26",
  "shareholding": {
    "scripless": { "raw": "2265769458", "formatted": "2.27 B" },
    "scrip": { "raw": "88139129242", "formatted": "88.14 B" },
    "total_shares": { "raw": "90404898700", "formatted": "90.40 B" },
    "percentage": { "raw": 80.42, "formatted": "80.42%" },
    "value": { "raw": "76392139401500", "formatted": "76.39 T" }
  },
  "previous_shareholding": { "...": "bentuk sama" },
  "change": { "...": "bentuk sama dengan 5.8.4" }
}
```

**Catatan:**

- Endpoint ini hanya mengembalikan **kepemilikan langsung**. Prajogo (`8991`) → 3 holding: CUAN, BRPT, TPIA.
- Untuk kepemilikan **langsung + tidak langsung** (6 holding, termasuk CDIA/PTRO/BREN), pakai [`GET /insider/ubo?investor_id=`](#587-get-insideruboinvestor_idinvestor_id).
- `grand_total.percentage` menjumlahkan persentase lintas emiten sehingga bisa >100% (Prajogo: 156,82%). Jangan ditafsirkan sebagai porsi satu perusahaan.
- `grand_total.change` adalah perubahan nilai gabungan, bukan persentase.
- ID investor bisa didapat dari `profile.shareholder_one_percent[].id`, `holders[].investor.id` (5.8.4), atau hasil `/search?type=insider`.

**Error:**

- `investor_id=54` (company ID) → 404 `{"message":"Investor not found","error_type":"NOT_FOUND"}`.
- Symbol (`/investors/BBCA`) → 400 `{"message":"Invalid investor id","error_type":"INVALID_PARAMETER"}`.

**Status:** ✅ 200 (`investor_id=8991`, dengan dan tanpa `report_date`).

#### 5.8.6 `GET /insider/shareholding/network`

Graf jaringan kepemilikan (dipakai halaman `/ownership`). Menampilkan rantai investor ↔ perusahaan hingga kedalaman tertentu.

**Parameter**

| Nama | Wajib | Nilai |
|---|---|---|
| `root_id` | ya | ID node awal: investor ID (`8991`) atau company ID (`1000003994`) |
| `root_type` | ya | `SHAREHOLDING_NETWORK_NODE_TYPE_INVESTOR` atau `SHAREHOLDING_NETWORK_NODE_TYPE_COMPANY` |
| `max_depth` | tidak | Default `3` (konstanta client) |
| `max_edge_per_node` | tidak | Default `20` (konstanta client) |
| `report_date` | tidak | `YYYY-MM-DD` |

Nilai pendek seperti `INVESTOR`, `COMPANY`, atau `NODE_TYPE_INVESTOR` → 400 `{"message":"Your request is invalid","error_type":"INVALID_PARAMETER"}`.

**Respons 200 — field:**

```
nodes[], edges[]
```

`nodes[]`:

```json
{
  "id": "company:1000003994",
  "node_type": "SHAREHOLDING_NETWORK_NODE_TYPE_COMPANY",
  "metadata": {
    "company": {
      "id": 1000003994,
      "symbol": "CUAN",
      "name": "Petrindo Jaya Kreasi Tbk.",
      "icon_url": "https://assets.stockbit.com/logos/companies/CUAN.png"
    },
    "investor": null
  },
  "min_depth": 1,
  "is_rendered": true
}
```

`edges[]`:

```json
{
  "from_id": "investor:1000000349",
  "to_id": "company:432",
  "shareholding": {
    "scripless": { "raw": "0", "formatted": "0.00" },
    "scrip": { "raw": "13589972562", "formatted": "13.59 B" },
    "total_shares": { "raw": "13589972562", "formatted": "13.59 B" },
    "percentage": { "raw": 15.71, "formatted": "15.71%" },
    "value": null
  },
  "is_rendered": true
}
```

**Catatan:**

- Format `id` node: `investor:<id>` atau `company:<id>`; gunakan ini untuk mencocokkan `from_id`/`to_id`.
- `metadata.investor` dan `metadata.company` saling eksklusif; satu node hanya berisi salah satunya.
- `value` pada edge sering `null` — jangan diandalkan.
- `is_rendered` adalah petunjuk UI, bukan status kelengkapan data.
- Prajogo (`root_id=8991`, investor, depth 3, edge 20) → 15 node / 15 edge, mencakup CUAN, NCKL, BREN, TBIG, TPIA, BNLI, BRPT.
- Untuk perusahaan: `root_id=1000003994&root_type=SHAREHOLDING_NETWORK_NODE_TYPE_COMPANY` → 200.

**Status:** ✅ 200 (investor 8991 dan company 1000003994).

#### 5.8.7 `GET /insider/ubo?investor_id={investor_id}`

UBO **lintas emiten** untuk satu investor — menggabungkan kepemilikan langsung dan tidak langsung. Ini yang dipakai halaman `/ownership?investor=...` (bukan `/insider/shareholding/investors/{id}` yang hanya langsung).

**Parameter**

| Nama | Wajib | Keterangan |
|---|---|---|
| `investor_id` | ya | ID investor (`8991`) |
| `report_date` | tidak | `YYYY-MM-DD`; mendukung data historis (diuji `2026-06-30`) |

**Respons 200 — field:**

```
id, name, type, location, nationality, domicile, report_date,
holdings[], classification, first_available_date
```

`holdings[]`:

```json
{
  "id": "44380",
  "company": {
    "id": 1000003994,
    "symbol": "CUAN",
    "name": "Petrindo Jaya Kreasi Tbk.",
    "icon_url": "https://assets.stockbit.com/logos/companies/CUAN.png"
  },
  "investor": null,
  "report_date": "30 Sep 2026",
  "shareholding": {
    "total_shares": { "raw": "90404806164", "formatted": "90.40 B" },
    "percentage": { "raw": 80.42, "formatted": "80.42%" },
    "value": { "raw": "76392061208580", "formatted": "76.39 T" },
    "price": { "raw": "845", "formatted": "845.00" },
    "subholdings": []
  },
  "previous_shareholding": { "...": "bentuk sama" },
  "change": { "...": "bentuk sama dengan 5.8.4" }
}
```

**Contoh hasil untuk Prajogo (`8991`, 30 Sep 2026):**

| Emiten | Porsi | `subholdings` |
|---|---|---|
| CUAN | 80,42% | — |
| BRPT | 71,37% | — |
| CDIA | 60,00% | `PT CHANDRA ASRI PACIFIC TBK` (60%) |
| PTRO | 45,33% | `PT KREASI JASA PERSADA` (45,33%) |
| TPIA | 5,00% | — |
| BREN | 0,11% | — |

- Total 6 emiten, sedangkan `/insider/shareholding/investors/8991` hanya 3 (langsung).
- `shareholding.subholdings[]` berisi `{name, total_shares, percentage, value}` — perusahaan perantara yang membuat kepemilikan menjadi tidak langsung.
- `report_date` historis mengubah angka: 30 Jun 2026 → CUAN 80,37%, BREN 0,00%.

**Status:** ✅ 200 (`investor_id=8991`, snapshot terbaru dan `report_date=2026-06-30`).

### 5.9 Screener

#### 5.9.1 `GET /screener/templates`

Daftar screener milik pengguna.

```json
{
  "message": "Successfully retrieved your saved screener template",
  "data": [
    { "favorite": 0, "id": "4093464", "name": "Hancur", "type": "TEMPLATE_TYPE_CUSTOM" }
  ]
}
```

**Status:** ✅ 200.

#### 5.9.2 `GET /screener/preset`

Katalog template screener (tree).

**Respons:** array bertingkat:

```json
[
  {
    "id": 11,
    "name": "Guru Screener",
    "childs": [
      {
        "id": 1,
        "name": "Value Screener",
        "childs": [
          {
            "id": 2,
            "name": "Kenneth Fisher Price To Sales",
            "childs": [],
            "description": "",
            "image_url": null,
            "type": "TEMPLATE_TYPE_GURU",
            "header_color": null,
            "summary": null
          }
        ]
      }
    ]
  }
]
```

**Status:** ✅ 200.

#### 5.9.3 `GET /screener/templates/{id}`

Detail + hasil screener.

**Query:** `type=TEMPLATE_TYPE_GURU` atau `TEMPLATE_TYPE_CUSTOM`.

**Respons 200 — field:**

```
calcs, rules, columns, curpage, favorite, isguru, order, perpage,
screen_desc, screen_name, screenerid, sequence, sort, totalrows,
universe, type, screener_scope
```

`calcs[]`:

```json
{
  "company": {
    "country": "ID",
    "exchange": "IDX",
    "id": "1000000029",
    "name": "Transcoal Pacific Tbk.",
    "symbol": "TCPI",
    "symbol_2": "TCPI",
    "symbol_3": "TCPI",
    "type": "",
    "badges": { "is_new": false },
    "icon_url": "https://assets.stockbit.com/logos/companies/TCPI.png"
  },
  "results": [
    { "display": "53.96", "id": 2891, "item": "Current PE Ratio (TTM)", "raw": "53.96" }
  ]
}
```

`rules[]` berisi aturan filter; `columns[]` berisi kolom yang ditampilkan. **Status:** ✅ 200.

#### 5.9.4 `GET /screener/universe`

Pilihan universe (indeks, sektor, papan).

**Respons:** objek dengan kunci `index` (dan kemungkinan `sector`, `board`), berisi tree:

```json
{
  "index": [
    {
      "id": "0",
      "name": "IHSG",
      "scope": "IHSG",
      "list": [
        { "id": "559", "name": "IDX30", "scope": "idx" },
        { "id": "550", "name": "LQ45", "scope": "idx" }
      ]
    }
  ]
}
```

**Status:** ✅ 200.

#### 5.9.5 `GET /screener/favorites`

Daftar screener favorit.

```json
[
  { "id": 31, "name": "PE Strong Undervalued", "type": "TEMPLATE_TYPE_GURU", "order": 0 }
]
```

**Status:** ✅ 200.

#### 5.9.6 `GET /screener/metric`

Daftar metrik keuangan yang tersedia untuk screener.

```json
[
  {
    "fitem_id": "2892",
    "fitem_name": "Market Cap",
    "show_chart_icon": 1,
    "child": []
  }
]
```

**Status:** ✅ 200.

#### 5.9.7 `GET /screener/finitem-watchlist`

Daftar kolom metrik untuk watchlist.

```json
[
  { "fitem_id": "symbol", "fitem_name": "Alphabetical" },
  { "fitem_id": "fitemid_2661", "fitem_name": "Price" },
  { "fitem_id": "fitemid_2892", "fitem_name": "Market Cap" }
]
```

**Status:** ✅ 200.

#### 5.9.8 Endpoint tulis screener

| Method | Path | Body/Query | Status |
|---|---|---|---|
| POST | `/screener/templates` | Definisi screener (calcs/rules/columns/universe/name) | ✍️ |
| POST | `/screener/favorites` | `{screenerid, type}` | ✍️ |
| DELETE | `/screener/favorites/{id}?type=` | — | ✍️ |
| DELETE | `/screener/templates/{id}` | — | ✍️ |

Tidak diuji. Body pasti `POST /screener/templates` mengikuti struktur template yang dikembalikan `GET /screener/templates/{id}`.

### 5.10 Valuation

#### 5.10.1 `GET /valuation/all/templates`

Daftar template valuasi pengguna.

**Respons:** array. Untuk akun pengujian: `[]` (belum ada template).

**Status:** ✅ 200.

#### 5.10.2 `GET /valuation/metrics/lists`

Daftar metrik yang bisa dipilih untuk valuasi.

**Respons:**

```json
{
  "message": "...",
  "data": {
    "params": {
      "eps": [
        { "default": true, "fitem_id": "13200", "fitem_name": "Current EPS (TTM)" },
        { "default": false, "fitem_id": "CUSTOM", "fitem_name": "My Custom EPS" }
      ],
      "growth": [
        { "default": true, "fitem_id": "0", "fitem_name": "No Growth" },
        { "default": false, "fitem_id": "1472", "fitem_name": "EPS (YTD YoY Growth)" }
      ],
      "multiple": [ ]
    },
    "name": "..."
  }
}
```

**Status:** ✅ 200.

#### 5.10.3 Endpoint valuasi lainnya

| Method | Path | Keterangan | Status |
|---|---|---|---|
| GET | `/valuation/{id}` | Detail template | 📄 |
| POST | `/valuation` | Buat template | ✍️ |
| PUT | `/valuation/{id}` | Ubah template | ✍️ |
| DELETE | `/valuation/{id}` | Hapus template | ✍️ |
| POST | `/valuation/company/{symbol}` | Hitung valuasi saham | ✍️ |
| GET | `/valuation/company/{symbol}/metrics?metric=` | Metrik valuasi saham | 📄 |

Endpoint POST/PUT/DELETE tidak diuji. Untuk membaca, gunakan `GET /valuation/all/templates` lalu `GET /valuation/{id}`.

### 5.11 Watchlist

Service watchlist memakai header tambahan:

```http
X-Platform: web
X-AppVersion: 3.0.0
```

Untuk watchlist **portofolio**, service menambahkan:

```http
Authorization-Carina: Bearer <access_token>
```

#### 5.11.1 `GET /watchlist`

Daftar watchlist pengguna.

**Parameter**

| Nama | Tipe | Keterangan |
|---|---|---|
| `page` | int | default 1 |
| `limit` | int | default 500 |
| `company_id` | string | filter watchlist yang memuat company |
| `with_total` | bool | sertakan total |
| `category_types` | repeat | `CATEGORY_TYPE_ALL_WATCHLIST`, `CATEGORY_TYPE_PORTFOLIO`, `CATEGORY_TYPE_NORMAL` |

**Respons 200 — `data[]`:**

```json
{
  "watchlist_id": 1201415,
  "name": "All Watchlist",
  "description": "",
  "followed": 0,
  "total_items": 0,
  "is_default": true,
  "emoji": "",
  "contains_given_item": false,
  "is_favorite": true,
  "order_position": 0,
  "category_type": "CATEGORY_TYPE_ALL_WATCHLIST"
}
```

**Status:** ✅ 200.

#### 5.11.2 `GET /watchlist/favorite`

Sama seperti `/watchlist`, hanya watchlist favorit. Parameter `category_types` (repeat).

**Status:** ✅ 200.

#### 5.11.3 `GET /watchlist/{watchlist_id}`

Isi watchlist.

**Parameter**

| Nama | Keterangan |
|---|---|
| `page` | default 1 |
| `limit` | default 500 (web) / 100 (contoh) |
| `setfincol` | `1` untuk menyertakan kolom finansial |

**Respons 200 — field:**

```
watchlist_id, descriptions, header[], header_custom[], result[],
total, type, name, is_default, emoji, pagination, sort_by, sort_dir
```

`result[]`:

```json
{
  "change": 25,
  "id": 54,
  "last": 5125,
  "name": "Bank Central Asia Tbk.",
  "percent": 0.49,
  "previous": 5100,
  "symbol": "BBCA",
  "type": "Saham",
  "direction": "up",
  "notation": [],
  "uma": false,
  "corp_action": { },
  "icon_url": "...",
  "is_pinned": false,
  "prices": [],
  "status": "STATUS_ACTIVE",
  "day_trade_info": { },
  "trading_limit_info": { }
}
```

**Status:** ✅ 200.

#### 5.11.4 `GET /watchlist/{watchlist_id}/symbols`

Daftar simbol dalam watchlist (ringkas).

**Status:** 📄 ditemukan di service, belum diuji.

#### 5.11.5 `GET /watchlist/company/{company_id}/followers`

Daftar follower perusahaan.

**Query:** parameter pagination (`page`, `limit`, dll.).

**Status:** 📄.

#### 5.11.6 `GET /watchlist/company/follower-info`

Jumlah follower + status follow.

```http
GET /watchlist/company/follower-info?symbols=BBCA
```

```json
{
  "message": "...",
  "data": [
    { "symbol": "BBCA", "total_followers": 3501890, "is_followed": true }
  ]
}
```

**Status:** ✅ 200.

#### 5.11.7 `GET /watchlist/suggestion/company`

Saran perusahaan untuk ditambahkan.

**Query:** `watchlist_id`, `limit` (default 100).

**Status:** 📄.

#### 5.11.8 `GET /watchlist/metric`

Daftar metrik kolom watchlist (tree).

```json
[
  {
    "fitem_id": 18,
    "fitem_name": "Size",
    "show_chart_icon": 0,
    "child": [
      { "fitem_id": 2892, "fitem_name": "Market Cap", "show_chart_icon": 1, "child": [] }
    ]
  }
]
```

**Status:** ✅ 200.

#### 5.11.9 `GET /watchlist/search/company`

Cari perusahaan untuk ditambahkan ke watchlist.

**Parameter**

| Nama | Wajib |
|---|---|
| `watchlist_id` | ya |
| `keyword` | ya |
| `page` | ya |

Tanpa `watchlist_id` → 400 `"WatchlistID wajib diisi;"`. Tanpa `page` → 400 `"Page wajib diisi;"`.

**Respons:**

```json
{
  "message": "Successfully retrieved suggested company",
  "data": {
    "companies": [
      {
        "id": "54",
        "name": "BBCA",
        "country": "ID",
        "desc": "Bank Central Asia Tbk.",
        "exchange": "IDX",
        "is_following": false,
        "icon_url": "...",
        "is_verified": false,
        "status": "COMPANY_STATUS_ACTIVE",
        "symbol_2": "BBCA",
        "symbol_3": "BBCA",
        "total_followers": 0,
        "is_tradeable": true,
        "type": "Saham",
        "url": "symbol/BBCA",
        "is_exist": true
      }
    ]
  }
}
```

**Status:** ✅ 200.

#### 5.11.10 Endpoint tulis watchlist

| Method | Path | Body |
|---|---|---|
| POST | `/watchlist` | `{name, description}` |
| PUT | `/watchlist/{id}` | `{name, description}` |
| DELETE | `/watchlist/{id}` | — |
| POST | `/watchlist/{id}/company/item` | `{company_id}` |
| DELETE | `/watchlist/{id}/company/{company_id}/item` | — |
| PUT | `/watchlist/{id}/company/item` | Urutan/posisi |
| PUT | `/watchlist/{id}/company/pin` | `{companies: [...]}` |
| PUT | `/watchlist/favorite/{id}` | `{is_favorite}` |
| PUT | `/watchlist/favorites/rearrange` | Urutan favorit |
| POST | `/watchlist/{id}/column` | `{fitemid}` |
| DELETE | `/watchlist/{id}/column/{fitemid}` | — |
| PUT | `/watchlist/{id}/column/reorder` | `{fitemid}` |
| POST | `/watchlist/{id}/symbol-only` | — |

Semua ✍️ dan tidak dieksekusi. Untuk SMtracker, endpoint baca yang paling relevan: `/watchlist`, `/watchlist/{id}`, `/watchlist/company/follower-info`, `/watchlist/metric`.

### 5.12 Search

#### `GET /search`

Pencarian global (saham, orang, insider, chat, sektor, industri).

**Parameter**

| Nama | Nilai |
|---|---|
| `keyword` | Kata kunci, mis. `BBCA` |
| `type` | `all`, `company`, `users`, `emiten` (nilai yang dipakai web); `people`/`insider` diterima tetapi kosong untuk `BBCA` |
| `page` | dimulai dari **0** |
| `catalog_types` | Repeat: `CATALOG_TYPE_SECTOR`, `CATALOG_TYPE_INDUSTRY`, `CATALOG_TYPE_COMPANY_CATALOG` (dipakai untuk `type=all`) |

**Respons 200 — field:**

```
chat, company, insider, people, sector, industries, pagination, company_catalogs
```

`company[]`:

```json
{
  "id": "54",
  "name": "BBCA",
  "country": "ID",
  "desc": "Bank Central Asia Tbk.",
  "exchange": "IDX",
  "is_following": false,
  "img": "",
  "is_verified": false,
  "other": "saham",
  "status": "0",
  "symbol_2": "BBCA",
  "symbol_3": "BBCA",
  "total_followers": 0,
  "is_tradeable": true,
  "type": "Saham",
  "url": "symbol/BBCA",
  "icon_url": "..."
}
```

`pagination`:

```json
{
  "has_more_companies": false,
  "has_more_insiders": false,
  "has_more_users": false
}
```

**Catatan:**

- `type=company` dan `all` mengembalikan data; `people`/`insider` untuk `BBCA` kosong (bukan error).
- `type=emiten` dipakai untuk pencarian emiten dengan tambahan `country=ID`.
- `page=0` adalah halaman pertama.
- `GET /search/recent` mengembalikan riwayat pencarian; `POST /search/recent` menyimpannya (✍️).
- Untuk pencarian di dalam watchlist, gunakan `/watchlist/search/company`.

**Status:** ✅ 200.

### 5.13 Stream / social

Stream adalah domain paling kompleks: beberapa endpoint **baca** memakai POST, dan beberapa endpoint **tulis** memakai POST dengan path berbeda.

#### 5.13.1 Endpoint baca

| Method | Path | Parameter |
|---|---|---|
| GET | `/stream/v3` | `clean`, `beforelastpost`, `category`, `lastpost`, `keyword`, `limit`, `from`, `to`, `beforetimestamp`, `type`; ditambah `last_stream_id`, `last_reply`, `report_type`, `watchlist_ids` |
| POST | `/stream/v3/trending` | JSON `{date, last_stream_id, limit}` |
| GET | `/stream/v3/symbol/{symbol}` | `category`, `last_stream_id`, `keyword`, `from_date`, `to_date`, `limit`, `report_type` |
| GET | `/stream/v3/symbol/{symbol}/pinned` | — |
| POST | `/stream/v3/user/{username}` | JSON: `category`, `last_stream_id`, `keyword`, `from_date`, `to_date`, `limit` |
| POST | `/stream/v3/user/{username}/pinned` | — |
| POST | `/stream/v3/post/{stream_id}` | Body kosong |
| POST | `/stream/v3/conversation/{post_id}` | JSON `{stream_id, limit: 20}` |
| POST | `/stream/v3/conversation/comments` | JSON `{stream_id, is_previous: true, limit: 20}` |
| GET | `/stream/likers/{post_id}` | `username`, `page` |
| GET | `/stream/reactions` | — (terverifikasi 200) |
| GET | `/stream/non-login/symbol/{symbol}` | query opsional |
| GET | `/stream/non-login/post/{id}` | — |
| GET | `/stream/non-login/user/{username}` | — |
| GET | `/stream/announcement/{id}` | — |
| GET | `/stream/uploadtoken` | `bucket` (mis. `avatar`) |
| GET | `/stream/upload-tokens` | Parameter upload |

**Catatan penting tentang `GET /stream/v3`:**

- `type` (bukan `category`) menentukan mode: `latest` (default), `trending`, `ideas`, `reports`, dan varian lain.
- Untuk `type=trending` **tanpa keyword**, service justru memanggil `POST /stream/v3/trending`, bukan GET.
- `category` dikirim sebagai enum `STREAM_CATEGORY_*` (lihat 5.13.3).
- `watchlist_ids` hanya dikirim jika kategori `company watchlist`, dengan format repeat.

**Respons `/stream/v3`:**

```json
{
  "message": "20 stream post(s) retrieved",
  "data": {
    "stream": [ { "stream_id": 36929834, "content": "...", "user": { }, "...": "..." } ],
    "pagination": { },
    "invalid_watchlist_ids": []
  }
}
```

**Respons `/stream/non-login/symbol/{symbol}`:** `data` langsung berupa **array** post (bukan `data.stream`).

**Struktur post (`data.stream[]`):**

```
stream_id, title_url, title, content, content_original, created_at,
created_display, updated_at, user, status, total_replies, total_likes,
reposted_from, likers, type, images, polling, attachment,
parent_stream_id, reports, news_feed, target_price, analytics,
last_reply_date, topics, last_reply, mask_html, images_data,
image_frame_type, commenter_type, following_activity, sharetrade_info,
reply_to, reply_content, research, summary, reaction
```

`user`:

```json
{
  "user_id": 5286129,
  "is_author": false,
  "username": "Dhandot",
  "fullname": "Dhandot",
  "avatar": "https://avatar.stockbit.com/...",
  "is_verified": false,
  "user_privilege": "PRIVILEGE_..."
}
```

`content` mengandung placeholder mask `[%...%]`; `content_original` berisi teks asli dengan cashtag (`$BBCA`).

**Status:** ✅ 200 untuk endpoint yang diuji.

#### 5.13.2 Endpoint tulis (tidak dieksekusi)

| Method | Path | Fungsi |
|---|---|---|
| POST | `/stream/like/{id}` | Like |
| POST | `/stream/unlike/{id}` | Unlike |
| POST | `/stream/write` | Buat post |
| POST | `/stream/update/{postid}` | Edit post |
| POST | `/stream/v2/delete/{id}` | Hapus post; body `{reason, send_email}` |
| DELETE | `/stream/own/{id}` | Hapus post sendiri |
| DELETE | `/stream/own/comment/{id}` | Hapus komentar sendiri |
| POST | `/stream/delete/multiple` | Hapus banyak post |
| POST | `/stream/share/{postid}` | Share/repost |
| POST | `/stream/reply/{parent}` | Reply |
| POST | `/stream/report/{id}` | Report; form `type`, `message` |
| POST | `/stream/save/{id}` | Simpan |
| POST | `/stream/unsave/{id}` | Batal simpan |
| POST | `/stream/follow/{id}` | Follow post |
| POST | `/stream/unfollow/{id}` | Unfollow post |
| POST | `/stream/pin?postid=&symbol=` | Pin |
| POST | `/stream/unpin?postid=&symbol=` | Unpin |
| POST | `/stream/polling/vote/{id}` | Vote; body `{option}` |
| POST | `/stream/topic/untag/{id}` | Lepas topik |
| PUT | `/stream/commenter-type/{id}` | Body `{commenter_type}` |
| POST | `/stream/addvote/{tp_id}` | Form `tp_id`, `agree` |

Body pembuatan post (`/stream/write`) disusun dari:

```json
{
  "content": "...",
  "image": null,
  "images": [],
  "file": "",
  "target_price": null,
  "target_symbol": null,
  "target_duration": "0",
  "sharefacebook": 0,
  "sharetwitter": 0,
  "commenter_type": null,
  "polling_end": null,
  "polling_options": [],
  "polling_pin": false
}
```

Path di atas diambil dari service module dan **belum diverifikasi**. Jangan memanggil tanpa izin; beberapa di antaranya dapat menghasilkan konten publik.

**Status:** ✍️.

#### 5.13.3 Kategori stream

```
STREAM_CATEGORY_ALL
STREAM_CATEGORY_ALL_WATCHLIST
STREAM_CATEGORY_CHART
STREAM_CATEGORY_COMPANY_WATCHLIST
STREAM_CATEGORY_IDEAS
STREAM_CATEGORY_INSIDER
STREAM_CATEGORY_LIKED
STREAM_CATEGORY_MAIN_IDEAS
STREAM_CATEGORY_NEWS
STREAM_CATEGORY_PEOPLE_WATCHLIST
STREAM_CATEGORY_POLLING
STREAM_CATEGORY_PREDICTION
STREAM_CATEGORY_REPLY
STREAM_CATEGORY_REPORTS
STREAM_CATEGORY_SAVED
```

#### 5.13.4 Tipe report

```
REPORT_TYPE_ALL
REPORT_TYPE_LAPORAN_KEUANGAN
REPORT_TYPE_RUPS
REPORT_TYPE_KEPIMILIKAN_SAHAM
REPORT_TYPE_DIVIDEN
REPORT_TYPE_CORPORATE_ACTION
REPORT_TYPE_OTHER
```

### 5.14 User, notification, chat, discovery

#### 5.14.1 `GET /user/profile`

Profil pengguna yang sedang login.

**Respons 200 — field:**

```
id, created_at, statistics, profile, privilege, exchange, ir_symbols,
badges, is_alert_enabled, is_blocked, is_followed, email, last_modified_at,
last_login_at, has_password, is_newsletter_subscriber, is_activated,
is_phone_verified, is_shown_in_discovery, preferences, onboarding,
free_trial, sns, trading, support, pro, ban, onesignal_hash
```

`profile`:

```
username, fullname, about, website, avatar, country, language,
gender, location, address, birthday, phone, occupation
```

`statistics`:

```
follower_count, following_count, reputation_count, idea_count,
like_count, view_count
```

> **Privasi:** respons asli memuat email, nomor telepon, ID Google/Facebook, dan hash. Jangan pernah menuliskan respons ini ke log atau repository. Untuk dokumentasi, gunakan placeholder.

**Status:** ✅ 200.

#### 5.14.2 `GET /user/profile/{username}`

Profil publik pengguna lain. Field serupa, tanpa data sensitif pemilik akun.

**Status:** ✅ 200.

#### 5.14.3 `GET /user-setting/configurations`

**Query:** `user_setting_type=1` (nilai lain belum diuji).

**Status:** ✅ 200.

#### 5.14.4 `GET /user/v2/discovery/trending`

**Query:** `time_frame` (`TIME_FRAME_1W`, `TIME_FRAME_1M`, `TIME_FRAME_ALL`), `limit`.

**Respons:** `data.users[]`, `data.pagination`.

**Status:** ✅ 200.

#### 5.14.5 `GET /notification/count/unread`

**Query:** `types` (repeat). Daftar 36 tipe yang dikirim web:

```
NOTIF_TYPE_INBOX
NOTIF_TYPE_MENTIONS
NOTIF_TYPE_FOLLOWING
NOTIF_TYPE_RETWEET
NOTIF_TYPE_REPLY
NOTIF_TYPE_LIKE
NOTIF_TYPE_SAVE
NOTIF_TYPE_POSTALERT
NOTIF_TYPE_TRADING_MATCH_ORDER
NOTIF_TYPE_NEW_TRENDING
NOTIF_TYPE_STOCK_ALERT
NOTIF_TYPE_NEWUSERJOIN
NOTIF_TYPE_TARGETPRICE
NOTIF_TYPE_TIPPING_RECEIVER
NOTIF_TYPE_TIPPING_SENDER
NOTIF_TYPE_CLAIM
NOTIF_TYPE_VERIFIED_BADGE
NOTIF_TYPE_SECURITIES_DAY_TRADE
NOTIF_TYPE_SHARIA_STOCK_DELISTED
NOTIF_TYPE_SECURITIES_DEPOSIT
NOTIF_TYPE_SECURITIES_WITHDRAW
NOTIF_TYPE_SECURITIES_REFERRAL
NOTIF_TYPE_SECURITIES_MATCH
NOTIF_TYPE_SECURITIES_REJECT
NOTIF_TYPE_MESSAGE_REQUEST
NOTIF_TYPE_EIPO_CONFIRMATION
NOTIF_TYPE_GROUPCHAT
NOTIF_TYPE_NEW_REPORT
NOTIF_TYPE_NEWSFEED
NOTIF_TYPE_COMPANY_PUBLIC_EXPOSE
NOTIF_TYPE_COMPANY_SHAREHOLDING
NOTIF_TYPE_COMPANY_DIVIDEND
NOTIF_TYPE_COMPANY_CORP_ACTION
NOTIF_TYPE_COMPANY_OTHERS
NOTIF_TYPE_TRADING_COMMUNITY
NOTIF_TYPE_STREAM_REACTION
```

**Respons:**

```json
{ "message": "...", "data": { "count": 0, "has_new_messages": false } }
```

**Status:** ✅ 200.

#### 5.14.6 `GET /notification/v3/settings`

Pengaturan notifikasi per grup.

```json
{
  "group": "NOTIF_GROUP_SOCIAL",
  "label": "Social",
  "notifications": [
    {
      "type": "NOTIF_TYPE_MENTIONS",
      "settings": [
        { "key": "NOTIF_SETTING_KEY_DN", "value": false },
        { "key": "NOTIF_SETTING_KEY_PN", "value": true },
        { "key": "NOTIF_SETTING_KEY_EM", "value": false }
      ],
      "label": "Mentions",
      "info": ""
    }
  ]
}
```

Kunci setelan: `NOTIF_SETTING_KEY_DN` (desktop), `PN` (push), `EM` (email).

**Status:** ✅ 200.

#### 5.14.7 `GET /chat/v2/rooms/unread/count`

```json
{ "message": "...", "data": { "count": 0, "has_new_messages": false } }
```

**Status:** ✅ 200.

#### 5.14.8 Endpoint chat

**Baca:**

| Method | Path | Parameter |
|---|---|---|
| GET | `/chat/v2/rooms` | `offset`, `limit` |
| GET | `/chat/v2/rooms/{room_id}` | — |
| GET | `/chat/rooms/{room_id}/messages` | pagination |
| GET | `/chat/v2/rooms/type/invited` | pagination |
| GET | `/chat/v2/groups/{group_id}/messages` | pagination |
| GET | `/chat/v2/personal/{user_id}/messages` | pagination |
| GET | `/chat/v2/broadcast/{id}/messages` | pagination |
| GET | `/chat/v3/user/search` | `keyword` |
| GET | `/chat/v2/groups/members/suggestions` | `keyword`, dll. |
| GET | `/chat/v2/groups/members/suggestions/contacts` | `keyword`, `cursor`, `limit`, `for_group_id` |
| GET | `/chat/v2/groups/{group_id}/members` | `keyword`, `limit`, `offset`, `status`, `self_exclude` |
| GET | `/chat/rooms/userid/{user_id}` | — |
| GET | `/chat/v2/groups/room-id/{id}` | — |
| GET | `/chat/v2/eligibility/new-personal` | `target_username` |
| GET | `/chat/v2/groups/eligibility` | — |
| GET | `/chat/s3/policy` | — |
| GET | `/chat/v2/invitations/preview/{id}` | — |
| GET | `/chat/v2/invitations/public-preview/{id}` | — |
| GET | `/chat/v2/groups/members/max` | — |
| GET | `/chat/v2/receivers/shareable-search` | `keyword` |
| GET | `/chat/v2/rooms/unread/count` | — |

**Tulis (✍️, tidak dieksekusi):**

| Method | Path | Body |
|---|---|---|
| POST | `/chat/messages` | `{to_user_id, text, attachment_url, ...}` |
| POST | `/chat/v2/messages` | `{to_user_id, text, attachment_url, ...}` |
| POST | `/chat/v2/messages/bulk` | `{...}` |
| POST | `/chat/v2/messages/forward` | `{...}` |
| POST | `/chat/v2/messages/bulk-delete` | `{message_ids}` |
| POST | `/chat/rooms/{room_id}/read` | — |
| POST | `/chat/rooms/{room_id}/clear` | — |
| POST | `/chat/rooms/{room_id}/accept` | — |
| POST | `/chat/rooms/{room_id}/reject` | — |
| POST | `/chat/v2/rooms/{room_id}/mute` | `{is_muted}` |
| DELETE | `/chat/rooms/{room_id}` | — |
| POST | `/chat/v2/groups` | Objek grup |
| PUT | `/chat/v2/groups/{group_id}` | Objek grup |
| POST | `/chat/v2/groups/{group_id}/members/invite` | `{user_ids}` |
| POST | `/chat/v2/groups/{group_id}/members/leave` | `{...}` |
| POST | `/chat/v2/groups/{group_id}/change-admin-and-leave` | `{...}` |
| POST | `/chat/v2/groups/{group_id}/settings` | `{...}` |
| POST | `/chat/v2/groups/{group_id}/reset-link` | — |
| POST | `/chat/v2/groups/{group_id}/set-admin-status` | `{...}` |
| POST | `/chat/v2/groups/{group_id}/members/remove` | `{...}` |
| POST | `/chat/v2/groups/{group_id}/messages/bulk-delete` | `{message_ids}` |
| POST | `/chat/v2/invitations/room-id/{id}/respond` | `{action}` |
| POST | `/chat/v2/invitations/join/{id}` | — |
| POST | `/chat/v2/invitations/bulk-respond` | `{...}` |
| DELETE | `/chat/v2/invitations` | — |

**Status:** ✅ untuk endpoint baca yang diuji (`/chat/v2/rooms/unread/count`); sisanya 📄/✍️.

#### 5.14.9 Endpoint user lain

| Method | Path | Parameter/Body | Status |
|---|---|---|---|
| PUT | `/user/profile` | `{website, gender, about, avatar, fullname, email, exchange, ...}` | ✍️ |
| PUT | `/user/profile/country` | `{country}` | ✍️ |
| GET | `/user/trending` | `key=1W` (time frame) | 📄 |
| GET | `/user/blocked` | `page` | 📄 |
| POST | `/user/{username}/block` | — | ✍️ |
| POST | `/user/{username}/unblock` | — | ✍️ |
| POST | `/user/onboarding` | `{step}` | ✍️ |
| POST | `/user/upload/token` | `{filename}` | ✍️ |
| POST | `/user/v2/connect/{provider}` | Body penyedia | ✍️ |
| POST | `/user/disconnect/{provider}` | Body penyedia | ✍️ |
| GET | `/user/avatar/collection` | — | 📄 |
| GET | `/usergraph/socialinfo/{username}` | — | 📄 |
| GET | `/usergraph/socialinfo/user/me` | — | 📄 |
| GET | `/usergraph/non-login/socialinfo/{username}` | — | 📄 |

Status `📄` berarti path ditemukan di service module dan belum diuji live. Ini bukan endpoint inti SMtracker.

### 5.15 WebSocket

#### 5.15.1 `GET /auth/websocket/key`

Mengeluarkan kunci untuk koneksi WebSocket.

```json
{ "message": "...", "data": { "key": "<opaque-key>" } }
```

Kunci yang sama dipakai untuk social dan trading (`getWSKey` dan `getWSTradingKey` memanggil endpoint yang sama).

**Status:** ✅ 200.

#### 5.15.2 Social socket

```text
wss://wssocial.stockbit.com?wskey=<key>
```

- Pesan berupa **protobuf biner** (bukan JSON).
- Client melakukan encode/decode dengan skema protobuf aplikasi.
- Gunakan kunci dari `/auth/websocket/key`.
- Perhatikan reconnect/backoff; jangan membuka banyak koneksi paralel.

#### 5.15.3 Trading socket

```text
wss://wss-jkt.trading.stockbit.com/ws
wss://wss-jkt.trading.stockbit.com/ws?type=chart
```

- Subprotocol: `web`.
- `?type=chart` untuk stream chart.
- Pesan juga biner/protobuf.

#### 5.15.4 General socket

```text
wss://ws-gen.stockbit.com/v1
```

Ditemukan di bundle, belum dipetakan detail. Kemungkinan untuk market data umum.

### 5.16 Akademi, paywall, research, badge

#### 5.16.1 `GET /paywall/eligibility/check`

**Query**

| Nama | Nilai |
|---|---|
| `company` | Simbol, mis. `BBCA` |
| `features` | Repeat: `PAYWALL_FEATURE_*` |

**Respons:**

```json
{
  "message": "Success check eligibility",
  "data": {
    "last_subscription": null,
    "features": [
      { "feature": "PAYWALL_FEATURE_ORDERBOOK", "is_eligible": true },
      { "feature": "PAYWALL_FEATURE_RUNNING_TRADE", "is_eligible": true }
    ],
    "company": { "company": "BBCA", "is_eligible": true }
  }
}
```

**Status:** ✅ 200.

Daftar fitur paywall ada di bagian 6.

#### 5.16.2 `POST /paywall/counter/increment`

Dipicu otomatis oleh web saat membuka fitur paywall. Body tidak dicatat. **Status:** ✅ 200 (dipicu halaman, bukan pengujian langsung).

#### 5.16.3 Academy

| Method | Path | Parameter | Status |
|---|---|---|---|
| GET | `/academy/unboxing` | `limit`, `last_volume` | ✅ |
| POST | `/academy/v2/module` | Body modul | ✅ (dipicu halaman) |
| GET | `/academy/lessons/last-read` | `count` | ✅ |
| POST | `/academy/tokens/new` | — | ✅ (dipicu halaman) |

`/academy/unboxing` mengembalikan `data[]` berisi `id`, `title`, `description`, dan field lain.

#### 5.16.4 `GET /research/indicator/new`

**Query:** `symbol` (opsional).

```json
{ "message": "...", "data": { "has_new": false, "count": 0 } }
```

**Status:** ✅ 200.

#### 5.16.5 `GET /live-stream/event`

**Query:** `page`, `limit`.

**Item field:**

```
id, title, schedule, host, media, status, created_at, updated_at,
description, reminder_enabled, question_enabled, user_question, code,
hide_enabled, deeplink_url, is_priority, description_masked, masks,
type, audience_type
```

`schedule`: `{start, end, upcoming}` (ISO 8601 UTC).

**Status:** ✅ 200.

#### 5.16.6 `GET /verified-badge/user/{user_id}`

Status badge verifikasi pengguna.

**Status:** ✅ 200.

#### 5.16.7 `GET /remisier/referral/status`

**Status:** ⛔ 404 `{"message":"Unrecognized Command"}`. Endpoint direferensikan di bundle tetapi tidak tersedia untuk akun ini.

### 5.17 Katalog konglomerasi (KONGLO)

Dua endpoint REST yang menjadi sumber data menu **Group** / `/stock-group`. Berbeda dari jalur insider (5.8), jalur ini berbasis katalog: daftar grup → daftar emiten per grup.

#### 5.17.1 `GET /emitten/catalog`

Daftar katalog. Tanpa filter, yang dikembalikan adalah `CATALOG_TYPE_SUBINDUSTRY` (139 item).

**Parameter**

| Nama | Wajib | Nilai |
|---|---|---|
| `catalog_type` | tidak | `CATALOG_TYPE_KONGLO` untuk daftar grup konglomerasi |
| `page` | tidak | Default `1` |
| `limit` | tidak | Default `20`; `100` cukup untuk seluruh 33 grup |

**Contoh:**

```http
GET /emitten/catalog?catalog_type=CATALOG_TYPE_KONGLO&page=1&limit=100
```

**Respons 200:**

```json
{
  "message": "Successfully retrieved catalog list",
  "data": {
    "catalogs": [
      {
        "id": "9",
        "catalog_code": "SALIM",
        "catalog_name": "Salim",
        "catalog_type": "CATALOG_TYPE_KONGLO",
        "logo_url": "https://assets.stockbit.com/logos/catalog/Salim Group.png?version=...",
        "catalog_desc": "",
        "sort_order": 1,
        "symbols": [],
        "is_active": true
      }
    ],
    "paginate": {
      "next_page": 0,
      "prev_page": 0,
      "current_page": 1,
      "total_page": 1,
      "data_per_page": 100,
      "total_data_in_page": 33,
      "total_data": 33
    }
  }
}
```

**Catatan:**

- Total 33 grup pada build ini. Contoh: `SALIM`, `DANANTARA`, `DJARUM`, `SINARMAS`, `PRAJOGO-PANGESTU`, `THOHIR`, `SANDIAGA`, `SARATOGA`, `HAJI-ISAM`, `LOW-TUCK-KWONG`, `ASTRA`, `TP-RACHMAT`, `BAKRIE`, `AGUAN`, `EMTEK`, `LIPPO`, `CT-CORP`, `HARITA`, `TANCORP`, `CIPUTRA`, `PANIN`, `RAJAWALI`, `MNC`, `HASHIM`, `PUNJABI`, `TOMMY-SOEHARTO`, `PAM-GROUP`, `TOMY-WINATA`.
- `symbols[]` selalu kosong di respons daftar; daftar emiten harus diambil dari endpoint 5.17.2.
- Filter `keyword`, `search`, `q`, `catalog_name`, dan `catalog_code` **diabaikan** server — penyaringan dilakukan client-side. Jangan mengandalkannya untuk pencarian.
- `catalog_type` adalah satu-satunya filter yang terbukti bekerja.

#### 5.17.2 `GET /emitten/catalog/{catalog_code}/company`

Daftar emiten dalam satu grup konglomerasi.

**Parameter**

| Nama | Wajib | Keterangan |
|---|---|---|
| `catalog_code` | path | Kode katalog (`PRAJOGO-PANGESTU`, `SALIM`, `ASTRA`), **bukan** `id` numerik |
| `page` | tidak | Default mengembalikan semua |
| `limit` | tidak | Wajib dikirim **bersama** `page` saat paginasi |

**Contoh:**

```http
GET /emitten/catalog/PRAJOGO-PANGESTU/company
GET /emitten/catalog/PRAJOGO-PANGESTU/company?page=2&limit=3
```

**Respons 200 — field:**

```
catalog, companies[], pagination
```

`catalog` berbentuk sama dengan item pada 5.17.1. `companies[]`:

```json
{
  "company_id": "1000003994",
  "symbol": "CUAN",
  "symbol_2": "CUAN",
  "symbol_3": "CUAN",
  "name": "Petrindo Jaya Kreasi Tbk.",
  "country": "ID",
  "type_company": "Saham",
  "icon_url": "https://assets.stockbit.com/logos/companies/CUAN.png",
  "last": "382",
  "formatted_price": "382",
  "change": "-28.00",
  "percent": "-6.83",
  "volume": 294307300,
  "avgvolume": "442753182.00",
  "valuema20": "256028203830.00",
  "marketcap": "42944019800000.00",
  "value": -2019049792,
  "popularity": 0,
  "followers": 744935,
  "tradeable": 1,
  "isexist": 0,
  "is_exists": false,
  "uma": false,
  "day_trade_info": { "is_show_multiplier": true, "multiplier": "2" },
  "trading_limit_info": { "is_trading_limit": true, "haircut_percentage": "70%" }
}
```

`pagination`:

```json
{ "next_page": 2, "prev_page": 0, "current_page": 1, "total_page": 3,
  "data_per_page": 3, "total_data_in_page": 3, "total_data": 9 }
```

**Contoh hasil:**

| Katalog | `catalog_code` | Jumlah emiten | Emiten |
|---|---|---|---|
| Prajogo Pangestu | `PRAJOGO-PANGESTU` | 9 | CUAN, CDIA, BRPT, PTRO, TPIA, BREN, RATU, SSIA, SINI |
| Salim | `SALIM` | 23 | BBCA, BUMI, INDF, ICBP, BRMS, LSIP, PANI, EMTK, AMMN, CBDK, FAST, SIMP, dst. |
| Astra | `ASTRA` | 10 | ASII, AALI, GOTO, UNTR, AUTO, HEAL, ASGR, ARKO, ACST, MMLP |
| Danantara | `DANANTARA` | 39 | BBRI, BMRI, TLKM, ANTM, PGAS, PTBA, BBNI, ADHI, SMGR, JSMR, dst. |

**Keanehan yang wajib diperhatikan:**

- `page` **tanpa** `limit` mengembalikan `companies: []` dan `pagination` semua nol. Selalu kirim keduanya saat paginasi.
- Tanpa `page`/`limit`, seluruh emiten grup dikembalikan (9 untuk Prajogo).
- Path memakai `id` numerik (`/emitten/catalog/57/company`) → 404 `{"message":"Katalog tidak ditemukan","error_type":"NOT_FOUND"}`. Gunakan `catalog_code`.
- `sort`/`order` tidak terbukti berpengaruh (respons identik).

#### 5.17.3 Hubungan dengan `/stock-group`

Halaman `/stock-group` **tidak** memanggil REST katalog saat render. Ia memakai WebSocket:

```
wss://wss-jkt.trading.stockbit.com/ws
```

dengan pesan `marketMoverBatch`:

```json
{
  "moverType": "CATALOG_KONGLO_MCAP_PCHANGE",
  "filterStocks": ["UNSPECIFIED"],
  "catalogType": "KONGLO",
  "catalogId": "0"
}
```

- Tanpa grup terpilih: `moverType=CATALOG_KONGLO_MCAP_PCHANGE`, `catalogId=0` (semua grup).
- Grup terpilih: `moverType=TOP_VALUE`, `catalogId=<id katalog>`.
- Respons WS memuat `catalog_detail` (`code`, `name`, `icon_url`, `up_count`, `down_count`, `unchanged_count`, `stock_count`, `catalog_id`) dan daftar saham.
- REST 5.17.1/5.17.2 adalah padanan yang dapat dipakai untuk mengambil data yang sama tanpa protobuf/WS. Bentuk responsnya tidak identik dengan payload WS.

**Status:** ✅ 200 untuk daftar 33 grup dan tiga katalog (`PRAJOGO-PANGESTU`, `SALIM`, `ASTRA`).

---

## 6. Enumerasi dan konstanta

Nilai di bawah diambil dari bundle dan/atau respons live. String harus dikirim **persis** (huruf besar, underscore). Beberapa endpoint tidak memvalidasi enum dan mengembalikan data kosong jika nilainya salah.

### 6.1 Periode broker, running trade, trade book

**`BROKER_SUMMARY_PERIOD_*`** (market detector / broker summary)

```
BROKER_SUMMARY_PERIOD_LATEST
BROKER_SUMMARY_PERIOD_YESTERDAY
BROKER_SUMMARY_PERIOD_LAST_7_DAYS
BROKER_SUMMARY_PERIOD_THIS_MONTH
BROKER_SUMMARY_PERIOD_PREVIOUS_MONTH
BROKER_SUMMARY_PERIOD_LAST_1_MONTH
BROKER_SUMMARY_PERIOD_LAST_3_MONTHS
BROKER_SUMMARY_PERIOD_LAST_6_MONTHS
BROKER_SUMMARY_PERIOD_YEAR_TO_DATE
BROKER_SUMMARY_PERIOD_LAST_1_YEAR
BROKER_SUMMARY_PERIOD_UNSPECIFIED
```

**`RT_PERIOD_*`** (broker activity, activity chart, running trade)

```
RT_PERIOD_LAST_1_DAY
RT_PERIOD_YESTERDAY
RT_PERIOD_LAST_3_DAYS
RT_PERIOD_LAST_7_DAYS
RT_PERIOD_THIS_MONTH
RT_PERIOD_PREVIOUS_MONTH
RT_PERIOD_LAST_1_MONTH
RT_PERIOD_LAST_3_MONTHS
RT_PERIOD_LAST_6_MONTH
RT_PERIOD_YEAR_TO_DATE
RT_PERIOD_LAST_1_YEAR
RT_PERIOD_UNSPECIFIED
```

> Perhatikan `RT_PERIOD_LAST_6_MONTH` (tunggal), berbeda dengan `BROKER_SUMMARY_PERIOD_LAST_6_MONTHS` (jamak).

**`TB_PERIOD_*`** (broker top)

```
TB_PERIOD_LAST_1_DAY
TB_PERIOD_PREVIOUS_DAY
TB_PERIOD_LAST_7_DAYS
TB_PERIOD_THIS_MONTH
TB_PERIOD_PREVIOUS_MONTH
TB_PERIOD_LAST_1_MONTH
TB_PERIOD_LAST_3_MONTHS
TB_PERIOD_LAST_6_MONTHS
TB_PERIOD_YEAR_TO_DATE
TB_PERIOD_LAST_1_YEAR
```

### 6.2 Board dan market type

**`MARKET_BOARD_*`** (dipakai `marketdetectors`, `prices/{sym}/market`, `broker/activity`)

```
MARKET_BOARD_ALL
MARKET_BOARD_REGULER
MARKET_BOARD_TUNAI
MARKET_BOARD_NEGO
MARKET_BOARD_UNSPECIFIED
```

**`BOARD_TYPE_*`** (activity chart, filter orderbook)

```
BOARD_TYPE_ALL
BOARD_TYPE_REGULAR
BOARD_TYPE_RG
BOARD_TYPE_CASH
BOARD_TYPE_TN
BOARD_TYPE_NEGOTIATION
BOARD_TYPE_NG
BOARD_TYPE_UNSPECIFIED
```

Alias yang ditemukan:

| Kode pendek | Board type |
|---|---|
| `RG` | `BOARD_TYPE_REGULAR` / `BOARD_TYPE_RG` |
| `TN` | `BOARD_TYPE_CASH` / `BOARD_TYPE_TN` |
| `NG` | `BOARD_TYPE_NEGOTIATION` / `BOARD_TYPE_NG` |

**`MARKET_TYPE_*`**

```
MARKET_TYPE_ALL
MARKET_TYPE_REGULER
MARKET_TYPE_TUNAI
MARKET_TYPE_NEGO
MARKET_TYPE_UNSPECIFIED
```

> Jebakan: `foreign-domestic` memakai **`MARKET_TYPE_REGULAR`** (dengan `AR`), sedangkan endpoint lain memakai **`MARKET_TYPE_REGULER`** (dengan `ER`). Keduanya berbeda dan tidak selalu diterima di endpoint yang sama.

### 6.3 Investor dan transaksi

**`INVESTOR_TYPE_*`**

```
INVESTOR_TYPE_ALL
INVESTOR_TYPE_DOMESTIC
INVESTOR_TYPE_FOREIGN
```

**`TRANSACTION_TYPE_*` yang relevan untuk order-trade**

```
TRANSACTION_TYPE_NET
TRANSACTION_TYPE_BUY
TRANSACTION_TYPE_SELL
TRANSACTION_TYPE_GROSS
```

Enum `TRANSACTION_TYPE_*` yang panjang (`BEA_METERAI`, `CASH_DIVIDEND`, `DEPOSIT`, `WITHDRAW`, `FR_MATURITY_REDEMPTION`, dll.) berasal dari modul sekuritas/Carina dan **bukan** parameter endpoint order-trade di dokumen ini.

### 6.4 Order dan trade book

**`TB_SORT_BY_*`** (broker top)

```
TB_SORT_BY_TOTAL_VALUE
TB_SORT_BY_CODE
```

**`ORDER_BY_*`**

```
ORDER_BY_ASC
ORDER_BY_DESC
```

**`GROUP_BY_*`** (trade book)

```
GROUP_BY_PRICE
GROUP_BY_TIME
GROUP_BY_CHART
GROUP_BY_UNSPECIFIED
```

**`RUNNING_TRADE_INVESTOR_TYPE_*`**

```
RUNNING_TRADE_INVESTOR_TYPE_ALL
RUNNING_TRADE_INVESTOR_TYPE_DOMESTIC_BUY
RUNNING_TRADE_INVESTOR_TYPE_DOMESTIC_SELL
RUNNING_TRADE_INVESTOR_TYPE_FOREIGN_BUY
RUNNING_TRADE_INVESTOR_TYPE_FOREIGN_SELL
RUNNING_TRADE_INVESTOR_TYPE_UNSPECIFIED
```

**`RUNNING_TRADE_ACTION_TYPE_*`**

```
RUNNING_TRADE_ACTION_TYPE_BUY
RUNNING_TRADE_ACTION_TYPE_SELL
```

**`RUNNING_TRADE_ORDER_BY_*`**

Nilai yang berhasil dipakai: `RUNNING_TRADE_ORDER_BY_TIME`. Enum lengkap tidak ditemukan sebagai literal di bundle; nilai lain belum diverifikasi.

**`SORT_BY_*`** (orderbook / daftar)

```
SORT_BY_PRICE
SORT_BY_QUEUE
SORT_BY_LOT
SORT_BY_TIME
SORT_BY_OPEN
SORT_BY_CODE
SORT_BY_TOTAL_VALUE
SORT_BY_EXCHANGE_ORDER_NUMBER
SORT_BY_UNSPECIFIED
```

### 6.5 Insider, corpaction, broker

**`ACTION_TYPE_*`**

```
ACTION_TYPE_ALL
ACTION_TYPE_BUY
ACTION_TYPE_SELL
ACTION_TYPE_TRANSFER
ACTION_TYPE_CROSS
ACTION_TYPE_CORPACTION
ACTION_TYPE_BONUS_STOCK
ACTION_TYPE_DIVIDEND_CASH
ACTION_TYPE_DIVIDEND_STOCK
ACTION_TYPE_UNSPECIFIED
```

**`SOURCE_TYPE_*`**

```
SOURCE_TYPE_IDX
SOURCE_TYPE_KSEI
SOURCE_TYPE_UNSPECIFIED
```

**`NATIONALITY_TYPE_*`**

```
NATIONALITY_TYPE_LOCAL
NATIONALITY_TYPE_FOREIGN
```

**`SHAREHOLDERS_COMPOSITION_VIEW_*`** (composition)

```
SHAREHOLDERS_COMPOSITION_VIEW_ALL
SHAREHOLDERS_COMPOSITION_VIEW_SCRIPPLESS
```

**`SHAREHOLDING_NETWORK_NODE_TYPE_*`** (network)

```
SHAREHOLDING_NETWORK_NODE_TYPE_UNSPECIFIED
SHAREHOLDING_NETWORK_NODE_TYPE_COMPANY
SHAREHOLDING_NETWORK_NODE_TYPE_INVESTOR
```

**`shareholder_type`** (chart, bukan enum berprefix)

```
all
local
foreign
```

**`BROKER_GROUP_*`**

```
BROKER_GROUP_LOCAL
BROKER_GROUP_FOREIGN
BROKER_GROUP_GOVERNMENT
```

Nilai `BROKER_GROUP_UNSPECIFIED` juga muncul di respons untuk broker tanpa grup.

**`BROKER_TYPE_*`**

```
BROKER_TYPE_LOCAL
BROKER_TYPE_FOREIGN
BROKER_TYPE_GOVERNMENT
BROKER_TYPE_UNSPECIFIED
```

**`PRIVILEGE_*`**

```
PRIVILEGE_MEMBER
PRIVILEGE_MODERATOR
PRIVILEGE_ADMIN
PRIVILEGE_CONFIGURATOR
PRIVILEGE_SUPER_ADMIN
```

**`VERIFIED_STATUS_*`**

```
VERIFIED_STATUS_UNVERIFIED
VERIFIED_STATUS_IDENTITY
VERIFIED_STATUS_COMMUNITY
```

### 6.6 Screener, watchlist, katalog

**`TEMPLATE_TYPE_*`**

```
TEMPLATE_TYPE_CUSTOM
TEMPLATE_TYPE_GURU
```

**`CATEGORY_TYPE_*`** (watchlist)

```
CATEGORY_TYPE_ALL_WATCHLIST
CATEGORY_TYPE_NORMAL
CATEGORY_TYPE_PORTFOLIO
```

**`CATALOG_TYPE_*`** (search)

```
CATALOG_TYPE_SECTOR
CATALOG_TYPE_INDUSTRY
CATALOG_TYPE_SUBINDUSTRY
CATALOG_TYPE_COMPANY_CATALOG
CATALOG_TYPE_ETF
CATALOG_TYPE_KONGLO
CATALOG_TYPE_UNSPECIFIED
```

### 6.7 Stream dan report

**`STREAM_CATEGORY_*`**

```
STREAM_CATEGORY_ALL
STREAM_CATEGORY_ALL_WATCHLIST
STREAM_CATEGORY_CHART
STREAM_CATEGORY_COMPANY_WATCHLIST
STREAM_CATEGORY_IDEAS
STREAM_CATEGORY_INSIDER
STREAM_CATEGORY_LIKED
STREAM_CATEGORY_MAIN_IDEAS
STREAM_CATEGORY_NEWS
STREAM_CATEGORY_PEOPLE_WATCHLIST
STREAM_CATEGORY_POLLING
STREAM_CATEGORY_PREDICTION
STREAM_CATEGORY_REPLY
STREAM_CATEGORY_REPORTS
STREAM_CATEGORY_SAVED
```

**`REPORT_TYPE_*`**

```
REPORT_TYPE_ALL
REPORT_TYPE_LAPORAN_KEUANGAN
REPORT_TYPE_RUPS
REPORT_TYPE_KEPIMILIKAN_SAHAM
REPORT_TYPE_DIVIDEN
REPORT_TYPE_CORPORATE_ACTION
REPORT_TYPE_OTHER
```

### 6.8 Paywall

**`PAYWALL_FEATURE_*`**

```
PAYWALL_FEATURE_ANALYSIS
PAYWALL_FEATURE_BANDAR_DETECTOR
PAYWALL_FEATURE_CALENDAR
PAYWALL_FEATURE_CHARTBIT
PAYWALL_FEATURE_COMPANY_PROFILE
PAYWALL_FEATURE_COMPARISON
PAYWALL_FEATURE_CORP_ACTION
PAYWALL_FEATURE_EARNINGS
PAYWALL_FEATURE_FINANCIALS
PAYWALL_FEATURE_FUNDACHART
PAYWALL_FEATURE_INSIDER
PAYWALL_FEATURE_KEYSTATS
PAYWALL_FEATURE_ORDERBOOK
PAYWALL_FEATURE_PRICE_ALERT
PAYWALL_FEATURE_RUNNING_TRADE
PAYWALL_FEATURE_SCREENER
PAYWALL_FEATURE_SEASONALITY
PAYWALL_FEATURE_VALUATION
PAYWALL_FEATURE_UNSPECIFIED
```

> Tidak ada `PAYWALL_FEATURE_ANALYST`; yang benar `PAYWALL_FEATURE_ANALYSIS`.

### 6.9 Sesi pasar

**`SESSION_TYPE_*`**

```
SESSION_TYPE_SESSION_1
SESSION_TYPE_SESSION_2
SESSION_TYPE_SESSION_3
SESSION_TYPE_SESSION_4
SESSION_TYPE_SESSION_5
SESSION_TYPE_MARKET_BREAK
SESSION_TYPE_POST_CLOSING
SESSION_TYPE_MARKET_CLOSE
SESSION_TYPE_UNSPECIFIED
```

**`SESSION_PHASE_*`**

```
SESSION_PHASE_ORDER_COLLECTION
SESSION_PHASE_ORDER_MATCHING
SESSION_PHASE_RANDOM_CLOSING
SESSION_PHASE_UNSPECIFIED
```

**`STATE_NAME_*`**

Nilai yang diamati di respons: `STATE_NAME_BREAK`. Enum lengkap tidak ditemukan sebagai literal di bundle; kemungkinan nama state lain (`STATE_NAME_OPEN`, `STATE_NAME_CLOSE`) ada tetapi belum terverifikasi.

**`PERIOD_*`** (umum, untuk chart/foreign-domestic)

```
PERIOD_1D
PERIOD_1W
PERIOD_1M
PERIOD_3M
PERIOD_6M
PERIOD_1Y
PERIOD_2Y
PERIOD_3Y
PERIOD_ALL
PERIOD_YTD
PERIOD_MTD
PERIOD_CUSTOM
PERIOD_LATEST
PERIOD_YESTERDAY
PERIOD_PREVIOUS_DAY
PERIOD_LAST_1_DAY
PERIOD_LAST_3_DAYS
PERIOD_LAST_7_DAYS
PERIOD_LAST_1_MONTH
PERIOD_LAST_3_MONTHS
PERIOD_LAST_6_MONTH
PERIOD_LAST_6_MONTHS
PERIOD_LAST_1_YEAR
PERIOD_THIS_MONTH
PERIOD_PREVIOUS_MONTH
PERIOD_YEAR_TO_DATE
PERIOD_UNSPECIFIED
```

Untuk foreign-domestic, nilai yang terbukti: `PERIOD_RANGE_1D`.

### 6.10 Company info

**`COMPANY_INFO_TYPE_*`**

```
COMPANY_INFO_TYPE_UNSPECIFIED
COMPANY_INFO_TYPE_EMITTEN
COMPANY_INFO_TYPE_CRYPTO
COMPANY_INFO_TYPE_ETF_GOLD
COMPANY_INFO_TYPE_FR
COMPANY_INFO_TYPE_TOKENIZED_STOCK
```

**`COMPANY_INFO_API_VERSION_*`**

```
COMPANY_INFO_API_VERSION_UNSPECIFIED
COMPANY_INFO_API_VERSION_V1
COMPANY_INFO_API_VERSION_V2
```

### 6.11 Notifikasi

**36 tipe notifikasi** yang dikirim web ke `/notification/count/unread`:

```
NOTIF_TYPE_INBOX
NOTIF_TYPE_MENTIONS
NOTIF_TYPE_FOLLOWING
NOTIF_TYPE_RETWEET
NOTIF_TYPE_REPLY
NOTIF_TYPE_LIKE
NOTIF_TYPE_SAVE
NOTIF_TYPE_POSTALERT
NOTIF_TYPE_TRADING_MATCH_ORDER
NOTIF_TYPE_NEW_TRENDING
NOTIF_TYPE_STOCK_ALERT
NOTIF_TYPE_NEWUSERJOIN
NOTIF_TYPE_TARGETPRICE
NOTIF_TYPE_TIPPING_RECEIVER
NOTIF_TYPE_TIPPING_SENDER
NOTIF_TYPE_CLAIM
NOTIF_TYPE_VERIFIED_BADGE
NOTIF_TYPE_SECURITIES_DAY_TRADE
NOTIF_TYPE_SHARIA_STOCK_DELISTED
NOTIF_TYPE_SECURITIES_DEPOSIT
NOTIF_TYPE_SECURITIES_WITHDRAW
NOTIF_TYPE_SECURITIES_REFERRAL
NOTIF_TYPE_SECURITIES_MATCH
NOTIF_TYPE_SECURITIES_REJECT
NOTIF_TYPE_MESSAGE_REQUEST
NOTIF_TYPE_EIPO_CONFIRMATION
NOTIF_TYPE_GROUPCHAT
NOTIF_TYPE_NEW_REPORT
NOTIF_TYPE_NEWSFEED
NOTIF_TYPE_COMPANY_PUBLIC_EXPOSE
NOTIF_TYPE_COMPANY_SHAREHOLDING
NOTIF_TYPE_COMPANY_DIVIDEND
NOTIF_TYPE_COMPANY_CORP_ACTION
NOTIF_TYPE_COMPANY_OTHERS
NOTIF_TYPE_TRADING_COMMUNITY
NOTIF_TYPE_STREAM_REACTION
```

**Grup notifikasi** yang diamati: `NOTIF_GROUP_CHAT`, `NOTIF_GROUP_SOCIAL`.

**Kunci setelan**: `NOTIF_SETTING_KEY_DN` (desktop), `NOTIF_SETTING_KEY_PN` (push), `NOTIF_SETTING_KEY_EM` (email). Nilai `true`/`false`.

### 6.12 Status, membership, tipe entitas

**Status yang muncul di respons:**

```
STATUS_ACTIVE
STATUS_DELISTED
STATUS_SUSPENDED
STATUS_DISABLED
STATUS_EXPIRED
STATUS_COMPLETED
STATUS_IN_PROGRESS
STATUS_REJECTED
STATUS_WAITING_APPROVAL
STATUS_WAITING_LOCK
STATUS_WITHDRAWN
STATUS_MATCHED
STATUS_MATCHING
STATUS_UNSPECIFIED
```

**Status perusahaan** yang diamati: `COMPANY_STATUS_ACTIVE`.

**Membership broker** yang diamati: `MEMBERSHIP_TYPE_EXCHANGE_MEMBER`.

**Tipe entitas di hasil pencarian:** `Saham`, `Indeks`, `ETF`, `Waran`, `Right Issue`, dll. (string bebas, bukan enum ketat).

### 6.13 Timeframe chart

**`/charts/{symbol}/daily` — nilai `timeframe` yang diuji:**

```
today
1d
1w
1m
3m
6m
1y
3y
5y
10y
ytd
max
```

**`/company-price-feed/price-performance/{symbol}` — timeframe yang dikembalikan:**

```
1D
1W
1M
3M
6M
YTD
1Y
3Y
5Y
10Y
```

**`/user/v2/discovery/trending` — `time_frame`:**

```
TIME_FRAME_1W
TIME_FRAME_1M
TIME_FRAME_ALL
```

---

## 7. Katalog error

### 7.1 Format umum

```json
{
  "message": "Pesan untuk manusia",
  "error_type": "INVALID_PARAMETER",
  "errors": [
    { "key": "NamaField", "error": "Pesan error" }
  ]
}
```

`errors` tidak selalu ada. Beberapa endpoint mengembalikan `message` saja.

### 7.2 Error yang terverifikasi

#### 400 — parameter wajib hilang

**Tanpa `watchlist_id`:**

```http
GET /watchlist/search/company?keyword=BBCA&page=1
```

```json
{
  "message": "WatchlistID wajib diisi;",
  "error_type": "INVALID_PARAMETER",
  "errors": [{ "key": "WatchlistID", "error": "WatchlistID wajib diisi" }]
}
```

**Tanpa `page`:**

```json
{
  "message": "Page wajib diisi;",
  "error_type": "INVALID_PARAMETER",
  "errors": [{ "key": "Page", "error": "Page wajib diisi" }]
}
```

**Trade book tanpa `group_by`:**

```json
{
  "message": "Group by is required",
  "error_type": "INVALID_PARAMETER"
}
```

**Running trade group tanpa `order_by`:**

```json
{
  "message": "Please check your request",
  "error_type": "INVALID_PARAMETER",
  "errors": [{ "key": "OrderBy", "error": "OrderBy wajib diisi" }]
}
```

**Classification company dengan `IDs` (huruf besar):**

```json
{
  "message": "Silahkan Periksa permintaan",
  "error_type": "INVALID_PARAMETER",
  "errors": [{ "key": "IDs", "error": "IDs wajib diisi" }]
}
```

> Pesannya membingungkan: parameter yang dikirim `IDs`, tetapi server mencari `ids` (huruf kecil) dan menganggapnya kosong.

**Financial dengan `data_type=2`:**

```json
{
  "message": "Your request is invalid",
  "error_type": "INVALID_PARAMETER",
  "errors": [{ "key": "Your request is invalid", "error": "Your request is invalid" }]
}
```

**Shareholding network tanpa `root_id`:**

```json
{
  "message": "Invalid root id",
  "error_type": "INVALID_PARAMETER"
}
```

#### 401 — tidak terautentikasi

```http
GET /emitten/BBCA/info
```

```json
{
  "error_type": "UNAUTHORIZED",
  "message": "Unauthorized"
}
```

Penyebab: token tidak dikirim, kedaluwarsa, atau sudah dirotasi.

#### 403 — paywall/partner

`/partnership/*` mengembalikan **HTML Cloudflare**, bukan JSON:

```html
<!DOCTYPE html>
<html class="no-js" lang="en-US">
<head>
  <title>Attention Required! | Cloudflare</title>
  ...
```

Jangan mencoba mem-parse sebagai JSON. Perlakukan sebagai “tidak berhak”.

#### 404 — path/ID tidak ditemukan

**Path tidak dikenal:**

```json
{ "message": "Unrecognized Command" }
```

Contoh: `/chartbit/search`.

**Investor ID tidak valid:**

```json
{ "message": "Investor not found", "error_type": "NOT_FOUND" }
```

**Template orderbook tidak ada:**

```json
{ "message": "Id tidak ditemukan", "error_type": "NOT_FOUND" }
```

**Remisier referral tidak tersedia:**

```json
{ "message": "Data not found", "error_type": "NOT_FOUND" }
```

#### 500 — kesalahan server

**Endpoint emitten v2:**

```json
{
  "message": "Failed to get emitten info",
  "error_type": "SYSTEM_ERROR"
}
```

Terjadi pada `/emitten/v2/IDX/BBCA/info` dan `/fin-items`, baik login maupun non-login.

### 7.3 429 — rate limit

Belum teramati pada pengujian (laju dijaga ≤ 8 req/s). Jika terjadi, biasanya disertai `Retry-After`. Strategi:

1. Baca `Retry-After`; jika ada, tunggu selama itu.
2. Jika tidak ada, backoff 1s → 2s → 4s → 8s (maksimal 3 percobaan).
3. Turunkan konkurensi menjadi 1 dan bagi batch.

### 7.4 Error di dalam HTTP 200

Client axios Stockbit melempar error jika body memiliki `error_type`, **meskipun status HTTP 200**. Klien buatan sendiri harus meniru perilaku ini:

```python
if response.status_code == 200 and "error_type" in response.json():
    raise ApiError(response.json())
```

---

## 8. Rate limit, header, dan caching

### 8.1 Kuota

| Header | Nilai diamati | Arti |
|---|---|---|
| `x-rate-limit-limit` | `10` | Maksimum request per jendela |
| `x-rate-limit-remaining` | `8` setelah 2 request | Sisa kuota |
| `x-rate-limit-reset` | `0` | Tidak informatif (sliding window) |

Rekomendasi operasional:

- **≤ 8 req/s** untuk endpoint baca.
- **≤ 2 request paralel** untuk endpoint berat (`financial`, `screener`, `stream`).
- Batch simbol dalam satu request bila memungkinkan (mis. `/prices/close`).
- Jangan polling endpoint yang sama lebih dari **1×/detik**.
- Untuk 100+ simbol, bagi menjadi batch 25–50 dan beri jeda 150–250 ms antar batch.

### 8.2 Header respons penting

```http
sb-request-id: 1-6adae678-1dd897b66dd623253ade7d2d
x-rate-limit-limit: 10
x-rate-limit-remaining: 9
x-rate-limit-reset: 0
cache-control: no-store
access-control-allow-origin: https://stockbit.com
access-control-allow-credentials: true
access-control-allow-methods: GET, OPTIONS
vary: Origin
strict-transport-security: max-age=63072000; includeSubDomains
x-content-type-options: nosniff
server: cloudflare
via: 1.1 ...cloudfront.net (CloudFront)
x-amz-cf-pop: SIN3-P3
x-cache: Miss from cloudfront
```

`sb-request-id` dapat diberikan ke support Stockbit saat melaporkan error.

### 8.3 Caching

| Host | `Cache-Control` | Saran |
|---|---|---|
| `exodus.stockbit.com` | `no-store` | Jangan cache di HTTP; cache di aplikasi |
| `exodus.api.stockbit.com` | `public, max-age=1` | Boleh cache 1 detik |

Cache aplikasi yang disarankan:

| Data | TTL |
|---|---|
| Info emiten | 5–30 detik |
| Orderbook | 1–2 detik |
| Running trade | 1 detik |
| Chart harian | 5–60 detik (tergantung timeframe) |
| Financial/keystats | 1–24 jam |
| Screener template | 5–15 menit |
| Profil perusahaan | 24 jam |

### 8.4 Timeout dan retry

- Connect timeout: **5 detik**.
- Read timeout: **20 detik** untuk endpoint biasa; **60 detik** untuk `financial` dan `screener/templates/{id}`.
- Retry hanya untuk **GET** dan hanya pada:
  - koneksi putus/timeout,
  - HTTP 502/503/504,
  - HTTP 429 (setelah backoff).
- **Jangan** retry otomatis POST/PUT/DELETE.

### 8.5 Refresh token single-flight

Karena refresh merotasi token:

1. Gunakan satu lock (file lock/Redis lock/mutex) untuk seluruh proses yang memakai akun yang sama.
2. Sebelum refresh, baca token terbaru dari penyimpanan; jika `expired_at` masih jauh, pakai yang ada.
3. Setelah refresh, tulis pasangan baru secara atomik (`os.replace`).
4. Jika refresh gagal 401, jangan mencoba lagi dengan token yang sama; token sudah tidak valid.

---

## 9. Endpoint bermasalah dan batasan

### 9.1 Ringkasan endpoint yang gagal

| Endpoint | Gejala | Penanganan |
|---|---|---|
| `GET /emitten/v2/{exchange}/{symbol}/info` | 500 `Failed to get emitten info` | Pakai `/emitten/{symbol}/info` |
| `GET /emitten/v2/{exchange}/{symbol}/fin-items` | 500 | Tidak ada pengganti langsung; gunakan `/findata-view/company/financial` |
| `GET /emitten/non-login/v2/{exchange}/{symbol}/info` | 500 | Pakai `/emitten/non-login/{symbol}/info` |
| `GET /emitten/non-login/v2/{exchange}/{symbol}/fin-items` | 500 | Sama |
| `GET /partnership/emitten/v2/...` | 403 HTML Cloudflare | Di luar akses akun biasa |
| `GET /partnership/charts/{symbol}` | 403 HTML Cloudflare | Sama |
| `GET /company-price-feed/prices/{saham}/market` | 200 tetapi `markets: []` | Hanya berguna untuk indeks (`IHSG`) |
| `GET /charts/{symbol}` (v2) | 200 tetapi `prices: []` | Pakai `/charts/{symbol}/daily` |
| `GET /company-price-feed/v2/orderbook/template/{id}` | 404 untuk `id=1` | Butuh ID template valid dari `/orderbook` |
| `GET /insider/shareholding/network` | 400 tanpa `root_id`/`root_type`; enum pendek juga 400 | Kirim `root_type=SHAREHOLDING_NETWORK_NODE_TYPE_INVESTOR\|_COMPANY` |
| `GET /insider/shareholding/investors/{id}` | 404 untuk `id=54` | `54` adalah company ID; butuh investor ID |
| `GET /insider/shareholding/companies/{symbol}` | 400 `Invalid company id` | Gunakan company ID numerik dari `/emitten/{symbol}/info` |
| `GET /insider/shareholding/companies/{investor_id}` | 404 `Company not found` | Jangan tertukar dengan investor ID |
| `GET /emitten/catalog/{id}/company` | 404 `Katalog tidak ditemukan` | Gunakan `catalog_code`, bukan ID numerik |
| `GET /emitten/catalog/{code}/company?page=2` | 200 tetapi `companies: []`, pagination nol | Kirim `page` **dan** `limit` bersamaan |
| `GET /emitten-metadata/shareholders/{symbol}/chart` (`shareholder_type=scripless`) | 200 tetapi `legend: []` | Nilai valid: `all`, `local`, `foreign` |
| `GET /emitten/catalog?keyword=...` | 200, filter diabaikan | Filter client-side |
| `GET /search?...catalog_types=CATALOG_TYPE_KONGLO` | 400 nilai tidak valid | Tidak didukung; pakai `/emitten/catalog` |
| `GET /remisier/referral/status` | 404 `Data not found` | Tidak tersedia untuk akun ini |
| `GET /chartbit/search` | 404 `Unrecognized Command` | Tidak ada di backend |
| `GET /emitten/{symbol}/contact` | 200 `data: []` | Data kontak ada di `/profile` |

### 9.2 Data yang kosong atau tidak lengkap

| Hal | Detail |
|---|---|
| `financial.data_tables.periods/accounts` | Selalu kosong; data ada di `html_report` |
| `valuation/all/templates` | Kosong untuk akun pengujian |
| `corpaction/{symbol}/stock_conversion` | Kosong untuk BBCA |
| `emitten/{symbol}/contact` | Kosong untuk BBCA |
| `charts/{symbol}` v2 | `prices` kosong untuk BBCA |
| `prices/{saham}/market` | `markets` kosong untuk saham individual |
| `/search?type=people\|insider` | Kosong untuk keyword `BBCA` (bukan error) |
| `analyst-consensus.raw_value` | 0 untuk semua item yang diamati; gunakan `value` |
| `chartbit.daily.foreignflow` | Nilai tidak wajar (bug data); jangan dipakai tanpa validasi |
| `profile.listing_information` | Nol/kosong untuk BBCA meski sudah tercatat |
| `profile.profile` | Kosong secara makna untuk saham biasa (hanya untuk reksa dana/ETF) |
| `composition` dengan rentang Jul–Sep 2026 | `total_shares.raw = "1"` dan persentase `ALL` membengkak; `SCRIPPLESS` masih benar |
| `shareholding/companies.grand_total` | Hanya menjumlahkan holder yang tampil (BBCA 58,18%), bukan seluruh cap |
| `shareholding/investors.grand_total.percentage` | Dijumlahkan lintas emiten, bisa >100% (Prajogo 156,82%) |
| `profile.subsidiary` vs `/emitten-metadata/subsidiary` | Jumlah dan bentuk berbeda (BBCA: 9 vs 7 baris) |

### 9.3 Keanehan parameter

1. **Case sensitivity**
   - `/emitten/classification/company` memakai `ids` huruf kecil.
   - `?IDs=88` dan `?id=88` → 400.
2. **Nama enum mirip**
   - `MARKET_TYPE_REGULAR` (foreign-domestic) vs `MARKET_TYPE_REGULER` (order-trade).
   - `RT_PERIOD_LAST_6_MONTH` vs `BROKER_SUMMARY_PERIOD_LAST_6_MONTHS`.
3. **Array**
   - `prices/close` memakai bracket (`symbol[0]`) karena serializer qs default.
   - `marketdetectors` dan `broker/activity` memakai repeat (`symbols=A&symbols=B`).
   - `watchlist` memakai repeat (`category_types=...`).
   - Jika array salah format, server sering mengembalikan data untuk satu item saja tanpa error.
4. **`page`**
   - Umumnya dimulai dari 1.
   - `/search` dimulai dari 0.
5. **`statement_type`**
   - 1 dan 3 menghasilkan periode kuartalan; 2 menghasilkan periode tahunan `12M`.
   - Mapping ini berdasarkan pengamatan HTML, bukan dokumentasi resmi.
6. **`data_type`**
   - Hanya `1` yang diterima pada `/findata-view/company/financial`; nilai lain 400.
7. **Tiga jenis identifier**
   - **Company ID** numerik (`54`) untuk `/insider/shareholding/companies/{company_id}`; didapat dari `/emitten/{symbol}/info` → `data.id`.
   - **Investor ID** numerik (`8991`) untuk `/insider/shareholding/investors/{id}` dan `/insider/ubo`.
   - **Catalog code** string (`PRAJOGO-PANGESTU`) untuk `/emitten/catalog/{code}/company`; ID numerik katalog → 404.
8. **`shareholder_type`**
   - Harus huruf kecil: `all`, `local`, `foreign`.
   - Nilai lain tetap 200 tetapi `legend` kosong — gagal tanpa error.
9. **`root_type` network**
   - Harus enum panjang: `SHAREHOLDING_NETWORK_NODE_TYPE_INVESTOR` / `..._COMPANY`.
   - `INVESTOR`, `COMPANY`, dan `NODE_TYPE_INVESTOR` → 400.
10. **Paginasi katalog**
    - `/emitten/catalog/{code}/company` membutuhkan `page` dan `limit` bersamaan; `page` saja mengosongkan hasil.
    - Tanpa keduanya, seluruh isi grup dikembalikan.
11. **Format `report_date` tidak seragam**
    - Composition: `2026-09-30`.
    - Shareholding companies/investors: `30 Sep 26`.
    - UBO: `30 Sep 2026`.
    - Jangan memakai satu parser untuk ketiganya.

### 9.4 Token dan sesi

- Refresh token **dirotasi**. Jangan memakai satu refresh token di dua proses.
- Browser yang masih terbuka dapat melakukan refresh sendiri dan menginvalidasi token klien.
- Access token 24 jam; refresh 7 hari.
- Logout tidak diuji agar sesi tidak berakhir.
- Jangan pernah menaruh token di URL, log, atau pesan error.

### 9.5 Zona waktu

- `market-time.datetime` dan waktu running trade mengikuti waktu pasar Indonesia (WIB, UTC+7), tetapi **tidak menyertakan offset**.
- `live-stream.schedule` memakai ISO 8601 UTC (`Z`).
- `chartbit` memakai Unix timestamp (UTC detik).
- `date` pada info emiten berformat `23 Oct 2026` (hari-bulan-tahun, bahasa Inggris).

### 9.6 Batasan dokumentasi

- Endpoint tulis hanya didokumentasikan dari kode; tidak ada verifikasi live.
- WebSocket hanya dipetakan host dan kunci; skema protobuf tidak didekode.
- Chat dan stream memiliki banyak varian yang belum diuji.
- Beberapa endpoint mungkin berubah tanpa pemberitahuan; versi web saat pengujian `v3.54.5`.
- Tidak ada dokumentasi resmi Stockbit; semua berdasarkan observasi.

### 9.7 Etika dan legal

- Gunakan hanya dengan akun dan izin yang sah.
- Hormati Terms of Service Stockbit.
- Jangan melakukan scraping agresif, trading otomatis, atau manipulasi data.
- Jangan membagikan token atau data pribadi pengguna lain.
- Untuk data pasar, tetap verifikasi dengan sumber resmi sebelum mengambil keputusan investasi.

---

## 10. Contoh klien Python minimal

Contoh ini hanya mengonsumsi token yang sudah ada. Login tidak diotomatiskan karena memerlukan reCAPTCHA dan persetujuan perangkat.

```python
import json
import os
import threading
import time
import requests

BASE = os.getenv("EXODUS_BASE", "https://exodus.api.stockbit.com")

COMMON_HEADERS = {
    "Accept": "application/json",
    "Origin": "https://stockbit.com",
    "Referer": "https://stockbit.com/",
    "User-Agent": "Mozilla/5.0",
}


class ExodusError(RuntimeError):
    pass


class ExodusClient:
    def __init__(self, access_token: str, refresh_token: str, token_file: str | None = None):
        self.access = access_token
        self.refresh = refresh_token
        self.token_file = token_file
        self.lock = threading.Lock()
        self.session = requests.Session()

    # ---------- token ----------
    def _save_tokens(self):
        if not self.token_file:
            return
        tmp = self.token_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"access": self.access, "refresh": self.refresh}, f)
        os.chmod(tmp, 0o600)
        os.replace(tmp, self.token_file)

    def _refresh_if_needed(self, access_used: str):
        with self.lock:
            # Proses lain mungkin sudah me-refresh saat kita menunggu lock.
            if self.access != access_used:
                return
            r = self.session.post(
                f"{BASE}/login/refresh",
                headers={
                    **COMMON_HEADERS,
                    "Authorization": f"Bearer {self.refresh}",
                },
                timeout=20,
            )
            if r.status_code != 200:
                raise ExodusError(f"refresh failed: {r.status_code} {r.text[:200]}")
            data = r.json()["data"]
            self.access = data["access"]["token"]
            self.refresh = data["refresh"]["token"]
            self._save_tokens()

    # ---------- GET ----------
    def get(self, path: str, params=None, timeout: int = 20):
        last_error = None
        for attempt in range(2):
            access_used = self.access
            r = self.session.get(
                f"{BASE}{path}",
                params=params,
                headers={**COMMON_HEADERS, "Authorization": f"Bearer {access_used}"},
                timeout=timeout,
            )

            if r.status_code == 401 and attempt == 0:
                self._refresh_if_needed(access_used)
                continue

            if r.status_code == 429:
                retry_after = int(r.headers.get("Retry-After", "1"))
                time.sleep(min(retry_after, 10))
                last_error = ExodusError("429 rate limited")
                continue

            if r.status_code >= 400:
                raise ExodusError(f"{r.status_code} {r.text[:300]}")

            body = r.json()
            if isinstance(body, dict) and body.get("error_type"):
                raise ExodusError(f"{body['error_type']}: {body.get('message')}")
            return body

        raise last_error or ExodusError("request failed after retry")


if __name__ == "__main__":
    client = ExodusClient(
        access_token=os.environ["EXODUS_ACCESS"],
        refresh_token=os.environ["EXODUS_REFRESH"],
        token_file=os.getenv("EXODUS_TOKEN_FILE"),
    )

    info = client.get("/emitten/BBCA/info")
    print(info["data"]["symbol"], info["data"]["price"])

    # Batch harga: format bracket, sesuai serializer web.
    symbols = ["BBCA", "BBRI", "BMRI"]
    params = [("interval", "1")]
    params += [(f"symbol[{i}]", s) for i, s in enumerate(symbols)]
    prices = client.get("/company-price-feed/prices/close", params=params)
    for row in prices["data"]:
        print(row["symbol"], row["prices"][-1] if row["prices"] else None)
```

**Catatan implementasi:**

- `_refresh_if_needed` membandingkan token yang dipakai request gagal dengan token saat ini; jika sudah berubah, tidak perlu refresh lagi.
- Simpan token dengan permission `0600`.
- Jangan mencetak `access`/`refresh` ke log.
- Untuk endpoint berat, naikkan `timeout` menjadi 60 detik.
- Untuk batch besar, loop dengan jeda dan batasi percobaan.

---

## 11. Catatan pengujian dan lampiran

### 11.1 Lingkungan pengujian

| Item | Nilai |
|---|---|
| Tanggal | 23–31 Oktober 2026 |
| Build web (awal) | `v3.54.5` (306 file JS, ±15 MB) |
| Build web (pembaruan) | `v3.54.10` (339 chunk JS, ±16 MB) |
| Route halaman | 148 (dari `_buildManifest.js`) |
| Halaman di-capture | 25+ |
| Respons runtime | 132 |
| Path unik runtime | 107 |
| Probe tambahan | 90+ respons tersimpan (profil, UBO, komposisi, chart, katalog) |
| Access token | 24 jam; diperbarui otomatis selama pengujian, tidak dicatat |
| Refresh token | 7 hari; dirotasi setiap refresh |

### 11.2 Metodologi

1. **Static analysis**
   - Unduh `_buildManifest.js` dan seluruh chunk JS.
   - Cari string path (`"/..."`), konstanta host, enum, dan pemanggilan axios.
   - Beautify modul service (`prettier`) untuk membaca parameter dan body.
2. **Runtime capture**
   - Jalankan Chromium headless dengan CDP.
   - Buka halaman-halaman utama (emiten, chart, orderbook, screener, watchlist, stream, profile, academy).
   - Rekam request/response via CDP Network domain.
   - Simpan body ke file dan indeks URL.
3. **Live probing**
   - Panggil endpoint dengan token valid.
   - Variasikan parameter satu per satu untuk menemukan yang wajib.
   - Catat status, body, dan header.
4. **Verifikasi**
   - Bandingkan respons dengan UI.
   - Cek konsistensi angka (harga, volume, nilai).
   - Tandai endpoint yang gagal atau kosong.
5. **Re-diff build `v3.54.10`**
   - Unduh ulang `_buildManifest.js` dan seluruh chunk.
   - Fokus pada route `symbol/[symbol]/shareholder-composition`, `/stock-group`, serta service `ownership`, `symbol page`, dan `shareholder-composition`.
   - Cocokkan nama fungsi/parameter dengan respons live, bukan hanya nama path.
6. **Verifikasi live terfokus**
   - Profil: BBCA, CUAN, BRPT.
   - Kepemilikan: company `54`/`93`/`1000003994`, investor `8991`, network investor/company.
   - Komposisi: kedua `view`, dengan dan tanpa rentang periode.
   - Chart: `all`, `local`, `foreign`, plus snapshot `date`.
   - Katalog: daftar KONGLO, `PRAJOGO-PANGESTU`, `SALIM`, `ASTRA`.
   - Simpan status, body, dan URL final untuk setiap probe.

### 11.3 Keterbatasan

- Tidak semua halaman dikunjungi; beberapa endpoint hanya ditemukan di kode.
- Endpoint tulis tidak dijalankan.
- WebSocket `/stock-group` (`marketMoverBatch`) belum didekode; hanya parameter dan enum yang dipetakan dari bundle.
- Data contoh hanya BBCA, CUAN, BRPT, dan tiga katalog konglomerasi.
- Perilaku dapat berubah antar build.
- `contact` kosong untuk BBCA meski profil memuat kontak.
- `shareholder_type=scripless` bukan nilai valid pada chart; komposisi scripless diambil dari endpoint composition.
- Rentang composition memiliki bug `total_shares` untuk Jul–Sep 2026 (lihat 5.8.2).
- Angka `grand_total` tidak boleh ditafsirkan sebagai kapitalisasi penuh atau porsi tunggal.

### 11.4 Artefak

Artefak kerja berikut diproduksi selama analisis. Direktori tersebut bersifat sementara dan tidak dipertahankan; yang disimpan di repository hanya dokumen ini.

| Path | Isi |
|---|---|
| `/tmp/opencode/exodus/js/` | 306 file JS build `v3.54.5` (artefak awal) |
| `/tmp/opencode/exodus/capture/index.json` | Indeks 132 respons |
| `/tmp/opencode/exodus/capture/*.json` | Body respons |
| `/tmp/opencode/exodus/probe/` | Hasil probe tambahan |
| `/tmp/opencode/exodus/module_*.pretty.js` | Modul service hasil beautify |
| `/tmp/opencode/stockbit/js/` | 339 chunk JS build `v3.54.10` |
| `/tmp/opencode/stockbit/probe/` | Respons probe profil, UBO, komposisi, chart, katalog |
| `/tmp/opencode/stockbit/ownership.pretty.js` | Service `/insider/ubo`, `/insider/shareholding/*`, network |
| `/tmp/opencode/stockbit/symbol_page.pretty.js` | Service profil, subsidiary, composition |
| `/tmp/opencode/stockbit/shareholder-composition.pretty.js` | Service chart + composition |
| `/tmp/opencode/stockbit/search_page.pretty.js` | Route `/search` (insider → `/ownership`) |
| `/tmp/opencode/stockbit/stock-group.pretty.js` | Route `/stock-group` + enum KONGLO |

> Jangan menyimpan token, cookie, atau kredensial di repository. Artefak probe di atas tidak disalin ke repo.

### 11.5 Glosarium

| Istilah | Arti |
|---|---|
| Emitten | Emiten/saham |
| Orderbook | Antrean bid/offer |
| Running trade | Tape transaksi |
| Trade book | Rekap transaksi per harga/waktu |
| Broker summary | Ringkasan transaksi per broker |
| Bandar detector | Indikator akumulasi/distribusi |
| UBO | Ultimate Beneficial Owner |
| Screener | Penyaring saham |
| Watchlist | Daftar pantau |
| Stream | Feed sosial |
| Carina | Sistem trading Stockbit |
| Exodus | Backend data/API Stockbit |

---

## 12. Peta cepat menu profil perusahaan dan group konglomerasi

Bagian ini merangkum pasangan menu UI → endpoint. Semua contoh memakai token Bearer kecuali chart shareholder (token khusus) dan WebSocket.

### 12.1 Profil perusahaan

| Menu / tab | Endpoint | Field utama |
|---|---|---|
| Header emiten | `GET /emitten/{symbol}/info` | `id`, `symbol`, `name`, `last`, `percentage` |
| Profil / latar belakang | `GET /emitten/{symbol}/profile` | `background`, `history`, `key_executive`, `address`, `secretary`, `classification` |
| Pemegang saham | `profile.shareholder`, `profile.shareholder_one_percent`; detail: `GET /insider/shareholding/companies/{company_id}` | `percentage`, `name`, `scripless`, `scrip`, `classification` |
| Perubahan pemegang saham | `GET /insider/company/majorholder?symbol={symbol}&page=1` | `movement[]`, `action_type`, `changes` |
| UBO | `GET /insider/shareholding/ubo/companies/{symbol}` | `owners[].name`, `ownership_percentage.to/from`, `subholdings[]` |
| Jumlah pemegang saham | `profile.shareholder_numbers[]` (tidak ada endpoint terpisah) | `shareholder_date`, `total_share`, `change` |
| Komposisi — All | `GET /insider/shareholding/composition/companies/{symbol}?view=SHAREHOLDERS_COMPOSITION_VIEW_ALL` | `periods[].compositions[]` |
| Komposisi — Scripless | `...?view=SHAREHOLDERS_COMPOSITION_VIEW_SCRIPPLESS` | `periods[].compositions[]` |
| Holding composition — All/Local/Foreign | `POST /emitten-metadata/shareholders/token` → `GET /emitten-metadata/shareholders/{symbol}/chart?shareholder_type=all\|local\|foreign&value_year=12` | `legend[]`, `summary[]` |
| Anak perusahaan (ringkas) | `profile.subsidiary[]` | `company`, `types`, `percentage`, `value` |
| Anak perusahaan (tabel aset) | `GET /emitten-metadata/subsidiary/{symbol}` | `company_name`, `business_type`, `total_assets`, `unit` |
| Kontak | `profile.address[]` (utama); `GET /emitten/{symbol}/contact` sering kosong | `office`, `phone`, `email[]`, `website` |

**Urutan pengambilan yang disarankan:**

1. `GET /emitten/{symbol}/info` → simpan `data.id` sebagai `company_id`.
2. `GET /emitten/{symbol}/profile` → render profil, pemegang saham, jumlah pemegang saham, UBO, anak perusahaan.
3. Jika butuh detail per-holder: `GET /insider/shareholding/companies/{company_id}`.
4. Jika butuh komposisi: panggil composition (tanpa rentang untuk snapshot terbaru).
5. Jika butuh tren holding scripless: minta token lalu panggil chart.
6. Jika butuh tabel aset anak perusahaan: panggil `/emitten-metadata/subsidiary/{symbol}`.

### 12.2 Group konglomerasi

Ada dua jalur yang tidak saling menggantikan:

**Jalur A — pencarian insider (dari nama orang):**

```text
GET /search?keyword=prajogo&type=all
  → data.insider[] = { id: "8991", label: "prajogo pangestu" }
  → UI: /ownership?investor=8991
  → GET /insider/ubo?investor_id=8991                  (langsung + tidak langsung)
  → GET /insider/shareholding/investors/8991           (hanya langsung)
  → GET /insider/shareholding/network?root_id=8991&root_type=SHAREHOLDING_NETWORK_NODE_TYPE_INVESTOR&max_depth=3&max_edge_per_node=20
```

**Jalur B — katalog KONGLO (dari daftar grup):**

```text
GET /emitten/catalog?catalog_type=CATALOG_TYPE_KONGLO&page=1&limit=100
  → 33 grup; cari catalog_name/catalog_code di client
  → GET /emitten/catalog/PRAJOGO-PANGESTU/company?page=1&limit=100
  → 9 emiten: CUAN, CDIA, BRPT, PTRO, TPIA, BREN, RATU, SSIA, SINI
```

**Perbedaan hasil:**

| Aspek | Jalur A (insider) | Jalur B (katalog) |
|---|---|---|
| Titik masuk | Nama orang | Nama grup |
| Cakupan | Kepemilikan investor pada emiten | Seluruh emiten yang diatribusikan ke grup |
| Contoh Prajogo | 6 emiten (UBO) | 9 emiten |
| Butuh ID | `investor_id` | `catalog_code` |
| Pencarian nama | Server-side (`/search`) | Client-side (filter diabaikan server) |

Gunakan Jalur A untuk "siapa pemilik saham X" dan Jalur B untuk "apa saja saham group Y". Selisih 6 vs 9 menunjukkan kedua sumber tidak identik — jangan menganggap salah satunya lengkap.

### 12.3 Resep `curl` minimal

```bash
BASE="https://exodus.stockbit.com"
AUTH="Authorization: Bearer $TOKEN"

# Profil lengkap
curl -s "$BASE/emitten/BBCA/profile" -H "$AUTH"

# Company ID → pemegang saham
curl -s "$BASE/emitten/BBCA/info" -H "$AUTH" | jq -r '.data.id'
curl -s "$BASE/insider/shareholding/companies/54" -H "$AUTH"

# UBO per emiten
curl -s "$BASE/insider/shareholding/ubo/companies/CUAN" -H "$AUTH"

# UBO lintas emiten
curl -s "$BASE/insider/ubo?investor_id=8991" -H "$AUTH"

# Komposisi (snapshot terbaru)
curl -s "$BASE/insider/shareholding/composition/companies/BBCA?view=SHAREHOLDERS_COMPOSITION_VIEW_SCRIPPLESS" -H "$AUTH"

# Chart holding composition
CHART_TOKEN=$(curl -s -X POST "$BASE/emitten-metadata/shareholders/token" -H "$AUTH" | jq -r '.data.value')
curl -s "$BASE/emitten-metadata/shareholders/BBCA/chart?symbol=BBCA&shareholder_type=all&value_year=12" \
  -H "Authorization: $CHART_TOKEN"

# Katalog konglomerasi
curl -s "$BASE/emitten/catalog?catalog_type=CATALOG_TYPE_KONGLO&page=1&limit=100" -H "$AUTH"
curl -s "$BASE/emitten/catalog/PRAJOGO-PANGESTU/company?page=1&limit=100" -H "$AUTH"
```

### 12.4 Checklist verifikasi cepat

- [ ] `company_id` diambil dari `info.data.id`, bukan dari symbol.
- [ ] `investor_id` berasal dari `shareholder_one_percent[].id`/`holders[].investor.id`, bukan dari company ID.
- [ ] `catalog_code` string, bukan ID numerik.
- [ ] `view` composition memakai enum panjang.
- [ ] `shareholder_type` huruf kecil; `scripless` bukan nilai valid.
- [ ] `page` + `limit` dikirim bersamaan untuk katalog.
- [ ] `report_date` diparse sesuai endpoint (tiga format berbeda).
- [ ] `grand_total` tidak dianggap kapitalisasi penuh.
- [ ] Token chart dikirim tanpa `Bearer`.
- [ ] Tidak ada token/kredensial yang tercetak di log atau dokumen.

---

## Lampiran A — Inventaris endpoint yang ter-capture

Tabel berikut dihasilkan dari `capture/index.json` (132 respons, 107 path unik). Kolom “Method” dan “Status” adalah yang diamati. Path yang memuat username/user ID telah disamarkan.

| # | Method | Path | Status | Count |
|---|---|---|---|---|
| 1 | GET | `/academy/lessons/last-read` | 200 | 1 |
| 2 | POST | `/academy/tokens/new` | 200 | 1 |
| 3 | GET | `/academy/unboxing` | 200 | 1 |
| 4 | POST | `/academy/v2/module` | 200 | 1 |
| 5 | GET | `/auth/websocket/key` | 200 | 1 |
| 6 | GET | `/chartbit/BBCA/price/daily` | 200 | 1 |
| 7 | GET | `/chartbit/BBCA/price/intraday` | 200 | 6 |
| 8 | GET | `/chartbit/chart-drawings` | 200 | 1 |
| 9 | GET | `/chartbit/charts` | 200 | 1 |
| 10 | GET | `/chartbit/charts/{chart_id}` | 200 | 1 |
| 11 | GET | `/chartbit/studies` | 200 | 1 |
| 12 | GET | `/charts/BBCA/daily` | 200 | 1 |
| 13 | GET | `/charts/IHSG/daily` | 200 | 1 |
| 14 | GET | `/chat/v2/rooms/unread/count` | 200 | 1 |
| 15 | GET | `/company-price-feed/market-time` | 200 | 1 |
| 16 | GET | `/company-price-feed/market-time/session` | 200 | 1 |
| 17 | GET | `/company-price-feed/price-performance/BBCA` | 200 | 1 |
| 18 | GET | `/company-price-feed/prices/IHSG/market` | 200 | 2 |
| 19 | GET | `/company-price-feed/prices/close` | 200 | 1 |
| 20 | GET | `/company-price-feed/v2/orderbook/companies/ADHI` | 200 | 1 |
| 21 | GET | `/company-price-feed/v2/orderbook/companies/ADRO` | 200 | 1 |
| 22 | GET | `/company-price-feed/v2/orderbook/companies/APII` | 200 | 1 |
| 23 | GET | `/company-price-feed/v2/orderbook/companies/ASGR` | 200 | 1 |
| 24 | GET | `/company-price-feed/v2/orderbook/companies/BACA` | 200 | 1 |
| 25 | GET | `/company-price-feed/v2/orderbook/companies/BBCA` | 200 | 1 |
| 26 | GET | `/company-price-feed/v2/orderbook/companies/BBKP` | 200 | 1 |
| 27 | GET | `/company-price-feed/v2/orderbook/companies/BBNI` | 200 | 1 |
| 28 | GET | `/company-price-feed/v2/orderbook/companies/BBRI` | 200 | 1 |
| 29 | GET | `/company-price-feed/v2/orderbook/companies/BCAP` | 200 | 1 |
| 30 | GET | `/company-price-feed/v2/orderbook/companies/BOSS` | 200 | 1 |
| 31 | GET | `/company-price-feed/v2/orderbook/companies/BUKA` | 200 | 1 |
| 32 | GET | `/company-price-feed/v2/orderbook/companies/BYAN` | 200 | 1 |
| 33 | GET | `/company-price-feed/v2/orderbook/companies/DOID` | 200 | 1 |
| 34 | GET | `/company-price-feed/v2/orderbook/companies/HMSP` | 200 | 1 |
| 35 | GET | `/company-price-feed/v2/orderbook/companies/HRUM` | 200 | 1 |
| 36 | GET | `/company-price-feed/v2/orderbook/companies/INOV` | 200 | 1 |
| 37 | GET | `/company-price-feed/v2/orderbook/companies/ITMG` | 200 | 1 |
| 38 | GET | `/company-price-feed/v2/orderbook/companies/KKGI` | 200 | 1 |
| 39 | GET | `/company-price-feed/v2/orderbook/companies/KREN` | 200 | 1 |
| 40 | GET | `/company-price-feed/v2/orderbook/companies/MBAP` | 200 | 1 |
| 41 | GET | `/company-price-feed/v2/orderbook/companies/MPPA` | 200 | 1 |
| 42 | GET | `/company-price-feed/v2/orderbook/companies/MTEL` | 200 | 1 |
| 43 | GET | `/company-price-feed/v2/orderbook/companies/PALM` | 200 | 1 |
| 44 | GET | `/company-price-feed/v2/orderbook/companies/PNLF` | 200 | 1 |
| 45 | GET | `/company-price-feed/v2/orderbook/companies/PTBA` | 200 | 1 |
| 46 | GET | `/company-price-feed/v2/orderbook/companies/SMMT` | 200 | 1 |
| 47 | GET | `/company-price-feed/v2/orderbook/companies/SRTG` | 200 | 1 |
| 48 | GET | `/company-price-feed/v2/orderbook/companies/TLKM` | 200 | 1 |
| 49 | GET | `/company-price-feed/v2/orderbook/companies/TOBA` | 200 | 1 |
| 50 | GET | `/company-price-feed/v2/orderbook/companies/WIIM` | 200 | 1 |
| 51 | GET | `/corpaction` | 200 | 1 |
| 52 | GET | `/corpaction/dividend` | 200 | 1 |
| 53 | GET | `/emitten-metadata/shareholders/BBCA/chart` | 200 | 1 |
| 54 | POST | `/emitten-metadata/shareholders/token` | 200 | 1 |
| 55 | GET | `/emitten-metadata/subsidiary/BBCA` | 200 | 1 |
| 56 | GET | `/emitten/BBCA/contact` | 200 | 1 |
| 57 | GET | `/emitten/BBCA/info` | 200 | 2 |
| 58 | GET | `/emitten/BBCA/profile` | 200 | 1 |
| 59 | GET | `/emitten/classification` | 200 | 3 |
| 60 | GET | `/emitten/indexes/special-board` | 200 | 1 |
| 61 | GET | `/emitten/trending` | 200 | 1 |
| 62 | GET | `/emitten/v2/IDX/BBCA/info-type` | 200 | 1 |
| 63 | GET | `/findata-view/company/financial` | 200 | 1 |
| 64 | GET | `/findata-view/foreign-domestic/v1/chart-data/BBCA` | 200 | 1 |
| 65 | GET | `/insider/company/majorholder` | 200 | 3 |
| 66 | GET | `/insider/shareholding/companies/54` | 200 | 1 |
| 67 | GET | `/insider/shareholding/composition/companies/BBCA` | 200 | 1 |
| 68 | GET | `/insider/shareholding/ubo/companies/BBCA` | 200 | 1 |
| 69 | GET | `/keystats/ratio/v1/BBCA` | 200 | 1 |
| 70 | GET | `/live-stream/event` | 200 | 1 |
| 71 | GET | `/marketdetectors/BBCA` | 200 | 1 |
| 72 | GET | `/notification/count/unread` | 200 | 1 |
| 73 | GET | `/notification/v3/settings` | 200 | 1 |
| 74 | GET | `/order-trade/broker/activity` | 200 | 1 |
| 75 | GET | `/order-trade/broker/activity-chart` | 200 | 1 |
| 76 | GET | `/order-trade/broker/top` | 200 | 1 |
| 77 | GET | `/order-trade/running-trade` | 200 | 2 |
| 78 | GET | `/orderbook/companies/BBCA` | 200 | 1 |
| 79 | POST | `/paywall/counter/increment` | 200 | 1 |
| 80 | GET | `/paywall/eligibility/check` | 200 | 13 |
| 81 | GET | `/remisier/referral/status` | 404 | 1 |
| 82 | GET | `/research/indicator/new` | 200 | 2 |
| 83 | GET | `/screener/favorites` | 200 | 1 |
| 84 | GET | `/screener/finitem-watchlist` | 200 | 1 |
| 85 | GET | `/screener/metric` | 200 | 1 |
| 86 | GET | `/screener/preset` | 200 | 1 |
| 87 | GET | `/screener/templates` | 200 | 1 |
| 88 | GET | `/screener/templates/31` | 200 | 1 |
| 89 | GET | `/screener/universe` | 200 | 1 |
| 90 | GET | `/stream/reactions` | 200 | 1 |
| 91 | GET | `/stream/v3` | 200 | 1 |
| 92 | GET | `/stream/v3/symbol/BBCA` | 200 | 1 |
| 93 | GET | `/stream/v3/symbol/BBCA/pinned` | 200 | 1 |
| 94 | GET | `/user-setting/configurations` | 200 | 1 |
| 95 | GET | `/user/profile` | 200 | 1 |
| 96 | GET | `/user/profile/{username}` | 200 | 1 |
| 97 | GET | `/user/v2/discovery/trending` | 200 | 1 |
| 98 | GET | `/v2/account/bank/amend` | 200 | 1 |
| 99 | GET | `/v2/registration/check` | 200 | 1 |
| 100 | GET | `/valuation/all/templates` | 200 | 1 |
| 101 | GET | `/valuation/metrics/lists` | 200 | 1 |
| 102 | GET | `/verified-badge/user/{user_id}` | 200 | 1 |
| 103 | GET | `/watchlist` | 200 | 1 |
| 104 | GET | `/watchlist/1201415` | 200 | 1 |
| 105 | GET | `/watchlist/company/follower-info` | 200 | 1 |
| 106 | GET | `/watchlist/favorite` | 200 | 1 |
| 107 | GET | `/watchlist/metric` | 200 | 1 |

### A.1 Probe live tambahan (v1.1)

Baris berikut berasal dari probe terfokus, bukan capture runtime awal. Semua 200 kecuali dicatat.

| # | Method | Path | Status | Catatan |
|---|---|---|---|---|
| 108 | GET | `/emitten/{symbol}/profile` | 200 | BBCA, CUAN, BRPT |
| 109 | GET | `/emitten/{symbol}/info` | 200 | Sumber `company_id` |
| 110 | GET | `/emitten/{symbol}/contact` | 200 | `data: []` untuk BBCA |
| 111 | GET | `/emitten-metadata/subsidiary/{symbol}` | 200 | 7 baris untuk BBCA |
| 112 | POST | `/emitten-metadata/shareholders/token` | 200 | Token chart |
| 113 | GET | `/emitten-metadata/shareholders/{symbol}/chart` | 200 | `all`, `local`, `foreign` |
| 114 | GET | `/emitten/catalog` | 200 | 33 grup KONGLO dengan `limit=100` |
| 115 | GET | `/emitten/catalog/{catalog_code}/company` | 200 | `PRAJOGO-PANGESTU`, `SALIM`, `ASTRA` |
| 116 | GET | `/insider/company/majorholder` | 200 | `symbol=BBCA` |
| 117 | GET | `/insider/shareholding/composition/companies/{symbol}` | 200 | ALL dan SCRIPPLESS |
| 118 | GET | `/insider/shareholding/ubo/companies/{symbol}` | 200 | BBCA, CUAN |
| 119 | GET | `/insider/shareholding/companies/{company_id}` | 200 | `54`, `93`, `1000003994` |
| 120 | GET | `/insider/shareholding/investors/{investor_id}` | 200 | `8991` |
| 121 | GET | `/insider/shareholding/network` | 200 | investor `8991`, company `1000003994` |
| 122 | GET | `/insider/ubo` | 200 | `investor_id=8991`, plus `report_date` historis |

Status non-200 yang tercatat: `companies/BBCA` 400, `companies/8991` 404, `investors/BBCA` 400, `catalog/{id}/company` 404, `search?...catalog_types=CATALOG_TYPE_KONGLO` 400.

---

## Lampiran B — Checklist penggunaan

- [ ] Token disimpan di file `0600`, bukan di repository.
- [ ] Refresh memakai lock single-flight.
- [ ] Rate limit ≤ 8 req/s.
- [ ] Timeout dan retry hanya untuk GET.
- [ ] Cek `error_type` meski HTTP 200.
- [ ] Jangan retry POST/PUT/DELETE.
- [ ] Redaksi email/telepon/username dari log.
- [ ] Hormati Terms of Service dan izin pengguna.

---

## Lampiran C — Riwayat dokumen

| Versi | Tanggal | Perubahan |
|---|---|---|
| 1.0 | 23 Okt 2026 | Versi awal: 107 path runtime, 40+ probe, enum, error, klien Python |
| 1.1 | 31 Okt 2026 | Build `v3.54.10`; profil perusahaan (5.2.5), anak perusahaan (5.3.1), chart holding composition (5.3.3), pemegang saham/UBO/komposisi/network (5.8.2–5.8.7), katalog konglomerasi (5.17), peta menu (12), koreksi status dan batasan |
