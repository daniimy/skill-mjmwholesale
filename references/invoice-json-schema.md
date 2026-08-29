{
  "supplier": {
    "company_name": "string",
    "address": "string",
    "phone": "string",
    "npwp": "string",
    "bank_accounts": [{"bank": "string", "account_number": "string", "account_name": "string"}]
  },
  "customer": {
    "name": "string — required",
    "id": "int — OPTIONAL override. If present, skip fuzzy lookup and use this customer_id verbatim. Use this when the invoice name doesn't match an existing customer verbatim (e.g. 'D&D ACCU MOJOKERTO' → id=170).",
    "address": "string — metadata only, ignored"
  },
  "invoice": {
    "invoice_number": "string — required, used as payments[0].notes prefix",
    "invoice_date": "YYYY-MM-DD — required",
    "due_date": "YYYY-MM-DD | null — null means Lunas; non-null means Tempo + due_date filled",
    "page": "string — ignored",
    "pages": "int — ignored"
  },
  "items": [
    {
      "product_code": "string — preferred lookup key (exact match against allProducts[].code)",
      "product_name": "string — fallback fuzzy match against allProducts[].label / name_only",
      "qty": "int — required",
      "unit_price": "int — final price per piece, goes into items_json[].price",
      "id": "int — OPTIONAL override. If present, skip lookup and use this product_id verbatim. Use this for ambiguous codes (e.g. invoice 'N2' for NEPEL KECIL → id=613).",
      "weight_kg": "number — metadata, ignored",
      "line_total": "int — metadata, ignored (computed from unit_price × qty)",
      "cost_price": "int — metadata, ignored",
      "omset": "any — metadata, ignored",
      "profit": "int — metadata, ignored",
      "cost_total": "int — metadata, ignored"
    }
  ],
  "summary": {
    "grand_total": "int — REQUIRED. Drives payments[0].amount and the rounding reconciliation. If `delta = grand_total - sum(price×qty) != 0`, append a `global_adjustments` entry to reconcile.",
    "total_amount": "int — alias for grand_total",
    "subtotal": "int — items subtotal before adjustments (pre-cashback)",
    "cashback": "int — discount amount → maps to subtract global_adjustment",
    "cashback_description": "string — goes into the subtract adjustment's description",
    "page_1_total": "int — ignored if grand_total present",
    "page_2_total": "int — ignored",
    "total_cost": "int — metadata, ignored",
    "total_profit": "int — metadata, ignored",
    "profit_percentage": "number — metadata, ignored",
    "total_weight_kg": "number — metadata, ignored"
  },
  "profit": {
    "page_1_profit": "int — metadata, ignored",
    "page_1_percentage": "number — metadata, ignored",
    "page_2_profit": "int — metadata, ignored",
    "page_2_percentage": "number — metadata, ignored"
  },
  "signatures": {
    "sender": "any — ignored",
    "receiver": "any — ignored"
  }
}

# Normalization rules (apply before building items_json / payments / global_adjustments)

1. `branch` defaults to `"Kiriman Luar Kota"` when omitted.
2. `customer.name` required; `customer.id` preferred when present (verbatim).
3. `invoice.invoice_date` → `custom_sale_date`. `invoice.due_date == null` → payment_status=Lunas; otherwise payment_status=Tempo + `due_date=invoice.due_date`.
4. For each item:
   - Resolve product via (in order): `items[].id` (if present) → exact `product_code` match → fuzzy `product_name` match.
   - If ambiguous (2+ candidates), surface them with label+ws+stock and ask the user.
   - Output shape: `{id, name: <label>, price: unit_price, base_price: <price_wholesale>, quantity: qty}`. Omit `adjustment_*` fields (we use priceMode=custom).
5. Compute `delta = summary.grand_total - sum(price × qty)`.
   - If `delta > 0`: append `{"description": "Penyesuaian pembulatan", "type": "add", "amount": delta}` to global_adjustments.
   - If `delta < 0`: append `{"description": "Penyesuaian pembulatan", "type": "subtract", "amount": abs(delta)}` to global_adjustments.
   - If `summary.cashback` is set, also append `{"description": cashback_description, "type": "subtract", "amount": cashback}` BEFORE the rounding delta.
6. `payments[0] = {"method": <default "Transfer">, "amount": summary.grand_total, "notes": "Invoice <invoice_number>"}`.
