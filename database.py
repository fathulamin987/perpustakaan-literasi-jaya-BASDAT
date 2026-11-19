import pymysql
import pymysql.cursors
from config import Config

def get_db_connection():
    """Membuka koneksi ke database MySQL XAMPP"""
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset=Config.DB_CHARSET,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )

def query_db(query, args=(), one=False):
    """Menjalankan query SELECT dan mengembalikan dictionary"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, args)
            rv = cursor.fetchall()
            return (rv[0] if rv else None) if one else rv
    finally:
        conn.close()

def execute_db(query, args=(), return_id=False):
    """Menjalankan query INSERT/UPDATE/DELETE dengan commit"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, args)
            conn.commit()
            if return_id:
                return cursor.lastrowid
            return cursor.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def call_procedure(proc_name, args=()):
    """Menjalankan Stored Procedure MySQL"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.callproc(proc_name, args)
            conn.commit()
            results = cursor.fetchall()
            return results
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def check_db_health():
    """Memeriksa status koneksi dan metadata database"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION() as version, DATABASE() as current_db")
            info = cursor.fetchone()
            
            # Hitung jumlah baris per tabel
            cursor.execute("SELECT COUNT(*) as total FROM buku")
            total_buku = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM anggota")
            total_anggota = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM peminjaman")
            total_peminjaman = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM peminjaman WHERE Status_Peminjaman = 'Dipinjam'")
            total_dipinjam = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as total FROM peminjaman WHERE Status_Peminjaman = 'Terlambat'")
            total_terlambat = cursor.fetchone()['total']

        conn.close()
        return {
            'status': 'online',
            'version': info['version'],
            'database': info['current_db'],
            'total_buku': total_buku,
            'total_anggota': total_anggota,
            'total_peminjaman': total_peminjaman,
            'total_dipinjam': total_dipinjam,
            'total_terlambat': total_terlambat,
            'error': None
        }
    except Exception as e:
        return {
            'status': 'offline',
            'version': None,
            'database': Config.DB_NAME,
            'total_buku': 0,
            'total_anggota': 0,
            'total_peminjaman': 0,
            'total_dipinjam': 0,
            'total_terlambat': 0,
            'error': str(e)
        }
