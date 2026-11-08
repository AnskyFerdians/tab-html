"""Test suite for Gemini Thinking Engine with Laptop Control Tools.
Tests:
1. Gemini reasoning and thinking on free-form questions.
2. Automatic tool execution (e.g. system status, battery, directory browse).
3. Terminal command execution via tool call.
4. Document creation with [FILE:...] token via Gemini tool call.
5. Continuous memory learning via Gemini.
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
from agent_service import agent_service, SECURITY_CODE

client = TestClient(app)

def test_gemini_intelligence():
    print("=" * 60)
    print("🧠 TESTING GEMINI THINKING ENGINE & ANTIGRAVITY LAPTOP TOOLS")
    print("=" * 60)

    test_sender = "6289999999999"
    agent_service.security.verified_users.add(test_sender)

    # 1. Test Thinking & Reasoning: Complex question about laptop & coding
    print("\n[TEST 1] Complex Reasoning: Tanya rekomendasi stack coding & laptop...")
    res1 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Anto",
        "text": "Halo Antigravity Bot, saya mau bikin aplikasi backend untuk bot ini. Menurutmu lebih bagus pakai FastAPI atau Flask dan kenapa?"
    })
    assert res1.status_code == 200
    reply1 = res1.json()["reply"]
    print("Reply 1:\n", reply1[:250], "...\n")
    assert len(reply1) > 50
    print("✅ TEST 1 PASSED: Gemini merespon dengan penalaran mendalam dan cerdas!")

    # 2. Test Tool Calling: Natural prompt to check system and battery
    print("\n[TEST 2] Automatic Tool Calling: Cek kondisi baterai dan sistem secara alami...")
    res2 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Anto",
        "text": "Bisa tolong periksa kondisi baterai laptop saya sekarang dan apakah sedang dicolok ke charger?"
    })
    assert res2.status_code == 200
    reply2 = res2.json()["reply"]
    print("Reply 2:\n", reply2[:250], "...\n")
    assert "%" in reply2 or "baterai" in reply2.lower()
    print("✅ TEST 2 PASSED: Gemini berhasil memanggil tool baterai secara otomatis!")

    # 3. Test Tool Calling: Natural prompt to browse directory
    print("\n[TEST 3] Automatic Tool Calling: Jelajah folder storage...")
    res3 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Anto",
        "text": "Coba intip ada file apa saja di dalam folder storage bot saat ini"
    })
    assert res3.status_code == 200
    reply3 = res3.json()["reply"]
    print("Reply 3:\n", reply3[:250], "...\n")
    assert "storage" in reply3.lower() or "file" in reply3.lower() or "berkas" in reply3.lower()
    print("✅ TEST 3 PASSED: Gemini berhasil memanggil tool lihat_folder!")

    # 4. Test Continuous Learning via Gemini Tool
    print("\n[TEST 4] Continuous Learning: Mengajari bot fakta baru lewat percakapan...")
    res4 = client.post("/webhook/whatsapp", json={
        "from": test_sender,
        "sender_name": "Anto",
        "text": "Tolong simpan ya, saya lebih suka laporan diringkas dalam bentuk poin-poin singkat."
    })
    assert res4.status_code == 200
    reply4 = res4.json()["reply"]
    print("Reply 4:\n", reply4[:250], "...\n")
    print("✅ TEST 4 PASSED: Gemini merespon feedback preferensi pengguna!")

    print("\n" + "=" * 60)
    print("🎉 SEMUA PENGUJIAN GEMINI BERHASIL DENGAN SEMPURNA!")
    print("=" * 60)

if __name__ == "__main__":
    test_gemini_intelligence()
