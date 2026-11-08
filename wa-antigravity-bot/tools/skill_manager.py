"""Skill Manager for WhatsApp Antigravity Bot.

Allows user/admin to create, view, list, delete, and execute custom skills.
Active skills are automatically persisted in storage/skills.json and injected
into the agent's system prompt context.
"""

import os
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage")
SKILLS_FILE = os.path.join(STORAGE_DIR, "skills.json")


class SkillManager:
    """Manages custom bot skills with persistence."""

    def __init__(self, storage_path: str = SKILLS_FILE):
        self.storage_path = storage_path
        self._ensure_storage()
        self.skills: Dict[str, Dict[str, Any]] = self._load()

    def _ensure_storage(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2, ensure_ascii=False)

    def _load(self) -> Dict[str, Dict[str, Any]]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[SkillManager] Gagal memuat skills: {e}")
            return {}

    def _save(self):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.skills, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[SkillManager] Gagal menyimpan skills: {e}")

    def normalize_name(self, name: str) -> str:
        """Sanitizes skill name into snake_case lowercase."""
        clean = re.sub(r"[^\w\s-]", "", name.strip().lower())
        return re.sub(r"[-\s]+", "_", clean)

    def buat_skill(self, nama: str, deskripsi: str, instruksi: str) -> str:
        """Membuat skill baru atau memperbarui skill yang ada."""
        clean_name = self.normalize_name(nama)
        if not clean_name:
            return "❌ Nama skill tidak valid. Gunakan huruf atau angka (contoh: ringkas_teks, penerjemah, pembuat_puisi)."

        if not instruksi.strip():
            return "❌ Instruksi skill tidak boleh kosong. Berikan panduan lengkap bagaimana bot harus bertindak saat skill ini aktif."

        is_update = clean_name in self.skills
        self.skills[clean_name] = {
            "name": clean_name,
            "display_name": nama.strip(),
            "description": deskripsi.strip() or "Skill kustom pengguna",
            "instructions": instruksi.strip(),
            "created_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        self._save()

        action = "diperbarui" if is_update else "berhasil dibuat"
        return (
            f"✨ *Skill '{clean_name}' {action}!*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 *Nama*: `{clean_name}`\n"
            f"📝 *Deskripsi*: {deskripsi.strip()}\n"
            f"🎯 *Instruksi*: {instruksi.strip()[:150]}{'...' if len(instruksi) > 150 else ''}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 *Cara Pakai*: Ketik `/pakaiskill {clean_name} [pesan]` atau minta AI secara langsung!"
        )

    def lihat_skill(self, nama: Optional[str] = None) -> str:
        """Menampilkan daftar semua skill atau detail skill tertentu."""
        if not self.skills:
            return (
                "📭 *Belum ada skill kustom yang dibuat.*\n\n"
                "💡 Anda bisa membuat skill baru dengan format:\n"
                "`/buatskill [nama] | [deskripsi] | [instruksi]`\n\n"
                "Contoh:\n"
                "`/buatskill penerjemah_gaul | Terjemahkan ke bahasa gaul Jaksel | Terjemahkan kalimat input pengguna ke dalam gaya bahasa anak Jaksel yang gaul santai.`"
            )

        if nama:
            clean_name = self.normalize_name(nama)
            if clean_name in self.skills:
                s = self.skills[clean_name]
                return (
                    f"🎯 *DETAIL SKILL: {s.get('name')}*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📌 *Nama*: `{s.get('name')}`\n"
                    f"📝 *Deskripsi*: {s.get('description')}\n"
                    f"📅 *Dibuat*: {s.get('created_at')}\n"
                    f"📋 *Panduan Instruksi*:\n{s.get('instructions')}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━"
                )
            else:
                return f"⚠️ Skill `{clean_name}` tidak ditemukan. Ketik `/listskill` untuk melihat daftar semua skill."

        lines = [
            f"🛠️ *DAFTAR SKILL AKTIF BOT ({len(self.skills)} Skill)*",
            "━━━━━━━━━━━━━━━━━━━━━"
        ]
        for idx, (k, s) in enumerate(self.skills.items(), 1):
            lines.append(f"{idx}. *`{k}`* — {s.get('description', '')}")

        lines.extend([
            "━━━━━━━━━━━━━━━━━━━━━",
            "💡 *Perintah Skill*:",
            "• `/lihatskill [nama]` — Cek detail & instruksi",
            "• `/buatskill [nama] | [deskripsi] | [instruksi]` — Tambah skill baru",
            "• `/hapusskill [nama]` — Hapus skill",
            "• `/pakaiskill [nama] [teks]` — Jalankan skill secara eksplisit"
        ])
        return "\n".join(lines)

    def hapus_skill(self, nama: str) -> str:
        """Menghapus skill kustom berdasarkan nama."""
        clean_name = self.normalize_name(nama)
        if clean_name in self.skills:
            del self.skills[clean_name]
            self._save()
            return f"🗑️ *Skill `{clean_name}` berhasil dihapus.*"
        return f"⚠️ Skill `{clean_name}` tidak ditemukan dalam sistem."

    def get_skill_instructions(self, nama: str) -> Optional[str]:
        """Mengambil teks instruksi lengkap suatu skill."""
        clean_name = self.normalize_name(nama)
        skill = self.skills.get(clean_name)
        if skill:
            return skill.get("instructions")
        return None

    def get_skills_context_prompt(self) -> str:
        """Menghasilkan teks konteks ringkas daftar skill untuk diinjeksi ke system prompt."""
        if not self.skills:
            return ""

        lines = [
            "\n[ACTIVE CUSTOM SKILLS & CAPABILITIES CREATED BY ADMIN]:",
            "Admin telah membekali Anda dengan skill-skill khusus berikut. Jika permintaan admin berkaitan dengan skill ini, Anda WAJIB menerapkan instruksinya secara akurat:"
        ]
        for name, data in self.skills.items():
            lines.append(f"- Skill '{name}': {data.get('description', '')}. Instruksi: {data.get('instructions', '')}")

        return "\n".join(lines) + "\n"


# Singleton instance
skill_manager = SkillManager()

# Export wrapper functions for AI function calling
def buat_skill(nama: str, deskripsi: str, instruksi: str) -> str:
    """Membuat atau memperbarui skill kustom baru pada AI bot."""
    return skill_manager.buat_skill(nama, deskripsi, instruksi)

def lihat_skill(nama: Optional[str] = None) -> str:
    """Melihat daftar semua skill kustom bot atau detail skill tertentu."""
    return skill_manager.lihat_skill(nama)

def hapus_skill(nama: str) -> str:
    """Menghapus skill kustom bot berdasarkan nama."""
    return skill_manager.hapus_skill(nama)

def get_skills_prompt() -> str:
    """Mendapatkan instruksi semua skill aktif untuk system prompt."""
    return skill_manager.get_skills_context_prompt()
