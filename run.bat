@echo off
title Sistem Informasi Perpustakaan Literasi Jaya
color 0B

echo ==========================================================
echo    PERPUSTAKAAN LITERASI JAYA - SISTEM INFORMASI WEB      
echo ==========================================================
echo.
echo Memeriksa modul Python...
python -m pip install -r requirements.txt >nul 2>&1

echo.
echo Menjalankan aplikasi Flask...
echo Server URL: http://127.0.0.1:5000
echo Tekan CTRL + C di jendela ini untuk menghentikan server.
echo.

start http://127.0.0.1:5000
python app.py

pause
