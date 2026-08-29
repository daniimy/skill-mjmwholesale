# Verified Page State — `sale_custom_wholesale.php`

Captured from the live page (June 2026). Update this file if the form fields change.

## URLs

| Purpose | Method | URL |
|---|---|---|
| Branch picker / cart form | GET | `/admin/sale_custom_wholesale.php?branch=<NAME>` |
| Customer autocomplete | GET | `/admin/ajax/search_customers.php?q=<query>` |
| Customer scrap deposits (potong-nota) | GET | `/admin/ajax/get_customer_scrap_deposits.php?customer_name=<name>` |
| Submit sale | POST | `/admin/sale_save.php` (form id `saleForm`) |
| Login | GET/POST | `/admin/login.php` (redirects to `/admin/index.php`) |

`OUT_OF_TOWN` is a valid `?branch=` value — maps to `Kiriman Luar Kota` in the branches table.

## `saleForm` field reference

| Field | Type | Source / Notes |
|---|---|---|
| `csrf_token` | hidden | scraped from the form, per-page-load |
| `price_type` | hidden | always `CustomGrosir` |
| `sale_type` | hidden | always `Grosir` |
| `branch` | select | branch name string |
| `branch_name` | hidden | mirrors branch |
| `customer_id` | hidden | set by autocomplete |
| `customer_name` | hidden | set by autocomplete |
| `custom_sale_date` | date | `YYYY-MM-DD`; backdate supported |
| `items_json` | hidden | the cart as JSON string |
| `payment_method` | select | `Cash` / `Transfer` / `QRIS` / `Potong Nota/Deposit` |
| `payment_status` | hidden | `Lunas` or `Tempo` |
| `payment_status_radio` | hidden | mirrors status |
| `due_date` | date | only when `Tempo` |
| `payments` | hidden | JSON-stringified array of payment rows |
| `global_adjustments` | hidden | cart-level adjustments (usually empty) |
| `excess_handling` | hidden | `cash` if customer overpays |
| `excessHandling` | hidden | duplicate, same value |
| `adjType` | select | default adjustment type for the cart |
| `priceMode` | radio | `adjust` or `custom` |
| `shipment_list_id` | hidden | only set if pre-filling from `?shipment_id=…` |
| `scrap_note_id` | hidden | only when using potong-nota deposit |
| `editAdjType` | select | per-row edit modal default |

## `items_json` schema (the cart)

```json
[
  {
    "id": "788",
    "name": "GS Astra NS40ZL N40",
    "price": 580000,
    "base_price": 580000,
    "quantity": 2,
    "adjustment_type": "percent",
    "adjustment_value": -5,
    "source_branches": [],
    "source_quantities": []
  }
]
```

`adjustment_type` ∈ `percent` | `nominal`. Positive or negative. Omit when no per-item adjustment.

## `global_adjustments` schema (cart-level adjustments)

```json
[
  {"description": "Cashback aki GS mobil (4 pcs)", "type": "subtract", "amount": 20000}
]
```

- `type`: `"add"` adds to subtotal, `"subtract"` subtracts. Default in the UI is `"subtract"`.
- `amount`: integer rupiah.
- `description`: free text, shown in the receipt.
- Order: `final_total = items_subtotal + sum(add) − sum(subtract)`.
- Set `payments[0].amount` to `final_total` (not items_subtotal). The page auto-recomputes; if you set it to the subtotal and the page uses it as the expected payment, you can end up overpaying → triggers the lebih-bayar branch.
- If the JSON input has `summary.cashback` or any discount field, map it to a `subtract` adjustment here.
- **Rounding reconciliation** — IMPORTANT for zero-discrepancy against the supplier invoice. The supplier's printed invoice total may differ from `sum(items[].price × qty)` by a few rupiah due to their own rounding. Compute `delta = invoice.grand_total − sum(price × qty)`. If `delta ≠ 0`, append one adjustment:
  - `delta > 0` → `{"description":"Penyesuaian pembulatan","type":"add","amount":delta}`
  - `delta < 0` → `{"description":"Penyesuaian pembulatan","type":"subtract","amount":abs(delta)}`
  Then set `payments[0].amount = invoice.grand_total`. Result: page `final_total = items_sum + delta = invoice.grand_total`; payment = `invoice.grand_total`; sisa hutang = 0; lebih bayar = 0 — exact match against the supplier invoice, no orphaned receivables.

## `payments` schema

```json
[{"method":"Cash","amount":1160000,"notes":""}]
```

For `Tempo`, leave `payments` empty (or one zero row) and fill `payment_status=Tempo`, `due_date=YYYY-MM-DD`.

## Product list source

`<script>const allProducts = [...]</script>` is server-injected only when `?branch=<valid>` is set. Schema per item:

```json
{ "id": 788, "label": "Ganti pull Perbaikan Pull", "code": "Perbaikan Pull", "stock": 9991, "price_wholesale": 0, "name_only": "Ganti pull" }
```

Multi-keyword AND-match client-side filter on `label` + `code` + `name_only`. Space-separated.

## Price modes

- `priceMode=adjust` (default): `final = base + adjustment`. Use when `unit_price ≈ price_wholesale` and you want +/- percent or nominal.
- `priceMode=custom`: `final = typed value`. Use when `unit_price` differs from `price_wholesale` and you don't want to compute the adjustment. **Default for this skill's invoice flow.**

## Pitfalls — quick reference

- **Submit button silent no-op.** Same PHP quirk as stock_edit.php — fall back to `document.getElementById('saleForm').submit();` or direct `fetch` POST to `sale_save.php` if button click doesn't redirect/flash.
- **Session expires 2-3 min.** If redirected to login mid-flow, re-login and resume from Step 3.
- **Wrong branch = empty `allProducts`.** Form renders but search returns nothing. Validate `?branch=` first by sampling 200 chars after `allProducts = [`.
- **Customer must already exist.** No create-customer flow here. If autocomplete empty, stop and tell user.
- **Credentials redacted.** Hermes strips secrets from chat history. Always ask at session start; don't hardcode.
OUT_OF_TOWN (invisible). Not in the dropdown but `?branch=OUT_OF_TOWN` works — maps to `Kiriman Luar Kota`.
- **CSRF token is per-page-load.** Don't reuse across sessions.
- **`price_type` and `sale_type` are hardcoded hidden values.** Don't change them.
- **`Potong Nota / Deposit`** uses a different code path (`get_customer_scrap_deposits.php` + `scrap_note_id`). Out of scope unless user explicitly asks.
