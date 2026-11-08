@echo off
title WhatsApp Antigravity Bot - Launcher
chcp 65001 > nul
cd /d "%~dp0"
echo ========================================================
echo   MEMULAI SELURUH SISTEM WHATSAPP ANTIGRAVITY BOT
echo ========================================================
echo 1. Membuka jendela FastAPI Backend di port 8000...
start "FastAPI Backend" cmd /k "run_server.bat"

echo 2. Menunggu server backend siap...
ping 127.0.0.1 -n 4 > nul

echo 3. Membuka WhatsApp Bridge dan Menampilkan QR Code...
start "WhatsApp Bridge" cmd /k "run_bridge.bat"

echo 4. Membuka Halaman Scan QR di Browser...
timeout /t 3 /nobreak > nul
start http://localhost:3000

echo.
echo ========================================================
echo   Server telah dijalankan!
echo   Buka link ini di browser: http://localhost:3000
echo   - Buka WhatsApp di HP Anda
echo   - Masuk ke Menu Titik Tiga / Pengaturan
echo   - Pilih "Perangkat Tertaut" / "Tautkan Perangkat"
echo   - Arahkan kamera HP ke QR Code di layar browser!
echo ========================================================

if "%1"=="--no-pause" goto :eof
pause


