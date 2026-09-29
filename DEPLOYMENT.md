# Panduan deployment

## Sebelum dipublikasikan

- Pastikan repository tidak berisi dokumen QA atau data produksi.
- Jangan commit `.env`, password PostgreSQL, API key, atau kredensial lain.
- Folder `.venv`, log, cache, dan artefak target dbt sudah dikecualikan melalui `.gitignore`.
- Gunakan sample sintetis yang tersedia untuk demonstrasi.

## Push ke GitHub

Setelah repository kosong dibuat di GitHub, jalankan dari folder project:

```powershell
git remote add origin https://github.com/USERNAME/qa-deployment-validator.git
git push -u origin main
```

Untuk konteks perusahaan/perbankan, gunakan repository **private** kecuali publikasi sudah disetujui.

## Streamlit Community Cloud

1. Buka Streamlit Community Cloud.
2. Pilih **Create app**.
3. Pilih repository dan branch `main`.
4. Isi main file path dengan `app.py`.
5. Pilih Python 3.12 jika tersedia.
6. Jalankan deployment.

`requirements.txt` akan dipasang otomatis oleh platform.

## Batasan deployment cloud

Fitur validator inti, parser, mapping manual, tabel hasil, dan ekspor laporan dapat berjalan di cloud. Namun:

- `127.0.0.1:11434` di server cloud bukan Ollama pada laptop pengguna.
- PostgreSQL lokal di laptop tidak dapat dijangkau oleh server cloud.
- Auto-mapping Qwen dan penjelasan AI akan tidak tersedia kecuali Ollama ditempatkan pada endpoint privat yang memang dapat dijangkau deployment.
- Jangan membuka Ollama atau PostgreSQL lokal ke internet tanpa autentikasi, TLS, pembatasan jaringan, dan persetujuan keamanan.

Untuk demo cloud tanpa AI, matikan toggle **Penjelasan AI Ollama**. Header standar tetap dipetakan secara deterministik, sedangkan header asing dapat dipetakan manual melalui tabel pemetaan.

## Deployment internal dengan fitur lengkap

Untuk menggunakan Ollama dan database internal, jalankan aplikasi pada workstation atau server internal yang memiliki akses jaringan ke layanan tersebut:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 0.0.0.0
```

Penerapan internal harus mengikuti kebijakan autentikasi, firewall, TLS, secret management, logging, dan klasifikasi data organisasi.

