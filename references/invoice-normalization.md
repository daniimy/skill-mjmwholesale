# Invoice JSON Normalization

The user's invoice JSON has a different shape from what the form expects. This file documents the mapping.

## Variant C: Indonesian-key Faktur Penjualan (combined pages in ONE object)

Saw 2026-08-05 batch. Supplier export with Indonesian keys; multi-page invoices often arrive as a SINGLE JSON object with all pages' items combined in one `items` array (page field says `"1 / 2 & 2 / 2"`):

```json
{
  "perusahaan": {"nama": "CV MJM BATTERY BAROKAH", "alamat": "...", "telepon": "...", "npwp": "...", "rekening": [...]},
  "faktur": {
    "judul": "FAKTUR PENJUALAN",
    "kepada": "HERU AKI NGAWI",
    "page": "1 / 2 & 2 / 2",
    "no_faktur": "143/HA-N/VIII/26",
    "tgl_faktur": "03 Agustus 2026",
    "tgl_jatuh_tempo": "-"
  },
  "items": [
    {"no": 1, "kode_barang": "INGO-NS40ZL", "nama_barang": "INCOE GOLD NS40ZL", "qty_pcs": 5, "berat_kg": 48.5, "harga": 558195, "total": 2790975}
  ],
  "total_halaman_1": 29559742,
  "total_halaman_2": 9000000,
  "total": 38559742,
  "tonase": 632.90,
  "catatan_halaman_2": {"rekening_alternatif": {"bank": "BCA KCU JOMBANG", "no_rek": "1132555235", "atas_nama": "MOCHAMMAD JEHAN MUJIYANTO"}},
  "tanda_tangan": {"pengirim": "", "penerima": ""}
}
```

**Normalization:**

| Source field | Target field | Notes |
|-------------|-------------|-------|
| `faktur.kepada` | `customer` | bare string |
| `faktur.no_faktur` | `invoice_number` | |
| `faktur.tgl_faktur` | `date` | Indonesian date "03 Agustus 2026" → parse with `parse_id_date()` (see SKILL.md §Date conversion helper) |
| `faktur.tgl_jatuh_tempo` | `due_date` | `"-"` or `null` → Lunas. Date string ("03 September 2026") → Tempo, parse to ISO. |
| `items[].kode_barang` | `product_code` | |
| `items[].nama_barang` | `product_name` | |
| `items[].qty_pcs` | `qty` | |
| `items[].harga` | `unit_price` | |
| `items[].total` | _(drop)_ | server computes price×qty |
| `total` | `summary.grand_total` | combined pages total |
| `total_halaman_1` / `total_halaman_2` | _(verify)_ | sanity: sum of per-page line totals; combined total should match |
| `catatan_halaman_2.rekening_alternatif` | _(drop)_ | BCA owner 1132555235 = payment routing info only. **Same merge rule as seller stamp — NOT a separate transaction.** |
| `tanda_tangan` | _(drop)_ | |
| `perusahaan` | _(metadata)_ | seller stamp — same merge rule applies |

**`page` = "1 / 2 & 2 / 2" means the items array already contains BOTH pages** — do NOT look for a second JSON object; there is none. Post as ONE sale. Any `rekening_alternatif` (owner's BCA) is just where page-2 payment goes.

**⚠️ `customer` (kepada) = null / missing → STOP & ask user.** Real case 2026-08-05: NOTA `046/VII/26` had `customer: null`, invoice number WITHOUT customer prefix (unusual — normally `NNN/PRE-CITY/VIII/26`). User supplied "ASIA JAYA" → id=62. Jangan tebak, jangan post tanpa customer.

**⚠️ `claim` field = warranty/replacement note, drop it.** 094/AA-Y had `"claim": {"description": "INGO NS60 : 1 PCS BD BILAL & ERVAN"}` — metadata, NOT an item. Same for free promo items (KAOS GLX price=0, not in admin → skip per free/promo rule).

## Variant A: Full supplier-invoice shape (from supplier system export)

```json
{
  "supplier": {"company_name", "address", "phone", "npwp", "bank_accounts": [...]},
  "customer": {"name": "..."},
  "invoice": {"page", "invoice_number", "invoice_date", "due_date": null},
  "items": [
    {
      "no", "product_code", "product_name",
      "qty", "weight_kg",
      "unit_price", "line_total",
      "cost_price", "omset": null
    }
  ],
  "summary": {"total_amount", "total_cost", "total_omset", "profit_percentage", "total_weight_kg"},
  "signatures": {"sender": null, "receiver": null}
}
```

`customer` may also be a bare string — accept both, prefer the object form.

**Normalization** — fields nest under `supplier`, `invoice`, `summary` objects. Extract:
- `customer` → `input.customer.name || input.customer`
- `invoice_number` → `input.invoice.invoice_number`
- `invoice_date` → `input.invoice.invoice_date || input.date`
- `due_date` → `input.invoice.due_date`
- `grand_total` → `input.summary.total_amount` or `input.summary.selling_total`
- `items[].product_code` → `input.items[].product_code`
- `items[].unit_price` → `input.items[].unit_price`

## Variant B: Root-level totals shape (from image OCR / manual entry)

```json
{
  "customer": "IMAM ACCU BLITAR",             // bare string, not object
  "invoice_number": "160/IA-B/VII/26",        // at root, not under "invoice"
  "invoice_date": "2026-07-13",
  "due_date": null,
  "company": "CV MJM BATTERY BAROKAH",
  "page": "1/2",
  "items": [
    {
      "code": "INGO-NS70",                    // "code" not "product_code"
      "name": "INCOE GOLD NS70",              // "name" not "product_name"
      "qty": 15,
      "unit": "pcs",
      "weight": 238.5,
      "price": 803518,                        // "price" not "unit_price"
      "total": 12052770                       // line_total at item level
    }
  ],
  "subtotal": 46485706,                        // root level, not under summary
  "cashbacks": [
    {"description": "Cashback GS Mobil (20 pcs)", "amount": 100000}
  ],
  "total": 46385706,                           // grand_total = subtotal - sum(cashbacks)
  "tonnage": 814.5
}
```

**Characteristics that distinguish this variant:**
- `customer` is a bare `string` at root (not `customer.name` or `customer.id`)
- `invoice_number`, `invoice_date`, `due_date` at root level (not under an `invoice` object)
- No `summary` object — totals at root: `subtotal`, `total` (= grand total after cashback)
- `cashbacks` array at root with `description` and `amount` per cashback
- Items use `code` (not `product_code`), `name` (not `product_name`), `price` (not `unit_price`)
- Items carry `total` (line_total), `unit`, `weight` — all ignorable metadata
- `company` at root identifies the seller stamp (for multi-page merge decisions)
- `page`, `tonnage` at root

**Normalization to internal shape:**

| Source field | Target field | Notes |
|-------------|-------------|-------|
| `customer` (string) | `customer.name` | Wrap in object for post_sale |
| `invoice_number` | `invoice_number` | Direct |
| `invoice_date` | `date` | `build_payload` reads `invoice.get("date")` |
| `due_date` | `due_date` | Direct |
| `total` | `summary.grand_total` | Already post-cashback |
| `items[].code` | `items[].product_code` | |
| `items[].name` | `items[].product_name` | |
| `items[].qty` | `items[].qty` | |
| `items[].price` | `items[].unit_price` | This is **before** cashback absorption |
| `items[].total` | _(drop)_ | Line total — server computes from price×qty |
| `items[].unit` | _(drop)_ | |
| `items[].weight` | _(drop)_ | |
| `cashbacks[]` | _(absorb into prices)_ | Each cashback reduces affected brand group prices. See `references/cashback-handling.md`. |
| `company` | _(metadata for merge)_ | Different seller stamps still merge if customer+invoice_number same |
| `subtotal` | _(verify)_ | Should equal `sum(items.price × items.qty)` before cashback |
| `tonnage` | _(drop)_ | |

**Cashback handling for this variant:**
- Cashback amount = `subtotal - total` (or sum of `cashbacks[].amount`). Dengan default `cashback_mode='expense'`, cashback otomatis dipost sebagai Biaya Marketing expense. Items tetap full price.
- Set `summary.grand_total = total` hanya sebagai metadata untuk `_extract_cashback()`.

## Internal shape (what the form needs)

```js
{
  branch: input.branch || "Kiriman Luar Kota",
  customer: input.customer?.name || input.customer,
  date: input.invoice?.invoice_date || input.date || today(),
  invoice_number: input.invoice?.invoice_number,        // → payments[0].notes
  due_date: input.invoice?.due_date || null,             // null → Lunas; non-null → Tempo
  items: input.items.map(i => ({
    product_code: i.product_code || i.code,
    product_name: i.product_name || i.name,
    qty: i.qty ?? i.quantity,
    unit_price: i.unit_price ?? i.price,                 // FINAL price override
  }))
}
```

## Drop silently (invoice metadata, not for the form)

- `supplier` — form has no supplier field
- `signatures` — form has no signature field
- `claim` — catatan klaim/barang diganti (misal `"claim": {"description": "INGO NS60 : 1 PCS BD BILAL & ERVAN"}`), metadata, not an item
- `weight_kg`, `cost_price`, `omset`, `line_total` — per-item metadata
- `summary.profit_percentage`, `summary.total_cost`, `summary.total_omset`, `summary.total_weight_kg` — derived stats

## TAGIHAN NOTA — wajib skip

Tagihan (pending bill dari sales sebelumnya) bisa muncul di 2 tempat berbeda dalam JSON:

### Variant A: TAGIHAN sebagai item di `items` array

Jika di `items` array ada entry dengan `product_code` atau `product_name` mengandung kata:
- "TAGIHAN"
- "ITAGIHAN"
- "PIUTANG"

→ **hapus entry tersebut dari array**. Sales udah terjadi di masa lalu, gak perlu diproses ulang.

⚠️ Setelah skip, **recalculate grand_total**: `sum(remaining items unit_price × qty)`. Jangan pakai grand_total asli dari JSON karena itu udah termasuk tagihan.

### Variant B: TAGIHAN di `notes` array (bukan items)

Beberapa invoice punya `notes` array terpisah dengan tagihan entry:

```json
{
  "items": [{"code": "GSHY-NS40ZL", "price": 709598, "total": 709598}],
  "notes": [
    {"description": "TAGIHAN NOTA", "reference": "M2-0626-01095", "amount": 1388934}
  ],
  "summary": {
    "subtotal": 709598,
    "grand_total": 2098532
  }
}
```

Di sini `items` sudah bersih (gak ada entry tagihan), tapi `grand_total` **masih include** tagihan amount (709.598 + 1.388.934 = 2.098.532).

**Cara handle:**
1. `items` array — jangan diubah (sudah bersih)
2. Deteksi: cek apakah ada field `notes` dengan entry ber-`description` mengandung "TAGIHAN" / "PIUTANG"
3. Kalau ada → **pakai `summary.subtotal` sebagai grand_total**, bukan `summary.grand_total`
4. Jangan post tagihan sebagai sale item — itu urusan masa lalu

⚠️ Jangan double-count: kalau tagihan ada di `notes`, jangan juga cek `items` — cukup satu sumber.

## Free/promo items (harga 0, tidak di admin)

Beberapa invoice menyertakan item promosi gratis (free kaos, free sample, dll) dengan `price: 0`. Item ini biasanya tidak ada di katalog admin (`allProducts`).

**Aturan:** Jika item dengan `unit_price === 0` dan kodenya **tidak ditemukan** di admin `allProducts` → **hapus dari array items**. Gak perlu post barang yang gak dijual.

**Pengecualian:** Jika item gratis tetap punya product_id valid di admin (misal diskon 100% dari barang regular), biarkan — nanti `unit_price=0` tetap terkirim. Cek dulu kodenya di by_code. Kalau ada → retain; kalau tidak ada → skip.

**Contoh validasi:**
```
KAOS: price=0, not in by_code → SKIP
INPR-N100: price=0, id=752 in by_code → RETAIN (diskon penuh barang regular)
```

## Sanity check
If both `summary.total_amount` and items are present:
```
sum(items.unit_price * items.qty) === summary.total_amount
```
Warn user on mismatch (likely a typo or rounding).

**Known mismatch source**: Items may show `harga` and `qty` whose product doesn't equal the stated `total` on that line. This is a supplier billing system artifact (rounding at display vs precision at calculation). When this happens, DON'T add a "Penyesuaian pembulatan" — use `summary.total_amount` as `payments[0].amount` and leave global_adjustments empty. The user prefers "harus apa adanya".

**Supplier invoice variants**: Some invoices use `summary.selling_total` instead of `total_amount`/`grand_total`. When `total_amount` is absent but `selling_total` is present, treat `selling_total` as the customer-facing grand total. When both exist, `selling_total` takes precedence (it reflects actual sale price after margin adjustments).

## Combine rule

When the user input contains multiple JSON objects with the same `invoice_number` AND the same `customer.name`, they are parts of one sale — **but only if their payment status matches**.

### Payment status check (wajib)

Before merging, check each page's `due_date`:

| Pattern | Action |
|---------|--------|
| ALL pages `due_date === null` (Lunas) | Merge items into **one Lunas sale**. `payment_status=Lunas`, `payments[0].amount=combined_grand_total`. |
| ALL pages `due_date !== null` (Tempo) | Merge items into **one Tempo sale**. `payment_status=Tempo`, `due_date` = earliest due_date among pages. `payments[0].amount=0`. |
| **MIXED** (some Lunas, some Tempo) | **DO NOT merge.** Process each page as a separate sale with its own payment status. Dua sale terpisah — satu Lunas, satu Tempo — meskipun nomor invoice dan customer sama. |

**Why:** Admin panel `sale_save.php` hanya punya satu `payment_status` per sale. Gabisa campur Lunas + Tempo dalam satu transaksi. Kalau dipaksa, payment amount salah dan hutang tercacat tidak akurat.

**Exception — owner's personal name**: Multi-page invoices sometimes have page 2 with customer = the company owner's personal name (e.g. "MOCHAMMAD JEHAN MUJIYANTO") and a different bank account (owner's personal BCA 1132555235). **This is NOT a separate customer.** The owner's personal name on page 2 means those items are part of the SAME business sale as page 1 — the owner's personal bank account is used for that portion. Always merge back to page 1's business customer. 

How to detect: if the customer name on a page matches the bank account holder name on that page's bank info, AND it doesn't match the main customer from page 1, it's the owner. Merge items into page 1's customer, don't create a separate sale.

**⚠️ Owner-name exception + payment status conflict:** If the owner's personal-name page has a different payment status than page 1's business customer — rare but possible — prioritize the owner-name merge. Payment status mengikuti majority atau user decide.

### Different seller stamp — same merge rule

Kadang multi-page invoice punya **seller berbeda** antar halaman (misal "CV MJM BATTERY BAROKAH" di page 1-2 vs "MJM BATTERY" di page 3), dengan bank account berbeda (BCA perusahaan vs BCA owner pribadi). 

**Ini TETAP merge selama customer.name sama.** Seller stamp yang beda itu cuma variasi cetak faktur, bukan transaksi terpisah. Yang penting: customer name dan invoice number sama.

**Confirmed by owner 2026-08-05:** seller `MJM BATTERY` dan `CV MJM BATTERY BAROKAH` adalah SATU sistem/entitas yang sama. Bedanya cuma bank tujuan: CV → BCA 1132446525 (perusahaan), MJM BATTERY → BCA 1132555235 (owner pribadi Mas Jehan). Bank beda itu cuma info pembayaran, gak ngaruh ke struktur sale. Perlakukan keduanya identik saat merge.

Pengecualian: kalau **customer.name** berubah jadi nama pemilik bank (owner-name exception di atas) → baru dipisah/merge khusus.

### Multi-part merge — 3+ bagian (p1 + p1-continued + p2)

Invoice besar bisa pecah jadi JSON lebih dari 2 bagian: `{...p1 items...}` + `{"page_1_continued": {...}}` + `{"page_2": {...}}`. Semua bagian dengan invoice_number + customer sama → merge jadi SATU sale.

**Hazard: stated `grand_total` di bagian `page_1_continued` SERING BELUM termasuk halaman berikutnya.** Contoh nyata 094/AA-Y/VII/26 (2026-08-05, sale 22422): stated grand 265,813,634 cuma p1+continued, padahal masih ada page_2 senilai 2,82jt. Kalau dipakai verbatim → sale 2,82jt lebih kecil dari fisik.

**Fix:** jangan percaya stated grand_total pada multi-part. Hitung ulang `sum(price × qty)` dari SEMUA item gabungan, pakai itu sebagai payment/subtotal. Verify pakai skrip merge (jangan transkrip manual 39 item).

**`claim` field** = metadata (catatan klaim/BD, misal `"claim": {"description": "INGO NS60 : 1 PCS BD BILAL & ERVAN"}`) → DROP, bukan item yang dipost. Sama seperti `signatures`.

**Big-volume pricing:** customer langganan besar (AMRI ACCU YOGYAKARTA = harga termurah) sering jual jauh di bawah admin wholesale (INGO NS60 @577,850 vs ws 627,278; GLX-GTZ-5S @98,000 vs 110,000). Ini legit — jangan flag sebagai salah mapping.

## Payment mapping
- `due_date === null` → `payment_status = Lunas`, no `due_date` field set.
- `due_date !== null` → `payment_status = Tempo`, fill `due_date`.
- `payment_method` default `Transfer` for invoice-style input (override if user says otherwise).
- `payments[0].amount` = `summary.total_amount` (or computed sum) when `Lunas`, else `0`.
- `payments[0].notes` = `"Invoice " + invoice_number`. Empty if no invoice number.

## Product lookup
For each item, try in order:
1. `product_code` exact match against `allProducts[i].code` (most reliable).
2. Substring match against `allProducts[i].code` + `label` + `name_only` (multi-keyword AND).

If no match → STOP and tell the user which codes failed. Don't guess.

## Worked example
Input (from a real user invoice):

```json
{
  "customer": {"name": "HS AKI SIDOARJO"},
  "invoice": {"invoice_number": "241/HS-S/VI/26", "invoice_date": "2026-06-21", "due_date": null},
  "items": [
    {"product_code": "GSMFN-NS40ZL", "qty": 2, "unit_price": 797475},
    {"product_code": "INPR-NX120-7L", "qty": 1, "unit_price": 1130823},
    {"product_code": "INGO-N70Z", "qty": 1, "unit_price": 1013947},
    {"product_code": "INPR-N50Z", "qty": 1, "unit_price": 763911},
    {"product_code": "GSHY-NS60", "qty": 1, "unit_price": 770515}
  ],
  "summary": {"total_amount": 5274146}
}
```

Normalized for the form:
- `branch` = `"Kiriman Luar Kota"` (omitted in input)
- `customer` = `"HS AKI SIDOARJO"`
- `date` = `"2026-06-21"`
- `due_date` = `null` → Lunas
- `invoice_number` = `"241/HS-S/VI/26"`
- 5 items with `priceMode=custom` and `final = unit_price`
- `payments[0]` = `{"method":"Transfer","amount":5274146,"notes":"Invoice 241/HS-S/VI/26"}`

Sanity: 797475×2 + 1130823 + 1013947 + 763911 + 770515 = 5,274,146 ✓
