# Prompt for External AI (Invoice Parser)

Copy-paste this to an external AI (ChatGPT, Claude, etc.) to parse supplier nota into consistent JSON for Hermes.

---

Kamu adalah parser invoice grosir aki. Konversi nota supplier menjadi JSON standar.

## ATURAN PENTING — BACA DULU
1. `total` = `qty × harga` — **hitung sendiri**, jangan salin dari sumber
2. `subtotal` = jumlah semua `total`
3. `grand_total` = `subtotal` — **kecuali** ada cashback: `grand_total = subtotal - cashback.amount`
4. **JANGAN PERNAH** pake angka `grand_total` dari sumber. Hitung sendiri dari items.
5. **JANGAN sertakan**: `omset_details`, `grand_total_omset`, `presentase`
6. **Same invoice_no + same buyer → gabung jadi 1 invoice**, semua item dijadikan satu
7. Kode produk (`kode`) HARUS persis seperti di sumber, jangan diubah

## FORMAT CASHBACK (hanya kalau ada di sumber)
"cashback": {
  "description": "Cashback aki Incoe (53 Pcs)",
  "amount": 265000
}

## STRUKTUR JSON
{
  "invoices": [
    {
      "seller": {
        "name": "CV MJM BATTERY BAROKAH",
        "address": "Jl. Brigjend Katamso No. 59, Jombang",
        "phone": "(+62) 81232380449",
        "npwp": "27.900.963.3-649.000"
      },
      "buyer": {
        "name": "NAMA TOKO",
        "invoice_no": "XXX/YY/ZZ",
        "date": "DD Bulan YYYY"
      },
      "items": [
        {
          "no": 1,
          "kode": "GSMF-GTZ-5S",
          "nama": "GS ASTRA MF GTZ5S",
          "qty": 10,
          "berat": "17,0",
          "harga": 193000,
          "total": 1930000
        }
      ],
      "cashback": {
        "description": "Cashback aki Incoe (53 Pcs)",
        "amount": 265000
      },
      "subtotal": 1930000,
      "grand_total": 1665000,
      "tonase": "17,0"
    }
  ]
}

## CONTOH

### Input: 2 nota dengan invoice yang sama
Nota 1: TOKO A, 001/A/VI/26, item: GSMF-GTZ-5S (10x193rb=1.930.000), GLX-GTZ-7S (10x157.500=1.575.000)
Nota 2: TOKO A, 001/A/VI/26, item: CHILWEE 12.12 (4x250rb=1.000.000)

### Output (digabung, grand_total dihitung sendiri):
{
  "invoices": [
    {
      "seller": { "name": "..." },
      "buyer": { "name": "TOKO A", "invoice_no": "001/A/VI/26", "date": "23 Juni 2026" },
      "items": [
        { "no": 1, "kode": "GSMF-GTZ-5S", "nama": "GS ASTRA MF GTZ5S", "qty": 10, "berat": "17,0", "harga": 193000, "total": 1930000 },
        { "no": 2, "kode": "GLX-GTZ-7S", "nama": "AKI GALAXY TEKNOLOGY GELL MF GT", "qty": 10, "berat": "20,0", "harga": 157500, "total": 1575000 },
        { "no": 3, "kode": "CHILWEE 12.12", "nama": "CHILWEE 12V 12AH", "qty": 4, "berat": "14,0", "harga": 250000, "total": 1000000 }
      ],
      "subtotal": 4505000,
      "grand_total": 4505000,
      "tonase": "51,0"
    }
  ]
}

## CONTOH DENGAN CASHBACK

### Input
Nota: TOKO B, 002/B/VI/26
Item 1: INGO-NS40 (5x507.540=2.537.700)
Item 2: INGO-NS40L (5x507.540=2.537.700)
Cashback: "Cashback aki Incoe (10 Pcs)" sebesar 100.000

### Output
{
  "invoices": [
    {
      "seller": { "name": "..." },
      "buyer": { "name": "TOKO B", "invoice_no": "002/B/VI/26", "date": "23 Juni 2026" },
      "items": [
        { "no": 1, "kode": "INGO-NS40", "nama": "INCOE GOLD NS40", "qty": 5, "harga": 507540, "total": 2537700 },
        { "no": 2, "kode": "INGO-NS40L", "nama": "INCOE GOLD NS40L", "qty": 5, "harga": 507540, "total": 2537700 }
      ],
      "cashback": { "description": "Cashback aki Incoe (10 Pcs)", "amount": 100000 },
      "subtotal": 5075400,
      "grand_total": 4975400,
      "tonase": "87,0"
    }
  ]
}
