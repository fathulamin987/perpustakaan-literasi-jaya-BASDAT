# 📚 Sistem Informasi Perpustakaan Literasi Jaya

Aplikasi web manajemen perpustakaan modern, profesional, dan responsif yang dibangun dengan **Python Flask** dan terintegrasi langsung dengan database relasional **MySQL / MariaDB via XAMPP**.

---

## 🌟 Fitur Utama & Desain

1. **Dashboard Interaktif & Realtime**
   - Kartu statistik KPI: Total Buku, Stok Eksemplar, Anggota Terdaftar, Peminjaman Berjalan, dan Keterlambatan.
   - Grafik Interaktif (Chart.js):
     - **Buku Paling Populer** (bersumber langsung dari View `v_bukupopuler`).
     - **Komposisi Kategori Buku** (doughnut chart).
   - Widget Peminjaman Jatuh Tempo Terdekat (bersumber dari Stored Procedure `SP_LaporanBukuBelumKembali`).
   - Widget Anggota Paling Aktif & Bebas Denda (bersumber dari View `v_anggotaaktif`).
   - Sirkulasi Transaksi Terkini dengan tombol aksi pengembalian cepat.

2. **Katalog & Inventaris Buku (CRUD Lengkap)**
   - Daftar koleksi buku lengkap dengan filter kategori, status ketersediaan stok, dan pencarian cepat (judul, penulis, ISBN).
   - Tambah buku baru dengan auto-generate ID `BK00X`.
   - Edit informasi buku (judul, penulis, penerbit, tahun terbit, ISBN, stok, kategori).
   - Hapus buku dengan validasi pengaman (buku yang sedang dipinjam terlindungi dari penghapusan).

3. **Manajemen Anggota (Member Management)**
   - Pencarian anggota berdasarkan nama, email, nomor HP, atau alamat.
   - Pendaftaran anggota baru dengan auto-generate ID `AGT00X`.
   - Edit profil anggota.
   - **Kartu Anggota Digital**: Fitur preview kartu tanda anggota perpustakaan yang siap dicetak langsung (`Print Ready`).

4. **Sirkulasi Transaksi (Peminjaman & Pengembalian)**
   - **Form Peminjaman Terintegrasi Stored Procedure**: Memanggil langsung `SP_PinjamBuku(p_ID_Buku, p_ID_Anggota)` yang otomatis menghasilkan ID transaksi (`PJMxxx`), mengurangi stok buku, dan menetapkan tanggal jatuh tempo 7 hari ke depan.
   - **Pengembalian Cepat Terintegrasi Stored Procedure**: Memanggil `SP_KembalikanBuku(p_ID_Peminjaman)` yang otomatis menghitung apakah pengembalian tepat waktu atau terlambat, mengupdate tanggal pengembalian, dan menambah kembali stok buku.
   - Filter transaksi berdasarkan status: *Semua*, *Dipinjam*, *Dikembalikan*, *Terlambat*.

5. **Laporan & Analitik Basis Data (Views & Stored Procedures)**
   - **Laporan 1**: Buku Belum Dikembalikan (`CALL SP_LaporanBukuBelumKembali()`).
   - **Laporan 2**: Buku Terpopuler (`SELECT * FROM v_bukupopuler`).
   - **Laporan 3**: Anggota Teladan / Bebas Denda (`SELECT * FROM v_anggotaaktif`).
   - **Laporan 4**: Riwayat Peminjaman Terlambat (`SELECT * FROM v_peminjamanterlambat`).
   - Fitur **Export CSV** untuk setiap laporan.
   - Fitur **Cetak Laporan Resmi** yang diformat khusus untuk kertas cetak.

6. **Status & Diagnostik Database XAMPP**
   - Halaman inspeksi parameter koneksi server (Host, Port, User, Versi MariaDB/MySQL).
   - Ringkasan objek database: Base Tables, Views, Stored Procedures, dan Triggers (`TR_InsertStatusPeminjaman` & `TR_UpdateStatusPeminjaman`).

---

## 🛠️ Persyaratan Sistem

- **Python**: Versi 3.8 ke atas (sudah terinstal Python 3.12).
- **XAMPP**: Modul Apache dan MySQL aktif.
- **Database**: `perpustakaanliterasijaya` (berada di file `perpustakaanliterasijaya.sql`).

---

## 🚀 Cara Menjalankan Aplikasi

### Cara 1: Menggunakan File Batch (Paling Mudah)
Cukup klik dua kali file **`run.bat`**. Browser akan otomatis terbuka mengarah ke `http://127.0.0.1:5000`.

### Cara 2: Melalui Terminal / Command Prompt
1. Pastikan **MySQL di XAMPP** sudah berjalan (`Start` pada XAMPP Control Panel).
2. Buka terminal di folder project ini:
   ```bash
   cd "c:\Users\Fathul Amin\OneDrive\Documents\basis data 1\perpustakaan-basdat"
   ```
3. Install dependensi (jika belum):
   ```bash
   pip install -r requirements.txt
   ```
4. Jalankan aplikasi Flask:
   ```bash
   python app.py
   ```
5. Buka browser dan akses:
   ```
   http://127.0.0.1:5000
   ```

---

## 🗄️ Struktur Basis Data yang Digunakan

- **Tabel**:
  - `buku`: Menyimpan data buku, penulis, penerbit, tahun, ISBN, stok, dan kategori.
  - `anggota`: Menyimpan identitas peminjam, kontak, dan tanggal daftar.
  - `peminjaman`: Menyimpan sirkulasi peminjaman dengan relasi ke buku dan anggota.
- **Stored Procedures**:
  - `SP_PinjamBuku(ID_Buku, ID_Anggota)`: Memvalidasi stok dan mencatat peminjaman baru.
  - `SP_KembalikanBuku(ID_Peminjaman)`: Memvalidasi denda/keterlambatan dan memulihkan stok.
  - `SP_LaporanBukuBelumKembali()`: Mengambil daftar buku yang belum dikembalikan urut jatuh tempo.
- **Views**:
  - `v_bukupopuler`: Buku yang dipinjam $\ge$ 2 kali.
  - `v_anggotaaktif`: Anggota dengan peminjaman aktif tanpa riwayat terlambat.
  - `v_peminjamanterlambat`: Transaksi yang berstatus terlambat.
- **Triggers**:
  - `TR_InsertStatusPeminjaman` & `TR_UpdateStatusPeminjaman`: Pengubah status otomatis ke `Terlambat` jika tanggal jatuh tempo telah lewat.
