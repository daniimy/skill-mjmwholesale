# Cashback / Diskon Handling

**DEFAULT: Expense approach.** Cashback recorded as separate Biaya Marketing expense. Items posted at full price. See §Expense approach below.

**Legacy: Absorbed** (`cashback_mode='absorb'`) — available via `--cashback-mode=absorb` for edge cases.

## Worked Example — FLYING STAR SOLO (085/FS-S/VI/26)

Invoice data:
- 8 INGO items (53 pcs total): subtotal 33,830,940
- 1 GLX-GM5Z-3B: 100 pcs × 96,000 = 9,600,000
- Cashback Incoe: -265,000
- Grand total: 33,565,940

Items sum without adjustment: 33,830,940 + 9,600,000 = 43,430,940
Grand total: 43,165,940 (43,430,940 - 265,000)
Delta: -265,000

**Approach**: Reduce INGO (Incoe) unit prices to absorb the Incoe cashback — NOT the GLX:
- Cashback: 265,000 for 53 pcs Incoe = 5,000/pcs
- All 8 INGO items reduced by exactly 5,000/pcs each
- GLX-GM5Z-3B stays at original 96,000/pcs

Result:
- INGO NS40: 502,540 × 5 = 2,512,700 (was 507,540)
- INGO NS40L: 502,540 × 5 = 2,512,700
- INGO NS40ZL: 539,500 × 7 = 3,776,500
- INGO NS60: 581,740 × 11 = 6,399,140
- INGO NS60L: 581,740 × 9 = 5,235,660
- INGO NS5OZ: 722,320 × 6 = 4,333,920
- INGO NS70: 783,700 × 4 = 3,134,800
- INGO N7OZ: 943,420 × 6 = 5,660,520
- GLX GM5Z-3B: 96,000 × 100 = 9,600,000
- Total: 33,565,940 + 9,600,000 = 43,165,940 ✅

## Selection heuristic

**CRITICAL**: Absorb cashback/diskon into the items that the cashback is FOR — not unrelated items.
- Cashback "aki Incoe (53 Pcs)" → reduce Incoe items only, NOT other brands
- If per-item rate is clean (e.g. 5,000/pcs for all items), apply evenly
- If uneven, apply to the affected group's highest-qty item first

### ⚠️ CASHBACK PENCAPAIAN — brand-specific (jangan tebak!)

Banyak invoice supplier ada **cashback pencapaian bulanan** yang tertulis jelas di faktur:

> "CASHBACK PENCAPAIAN GS DAN INCOE MOBIL BULAN JUNI 2026 (78 PCS X Rp 10.000)"

**ARTINYA:** Cashback cuma untuk produk **GS** + **INCOE MOBIL** (bukan INCOE MOTOR, bukan Motobatt, bukan Yuasa, bukan aksesoris).

**Cara baca deskripsi cashback:**
1. Cari kata kunci brand (GS, INCOE, GSHY, GSMFN, GSMF, INGO, INPR, INMF, dll)
2. Cari kata "MOBIL" vs "MOTOR" — INCOE punya produk mobil dan motor, bedain!
3. Kalo cuma "GS DAN INCOE" tanpa "MOBIL" → semua produk GS + INCOE kena
4. Kalo "GS DAN INCOE MOBIL" → hanya GS mobil (GSHY, GSMFN, GSPR, GSPK, GSMFOE, dll) + INCOE mobil (INGO, INPR, INMF untuk mobil). Motobatt, Yuasa, aksesoris, dan INCOE motor tetap utuh
5. Kalo deskripsi gak jelas / gak ada → **KONFIRMASI KE USER**, jangan tebak distribusi ke semua item

**Contoh case nyata — HS AKI 245/HS-S/VII/26:**
- 6 item: Yuasa, GSMFN-55D23L, INGO-NS70, GSHY-NS60, MTZ5S, MTZ6S
- Cashback: "PENCAPAIAN GS DAN INCOE MOBIL" = Rp780.000
- Yang kena: **GSMFN-55D23L**, **INGO-NS70**, **GSHY-NS60** (3 item, total 2.650.057)
- Yang TIDAK kena: **12N10** (Yuasa motor), **MTZ5S** (Motobatt motor), **MTZ6S** (Motobatt motor)
- Distribusi proporsional dalam grup: tiap item dikurangi proporsi line_total-nya terhadap subtotal grup (2.650.057)

**Contoh nyata — IMAM ACCU 160/IA-B/VII/26:**
- 5 item: INGO-NS70, INGO-N50Z, INGO-N70Z, GSMFN-NS60L, GSMFN-NS60
- Cashback: "Cashback GS Mobil (20 pcs)" = Rp100.000 — **tanpa INCOE**, hanya GS
- Yang kena: hanya **GSMFN-NS60L** (10 pcs) + **GSMFN-NS60** (10 pcs) — total 20 pcs ✓
- Yang TIDAK kena: INGO items (3 item, 35 pcs) — Incoe tidak disebut di deskripsi
- Per-item: 100.000 / 20 = 5.000/pcs, flat ke kedua item GS

**Contoh nyata — SUKA SUKA AKI 032/SSA-M/VII/26:**
- 19 item dengan campuran INCOE (INGO), GS Mobil (GSHY, GSMFN), GS Motor (GSMF-GTZ)
- Cashback 1: "CASHBACK INCOE (33 pcs)" = Rp165.000 → hanya INGO items (33 pcs) = 5.000/pcs
- Cashback 2: "CASHBACK GS Mobil (27 pcs)" = Rp135.000 → hanya GSHY+GSMFN items (27 pcs) = 5.000/pcs
- GSMF-GTZ (motor, 22 pcs) — tidak kena cashback manapun
- Dua cashback independen, masing-masing absorb ke grup brand-nya sendiri

**Contoh salah (yang pernah terjadi):** Cashback di-absorb ke SEMUA item termasuk motor & aksesoris. ❌ Jangan!

## Expense approach — cashback as Biaya Marketing

**Instead of** absorbing cashback into item prices, split into two transactions:

1. **Sale** at full price (no cashback absorption). `items_sum = subtotal` (before cashback). `payments[0].amount = subtotal`.
2. **Expense** — record cashback as Biaya Marketing expense at Kiriman Luar Kota branch.

### Why

- Revenue recorded at full value (cleaner accounting)
- Cashback tracked as a deductible marketing cost
- Kiriman Luar Kota branch bears the marketing expense
- Payment source "Bank Transfer" = pengeluaran transfer

### Sale payload (no absorption)

```python
# items at FULL price — jangan kurangi harga
items = [
    {"id": str(prod['id']), "name": ..., "price": original_price,
     "base_price": original_price, "quantity": qty, "price_type": "CustomGrosir"}
]
# NO global_adjustments for cashback
# payments = full subtotal
```

### Expense payload

```python
expense_payload = {
    "csrf_token": csrf,          # from expense_new.php
    "expense_date": sale_date,   # same date as sale
    "category_id": "13",         # Biaya Marketing
    "payment_source": "Bank Transfer",
    "amount": str(cashback_amount),
    "description": f"Cashback penjualan {customer_name} - {invoice_no}",
    "vendor_name": customer_name,
    "branch_name": "Kiriman Luar Kota",
    "tax_type": "None",
}
```

POST to `/admin/expenses/expense_save.php`. Returns 302 → `expenses.php?status=approved&id=N`.

### CSRF for expense form

Must harvest from `expense_new.php` (different from sale form CSRF — separate page, separate token).

```python
body = fetch("https://mjmbattery.com/admin/expenses/expense_new.php")
csrf = re.search(r'name="csrf_token"\s+value="([^"]+)"', body).group(1)
```

### Sequence

1. Login (same PHPSESSID — session is shared)
2. POST sale (full price) → get sale_id
3. Harvest CSRF from expense_new.php
4. POST expense (cashback amount) → get expense_id
5. Report both to user

### Rounding

If `items_sum ≠ subtotal_cashback` by 1-2 rupiah, let payments absorb the micro-delta. No global_adjustments needed — the expense entry is the adjustment.

When `harga × qty ≠ line_total` (e.g. 763,911×4=3,055,644 but invoice says 3,055,643):
- Don't adjust any price
- Just set `payments[0].amount = invoice.grand_total`
- The 1-2 rupiah delta is ignored — the admin panel records it as dust