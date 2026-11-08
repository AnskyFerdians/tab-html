@echo off
title WhatsApp Antigravity Bot - Akun 2 (Port 3001)
chcp 65001 > nul
cd /d "%~dp0bridge"
set BRIDGE_PORT=3001
set AUTH_DIR=auth_info_baileys_2
echo ========================================================
echo   Menjalankan WhatsApp Bridge Akun 2 (Port :3001)
echo   Buka browser untuk scan QR: http://localhost:3001
echo ========================================================
node index.js
pause
