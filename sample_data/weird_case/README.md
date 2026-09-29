# Demo aneh / kasus khusus

Semua data di folder ini sintetis.

Unggah:

1. `qa_weird.csv` sebagai QA document.
2. `manifest_weird.json` sebagai manifest.
3. `run_results_weird.json` sebagai artifact opsional.
4. `schema_weird.yml` sebagai schema/properties opsional.

Kasus yang sengaja dibuat:

- Selisih row count 8% (FAIL dengan konfigurasi default).
- `INTEGER` versus `BIGINT` (compatible/WARNING).
- `DATE` versus `TIMESTAMP` (compatible/WARNING).
- Presisi `DECIMAL(18,2)` versus `DECIMAL(12,2)` (FAIL).
- Kolom `legacy_flag` hilang (FAIL).
- Kolom `debug_payload` tidak diharapkan (WARNING).
- Model `dim_orphan` hilang (FAIL).
- Model `incomplete_model` ada tetapi tanpa metadata kolom (FAIL).
- Test `unique` memiliki 37 failure walaupun QA menyatakan PASS (FAIL).
- Test `accepted_values` berstatus `skipped` (WARNING).
- `schema_weird.yml` menambahkan constraint `not_null` untuk `customer_id`.

Untuk melihat perbedaan evidence, jalankan sekali tanpa schema YAML, lalu jalankan lagi dengan `schema_weird.yml`.
