# Demo pemetaan otomatis

`qa_header_acak.csv` sengaja menggunakan header yang tidak termasuk alias bawaan aplikasi:

- `TBL_OBJ`
- `FIELD_NM`
- `TARGET_FMT`
- `REQUIRED_FLAG`
- `UNIQUE_FLAG`
- `EXPECTED_ROWS`
- `OBSERVED_ROWS`
- `FULL_LAYOUT`

Unggah CSV ini bersama `../manifest.json` dan `../run_results.json`. Qwen lokal akan menyarankan mapping, lalu aplikasi menampilkan tabel mapping yang dapat diperiksa atau dikoreksi sebelum tombol **Jalankan Validasi** ditekan.

