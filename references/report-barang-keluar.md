# Barang Keluar Report — Kiriman Luar Kota Sales

`report_barang_keluar.php` has a branch filter dropdown. After DB rename, the `branches` table has `Kiriman Luar Kota` instead of `OUT_OF_TOWN`. The URL parameter `branch=Kiriman+Luar+Kota` filters by `s.branch_name = 'Kiriman Luar Kota'` — which matches all Kiriman Luar Kota sales.

**URL:**
```
https://mjmbattery.com/admin/report_barang_keluar.php?start_date=2026-07-06&end_date=2026-07-06&branch=Kiriman+Luar+Kota
```

Use `branch=Kiriman+Luar+Kota`. The branch dropdown also shows "Kiriman Luar Kota" after the DB rename.

The report shows all Kiriman Luar Kota sales for that date range, including Custom Grosir wholesale sales. Items get HPP allocated from inventory batches (or [Fallback Purchase Items] if no batch exists).
