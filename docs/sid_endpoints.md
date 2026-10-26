# AKSes / SID — endpoint publik (`akses.ksei.co.id`)

### [S01] GET https://akses.ksei.co.id/service/informasi-saham/daftar-saham

- **Deskripsi**: Full listed-securities snapshot with reference prices
- **Parameter**: —
- **Response fields**: `sec_issuer`, `code_base_sec`, `opening_price`, `closing_price`, `change`, `percent`
- **Contoh**: lihat `samples/sid/S01__daftar-saham.json`
- **Status**: ✅ aktif (per 2026-10-26T07:35:19Z)
- **HTTP**: 200 · **Ukuran**: 209529 byte
- **Sumber ditemukan**: bundle `https://akses.ksei.co.id/main.9351f7724eaebe22ca45.js`

---

### [S02] GET https://akses.ksei.co.id/service/demografis/gender

- **Deskripsi**: SID investor demographics by province/city split by gender (empty id = national)
- **Parameter**: `id`=
- **Response fields**: `kodeDukcapil`, `latitude`, `longitude`, `latlong`, `provKota`, `wanita`, `pria`
- **Contoh**: lihat `samples/sid/S02__gender.json`
- **Status**: ✅ aktif (per 2026-10-26T07:35:19Z)
- **HTTP**: 200 · **Ukuran**: 91051 byte
- **Sumber ditemukan**: bundle `https://akses.ksei.co.id/main.9351f7724eaebe22ca45.js`

---

### [S03] GET https://akses.ksei.co.id/service/demografis/detil-data

- **Deskripsi**: Per-region investor counts with lat/long, for map rendering
- **Parameter**: —
- **Response fields**: `kodeDukcapil`, `latitude`, `longitude`, `latlong`, `province`, `wanita`, `pria`
- **Contoh**: lihat `samples/sid/S03__detil-data.json`
- **Status**: ✅ aktif (per 2026-10-26T07:35:19Z)
- **HTTP**: 200 · **Ukuran**: 6424 byte
- **Sumber ditemukan**: bundle `https://akses.ksei.co.id/main.9351f7724eaebe22ca45.js`

---

### [S04] GET https://akses.ksei.co.id/service/demografi/master/place

- **Deskripsi**: Dukcapil region master: province + city codes used by every demografi filter
- **Parameter**: —
- **Response fields**: `place`
- **Contoh**: lihat `samples/sid/S04__place.json`
- **Status**: ✅ aktif (per 2026-10-26T07:35:19Z)
- **HTTP**: 200 · **Ukuran**: 75016 byte
- **Sumber ditemukan**: bundle `https://akses.ksei.co.id/main.9351f7724eaebe22ca45.js`

---

### [S05] GET https://akses.ksei.co.id/service/demografis/updated-at

- **Deskripsi**: Timestamp of the last demographics refresh
- **Parameter**: `lang`='id'
- **Response fields**: `updatedAt`
- **Contoh**: lihat `samples/sid/S05__updated-at.json`
- **Status**: ✅ aktif (per 2026-10-26T07:35:19Z)
- **HTTP**: 200 · **Ukuran**: 74 byte
- **Sumber ditemukan**: bundle `https://akses.ksei.co.id/main.9351f7724eaebe22ca45.js`

---

### [S06] GET https://akses.ksei.co.id/service/aksi-korporasi/news/landing/periode/current-year

- **Deskripsi**: Current corporate-action year marker
- **Parameter**: —
- **Response fields**: —
- **Contoh**: lihat `samples/sid/S06__current-year.json`
- **Status**: ✅ aktif (per 2026-10-26T07:35:19Z)
- **HTTP**: 200 · **Ukuran**: 10 byte
- **Sumber ditemukan**: bundle `https://akses.ksei.co.id/main.9351f7724eaebe22ca45.js`

---

### [S07] POST https://akses.ksei.co.id/service/demografis/occupation

- **Deskripsi**: Investor occupation breakdown, filterable by city/province
- **Parameter**: `city`=&`province`=
- **Response fields**: —
- **Contoh**: tidak ada (endpoint tidak mengembalikan data)
- **Status**: http-500 (per 2026-10-26T07:35:19Z)
- **HTTP**: 500 · **Ukuran**: 897 byte
- **Sumber ditemukan**: bundle `https://akses.ksei.co.id/main.9351f7724eaebe22ca45.js`

---

### [S08] GET https://akses.ksei.co.id/service/demografi/age

- **Deskripsi**: Investor age-band breakdown, filterable by city/province
- **Parameter**: `city`=&`province`=
- **Response fields**: —
- **Contoh**: tidak ada (endpoint tidak mengembalikan data)
- **Status**: http-500 (per 2026-10-26T07:35:19Z)
- **HTTP**: 500 · **Ukuran**: 134 byte
- **Sumber ditemukan**: bundle `https://akses.ksei.co.id/main.9351f7724eaebe22ca45.js`

---

### [S09] GET https://akses.ksei.co.id/service/demografi/investor

- **Deskripsi**: Investor type breakdown (individual/corporate/...)
- **Parameter**: `city`=&`province`=
- **Response fields**: —
- **Contoh**: tidak ada (endpoint tidak mengembalikan data)
- **Status**: http-500 (per 2026-10-26T07:35:19Z)
- **HTTP**: 500 · **Ukuran**: 139 byte
- **Sumber ditemukan**: bundle `https://akses.ksei.co.id/main.9351f7724eaebe22ca45.js`

---

### [A01] GET https://akses.ksei.co.id/service/orchid/

- **Deskripsi**: Investor portfolio/sub-account service (login required) (93 routes in bundle)
- **Parameter**: —
- **Response fields**: —
- **Contoh**: tidak ada (endpoint tidak mengembalikan data)
- **Status**: 🔒 perlu login (per 2026-10-26T07:35:19Z)
- **Sumber ditemukan**: bundle `main.<hash>.js`, hanya terlihat sebagai rute SPA

---

### [A02] GET https://akses.ksei.co.id/service/myportofolio/

- **Deskripsi**: Investor portfolio views (login required) (48 routes in bundle)
- **Parameter**: —
- **Response fields**: —
- **Contoh**: tidak ada (endpoint tidak mengembalikan data)
- **Status**: 🔒 perlu login (per 2026-10-26T07:35:19Z)
- **Sumber ditemukan**: bundle `main.<hash>.js`, hanya terlihat sebagai rute SPA

---

### [A03] GET https://akses.ksei.co.id/service/myaccount/

- **Deskripsi**: Investor account settings (login required) (25 routes in bundle)
- **Parameter**: —
- **Response fields**: —
- **Contoh**: tidak ada (endpoint tidak mengembalikan data)
- **Status**: 🔒 perlu login (per 2026-10-26T07:35:19Z)
- **Sumber ditemukan**: bundle `main.<hash>.js`, hanya terlihat sebagai rute SPA

---

### [A04] GET https://akses.ksei.co.id/service/emiten-area/

- **Deskripsi**: Issuer-area reporting (issuer login required) (16 routes in bundle)
- **Parameter**: —
- **Response fields**: —
- **Contoh**: tidak ada (endpoint tidak mengembalikan data)
- **Status**: 🔒 perlu login (per 2026-10-26T07:35:19Z)
- **Sumber ditemukan**: bundle `main.<hash>.js`, hanya terlihat sebagai rute SPA

---

### [A05] GET https://akses.ksei.co.id/service/admin-mgt/

- **Deskripsi**: Back-office administration (staff login required) (11 routes in bundle)
- **Parameter**: —
- **Response fields**: —
- **Contoh**: tidak ada (endpoint tidak mengembalikan data)
- **Status**: 🔒 perlu login (per 2026-10-26T07:35:19Z)
- **Sumber ditemukan**: bundle `main.<hash>.js`, hanya terlihat sebagai rute SPA

---
