@echo off
title WhatsApp Antigravity Bot - Refresh & Restart Engine
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================================
echo   🔄 REFRESH & RESTART ENGINE BOT WHATSAPP
echo ========================================================
echo.

echo [1/4] Memeriksa status sesi WhatsApp yang tertaut...
if exist "bridge\auth_info_baileys\creds.json" (
    echo   ✅ Sesi WhatsApp sebelumnya DITEMUKAN!
    echo   ✅ Bot akan langsung otomatis terhubung tanpa perlu scan QR ulang.
) else (
    echo   ⚠️ Sesi belum ditemukan. QR Code akan ditampilkan jika belum tertaut.
)
echo.

echo [2/4] Membersihkan proses lama yang menggantung di port 8000 & 3000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /f /pid %%a > nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do taskkill /f /pid %%a > nul 2>&1
echo   ✅ Port bersih dan siap digunakan.
echo.

echo [3/4] Memulai ulang FastAPI Backend (:8000)...
start "FastAPI Backend" cmd /k "run_server.bat"
timeout /t 3 /nobreak > nul

echo [4/4] Memulai ulang WhatsApp Bridge Engine (:3000)...
start "WhatsApp Bridge" cmd /k "run_bridge.bat"

echo.
echo ========================================================
echo   ✨ ENGINE BOT WHATSAPP BERHASIL DI-REFRESH! ✨
echo ========================================================
echo   • Akun WA Anda akan terhubung otomatis dalam beberapa detik.
echo   • Fitur baru (Anti-link, Welcome, Kick, Stiker, AI) sudah aktif.
echo   • Ketik .menu di grup untuk melihat semua perintah.
echo ========================================================
echo.
pause
