## Product Code Mappings

### Session 2026-06-25 — IMAM ACCU BLITAR & ANDRI AKI BLITAR

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `GSMF-GTZ-5S` | `GSMF GTZ5S` | Dash → space; was rejected as "(Retail) tidak valid" because `build_payload` didn't send `price_type: "CustomGrosir"` per-item. PHP backend defaults to 'Retail' if missing → validates against `price_retail`. **Fix:** add `"price_type": "CustomGrosir"` to each item in `items_json`. Patched in post_sale.py `build_payload()` (2026-06-25). |
| `GLX-GM5Z-3B` | `GLX PREMIUM GM5Z-3B` | ID 735, ws=105000. Bukan GSPK. |
| `INGO-NS40Z2L` | `INGO-NS40ZL` | Z2L → ZL (left-terminal variant) |
| `INGO-N570` | `INGO-NS70` | N570 → NS70 (weight/price match) |

### Session 2026-06-25 — IMAM ACCU BLITAR + SUKA SUKA AKI MALANG

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `INGO-NS40Z2L` | `INGO-NS40ZL` | Z2L = dual left terminal variant; admin uses `ZL` suffix |
| `INGO-N570` | `INGO-NS70` | N570 not in admin; matched by weight (15.9kg/pcs = NS70) & price proximity |
| `GSMF-GTZ-6V` | `GSMF GTZ6V` | Dash → space; wholesale=240000 ✓ |
| `YTZ6V-S` | `YMF YTZ6V-O` | Price 233,000 matches YMF YTZ6V-O wholesale |
| `CHILWEE 12.12` | `CHILWEI 12.12` | Typo in supplier code (CHILWEE vs CHILWEI) |
| `GSMF-GTZ-5S` | `GSMF GTZ5S` | Previously retail-restricted. **FIXED** by per-item `price_type: "CustomGrosir"` in `build_payload()`. Verified working 2026-06-25 (sale 16887, OUT-0626-00060 — SUKA SUKA AKI MALANG). |

### Session 2026-06-28 — 4-invoice batch (DAVY, DINAMO, SUNAR JAYA, PAK ALVIN)

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `YAMA-GTZ5S` | `YAMA MF GTZ5S` | id=770, ws=95000 (vs invoice 93k — slight diff) |
| `YB5L-B` | `PREMIUM YB5L-B` | id=677, ws=163000 ✓ |
| `YTZ6V` | `YMF YTZ6V` | id=664, ws=230000 ✓ (non-O variant; O variant has ws=233k) |
| `AMARON 95D31L` | `AMR-95D31L` | id=370, ws=1528000 ✓ |
| `AMARON NS40ZL` | `AMR-38B20L` | id=362, ws=748000 ✓ (NS40ZL = 38B20L) |
| `AMARON NS40Z` | `AMR-38B20R` | id=363, ws=748000 ✓ (NS40Z = 38B20R) |
| `D'WATER1` | `AIR AKI 500ML D'WATER1` | id=418, ws=5000 (admin code has full name) |
| `GSPR-95D31L` | `GSPR-95D31L` | id=506, ws=1388934 ✓ (direct match, no map needed) |

### Session 2026-06-28 — 5-invoice batch (HERU, TOKO AKI CARUBAN, EMTE, RAJAWALI, TOKO AKI BOJONEGORO)

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `GLX-GT6A` | `GLX MF-GT6A` | id=732, ws=135500 — Galaxy MF GT6A |
| `ECHO 12.15` | `ECHO 15Ah` | id=812, ws=260000 — ECHO 12V 15AH |

### Session 2026-06-28 — 7-invoice batch (DELTA, TJ, B&B, ALFIN, PAK GIONO, HS, AGUNG)

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `ZUUR GLX` | `ZUUR-GLX` | id=815, ws=0 — AIR ZUUR GLX botol @5000 |
| `AIR ZUUR` | `ZUUR-JRG` | id=816, ws=0 — AIR ZUUR JURIGEN (jerrycan) @100000. Product created manually in admin by user. |

### Session 2026-07-01 — AMRI ACCU YOGYAKARTA (invoice 093/AA-Y/VI/26)

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `ASMF-NS40ZL` | `ASMF NS40ZL` | id=695, ws=618821. Dash→space. ASPIRA MAINTENANCE FREE NS40ZL. |
| `ASMF-NX120-7L` | `ASMF NX120-7L` | id=691, ws=1194652. Dash→space. ASPIRA MAINTENANCE FREE NX120-7L. |
| `GSMF-GTZ-5S` | `GSMF GTZ5S` | id=484, ws=193000. Already mapped from prev sessions, re-verified. |
| `GLX-GTZ-5S` | `GLX MF GTZ5S` | id=733, ws=102500. Already mapped, re-verified. |
| `YAMA-GTZ5S` | `YAMA MF GTZ5S` | id=770, ws=95000. Already mapped, re-verified. |

### Session 2026-06-30 — 9-invoice batch (PIPU, KJ, TJ, HS, MAS TATOK, DELTA, AGUNG, SYILA, D&D)

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `ASHY-NS60L` | `ASHY NS60L` | id=687, ws=591282 — ASPIRA HYBRID NS60L, dash→space |
| `ASHY-NS40ZL` | `ASHY NS40ZL` | id=685, ws=549000 — ASPIRA HYBRID NS40ZL, dash→space |
| `ASHY-NS70` | `ASHY NS70` | id=689, ws=795423 — ASPIRA HYBRID NS70, dash→space |
| `YTZ5S-S` | `YMF YTZ5S-O` | id=663, ws=187000 (bukan YMF YTZ5S id=662 ws=184000 — YTZ5S-S = WET CHARGED = O variant) |

### Session 2026-08-05 — AMRI ACCU YOGYAKARTA (094/AA-Y/VII/26, sale 22422) — 3-part merge, 39 items, 268.6jt

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `ASMF-NS60L` | `ASMF NS60L` | id=697, ws=676,949. Dash→space (same as `ASMF-NS40ZL`→`ASMF NS40ZL`). Added to code_map.json 2026-08-05. Invoice 631,684 (below ws — volume discount). |
| `INPR-N50ZL` | `INPR-N50ZL` | id=756, ws=763,911. Direct match, dash retained. Not in code_map. |
| `INPR-58024` | `INPR-58024` | id=577, ws=1,361,977. Direct match. INCOE PREMIUM DIN 58024. Invoice 1,262,080 (below ws — legit). |
| `GSHY-NS40` | `GSHY-NS40` | id=473, ws=662,676. Direct, dash retained. |
| `GSHY-NS60LS` | `GSHY-NS60LS` | id=479, ws=770,515. Direct, dash retained. |
| `GSHY-N50Z` | `GSHY-N50Z` | id=470, ws=953,266. Direct, dash retained. |
| `GSMFN-NS60LS` | `GSMFN-NS60LS` | id=498, ws=868,035. Direct, dash retained. |

Merge note: 094/AA-Y split across 3 JSON parts (p1 19 items + p1-continued 18 items + p2 seller MJM BATTERY 2 items). Same customer AMRI ACCU → one Lunas sale. Stated 265,813,634 EXCLUDED page 2 (2.82jt). `claim` field (BD BILAL & ERVAN) = metadata, dropped — not an item. Posted as sum(price×qty) = 268,633,649. Big-volume prices all below admin ws (INGO NS60 @577,850 ws=627,278; GLX-GTZ-5S @98,000 ws=110,000) — legitimate volume pricing, not code errors. AMRI ACCU YOGYAKARTA is a standing langganan getting the cheapest prices — expect its invoices to sit well below admin ws; never flag price mismatch for this customer.

### Session 2026-08-05 — SUNAR JAYA ACCU KEDIRI (175/SJA-K/VII/26, sale 22438) — 43 items, 119.0jt, page 1/2 only

INMF prefix confirmed MIXED (some dash-retained, some space). Added to code_map.json 2026-08-05:

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `INMF-N70Z` | `INMF N70Z` | id=742, ws=1,264,080. Dash→space. |
| `INMF-NX110-5L` | `INMF NX110-5L` | id=786, ws=1,235,100. Dash→space. |
| `INMF-55D23L` | `INMF 55D23L` | id=738, ws=920,460. Dash→space. |
| `INMF-NS60LS` | `INMF NS60LS` | id=749, ws=738,300. Dash→space. |
| `INMF-55559` | `INMF 55559` | id=783, ws=1,118,490. Dash→space. INCOE MF 55559/LN2. |

INMF dash-RETAINED (direct, no map): `INMF-NS40Z` id=745, `INMF-NS40ZL` id=746, `INMF-58024` id=556 (INCOE MF 58024/LN3, ws=1,540,080).

Other new direct matches (no map needed): `GSHY-55D23L` id=467 ws=923,630 | `INGO-NX120-7L` id=552 | `INGO-NX110-5L` id=550 (invoice name typo'd "NX120-5L", code/correct product = NX110-5L) | `INGO-55D23L` id=532 | `INPR-N120` id=753 | `GSMFN-N70Z` id=491 | `GSMFN-NS70` id=777 | `GSMFN-80D26L` id=482.

All prices ≤ admin ws — SUNAR JAYA volume pricing (like AMRI). Posted sum(price×qty)=119,010,795 (stated 119,010,806, 11rp line artifacts). Invoice keys were Indonesian (kode_barang/qty_pcs/harga) — normalize same as ASHY/invoice variants.

### Session 2026-07-01 — 354 NK ACCU MAGETAN (invoice 054/NKA-M/VI/26, sale 17644)

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `ASPR-NS70` | `ASPR NS70` | id=713, ws=783404. Dash→space. |
| `ASPR-N70Z` | `ASPR N70Z` | id=705, ws=938159. Dash→space. |
| `ASPR-NS60` | `ASPR NS60` | id=710, ws=579128. Dash→space. |
| `ASPR-NS60L` | `ASPR NS60L` | id=711, ws=579128. Dash→space. |
| `ASPR-N50Z` | `ASPR N50Z` | id=703, ws=720814. Dash→space. |
| `ASPR-NX110-5L` | `ASPR NX110-5L` | id=699, ws=985617. Dash→space only for ASPR prefix, NX110-5L retains dash. |
| `ASPR-NS40Z` | `ASPR NS40Z` | id=708, ws=538547. Dash→space. |
| `ASHY-NS70` | `ASHY NS70` | id=689, ws=795423. Dash→space. |
| `ASHY-N70Z` | `ASHY N70Z` | id=681, ws=956621. Dash→space. |
| `ASHY-NS60` | `ASHY NS60` | id=686, ws=591282. Dash→space. |
| `ASHY-NS40Z` | `ASHY NS40Z` | id=684, ws=549000. Dash→space. |
| `ASMF-NS40ZL` | `ASMF NS40ZL` | id=695, ws=618821. Dash→space. Already mapped from prev sessions, re-verified. |
| `YUASAMF-NS60` | `YMF NS60` | id=773, ws=818021. YUASAMF → YMF prefix. |
| `YUASAMF-NS60L` | `YMF NS60L` | id=774, ws=818021. YUASAMF → YMF prefix. |
| `GSMFOE-355LN2` | `GSMFOE 355LN2` | id=501, ws=1600115. Dash→space. Direct code match confirmed. |
| `GSMFOE-370LN3` | `GSMFOE 370LN3` | id=502, ws=2257225. Dash→space. Direct code match confirmed. |

### Session 2026-07-01 — TJ BATTERY + D&D ACCU (invoice 232/TJB-S/VI/26 & 050/DD-M/VI/26)

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `YTZ5S-S` | `YMF YTZ5S-O` | id=663, ws=187000. Re-verified: TJ BATTERY invoice price 187000 matches YMF YTZ5S-O wholesale. Previous mapping fixed. |
| `GLX-GM5Z-3B` | `GLX PREMIUM GM5Z-3B` | id=735, ws=113000 (invoice price 102500 — difference because wholesale discount applied). Galaxy GM5Z-3B, bukan GSPK. Already mapped from prev sessions, re-verified. |
| `GSHY-NS40ZL` | `GSHY-NS40ZL` | id=476, ws=709598. Direct match, no map needed. D&D page 1 Lunas. |
| `GSPR-NS70` | `GSPR-NS70` | id=530, ws=1010517. Direct match, no map needed. D&D page 2 Tempo. |

### Session 2026-07-03 — RAJAWALI MOTOR, HS AKI, TJ BATTERY (invoice 046, 244, 233)

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `GSMF-LN3` | `GSMFOE 370LN3` | id=502, ws=2,257,225. **Bukan GSMF-LN3 atau GSMF LN3.** Admin code `GSMFOE 370LN3` (GS Astra MAINTENANCE FREE 370LN3). Harga match 2,257,225. |
| `INPR-NS60L` | `INPR-NS60L` | id=764, ws=614,211. Direct match. |
| `GSMFN-NS40ZL` | `GSMFN-NS40ZL` | id=495, ws=797,475. Direct match (dash retained, like GSHY). |
| `GSMFN-NS60L` | `GSMFN-NS60L` | id=497, ws=868,035. Direct match. |

### Session 2026-07-03 — HERU AKI NGAWI + GARENG AKI SARADAN (invoice 140 & 047)

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `GSHY-NS60` | `GSHY-NS60` | id=477, ws=770515. **Direct match — dash retained!** Beda sama ASHY (dash→space). GSHY di admin pake dash `GSHY-NS60`, bukan space. Gagal pertama karena codemap salah dipetakan ke `"GSHY NS60"` (space). | 
| `INGO-NS70` | `INGO-NS70` | id=548, ws=843192. Direct match. |
| `INGO-NS70L` | `INGO-NS70L` | id=549, ws=843192. Direct match. |

### Session 2026-07-04 — 5-invoice batch (PAK GIONO, PAK MUN, HS AKI, B&B, D&D)

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `INMF-NS60` | `INMF NS60` | id=747, ws=738300. INMF prefix is **mixed** — some retain dash (`INMF-NS40ZL` id=746), some use space (`INMF NS60` id=747). Cek by_code dulu, jangan asumsi semua INMF sama. |
| `12N10` | `PREMIUM 12N10-3B` | **⚠️ DUPLICATE CODE COLLISION — two products share admin code `PREMIUM 12N10-3B`:** id=675 (YUASA, ws=245000) dan id=679 (ALFABATT, ws=165000). by_code dict cuma nyimpen satu (yg terakhir = Alfabatt). Invoice price 245k → Yuasa. **Fix:** jangan rely di by_code untuk kode ini. Pake id langsung: `by_code["12N10"] = next(p for p in all_products if p['id'] == 675)`. |
| `N2` | `NEPEL` | id=614, ws=19000. Non-battery item, kode supplier "N2" → admin "NEPEL" (Besar N2). |
| `D'WATER` | `AIR ZUUR D'WATER` | id=419, ws=15000. Direct match — D'WATER in admin is same product. |
| `GSMF-GT6A` | `GSMF-GT6A` | id=483, ws=178000. **Direct match — dash retained!** Beda sama `GSMF-GTZ-5S` (dash→space `GSMF GTZ5S`). GS Astra MF GT6A pake dash di admin. |
| `SHOOK` | `SHOOK AKI` | id=645, ws=10000. Direct match. |

New customers resolved:
- `PAK MUN MOJOKERTO` → id=186 (Grosir). Search with "MUN" not "PAK" (prefix flood).

Also verified direct matches (no code map needed, but listed for reference):
- `GSPR-NS60` → id=527, ws=749249
- `GSMFN-NS60L` → id=497, ws=868035
- `GSHY-NS60` → id=477, ws=770515
- `MTZ5S` → id=602, ws=185000
- `MTZ6S` → id=603, ws=241000

### Session 2026-07-08 — 3-invoice batch (IMAM ACCU, ANDRI AKI, RAJAWALI MOTOR) — REPOST (previous deleted)

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `INGO-N50` | `INGO-N50` | id=533, ws=668,909. Direct match. N50 = non-Z variant. Repost on sale_id=18603. |
| `INPR-N150` | `INPR-N150` | id=754, ws=2,063,513. Incoe Premium N150. Repost on sale_id=18603. |
| `INGO-N70` | `INGO-N70` | id=537, ws=961,027. Direct match. N70 = non-Z variant (17.1kg/pcs vs NS70). Repost on sale_id=18605. |
| `CHILWEI 12.12` | `CHILWEI 12.12` | id=416, ws=250,000. Direct match. Repost on sale_id=18604. |
| `INGO-NS70` | `INGO-NS70` | id=548, ws=843,192. Direct match, dash retained. Cashback price: 798,518. Repost on sale_id=18603. |
| `INGO-NS60` | `INGO-NS60` | id=545, ws=627,278. Direct match. Cashback price: 592,764. Repost on sale_id=18603. |
| `INGO-N70Z` | `INGO-N70Z` | id=539, ws=1,013,947. Direct match. Cashback price: 961,239. Repost on sale_id=18603. |

Cashback note: Cashback INCOE 460k/92pcs = **5,000/pcs rata ke semua item INCOE** (baik Gold maupun Premium). delta=9 rupiah accepted by server.

### Session 2026-07-27 — BATCH 1: HS AKI + SYILA AKI (249/HS-S & 058/SA-S) — sales 21252–21253

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `YTZ6V-ORI` | `YMF YTZ6V-O` | id=665, ws=233,000. **Bukan YMF YTZ6V** (ws=230,000). YTZ6V-ORI (WET CHARGED) = O variant. Invoice price 233,000 matches. |
| `GSHY-NS60L` | `GSHY-NS60L` | id=478, ws=770,515. **Direct match — dash retained!** GSHY prefix retains dash (same as `GSHY-NS60` id=477). Jangan map ke space. |
| `ASPR-NS40ZL` | `ASPR NS40ZL` | id=709, ws=538,547. Dash→space. Same pattern as other ASPR codes. |
| `ASPR-NS60LS` | `ASPR NS60LS` | id=712, ws=579,128. Dash→space. |
| `D'WATER` | `AIR ZUUR D'WATER` | id=419, ws=15,000. Invoice price 150,000 — legitimate markup (not code mapping error). |

Direct matches re-verified (no map needed):
- `GSMFN-NS60LS` id=497 ws=868,035 | `GSMFN-NS40ZL` id=495 ws=797,475
- `INGO-NS70` id=548 ws=843,192 | `INGO-NS70L` id=549 ws=843,192
- `INGO-NS40L` id=542 ws=542,606 | `INGO-NS60` id=545 ws=627,278
- `GSHY-NS40Z` id=475 ws=709,598 | `GSHY-NS70` id=478 ws=1,039,702
- `GSMF-GT6A` id=483 ws=178,000 — **dash retained** (beda sama GTZ-5S → space)
- `GSMF GTZ6V` id=485 ws=240,000 | `GSMF GTZ5S` id=484 ws=193,000

Free items skipped:
- `KARDUS` — price=0, not in admin by_code → skip silently per free/promo rule.

Customers resolved:
- `SYILA AKI SIDOARJO` → id=181 (Grosir). Already in cache.

### Session 2026-07-10 — 3-invoice batch (PAK ALVIN KEDIRI, ISTANA AKI KEDIRI, DAVY BATTERY KEDIRI) — sales 18946–18948

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `YUASAMF-LN3` | `YMF 566LN3` | id=652, ws=1,501,706. YUASA MF LN3 — YUASAMF → YMF prefix consistent with prior (YUASAMF-NS60 → YMF NS60). Invoice "Yuasa MAINTENANCE FREE LN3" @1,501,706 matches ws exactly. |
| `AMR-LN3` | `AMR-DIN 84` | id=374, ws=1,935,000. AMARON LN3 — LN3 spec for Amaron maps to `AMR-DIN 84` in admin. Bukan `AMR-DIN 66` (ws=1,563,000). |
| `12N10` | `PREMIUM 12N10-3B` (id=675) | Re-verified. Duplicate code collision id=675 (YUASA ws=245k) vs id=679 (ALFABATT ws=165k). Invoice price 245,000 → Yuasa. Override: `by_code["12N10"] = next(p for all_products if p['id'] == 675)` |

Direct matches re-verified (no map needed):
- `INGO-NS40Z` id=543 ws=582,120 | `INGO-NS60` id=545 ws=627,278 | `INGO-NS60L` id=546 ws=627,278
- `INGO-NS40ZL` id=544 ws=582,120 | `INGO-N70Z` id=539 ws=1,013,947 | `INGO-NS70` id=548 ws=843,192
- `INGO-N50Z` id=535 ws=777,571 | `INPR-N100` id=752 ws=1,296,667
- `GSHY-NS40Z` id=475 ws=709,598 | `GSHY-NS60` id=477 ws=770,515 | `GSHY-N70Z` id=472 ws=1,257,026
- `GSMFN-NS40ZL` id=495 ws=797,475 | `GSPR-NS60` id=527 ws=749,249 | `GSPR-NS60LS` id=529 ws=749,249
- `AMR-95D31L` id=370 ws=1,528,000 | `MTX7A` id=607 ws=350,000 | `MTX7D` id=608 ws=335,000
- `MTZ5S` id=602 ws=185,000 | `MTZ6S` id=603 ws=241,000 | `K2` id=600 ws=45,000

### Session 2026-07-27 — BATCH 2: DELTA AKI + AGUNG AKI (179/DA-S & 094/AA-M) — sales 21254–21255

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `INPR-N70Z` | `INPR-N70Z` | id=758, ws=995,065. **Direct match — dash retained.** Same pattern as `INPR-N50Z` (id=755). |
| `GLX-GTZ-5S` | `GLX MF GTZ5S` | id=733, ws=110k. Invoice price 105k — slight discount, not code error. Re-verified. |
| `CHILWEI 12.12` | `CHILWEI 12.12` | id=416, ws=250,000. Direct match. Re-verified. |

Direct matches re-verified: `INGO-N50Z` id=535, `GSMFN-NS40ZL` id=495, `INGO-NS60` id=545.

### Session 2026-07-27 — BATCH 3: PAK ALVIN KEDIRI (134/PA-K) — sale 21257 (23 items, merged pages 1+2)

⚠️ **ADMIN CODES CHANGED since 2026-07-10: 12N10 now has per-brand unique codes, no more duplicate collision!**

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `12N10` | `YUASAPR 12N10-3B` | id=675, ws=245,000. **Admin code CHANGED** from `PREMIUM 12N10-3B` to `YUASAPR 12N10-3B`. Each brand now has unique code: YUASA=`YUASAPR 12N10-3B`, ALFABATT=`ALFAPR 12N10-3B`, GSPK=`GSPK PREMIUM 12N10-3B`. No more by_code collision! |
| `GLX-GOLD GTZ5S` | `GLXG GTZ5S` | id=796, ws=120,000. **New GLX Gold variant** — different product from `GLX MF GTZ5S` (id=733, ws=110k). Invoice name: "AKI GALAXY TEKNOLOGY GELL MF GOLD 5S". Price 105k (below ws — legitimate selling price). |
| `GLX GOLD-GTZ7S` | `GLXG GTZ7S` | id=797, ws=165,000. **New GLX Gold variant GTZ7S.** Invoice price 162,500 (below ws — legitimate). |
| `GLX-GTZ-7S` | `GLX MF GTZ7S` | id=734, ws=162,500. Regular GLX MF variant (not Gold). Invoice price 162,500 = ws. |
| `YB5L-B` | `PREMIUM YB5L-B` | id=677, ws=163,000. Dash→space mapping. |
| `N7` | `N7` | id=611, ws=147,000. **Direct match.** NAGOYA UPS 12V 7AH — non-battery item. |
| `D'WATER1` | `AIR AKI 500ML D'WATER1` | id=418, ws=5,000. Invoice price 50,000 — legitimate markup. |
| `GSMFN-55D23L` | `GSMFN-55D23L` | id=481, ws=1,036,350. Direct match — dash retained. |
| `GSPR-NS40Z` | `GSPR-NS40Z` | id=524, ws=686,039. Direct match — dash retained. |
| `GSMFN-NS60` | `GSMFN-NS60` | id=496, ws=868,035. Direct match — dash retained. |

GLXG series note: Also in admin: `GLXG GT6A` (id=798, ws=140,000). The invoice used `GLX MF-GT6A` (regular, id=732) since name said "GELL MF GT6A" not "GOLD".

INPR series price pattern: INCOE PREMIUM items often have invoice price below admin wholesale (cashback-discounted). Not code mapping errors:
- INPR-N50Z: invoice 734k vs ws 763k
- INPR-NS70: invoice 797k / 814k vs ws 830k
- INPR-N70Z: invoice 957k vs ws 995k

### Session 2026-07-27 — BATCH 4: D&D + B&B + ARKIE BERKAH + PAK MUN (056/DD-M, 111/BB-M, 086/ABA-M, 008/PM-M) — sales 21260–21263

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `GLXGT6A` | `GLX MF-GT6A` | id=732, ws=140,000. Re-verified from Session 2026-06-28. Different from `GLXG GT6A` (Gold, id=798). |

Customers resolved (all cached):
- D&D ACCU MOJOKERTO → id=170 | B&B BATTERY MOJOKERTO → id=159
- ARKIE BERKAH ACCU MOJOKERTO → id=152 | PAK MUN MOJOKERTO → id=186

ARKIE BERKAH cashback: subtotal 10,631,875 - grand_total 10,566,875 = **65,000 cashback** (Incoe 12pcs@60k + GS 1pc@5k). Auto-posted as Biaya Marketing expense id=1838 via `post_expense_after=True`. `_extract_cashback()` detected via subtract-grand_total difference.

### Session 2026-07-27 — BATCH 6: HS AKI + TJ BATTERY + AGUNG AKI (248/HS-S, 236/TJB-S, 093/AA-M) — sales 21304–21308

New verified direct matches (not in code_map, resolved via by_code):

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `INPR-NX120-7L` | `INPR-NX120-7L` | id=596, ws=1,130,823. Direct match — dash retained. Not in code_map. |
| `INPR-NS60` | `INPR-NS60` | id=763, ws=614,211. Direct match — dash retained. Not in code_map. |
| `GSMFN-80D26L` | `GSMFN-80D26L` | id=482, ws=1,594,215. Direct match — dash retained. Not in code_map. |
| `GSMFN-NS40Z` | `GSMFN-NS40Z` | id=494, ws=797,475. Direct match — dash retained. Re-verified. |
| `GSMFN-55D23L` | `GSMFN-55D23L` | id=481, ws=1,036,350. Direct match. Re-verified. |
| `GSPK-GM5Z-3B` | `GSPK-GM5Z-3B` | id=511, ws=145,000. Direct match. **Bukan** `GLX PREMIUM GM5Z-3B` (id=735, ws=113k). GSPK variant. |

Existing code_map entries re-verified:
- `GSMF-GTZ-7V` → `GSMF GTZ7V` (id=487, ws=306,000) — TJ BATTERY
- `GLX-GOLD-GTZ7S` → `GLXG GTZ7S` (id=797, ws=165,000) — TJ BATTERY
- `YTZ5S-S` → `YMF YTZ5S-O` (id=663, ws=187,000) — HS AKI (10 pcs)
- `12N10` → `YUASAPR 12N10-3B` (id=675, ws=245,000) — AGUNG AKI (YUASA brand)
- `CHILWEI 12.12` → direct match (id=416, ws=250,000) — AGUNG AKI page 2
- `D'WATER` → `AIR ZUUR D'WATER` (id=419, ws=15,000) — AGUNG AKI page 2 (invoice 150k markup)

Customer name variant resolved:
- Page 1: `AGUNG AKI MOJOKERTO`, Page 2: `AGUNG AKI MOKER` — same customer id=88. "MOKER" is truncation of "MOJOKERTO".

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `CHILWEI 12.12` | `CHILWEI 12.12` | id=416, ws=250,000. ANDRI AKI invoice price 235,000 — discount. Re-verified. |
| `GSMF-GT6A` | `GSMF-GT6A` | id=483, ws=178,000. ZANU AKI. Direct match, dash retained. |
| `D'WATER` | `AIR ZUUR D'WATER` | id=419, ws=15,000. ZANU AKI invoice 150k — markup (selling price). |

Customers resolved:
- `ANDRI AKI BLITAR` → id=195 (cached)
- `ZANU AKI BLITAR` → id=182 (new, auto-resolved)

### Session 2026-08-05 — 9-invoice batch (WIJAYA, HS, TJ, ADHEEFA, D&D, ISTANA, PAK SAIFUL, DINAMO, MAS FERI) — sales 22402–22411

New verified direct matches (no map needed, resolved via by_code):

| User Code | Admin Code | Notes |
|-----------|-----------|-------|
| `INPR-NX110-5L` | `INPR-NX110-5L` | id=594, ws=1,044,232. Direct — dash retained. Same pattern as `INPR-NX120-7L` (id=596). |
| `INGO-NS60LS` | `INGO-NS60LS` | id=547, ws=627,278. Direct. ⚠️ pitfalls.md ambiguous-table lists NS60LS id=479 — stale; actual id=547. |
| `GSPR-N100` | `GSPR-N100` | id=512, ws=1,545,695. Direct. |
| `GSHY-N70Z` | `GSHY-N70Z` | id=472, ws=1,257,026. Direct. Re-verified. |
| `GSHY-NS70` | `GSHY-NS70` | id=480, ws=1,039,702. Direct. |
| `GSHY-NS40ZL` | `GSHY-NS40ZL` | id=476, ws=709,598. Direct. |
| `INGO-NS40` | `INGO-NS40` | id=541, ws=542,606. Direct. |
| `INGO-NS40Z` | `INGO-NS40Z` | id=543, ws=582,120. Direct. |
| `INPR-NS70` | `INPR-NS70` | id=766, ws=830,689. Direct. |
| `GSMFN-NS60` | `GSMFN-NS60` | id=496, ws=868,035. Direct. |
| `GSPK-GM5Z-3B` | `GSPK-GM5Z-3B` | id=511, ws=145,000. Direct (bukan GLX PREMIUM GM5Z-3B). Re-verified. |
| `N7` | `N7` | id=611, ws=147,000. Direct. NAGOYA UPS 12V 7AH. |

Existing mappings re-verified with below-ws invoice prices (all legit GLX/GS discounts, NOT mapping errors):
- `GLX-GTZ-7S` → `GLX MF GTZ7S` (id=734, ws=162,500). Invoice 150,000 — discount. GELL MF, bukan Gold (GLXG GTZ7S id=797 ws=165k).
- `GLX-GM5Z-3B` → `GLX PREMIUM GM5Z-3B` (id=735, ws=113,000). Invoice 103,000–108,000 range. Consistent discount pattern.
- `GSMF-GTZ-6V` → `GSMF GTZ6V` (id=485, ws=240,000). Invoice 235,000 — discount.
- `GLX-GOLD-GTZ5S` → `GLXG GTZ5S` (id=796, ws=120,000). Invoice 105,000. Re-verified.

New customers resolved (auto-cache):
- `WIJAYA AKI MOJOKERTO` → id=29, WIJAYA AKI MOJOSARI (PAK DONNY), Grosir, MOJOSARI. Search "WIJAYA".
- `ADHEEFA JAYA BATTERY MOJOKERTO` → id=48, ADHEEFA JAYA BATTERY (MAS IMAM), Grosir, MOJOKERTO. (Retail twin id=279 same name — pick Grosir.)
- `PAK SAIFUL TRENGGALEK` → id=36, Grosir, TRENGGALEK. Search "SAIFUL" NOT "PAK" (prefix flood). Careful: "SAIFUL" also returns MAS SAIFUL SN BATTERY KEDIRI id=1261 — exact-name match picks id=36.

### Session 2026-08-07 — 354 NK ACCU MAGETAN (056/NKA-M/VIII/26, sale 22694) + FIYAN JAYA (061/FJA-M/VIII/26, sale 22696)

⭐ **Admin catalog codes CONSOLIDATED to dash-retained.** Confirmed 2026-08-07: ALL prefixes that code_map.json maps to space (`ASPR NS70`, `GSMF GTZ5S`, `ASMF NS40ZL`, etc.) now exist in the live catalog as dash-form (`ASPR-NS70`, `GSMF-GTZ-5S`, `ASMF-NS40ZL`, `ASMF-NX120-7L`) — direct matches, code_map no longer needed for them. code_map.json space-entries are STALE but harmless (they map to non-existent space keys, so `resolve_products` falls through to the live dash code correctly; only raises if neither form exists). **Don't add new space mappings — verify live by_code each session.**

Products that needed explicit admin-ID resolution (not resolvable by code convention):
| User Code | Admin ID | Notes |
|-----------|----------|-------|
| `ASPR-NX120-7L` | id=700 | **No ASPIRA PREMIUM NX120-7L in catalog** — user supplied id=700 (ASPR 95D31L, ws=1,100,818). Invoiced @1,143,901. |
| `FBPR-NX110-5L` | id=434 | No FBPR NX* code; user supplied id=434 `FURUKAWA BATTERY NX110-5L` (ws=1,231,524). Inv @1,258,891. |

Resolution pattern: book the missing code against the exact id the user names — NOT a by_code-override guess.

FIYAN JAYA ACCU MADIUN → id=26 (Grosir, Madiun). CHILWEI 12.12 (id=416) invoice @240k vs ws=250k = discount, not error. Invoice 061 arrived with **no `pelanggan` field** → user supplied it; **never post a missing-customer invoice** → hard STOP + ask (new guard in build_payload — `customer.name is EMPTY`).