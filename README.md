# Validator Deployment QA

MVP Streamlit lokal untuk membandingkan requirement QA dengan metadata dbt dan bukti eksekusi opsional sebelum deployment. Aplikasi ini merupakan **alat bantu validasi dan pengambilan keputusan**; aplikasi tidak mengesahkan deployment produksi secara otomatis. Keputusan akhir tetap berada pada Data Engineer.

## Fungsi aplikasi

Aplikasi mengubah dokumen QA menjadi model data yang tidak bergantung pada format, membaca artefak dbt, lalu menjalankan aturan perbandingan deterministik. Hasil menggunakan status `PASS`, `WARNING`, atau `FAIL` dan selalu disertai pesan “Validasi selesai. Peninjauan engineer tetap diperlukan.”

Alur utama berjalan sepenuhnya secara lokal dan tidak membutuhkan database, API cloud, atau LLM.

## Arsitektur

```text
Berkas QA -> parser format -> QARequirement --+
                                             +-> MatchingEngine -> hasil/anomali -> Streamlit/ekspor
Berkas dbt -> parser artefak -> DBTProject ---+
                                                      |
                                             penjelasan Ollama lokal opsional
```

- `app.py`: pengaturan UI Streamlit, tampilan, dan ekspor CSV/JSON/PDF.
- `src/models`: model data Pydantic yang sudah dinormalisasi.
- `src/parsers`: parser CSV, Excel, Word, PDF, manifest, hasil eksekusi, dan schema YAML.
- `src/validator`: aturan tipe data, validasi deterministik, pencocokan, dan pemilihan anomali.
- `src/services`: klien Ollama lokal dan pembuat laporan PDF.
- `src/utils`: utilitas input, konfigurasi, dan normalisasi.
- `tests`: rangkaian pengujian pytest offline.
- `sample_data`: data demonstrasi yang sepenuhnya sintetis.

Struktur modul menyediakan titik pengembangan untuk adapter CI/CD, orchestrator, validasi database, audit trail, dan pemetaan semantik tanpa menggabungkannya ke MVP ini.

## Instalasi

Jalankan melalui Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Python 3.11 atau lebih baru disarankan. Workspace ini telah diverifikasi menggunakan Python 3.13.

## Menjalankan aplikasi

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Streamlit biasanya tersedia di <http://localhost:8501>. Untuk demonstrasi cepat, unggah berkas dari folder `sample_data/`.

## Menjalankan pengujian

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Pengujian hanya menggunakan fixture sintetis lokal dan tidak membutuhkan akses internet.

## Format QA yang didukung

- Tabel CSV dengan alias header umum.
- Workbook `.xlsx` dan `.xls`; seluruh lembar diperiksa.
- Tabel `.docx` dan definisi teks ringkas yang umum.
- PDF berbasis teks dengan definisi ringkas yang umum.

Alias tidak peka huruf besar-kecil mencakup Model/Table, Column/Field, Data Type/Datatype, Nullable/Not Null, Unique, Test/Validation, dan jumlah baris expected/actual. Karena format dokumen dapat sangat bervariasi, bukti yang tidak dikenali atau tidak tersedia akan ditandai sebagai peringatan jika perbandingan tidak dapat dilakukan secara meyakinkan.

### Pemetaan header otomatis

Untuk CSV, Excel, dan tabel Word, aplikasi memeriksa header segera setelah berkas diunggah. Alias umum dipetakan secara deterministik. Header yang tidak dikenal dikirim ke Qwen lokal bersama maksimal dua contoh nilai pendek untuk memperoleh saran mapping. Hasilnya ditampilkan dalam tabel **Pemetaan kolom QA otomatis** dan dapat dikoreksi pengguna sebelum validasi. Dokumen lengkap tidak dikirim ke model dan keputusan `PASS`, `WARNING`, atau `FAIL` tetap dibuat oleh mesin aturan deterministik.

Contoh header internal seperti `TBL_OBJ`, `FIELD_NM`, atau `TARGET_FMT` tersedia dalam `sample_data/auto_mapping_case/`.

## Artefak dbt yang didukung

- Wajib: `manifest.json`, dibaca secara defensif terhadap variasi struktur manifest.
- Opsional: `run_results.json`.
- Opsional: `schema.yml` atau `properties.yml`, termasuk `tests`, `data_tests`, dan constraint umum.

## Aturan validasi

1. Keberadaan model.
2. Keberadaan kolom.
3. Perbandingan tipe data: sama persis, kompatibel/perlu ditinjau, atau tidak cocok.
4. Pengujian wajib `not_null`.
5. Pengujian wajib `unique`.
6. Keberadaan pengujian dbt lain yang dapat dipetakan.
7. Hasil eksekusi pengujian dbt opsional.
8. Konsistensi sumber dan target jika dapat dibandingkan.
9. Kolom tak terduga apabila QA menyatakan skema lengkap.
10. Bukti tipe data QA yang tidak tersedia.
11. Toleransi jumlah baris yang dapat dikonfigurasi.

Status keseluruhan mengikuti tingkat temuan tertinggi: satu kegagalan deterministik menghasilkan `FAIL`; jika tidak ada kegagalan tetapi terdapat peringatan, hasilnya `WARNING`; selebihnya `PASS`. Status ini bukan keputusan deployment.

## Konfigurasi

`config.yaml` mengatur kelompok dan kompatibilitas tipe data, kolom yang diabaikan, ambang jumlah baris, ukuran maksimum unggahan, dan pengaturan Ollama opsional. Ambang jumlah baris menggunakan persentase. Perbedaan di bawah ambang gagal tetap menjadi peringatan kecuali pencocokan persis diaktifkan.

## Integrasi Ollama

Ollama aktif secara default dan menggunakan model lokal `qwen3.5:4b`. Pengaturan dapat diubah melalui sidebar dan `config.yaml`, termasuk URL, model, dan timeout. Hanya temuan yang sudah dinormalisasi beserta bukti terkait yang dikirim ke endpoint lokal—bukan dokumen asli. Penjelasan dibuat sesuai permintaan melalui tombol **Buat penjelasan AI** pada setiap temuan agar halaman tidak menjalankan banyak request secara bersamaan. Jika Ollama tidak tersedia, UI menampilkan “Penjelasan AI tidak tersedia.” dan validasi deterministik tetap berjalan. AI tidak pernah menentukan atau mengubah status validasi.

## Ekspor laporan

Hasil dapat diunduh sebagai CSV, JSON, atau PDF. Seluruh label laporan menggunakan Bahasa Indonesia. PDF dibuat langsung di memori dan hanya memuat metadata ringkas serta hasil validasi yang sudah dinormalisasi.

## Pertimbangan keamanan

- Berkas unggahan diproses di memori dan tidak disimpan permanen oleh aplikasi.
- Tidak ada telemetry, analitik eksternal, LLM cloud, atau secret yang ditanam di kode.
- Log hanya mencatat nama berkas dan jumlah data, bukan isi dokumen.
- Hasil ekspor memuat temuan dan nama berkas, bukan dokumen asli.
- Gunakan workstation, akses, retensi, dan prosedur peninjauan yang telah disetujui organisasi sebelum memproses materi sensitif.

## Keterbatasan

- Parser QA bersifat heuristik; layout yang sangat khusus mungkin membutuhkan profil parser tersendiri.
- PDF hasil scan atau berbasis gambar membutuhkan OCR yang belum disertakan.
- Tipe data bergantung pada metadata yang tersedia dalam artefak dbt atau schema YAML; aplikasi tidak menyimpulkan tipe dari compiled SQL.
- Jumlah baris aktual hanya dibandingkan jika tercantum dalam input QA; MVP tidak melakukan query database.
- Deteksi skema lengkap harus dinyatakan eksplisit (`Complete Schema = Yes`) untuk mencegah temuan kolom tambahan yang keliru.
- Nama pengujian dbt generik atau kustom dapat diperiksa keberadaannya, tetapi kesetaraan semantiknya belum disimpulkan.
- Validasi ukuran berkas berada pada tingkat aplikasi; environment deployment sebaiknya juga mengatur batas unggahan Streamlit.

## Pengembangan berikutnya

Milestone berikut yang disarankan adalah profil template QA yang dapat dikonfigurasi dan adapter CI yang menghasilkan laporan JSON sebagai artefak peninjauan. Pengembangan selanjutnya dapat menambahkan webhook/orchestration, eksekusi dbt otomatis, query jumlah baris database, audit trail, workflow persetujuan, dan pemetaan semantik konservatif tanpa menggantikan mesin deterministik.

## Demo koneksi dbt ke PostgreSQL

Folder `dbt_postgres_demo/` menyediakan project dbt opsional untuk menguji PostgreSQL lokal. Adapter dipisahkan dalam `requirements-dbt-postgres.txt` agar aplikasi validator utama tetap ringan. Seluruh kredensial dibaca melalui environment variable dan password tidak ditulis ke repository. Ikuti petunjuk dalam `dbt_postgres_demo/README.md`.
