# IDX — endpoint JSON publik (`www.idx.co.id`)

### [I01] GET https://www.idx.co.id/primary/StockData/GetSecuritiesStock

- **Deskripsi**: Full listed-securities master: code, name, listing date, shares, board
- **Parameter**: `start`='0'&`length`='9999'&`language`='id'
- **Response fields**: `Code`, `Name`, `ListingDate`, `Shares`, `ListingBoard`
- **Contoh**: lihat `samples/idx/I01__GetSecuritiesStock.json`
- **Status**: ✅ aktif (per 2026-10-26T07:51:42Z)
- **HTTP**: 200 · **Ukuran**: 130547 byte
- **Sumber ditemukan**: https://www.idx.co.id/id/market-data + probe `/primary/`

---

### [I02] GET https://www.idx.co.id/primary/ListedCompany/GetCompanyProfiles

- **Deskripsi**: Issuer profiles: address, sector, sub-sector, listing board, website
- **Parameter**: `start`='0'&`length`='9999'&`language`='id'
- **Response fields**: `Alamat`, `BAE`, `DataID`, `Divisi`, `EfekEmiten_EBA`, `EfekEmiten_ETF`, `EfekEmiten_Obligasi`, `EfekEmiten_Saham`, `EfekEmiten_SPEI`, `Industri`, `SubIndustri`, `Email`, `Fax`, `id`, `JenisEmiten`, `KegiatanUsahaUtama`
- **Contoh**: lihat `samples/idx/I02__GetCompanyProfiles.json`
- **Status**: ✅ aktif (per 2026-10-26T07:51:42Z)
- **HTTP**: 200 · **Ukuran**: 880639 byte
- **Sumber ditemukan**: https://www.idx.co.id/id/market-data + probe `/primary/`

---

### [I03] GET https://www.idx.co.id/primary/ListedCompany/GetCompanyProfilesDetail

- **Deskripsi**: Single-issuer detail: management, commissioners, shareholders, subsidiaries
- **Parameter**: `KodeEmiten`='BBCA'&`language`='id'
- **Response fields**: `ResultCount`, `Search`, `Profiles`, `Sekretaris`, `Direktur`, `Komisaris`, `KomiteAudit`, `PemegangSaham`, `AnakPerusahaan`, `KAP`, `Dividen`, `BondsAndSukuk`, `IssuedBond`
- **Contoh**: lihat `samples/idx/I03__GetCompanyProfilesDetail.json`
- **Status**: ✅ aktif (per 2026-10-26T07:51:42Z)
- **HTTP**: 200 · **Ukuran**: 27729 byte
- **Sumber ditemukan**: https://www.idx.co.id/id/market-data + probe `/primary/`

---

### [I04] GET https://www.idx.co.id/primary/TradingSummary/GetStockSummary

- **Deskripsi**: Daily trading summary per stock: open/high/low/close, volume, value, freq
- **Parameter**: `start`='0'&`length`='9999'&`language`='id'
- **Response fields**: `No`, `IDStockSummary`, `Date`, `StockCode`, `StockName`, `Remarks`, `Previous`, `OpenPrice`, `FirstTrade`, `High`, `Low`, `Close`, `Change`, `Volume`, `Value`, `Frequency`
- **Contoh**: lihat `samples/idx/I04__GetStockSummary.json`
- **Status**: ✅ aktif (per 2026-10-26T07:51:42Z)
- **HTTP**: 200 · **Ukuran**: 644097 byte
- **Sumber ditemukan**: https://www.idx.co.id/id/market-data + probe `/primary/`

---

### [I05] GET https://www.idx.co.id/primary/TradingSummary/GetIndexSummary

- **Deskripsi**: Index summary (IHSG and friends): previous/current, change, volume, value
- **Parameter**: `start`='0'&`length`='9999'&`language`='id'
- **Response fields**: `No`, `IndexSummaryID`, `Date`, `IndexCode`, `Previous`, `Highest`, `Lowest`, `Close`, `NumberOfStock`, `Change`, `Volume`, `Value`, `Frequency`, `MarketCapital`
- **Contoh**: lihat `samples/idx/I05__GetIndexSummary.json`
- **Status**: ✅ aktif (per 2026-10-26T07:51:42Z)
- **HTTP**: 200 · **Ukuran**: 13336 byte
- **Sumber ditemukan**: https://www.idx.co.id/id/market-data + probe `/primary/`

---

### [I06] GET https://www.idx.co.id/primary/TradingSummary/GetBrokerSummary

- **Deskripsi**: Broker summary: top buy/sell brokers per stock
- **Parameter**: `start`='0'&`length`='9999'&`language`='id'
- **Response fields**: `No`, `IDBrokerSummary`, `Date`, `IDFirm`, `FirmName`, `Volume`, `Value`, `Frequency`
- **Contoh**: lihat `samples/idx/I06__GetBrokerSummary.json`
- **Status**: ✅ aktif (per 2026-10-26T07:51:42Z)
- **HTTP**: 200 · **Ukuran**: 15751 byte
- **Sumber ditemukan**: https://www.idx.co.id/id/market-data + probe `/primary/`

---

### [I07] GET https://www.idx.co.id/primary/ListedCompany/GetAnnouncement

- **Deskripsi**: Issuer announcements / keterbukaan informasi feed (237k records; pagesize is the parameter that actually paginates -- length is ignored)
- **Parameter**: `start`='0'&`length`='5'&`pagesize`='5'&`language`='id'
- **Response fields**: `ResultCount`, `SearchParams`, `Replies`
- **Contoh**: lihat `samples/idx/I07__GetAnnouncement.json`
- **Status**: ✅ aktif (per 2026-10-26T07:53:33Z)
- **HTTP**: 200 · **Ukuran**: 7352 byte
- **Sumber ditemukan**: https://www.idx.co.id/id/market-data + probe `/primary/`

---
