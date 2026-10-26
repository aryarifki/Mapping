# KSEI — endpoint JSON publik (`www.ksei.co.id`)

### [K01] GET https://www.ksei.co.id/api/settings

- **Deskripsi**: Site-wide settings key/value bundle
- **Parameter**: `locale`='id'
- **Response fields**: `rn`, `id`, `key`, `value`, `type`, `deleted_at`, `created_at`, `updated_at`
- **Contoh**: lihat `samples/ksei/K01__site-meta-settings.json`
- **Status**: ✅ aktif (per 2026-10-26T07:54:39Z)
- **HTTP**: 200 · **Ukuran**: 3840 byte
- **Sumber ditemukan**: bundle `/_nuxt/*.js` halaman https://www.ksei.co.id/id

---

### [K02] GET https://www.ksei.co.id/api/menus

- **Deskripsi**: Full CMS navigation tree
- **Parameter**: `locale`='id'
- **Response fields**: `rn`, `id`, `order`, `level`, `parent_id`, `type`, `is_published`, `published_at`, `created_at`, `updated_at`, `deleted_at`, `title`, `url_menu`, `url_content`
- **Contoh**: lihat `samples/ksei/K02__site-meta-menus.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 13764 byte
- **Sumber ditemukan**: bundle `/_nuxt/*.js` halaman https://www.ksei.co.id/id

---

### [K03] GET https://www.ksei.co.id/api/banners

- **Deskripsi**: Homepage banner carousel
- **Parameter**: `locale`='id'
- **Response fields**: `rn`, `updated_at`, `order`, `published_at`, `id`, `deleted_at`, `is_published`, `created_at`, `name`
- **Contoh**: lihat `samples/ksei/K03__site-meta-banners.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 1191 byte
- **Sumber ditemukan**: bundle `/_nuxt/*.js` halaman https://www.ksei.co.id/id

---

### [K04] GET https://www.ksei.co.id/api/seo_metas

- **Deskripsi**: Per-page SEO metadata
- **Parameter**: `locale`='id'
- **Response fields**: `rn`, `id`, `attachable_type`, `locale`, `seo_url`, `seo_title`, `seo_description`, `seo_content`, `open_graph_type`, `deleted_at`, `created_at`, `updated_at`, `attachable_id`
- **Contoh**: lihat `samples/ksei/K04__site-meta-seo-metas.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 458 byte
- **Sumber ditemukan**: bundle `/_nuxt/*.js` halaman https://www.ksei.co.id/id

---

### [K05] GET https://www.ksei.co.id/api/board_types

- **Deskripsi**: IDX board classification (Utama/Pengembangan/Ekonomi Baru)
- **Parameter**: `locale`='id'
- **Response fields**: `rn`, `published_at`, `is_published`, `created_at`, `updated_at`, `id`, `order`, `deleted_at`, `show_year`, `name`
- **Contoh**: lihat `samples/ksei/K05__reference-board-types.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 831 byte
- **Sumber ditemukan**: bundle `/_nuxt/*.js` halaman https://www.ksei.co.id/id

---

### [K06] GET https://www.ksei.co.id/api/investor_demographic/sid_growths/types

- **Deskripsi**: Enumerates the four SID investor-count series
- **Parameter**: `locale`='id'
- **Response fields**: `key`, `name`
- **Contoh**: lihat `samples/ksei/K06__investor-sid-types.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 376 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik

---

### [K07] GET https://www.ksei.co.id/api/investor_demographic/sid_growths

- **Deskripsi**: SID investor-count growth, 3-year window for one series
- **Parameter**: `locale`='en'&`filter[type]`='Number of Capital Market Investors'&`filter[three_years_data]`='October 2026'
- **Response fields**: `rn`, `month`, `asset_local`, `type`
- **Contoh**: lihat `samples/ksei/K07__investor-sid-sid-growths.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 471 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik

---

### [K08] GET https://www.ksei.co.id/api/investor_demographic/domestic_investors

- **Deskripsi**: Domestic vs foreign investor composition
- **Parameter**: `locale`='id'
- **Response fields**: `rn`, `asset_total`, `created_at`, `updated_at`, `investor_percentage`, `asset_percentage`, `month`, `id`, `deleted_at`, `area`
- **Contoh**: lihat `samples/ksei/K08__investor-sid-domestic-investors.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 7970 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik

---

### [K09] GET https://www.ksei.co.id/api/investor_demographic/individual/age

- **Deskripsi**: Individual investor count by age band
- **Parameter**: `locale`='id'
- **Response fields**: `rn`, `created_at`, `updated_at`, `month`, `order`, `age_range_qty`, `total_asset`, `published_at`, `id`, `deleted_at`, `is_published`, `age_range_id`, `age_range_count`, `name`
- **Contoh**: lihat `samples/ksei/K09__investor-sid-age.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 11609 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik

---

### [K10] GET https://www.ksei.co.id/api/investor_demographic/individual/education

- **Deskripsi**: Individual investor count by education level
- **Parameter**: `locale`='id'
- **Response fields**: `rn`, `created_at`, `updated_at`, `month`, `order`, `education_category_count`, `total_asset`, `published_at`, `id`, `deleted_at`, `is_published`, `education_category_id`, `name`
- **Contoh**: lihat `samples/ksei/K10__investor-sid-education.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 11134 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik

---

### [K11] GET https://www.ksei.co.id/api/investor_demographic/individual/gender

- **Deskripsi**: Individual investor count by gender
- **Parameter**: `locale`='id'
- **Response fields**: `rn`, `month`, `created_at`, `updated_at`, `published_at`, `id`, `deleted_at`, `is_published`, `man_count`, `man_total_asset`, `woman_count`, `woman_total_asset`
- **Contoh**: lihat `samples/ksei/K11__investor-sid-gender.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 2340 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik

---

### [K12] GET https://www.ksei.co.id/api/investor_demographic/individual/income

- **Deskripsi**: Individual investor count by income band
- **Parameter**: `locale`='id'
- **Response fields**: `rn`, `created_at`, `updated_at`, `month`, `order`, `income_range_qty`, `total_asset`, `published_at`, `id`, `deleted_at`, `is_published`, `income_range_id`, `income_range_count`, `name`
- **Contoh**: lihat `samples/ksei/K12__investor-sid-income.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 11112 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik

---

### [K13] GET https://www.ksei.co.id/api/investor_demographic/individual/job_demographics

- **Deskripsi**: Individual investor count by occupation
- **Parameter**: `locale`='id'
- **Response fields**: `rn`, `month`, `order`, `occupation_qty`, `total_asset`, `created_at`, `updated_at`, `published_at`, `id`, `deleted_at`, `is_published`, `occupation_id`, `job_category_count`, `name`
- **Contoh**: lihat `samples/ksei/K13__investor-sid-job-demographics.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 11852 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik

---

### [K14] GET https://www.ksei.co.id/api/investor_demographic/mutual_assets

- **Deskripsi**: Mutual fund product count and AUM, 4-year window
- **Parameter**: `locale`='en'&`filter[four_years_data]`='October 2026'
- **Response fields**: `rn`, `month`, `investation_product_count`, `managed_asset`
- **Contoh**: lihat `samples/ksei/K14__investor-sid-mutual-assets.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 411 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik

---

### [K15] GET https://www.ksei.co.id/api/securities_ownerships

- **Deskripsi**: Securities ownership breakdown (local vs foreign)
- **Parameter**: `locale`='id'
- **Response fields**: `date`, `name`, `pdf_id`
- **Contoh**: lihat `samples/ksei/K15__ownership-securities-ownerships.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 7296 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/kepemilikan-efek

---

### [K16] GET https://www.ksei.co.id/api/static_stocks

- **Deskripsi**: Monthly static securities master files (zip download links)
- **Parameter**: `locale`='id'
- **Response fields**: `date`, `name`, `pdf_id`
- **Contoh**: lihat `samples/ksei/K16__bulk-download-static-stocks.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 7240 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/statik-efek

---

### [K17] GET https://www.ksei.co.id/api/sro

- **Deskripsi**: SRO / self-regulatory organisation reference data
- **Parameter**: `locale`='id'
- **Response fields**: `rn`, `name`, `type`, `link`, `order`, `created_at`, `updated_at`, `id`, `deleted_at`, `is_published`, `published_at`, `type_id`
- **Contoh**: lihat `samples/ksei/K17__reference-sro.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 4089 byte
- **Sumber ditemukan**: bundle `/_nuxt/*.js` halaman https://www.ksei.co.id/id

---

### [K18] GET https://www.ksei.co.id/api/account_managements

- **Deskripsi**: Sub-account administration statistics
- **Parameter**: `locale`='id'
- **Response fields**: `rn`, `created_at`, `updated_at`, `order`, `id`, `category`, `deleted_at`, `published_at`, `is_published`, `category_id`, `document_name`
- **Contoh**: lihat `samples/ksei/K18__account-account-managements.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 4324 byte
- **Sumber ditemukan**: bundle `/_nuxt/*.js` halaman https://www.ksei.co.id/id

---

### [K19] GET https://www.ksei.co.id/api/account_managements/categories

- **Deskripsi**: Categories used by account_managements
- **Parameter**: `locale`='id'
- **Response fields**: `key`, `name`
- **Contoh**: lihat `samples/ksei/K19__reference-categories.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 215 byte
- **Sumber ditemukan**: bundle `/_nuxt/*.js` halaman https://www.ksei.co.id/id

---

### [K20] GET https://www.ksei.co.id/api/graph/aktiva_graphs/assets

- **Deskripsi**: Custody assets: total/foreign/local (IDR tn)
- **Parameter**: `locale`='id'&`sort`='month'
- **Response fields**: `category`, `month`, `foreign_asset`, `local_asset`, `total`
- **Contoh**: lihat `samples/ksei/K20__graph-assets.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 1808 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik

---

### [K21] GET https://www.ksei.co.id/api/graph/aktiva_graphs/bonds

- **Deskripsi**: Custody bonds series
- **Parameter**: `locale`='id'&`sort`='month'
- **Response fields**: `category`, `month`, `foreign_asset`, `local_asset`, `total`
- **Contoh**: lihat `samples/ksei/K21__graph-bonds.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 1786 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik

---

### [K22] GET https://www.ksei.co.id/api/graph/aktiva_graphs/shares

- **Deskripsi**: Custody shares series
- **Parameter**: `locale`='id'&`sort`='month'
- **Response fields**: `category`, `month`, `foreign_asset`, `local_asset`, `total`
- **Contoh**: lihat `samples/ksei/K22__graph-shares.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 1705 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik

---

### [K23] GET https://www.ksei.co.id/api/graph/aktiva_graphs/sub_account

- **Deskripsi**: Sub-account count series
- **Parameter**: `locale`='id'&`sort`='month'
- **Response fields**: `category`, `month`, `foreign_asset`, `local_asset`, `total`
- **Contoh**: lihat `samples/ksei/K23__graph-sub-account.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 1706 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik

---

### [K24] GET https://www.ksei.co.id/api/graph/cbest_graphs/customer

- **Deskripsi**: C-BEST participant customer composition
- **Parameter**: `locale`='id'
- **Response fields**: `id`, `participant`, `amount`, `percentage`, `category`
- **Contoh**: lihat `samples/ksei/K24__graph-customer.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 387 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik

---

### [K25] GET https://www.ksei.co.id/api/graph/cbest_graphs/instrument_information

- **Deskripsi**: C-BEST instrument mix
- **Parameter**: `locale`='id'
- **Response fields**: `id`, `instrument`, `amount`, `percentage`, `category`
- **Contoh**: lihat `samples/ksei/K25__graph-instrument-information.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 2874 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik

---

### [K26] GET https://www.ksei.co.id/api/graph/overbooking_graphs/value

- **Deskripsi**: Overbooking value, FOP vs VP
- **Parameter**: `locale`='id'&`sort`='month'
- **Response fields**: `category`, `month`, `fop`, `vp`, `total`
- **Contoh**: lihat `samples/ksei/K26__graph-value.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 20255 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik

---

### [K27] GET https://www.ksei.co.id/api/graph/overbooking_graphs/volume

- **Deskripsi**: Overbooking volume
- **Parameter**: `locale`='id'&`sort`='month'
- **Response fields**: `category`, `month`, `fop`, `vp`, `total`
- **Contoh**: lihat `samples/ksei/K27__graph-volume.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 20890 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik

---

### [K28] GET https://www.ksei.co.id/api/graph/overbooking_graphs/frequency

- **Deskripsi**: Overbooking frequency (DFOP/DVP)
- **Parameter**: `locale`='id'&`sort`='month'
- **Response fields**: `category`, `month`, `dfop`, `dvp`, `total`
- **Contoh**: lihat `samples/ksei/K28__graph-frequency.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 24804 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik

---

### [K29] GET https://www.ksei.co.id/api/graph/overbooking_graphs/cnf

- **Deskripsi**: CNF settlement series
- **Parameter**: `locale`='id'&`sort`='month'
- **Response fields**: `category`, `month`, `fop`, `vp`, `total`
- **Contoh**: lihat `samples/ksei/K29__graph-cnf.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 1355 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik

---

### [K30] GET https://www.ksei.co.id/api/graph/overbooking_graphs/sectrs

- **Deskripsi**: SECTRS series
- **Parameter**: `locale`='id'&`sort`='month'
- **Response fields**: `category`, `month`, `fop`, `vp`, `total`
- **Contoh**: lihat `samples/ksei/K30__graph-sectrs.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 1258 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik

---

### [K31] GET https://www.ksei.co.id/api/graph/overbooking_graphs/bts

- **Deskripsi**: BTS series
- **Parameter**: `locale`='id'&`sort`='month'
- **Response fields**: `category`, `month`, `fop`, `vp`, `total`
- **Contoh**: lihat `samples/ksei/K31__graph-bts.json`
- **Status**: ✅ aktif (per 2026-10-26T07:16:05Z)
- **HTTP**: 200 · **Ukuran**: 1280 byte
- **Sumber ditemukan**: https://www.ksei.co.id/id/publikasi/data-dan-statistik/grafik

---

### [K32] GET https://www.ksei.co.id/api/auth/user

- **Deskripsi**: Current session user (cookie auth.strategy=local)
- **Parameter**: —
- **Response fields**: —
- **Contoh**: tidak ada (endpoint tidak mengembalikan data)
- **Status**: 🔒 perlu login (per 2026-10-26T07:54:39Z)
- **Sumber ditemukan**: bundle `/_nuxt/*.js` halaman https://www.ksei.co.id/id

---

### [K33] POST https://www.ksei.co.id/api/auth/login

- **Deskripsi**: Login handler; requires credentials + session
- **Parameter**: —
- **Response fields**: —
- **Contoh**: tidak ada (endpoint tidak mengembalikan data)
- **Status**: 🔒 perlu login (per 2026-10-26T07:54:39Z)
- **Sumber ditemukan**: bundle `/_nuxt/*.js` halaman https://www.ksei.co.id/id

---

### [K34] POST https://www.ksei.co.id/api/auth/logout

- **Deskripsi**: Logout handler
- **Parameter**: —
- **Response fields**: —
- **Contoh**: tidak ada (endpoint tidak mengembalikan data)
- **Status**: 🔒 perlu login (per 2026-10-26T07:54:39Z)
- **Sumber ditemukan**: bundle `/_nuxt/*.js` halaman https://www.ksei.co.id/id

---
