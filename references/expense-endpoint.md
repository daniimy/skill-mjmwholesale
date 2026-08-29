# Expense POST Endpoint — `expense_save.php`

Recording cashback as Biaya Marketing (category_id=13) at Kiriman Luar Kota branch.

## Endpoint

`POST https://mjmbattery.com/admin/expenses/expense_save.php`

## Required headers

| Header | Value |
|--------|-------|
| `Cookie` | `PHPSESSID=<valid_session>` |
| `Content-Type` | `application/x-www-form-urlencoded` |
| `Origin` | `https://mjmbattery.com` |
| `Referer` | `https://mjmbattery.com/admin/expenses/expense_new.php` |
| `X-Requested-With` | `XMLHttpRequest` |

## Form fields

| Field | Value | Notes |
|-------|-------|-------|
| `csrf_token` | (from expense_new.php) | Per-page token, different from sale form |
| `expense_date` | `YYYY-MM-DD` | Same date as the sale |
| `category_id` | `13` | **Biaya Marketing** — auto-approved, no limit |
| `payment_source` | `Bank Transfer` | = pengeluaran transfer. Also: `Cash` |
| `amount` | integer rupiah | e.g. `50000` |
| `description` | free text | e.g. "Cashback penjualan HS AKI - 063/PS-T/VI/26" |
| `vendor_name` | customer name | e.g. "HS AKI SIDOARJO" |
| `branch_name` | `Kiriman Luar Kota` | Or any branch from the dropdown |
| `tax_type` | `None` | Also: `PPN`, `PPh23` |

## Success response

HTTP 302 → `Location: expenses.php?status=approved&id=<expense_id>`

Category_id=13 (Biaya Marketing) has `requires_approval=0` and `limit=0` — so status is always `approved`.

## Python helper

Use `post_sale.post_expense()` which handles CSRF harvest, POST, and response parsing:

```python
from post_sale import post_expense

result = post_expense(
    phpsessid=sid,
    base_url="https://mjmbattery.com",
    expense_date="2026-07-27",
    amount=50000,
    description="Cashback penjualan HS AKI - 063/PS-T/VI/26",
    vendor_name="HS AKI SIDOARJO",
    branch_name="Kiriman Luar Kota",
    payment_source="Bank Transfer",
    category_id="13",
)
# → {"expense_id": 1833, "status": "approved"}
```

## Auto-posting (recommended)

Use `post_sale(post_expense_after=True)` which posts the expense automatically after a successful sale when cashback is detected:

```python
result = post_sale(
    ...,
    cashback_mode="expense",
    post_expense_after=True,
)
# result["expense_id"] = 1833 if cashback > 0 else None
```

## Standalone CLI

```bash
python3 scripts/post_sale.py expense \
    --date 2026-07-27 --amount 50000 \
    --description "Cashback penjualan HS AKI - 063/PS-T/VI/26" \
    --vendor "HS AKI SIDOARJO"
```
