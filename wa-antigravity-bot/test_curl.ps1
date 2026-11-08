# PowerShell test script for WhatsApp Antigravity Bot
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  PENGUJIAN WEBHOOK WHATSAPP ANTIGRAVITY BOT (POWERSHELL)" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$endpoint = "http://localhost:8000/webhook/whatsapp"
$sender = "6281234567890"

# 1. New user (Unverified)
Write-Host "`n[1] Kirim pesan tanpa kode verifikasi:" -ForegroundColor Yellow
$body1 = @{ from = $sender; sender_name = "Andi"; text = "Halo bot!" } | ConvertTo-Json
$res1 = Invoke-RestMethod -Uri $endpoint -Method Post -ContentType "application/json" -Body $body1
$res1 | ConvertTo-Json -Depth 3

# 2. Enter security code RajaWali0108
Write-Host "`n[2] Masukkan kode verifikasi keamanan RajaWali0108:" -ForegroundColor Yellow
$body2 = @{ from = $sender; sender_name = "Andi"; text = "RajaWali0108" } | ConvertTo-Json
$res2 = Invoke-RestMethod -Uri $endpoint -Method Post -ContentType "application/json" -Body $body2
$res2 | ConvertTo-Json -Depth 3

# 3. Chat after verification
Write-Host "`n[3] Obrolan biasa:" -ForegroundColor Yellow
$body3 = @{ from = $sender; sender_name = "Andi"; text = "Halo bot, apa kabar? Siapa namamu?" } | ConvertTo-Json
$res3 = Invoke-RestMethod -Uri $endpoint -Method Post -ContentType "application/json" -Body $body3
$res3 | ConvertTo-Json -Depth 3

# 4. Memory test
Write-Host "`n[4] Uji ingatan percakapan sebelumnya:" -ForegroundColor Yellow
$body4 = @{ from = $sender; sender_name = "Andi"; text = "Kemarin saya tanya tentang apa?" } | ConvertTo-Json
$res4 = Invoke-RestMethod -Uri $endpoint -Method Post -ContentType "application/json" -Body $body4
$res4 | ConvertTo-Json -Depth 3

# 5. Word document request
Write-Host "`n[5] Permintaan buat dokumen Word APBN:" -ForegroundColor Yellow
$body5 = @{ from = $sender; sender_name = "Andi"; text = "Tolong buatkan dokumen Word berisi ringkasan materi pelajaran ekonomi tentang APBN." } | ConvertTo-Json
$res5 = Invoke-RestMethod -Uri $endpoint -Method Post -ContentType "application/json" -Body $body5
$res5 | ConvertTo-Json -Depth 3

Write-Host "`nPengujian Selesai!" -ForegroundColor Green
