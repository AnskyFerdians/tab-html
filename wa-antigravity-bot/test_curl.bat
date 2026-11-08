@echo off
chcp 65001 > nul
echo ========================================================
echo   PENGUJIAN WEBHOOK WHATSAPP ANTIGRAVITY BOT DENGAN CURL
echo ========================================================
echo.

echo 1. UJI PESAN DARI NOMOR BARU (Belum Verifikasi):
curl -X POST http://localhost:8000/webhook/whatsapp ^
  -H "Content-Type: application/json" ^
  -d "{\"from\": \"6281234567890\", \"sender_name\": \"Andi\", \"text\": \"Halo bot, apa kabar?\"}"
echo.
echo.

echo 2. UJI KIRIM KODE KEAMANAN (RajaWali0108):
curl -X POST http://localhost:8000/webhook/whatsapp ^
  -H "Content-Type: application/json" ^
  -d "{\"from\": \"6281234567890\", \"sender_name\": \"Andi\", \"text\": \"RajaWali0108\"}"
echo.
echo.

echo 3. UJI OBROLAN BIASA (Setelah Verifikasi):
curl -X POST http://localhost:8000/webhook/whatsapp ^
  -H "Content-Type: application/json" ^
  -d "{\"from\": \"6281234567890\", \"sender_name\": \"Andi\", \"text\": \"Halo bot, apa kabar? Siapa namamu?\"}"
echo.
echo.

echo 4. UJI MULTI-TURN MEMORY (Konteks Chat Sebelumnya):
curl -X POST http://localhost:8000/webhook/whatsapp ^
  -H "Content-Type: application/json" ^
  -d "{\"from\": \"6281234567890\", \"sender_name\": \"Andi\", \"text\": \"Kemarin saya tanya tentang apa?\"}"
echo.
echo.

echo 5. UJI BUAT DOKUMEN WORD (.DOCX) APBN:
curl -X POST http://localhost:8000/webhook/whatsapp ^
  -H "Content-Type: application/json" ^
  -d "{\"from\": \"6281234567890\", \"sender_name\": \"Andi\", \"text\": \"Tolong buatkan dokumen Word berisi ringkasan materi pelajaran ekonomi tentang APBN.\"}"
echo.
echo.

echo 6. UJI BUAT DOKUMEN PDF:
curl -X POST http://localhost:8000/webhook/whatsapp ^
  -H "Content-Type: application/json" ^
  -d "{\"from\": \"6281234567890\", \"sender_name\": \"Andi\", \"text\": \"Tolong buatkan pdf ringkasan materi inflasi dan perbankan.\"}"
echo.
echo.

echo Selesai.
pause
