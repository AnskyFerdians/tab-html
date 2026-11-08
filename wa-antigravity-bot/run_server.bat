@echo off
title WhatsApp Antigravity Bot - FastAPI Backend
chcp 65001 > nul
cd /d "%~dp0"
echo ========================================================
echo   Menjalankan FastAPI Backend Antigravity Bot (:8000)
echo ========================================================
python main.py
pause
