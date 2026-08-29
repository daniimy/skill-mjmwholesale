# Cashback Distribution Algorithm

When an invoice has cashback that must be absorbed into item prices (no `global_adjustments`), use this approach:

## Algorithm

1. Group items by cashback eligibility (INCOE, GS, GLX, etc.)
2. For each group with a cashback amount:
   - Compute group subtotal = sum(harga * qty for items in group)
   - For each item: reduction = round(cashback * item_total / group_subtotal)
   - Target line_total = item_total - reduction
   - adj_price = round(target_line_total / qty)
3. Items with no cashback keep original harga
4. If current_sum != grand_total, iteratively adjust ±1 on smallest-qty items in cashback-eligible groups until match

## Verified runs

- **158/IA-B/VI/26** (IMAM ACCU BLITAR): 10 items, 1 cashback group (INCOE -1,170,000), grand=85,538,275 ✅
- **031/SSA-M/VI/26** (SUKA SUKA AKI MALANG): 12 items (after split), 3 cashback groups (INCOE -160k, GS -30k, GLX -100k), grand=31,892,337 ✅
