import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'literasijaya-secret-key-2026-basdat')
    
    # Konfigurasi Koneksi MySQL XAMPP
    DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'perpustakaanliterasijaya')
    DB_CHARSET = 'utf8mb4'
