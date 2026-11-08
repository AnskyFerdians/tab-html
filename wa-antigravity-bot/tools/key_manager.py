"""Key Manager Tool for WhatsApp Antigravity Bot.

Allows admin to add, update, and manage AI API keys directly via WhatsApp chat:
- Groq (gsk_...)
- Google Gemini (AIzaSy..., AQ....)
- Grok xAI (xai-...)

Persists changes to .env file and hot-reloads runtime client state.
"""

import os
import re
from typing import Dict, Any, Tuple

ENV_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))

def update_env_file(key_name: str, key_val: str) -> bool:
    """Updates or appends a key-value pair in the .env file safely."""
    try:
        content = ""
        if os.path.exists(ENV_FILE):
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                content = f.read()

        # Check if key already exists
        pattern = rf"^{re.escape(key_name)}=.*$"
        if re.search(pattern, content, flags=re.MULTILINE):
            content = re.sub(pattern, f"{key_name}={key_val}", content, flags=re.MULTILINE)
        else:
            if content and not content.endswith("\n"):
                content += "\n"
            content += f"{key_name}={key_val}\n"

        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"[KeyManager Error] Gagal update .env: {e}")
        return False

def deteksi_jenis_key(api_key: str, jenis_hint: str = "") -> str:
    """Mendeteksi provider API key berdasarkan format/prefix."""
    k = api_key.strip()
    hint = (jenis_hint or "").lower()

    if "groq" in hint or k.startswith("gsk_"):
        return "GROQ"
    elif "grok" in hint or "xai" in hint or k.startswith("xai-"):
        return "GROK"
    elif "gemini" in hint or k.startswith("AIzaSy") or k.startswith("AQ."):
        return "GEMINI"
    
    # Default fallbacks
    if k.startswith("gsk_"):
        return "GROQ"
    elif k.startswith("xai-"):
        return "GROK"
    return "GEMINI"

def tambah_api_key(api_key: str, jenis: str = "") -> str:
    """Menambahkan atau memperbarui API key kecerdasan buatan (Groq, Gemini, Grok) langsung dari chat WhatsApp.
    
    Args:
        api_key: Token string API key yang diberikan pengguna (contoh: 'gsk_...', 'AIzaSy...', 'xai-...').
        jenis: Tipe penyedia jika ingin ditentukan eksplisit ('groq', 'gemini', 'grok').
    """
    if not api_key or not api_key.strip():
        return "⚠️ API Key tidak boleh kosong."

    clean_key = api_key.strip()
    provider = deteksi_jenis_key(clean_key, jenis)

    masked_key = clean_key[:7] + "..." + clean_key[-5:] if len(clean_key) > 14 else clean_key[:4] + "..."

    env_var_name = ""
    if provider == "GROQ":
        env_var_name = "GROQ_API_KEY"
    elif provider == "GROK":
        env_var_name = "GROK_API_KEY"
    elif provider == "GEMINI":
        # Check if GEMINI_API_KEY exists, if so check GEMINI_API_KEY_2, etc.
        gemini_primary = os.getenv("GEMINI_API_KEY", "").strip()
        if not gemini_primary or gemini_primary == clean_key:
            env_var_name = "GEMINI_API_KEY"
        else:
            env_var_name = "GEMINI_API_KEY_2"

    # Update .env file
    success = update_env_file(env_var_name, clean_key)
    # Set to current environment
    os.environ[env_var_name] = clean_key

    # Hot-reload in agent_service if loaded
    try:
        from agent_service import agent_service
        agent_service._init_llm()
        hot_reloaded = True
    except Exception as e:
        hot_reloaded = False
        print(f"[KeyManager] Hot reload note: {e}")

    if success:
        return (
            f"✅ *API Key {provider} Berhasil Ditambahkan!*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔑 Variabel: `{env_var_name}`\n"
            f"🔒 Token: `{masked_key}`\n"
            f"⚡ Status: *Langsung Aktif* (Hot-Reload {'Sukses' if hot_reloaded else 'Siap'})\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Bot sekarang dapat menggunakan kuota dari API Key ini secara otomatis."
        )
    else:
        return f"⚠️ Gagal menyimpan API Key {provider} ke konfigurasi sistem."
