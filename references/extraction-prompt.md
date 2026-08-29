# Extraction Prompt — Invoice Image → JSON

Prompt untuk ekstrak data nota/faktur dari gambar ke format JSON. Copy paste ini ke chat waktu kirim foto nota.

## Prompt

```
Ekstrak data dari gambar nota ini ke JSON dengan format berikut. 
Hanya output JSON, tanpa penjelasan. Hapus field yg gak ada datanya (null/undefined).

{
  "customer": {
    "name": "nama customer"
  },
  "invoice": {
    "invoice_number": "nomor nota",
    "invoice_date": "YYYY-MM-DD",
    "due_date": null
  },
  "items": [
    {
      "product_code": "kode produk dari nota",
      "product_name": "nama produk",
      "qty": jumlah,
      "unit_price": harga satuan,
      "line_total": total baris (opsional)
    }
  ],
  "summary": {
    "grand_total": total_akhir
  }
}

Aturan:
- Gunakan product_code persis seperti di nota — jangan ubah formatnya.
- unit_price dan grand_total dalam Rupiah, tanpa titik/koma (integer).
- Kalau ada diskon/cashback, kurangi dari grand_total jangan bikin field terpisah.
- **ABAIIKAN** item yang mengandung kata "TAGIHAN" / "ITAGIHAN" / "PIUTANG" — itu tagihan nota lama, sales udah terjadi, jangan dimasukin ke items.
- Kalau nota multi halaman, kombinasi semua item jadi satu array items.
- invoice_date pake format YYYY-MM-DD.
- Kalau ada "INVOICE" atau "FAKTUR" atau "NOTA" ditulis sebagai invoice_number.
```

## Output example

```json
{
  "customer": {
    "name": "HS AKI SIDOARJO"
  },
  "invoice": {
    "invoice_number": "063/PS-T/VI/26",
    "invoice_date": "2026-06-24",
    "due_date": null
  },
  "items": [
    {"product_code": "GLX MF GTZ5S", "product_name": "GS HYBRID GTZ5S", "qty": 10, "unit_price": 288800},
    {"product_code": "GSMF NS40ZL", "product_name": "GS MF NS40ZL", "qty": 5, "unit_price": 425000}
  ],
  "summary": {
    "grand_total": 5013000
  }
}
```

## Notes

- Selalu kirim prompt INI BESERTA GAMBARNYA dalam satu pesan.
- Kalau hasil OCR kelihatan aneh (angka ngawur, barang ilang), bilang aja "hasil OCR kacau" nanti diperbaiki manual.
- JSON minimal: `customer.name`, `invoice.invoice_number`, `invoice.invoice_date`, `items[].product_code`, `items[].qty`, `items[].unit_price`, `summary.grand_total`.
