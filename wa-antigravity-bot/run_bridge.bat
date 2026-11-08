@echo off
title WhatsApp Antigravity Bot - Baileys Bridge
chcp 65001 > nul
cd /d "%~dp0bridge"
echo ========================================================
echo   Menjalankan WhatsApp Bridge (Baileys :3000)
echo   Buka link browser untuk scan QR: http://localhost:3000
echo   Atau scan langsung QR Code di terminal ini!
echo ========================================================
node index.js

pause
