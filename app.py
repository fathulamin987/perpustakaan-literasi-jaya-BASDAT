"""
=============================================================================
SISTEM INFORMASI PERPUSTAKAAN LITERASI JAYA
Aplikasi Web Antarmuka Basis Data MySQL (XAMPP) menggunakan Python Flask
=============================================================================
"""

import io
import csv
from datetime import date, datetime
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from config import Config
from database import query_db, execute_db, call_procedure, check_db_health

app = Flask(__name__)
app.config.from_object(Config)


# =============================================================================
# FILTER TANGGAL DAN STATUS JINJA2 (MUDAH DIBACA)
# =============================================================================

@app.template_filter('format_date')
def format_date(value, fmt='%d %b %Y'):
    """Format tanggal standar Indonesia: 14 Nov 2026"""
    if not value:
        return '-'
    if isinstance(value, (datetime, date)):
        return value.strftime(fmt)
    try:
        dt = datetime.strptime(str(value), '%Y-%m-%d')
        return dt.strftime(fmt)
    except Exception:
        return str(value)


@app.template_filter('status_badge')
def status_badge(status):
    """Memberi class CSS status yang sesuai"""
    badges = {
        'Dipinjam': 'status-pill dipinjam',
        'Dikembalikan': 'status-pill dikembalikan',
        'Terlambat': 'status-pill terlambat'
    }
    return badges.get(status, 'status-pill dipinjam')


# =============================================================================
# CLASS SERVICE (FUNGSI-FUNGSI LOGIKA DATABASE)
# Dibuat terstruktur per tabel dan objek database agar mudah dipahami
# =============================================================================

class BukuService:
    """Mengelola operasi tabel 'buku' (CRUD & Stok)"""

    @staticmethod
    def get_all(search='', kategori='', stok=''):
        sql = "SELECT * FROM buku WHERE 1=1"
        params = []
        if search:
            sql += " AND (Judul LIKE %s OR Penulis LIKE %s OR Penerbit LIKE %s OR ISBN LIKE %s OR ID_Buku LIKE %s)"
            p = f"%{search}%"
            params.extend([p, p, p, p, p])
        if kategori:
            sql += " AND Kategori = %s"
            params.append(kategori)
        if stok == 'tersedia':
            sql += " AND Jumlah_Stok > 0"
        elif stok == 'habis':
            sql += " AND Jumlah_Stok = 0"
        sql += " ORDER BY ID_Buku ASC"
        return query_db(sql, params)

    @staticmethod
    def get_categories():
        return query_db("SELECT DISTINCT Kategori FROM buku WHERE Kategori IS NOT NULL AND Kategori != '' ORDER BY Kategori ASC")

    @staticmethod
    def generate_next_id():
        row = query_db("SELECT MAX(CAST(SUBSTRING(ID_Buku, 3) AS UNSIGNED)) as max_id FROM buku", one=True)
        next_num = (row['max_id'] or 0) + 1 if row else 1
        return f"BK{next_num:03d}"

    @staticmethod
    def insert(id_buku, judul, penulis, penerbit, tahun, isbn, stok, kategori):
        sql = """
            INSERT INTO buku (ID_Buku, Judul, Penulis, Penerbit, Tahun_Terbit, ISBN, Jumlah_Stok, Kategori)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        return execute_db(sql, (id_buku, judul, penulis, penerbit, int(tahun), isbn, int(stok), kategori))

    @staticmethod
    def update(id_buku, judul, penulis, penerbit, tahun, isbn, stok, kategori):
        sql = """
            UPDATE buku 
            SET Judul=%s, Penulis=%s, Penerbit=%s, Tahun_Terbit=%s, ISBN=%s, Jumlah_Stok=%s, Kategori=%s
            WHERE ID_Buku=%s
        """
        return execute_db(sql, (judul, penulis, penerbit, int(tahun), isbn, int(stok), kategori, id_buku))

    @staticmethod
    def delete(id_buku):
        cek = query_db("SELECT COUNT(*) as cnt FROM peminjaman WHERE ID_Buku = %s", (id_buku,), one=True)
        if cek and cek['cnt'] > 0:
            return False, f"Buku [{id_buku}] tidak dapat dihapus karena tercatat dalam {cek['cnt']} riwayat peminjaman."
        execute_db("DELETE FROM buku WHERE ID_Buku = %s", (id_buku,))
        return True, f"Buku [{id_buku}] berhasil dihapus dari database."


class AnggotaService:
    """Mengelola operasi tabel 'anggota'"""

    @staticmethod
    def get_all(search=''):
        sql = "SELECT * FROM anggota WHERE 1=1"
        params = []
        if search:
            sql += " AND (Nama_Anggota LIKE %s OR Email LIKE %s OR No_Telepon LIKE %s OR ID_Anggota LIKE %s)"
            p = f"%{search}%"
            params.extend([p, p, p, p])
        sql += " ORDER BY ID_Anggota ASC"
        return query_db(sql, params)

    @staticmethod
    def generate_next_id():
        row = query_db("SELECT MAX(CAST(SUBSTRING(ID_Anggota, 4) AS UNSIGNED)) as max_id FROM anggota", one=True)
        next_num = (row['max_id'] or 0) + 1 if row else 1
        return f"AGT{next_num:03d}"

    @staticmethod
    def insert(id_anggota, nama, alamat, no_telp, email, tanggal_daftar):
        sql = """
            INSERT INTO anggota (ID_Anggota, Nama_Anggota, Alamat, No_Telepon, Email, Tanggal_Daftar)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return execute_db(sql, (id_anggota, nama, alamat, no_telp, email, tanggal_daftar))

    @staticmethod
    def update(id_anggota, nama, alamat, no_telp, email, tanggal_daftar):
        sql = """
            UPDATE anggota 
            SET Nama_Anggota=%s, Alamat=%s, No_Telepon=%s, Email=%s, Tanggal_Daftar=%s
            WHERE ID_Anggota=%s
        """
        return execute_db(sql, (nama, alamat, no_telp, email, tanggal_daftar, id_anggota))

    @staticmethod
    def delete(id_anggota):
        cek = query_db("SELECT COUNT(*) as cnt FROM peminjaman WHERE ID_Anggota = %s", (id_anggota,), one=True)
        if cek and cek['cnt'] > 0:
            return False, f"Anggota [{id_anggota}] tidak dapat dihapus karena memiliki data peminjaman buku."
        execute_db("DELETE FROM anggota WHERE ID_Anggota = %s", (id_anggota,))
        return True, f"Anggota [{id_anggota}] berhasil dihapus."


class PeminjamanService:
    """Mengelola sirkulasi dan Stored Procedure database"""

    @staticmethod
    def pinjam_buku(id_buku, id_anggota):
        """Memanggil Stored Procedure: SP_PinjamBuku(p_ID_Buku, p_ID_Anggota)"""
        results = call_procedure('SP_PinjamBuku', (id_buku, id_anggota))
        pesan = results[0]['Pesan'] if results and 'Pesan' in results[0] else 'Proses selesai.'
        sukses = pesan.startswith('BERHASIL')
        return sukses, pesan

    @staticmethod
    def kembalikan_buku(id_peminjaman):
        """Memanggil Stored Procedure: SP_KembalikanBuku(p_ID_Peminjaman)"""
        results = call_procedure('SP_KembalikanBuku', (id_peminjaman,))
        pesan = results[0]['Pesan'] if results and 'Pesan' in results[0] else 'Proses selesai.'
        sukses = pesan.startswith('BERHASIL')
        return sukses, pesan

    @staticmethod
    def get_all(status='', search=''):
        sql = """
            SELECT p.*, b.Judul as Judul_Buku, b.Penulis, a.Nama_Anggota, a.No_Telepon
            FROM peminjaman p
            JOIN buku b ON p.ID_Buku = b.ID_Buku
            JOIN anggota a ON p.ID_Anggota = a.ID_Anggota
            WHERE 1=1
        """
        params = []
        if status and status != 'Semua':
            sql += " AND p.Status_Peminjaman = %s"
            params.append(status)
        if search:
            sql += " AND (p.ID_Peminjaman LIKE %s OR b.Judul LIKE %s OR a.Nama_Anggota LIKE %s)"
            p = f"%{search}%"
            params.extend([p, p, p])
        sql += " ORDER BY p.Tanggal_Peminjaman DESC, p.ID_Peminjaman DESC"
        return query_db(sql, params)

    @staticmethod
    def get_pinjam_aktif():
        """Mengambil data buku yang belum kembali (Status: Dipinjam atau Terlambat)"""
        sql = """
            SELECT p.*, b.Judul as Judul_Buku, b.Penulis, a.Nama_Anggota, a.No_Telepon
            FROM peminjaman p
            JOIN buku b ON p.ID_Buku = b.ID_Buku
            JOIN anggota a ON p.ID_Anggota = a.ID_Anggota
            WHERE p.Status_Peminjaman IN ('Dipinjam', 'Terlambat')
            ORDER BY p.Tanggal_Jatuh_Tempo ASC
        """
        return query_db(sql)


# =============================================================================
# ROUTE DAN KONTROLER
# =============================================================================

# 1. BERANDA / DASHBOARD UTAMA
@app.route('/')
@app.route('/dashboard')
def dashboard():
    health = check_db_health()
    if health['status'] == 'offline':
        return render_template('offline.html', error=health['error'])

    # 1. Metrik Realtime Sesuai Database
    buku_stats = query_db("SELECT COUNT(*) as total_judul, IFNULL(SUM(Jumlah_Stok), 0) as total_eksemplar FROM buku", one=True)
    total_buku = buku_stats['total_judul']
    total_stok = int(buku_stats['total_eksemplar'])
    total_anggota = query_db("SELECT COUNT(*) as cnt FROM anggota", one=True)['cnt']
    pinjam_aktif = query_db("SELECT COUNT(*) as cnt FROM peminjaman WHERE Status_Peminjaman = 'Dipinjam'", one=True)['cnt']
    pinjam_terlambat = query_db("SELECT COUNT(*) as cnt FROM peminjaman WHERE Status_Peminjaman = 'Terlambat'", one=True)['cnt']
    pinjam_selesai = query_db("SELECT COUNT(*) as cnt FROM peminjaman WHERE Status_Peminjaman = 'Dikembalikan'", one=True)['cnt']
    total_transaksi = query_db("SELECT COUNT(*) as cnt FROM peminjaman", one=True)['cnt']

    # 2. Stored Procedure: SP_LaporanBukuBelumKembali
    laporan_belum_kembali = []
    try:
        laporan_belum_kembali = call_procedure('SP_LaporanBukuBelumKembali')
    except Exception as e:
        app.logger.warning(f"Error SP_LaporanBukuBelumKembali: {e}")

    # 3. View Database: v_bukupopuler
    buku_populer = query_db("SELECT * FROM v_bukupopuler ORDER BY Jumlah_Peminjaman DESC LIMIT 5")

    # 4. View Database: v_anggotaaktif
    anggota_aktif = query_db("SELECT * FROM v_anggotaaktif ORDER BY Jumlah_Peminjaman DESC LIMIT 5")

    # 5. Riwayat Sirkulasi Terbaru
    transaksi_terbaru = query_db("""
        SELECT p.*, b.Judul as Judul_Buku, b.Penulis, a.Nama_Anggota, a.No_Telepon
        FROM peminjaman p
        JOIN buku b ON p.ID_Buku = b.ID_Buku
        JOIN anggota a ON p.ID_Anggota = a.ID_Anggota
        ORDER BY p.Tanggal_Peminjaman DESC, p.ID_Peminjaman DESC
        LIMIT 6
    """)

    # 6. Data untuk Form Pinjam & Form Pengembalian Cepat di Dashboard
    buku_tersedia = query_db("SELECT ID_Buku, Judul, Penulis, Jumlah_Stok FROM buku WHERE Jumlah_Stok > 0 ORDER BY Judul ASC")
    daftar_anggota = query_db("SELECT ID_Anggota, Nama_Anggota, No_Telepon FROM anggota ORDER BY Nama_Anggota ASC")
    daftar_pinjam_aktif = PeminjamanService.get_pinjam_aktif()

    return render_template(
        'dashboard.html',
        total_buku=total_buku,
        total_stok=total_stok,
        total_anggota=total_anggota,
        pinjam_aktif=pinjam_aktif,
        pinjam_terlambat=pinjam_terlambat,
        pinjam_selesai=pinjam_selesai,
        total_transaksi=total_transaksi,
        laporan_belum_kembali=laporan_belum_kembali,
        buku_populer=buku_populer,
        anggota_aktif=anggota_aktif,
        transaksi_terbaru=transaksi_terbaru,
        buku_tersedia=buku_tersedia,
        daftar_anggota=daftar_anggota,
        daftar_pinjam_aktif=daftar_pinjam_aktif
    )


# 2. DATA BUKU
@app.route('/buku')
def buku_list():
    q = request.args.get('q', '').strip()
    kategori = request.args.get('kategori', '').strip()
    stok_filter = request.args.get('stok', '').strip()

    books = BukuService.get_all(search=q, kategori=kategori, stok=stok_filter)
    kategori_list = BukuService.get_categories()
    next_id = BukuService.generate_next_id()

    return render_template(
        'buku.html',
        buku_list=books,
        kategori_list=kategori_list,
        selected_q=q,
        selected_kategori=kategori,
        selected_stok=stok_filter,
        next_id=next_id
    )

@app.route('/buku/tambah', methods=['POST'])
def buku_tambah():
    id_buku = request.form.get('id_buku', '').strip() or BukuService.generate_next_id()
    judul = request.form.get('judul', '').strip()
    penulis = request.form.get('penulis', '').strip()
    penerbit = request.form.get('penerbit', '').strip()
    tahun_terbit = request.form.get('tahun_terbit', '').strip()
    isbn = request.form.get('isbn', '').strip()
    jumlah_stok = request.form.get('jumlah_stok', '0').strip()
    kategori = request.form.get('kategori', '').strip()

    try:
        BukuService.insert(id_buku, judul, penulis, penerbit, tahun_terbit, isbn, jumlah_stok, kategori)
        flash(f'Buku "{judul}" [{id_buku}] berhasil ditambahkan!', 'success')
    except Exception as e:
        flash(f'Gagal menambahkan buku: {e}', 'danger')
    return redirect(url_for('buku_list'))

@app.route('/buku/edit/<id_buku>', methods=['POST'])
def buku_edit(id_buku):
    judul = request.form.get('judul', '').strip()
    penulis = request.form.get('penulis', '').strip()
    penerbit = request.form.get('penerbit', '').strip()
    tahun_terbit = request.form.get('tahun_terbit', '').strip()
    isbn = request.form.get('isbn', '').strip()
    jumlah_stok = request.form.get('jumlah_stok', '0').strip()
    kategori = request.form.get('kategori', '').strip()

    try:
        BukuService.update(id_buku, judul, penulis, penerbit, tahun_terbit, isbn, jumlah_stok, kategori)
        flash(f'Data buku "{judul}" [{id_buku}] berhasil diperbarui!', 'success')
    except Exception as e:
        flash(f'Gagal memperbarui buku: {e}', 'danger')
    return redirect(url_for('buku_list'))

@app.route('/buku/hapus/<id_buku>', methods=['POST'])
def buku_hapus(id_buku):
    sukses, pesan = BukuService.delete(id_buku)
    flash(pesan, 'success' if sukses else 'warning')
    return redirect(url_for('buku_list'))


# 3. DATA ANGGOTA
@app.route('/anggota')
def anggota_list():
    q = request.args.get('q', '').strip()
    members = AnggotaService.get_all(search=q)
    next_id = AnggotaService.generate_next_id()
    today_str = date.today().strftime('%Y-%m-%d')

    return render_template(
        'anggota.html',
        anggota_list=members,
        selected_q=q,
        next_id=next_id,
        today_str=today_str
    )

@app.route('/anggota/tambah', methods=['POST'])
def anggota_tambah():
    id_anggota = request.form.get('id_anggota', '').strip() or AnggotaService.generate_next_id()
    nama = request.form.get('nama_anggota', '').strip()
    alamat = request.form.get('alamat', '').strip()
    no_telp = request.form.get('no_telepon', '').strip()
    email = request.form.get('email', '').strip()
    tanggal_daftar = request.form.get('tanggal_daftar', '').strip() or date.today().strftime('%Y-%m-%d')

    try:
        AnggotaService.insert(id_anggota, nama, alamat, no_telp, email, tanggal_daftar)
        flash(f'Anggota "{nama}" [{id_anggota}] berhasil didaftarkan!', 'success')
    except Exception as e:
        flash(f'Gagal mendaftarkan anggota: {e}', 'danger')
    return redirect(url_for('anggota_list'))

@app.route('/anggota/edit/<id_anggota>', methods=['POST'])
def anggota_edit(id_anggota):
    nama = request.form.get('nama_anggota', '').strip()
    alamat = request.form.get('alamat', '').strip()
    no_telp = request.form.get('no_telepon', '').strip()
    email = request.form.get('email', '').strip()
    tanggal_daftar = request.form.get('tanggal_daftar', '').strip()

    try:
        AnggotaService.update(id_anggota, nama, alamat, no_telp, email, tanggal_daftar)
        flash(f'Data anggota "{nama}" [{id_anggota}] berhasil diperbarui!', 'success')
    except Exception as e:
        flash(f'Gagal memperbarui anggota: {e}', 'danger')
    return redirect(url_for('anggota_list'))

@app.route('/anggota/hapus/<id_anggota>', methods=['POST'])
def anggota_hapus(id_anggota):
    sukses, pesan = AnggotaService.delete(id_anggota)
    flash(pesan, 'success' if sukses else 'warning')
    return redirect(url_for('anggota_list'))


# 4. TRANSAKSI SIRKULASI (PEMINJAMAN)
@app.route('/peminjaman')
def peminjaman_list():
    status = request.args.get('status', 'Semua').strip()
    q = request.args.get('q', '').strip()

    loans = PeminjamanService.get_all(status=status, search=q)
    buku_tersedia = query_db("SELECT ID_Buku, Judul, Penulis, Jumlah_Stok FROM buku WHERE Jumlah_Stok > 0 ORDER BY Judul ASC")
    daftar_anggota = query_db("SELECT ID_Anggota, Nama_Anggota, No_Telepon FROM anggota ORDER BY Nama_Anggota ASC")

    counts = query_db("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN Status_Peminjaman = 'Dipinjam' THEN 1 ELSE 0 END) as dipinjam,
            SUM(CASE WHEN Status_Peminjaman = 'Dikembalikan' THEN 1 ELSE 0 END) as dikembalikan,
            SUM(CASE WHEN Status_Peminjaman = 'Terlambat' THEN 1 ELSE 0 END) as terlambat
        FROM peminjaman
    """, one=True)

    return render_template(
        'peminjaman.html',
        peminjaman_list=loans,
        buku_tersedia=buku_tersedia,
        daftar_anggota=daftar_anggota,
        counts=counts,
        selected_status=status,
        selected_q=q
    )

@app.route('/peminjaman/tambah', methods=['POST'])
def peminjaman_tambah():
    id_buku = request.form.get('id_buku', '').strip()
    id_anggota = request.form.get('id_anggota', '').strip()

    if not (id_buku and id_anggota):
        flash('Silakan pilih buku dan anggota peminjam.', 'danger')
        return redirect(request.referrer or url_for('peminjaman_list'))

    sukses, pesan = PeminjamanService.pinjam_buku(id_buku, id_anggota)
    flash(pesan, 'success' if sukses else 'warning')
    return redirect(request.referrer or url_for('peminjaman_list'))

@app.route('/peminjaman/kembalikan/<id_peminjaman>', methods=['POST'])
def peminjaman_kembalikan(id_peminjaman):
    sukses, pesan = PeminjamanService.kembalikan_buku(id_peminjaman)
    flash(pesan, 'success' if sukses else 'warning')
    return redirect(request.referrer or url_for('peminjaman_list'))

@app.route('/peminjaman/hapus/<id_peminjaman>', methods=['POST'])
def peminjaman_hapus(id_peminjaman):
    try:
        execute_db("DELETE FROM peminjaman WHERE ID_Peminjaman = %s", (id_peminjaman,))
        flash(f'Data transaksi {id_peminjaman} berhasil dihapus.', 'success')
    except Exception as e:
        flash(f'Gagal menghapus transaksi: {e}', 'danger')
    return redirect(url_for('peminjaman_list'))


# 5. HALAMAN PENGEMBALIAN BUKU DEDIKASI
@app.route('/pengembalian')
def halaman_pengembalian():
    daftar_pinjam_aktif = PeminjamanService.get_pinjam_aktif()
    return render_template('pengembalian.html', daftar_pinjam_aktif=daftar_pinjam_aktif)

@app.route('/pengembalian/proses', methods=['POST'])
def proses_pengembalian():
    id_peminjaman = request.form.get('id_peminjaman', '').strip()
    if not id_peminjaman:
        flash('Pilih transaksi yang ingin dikembalikan.', 'warning')
        return redirect(url_for('halaman_pengembalian'))

    sukses, pesan = PeminjamanService.kembalikan_buku(id_peminjaman)
    flash(pesan, 'success' if sukses else 'warning')
    return redirect(url_for('halaman_pengembalian'))


# 6. LAPORAN BASIS DATA (VIEWS & STORED PROCEDURES)
@app.route('/laporan')
def laporan():
    tab = request.args.get('tab', 'belum_kembali')

    laporan_belum_kembali = []
    try:
        laporan_belum_kembali = call_procedure('SP_LaporanBukuBelumKembali')
    except Exception as e:
        app.logger.warning(f"Error SP_LaporanBukuBelumKembali: {e}")

    buku_populer = query_db("SELECT * FROM v_bukupopuler ORDER BY Jumlah_Peminjaman DESC")
    anggota_aktif = query_db("SELECT * FROM v_anggotaaktif ORDER BY Jumlah_Peminjaman DESC")
    peminjaman_terlambat = query_db("SELECT * FROM v_peminjamanterlambat ORDER BY Tanggal_Jatuh_Tempo ASC")

    return render_template(
        'laporan.html',
        active_tab=tab,
        laporan_belum_kembali=laporan_belum_kembali,
        buku_populer=buku_populer,
        anggota_aktif=anggota_aktif,
        peminjaman_terlambat=peminjaman_terlambat
    )

@app.route('/laporan/export/<tipe>')
def laporan_export_csv(tipe):
    output = io.StringIO()
    writer = csv.writer(output)

    if tipe == 'belum_kembali':
        writer.writerow(['Judul Buku', 'Nama Anggota', 'Tanggal Peminjaman', 'Tanggal Jatuh Tempo'])
        data = call_procedure('SP_LaporanBukuBelumKembali')
        for row in data:
            writer.writerow([row['Judul_Buku'], row['Nama_Anggota'], row['Tanggal_Peminjaman'], row['Tanggal_Jatuh_Tempo']])
        filename = f"laporan_buku_belum_kembali_{date.today()}.csv"

    elif tipe == 'buku_populer':
        writer.writerow(['Judul Buku', 'Penulis', 'Jumlah Peminjaman'])
        data = query_db("SELECT * FROM v_bukupopuler ORDER BY Jumlah_Peminjaman DESC")
        for row in data:
            writer.writerow([row['Judul'], row['Penulis'], row['Jumlah_Peminjaman']])
        filename = f"laporan_buku_populer_{date.today()}.csv"

    elif tipe == 'anggota_aktif':
        writer.writerow(['ID Anggota', 'Nama Anggota', 'Jumlah Peminjaman Sukses'])
        data = query_db("SELECT * FROM v_anggotaaktif ORDER BY Jumlah_Peminjaman DESC")
        for row in data:
            writer.writerow([row['ID_Anggota'], row['Nama_Anggota'], row['Jumlah_Peminjaman']])
        filename = f"laporan_anggota_aktif_{date.today()}.csv"

    elif tipe == 'terlambat':
        writer.writerow(['Judul Buku', 'Nama Anggota', 'Tanggal Peminjaman', 'Tanggal Jatuh Tempo', 'Tanggal Pengembalian'])
        data = query_db("SELECT * FROM v_peminjamanterlambat")
        for row in data:
            writer.writerow([row['Judul_Buku'], row['Nama_Anggota'], row['Tanggal_Peminjaman'], row['Tanggal_Jatuh_Tempo'], row['Tanggal_Pengembalian'] or '-'])
        filename = f"laporan_peminjaman_terlambat_{date.today()}.csv"

    else:
        return redirect(url_for('laporan'))

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )


# 7. INFORMASI DATABASE XAMPP
@app.route('/pengaturan')
@app.route('/database-info')
def database_info():
    health = check_db_health()
    tables = []
    views = []
    procedures = []
    triggers = []

    if health['status'] == 'online':
        try:
            all_tables = query_db("SHOW FULL TABLES")
            for t in all_tables:
                name = list(t.values())[0]
                t_type = list(t.values())[1]
                if t_type == 'VIEW':
                    views.append(name)
                else:
                    tables.append(name)

            procs = query_db("SHOW PROCEDURE STATUS WHERE Db = %s", (Config.DB_NAME,))
            procedures = [p['Name'] for p in procs]

            triggers = query_db("SHOW TRIGGERS FROM " + Config.DB_NAME)
        except Exception as e:
            app.logger.error(f"Error database info: {e}")

    return render_template(
        'database_info.html',
        health=health,
        config=Config,
        tables=tables,
        views=views,
        procedures=procedures,
        triggers=triggers
    )


if __name__ == '__main__':
    print("=================================================================")
    print("       PERPUSTAKAAN LITERASI JAYA - SISTEM INFORMASI WEB        ")
    print("       Terhubung ke XAMPP MySQL (Host: 127.0.0.1:3306)          ")
    print("       Akses Antarmuka di: http://127.0.0.1:5000                ")
    print("=================================================================")
    app.run(debug=True, host='127.0.0.1', port=5000)
