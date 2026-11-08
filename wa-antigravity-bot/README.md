# WhatsApp Antigravity Bot 🤖🛡️📄

Proyek integrasi WhatsApp Bot cerdas berbasis **FastAPI**, **Antigravity AI Agent SDK (Gemini Thinking)**, **Baileys WebSocket Bridge**, dan **Document Generator** dengan fitur **Manajemen Grup & Proteksi Komprehensif (Anti-Link, Welcome Greetings, Admin Controls)**, **Sticker Maker**, serta **Akses Laptop Jarak Jauh**.

---

## 🌟 Fitur Premium Utama

### 🛡️ 1. Manajemen Grup & Proteksi Otomatis (Group Protection Engine)
* **Proteksi Anti-Link:**
  * Mendeteksi tautan undangan WhatsApp (`chat.whatsapp.com/`, `wa.me/`), grup/channel, dan tautan luar lainnya.
  * Pesan pelanggar otomatis dihapus seketika.
  * Pilihan tindakan: mode peringatan 3x (*warn mode* -> kick di pelanggaran ke-3) atau langsung kick (*instant kick mode*).
  * Khusus Admin grup dan Bot Owner kebal terhadap aturan anti-link.
  * Pengaturan fleksibel per grup: `.antilink [on|off|warn|kick]`.
* **Sambutan & Perpisahan Otomatis (Welcome & Goodbye Greetings):**
  * Mengirim kartu sambutan otomatis saat anggota baru bergabung dengan mention `@user`, nama grup, jumlah anggota, dan aturan/deskripsi grup.
  * Mengirim salam perpisahan saat anggota keluar dari grup.
  * Pesan sambutan dan perpisahan dapat dikustomisasi per grup: `.setwelcome [teks]` dan `.setgoodbye [teks]`.
* **Alat Administrasi Grup Lengkap:**
  * `.kick @user` / `.tendang @user` — Mengeluarkan anggota tertentu dari grup.
  * `.promote @user` / `.jadikanadmin @user` — Menaikkan anggota menjadi Admin grup.
  * `.demote @user` / `.turunkanadmin @user` — Menurunkan jabatan Admin menjadi anggota biasa.
  * `.tagall [pesan]` / `.hidetag [pesan]` — Memanggil seluruh anggota grup untuk pengumuman penting.
  * `.tutupgrup` / `.bukagrup` — Mengatur izin chat grup (hanya admin atau semua anggota).
  * `.linkgrup` — Mengambil tautan undangan grup secara langsung.
  * `.infogrup` — Menampilkan rangkuman profil, daftar admin, dan status fitur keamanan grup.

### 🎨 2. Pembuat Stiker & Konverter Media (Sticker Maker)
* `.s` / `.sticker` — Mengubah gambar menjadi stiker WhatsApp berkualitas tinggi secara instan (kirim gambar dengan caption `.s` atau balas gambar yang ada).
* `.toimg` — Mengubah kembali stiker WhatsApp menjadi gambar JPG/PNG.

### 🧠 3. Kecerdasan Buatan Terintegrasi di Grup & Chat Pribadi
* Di dalam grup: Ketik `.ai [pertanyaan]` atau langsung **tag `@bot`** untuk berdiskusi dengan Gemini AI.
* Di chat pribadi: Bertindak sebagai asisten remote pribadi untuk mengontrol laptop (screenshot, terminal, sistem, berkas, baterai, dll.).

1. **Keamanan Kontak Baru (One-Time Security Code)**:
   - Kontak yang baru pertama kali mengobrol wajib memasukkan kode keamanan: `RajaWali0108`.
   - Kode ini **hanya perlu dimasukkan 1 kali saja**. Status verifikasi disimpan secara persisten di `storage/verified_users.json`.
   - Setelah terverifikasi, pengguna bebas mengobrol, menjalankan otomasi, dan meminta pembuatan dokumen tanpa diminta kode lagi.

2. **Akses Terminal Laptop Langsung (PowerShell & CMD)**:
   - Menjalankan perintah terminal langsung di laptop host (`C:\Users\HP`) dari WhatsApp.
   - Contoh perintah: `terminal dir`, `cmd: ipconfig`, `terminal git status`, `terminal python --version`, `ps: Get-Process`.
   - Dilengkapi proteksi keamanan dari eksekusi perintah destruktif (seperti format drive).

3. **Sistem Pembelajaran & Memori Pengalaman Pengguna**:
   - Bot tidak sok pintar/sok tahu. Bot terus belajar langsung dari pengalaman, koreksi, dan fakta yang diajarkan pengguna.
   - **Ajari Bot**: `ingat: laptop saya RAM 16GB dual channel` atau `catat: folder kerja saya di C:\Users\HP\workspace`.
   - **Cek Ingatan**: `apa yang kamu ingat` / `daftar ingatan` / `profil laptop`.
   - **Hapus Ingatan**: `lupakan: [nomor/kata kunci]`.
   - Bot otomatis mengingat profil hardware laptop dan catatan pengalaman dalam setiap interaksi.

4. **Kepribadian Antigravity yang Sadar Diri (Self-Aware) & Bersahabat**:
   - Menjawab secara santai, luwes, dan akrab layaknya partner kerja/coding pribadi.
   - Mengerti dan sadar akan lingkungan laptopnya sendiri (Windows 11 di host HP).
   - Bersikap rendah hati: jika pengguna mengoreksi atau mengkritik, bot langsung menerima dengan tulus dan mencatat koreksi tersebut ke memori pengalaman.

5. **Pemantauan Status Laptop Real-Time (Hardware & Resources)**:
   - **Status Laptop**: Penggunaan CPU (Core), RAM (Terpakai/Sisa), Ruang Disk C, Persentase Baterai & status colokan charger, serta System Uptime.
   - **Top Proses**: Melihat 5 proses/aplikasi yang memakan memori RAM terbesar di laptop.
   - **Diagnostik Wi-Fi**: Menampilkan nama SSID Wi-Fi aktif, kekuatan sinyal, dan IP lokal.

6. **Eksekusi Otomasi & Analisis (Predefined Task Runner)**:
   - **Analisis Saham & Laporan Keuangan**: Menjalankan engine analisis saham (`saham_reporter`) dengan opsi kode ticker (misal: `jalankan saham BBCA`).
   - **NewsFilter Sentimen Pasar**: Mengambil update berita pasar modal dan sentimen IDX/BEI.
   - **TradingView Analyzer**: Menjalankan pemindaian indikator teknikal.

7. **Kelola & Edit Penyimpanan Laptop (File System Management)**:
   - **Jelajah Direktori**: Menampilkan daftar folder dan file (`list folder` / `lihat folder [path]`).
   - **Membaca Berkas**: Membaca isi file teks, catatan, atau skrip (`baca file [path]`).
   - **Menulis & Membuat Berkas Baru**: Menulis teks ke file baru atau menimpa berkas (`tulis file [path] isi [teks]`).
   - **Mengedit & Menambah Teks (Append)**: Menambahkan teks baris baru ke berkas (`tambah file [path] isi [teks]`).
   - **Membuat Folder**: Membuat direktori baru di laptop (`buat folder [path]`).
   - **Menghapus Berkas & Folder**: Menghapus file atau folder dengan proteksi keamanan direktori sistem (`hapus file [path]` / `hapus folder [path]`).
   - **Mengganti Nama & Memindahkan**: Mengubah nama atau memindahkan file/folder (`ganti nama [lama] ke [baru]`).
   - **Pengiriman Berkas Fisik Laptop**: Mengirim berkas apapun dari penyimpanan laptop ke chat WhatsApp via token `[FILE:path]`.

8. **Generator Dokumen Otomatis**:
   - **Word (.docx)**: Memformat judul, heading, sub-bab, bullet points, dan styling profesional secara otomatis ke folder `storage/`.
   - **PDF (.pdf)**: Mengonversi materi ke format PDF rapi menggunakan `fpdf2`.
   - **Teks (.txt)**: Alternatif berkas teks polos.
   - **Riwayat Berkas**: Melihat berkas laporan terbaru (`daftar file`).

9. **FastAPI Webhook & Dispatch Engine**:
   - Endpoint `POST /webhook/whatsapp` yang kompatibel dengan berbagai bridge WhatsApp (Baileys, WPPConnect).
   - Dilengkapi *internal mock bridge* untuk pengujian lokal tanpa memerlukan server WhatsApp aktif.

---

## 📁 Struktur Direktori

```text
wa-antigravity-bot/
├── main.py                 # Server FastAPI & Webhook receiver & Bridge dispatcher
├── agent_service.py        # Konfigurasi Antigravity Agent, verifikasi kode & router fitur
├── tools/
│   ├── __init__.py
│   ├── doc_generator.py    # Tools Python untuk membuat .docx, PDF, txt
│   ├── system_monitor.py   # Tools status CPU, RAM, Disk, Baterai & Top Proses
│   ├── task_runner.py      # Runner tugas otomasi terdaftar (saham, newsfilter, dll)
│   └── file_manager.py     # Manajemen berkas & dispatch file ke WhatsApp
├── storage/                # Folder penyimpanan dokumen & basis data sesi/verifikasi
├── requirements.txt        # Daftar pustaka dependensi Python (termasuk psutil)
├── .env.example            # Template konfigurasi variabel lingkungan
├── .env                    # File konfigurasi lokal
├── test_bot.py             # Skrip automated end-to-end test suite (11 skenario)
├── test_curl.bat           # Skrip uji coba cepat dengan cURL (Windows CMD)
├── test_curl.ps1           # Skrip uji coba cepat dengan PowerShell
└── README.md               # Dokumentasi & panduan penggunaan
```


---

## 🚀 Panduan Instalasi & Menjalankan Server

### 1. Pasang Dependensi
Buka terminal / PowerShell di folder `wa-antigravity-bot`:
```bash
pip install -r requirements.txt
```

### 2. Konfigurasi Variabel Lingkungan (.env)
Sesuaikan file `.env` jika diperlukan:
```env
PORT=8000
SECURITY_CODE=RajaWali0108
WHATSAPP_BRIDGE_URL=http://localhost:8000
# Opsional: Jika ingin menggunakan LLM Gemini cloud
GEMINI_API_KEY=
```

### 3. Jalankan Server
```bash
python main.py
```
Server akan aktif di: `http://localhost:8000`  
Dokumentasi interaktif Swagger UI tersedia di: `http://localhost:8000/docs`

---

## 🧪 Cara Pengujian Lokal (Tanpa Menunggu WhatsApp)

### Opsi A: Jalankan Automated Test Suite
Jalankan pengujian otomatis untuk memverifikasi 7 skenario (keamanan, obrolan, memori, pembuatan docx, pdf, dispatch):
```bash
python test_bot.py
```

### Opsi B: Uji dengan cURL / CMD Batch Script
Cukup klik ganda `test_curl.bat` atau jalankan via terminal:
```cmd
test_curl.bat
```

Atau jalankan perintah cURL secara manual:

#### 1. Pesan Pertama (Belum Terverifikasi)
```bash
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d "{\"from\": \"6281234567890\", \"sender_name\": \"Andi\", \"text\": \"Halo bot!\"}"
```
*Respon Bot: Meminta kode verifikasi keamanan.*

#### 2. Masukkan Kode Keamanan `RajaWali0108`
```bash
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d "{\"from\": \"6281234567890\", \"sender_name\": \"Andi\", \"text\": \"RajaWali0108\"}"
```
*Respon Bot: Konfirmasi verifikasi berhasil, nomor tersimpan secara permanen.*

#### 3. Obrolan Biasa & Pengenalan Diri
```bash
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d "{\"from\": \"6281234567890\", \"sender_name\": \"Andi\", \"text\": \"Halo bot, apa kabar? Siapa namamu?\"}"
```

#### 4. Uji Coba Multi-Turn (Konteks Percakapan)
```bash
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d "{\"from\": \"6281234567890\", \"sender_name\": \"Andi\", \"text\": \"Kemarin saya tanya tentang apa?\"}"
```
*Respon Bot: Mengingat bahwa pengguna sebelumnya bertanya tentang "Halo bot, apa kabar? Siapa namamu?".*

#### 5. Pembuatan Dokumen Word (.docx) Materi APBN
```bash
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d "{\"from\": \"6281234567890\", \"sender_name\": \"Andi\", \"text\": \"Tolong buatkan dokumen Word berisi ringkasan materi pelajaran ekonomi tentang APBN.\"}"
```
*Respon Bot:*
```json
{
  "status": "success",
  "has_file": true,
  "file_path": "storage/ringkasan_materi_pelajaran_ekonomi_tentang_apbn_20260927_020424.docx",
  "reply": "Dokumen *Ringkasan Materi Pelajaran Ekonomi Tentang Apbn* telah berhasil dibuat dan siap diunduh!...",
  "raw_response": "[FILE:storage/ringkasan_materi_pelajaran_ekonomi_tentang_apbn_20260927_020424.docx] ..."
}
```

---

## 🔗 Integrasi dengan WhatsApp Bridge (Baileys / WPPConnect)

Saat menghubungkan ke server bridge WhatsApp asli (misalnya Node.js Baileys):

1. **Teruskan Pesan Masuk (Inbound Webhook)**:
   Pada event `messages.upsert` di Baileys, kirimkan HTTP POST:
   ```javascript
   // Contoh di Node.js Baileys:
   const response = await fetch('http://localhost:8000/webhook/whatsapp', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({
           from: msg.key.remoteJid,
           sender_name: msg.pushName,
           text: msg.message?.conversation || msg.message?.extendedTextMessage?.text
       })
   });
   ```

2. **Kirim Pesan Keluar (Outbound Dispatch)**:
   Ubah `WHATSAPP_BRIDGE_URL` di `.env` menjadi port server bridge Anda (misal `http://localhost:3000`).
   Bridge Anda cukup menyediakan endpoint:
   - `POST /send-message` dengan payload `{ to, message }`
   - `POST /send-file` dengan payload `{ to, filePath, caption }`
