#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "=========================================================="
echo "🚀 WhatsApp Antigravity Bot - VPS Launcher"
echo "=========================================================="

# 1. Pastikan Python & pip terpasang
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 tidak ditemukan. Menginstal python3..."
    sudo apt update && sudo apt install -y python3 python3-pip python3-venv
fi

# 2. Virtual Environment Python
if [ ! -d "venv" ]; then
    echo "📦 Membuat virtual environment Python..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "📦 Memeriksa & menginstal dependencies Python..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# 3. Dependencies Node.js (Baileys)
cd "$DIR/bridge"
if [ ! -d "node_modules" ]; then
    echo "📦 Menginstal dependensi Node.js / Baileys..."
    npm install
fi

cd "$DIR"

# 4. Jalankan FastAPI di background jika belum berjalan
if ! pgrep -f "main.py" > /dev/null; then
    echo "⚡ Menjalankan FastAPI Backend di latar belakang (port 8000)..."
    nohup venv/bin/python main.py > fastapi.log 2>&1 &
    sleep 2
else
    echo "ℹ️ FastAPI Backend sudah berjalan."
fi

# 5. Jalankan WhatsApp Bridge (Dikelola PM2 agar tetap online 24 jam saat terminal ditutup)
if ! command -v pm2 &> /dev/null; then
    echo "📦 Menginstal PM2 Process Manager..."
    sudo npm install -g pm2 || npm install -g pm2 || true
fi

if command -v pm2 &> /dev/null; then
    echo "=========================================================="
    echo "📲 Menjalankan WhatsApp Bridge via PM2 Daemon..."
    echo "=========================================================="
    cd "$DIR/bridge"
    pm2 start index.js --name "wa-bridge" --update-env || pm2 restart "wa-bridge"
    pm2 save
    echo "✅ WhatsApp Bridge aktif di latar belakang (tahan restart/tutup terminal)."
    echo "📋 Menampilkan live logs & QR Code (Tekan Ctrl+C untuk keluar log, bot TETAP BERJALAN):"
    echo "=========================================================="
    pm2 logs wa-bridge --lines 30
else
    echo "=========================================================="
    echo "📲 Menjalankan WhatsApp Bridge (Foreground)..."
    echo "   Scan QR Code yang muncul di layar dengan WhatsApp Anda!"
    echo "=========================================================="
    cd "$DIR/bridge"
    node index.js
fi
