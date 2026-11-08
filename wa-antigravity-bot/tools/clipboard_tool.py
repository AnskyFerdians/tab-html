"""Clipboard Tool for WhatsApp Antigravity Bot.

Allows reading and writing the Windows clipboard remotely via WhatsApp.
"""

import subprocess
from datetime import datetime


def read_clipboard() -> str:
    """Reads the current text content from the Windows clipboard."""
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-Command", "Get-Clipboard"],
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8",
            errors="replace"
        )

        content = result.stdout.strip()
        if not content:
            return (
                "📋 *Clipboard Laptop Kosong*\n"
                "ℹ️ _Tidak ada teks yang tersimpan di clipboard saat ini._"
            )

        # Truncate for WhatsApp
        truncated = ""
        if len(content) > 2000:
            content = content[:2000]
            truncated = "\n⚠️ _(Konten dipotong karena melebihi batas pesan WhatsApp)_"

        return (
            f"📋 *ISI CLIPBOARD LAPTOP*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🕐 Waktu: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"📏 Panjang: {len(content)} karakter\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"```\n{content}\n```"
            f"{truncated}"
        )
    except subprocess.TimeoutExpired:
        return "⏱️ Timeout membaca clipboard."
    except Exception as e:
        return f"❌ Gagal membaca clipboard: {str(e)}"


def write_clipboard(text: str) -> str:
    """Writes text to the Windows clipboard."""
    if not text or not text.strip():
        return "⚠️ Teks yang akan disalin ke clipboard tidak boleh kosong."

    try:
        # Use PowerShell Set-Clipboard
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-Command", f"Set-Clipboard -Value '{text.replace(chr(39), chr(39)+chr(39))}'"],
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8",
            errors="replace"
        )

        preview = text[:200] + "..." if len(text) > 200 else text
        return (
            f"✅ *Teks Berhasil Disalin ke Clipboard Laptop!*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 *Preview*:\n```\n{preview}\n```\n"
            f"📏 Panjang: {len(text)} karakter\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"ℹ️ _Teks siap di-paste (Ctrl+V) di aplikasi mana pun._"
        )
    except Exception as e:
        return f"❌ Gagal menulis ke clipboard: {str(e)}"
