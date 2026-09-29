# Demo dbt ke PostgreSQL

Project terpisah ini membuktikan pola koneksi dbt ke PostgreSQL tanpa menyimpan password di source code.

## 1. Pasang adapter

Jalankan dari folder utama aplikasi:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dbt-postgres.txt
```

## 2. Isi koneksi hanya untuk sesi PowerShell aktif

```powershell
$env:DBT_PG_HOST = "127.0.0.1"
$env:DBT_PG_PORT = "5432"
$env:DBT_PG_USER = "postgres"
$env:DBT_ENV_SECRET_PG_PASSWORD = Read-Host "Password PostgreSQL"
$env:DBT_PG_DATABASE = "postgres"
$env:DBT_PG_SCHEMA = "public"
```

Password tidak ditulis ke file dan akan hilang saat jendela PowerShell ditutup. Untuk penggunaan perusahaan, gunakan akun database read-only atau schema development, bukan kredensial produksi.

## 3. Uji koneksi

```powershell
cd dbt_postgres_demo
..\.venv\Scripts\dbt.exe debug --profiles-dir .
```

Hasil yang dicari adalah `Connection test: OK connection ok` dan `All checks passed!`.

## 4. Jalankan query tanpa membuat tabel/view

```powershell
..\.venv\Scripts\dbt.exe show --inline "select current_database(), current_user, current_schema(), current_timestamp" --profiles-dir .
```

## 5. Membuat model demo (opsional dan menulis ke database)

Perintah berikut membuat view `connection_check`, sehingga hanya jalankan pada schema development yang memang boleh ditulis:

```powershell
..\.venv\Scripts\dbt.exe build --profiles-dir .
```

Setelah build, artefak yang dapat diunggah ke Validator Deployment QA berada di:

- `target/manifest.json`
- `target/run_results.json`

Untuk Snowflake, BigQuery, SQL Server, Databricks, Oracle, atau database lain, pola project-nya sama tetapi paket adapter dan field koneksinya berbeda.

