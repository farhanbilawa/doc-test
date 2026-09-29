# Uji blind mapping model AI

Kasus ini menguji generalisasi model AI. Seluruh header sengaja:

- tidak tercantum dalam alias bawaan aplikasi;
- tidak disebut sebagai contoh dalam prompt mapping;
- berbeda dari sample `TBL_OBJ`, `FIELD_NM`, dan header standar;
- hanya diberi maksimal dua contoh nilai oleh aplikasi.

## Cara menguji

1. Pastikan **Fitur AI Ollama** aktif dan status model siap.
2. Unggah `qa_blind_mapping.csv` sebagai dokumen QA.
3. Unggah `../manifest.json` sebagai `manifest.json`.
4. Opsional: unggah `../run_results.json` dan `../schema.yml`.
5. Buka tabel **Pemetaan kolom QA otomatis** sebelum menjalankan validasi.

## Kunci jawaban yang diharapkan

| Header asing | Mapping yang benar |
|---|---|
| `ASSET_SCOPE` | Nama Model/Tabel |
| `MEMBER_TOKEN` | Nama Kolom |
| `PHYSICAL_FORM` | Tipe Data Diharapkan |
| `PRESENCE_GUARD` | Wajib Terisi (Not Null) |
| `COLLISION_GUARD` | Harus Unik |
| `PLANNED_VOLUME` | Jumlah Baris Diharapkan |
| `SEEN_VOLUME` | Jumlah Baris Aktual |
| `AUTHORITATIVE_BLUEPRINT` | Skema Lengkap |
| `REVIEW_TICKET` | Abaikan |
| `OWNER_NOTE` | Abaikan |

## Cara menilai

- **9–10 benar:** model memahami struktur dengan baik.
- **7–8 benar:** model memahami sebagian, tetapi mapping tetap perlu dikoreksi.
- **0–6 benar:** respons model belum cukup andal untuk format ini.

Dua kolom pengalih (`REVIEW_TICKET` dan `OWNER_NOTE`) memang harus diabaikan. Setelah mapping benar, validasi sengaja menghasilkan `FAIL` untuk `birth_date` karena QA meminta `DATE`, sedangkan manifest berisi `STRING`. Kolom `religion_code` juga seharusnya muncul sebagai peringatan karena QA menyatakan skema lengkap.
