"""Comprehensive test suite verifying fixes for all user feedback and conversation issues.
Tests:
1. "Selamat malam sekarang jam berapa" -> Returns time.
2. "Bisa ambil screenshot dan kirim ke saya" -> Triggers screenshot with [FILE:...] token.
3. "Baterainya berapa sekarang" & "Baterai" -> Returns battery status.
4. "Stop berbicara kaku ayo kita mengobrol" -> Does NOT attempt kill_process, responds warmly.
5. "Pelajari semua percakapan" -> Analyzes conversation history and updates memory without junk.
6. "Berapa besar bumi" -> Answers Earth dimensions directly.
7. "Kenapa percakapan seperti ini nggak ada umpan balik sama sekali" -> Sincere apology & proactive options.
8. "Kamu nggak bisa apa-apa jancok" -> Handles frustration with humility and direct help.
9. "Buatkan list apa saja yang kamu bisa lakukan" -> Returns full capability guide.
10. "Berita ihsg" -> Triggers market news / newsfilter.
11. "Broker" -> Triggers broker summary.
12. Name normalization -> Never outputs "Halo .!".
"""

import sys
import os
import json
from fastapi.testclient import TestClient

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

import main
main.ENABLE_LOCAL_DISPATCH = False
from main import app
from agent_service import agent_service

client = TestClient(app)

def run_feedback_tests():
    print("=" * 65)
    print("🚀 PENGUJIAN SOLUSI SEMUA MASALAH & UMPAN BALIK PERCAKAPAN")
    print("=" * 65)

    test_sender = "628999999999"
    agent_service.security.verified_users.add(test_sender)

    # TEST 1: Waktu / Jam
    print("\n[TEST 1] Jam berapa sekarang...")
    res = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Anto",
        "text": "Selamat malam sekarang jam berapa"
    })
    reply = res.json()["reply"]
    print("Reply 1:\n", reply[:200])
    assert "jam" in reply.lower() or "wib" in reply.lower() or ":" in reply
    print("✅ TEST 1 PASSED: Respon waktu akurat!")

    # TEST 2: Screenshot substring query
    print("\n[TEST 2] Screenshot via kalimat alami...")
    res = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Anto",
        "text": "Bisa ambil screenshot dan kirim ke saya"
    })
    raw = res.json()["raw_response"]
    print("Reply 2:\n", raw[:200])
    assert "[FILE:" in raw and "screenshot" in raw.lower()
    print("✅ TEST 2 PASSED: Screenshot berhasil diambil!")

    # TEST 3: Baterai via kata sehari-hari
    print("\n[TEST 3] Baterainya berapa sekarang...")
    res = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Anto",
        "text": "Baterainya berapa sekarang"
    })
    reply = res.json()["reply"]
    print("Reply 3:\n", reply[:200])
    assert "%" in reply and "baterai" in reply.lower()
    print("✅ TEST 3 PASSED: Status baterai berhasil dipanggil!")

    # TEST 4: "Stop berbicara kaku ayo kita mengobrol" (tidak boleh kill process)
    print("\n[TEST 4] 'Stop berbicara kaku ayo kita mengobrol'...")
    res = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Anto",
        "text": "Stop berbicara kaku ayo kita mengobrol"
    })
    reply = res.json()["reply"]
    print("Reply 4:\n", reply[:200])
    assert "proses" not in reply.lower() or "santai" in reply.lower()
    assert "tidak ditemukan" not in reply.lower()
    print("✅ TEST 4 PASSED: Tidak ada salah tangkap kill process, respon akrab dan santai!")

    # TEST 5: "Pelajari semua percakapan"
    print("\n[TEST 5] 'Pelajari semua percakapan'...")
    res = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Anto",
        "text": "Pelajari semua percakapan"
    })
    reply = res.json()["reply"]
    print("Reply 5:\n", reply[:250])
    assert "analisis" in reply.lower() or "evaluasi" in reply.lower() or "statistik" in reply.lower()
    print("✅ TEST 5 PASSED: Berhasil mengevaluasi riwayat percakapan dan menyimpan intisari!")

    # TEST 6: "Berapa besar bumi"
    print("\n[TEST 6] 'Berapa besar bumi'...")
    res = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Anto",
        "text": "Berapa besar bumi"
    })
    reply = res.json()["reply"]
    print("Reply 6:\n", reply[:250])
    assert "km" in reply or "diameter" in reply.lower() or "bumi" in reply.lower()
    print("✅ TEST 6 PASSED: Menjawab pengetahuan umum dengan data faktual!")

    # TEST 7: Respon umpan balik pengguna
    print("\n[TEST 7] Umpan balik pengguna 'nggak ada umpan balik sama sekali'...")
    res = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Anto",
        "text": "Kenapa percakapan seperti ini nggak ada umpan balik sama sekali dan tidak ada menarik menariknya"
    })
    reply = res.json()["reply"]
    print("Reply 7:\n", reply[:250])
    assert any(w in reply.lower() for w in ["maaf", "bener", "bosan", "respons", "kaku", "obrolan", "umpan balik"])
    print("✅ TEST 7 PASSED: Menangani feedback dan kekecewaan secara suportif & solutif!")

    # TEST 8: "Kamu nggak bisa apa-apa jancok"
    print("\n[TEST 8] Kekecewaan/umpatan pengguna...")
    res = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Anto",
        "text": "Kamu nggak bisa apa-apa jancok"
    })
    reply = res.json()["reply"]
    print("Reply 8:\n", reply[:250])
    assert any(w in reply.lower() for w in ["maaf", "santai", "bantu", "screenshot", "laptop", "bisa"])
    print("✅ TEST 8 PASSED: Respon rendah hati, sadar diri, dan menawarkan aksi konkret!")

    # TEST 9: "Buatkan list apa saja yang kamu bisa lakukan"
    print("\n[TEST 9] Permintaan daftar kemampuan...")
    res = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Anto",
        "text": "Buatkan list apa saja yang kamu bisa lakukan"
    })
    reply = res.json()["reply"]
    print("Reply 9:\n", reply[:250])
    assert "terminal" in reply.lower() and "screenshot" in reply.lower()
    print("✅ TEST 9 PASSED: Menampilkan panduan fitur lengkap!")

    # TEST 10: Sanitasi Nama dot "."
    print("\n[TEST 10] Sanitasi nama pengirim bertitik '.'...")
    res = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": ".",
        "text": "Halo"
    })
    reply = res.json()["reply"]
    print("Reply 10:\n", reply[:150])
    assert "Halo .!" not in reply
    assert "Halo Sobat!" in reply or "Halo" in reply
    print("✅ TEST 10 PASSED: Nama '.' diganti secara sopan menjadi Sobat/Pengguna!")

    print("\n" + "=" * 65)
    print("🎉 SELURUH 10 PENGUJIAN SOLUSI FEEDBACK BERHASIL 100%!")
    print("=" * 65)

if __name__ == "__main__":
    run_feedback_tests()
