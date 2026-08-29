---
name: mjm-battery-wholesale-sale
# Pi adaptation: copied from Hermes; scripts retain shared ~/.hermes/state compatibility.
description: Create wholesale (custom-grosir) sales transactions on mjmbattery.com admin panel. Use when user provides a JSON invoice or an image of an invoice/receipt and wants it posted to /admin/sale_custom_wholesale.php. Default branch `Kiriman Luar Kota`. ZERO browser needed — all via curl.
---

# MJM Wholesale Sale (Custom Grosir) — Browserless

Create a sales transaction at `https://mjmbattery.com/admin/sale_custom_wholesale.php` from either an invoice-shaped JSON or an image of an invoice/receipt.

**Default branch: `Kiriman Luar Kota`**.

**Zero browser needed.** All steps use direct HTTP via `scripts/post_sale.py` — no byob, no browser click.

## References (load on demand)

- [`verified-page-state.md`](references/verified-page-state.md) — Form field reference, AJAX endpoints.
- [`invoice-normalization.md`](references/invoice-normalization.md) — How to convert the user's invoice JSON into the form's expected shape.
- [`operational-notes.md`](references/operational-notes.md) — Idempotency state file path, skill revision workflow.
- [`references/invoice-json-schema.md`](references/invoice-json-schema.md) — invoice JSON shape spec.
- [`references/pitfalls.md`](references/pitfalls.md) — production gotchas.
- [`references/verified-runs.md`](references/verified-runs.md) — every successful production POST with sale_ids.
- [`references/product-code-map.md`](references/product-code-map.md) — supplier invoice codes → admin codes mapping.
- [`references/extraction-prompt.md`](references/extraction-prompt.md) — Prompt template to copy-paste when user sends invoice image.
- [`references/cashback-handling.md`](references/cashback-handling.md) — Two approaches: absorbed into item prices (legacy), or posted as separate Biaya Marketing expense (new).
- [`references/cashback-distribution-algorithm.md`](references/cashback-distribution-algorithm.md) — Algorithm for distributing cashback proportionally with rounding fix.
- [`references/direct-post-recipe.md`](references/direct-post-recipe.md) — full annotated curl recipe.
- [`references/expense-endpoint.md`](references/expense-endpoint.md) — Expense POST endpoint for recording cashback as Biaya Marketing (category_id=13).
- [`references/report-barang-keluar.md`](references/report-barang-keluar.md) — How to verify Kiriman Luar Kota sales in the Barang Keluar report (`branch=Kiriman+Luar+Kota` parameter).

## Scripts (invoke, don't re-type)

- `scripts/post_sale.py` — main workhorse. Has CLI: `login`, `search`, `post` subcommands. Key Python API: `login()`, `search_customers()`, `get_page_data()`, `resolve_customer()`, `resolve_products()`, `filter_tagihan_items()`, `post_sale()`, `build_payload()`, `post_expense()` (record cashback as Biaya Marketing expense).
- `scripts/code_map.json` — canonical code map (supplier → admin codes). Pass with `--code-map scripts/code_map.json` in CLI, or load in Python.
- `scripts/idempotency_check.py` — pre-POST duplicate guard.

## Templates

- `templates/sale_save_post.sh` — bash+python hybrid, alternative entry point.

## When to use

- User provides a JSON invoice or image of an invoice.
- User says "post this sale", "buat nota grosir", "enter the wholesale order".
- Do NOT use for: editing product catalog (use sibling skill `mjm-battery-bulk-edit`).

## Credentials

`post_sale.py` resolves credentials in priority order (first hit wins):

1. **Env vars** — `MJM_USERNAME` / `MJM_PASSWORD` / `MJM_BASE_URL` (also auto-loaded from `.env` in repo root if present)
2. **State file** — `~/.hermes/state/mjm_credentials.json` (Hermes compat, still supported)
3. **CLI args** — `post_sale.py login --username X --password Y`

**Setup — pilih salah satu (tinggal edit di Notepad):**

```bash
# Opsi A — .env (recommended)
cp .env.example .env
# buka .env di Notepad, isi MJM_USERNAME & MJM_PASSWORD

# Opsi B — env vars
export MJM_USERNAME="your_user"
export MJM_PASSWORD="your_pass"
export MJM_BASE_URL="https://mjmbattery.com"  # optional

# Opsi C — state file (Hermes compat)
mkdir -p ~/.hermes/state
cat > ~/.hermes/state/mjm_credentials.json <<'JSON'
{
  "username": "YOUR_USERNAME",
  "password": "YOUR_PASSWORD",
  "base_url": "https://mjmbattery.com"
}
JSON
```

Copy `.env.example` → `.env` and fill in your values. `.env` is git-ignored.

## Workflow

### Step 0 — Load skill references

Load relevant references:
- `references/invoice-normalization.md` — if parsing a new JSON shape
- `references/product-code-map.md` — if codes mismatch
- `references/cashback-handling.md` — if cashback/diskon present (see §Expense approach for new workflow)
- `references/expense-endpoint.md` — if using expense-based cashback approach
- `references/pitfalls.md` — always worth a quick scan

### Step 1 — Idempotency check (mandatory)

**The mjmbattery server has no real-time pre-POST duplicate guard.** Always check the local state file **before** any other work:

```python
import sys
sys.path.insert(0, str(__import__("pathlib").Path.home() / ".pi/agent/skills/mjm-battery-wholesale-sale/scripts"))
from idempotency_check import check
dup = check(invoice.invoice_number)
if dup:
    print(f"⚠️ DUPLICATE: {invoice.invoice_number} already processed")
    print(f"   server_invoice={dup['server_invoice']}  sale_id={dup['sale_id']}  at={dup['processed_at']}")
    print(f"   verify at https://mjmbattery.com/admin/sales.php?search={dup['server_invoice']}")
    # skip POST; continue to next invoice in batch
```

Or CLI: `python3 scripts/idempotency_check.py check 063/PS-T/VI/26` — exit 0 means new, exit 1 means duplicate.

**⚠️ Compound key when same invoice has different customers**: Multi-page invoices may have the same invoice_number with different customer names. Key by `f"{invoice_number}|{customer_name}"` instead of bare invoice_number, or pass a compound key to `check()`:

```python
compound_key = f"{inv['nomor']}|{inv['customer']}"
dup = check(compound_key)
```

If the same invoice_number appears in multiple JSON parts with the same customer (combine rule), check only once before posting.

### Step 2 — Parse the input

Load `references/invoice-normalization.md` for field-mapping rules. Normalize to internal shape:

```js
{
  branch: input.branch || "Kiriman Luar Kota",
  customer: input.customer?.name || input.customer,
  date: input.invoice?.invoice_date || input.date || today(),
  invoice_number: input.invoice?.invoice_number,
  due_date: input.invoice?.due_date || null,
  items: input.items.map(i => ({product_code, product_name, qty, unit_price, ...}))
}
```

- Drop silently: `supplier`, `signatures`, `weight_kg`, `cost_price`, `omset`, `line_total`, `summary.*` (except `total_amount`).
- **TAGIHAN NOTA — skip:** setiap item di `items` yang `product_code` atau `product_name` mengandung kata "TAGIHAN", "ITAGIHAN", atau "PIUTANG" → hapus dari array. Sales udah terjadi, tagihan/pending bill gak perlu diproses. Gunakan `from post_sale import filter_tagihan_items` di Python untuk mechanical filter, atau filter manual pas parsing.
- **TAGIHAN NOTA di `notes` array:** kalau tagihan ada di `notes[]` (bukan items), `grand_total` sudah termasuk tagihan. Pakai `summary.subtotal` sebagai grand_total, bukan `summary.grand_total`. Lihat `references/invoice-normalization.md` §Variant B.
- **Free/promo items (harga 0):** cek apakah kode produk ada di admin `allProducts`. Kalau tidak ada → skip item. Kalau ada (diskon penuh barang regular) → retain. Lihat `references/invoice-normalization.md` §Free/promo items.
- Sanity-check: `sum(items.unit_price * items.qty)` should equal `summary.total_amount` if both present.
- For **image input**: Pi must use an available image/OCR tool; ALWAYS show the extracted JSON before proceeding. If no vision tool is available, ask the user for JSON.
- If `branch` or `customer` missing — STOP and ask.

**Combine same-invoice-number rule**: Multiple JSON objects sharing the same `invoice_no` AND same customer → check payment status first. **ALL Lunas** or **ALL Tempo** → combine into one POST. **MIXED** → separate sales (jangan digabung). Merge all items (keep full prices). Cashback total di-sum otomatis oleh `_extract_cashback()` → expense (default) atau absorb (legacy). Lihat `references/cashback-handling.md`. Jangan pakai `global_adjustments` untuk cashback.

**⚠️ Owner-name exception**: If a page has customer = company owner's personal name (e.g. "MOCHAMMAD JEHAN MUJIYANTO") matching the bank account holder, it's NOT a separate customer — merge items back to page 1's business customer. See `references/invoice-normalization.md` §Combine rule for details.

**⚠️ Different seller stamp**: Kadang seller berbeda antar halaman ("CV MJM BATTERY BAROKAH" vs "MJM BATTERY") dengan bank beda. **Ini tetap merge selama customer.name sama.** Seller stamp bukan penentu — customer.name dan invoice_number yang menentukan. See `references/invoice-normalization.md` §Different seller stamp.

**⚠️ Due date konflik dengan user**: Kalau user bilang 'ini harusnya Tempo/Lunas' tapi JSON bilang kebalikan — **jangan langsung re-post**. Konfirmasi ke user dulu: 'Faktur fisiknya ada tgl jatuh tempo atau --- (strip)?'. Kalau sudah pasti baru action. Jangan buru-buru merge pages yang beda status. See `references/pitfalls.md` §Due date in JSON can conflict.

**⚠️ Due date extraction artifact multi-page**: Kadang page 1 dari invoice multi-page punya due_date (Tempo) tapi page 2 punya due_date: null (Lunas) --- ini extraction artifact, bukan beneran mixed status. Page continuation sering kehilangan due_date karena JSON extractor cuma baca halaman pertama. **Jangan pisah jadi 2 sales.** Merge sebagai Tempo dengan due_date dari halaman yang punya. Kecuali nama customer juga berubah -> baru separate sales.

**⚠️ Multi-part shape (`page_1_continued` / incremental parts)**: An invoice may arrive as >2 JSON parts, e.g. `{main: page 1 items, page_1_continued: {items, summary}, page_2: {items}}` — all same invoice_no + customer. Merge ALL parts into one sale. CRITICAL: the `grand_total` on an early part often ONLY covers the parts seen so far (excludes later pages). E.g. 094/AA-Y stated 265,813,634 covered p1+continued but NOT page 2's 2.82jt. **Never trust a partial part's grand_total as the sale amount — always post `sum(price×qty)` across ALL merged items.** A `claim`/`note` field (e.g. "INGO NS60: 1 PCS BD BILAL & ERVAN") is metadata, drop it — not an item.

**DATE CHECK — wajib (jangan pernah skip):**
1. Parse `invoice_date` dari JSON. Format input: "29 Juni 2026" (Indonesia). Convert ke ISO `2026-06-29`. **Jangan pernah kirim "29 Juni 2026" langsung ke form — form pake input type=date, butuh YYYY-MM-DD.**
2. Ambil hari ini dengan `datetime.date.today()`.
3. Kalau `invoice_date` === null / kosong → STOP & tanya user tanggalnya.
4. Kalau `invoice_date > hari ini` → STOP & tanya user konfirmasi (faktur masa depan?).
5. Kalau `invoice_date < hari_ini - 30hari` → STOP & tanya user (faktur terlalu lama?).
6. Kalau wajar → inject `invoice_date` ke format ISO. **Cuma notifikasi, jangan ganti tanggal.**

⚠️ **Ini sering kelewatan. Jangan skip step ini.**

### Date conversion helper

```python
from datetime import datetime, date
BULAN_ID = {"januari":1,"februari":2,"maret":3,"april":4,"mei":5,"juni":6,
            "juli":7,"agustus":8,"september":9,"oktober":10,"november":11,"desember":12}

def parse_id_date(s):
    if not s: return None
    parts = s.strip().split()
    if len(parts) != 3: return None
    d, m, y = int(parts[0]), BULAN_ID.get(parts[1].lower()), int(parts[2])
    if not m: return None
    return date(y, m, d)
```

### Step 3 — Login + get session

**CSRF is mandatory.** The login endpoint rejects a direct username/password POST without the fresh hidden token from `/admin/login.php`:
`CSRF token tidak valid. Refresh halaman dan coba lagi.`

`login()` must:
1. GET `/admin/login.php` with a cookie jar.
2. Extract `<input name="csrf_token" value="...">`.
3. POST username, password, and `csrf_token` to `/admin/login_process.php`, preserving the cookie jar.
4. Accept the expected `302` redirect to `index.php`; capture the resulting `PHPSESSID`.
5. Propagate that PHPSESSID to every later request. Verify `sale_custom_wholesale.php` is authenticated before product resolution: HTTP 200 alone is insufficient; reject responses containing the login form, and require a non-empty `allProducts` catalogue. See `references/session-login-debugging.md`.

Use `post_sale.py` CLI or Python API after this flow is implemented:

```bash
python3 scripts/post_sale.py login
# → outputs PHPSESSID string
```

Or in Python:
```python
from post_sale import login
phpsessid = login()
```

Credentials: env vars (`MJM_USERNAME`/`MJM_PASSWORD`/`.env`) → `~/.hermes/state/mjm_credentials.json` fallback. See §Credentials above.

### Step 4 — Get page data (CSRF + products)

```python
from post_sale import get_page_data, resolve_products
csrf, all_products, by_code = get_page_data(
    "https://mjmbattery.com", phpsessid, branch="Kiriman Luar Kota"
)
# by_code is {code: product} dict for fast lookup
```

`allProducts` is extracted from the `<script>` block on `sale_custom_wholesale.php?branch=X`. No browser needed.

If session expired (CSRF not found), re-login and retry.

### Step 5 — Resolve customer

Priority:
1. **`invoice.customer.id`** from JSON → use verbatim, auto-cached for future.
2. **Customer cache** (`~/.hermes/state/mjm_customers.json`) → jika nama pernah di-resolve sebelumnya, skip lookup entirely.
3. **Search autocomplete** → pick first `type == 'Grosir'` candidate → auto-cache.
4. **Multiple Grosir** → exact name match first, else **STOP** and surface candidates for user to pick. User pilih → ID tersimpan di cache otomatis.

```python
from post_sale import resolve_customer, lookup_customer_id, cache_customer_id

# Auto: check JSON ID → cache → search → auto-cache
customer = resolve_customer(invoice, "https://mjmbattery.com", phpsessid)

# CRITICAL: resolve_customer returns a dict with 'id', but post_sale() requires
# invoice['customer'] to be a dict with both 'name' and 'id'. Update it here:
invoice["customer"] = {"name": invoice.get("customer") or customer.get("value"), "id": customer["id"]}

# Manual: cek cache langsung
cached = lookup_customer_id("HS AKI")  # → 160 or None

# Manual: simpan mapping sendiri
cache_customer_id("HS AKI", 160)
```

Cache file is `~/.hermes/state/mjm_customers.json` — struktur `{"nama lower": id}`.

**User preference on wrong posts:**一旦 ada sale yang salah produk/total, **user yang hapus manual dari admin**. Jangan coba cancel/rollback via code. Cukup laporkan salahnya,_user fix manual, lalu baru repost yang benar.

### Step 6 — Resolve products

Match invoice item codes to `by_code` dict. Apply code-map for supplier→admin code translation.

**⚠️ Product tidak ditemukan → STOP & TANYA product ID. Jangan tebak, jangan fallback dasbor/spasi otomatis.** `resolve_products()` sekarang gak akan fallback otomatis. Kalau error → kasih tau user kode yang gagal + similar codes, minta product ID dari admin panel.

**Ada code_map kosong?** Cek `scripts/code_map.json` dulu sebelum nambah mapping baru. Maintain biar makin lengkap.

```python
from post_sale import resolve_products
code_map = {                              # supplier → admin
    "GLX-GTZ-5S": "GLX MF GTZ5S",
    "GSMF-NS40ZL": "GS MF NS40ZL",
}
resolved = resolve_products(invoice["items"], by_code, code_map)
# resolved: [{code, mapped_code, product, qty, price, name}, ...]

# Validate price vs wholesale — ONLY for code-mapped items (where the
# invoice code was transformed via code_map). Direct code matches
# (item["code"] == r["mapped_code"]) are the right product regardless
# of price — invoice prices often differ legitimately from admin
# wholesale (Incoe Premium/Incoe Gold/Aspira/Galaxy markup, etc.).
# Jangan paksa posting pakai produk yang salah.
# Jangan tebak — STOP & tanya user product ID kalau gak ditemukan.
# Price validation untuk code-mapped items: kalo price beda jauh dari ws, kemungkinan salah mapping.
for item, r in zip(invoice["items"], resolved):
    expected_price = item.get("unit_price") or r["price"]
    actual_ws = r["product"].get("price_wholesale")
    was_mapped = item["code"] != r["mapped_code"]
    if was_mapped and actual_ws and abs(actual_ws - expected_price) > 5000:
        # Code was mapped -> price must match, else wrong product
        print(f"  ⚠️ {item['code']} -> {r['mapped_code']}: invoice={expected_price:,} vs ws={actual_ws:,}")
        raise ValueError(
            f"Product mismatch for {item['code']} (mapped->{r['mapped_code']}): "
            f"ws={actual_ws}, expected ~{expected_price}. "
            f"Code mapping may be wrong. Stop and verify admin code."
        )
    # For direct matches, just log the difference (legitimate markup)
    if actual_ws and abs(actual_ws - expected_price) > 5000:
        print(f"  ℹ️ {item['code']}: invoice={expected_price:,} vs ws={actual_ws:,} (markup, OK)")
    item["id"] = r["product"]["id"]
    item["unit_price"] = expected_price
    item["qty"] = r["qty"]
    item["product_code"] = r["mapped_code"]
```

### Step 7 — Post the sale + auto-record cashback expense

**Default mode: cashback → Biaya Marketing expense.** Items posted at full price, cashback recorded as separate expense entry at Kiriman Luar Kota via Bank Transfer.

Use `post_expense_after=True` to auto-post the expense after sale succeeds:

```python
from post_sale import post_sale

# Build products_by_code dict
products_by_code = {r["mapped_code"]: r["product"] for r in resolved}
for r in resolved:
    if r["code"] != r["mapped_code"]:
        products_by_code[r["code"]] = r["product"]

result = post_sale(
    phpsessid=phpsessid,
    invoice=invoice,
    products_by_code=products_by_code,
    branch="Kiriman Luar Kota",
    csrf=csrf,
    base_url="https://mjmbattery.com",
    cashback_mode="expense",          # items at FULL price
    post_expense_after=True,          # auto-create Biaya Marketing expense
)
print(f"✅ {result['server_invoice']}  sale_id={result['sale_id']}")
if result.get("expense_id"):
    print(f"💰 Cashback expense id={result['expense_id']}")
elif result.get("expense_error"):
    print(f"⚠️  Expense failed: {result['expense_error']}")
```

Or CLI (single command):
```bash
# Auto: sale + expense in one call
cat invoice.json | python3 scripts/post_sale.py post --expense

# Legacy: absorb cashback into items (old behavior)
cat invoice.json | python3 scripts/post_sale.py post --cashback-mode=absorb

# Standalone expense (manual)
python3 scripts/post_sale.py expense \
    --date 2026-07-27 --amount 50000 \
    --description "Cashback penjualan HS AKI - 063/PS-T/VI/26" \
    --vendor "HS AKI SIDOARJO"
```

When `cashback_mode='expense'` (default), `post_sale()` extracts cashback from the invoice JSON automatically via `summary.cashback`, `cashbacks[]` array, or `subtotal - grand_total` difference. If no cashback detected, expense is skipped.

### Step 8 — Record idempotency

```python
from idempotency_check import append as idem_append
idem_append({
    "user_invoice": invoice["invoice_number"],
    "customer_name": customer["value"],
    "grand_total": int(invoice["summary"]["grand_total"]),
    "server_invoice": result["server_invoice"],
    "sale_id": result["sale_id"],
})
```

### Step 9 — Report result

Return to user: invoice number, server invoice, sale_id, grand_total, items summary.

## Pitfalls

- **`sale_wholesale.php?error=empty` on direct `post_sale()` API** — happens when you call `post_sale()` directly (Python, not the CLI `post` subcommand) and `invoice['items']` entries lack an `id` field. `build_payload` builds items_json from items with `id`, and if no item has `id` it posts an empty set → server redirects `error=empty`. The CLI `post` subcommand injects `item["id"]` from `resolve_products` automatically; when calling the API you must do it yourself:
  ```python
  for item, r in zip(invoice["items"], resolved):
      item["id"] = r["product"]["id"]
  ```
  (Serviceable via SANITY: invoice should have `items` populated with matched ids before `post_sale`.)

- **Session expires fast** (2-3 min). If CSRF harvest fails → re-login and re-fetch page data.
- **Session expires fast** (2-3 min). If CSRF harvest fails → re-login and re-fetch page data.
- **Login CSRF + redirect.** Before POSTing to `/admin/login_process.php`, GET `/admin/login.php` with the same cookie jar and extract the fresh hidden `csrf_token`. Send username, password, and token. A direct credentials-only POST returns HTTP 403: `CSRF token tidak valid. Refresh halaman dan coba lagi.` Successful login returns 302 to `index.php`; use a no-redirect handler to capture `PHPSESSID`.
- **Python 3.13 compat:** `OpenerDirector.open()` doesn't accept `context=` kwarg anymore. Fix: pass SSL context via `HTTPSHandler(context=ctx)` instead of `opener.open(req, context=ctx)`.
- **`search_customers.php` uses `+` not `%20`** for spaces. `search_customers()` handles this.
- **`allProducts` parsing** — the JS array may contain unescaped single quotes inside string values. `get_page_data()` uses `re.DOTALL` match which handles most cases.
- **Stock error** — `Stok tidak cukup` means a real branch was used instead of `Kiriman Luar Kota`. `Kiriman Luar Kota` has stock=0 for all products and the server accepts that.

**Stock error** — `Stok tidak cukup` means a real branch was used instead of `Kiriman Luar Kota`. `Kiriman Luar Kota` has stock=0 for all products and the server accepts that.
- **`Origin` header is mandatory.** `post_sale()` and all HTTP helpers set `Origin: https://mjmbattery.com`. Missing it → 403.
- **Code-map gaps** — when a supplier code is unknown, stop and ask user for the admin panel code, then update `product-code-map.md`.
- **INMF prefix is MIXED dash/space** — don't assume one convention. Some INCOE MF codes retain dash (`INMF-NS40Z` id=745, `INMF-NS40ZL` id=746, `INMF-58024` id=556), others are space (`INMF N70Z` id=742, `INMF NX110-5L` id=786, `INMF NS60` id=747, `INMF 55559` id=783). Probe each code in `by_code` before mapping; dash→space only for the space variant. Full INMF table in `references/product-code-map.md` §2026-08-05.
- **- **"(Retail) tidak valid" error** — Produk GSMF GTZ5S dkk ditolak dgn `(Retail)`. **Bukan produk retail!** Penyebab: PHP backend `$item["price_type"] ?? "Retail"`. Fix: tiap item harus ada `"price_type": "CustomGrosir"`. Udah di-patch di `post_sale.py build_payload()`.

- **Customer exact-name miss** — search query is first-word fragment, not full name. If no results, show candidates and ask.
- **Common Indonesian prefix floods search** — `resolve_customer()` uses `name.split()[0]` as the query. For names starting with `PAK`, `MAS`, `TOKO`, `CV`, `UD` this returns hundreds of candidates and raises `ValueError` (multiple Grosir). **Fix**: search manually with a more specific word (e.g. "ALVIN" instead of "PAK"), get the id, then set `invoice["customer"]["id"] = <id>` before calling `resolve_customer()`. Cache the id with `cache_customer_id()` afterwards so next time is instant.
- **Delta handling** — DEFAULT `cashback_mode='expense'`: items_sum = full subtotal (before cashback). Cashback auto-recorded as separate Biaya Marketing expense via `post_sale(post_expense_after=True)`. No absorption needed. Legacy `cashback_mode='absorb'`: old behavior, cashback absorbed into item prices, 1-2 rupiah rounding acceptable.

**⚠️ Cashback brand-specific — default mode `cashback_mode='expense'` no longer needs brand-specific absorption.** Cashback amount ditotal otomatis oleh `_extract_cashback()`. Untuk legacy mode `cashback_mode='absorb'` saja yang perlu distribusi proporsional per brand. Lihat `references/cashback-handling.md` §CASHBACK PENCAPAIAN.
- **byob NOT used.** All communication is direct HTTP. If you see browser tool calls in the old flow, ignore them.
- **Numeric-prefix customer names** — `resolve_customer()` searches `name.split()[0]`. For names starting with digits (e.g. "354 NK ACCU MAGETAN", "212 TOKO AKI") this searches a numeric string. It works if the autocomplete returns a match, but may fail for unknown numeric prefixes. **Fix**: if the first word is numeric and search returns empty, try the second word or a meaningful keyword instead. Cache the result afterwards.

## Worked example

```json
// invoice.json
{
  "customer": {"name": "HS AKI SIDOARJO"},
  "items": [
    {"product_code": "GLX MF GTZ5S", "qty": 10, "unit_price": 288800}
  ],
  "summary": {"grand_total": 2888000},
  "invoice": {"invoice_number": "063/PS-T/VI/26", "invoice_date": "2026-06-24"}
}
```

Flow:
1. `idempotency_check.py check "063/PS-T/VI/26"` → NEW
2. `login()` → get PHPSESSID
3. `get_page_data()` → csrf + products
4. `resolve_customer()` → search "HS AKI" → Grosir id=160
5. `resolve_products()` → match GLX MF GTZ5S → product id=...
6. `post_sale(cashback_mode='expense', post_expense_after=True)` → sale `OUT-4006-010626` id=4006 + expense id=... (cashback=0, skipped)
7. `idempotency_check.py append` → record
