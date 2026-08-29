#!/usr/bin/env bash
# Template: POST a wholesale sale to mjmbattery.com /admin/sale_save.php
# Use when byob browser tools rate-limit or when you already have the
# PHPSESSID cookie + csrf_token harvested from the form page.
#
# Verified working: 4 invoice runs on 2026-06-21 (sale ids 16472, 16473,
# 16478, 16498). See references/verified-runs.md for full details.
#
# Critical: the `Origin` header is REQUIRED, otherwise the server returns 403
# (Cloudflare-style block). Also: implement the rounding-reconciliation block
# to ensure page final_total matches the supplier invoice exactly (zero
# selisih). See references/pitfalls.md.
#
# Usage:
#   1. Get cookie:    mcp_byob_browser_get_cookies domain=mjmbattery.com
#                     -> PHPSESSID value
#   2. Get CSRF:      curl -s '.../sale_custom_wholesale.php?branch=Kiriman+Luar+Kota' \\
#                       -H "Cookie: PHPSESSID=<id>" | grep csrf_token
#   3. Set env vars below (or export them before running)
#   4. Run:           bash sale_save_post.sh
#
# For programmatic use, convert to Python via urllib (preferred — easier to
# compute items array from a parsed JSON invoice).

set -euo pipefail

# --- REQUIRED environment ---
: "${COOKIE:?Set COOKIE='PHPSESSID=...'}"
: "${CSRF:?Set CSRF='<csrf_token from form HTML>'}"
: "${CUSTOMER_ID:?Set CUSTOMER_ID, e.g. 160}"
: "${CUSTOMER_NAME:?Set CUSTOMER_NAME, e.g. 'HS AKI'}"
: "${DATE:?Set DATE=YYYY-MM-DD, e.g. 2026-06-21}"
: "${INVOICE_NOTE:?Set INVOICE_NOTE, e.g. 'Invoice 241/HS-S/VI/26'}"

BRANCH='OUT_OF_TOWN'  # Production sale_save.php checks $branch_name === 'OUT_OF_TOWN' to bypass stock
INVOICE_GRAND_TOTAL="${INVOICE_GRAND_TOTAL:?Set INVOICE_GRAND_TOTAL to summary.grand_total from JSON}"

# --- items_json (one entry per product line) ---
# Each: {id, name, price, base_price, quantity}
# price = unit_price (final price after any per-item adjustment).
# Resolve products via references/invoice-json-schema.md before populating.
ITEMS_JSON='[
  {"id":"495","name":"GS Astra MAINTENANCE FREE GSMFN-NS40ZL","price":797475,"base_price":797475,"quantity":2},
  {"id":"596","name":"INCOE Premium INPR-NX120-7L","price":1130823,"base_price":1130823,"quantity":1}
]'

# --- Compute: items subtotal, delta vs invoice, payments, global_adjustments ---
read ITEMS_SUM DELTA ADJUSTMENTS_JSON PAYMENTS_JSON <<EOF
$(python3 <<PYEOF
import json, sys

items = json.loads('''${ITEMS_JSON}''')
items_sum = sum(i['price'] * i['quantity'] for i in items)
invoice_grand = ${INVOICE_GRAND_TOTAL}
delta = invoice_grand - items_sum

adjustments = []
# Optional: append cashback if set via env
if "${CASHBACK:-}" and "${CASHBACK:-0}" != "0":
    adjustments.append({
        "description": "${CASHBACK_DESCRIPTION:-Cashback}",
        "type": "subtract",
        "amount": int("${CASHBACK}"),
    })
# Append rounding reconciliation
if delta != 0:
    adjustments.append({
        "description": "Penyesuaian pembulatan",
        "type": "add" if delta > 0 else "subtract",
        "amount": abs(delta),
    })

payments = [{
    "method": "${PAYMENT_METHOD:-Transfer}",
    "amount": invoice_grand,           # NOTE: invoice_grand, NOT items_sum
    "notes": "${INVOICE_NOTE}",
}]

print(f"{items_sum} {delta} {json.dumps(adjustments)} {json.dumps(payments)}")
PYEOF
)
EOF

echo "items_subtotal=${ITEMS_SUM}"
echo "delta_vs_invoice=${DELTA}"
echo "global_adjustments=${ADJUSTMENTS_JSON}"
echo "payments=${PAYMENTS_JSON}"

# --- POST ---
curl -sS -L \
  -X POST 'https://mjmbattery.com/admin/sale_save.php' \
  -H "Cookie: ${COOKIE}" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -H 'Referer: https://mjmbattery.com/admin/sale_custom_wholesale.php?branch=Kiriman+Luar+Kota' \\
  -H 'Origin: https://mjmbattery.com' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' \
  --data-urlencode "csrf_token=${CSRF}" \
  --data-urlencode 'price_type=CustomGrosir' \
  --data-urlencode 'sale_type=Grosir' \
  --data-urlencode "branch=${BRANCH}" \
  --data-urlencode "branch_name=${BRANCH}" \
  --data-urlencode "customer_id=${CUSTOMER_ID}" \
  --data-urlencode "customer_name=${CUSTOMER_NAME}" \
  --data-urlencode "custom_sale_date=${DATE}" \
  --data-urlencode "items_json=${ITEMS_JSON}" \
  --data-urlencode "payment_method=${PAYMENT_METHOD:-Transfer}" \
  --data-urlencode 'payment_status=Lunas' \
  --data-urlencode 'payment_status_radio=Lunas' \
  --data-urlencode "payments=${PAYMENTS_JSON}" \
  --data-urlencode "global_adjustments=${ADJUSTMENTS_JSON}" \
  --data-urlencode 'excess_handling=cash' \
  --data-urlencode 'excessHandling=cash' \
  --data-urlencode 'adjType=percent' \
  --data-urlencode 'priceMode=custom' \
  -o /tmp/sale_save_response.html \
  -w 'status=%{http_code}\nfinal-url=%{url_effective}\n'

# A successful response is a 200 with redirect to:
#   sales.php?status=success&invoice=OUT-NNNN-NNNNN&id=NNNNN
# Capture `invoice` and `id` from the final-url for the report.
# If status != 200 or status flag != 'success', inspect /tmp/sale_save_response.html.
