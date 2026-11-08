"""Automated End-to-End Test Suite for WhatsApp Antigravity Bot.

Tests:
1. Security verification challenge (unverified contact).
2. One-time verification code activation ('RajaWali0108').
3. Casual chat and personality response.
4. Multi-turn memory retention ("Kemarin saya tanya tentang apa?").
5. Automated Word (.docx) document generation for APBN economics.
6. Automated PDF (.pdf) document generation.
7. Verification persistence (no code needed on subsequent turns).
"""

import sys
import os
import json
from fastapi.testclient import TestClient

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import main
main.ENABLE_LOCAL_DISPATCH = False
from main import app
from agent_service import SECURITY_CODE, VERIFIED_USERS_FILE, SESSIONS_BACKUP_FILE

client = TestClient(app)

def test_full_bot_workflow():
    print("=" * 60)
    print("🤖 STARTING WHATSAPP ANTIGRAVITY BOT END-TO-END TESTS")
    print("=" * 60)

    # Clean test sender to start fresh
    test_sender = "6289912345678"
    from agent_service import agent_service
    agent_service.security.verified_users.discard(test_sender)
    agent_service.session.sessions.pop(test_sender, None)
    if os.path.exists(VERIFIED_USERS_FILE):
        try:
            with open(VERIFIED_USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["verified_users"] = [u for u in data.get("verified_users", []) if u != test_sender]
            with open(VERIFIED_USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    # TEST 1: Unverified User Sends Message
    print("\n[TEST 1] Pesan dari Kontak Belum Terverifikasi...")
    res1 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": "Halo bot, apa kabar?"
    })
    assert res1.status_code == 200, f"Failed: {res1.text}"
    data1 = res1.json()
    print("Response Status:", data1["status"])
    print("Bot Reply:\n", data1["reply"])
    assert "kode verifikasi" in data1["reply"].lower()
    print("✅ TEST 1 PASSED: Bot meminta kode verifikasi keamanan.")

    # TEST 2: User Enters Security Code 'RajaWali0108'
    print(f"\n[TEST 2] Pengguna Memasukkan Kode Keamanan '{SECURITY_CODE}'...")
    res2 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": SECURITY_CODE
    })
    assert res2.status_code == 200
    data2 = res2.json()
    print("Bot Reply:\n", data2["reply"])
    assert "Verifikasi berhasil" in data2["reply"]
    print("✅ TEST 2 PASSED: Pengguna berhasil diverifikasi 1x.")

    # TEST 3: Casual Chat & Identity
    print("\n[TEST 3] Obrolan Santai & Tanya Identitas...")
    res3 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": "Halo bot, apa kabar? Siapa namamu?"
    })
    assert res3.status_code == 200
    data3 = res3.json()
    print("Bot Reply:\n", data3["reply"])
    assert "Antigravity Bot" in data3["reply"]
    print("✅ TEST 3 PASSED: Bot menjawab dengan ramah dan menyebut identitas.")

    # TEST 4: Multi-Turn Memory Retention
    print("\n[TEST 4] Uji Coba Multi-Turn (Konteks Chat: 'Kemarin saya tanya tentang apa?')...")
    res4 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": "Kemarin saya tanya tentang apa?"
    })
    assert res4.status_code == 200
    data4 = res4.json()
    print("Bot Reply:\n", data4["reply"])
    assert "Siapa namamu" in data4["reply"] or "Halo bot" in data4["reply"]
    print("✅ TEST 4 PASSED: Bot berhasil mengingat topik chat sebelumnya!")

    # TEST 5: Document Generation (Word .docx for APBN)
    print("\n[TEST 5] Permintaan Pembuatan Dokumen Word Materi APBN...")
    res5 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": "Tolong buatkan dokumen Word berisi ringkasan materi pelajaran ekonomi tentang APBN."
    })
    assert res5.status_code == 200
    data5 = res5.json()
    print("Has File:", data5["has_file"])
    print("File Path:", data5["file_path"])
    print("Bot Reply:\n", data5["reply"])
    print("Raw Response Token:\n", data5["raw_response"])
    assert data5["has_file"] is True
    assert data5["file_path"].endswith(".docx")
    assert os.path.exists(data5["file_path"])
    assert "[FILE:" in data5["raw_response"]
    print("✅ TEST 5 PASSED: File .docx berhasil dibuat di storage dan token [FILE:...] dikirim!")

    # TEST 6: Document Generation (PDF)
    print("\n[TEST 6] Permintaan Pembuatan Dokumen PDF...")
    res6 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": "Tolong buatkan pdf ringkasan sistem moneter dan inflasi."
    })
    assert res6.status_code == 200
    data6 = res6.json()
    print("Has File:", data6["has_file"])
    print("File Path:", data6["file_path"])
    assert data6["has_file"] is True
    assert data6["file_path"].endswith(".pdf")
    assert os.path.exists(data6["file_path"])
    print("✅ TEST 6 PASSED: File .pdf berhasil dibuat di storage!")

    # TEST 7: Mock Bridge Endpoints
    print("\n[TEST 7] Simulasi Dispatch Endpoint Bridge (/send-message & /send-file)...")
    res_mock_msg = client.post("/send-message", json={
        "to": test_sender,
        "message": "Pesan tes langsung ke bridge"
    })
    assert res_mock_msg.status_code == 200
    assert res_mock_msg.json()["status"] == "delivered"

    res_mock_file = client.post("/send-file", json={
        "to": test_sender,
        "filePath": data5["file_path"],
        "caption": "Lampiran Dokumen Word APBN"
    })
    assert res_mock_file.status_code == 200
    assert res_mock_file.json()["status"] == "delivered"
    # TEST 8: Menu & Help Command
    print("\n[TEST 8] Pengecekan Menu Bantuan...")
    res8 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": "menu"
    })
    assert res8.status_code == 200
    data8 = res8.json()
    print("Bot Reply:\n", data8["reply"][:200], "...")
    assert "PANDUAN LENGKAP FITUR" in data8["reply"]
    print("✅ TEST 8 PASSED: Menu bantuan dan fitur berhasil ditampilkan!")

    # TEST 9: System Hardware & Resource Monitoring
    print("\n[TEST 9] Pengecekan Status Laptop (CPU/RAM/Disk/Baterai)...")
    res9 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": "status laptop"
    })
    assert res9.status_code == 200
    data9 = res9.json()
    print("Bot Reply:\n", data9["reply"])
    assert "STATUS KESEHATAN LAPTOP" in data9["reply"]
    assert "RAM" in data9["reply"]
    print("✅ TEST 9 PASSED: Status hardware laptop berhasil dimonitor!")

    # TEST 10: Top Processes
    print("\n[TEST 10] Pengecekan Top Proses Laptop...")
    res10 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": "top proses"
    })
    assert res10.status_code == 200
    data10 = res10.json()
    print("Bot Reply:\n", data10["reply"])
    assert "PROSES TERBESAR" in data10["reply"]
    print("✅ TEST 10 PASSED: Top proses RAM berhasil didaftarkan!")

    # TEST 11: File Manager (List Files & Dispatch)
    print("\n[TEST 11] Pengecekan Manajemen Berkas & Riwayat Dokumen...")
    res11 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": "daftar file"
    })
    assert res11.status_code == 200
    data11 = res11.json()
    print("Bot Reply:\n", data11["reply"])
    assert "DAFTAR BERKAS TERAKHIR" in data11["reply"]
    print("✅ TEST 11 PASSED: Daftar berkas berhasil dimuat!")

    # TEST 12: Storage Help Guide
    print("\n[TEST 12] Pengecekan Panduan Pengelolaan & Edit Penyimpanan Laptop...")
    res12 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": "menu penyimpanan"
    })
    assert res12.status_code == 200
    data12 = res12.json()
    assert "PANDUAN LENGKAP PENGELOLAAN & EDIT PENYIMPANAN LAPTOP" in data12["reply"]
    print("✅ TEST 12 PASSED: Menu panduan penyimpanan berhasil!")

    # TEST 13: List Folder (Explore Directory)
    print("\n[TEST 13] Menjelajah Direktori / Folder Laptop (list folder)...")
    res13 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": "list folder"
    })
    assert res13.status_code == 200
    data13 = res13.json()
    assert "ISI FOLDER LAPTOP" in data13["reply"]
    print("✅ TEST 13 PASSED: List folder laptop berhasil ditampilkan!")

    # TEST 14: Create New Directory (Folder)
    test_subfolder = "storage/test_storage_mgmt"
    print(f"\n[TEST 14] Membuat Folder Baru: {test_subfolder}...")
    res14 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": f"buat folder {test_subfolder}"
    })
    assert res14.status_code == 200
    data14 = res14.json()
    assert "Folder Berhasil Dibuat" in data14["reply"] or "Folder sudah ada" in data14["reply"]
    print("✅ TEST 14 PASSED: Pembuatan folder baru berhasil!")

    # TEST 15: Write / Create New File with Content
    test_filepath = f"{test_subfolder}/catatan_rahasia.txt"
    print(f"\n[TEST 15] Menulis Berkas Baru ({test_filepath})...")
    res15 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": f"tulis file {test_filepath} isi Halo dunia! Ini adalah catatan pengujian bot WA."
    })
    assert res15.status_code == 200
    data15 = res15.json()
    assert "Berkas Berhasil Ditulis / Disimpan" in data15["reply"]
    print("✅ TEST 15 PASSED: Penulisan berkas baru berhasil!")

    # TEST 16: Read File Content
    print(f"\n[TEST 16] Membaca Isi Berkas ({test_filepath})...")
    res16 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": f"baca file {test_filepath}"
    })
    assert res16.status_code == 200
    data16 = res16.json()
    assert "Halo dunia! Ini adalah catatan pengujian bot WA." in data16["reply"]
    print("✅ TEST 16 PASSED: Pembacaan isi berkas berhasil!")

    # TEST 17: Append / Edit File Content
    print(f"\n[TEST 17] Menambahkan Teks Baru ke Berkas (Edit/Append)...")
    res17 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": f"tambah file {test_filepath} isi Baris 2: Tambahan catatan baru via WhatsApp."
    })
    assert res17.status_code == 200
    data17 = res17.json()
    assert "Berhasil" in data17["reply"] and "Berkas" in data17["reply"]

    # Verify both lines exist
    res17_read = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": f"baca file {test_filepath}"
    })
    assert "Baris 2: Tambahan catatan baru via WhatsApp." in res17_read.json()["reply"]
    print("✅ TEST 17 PASSED: Penambahan/edit isi berkas berhasil diverifikasi!")

    # TEST 18: Rename / Move File
    renamed_filepath = f"{test_subfolder}/catatan_final.txt"
    print(f"\n[TEST 18] Mengganti Nama Berkas...")
    res18 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": f"ganti nama file {test_filepath} ke {renamed_filepath}"
    })
    assert res18.status_code == 200
    data18 = res18.json()
    assert "Berhasil Mengganti Nama" in data18["reply"]
    print("✅ TEST 18 PASSED: Rename berkas berhasil!")

    # TEST 19: Dispatch Laptop File via WhatsApp
    print(f"\n[TEST 19] Mengunduh & Mengirim Berkas Fisik Laptop ke WhatsApp...")
    res19 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": f"kirim file {renamed_filepath}"
    })
    assert res19.status_code == 200
    data19 = res19.json()
    assert data19["has_file"] is True
    assert "catatan_final.txt" in data19["file_path"]
    print("✅ TEST 19 PASSED: Berkas fisik berhasil dipaketkan dengan token [FILE:...]!")

    # TEST 20: Safe Delete File & Folder
    print(f"\n[TEST 20] Menghapus Berkas dan Folder Uji Coba...")
    res20_file = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": f"hapus file {renamed_filepath}"
    })
    assert res20_file.status_code == 200
    assert "Berkas Berhasil Dihapus" in res20_file.json()["reply"]

    res20_folder = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": f"hapus folder {test_subfolder}"
    })
    assert res20_folder.status_code == 200
    assert "Folder Berhasil Dihapus" in res20_folder.json()["reply"]
    print("✅ TEST 20 PASSED: Penghapusan berkas dan folder berhasil!")

    # TEST 21: Security Protection against deleting system directory
    print(f"\n[TEST 21] Pengujian Proteksi Keamanan Terhadap Penghapusan Folder Sistem...")
    res21 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": "hapus folder C:\\Windows"
    })
    assert res21.status_code == 200
    assert "Tindakan Berbahaya Dicegah" in res21.json()["reply"]
    print("✅ TEST 21 PASSED: Proteksi keamanan folder sistem aktif!")

    # TEST 22: Natural Language Capabilities Understanding ("Anda bisa melakukan apa saja")
    print("\n[TEST 22] Natural Language Capabilities ('Anda bisa melakukan apa saja')...")
    res22 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": "Anda bisa melakukan apa saja"
    })
    assert res22.status_code == 200
    assert "PANDUAN LENGKAP FITUR" in res22.json()["reply"]
    print("✅ TEST 22 PASSED: Pertanyaan kapabilitas natural dijawab dengan panduan eksekutif!")

    # TEST 23: Wi-Fi & Network Diagnostics ("terhubung ke wi-fi apa")
    print("\n[TEST 23] Diagnostik Jaringan & Wi-Fi ('terhubung ke wi-fi apa')...")
    res23 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": "Tolong beritahu saya berdasarkan perangkat anda sedang terhubung ke wi-fi apa"
    })
    assert res23.status_code == 200
    assert "STATUS" in res23.json()["reply"] and ("WI-FI" in res23.json()["reply"] or "JARINGAN" in res23.json()["reply"])
    print("✅ TEST 23 PASSED: Wi-Fi & koneksi jaringan laptop berhasil dideteksi real-time!")

    # TEST 24: Direct Battery Status ("Berapa persentase baterai laptop saya")
    print("\n[TEST 24] Pertanyaan Baterai Spesifik ('Berapa persentase baterai laptop saya')...")
    res24 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": "Berapa persentase baterai laptop saya"
    })
    assert res24.status_code == 200
    assert "BATERAI" in res24.json()["reply"] and "%" in res24.json()["reply"]
    print("✅ TEST 24 PASSED: Respon baterai fokus dan akurat!")

    # TEST 25: Natural Folder Query ("Di folder download ada file apa aja")
    print("\n[TEST 25] Jelajah Folder Bahasa Alami ('Di folder download ada file apa aja')...")
    res25 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": "Di folder download ada file apa aja"
    })
    assert res25.status_code == 200
    assert "ISI FOLDER LAPTOP" in res25.json()["reply"]
    print("✅ TEST 25 PASSED: Folder Downloads berhasil dijelajah via pertanyaan alami!")

    # TEST 26: Financial & Equity Reasoning ("Menurutmu bagaimana prospek saham BBCA?")
    print("\n[TEST 26] Penalaran Finansial & Valuasi Saham BBCA...")
    res26 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": "Menurutmu bagaimana prospek saham BBCA?"
    })
    assert res26.status_code == 200
    assert "ANALISIS PASAR MODAL" in res26.json()["reply"]
    assert "BBCA" in res26.json()["reply"]
    assert "Economic Moat" in res26.json()["reply"] or "Fundamental" in res26.json()["reply"]
    print("✅ TEST 26 PASSED: Penalaran finansial pasar modal profesional & logis!")

    # TEST 27: System Troubleshooting Reasoning ("mengatasi laptop lemot")
    print("\n[TEST 27] Penalaran Diagnostik Kinerja Laptop Lemot...")
    res27 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Budi",
        "text": "Kenapa laptop saya terasa lemot dan bagaimana solusinya?"
    })
    assert res27.status_code == 200
    assert "DIAGNOSTIK LOGIS KINERJA SISTEM LAPTOP" in res27.json()["reply"]
    assert "Drive C" in res27.json()["reply"]
    print("✅ TEST 27 PASSED: Penalaran troubleshooting laptop logis dan terhubung status real-time!")

    print("\n" + "=" * 60)
    print("🎉 SEMUA TEST BERHASIL LULUS 100%!")
    print("=" * 60)

if __name__ == "__main__":
    test_full_bot_workflow()


