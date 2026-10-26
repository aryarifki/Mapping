# ENDPOINTS.md

Daftar lengkap endpoint publik yang berhasil dipetakan dan **diverifikasi dengan
permintaan nyata**. Setiap baris punya contoh respons mentah di `samples/`.

**Total didokumentasikan: 55** (KSEI 34, AKSes/SID 14, IDX 7)

Legenda status: ✅ aktif · ⚠️ butuh parameter khusus · 🔒 perlu login · ❌ mati/diblokir

## Ringkasan per situs

| Situs | Endpoint didokumentasikan | Aktif |
|---|---|---|
| KSEI (`www.ksei.co.id`) | 34 | 31 |
| AKSes / SID (`akses.ksei.co.id`) | 14 | 6 |
| IDX (`www.idx.co.id`) | 7 | 7 |

## KSEI

| # | Host | Path | Method | Parameter | Kategori | Status |
|---|---|---|---|---|---|---|
| K01 | `www.ksei.co.id` | `/api/settings` | GET | `locale`='id' | site-meta | ✅ aktif |
| K02 | `www.ksei.co.id` | `/api/menus` | GET | `locale`='id' | site-meta | ✅ aktif |
| K03 | `www.ksei.co.id` | `/api/banners` | GET | `locale`='id' | site-meta | ✅ aktif |
| K04 | `www.ksei.co.id` | `/api/seo_metas` | GET | `locale`='id' | site-meta | ✅ aktif |
| K05 | `www.ksei.co.id` | `/api/board_types` | GET | `locale`='id' | reference | ✅ aktif |
| K06 | `www.ksei.co.id` | `/api/investor_demographic/sid_growths/types` | GET | `locale`='id' | investor/sid | ✅ aktif |
| K07 | `www.ksei.co.id` | `/api/investor_demographic/sid_growths` | GET | `locale`='en'&`filter[type]`='Number of Capital Market Investors'&`filter[three_years_data]`='October 2026' | investor/sid | ✅ aktif |
| K08 | `www.ksei.co.id` | `/api/investor_demographic/domestic_investors` | GET | `locale`='id' | investor/sid | ✅ aktif |
| K09 | `www.ksei.co.id` | `/api/investor_demographic/individual/age` | GET | `locale`='id' | investor/sid | ✅ aktif |
| K10 | `www.ksei.co.id` | `/api/investor_demographic/individual/education` | GET | `locale`='id' | investor/sid | ✅ aktif |
| K11 | `www.ksei.co.id` | `/api/investor_demographic/individual/gender` | GET | `locale`='id' | investor/sid | ✅ aktif |
| K12 | `www.ksei.co.id` | `/api/investor_demographic/individual/income` | GET | `locale`='id' | investor/sid | ✅ aktif |
| K13 | `www.ksei.co.id` | `/api/investor_demographic/individual/job_demographics` | GET | `locale`='id' | investor/sid | ✅ aktif |
| K14 | `www.ksei.co.id` | `/api/investor_demographic/mutual_assets` | GET | `locale`='en'&`filter[four_years_data]`='October 2026' | investor/sid | ✅ aktif |
| K15 | `www.ksei.co.id` | `/api/securities_ownerships` | GET | `locale`='id' | ownership | ✅ aktif |
| K16 | `www.ksei.co.id` | `/api/static_stocks` | GET | `locale`='id' | bulk-download | ✅ aktif |
| K17 | `www.ksei.co.id` | `/api/sro` | GET | `locale`='id' | reference | ✅ aktif |
| K18 | `www.ksei.co.id` | `/api/account_managements` | GET | `locale`='id' | account | ✅ aktif |
| K19 | `www.ksei.co.id` | `/api/account_managements/categories` | GET | `locale`='id' | reference | ✅ aktif |
| K20 | `www.ksei.co.id` | `/api/graph/aktiva_graphs/assets` | GET | `locale`='id'&`sort`='month' | graph | ✅ aktif |
| K21 | `www.ksei.co.id` | `/api/graph/aktiva_graphs/bonds` | GET | `locale`='id'&`sort`='month' | graph | ✅ aktif |
| K22 | `www.ksei.co.id` | `/api/graph/aktiva_graphs/shares` | GET | `locale`='id'&`sort`='month' | graph | ✅ aktif |
| K23 | `www.ksei.co.id` | `/api/graph/aktiva_graphs/sub_account` | GET | `locale`='id'&`sort`='month' | graph | ✅ aktif |
| K24 | `www.ksei.co.id` | `/api/graph/cbest_graphs/customer` | GET | `locale`='id' | graph | ✅ aktif |
| K25 | `www.ksei.co.id` | `/api/graph/cbest_graphs/instrument_information` | GET | `locale`='id' | graph | ✅ aktif |
| K26 | `www.ksei.co.id` | `/api/graph/overbooking_graphs/value` | GET | `locale`='id'&`sort`='month' | graph | ✅ aktif |
| K27 | `www.ksei.co.id` | `/api/graph/overbooking_graphs/volume` | GET | `locale`='id'&`sort`='month' | graph | ✅ aktif |
| K28 | `www.ksei.co.id` | `/api/graph/overbooking_graphs/frequency` | GET | `locale`='id'&`sort`='month' | graph | ✅ aktif |
| K29 | `www.ksei.co.id` | `/api/graph/overbooking_graphs/cnf` | GET | `locale`='id'&`sort`='month' | graph | ✅ aktif |
| K30 | `www.ksei.co.id` | `/api/graph/overbooking_graphs/sectrs` | GET | `locale`='id'&`sort`='month' | graph | ✅ aktif |
| K31 | `www.ksei.co.id` | `/api/graph/overbooking_graphs/bts` | GET | `locale`='id'&`sort`='month' | graph | ✅ aktif |
| K32 | `www.ksei.co.id` | `/api/auth/user` | GET | — | auth | 🔒 perlu login |
| K33 | `www.ksei.co.id` | `/api/auth/login` | POST | — | auth | 🔒 perlu login |
| K34 | `www.ksei.co.id` | `/api/auth/logout` | POST | — | auth | 🔒 perlu login |

<details><summary>Sumber penemuan per kategori</summary>

- **site-meta** — bundle `/_nuxt/*.js` halaman https://www.ksei.co.id/id
- **reference** — bundle `/_nuxt/*.js` halaman https://www.ksei.co.id/id
- **investor/sid** — https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik
- **ownership** — https://www.ksei.co.id/id/publikasi/data-dan-statistik/kepemilikan-efek
- **bulk-download** — https://www.ksei.co.id/id/publikasi/data-dan-statistik/statik-efek
- **account** — bundle `/_nuxt/*.js` halaman https://www.ksei.co.id/id
- **graph** — https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik
- **auth** — bundle `/_nuxt/*.js` halaman https://www.ksei.co.id/id

</details>

## AKSes / SID

| # | Host | Path | Method | Parameter | Kategori | Status |
|---|---|---|---|---|---|---|
| S01 | `akses.ksei.co.id` | `/service/informasi-saham/daftar-saham` | GET | — | market-data | ✅ aktif |
| S02 | `akses.ksei.co.id` | `/service/demografis/gender` | GET | `id`= | investor/sid | ✅ aktif |
| S03 | `akses.ksei.co.id` | `/service/demografis/detil-data` | GET | — | investor/sid | ✅ aktif |
| S04 | `akses.ksei.co.id` | `/service/demografi/master/place` | GET | — | reference | ✅ aktif |
| S05 | `akses.ksei.co.id` | `/service/demografis/updated-at` | GET | `lang`='id' | investor/sid | ✅ aktif |
| S06 | `akses.ksei.co.id` | `/service/aksi-korporasi/news/landing/periode/current-year` | GET | — | corporate-action | ✅ aktif |
| S07 | `akses.ksei.co.id` | `/service/demografis/occupation` | POST | `city`=&`province`= | investor/sid | http-500 |
| S08 | `akses.ksei.co.id` | `/service/demografi/age` | GET | `city`=&`province`= | investor/sid | http-500 |
| S09 | `akses.ksei.co.id` | `/service/demografi/investor` | GET | `city`=&`province`= | investor/sid | http-500 |
| A01 | `akses.ksei.co.id` | `/service/orchid/` | GET | — | authenticated | 🔒 perlu login |
| A02 | `akses.ksei.co.id` | `/service/myportofolio/` | GET | — | authenticated | 🔒 perlu login |
| A03 | `akses.ksei.co.id` | `/service/myaccount/` | GET | — | authenticated | 🔒 perlu login |
| A04 | `akses.ksei.co.id` | `/service/emiten-area/` | GET | — | authenticated | 🔒 perlu login |
| A05 | `akses.ksei.co.id` | `/service/admin-mgt/` | GET | — | authenticated | 🔒 perlu login |

## IDX

| # | Host | Path | Method | Parameter | Kategori | Status |
|---|---|---|---|---|---|---|
| I01 | `www.idx.co.id` | `/primary/StockData/GetSecuritiesStock` | GET | `start`='0'&`length`='9999'&`language`='id' | listing | ✅ aktif |
| I02 | `www.idx.co.id` | `/primary/ListedCompany/GetCompanyProfiles` | GET | `start`='0'&`length`='9999'&`language`='id' | listing | ✅ aktif |
| I03 | `www.idx.co.id` | `/primary/ListedCompany/GetCompanyProfilesDetail` | GET | `KodeEmiten`='BBCA'&`language`='id' | listing | ✅ aktif |
| I04 | `www.idx.co.id` | `/primary/TradingSummary/GetStockSummary` | GET | `start`='0'&`length`='9999'&`language`='id' | market-data | ✅ aktif |
| I05 | `www.idx.co.id` | `/primary/TradingSummary/GetIndexSummary` | GET | `start`='0'&`length`='9999'&`language`='id' | market-data | ✅ aktif |
| I06 | `www.idx.co.id` | `/primary/TradingSummary/GetBrokerSummary` | GET | `start`='0'&`length`='9999'&`language`='id' | market-data | ✅ aktif |
| I07 | `www.idx.co.id` | `/primary/ListedCompany/GetAnnouncement` | GET | `start`='0'&`length`='5'&`pagesize`='5'&`language`='id' | disclosure | ✅ aktif |

## Catatan pembacaan

- Semua endpoint KSEI/AKSes menerima `User-Agent` umum; tidak ada signature, token, atau
  API key. Yang wajib hanya header `Accept: application/json` untuk `/api/*`.
- Endpoint IDX **mewajibkan** header `Sec-Fetch-Dest/Mode/Site`. Tanpa itu Cloudflare
  mengembalikan halaman challenge `Just a moment...` (HTTP 403), bukan JSON.
- IDX membatasi laju secara agresif. Collector memakai jeda 6 detik dan backoff 20–60 detik.

Detail per situs: [`docs/ksei_endpoints.md`](docs/ksei_endpoints.md) ·
[`docs/sid_endpoints.md`](docs/sid_endpoints.md) ·
[`docs/idx_endpoints.md`](docs/idx_endpoints.md)
