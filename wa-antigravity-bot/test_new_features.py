"""Unit tests for new features: Terminal Access, Experience Learning & Self-Aware Humility."""

import os
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
import main
main.ENABLE_LOCAL_DISPATCH = False
from main import app
from agent_service import agent_service, SECURITY_CODE
from tools.memory_manager import memory_manager

client = TestClient(app)
test_user = "test_user_6281"

def run_tests():
    print("=" * 60)
    print("🧪 TESTING NEW FEATURES: TERMINAL, MEMORY LEARNING & HUMILITY")
    print("=" * 60)

    # 1. Verify user
    agent_service.security.verified_users.add(test_user)

    # 2. Test Terminal execution
    print("\n[TEST A] Terminal Execution (terminal hostname)...")
    res_term = client.post("/webhook/whatsapp", json={
        "from": test_user,
        "sender_name": "Anto",
        "text": "terminal hostname"
    })
    assert res_term.status_code == 200
    reply = res_term.json()["reply"]
    print("Reply:\n", reply)
    assert "Terminal" in reply
    assert "Command*: `hostname`" in reply
    print("✅ TEST A PASSED: Terminal berhasil dieksekusi!")

    # 3. Test Terminal Safety (Blocked Command)
    print("\n[TEST B] Terminal Blocked Command (format c:)...")
    res_blocked = client.post("/webhook/whatsapp", json={
        "from": test_user,
        "sender_name": "Anto",
        "text": "terminal format c:"
    })
    assert res_blocked.status_code == 200
    reply_b = res_blocked.json()["reply"]
    print("Reply:\n", reply_b)
    assert "Akses Ditolak" in reply_b
    print("✅ TEST B PASSED: Perintah destruktif berhasil diblokir!")

    # 4. Test Memory Learning ("ingat: ...")
    print("\n[TEST C] Belajar Fakta Baru ('ingat: laptop saya RAM 16GB dual channel')...")
    res_learn = client.post("/webhook/whatsapp", json={
        "from": test_user,
        "sender_name": "Anto",
        "text": "ingat: laptop saya RAM 16GB dual channel dan suka dipakai buat koding python"
    })
    assert res_learn.status_code == 200
    reply_c = res_learn.json()["reply"]
    print("Reply:\n", reply_c)
    assert "memori" in reply_c.lower() or "mencatat" in reply_c.lower()
    print("✅ TEST C PASSED: Bot mencatat/mengingat fakta ke memori!")

    # 5. Test Memory Query ("apa yang kamu ingat")
    print("\n[TEST D] Memeriksa Memori Pengalaman ('apa yang kamu ingat')...")
    res_mem = client.post("/webhook/whatsapp", json={
        "from": test_user,
        "sender_name": "Anto",
        "text": "apa yang kamu ingat"
    })
    assert res_mem.status_code == 200
    reply_d = res_mem.json()["reply"]
    print("Reply:\n", reply_d)
    assert "MEMORI & PENGALAMAN" in reply_d
    assert "dual channel" in reply_d
    print("✅ TEST D PASSED: Daftar memori dan profil laptop berhasil ditampilkan!")

    # 6. Test Humility / Self-Awareness ("kamu kaku banget dan sok pinter")
    print("\n[TEST E] Uji Coba Koreksi Pengguna ('jangan sok pinter kaku banget')...")
    res_humble = client.post("/webhook/whatsapp", json={
        "from": test_user,
        "sender_name": "Anto",
        "text": "kenapa kamu kaku banget dan sok pinter coba lebih santai"
    })
    assert res_humble.status_code == 200
    reply_e = res_humble.json()["reply"]
    print("Reply:\n", reply_e)
    assert any(w in reply_e.lower() for w in ["maaf", "ampun", "santai", "antigravity bot"])
    print("✅ TEST E PASSED: Bot merespon dengan rendah hati, sadar diri, dan mencatat koreksi!")

    print("\n" + "=" * 60)
    print("🎉 SEMUA TEST FITUR BARU LULUS 100%!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
