# Direct POST Recipe for `sale_save.php`

The verified-working way to submit a wholesale sale to `https://mjmbattery.com/admin/sale_save.php` from outside the browser. **This is the primary submission path** — faster, deterministic, and the only way proven across production runs.


The byob browser UI is reserved for verification only (read-back the cart, confirm totals before submission). Submit via the button is unreliable — see `pitfalls.md` "Submit button may silently no-op".

## When to use this recipe

- After customer + product lookups are done.
- For batch processing of multiple invoices in one session.

## Step-by-step

### 1. Get the session cookie

```python
# Or use mcp_byob_browser_get_cookies for the live session
import urllib.request
req = urllib.request.Request('https://mjmbattery.com/admin/index.php', method='HEAD')
req.add_header('User-Agent', 'Mozilla/5.0 ...')
# Pull the PHPSESSID for the mjmbattery.com domain (NOT the subdomains
# like absen/payroll/penjualan/boyolali — those are separate sessions)
```

The easiest source is `post_sale.login()` which POSTs to `/admin/login.php` and returns the PHPSESSID from the Set-Cookie header. Credentials auto-read from `~/.hermes/state/mjm_credentials.json`.

### 2. Get CSRF token

CSRF is per-page-load, bound to the session, and expires with the session. Always re-harvest right before the POST:

```python
import re, urllib.request
body = urllib.request.urlopen(urllib.request.Request(
    'https://mjmbattery.com/admin/sale_custom_wholesale.php?branch=Kiriman+Luar+Kota',
    headers={'Cookie': f'PHPSESSID={sid}'}
)).read().decode()
csrf = re.search(r'name="csrf_token" value="([^"]+)"', body).group(1)
```

If the page is rate-limited, you can also re-use a recent CSRF for ~30s within the same session.

### 3. Resolve customer (Grosir-first)

Query the autocomplete endpoint with a short fragment of the customer name (full name with spaces often returns `[]`):

```python
import json, urllib.parse, urllib.request
qs = urllib.parse.urlencode({'q': 'HS AKI'}).replace('%20', '+')  # + not %20 here
data = urllib.request.urlopen(urllib.request.Request(
    f'https://mjmbattery.com/admin/ajax/search_customers.php?{qs}',
    headers={'Cookie': f'PHPSESSID={sid}', 'Referer': 'https://mjmbattery.com/admin/sale_custom_wholesale.php'}
)).read().decode()
candidates = json.loads(data)  # list of {id, label, value, type, phone, address}
```

**Selection rules** (priority order):
1. **Pick the first `type == 'Grosir'` candidate** — auto-resolve, no user prompt needed.
2. If multiple Grosir, surface `(label, type, address, phone)` and ask.
3. If only Retail candidates for a clearly-wholesale customer, ask or stop and create the customer in `/admin/customers.php`.
4. If the input JSON has `customer.id` (or `customer._resolved_id`), skip the lookup entirely.

### 4. Resolve products

The `allProducts` array is injected as a `<script>` block on `sale_custom_wholesale.php?branch=X`. Re-fetch the page and parse it:

```python
all_products = json.loads(re.search(
    r'allProducts\s*=\s*(\[[\s\S]*?\]);',
    body
).group(1))
```

**Lookup**: exact match on `code` first (most reliable). If multiple match, tiebreak by `unit_price == price_wholesale`. If still ambiguous (e.g. NEPEL KECIL code "N2" → N1 vs N2), use label-substring match and surface to the user. See `pitfalls.md` "Ambiguous product codes" for the full ambiguity table.

### 4.5. DATE CHECK — wajib sebelum build payload

**Wajib pakai `input_invoice['invoice_date']` mentah-mentah dari JSON.** Jangan timpa, jangan default ke hari ini. Kalau gak ada → tanya user.

Cek kalau tanggal mencurigakan:
- Invoice_date > hari ini → STOP, tanya user konfirmasi
- Invoice_date > 30 hari lalu → STOP, tanya user, jangan asal submit
- Wajar → lanjut

**PENTING:** Cuma notifikasi. Jangan ganti tanggalnya. Yang di-post tetep `invoice_date` dari JSON.

### 5. Build the payload — ZERO adjustments

```python
import json

items = [
    {"id": str(p['id']),
     "name": f"{p['name_only']} {p['code']}",
     "price": int(i['unit_price']),
     "base_price": int(i['price_wholesale']),
     "quantity": int(i['qty'])}
    for p, i in zip(resolved_products, input_items)
]

# ZERO adjustments — cashback → separate Biaya Marketing expense
# Use post_sale(cashback_mode='expense', post_expense_after=True) instead of
# absorbing into item prices.
# See references/cashback-handling.md §Expense approach

payments = [{
    "method": "Transfer",
    "amount": int(input_invoice['grand_total']),
    "notes": f"Invoice {input_invoice['invoice_number']}"
}]
```

### 6. POST with required headers

```python
import urllib.parse, urllib.request

payload = {
    'csrf_token': csrf,
    'price_type': 'CustomGrosir',
    'sale_type': 'Grosir',
    'branch': 'OUT_OF_TOWN',           # Production checks $branch_name === 'OUT_OF_TOWN' to bypass stock
    'branch_name': 'OUT_OF_TOWN',
    'customer_id': str(customer['id']),
    'customer_name': customer['value'],
    'custom_sale_date': input_invoice['invoice_date'],
    'items_json': json.dumps(items),
    'payment_method': payments[0]['method'],
    'payment_status': 'Lunas',
    'payment_status_radio': 'Lunas',
    'payments': json.dumps(payments),
    'global_adjustments': json.dumps(adjustments),
    'excess_handling': 'cash',
    'excessHandling': 'cash',
    'adjType': 'percent',
    'priceMode': 'custom',
}
data = urllib.parse.urlencode(payload).encode()
req = urllib.request.Request(
    'https://mjmbattery.com/admin/sale_save.php',
    data=data, method='POST',
    headers={
        'Cookie': f'PHPSESSID={sid}',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://mjmbattery.com/admin/sale_custom_wholesale.php?branch=Kiriman+Luar+Kota',
        'Origin': 'https://mjmbattery.com',   # REQUIRED — without it 403
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    }
)
resp = urllib.request.urlopen(req, timeout=30)
```

### 7. Read the result

Success: `Location` header redirects to `sales.php?status=success&invoice=OUT-NNNN-NNNNN&id=NNNNN`. Capture `invoice` and `id` for the report.

Failure: body will be HTML — look for `alert-danger` or the page's error toast text. Common causes:
- `CSRF token tidak valid` → re-harvest from the page.
- `Stock tidak cukup` → branch_name is likely `Kiriman Luar Kota` (triggers stock check). Must be `OUT_OF_TOWN` to bypass inventory validation. See pitfalls.
- HTTP 403 with no JSON → missing `Origin` header.

## Verified runs (2026-06-21)

| sale_id | invoice | customer (id) | items | items_sum | invoice.grand | delta | adjustment |
|---|---|---|---|---|---|---|---|
| 16472 | OUT-0626-00003 | HS AKI (160, Grosir) | 5 | 5,274,146 | 5,274,146 | 0 | none |
| 16473 | OUT-0626-00004 | D&D ACCU MOJOKERTO (170, user-supplied) | 5 | 2,748,912 | 2,748,913 | +1 | add 1 |
| 16478 | OUT-0626-00005 | ARKIE BERKAH ACCU (152, Grosir) | 6 + 20k cashback | 8,436,920 | 8,436,920 | 0 | none (cashback = separate subtract adj) |
| 16498 | OUT-0626-00006 | MAS ALFIN (121, Grosir) | 11 | 20,692,084 | 20,692,088 | +4 | add 4 |
| 16592 | OUT-0626-00018 | PAK SAIFUL TRENGGALEK (36, Grosir) | 4 | 6,875,000 | 6,875,000 | 0 | none |

Note: 16473 and 16498 were submitted **before** the delta-reconciliation rule was added to the skill, so their page total = items_sum, not invoice.grand_total. Both have small outstanding receivables (1 and 4 rupiah). New sales follow the recipe above and match exactly.

## Python helper

The `templates/sale_save_post.sh` script is a bash+python hybrid that wraps this recipe. Set env vars `COOKIE`, `CSRF`, `ITEMS_JSON`, `INVOICE_GRAND`, `CUSTOMER_ID`, `CUSTOMER_NAME`, `BRANCH`, `INVOICE_DATE` and invoke:

```bash
bash templates/sale_save_post.sh
```

The script computes delta and adjustments internally, so the only required field is `INVOICE_GRAND` (the supplier invoice total).
