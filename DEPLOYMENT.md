# Panduan deployment

## Sebelum dipublikasikan

- Pastikan repository tidak berisi dokumen QA atau data produksi.
- Jangan commit `.env`, password PostgreSQL, API key, atau kredensial lain.
- Folder `.venv`, log, cache, dan artefak target dbt sudah dikecualikan melalui `.gitignore`.
- Gunakan sample sintetis yang tersedia untuk demonstrasi.

## Push ke GitHub

Setelah repository kosong dibuat di GitHub, jalankan dari folder project:

```powershell
git remote add origin https://github.com/farhanbilawa/doc-test.git
git push -u origin main
```

Untuk konteks perusahaan/perbankan, gunakan repository **private** kecuali publikasi sudah disetujui.

## Streamlit Community Cloud

1. Buka Streamlit Community Cloud.
2. Pilih **Create app**.
3. Pilih repository dan branch `main`.
4. Isi main file path dengan `app.py`.
5. Pilih Python 3.12 jika tersedia.
6. Buka **Advanced settings**, lalu isi **Secrets** seperti contoh berikut:

```toml
AI_PROVIDER = "aivene"
AIVENE_ENABLED = "true"
AIVENE_BASE_URL = "https://api.aivene.com/v1"
AIVENE_MODEL = "gpt-6-astra"
AIVENE_API_KEY = "API_KEY_AIVENE_ANDA"
AIVENE_TIMEOUT_SECONDS = "120"
```

7. Jalankan deployment.

`requirements.txt` akan dipasang otomatis oleh platform.

Nilai `AIVENE_MODEL` harus sama persis dengan model ID dalam Aivene Console. Contoh aman untuk Aivene dan Ollama tersedia di `.streamlit/secrets.example.toml`. Jangan membuat atau mengunggah `.streamlit/secrets.toml` berisi API key ke GitHub.

Jangan menaruh URL Aivene dalam `OLLAMA_URL`. Kedua provider memakai protokol berbeda. Aplikasi memilih adapter yang benar melalui `AI_PROVIDER`.

Integrasi cloud memakai endpoint `/api/chat`. Karena Ollama Cloud tidak mendukung structured outputs, aplikasi meminta JSON melalui instruksi prompt dan memvalidasi hasilnya sendiri. Jika request atau parsing gagal, detail kegagalan ditampilkan pada panel pemetaan; aplikasi tidak lagi menyamarkan kegagalan AI sebagai mapping yang berhasil.

## Batasan deployment cloud

Fitur validator inti, parser, mapping manual, tabel hasil, dan ekspor laporan dapat berjalan di cloud. Namun:

- `127.0.0.1:11434` di server cloud bukan Ollama pada laptop pengguna.
- PostgreSQL lokal di laptop tidak dapat dijangkau oleh server cloud.
- Auto-mapping dan penjelasan AI memerlukan Aivene, Ollama Cloud, atau endpoint privat yang dapat dijangkau deployment.
- Jangan membuka Ollama atau PostgreSQL lokal ke internet tanpa autentikasi, TLS, pembatasan jaringan, dan persetujuan keamanan.

Untuk demo cloud tanpa AI, matikan toggle **Fitur AI**. Header standar tetap dipetakan secara deterministik, sedangkan header asing dapat dipetakan manual melalui tabel pemetaan.

## Pilihan penempatan AI

- **Demo paling mudah:** Streamlit Community Cloud + Aivene atau Ollama Cloud. Data terbatas yang digunakan untuk mapping/penjelasan meninggalkan jaringan lokal, sehingga jangan gunakan dokumen bank sebelum ada persetujuan keamanan dan privasi.
- **Data sensitif:** deploy Streamlit dan Ollama pada server internal yang sama atau jaringan privat yang sama. Gunakan URL internal pada `OLLAMA_URL`; API key hanya diperlukan jika gateway internal mewajibkannya.
- **Endpoint Ollama mandiri:** letakkan di belakang HTTPS reverse proxy/API gateway yang memiliki autentikasi. Jangan publikasikan port `11434` mentah ke internet karena API Ollama lokal tidak menyediakan autentikasi bawaan.

## Deployment internal dengan fitur lengkap

Untuk menggunakan Ollama dan database internal, jalankan aplikasi pada workstation atau server internal yang memiliki akses jaringan ke layanan tersebut:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 0.0.0.0
```

Penerapan internal harus mengikuti kebijakan autentikasi, firewall, TLS, secret management, logging, dan klasifikasi data organisasi.
