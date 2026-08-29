# Pitfalls (verified from production runs)

Real-world gotchas hit during MJM Battery wholesale-sale ingestion. Read this when a step misbehaves before re-deriving the fix.

### Python 3.13+ — `context` kwarg not accepted by `OpenerDirector.open()`

`urllib.request.build_opener().open()` in Python 3.13+ does NOT accept `context=` keyword argument (raises `TypeError`).

**Wrong** (old code):
```python
opener = build_opener(NoRedirect)
resp = opener.open(req, timeout=20, context=_ctx())  # TypeError in 3.13+
```

**Fix** — pass context via HTTPSHandler:
```python
ctx = _ctx()
opener = build_opener(NoRedirect, urllib.request.HTTPSHandler(context=ctx))
resp = opener.open(req, timeout=20)
```

### Python 3.13+ — `http_error_default` raises HTTPError(302) when redirect_request returns None

Overriding `redirect_request` to return `None` used to suppress redirects. In Python 3.13+, the handler returns `None` → `_call_chain` falls through to `http_error_default` → raises `HTTPError(302)`.

**Wrong**:
```python
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, hdrs, newurl):
        return None        # → HTTPError(302) in 3.13+
```

**Fix** — override `http_error_302` to return `fp` directly:
```python
class NoRedirect(HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, hdrs):
        return fp
    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302
    http_error_308 = http_error_302
```

### Auto-login — now fixed (2026-06-28)

Previously `login()` POSTed to `/admin/login.php` which returned login HTML with no usable session. `post_sale.py` now POSTs to **`/admin/login_process.php`** with a proper NoRedirect handler (`http_error_302` override — Python 3.13 compat). Login works reliably via script. The browser workaround (`--phpsessid`) is no longer needed.

If login still fails, double-check credentials in `~/.hermes/state/mjm_credentials.json` and ensure the base_url is correct.

### GSMF GTZ5S — was "(Retail)" rejection, now fixed

Product `GSMF GTZ5S` (id:484, admin code `GSMF GTZ5S`, user code `GSMF-GTZ-5S`) was previously rejected with:
```
Harga untuk produk GS ASTRA MF GTZ5S (Retail) tidak valid. Harap refresh halaman dan coba lagi.
```
The error occurred because PHP backend defaults `$item["price_type"]` to `'Retail'` when missing, then validates against `price_retail`. **Fix:** every item in `items_json` must include `"price_type": "CustomGrosir"`. Patched in `post_sale.py build_payload()` on 2026-06-25. Verified working same day (sale 16887 — SUKA SUKA AKI MALANG, GSMF GTZ5S ×10 @193k posted successfully).

### Product code not found — STOP, ask user for product ID

No automatic fallback (dash→space, Z↔2). `resolve_products()` raises `KeyError` with similar codes when a code isn't found. User must provide the correct admin product code or ID, then update `code_map.json`.

Common OCR misreads to be aware of (but: **ask user, don't auto-fix**):
- Letter `Z` vs digit `2`: `GLX-GM52-3B` should be `GLX-GM5Z-3B`
- Letter `O` vs digit `0`: `ING0-NS70` should be `INGO-NS70`
- Letter `l` vs digit `1`: `GSMFN-NS4OZl` vs `GSMFN-NS40ZL`

### Ambiguous product codes

Several invoice codes have variants that the supplier's invoice printer collapses. The OUT_OF_TOWN product list contains multiple entries that substring-match the same code fragment. When exact match returns 2+ candidates, surface the list to the user with `(label + ws price + stock)` and ask for confirmation — **never silently pick the first**.

| Invoice code fragment | Real candidates in OUT_OF_TOWN |
|---|---|
| `NS60` | NS60 (id 527), NS60L (id 528), NS60LS (id 479) |
| `NS40Z` | NS40Z (id 524/543/...), NS40ZL (id 495/525/...) |
| `N70Z` | N70Z (id 539/758/...), N70ZL (id 540/...) |
| `NEPEL N2` | Kecil N1 (id 613, ws 14000), Besar N2 (id 614, ws 18000) |
| `NS70` | NS70 (id 530), NS70L (id 532), NS70LS (id 533) |

### Product-specific server-side validation blocks

Some products are currently blocked by server-side validation when posted via direct POST as Grosir / CustomGrosir, even with valid wholesale prices and stock:

### GSMF GTZ5S — "(Retail)" rejection (FIXED 2026-06-25)

Product `GSMF GTZ5S` (id:484, admin code `GSMF GTZ5S`, user code `GSMF-GTZ-5S`) was previously rejected with:
```
Harga untuk produk GS ASTRA MF GTZ5S (Retail) tidak valid. Harap refresh halaman dan coba lagi.
```
The error occurred because PHP backend defaults `$item["price_type"]` to `'Retail'` when missing, then validates against `price_retail`. **Fix:** every item in `items_json` must include `"price_type": "CustomGrosir"`. Patched in `post_sale.py build_payload()` on 2026-06-25. Verified working on 2026-06-25 (sale 16887 — SUKA SUKA AKI MALANG, GSMF GTZ5S ×10 @193k) and 2026-06-28 (sale 17224 — HS AKI, GSMF GTZ5S ×5 @193k). No workarounds needed — the code handles it.

**Tiebreaker**: the supplier's `unit_price` matching `price_wholesale` is the strongest signal. Example: invoice "NEPEL KECIL" with code "N2" @ 14000 → id 613 (Kecil N1 ws=14000), not id 614 (Besar N2 ws=18000). When prices also tie, fall back to label-substring match on `name_only` (e.g. "Kecil" vs "Besar").

## Customer fuzzy match is unreliable

The supplier invoice customer name often doesn't exist verbatim in the customers table. Real cases:

| Invoice name | Real customer (id, label, address) |
|---|---|
| `HS AKI SIDOARJO` | id=160, HS AKI (Grosir), Mojokerto |
| `D&D ACCU MOJOKERTO` | id=170, (user-supplied) |
| `ALFIN ACCU MOJOKERTO` | id=121, MAS ALFIN (Grosir), Mojokerto |
| `WIJAYA AKI MOJOKERTO` | id=29, WIJAYA AKI MOJOSARI (PAK DONNY) (Grosir), Mojosari — search "WIJAYA" (invoice says MOJOKERTO, customer is MOJOSARI — same area, one Grosir candidate) |
| `ADHEEFA JAYA BATTERY MOJOKERTO` | id=48, ADHEEFA JAYA BATTERY (MAS IMAM) (Grosir), Mojokerto — auto-pick Grosir; a same-name Retail (id=279) exists, ignore |
| `ALNO JAYA AKI YOGYAKARTA` | id=104, ALNO JAYA AKI (Grosir), Yogyakarta |
| `SP AKI JOGJA` | id=1456, SP AKI JOGJA (Grosir) — **NOW EXISTS in DB** (2026-08-05; earlier session had to create it). "SP" 2-letter search still returns noise → search "JOGJA", or inject id=1456. |
| `ASIA JAYA` | id=62, ASIA JAYA MOTOR (Grosir), Jombang — NOTA 046/VII/26 had customer null, user said "asia jaya" |
| `PAK PAUL SIDOARJO` | id=158, PAK PAUL (Grosir) — search "PAUL" not "PAK" (prefix flood) |
| `D'WATER` | id=107, D'WATER (Grosir) — **customer actually named D'WATER**, NOT a misread of the AIR ZUUR product. Search "D'WATER" works. |
| `AMRI ACCU YOGYAKARTA` | id=134, AMRI ACCU (Grosir) — standing langganan, cheapest prices, invoices sit far below admin ws. Never flag price mismatch for AMRI. |
| `ARKIE BERKAH ACCU MOJOKERTO` | id=152, ARKIE BERKAH ACCU (MAS YOYON) (Grosir), Mojokerto |
| `ARKIE BERKAH ACCU MOJOKERTO` | id=152, ARKIE BERKAH ACCU (MAS YOYON) (Grosir), Mojokerto |
| `DELTA AKI SIDOARJO` | id=49, DELTA AKI (Grosir) |
| `TJ BATTERY SURABAYA` | id=9, TJ BATTERY (Grosir) |
| `B&B BATTERY MOJOKERTO` | id=159, B&B BATTERY (Grosir), Mojokerto |
| `PAK GIONO MOJOKERTO` | id=162, PAK GIONO (Grosir), Mojokerto — search with "GIONO" not "PAK" (common prefix flood) |
| `PAK MUN MOJOKERTO` | id=186, PAK MUN MOJOKERTO (Grosir) — search with "MUN" not "PAK" |
| `AGUNG AKI MOJOKERTO` | id=88, AGUNG AKI (Grosir), Mojokerto |
| `KJ ACCU MOJOKERTO` | id=13, KJ ACCU (MAS EKO) (Grosir) — search "KJ", NOT "KJ ACCU" floods Retail |
| `MAS TATOK KRIAN` | id=278, Mas Tatok Krian (Grosir) — search "TATOK", NOT "MAS" (prefix flood) |
| `SYILA AKI SIDOARJO` | id=181, SYILA AKI SIDOARJO (Grosir) |
| `PIPU ACCU SIDOARJO` | id=28, PIPU ACCU SIDOARJO (Grosir) |
| `AKI BLITAR` | id=1453, VARA ACCU BLITAR (Grosir) — "AKI BLITAR" was a typo, actual is "VARA ACCU BLITAR". First-word search "AKI" floods all "AKI" customers. Search with second word "BLITAR" instead, or ask user. |
| `SP AKI JOGJA` | id=1456, SP AKI JOGJA (Grosir) — 2-letter prefix "SP" too short, search returns noise. The customer wasn't in DB; user had to create/admin first. Short prefixes (<3 chars) are unreliable for autocomplete — fall back to asking user for customer ID. |

**Workflow**: when the JSON has no `customer.id`, query `ajax/search_customers.php?q=<short fragment>` and surface candidates `(label, type, address)`.

**Selection rules** (in priority order):
1. **Prefer `Grosir` over `Retail`** — for wholesale-sale postings, always pick the Grosir candidate when the search returns a mix. Multiple Grosir → see rule 2. All Retail → see rule 3.
2. **Multiple same-type candidates** (e.g. 2 Grosir with similar name) → surface to user with `(label, type, address, phone)` and ask which.
3. **No exact match** (only Retail candidates for what is clearly a wholesale customer, or single non-Grosir candidate) → surface to user and ask whether to use it, or stop and create the customer in `/admin/customers.php` first.
4. **User supplies `customer.id`** → skip the lookup entirely and use that ID verbatim.

This is a deliberate override of the earlier "user picks via UI autocomplete" rule: the user explicitly asked to auto-resolve to Grosir whenever possible to skip the manual pick step on batch runs.

## Rounding reconciliation (mandatory for zero selisih)

`sum(items[].price × qty)` often differs from `invoice.grand_total` by 1-4 rupiah because the supplier's billing system does its own rounding. The mjmbattery page records `final_total = items_subtotal + sum(add) − sum(subtract)` and tracks `payment_status` based on `payment amount vs final_total`.

To match the supplier invoice exactly:
- Compute `delta = invoice.grand_total − sum(price × qty)`.
- If `delta ≠ 0`, append one entry to `global_adjustments`:
  - `delta > 0`: `{"description":"Penyesuaian pembulatan","type":"add","amount":delta}`
  - `delta < 0`: `{"description":"Penyesuaian pembulatan","type":"subtract","amount":abs(delta)}`
- Set `payments[0].amount = invoice.grand_total` (not items_sum).
- Result: page `final_total = invoice.grand_total`; payment = same; sisa hutang 0; lebih bayar 0.

Without this, the page records a small but real outstanding receivable (e.g. sale 16473 had 1 rupiah hutang, sale 16498 had 4 rupiah — both visible in the daily_cash_summary until reconciled).

## Item unit_price × qty may not match stated line_total

Invoice lines sometimes show a `total` that doesn't equal `harga × qty`. Example from 2026-06-23 KELVIN AKI batch:
- `INPR-N5OZ`: harga=763,911, qty=4, stated total=3,055,643 (763,911×4=3,055,644 — off by 1)
- `INPR-NS70`: harga=830,689, qty=4, stated total=3,322,755 (830,689×4=3,322,756 — off by 1)

This happens when the supplier's billing system rounds/truncates unit prices before displaying but calculates line totals from a more precise base. The admin panel always computes `price × qty`, so 763,911×4=3,055,644 regardless of what the invoice says.

**User preference: no pembulatan**: Do NOT add "Penyesuaian pembulatan" global_adjustments for these small deltas (≤2 rupiah). Use the invoice `summary.grand_total` as `payments[0].amount` and skip the adjustment entry entirely. The user wants "harus apa adanya" — exact as the invoice states. Structural deltas from `omset_details` (50k-125k range) are legitimate and should keep their adjustments.

## Image OCR paths in Downloads are sandbox-blocked

`vision_analyze` against `/Users/daniimy/Downloads/<file>` returns `Operation not permitted` because the agent sandbox doesn't have read access there. Two workarounds (user-side):
1. Paste image inline in chat (drag-drop / attach).
2. Copy to `/tmp/<file>` then reference that path: `cp "/Users/daniimy/Downloads/foo.jpg" /tmp/foo.jpg`.

Don't retry the original path with different escape sequences — the deny is at the directory level, not the filename.

### Customer name variant between pages (truncation/OCR)

Multi-page invoice JSON sometimes has slightly different customer names across pages due to OCR truncation or supplier printer limits. Real case: page 1 `AGUNG AKI MOJOKERTO`, page 2 `AGUNG AKI MOKER` — "MOKER" is truncation of "MOJOKERTO". Both resolved to same customer id=88 (AGUNG AKI, Grosir).

**How to detect:**
1. Same invoice number across pages but customer names differ
2. First word(s) match (e.g. "AGUNG AKI") — same business name prefix
3. Second part is clearly a city/place name variant ("MOKER" vs "MOJOKERTO", "SBY" vs "SURABAYA")
4. NOT the owner-name exception (customer ≠ bank account holder name)

**Action:** merge as same customer. Use the fuller name from page 1 for the combined sale.

**Wrong:** post separate sales under different names for the same invoice/customer.

Multi-page CV MJM BATTERY BAROKAH invoices often switch to `penjual="MJM BATTERY"` with `customer="MOCHAMMAD JEHAN MUJIYANTO"` on page 2+, using BCA 1132555235 (owner's personal account). **This is the same sale.** The owner (Mas Jehan) is not a separate customer — page 2 items are part of page 1's business sale. Always merge items back to page 1's customer.

**Wrong** (what happened 2026-06-30):
- Page 1 → DELTA AKI → posted as sale 17492 (correct)
- Page 2 → MOCHAMMAD JEHAN MUJIYANTO → posted as sale 17498 (WRONG — should be merged into DELTA)

**Fix**: detect by checking if page 2's customer name matches the bank account holder on that page. If it does and it differs from page 1's customer, merge all page 2 items into page 1's customer and post as one sale. User had to manually delete 4 wrong sales from admin.

**Heuristic**: when processing multi-page invoices for CV MJM BATTERY BAROKAH, any page with `customer="MOCHAMMAD JEHAN MUJIYANTO"` automatically means "merge back to page 1's business customer." Update the customer-cache to NOT cache this name — it's a special sentinel, not a real customer.

## Duplicate-submit gotcha (added 2026-06-23)

The 2026-06-23 batch run re-submitted invoice `063/PS-T/VI/26` because the server's `sales.php` search field does not index the user-supplied invoice number — only the server-generated `OUT-NNNN-NNNNN` and customer name. The form happily accepted the second POST and created a duplicate sale (id 16592, OUT-0626-00018).

**Workaround**: a local state file at `~/.hermes/state/mjm_processed_invoices.json` keyed by user-invoice-number. The skill checks it before every POST. See `Step 1.5` in `SKILL.md` for the exact pattern. State file is seeded with all 9 known sales (4 from 2026-06-22 + 5 from 2026-06-23 batch).

**⚠️ Compound key needed for multi-page invoices**: When the same invoice_number has different customers across pages (e.g. page 1 = DELTA AKI, page 2 = MOCHAMMAD JEHAN), keying by invoice_number alone causes false duplicate detection on page 2. **Fix**: use compound key `f"{invoice_number}|{customer_name}"` instead of bare invoice_number. Update `idempotency_check.py check()` to accept an optional `customer` param, or call with compound key manually.

```python
compound_key = f"{unit['nomor']}|{unit['customer']}"
dup = idem_check(compound_key)
# On append, store the compound key as user_invoice
idem_append({"user_invoice": compound_key, "customer_name": cust, ...})
```

**Limitation**: this only catches duplicates on the same machine/profile. If you run on a different laptop or as a different Hermes user, the state file is empty and duplicates can slip through. Cross-machine safety would require a shared store (DB row, S3 object, or a single shared `~/.hermes` synced via iCloud/Dropbox).

### Duplicate admin code — RESOLVED: 12N10 now has per-brand unique codes

**UPDATE 2026-07-27: Admin codes changed.** Previously `PREMIUM 12N10-3B` was a shared duplicate code for YUASA (id=675, ws=245k) and ALFABATT (id=679, ws=165k). **Sekarang setiap brand punya kode unik:**
- YUASA → `YUASAPR 12N10-3B` (id=675, ws=245,000)
- ALFABATT → `ALFAPR 12N10-3B` (id=679, ws=165,000)
- GSPK → `GSPK PREMIUM 12N10-3B` (id=736, ws=230,000)

by_code sekarang bisa resolve langsung tanpa override. Cuma perlu mapping:
```python
code_map["12N10"] = "YUASAPR 12N10-3B"  # untuk YUASA (brand paling umum di invoice)
```

Identifikasi brand dari `name` item: "YUASA" → YUASAPR, "ALFABATT"/"ALFA" → ALFAPR, "GS"/"GS ASTRA" → GSPK. Lihat `references/product-code-map.md` §2026-07-27.

## POST `sale_save.php` requires `Origin` header

Confirmed: omitting `Origin: https://mjmbattery.com` returns 403 with body `error code: 1010` (Cloudflare-style block). The required minimum headers are:

```
Cookie: PHPSESSID=<from browser_get_cookies>
Content-Type: application/x-www-form-urlencoded
Referer: https://mjmbattery.com/admin/sale_custom_wholesale.php?branch=Kiriman+Luar+Kota
Origin: https://mjmbattery.com
X-Requested-With: XMLHttpRequest
User-Agent: Mozilla/5.0 ...
```

## Invoice product codes often don't match admin panel codes verbatim

Excellent example: supplier invoice `GLX-GTZ-5S` resolves to admin panel `GLX MF GTZ5S`. The invoice printer uses different conventions from the admin CRUD system:
- Hyphens become spaces: `GSMF-GTZ-5S` → `GSMF GTZ5S`
- Brand prefix is dropped or restructured: `GSPR-12N10` → `GSPK PREMIUM 12N10-3B`
- Typos differ: `CHILWEE 12.12` → `CHILWEI 12.12`

**Workflow**: build a `CODE_MAP` dict before the batch. Treat invoice codes as lookup keys, admin codes as targets. Use this map FIRST before any other matching. When unknown: exact match on code; if 0 matches, substring match on partial; if still 0, surface to user.

Should this map grow large, carve out `references/product-code-map.md`.

## Duplicate invoice guard

`sale_save.php` redirects to `sales.php?status=duplicate&id=<id>&invoice=<code>` when the same sale is posted twice in the same session. The first call returns 200 with full HTML body (no error HTTP status), only the Location header reveals the duplicate. In a batch run, if a test-only invoice lands in the same session it collides with the real one.

**Mitigation**: before POSTing, check whether the invoice already exists. `sales.php?status=success` page shows all sales; parse invoice numbers. If the exact supplier invoice number is already in today's sales list, skip the POST or warn before overwriting.

## Submit via browser button is deprecated

Use **Direct `curl`/`urllib` POST** to `sale_save.php` exclusively — via `scripts/post_sale.py` or the CLI. The browser button is unreliable and no longer needed. Full recipe in `references/direct-post-recipe.md`.

## CSRF tokens are per-page-load

`csrf_token` is generated server-side each request to `sale_custom_wholesale.php`. Harvest it from the page that initiated the action (the form page, not `sales.php`). Tokens expire with session (2-3 min of inactivity).

## Session expires fast

2-3 min idle → bounced to `/admin/login.php`. On 403 or unexpected redirect mid-workflow, re-login and re-fetch CSRF + re-check `allProducts` for the current branch (cache invalidates on session change).

### customer.id missing error from `build_payload()`

`post_sale.py` requires `invoice['customer']` to be a dict with both `name` and `id`. 
If you pass a bare string, it raises: `customer.id missing. Resolve customer and inject into invoice['customer']['id']`.

**Fix**: after `resolve_customer()`, always set:
```python
invoice["customer"] = {"name": invoice.get("customer") or customer.get("value"), "id": customer["id"]}
```

### `customer.name` EMPTY — refusing guard (added 2026-08-07)

`build_payload()` now **refuses to post** if `invoice['customer']['name']` is `None`/empty — raises `customer.name is EMPTY`. Pelanggan blank pernah kepost; jangan pernah ulangi. Kalau raise ini muncul:
1. Jangan override/tebak.
2. Resolve customer beneran (`resolve_customer` / `search_customers` / cache) sampai punya name non-kosong **dan** id.
3. Aneh/ambigu → **tanya user**, baru post.

### byob NOT used — all HTTP direct

The skill now uses direct HTTP via `scripts/post_sale.py` exclusively. No browser needed. The byob MCP server rate-limit issue that affected old runs no longer applies.

## Due date in JSON can conflict with real invoice

JSON extraction sometimes gets `due_date` wrong. D&D case: page 1 JSON had `due_date: null` (correct = Lunas), but user initially misread and said "harusnya Tempo". Rush re-post merged all 3 pages as Tempo — wrong.

**Fix:** When user says "this page should be Tempo/Lunas" and JSON says opposite:
1. **Jangan langsung re-post.** Tanya user konfirmasi dulu: "Ini page 1 di faktur fisiknya ada tgl jatuh tempo atau — (strip)?"
2. Kalau user yakin → ikut user (dia pegang faktur fisik).
3. Tapi jangan merge pages dengan status beda (mixed → separate sales).

## Different seller entity, same invoice number, same customer

D&D page 3: seller tercetak "MJM BATTERY" (bukan "CV MJM BATTERY BAROKAH") dengan BCA owner (1132555235 a.n. MOCHAMMAD JEHAN MUJIYANTO). Tapi customer tetap "D&D ACCU MOJOKERTO" dan nomor invoice sama.

**Ini BUKAN owner-name exception.** Owner-name exception cuma berlaku kalau **customer name** berubah jadi nama pemilik. Kalau seller doang yang beda tapi customer sama → item tetap merge ke sale yang sama.

Cara deteksi:
- Cek `customer.name` — kalau match dengan page lain → merge meskipun seller/bank berbeda
- Cek apakah customer.name === bank account holder name → baru owner-name exception

## Free/promo items (price=0, not in admin) — skip silently

Item promosi kayak "FREE KAOS GLX" dengan `price: 0` dan kode tidak dikenal admin (`allProducts`) → **hapus dari items array sebelum post**. Ini bukan barang yang dijual, cuma catatan promosi di faktur.

Aturan: price=0 AND code not in admin by_code → skip. Price=0 but code exists in admin (diskon penuh barang regular) → retain.

## HTTP 522 server timeout

mjmbattery.com kadang ngereturn 522 (Cloudflare timeout). Sederhana: retry aja. Login ulang, post ulang. Biasanya works di percobaan kedua. Gak perlu ubah kode — cukup retry logic di client.`
