"""System Prompt Manager for WhatsApp Antigravity Bot.

Allows admin to view, update, customize, and reset the active AI System Prompt / Persona.
Changes persist in storage/custom_system_prompt.txt and take effect immediately.
"""

import os
from typing import Optional

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage")
PROMPT_FILE = os.path.join(STORAGE_DIR, "custom_system_prompt.txt")


class PromptManager:
    """Manages custom dynamic system prompt overrides."""

    def __init__(self, prompt_path: str = PROMPT_FILE):
        self.prompt_path = prompt_path
        os.makedirs(os.path.dirname(self.prompt_path), exist_ok=True)

    def get_custom_prompt(self) -> Optional[str]:
        """Returns the custom prompt if saved and non-empty, else None."""
        if os.path.exists(self.prompt_path):
            try:
                with open(self.prompt_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    return content if content else None
            except Exception as e:
                print(f"[PromptManager] Gagal membaca custom prompt: {e}")
        return None

    def set_custom_prompt(self, new_prompt: str) -> str:
        """Saves a new custom system prompt / persona."""
        clean = new_prompt.strip()
        if not clean:
            return "❌ Teks sistem prompt tidak boleh kosong."

        try:
            with open(self.prompt_path, "w", encoding="utf-8") as f:
                f.write(clean)
            return (
                "✅ *SISTEM PROMPT BERHASIL DIPERBARUI!* 🎯\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"📝 *Instruksi/Persona Baru*:\n{clean}\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "🤖 *Status*: AI akan langsung patuh pada arahan dan kepribadian baru ini mulai pesan berikutnya!\n"
                "💡 _Ketik `/resetprompt` untuk mengembalikan ke prompt default bawaan._"
            )
        except Exception as e:
            return f"❌ Gagal menyimpan sistem prompt: {e}"

    def reset_custom_prompt(self) -> str:
        """Removes the custom system prompt and reverts to default."""
        if os.path.exists(self.prompt_path):
            try:
                os.remove(self.prompt_path)
                return "🔄 *Sistem prompt berhasil di-reset ke mode default bawaan (Hermes Senior DevOps AI Agent).* ✅"
            except Exception as e:
                return f"❌ Gagal mereset sistem prompt: {e}"
        return "ℹ️ Sistem prompt saat ini sudah menggunakan mode default bawaan."

    def get_active_prompt_display(self, default_prompt: str) -> str:
        """Returns readable display of current active prompt."""
        custom = self.get_custom_prompt()
        if custom:
            return (
                "🎯 *STATUS SISTEM PROMPT AKTIF (MODE KUSTOM)*\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"{custom}\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "💡 *Info*: Bot saat ini mengikuti persona kustom Anda.\n"
                "• Ketik `/sistem prom [teks baru]` untuk mengubahnya.\n"
                "• Ketik `/resetprompt` untuk kembali ke default."
            )
        else:
            preview = default_prompt.strip()[:400]
            return (
                "⚙️ *STATUS SISTEM PROMPT AKTIF (MODE DEFAULT)*\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"{preview}...\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "💡 *Info*: Belum ada custom prompt yang aktif.\n"
                "Anda bisa mengatur persona atau sistem prompt kustom kapan saja:\n"
                "`/sistem prom [isi instruksi / persona yang Anda inginkan]`"
            )


# Singleton
prompt_manager = PromptManager()

def atur_sistem_prompt(instruksi_baru: str) -> str:
    """Mengubah dan memperbarui sistem prompt atau kepribadian bot secara permanen."""
    return prompt_manager.set_custom_prompt(instruksi_baru)

def reset_sistem_prompt() -> str:
    """Mereset sistem prompt bot kembali ke pengaturan default."""
    return prompt_manager.reset_custom_prompt()

def lihat_sistem_prompt() -> str:
    """Melihat sistem prompt yang sedang aktif saat ini."""
    from agent_service import AntigravityAgent
    return prompt_manager.get_active_prompt_display(AntigravityAgent.SYSTEM_PROMPT_ADMIN)
