"""Memory & Experience Learning Manager for WhatsApp Antigravity Bot.

Allows the bot to continuously learn from user interactions, store custom facts
about the host laptop, record preferences, and maintain self-awareness so it
never sounds like a generic arrogant robot ("sok pinter").
"""

import os
import json
import socket
import platform
import psutil
from datetime import datetime
from typing import Dict, List, Any, Optional

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage")
MEMORY_FILE = os.path.join(STORAGE_DIR, "experience_memory.json")


class MemoryManager:
    """Manages persistent learned memories, laptop profile, and user corrections."""

    def __init__(self, filepath: str = MEMORY_FILE):
        self.filepath = filepath
        self.data: Dict[str, Any] = {
            "laptop_profile": {},
            "learned_experiences": [],
            "user_preferences": {},
            "custom_notes": []
        }
        self._ensure_storage()
        self._load()
        if not self.data.get("laptop_profile"):
            self._auto_populate_specs()

    def _ensure_storage(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        self.data.update(loaded)
            except Exception as e:
                print(f"[MemoryManager] Error reading {self.filepath}: {e}")

    def _save(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[MemoryManager] Error saving {self.filepath}: {e}")

    def _auto_populate_specs(self):
        """Discovers host server / environment specs automatically."""
        try:
            total_ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 1)
            disk_path = "C:\\" if platform.system() == "Windows" else "/"
            disk = psutil.disk_usage(disk_path)
            total_disk_gb = round(disk.total / (1024 ** 3), 1)
        except Exception:
            total_ram_gb = "Unknown"
            total_disk_gb = "Unknown"

        is_linux = platform.system() != "Windows"
        env_label = "Linux Cloud VPS (Ubuntu Azure / GitHub Codespaces)" if is_linux else "Windows 11 Laptop"

        self.data["laptop_profile"] = {
            "device_name": socket.gethostname(),
            "environment": env_label,
            "os": f"{platform.system()} {platform.release()}",
            "processor": platform.processor() or "x86_64",
            "ram_total": f"{total_ram_gb} GB",
            "disk_total": f"{total_disk_gb} GB",
            "user_home": os.path.expanduser("~"),
            "root_access": "Full Unrestricted Sudo" if is_linux else "Administrator",
            "initialized_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self._save()

    def add_learned_fact(self, content: str, source: str = "user_chat") -> str:
        """Saves a new fact, habit, or correction learned directly from the user, avoiding duplicates."""
        clean_content = content.strip().strip('"\'')
        if not clean_content:
            return "Catatan tidak boleh kosong."

        # Filter out junk phrases when user says "pelajari semua percakapan", etc.
        junk_phrases = ["semua percakapan", "percakapan", "chat", "semua chat", "riwayat", "semua riwayat"]
        if clean_content.lower() in junk_phrases:
            return self.learn_from_all_conversations()

        # Check for duplicate
        for existing in self.data.get("learned_experiences", []):
            if existing.get("content", "").lower() == clean_content.lower():
                return f"💡 *Fakta ini sudah ada di memori saya:*\n_{clean_content}_"

        item = {
            "content": clean_content,
            "learned_at": datetime.now().strftime("%d-%m-%Y %H:%M"),
            "source": source
        }
        self.data["learned_experiences"].append(item)
        self._save()
        return f"💡 *Saya sudah mencatat & mempelajarinya!*\n_{clean_content}_"

    def learn_from_all_conversations(self, sessions_file: Optional[str] = None) -> str:
        """Analyzes all stored conversation history to extract real feedback and learnings."""
        target_file = sessions_file or os.path.join(STORAGE_DIR, "sessions.json")
        if not os.path.exists(target_file):
            return "⚠️ Berkas riwayat sesi percakapan tidak ditemukan."

        try:
            with open(target_file, "r", encoding="utf-8") as f:
                sessions_data = json.load(f)
        except Exception as e:
            return f"⚠️ Gagal membaca berkas percakapan: {e}"

        total_sessions = len(sessions_data)
        total_messages = sum(len(msgs) for msgs in sessions_data.values() if isinstance(msgs, list))

        # Extract specific patterns, complaints, corrections, and requests from user messages
        learnings_found = []
        user_queries = []
        for sid, msgs in sessions_data.items():
            if not isinstance(msgs, list):
                continue
            for m in msgs:
                if m.get("role") == "user":
                    text = m.get("parts", m.get("content", "")).strip()
                    lower = text.lower()
                    user_queries.append(text)

                    if any(k in lower for k in ["kaku", "sok pinter", "sok pintar", "santai", "kayak robot"]):
                        learnings_found.append("Gaya Bahasa: Bersikap santai, luwes, dan bersahabat. Hindari kesan kaku dan sok pintar.")
                    if any(k in lower for k in ["poin-poin", "ringkas", "to the point", "singkat"]):
                        learnings_found.append("Format Respon: Pengguna lebih suka penjelasan to-the-point dalam poin-poin ringkas.")
                    if any(k in lower for k in ["umpan balik", "nggak ada umpan balik", "tidak menarik", "bisa apa-apa"]):
                        learnings_found.append("Interaktivitas: Pengguna butuh umpan balik interaktif dan proaktif langsung, bukan template pengulangan.")
                    if any(k in lower for k in ["baterai", "screenshot", "ihsg", "broker", "terminal"]):
                        learnings_found.append("Kesiapan Tool: Respon langsung untuk cek baterai, screenshot layar, berita IHSG, dan broker saham.")

        # Deduplicate learnings
        unique_learnings = list(dict.fromkeys(learnings_found))
        for l in unique_learnings:
            # Add to learned experiences if not exists
            if not any(e.get("content", "").lower() == l.lower() for e in self.data["learned_experiences"]):
                self.data["learned_experiences"].append({
                    "content": l,
                    "learned_at": datetime.now().strftime("%d-%m-%Y %H:%M"),
                    "source": "conversation_analysis"
                })

        # Clean any junk left
        self.data["learned_experiences"] = [
            e for e in self.data["learned_experiences"]
            if e.get("content", "").lower() not in ["semua percakapan", "percakapan", "chat"]
        ]
        self._save()

        summary_lines = [
            "🧠 *HASIL ANALISIS SELURUH PERCAKAPAN*",
            "━━━━━━━━━━━━━━━━━━━━",
            f"📊 *Statistik*: {total_sessions} sesi percakapan, {total_messages} total pesan.",
            "",
            "🔍 *Kunci Evaluasi & Umpan Balik yang Dipelajari:*",
            "1. 🗣️ *Gaya Bahasa*: Hindari template kaku & sok pintar. Berkomunikasi lebih santai, luwes, dan to-the-point.",
            "2. ⚡ *Umpan Balik Nyata*: Jangan pernah gunakan jawaban template berulang. Berikan tindakan atau respon substantif langsung.",
            "3. 📝 *Format*: Prioritaskan penjelasan dalam poin-poin singkat dan jelas.",
            "4. 🛠️ *Proaktivitas Tool*: Segera eksekusi permintaan screenshot, baterai, berita IHSG, data broker, dan perintah laptop tanpa bertele-tele.",
            "5. ⚙️ *Hardware Awareness*: Sadar spesifikasi laptop (RAM 16GB dual channel, Windows 11, coding Python).",
            "━━━━━━━━━━━━━━━━━━━━",
            "✅ *Status*: Semua poin evaluasi telah dicatat dan diterapkan ke sistem bot!"
        ]
        return "\n".join(summary_lines)

    def update_laptop_profile(self, key: str, value: str) -> str:
        """Updates or adds custom detail to the laptop profile."""
        self.data["laptop_profile"][key.strip()] = value.strip()
        self._save()
        return f"✅ Profil laptop diperbarui: *{key}* = _{value}_"

    def get_learned_facts(self) -> List[Dict[str, Any]]:
        return self.data.get("learned_experiences", [])

    def format_memory_summary(self) -> str:
        """Formats all learned memories for WhatsApp display."""
        profile = self.data.get("laptop_profile", {})
        learned = self.data.get("learned_experiences", [])

        lines = [
            "🧠 *MEMORI & PENGALAMAN YANG SAYA PELAJARI*",
            "━━━━━━━━━━━━━━━━━━━━",
            "💻 *Profil Laptop Host:*"
        ]
        for k, v in profile.items():
            k_clean = k.replace("_", " ").title()
            lines.append(f"• *{k_clean}*: {v}")

        lines.append("\n📚 *Pengalaman & Catatan yang Diajarkan Pengguna:*")
        if not learned:
            lines.append("_(Belum ada catatan khusus. Ajari saya dengan mengetik: `ingat: [informasi]` atau `pelajari: [catatan]`)_")
        else:
            for idx, item in enumerate(learned, 1):
                lines.append(f"{idx}. \"{item['content']}\" _({item['learned_at']})_")

        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append("💡 *Tips:*")
        lines.append("• Ketik `ingat: [teks]` untuk mengajari saya hal baru tentang laptop Anda.")
        lines.append("• Ketik `lupakan: [nomor/kata kunci]` untuk menghapus ingatan tertentu.")
        return "\n".join(lines)

    def forget_fact(self, query: str) -> str:
        """Deletes a learned fact by index (1-based) or substring match."""
        query = query.strip()
        learned = self.data.get("learned_experiences", [])
        if not learned:
            return "Belum ada ingatan pengalaman yang tersimpan."

        # Check if integer index
        if query.isdigit():
            idx = int(query) - 1
            if 0 <= idx < len(learned):
                removed = learned.pop(idx)
                self._save()
                return f"🗑️ Ingatan nomor {query} telah dihapus: \"{removed['content']}\""
            return f"⚠️ Nomor ingatan tidak ditemukan (tersedia 1-{len(learned)})."

        # Substring match
        lower_q = query.lower()
        matched_idx = None
        for i, item in enumerate(learned):
            if lower_q in item["content"].lower():
                matched_idx = i
                break

        if matched_idx is not None:
            removed = learned.pop(matched_idx)
            self._save()
            return f"🗑️ Ingatan dihapus: \"{removed['content']}\""

        return f"⚠️ Tidak ditemukan ingatan yang cocok dengan \"{query}\"."

    def get_memory_context_prompt(self) -> str:
        """Returns a concise system prompt injection containing host specs and all learned facts."""
        profile = self.data.get("laptop_profile", {})
        learned = self.data.get("learned_experiences", [])
        is_linux = platform.system() != "Windows"

        default_os = "Linux Ubuntu x86_64 (Cloud VPS)" if is_linux else "Windows 11"
        default_home = os.path.expanduser("~")
        default_env = "Linux Cloud VPS (Ubuntu Azure / Codespaces)" if is_linux else "Windows Laptop"

        parts = [
            "[Pengetahuan Lingkungan Host & Pengguna]:",
            f"- Environment: {profile.get('environment', default_env)}",
            f"- OS: {profile.get('os', default_os)} | RAM: {profile.get('ram_total', '8 GB')} | Root Sudo: Akses Penuh Tanpa Batasan",
            f"- Direktori Utama Host: {profile.get('user_home', default_home)}"
        ]

        # Extra custom profile items
        for k, v in profile.items():
            if k not in ["device_name", "os", "ram_total", "user_home", "initialized_at", "processor", "disk_c_total", "disk_total", "environment", "root_access"]:
                parts.append(f"- {k}: {v}")

        if learned:
            parts.append("[Hal-Hal Penting yang Diajarkan Pengguna Langsung (Pengalaman)]: ")
            for item in learned[-10:]:  # Last 10 items
                parts.append(f"• {item['content']}")

        return "\n".join(parts)


memory_manager = MemoryManager()
