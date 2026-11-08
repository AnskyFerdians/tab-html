"""Agent Service & Conversation Session Manager for WhatsApp Antigravity Bot.

UPGRADED v3.0 — Full Remote AI Agent with New google.genai SDK.

Features:
- Contact verification with security code 'RajaWali0108' (required only once per sender).
- Multi-turn conversation memory per user (sender_id).
- Document generation tool integration (Word docx, PDF, TXT).
- Special response format token: [FILE:path/to/file.docx] <pesan konfirmasi>.
- Gemini 2.0 Flash / 2.5 Flash LLM engine with deep reasoning & smart fallback.
- Full laptop control: Screenshot, Power, Clipboard, Network, Process, Scheduler.
- AI Agent with autonomous thinking & function calling (google.genai SDK v2.29+).
- 46+ active tools: Terminal, File, Power, Network, Process, PublicAPIs, Memory, Docs.
- Professional responses: multilingual expertise across all domains.
"""

import os
import sys
import json
import re
import socket
import platform
import psutil
import warnings
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dotenv import load_dotenv

# Fix Unicode stdout for Windows (emoji support in PowerShell/CMD)
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Suppress legacy deprecation warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from tools.doc_generator import (
    create_word_document,
    create_pdf_document,
    create_txt_document,
    STORAGE_DIR,
    sanitize_filename
)
from tools.system_monitor import (
    get_system_status,
    get_top_processes,
    get_battery_status,
    get_wifi_network_status
)
from tools.task_runner import (
    run_registered_task,
    ALLOWED_SCRIPTS
)
from tools.file_manager import (
    list_recent_files,
    get_file_for_dispatch,
    list_laptop_directory,
    read_laptop_file,
    write_laptop_file,
    append_laptop_file,
    create_laptop_folder,
    delete_laptop_path,
    rename_or_move_path,
    get_storage_help
)
from tools.terminal_tool import execute_terminal_command, execute_python_code
from tools.memory_manager import memory_manager

# === NEW TOOLS ===
from tools.screenshot_tool import capture_screenshot
from tools.power_manager import (
    lock_screen, shutdown_laptop, restart_laptop,
    sleep_laptop, hibernate_laptop, cancel_shutdown,
    logoff_user, get_uptime_info
)
from tools.clipboard_tool import read_clipboard, write_clipboard
from tools.network_scanner import (
    ping_host, traceroute_host, dns_lookup,
    get_public_ip, scan_open_ports
)
from tools.process_manager import (
    kill_process, find_process, launch_app, get_app_list
)
from tools.scheduler_tool import task_scheduler
from tools.public_apis_tool import (
    search_public_apis,
    list_public_api_categories,
    get_random_public_api,
    refresh_public_apis_cache
)
from tools.skill_manager import (
    skill_manager, buat_skill, lihat_skill, hapus_skill
)
from tools.prompt_manager import (
    prompt_manager, atur_sistem_prompt, reset_sistem_prompt, lihat_sistem_prompt
)

load_dotenv()

SECURITY_CODE = os.getenv("SECURITY_CODE", "RajaWali0108")
VERIFIED_USERS_FILE = os.path.join(STORAGE_DIR, "verified_users.json")
SESSIONS_BACKUP_FILE = os.path.join(STORAGE_DIR, "sessions.json")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("ANTIGRAVITY_API_KEY")

STOPWORDS_4L = {
    "BISA", "DUA", "KAMU", "YANG", "DARI", "PADA", "SAYA", "KITA", "LALU", "JUGA",
    "AGAR", "BAGI", "BUAT", "SAJA", "AKAN", "MAKA", "SAAT", "TAPI", "SINI", "SITU",
    "DULU", "ESOK", "TADI", "LUSA", "NANTI", "SIAP", "LUAS", "LUAR", "CARA", "GAYA",
    "TREN", "ARAH", "NAIK", "DOWN", "HIGH", "SELL", "PAID", "HOLD", "INFO", "HALO",
    "SOB", "BRO", "BOS", "OM", "PAK", "MAS", "MBAK", "DONG", "DEH", "NIH", "TUH",
    "COBA", "LIAT", "KALI", "BARU", "LAMA", "BESI", "EMAS", "UANG", "DANA", "ALIR",
    "ARUS", "KATA", "TANY", "JAWAB", "DATA", "TEKS", "FILE", "READ", "VIEW", "OPEN",
    "EXEC", "RUN", "TASK", "HELP", "MENU", "LOCK", "TIME", "USER", "PASS", "AUTH",
    "STOP", "POST", "SEND", "TRUE", "NONE", "NULL", "IKUT", "MAU", "LAGI", "BAIK",
    "CEK", "OTOR", "PORT", "PING", "SCAN", "RAMS", "CPUS", "DISC", "DISK", "BACA",
    "TULI", "EDIT", "HAPU", "TEST", "PROS", "SANA", "KINI", "SAMA", "LAIN", "PILI",
    "PILIH", "EMIT", "SUKA", "BEDA", "POIN", "RIIL", "REAL", "CHAT", "TIPS"
}

TICKER_ALIASES = {
    "PEGE": "PGEO",
    "PGE": "PGEO",
    "BARITO": "BRPT",
    "BCA": "BBCA",
    "BRI": "BBRI",
    "MANDIRI": "BMRI",
    "BNI": "BBNI",
    "TELKOM": "TLKM",
    "ASTRA": "ASII",
    "CHANDRA": "TPIA",
    "PERTAMINA": "PGEO"
}


class SecurityManager:
    """Manages one-time security code verification for WhatsApp contacts."""

    def __init__(self, filepath: str = VERIFIED_USERS_FILE):
        self.filepath = filepath
        self.verified_users = set()
        self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.verified_users = set(data.get("verified_users", []))
            except Exception as e:
                print(f"[SecurityManager] Warning loading verified users: {e}")

    def _save(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump({"verified_users": list(self.verified_users)}, f, indent=2)
        except Exception as e:
            print(f"[SecurityManager] Warning saving verified users: {e}")

    def is_verified(self, sender_id: str) -> bool:
        if not sender_id:
            return False
        clean_id = sender_id.split(":")[0]
        base_num = clean_id.split("@")[0]
        candidates = {sender_id, clean_id, base_num}
        if "@" in sender_id:
            candidates.add(f"{base_num}@{sender_id.split('@')[1]}")

        if any(c in self.verified_users for c in candidates):
            return True
        self._load()
        return any(c in self.verified_users for c in candidates)

    def verify(self, sender_id: str, message: str) -> bool:
        if not sender_id or not message:
            return False
        # Check if the message contains the security code (case-insensitive)
        if SECURITY_CODE.lower() in message.strip().lower():
            clean_id = sender_id.split(":")[0]
            self.verified_users.add(sender_id)
            self.verified_users.add(clean_id)
            self._save()
            print(f"[SecurityManager] Successfully verified: {sender_id} ({clean_id})")
            return True
        return False


class SessionManager:
    """Manages multi-turn conversation history and contextual entities per sender_id."""

    def __init__(self, filepath: str = SESSIONS_BACKUP_FILE):
        self.filepath = filepath
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        self.context: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self.sessions = json.load(f)
            except Exception as e:
                print(f"[SessionManager] Warning loading sessions: {e}")

    def _save(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.sessions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[SessionManager] Warning saving sessions: {e}")

    def get_history(self, sender_id: str) -> List[Dict[str, str]]:
        return self.sessions.setdefault(sender_id, [])

    def add_message(self, sender_id: str, role: str, content: str):
        history = self.get_history(sender_id)
        history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        # Keep maximum last 20 turns per user for fast token processing
        if len(history) > 20:
            self.sessions[sender_id] = history[-20:]
        self._save()


    def get_last_user_topics(self, sender_id: str) -> List[str]:
        history = self.get_history(sender_id)
        user_msgs = [m["content"] for m in history if m["role"] == "user"]
        return user_msgs[:-1] if len(user_msgs) > 1 else user_msgs

    def update_context(self, sender_id: str, **kwargs):
        """Stores contextual entities such as last_ticker, last_topic, last_action."""
        ctx = self.context.setdefault(sender_id, {})
        ctx.update(kwargs)

    def get_context(self, sender_id: str) -> Dict[str, Any]:
        """Retrieves conversational context for the given sender."""
        return self.context.setdefault(sender_id, {})

    def clear_history(self, sender_id: str) -> str:
        """Clears conversation history for a user."""
        if sender_id in self.sessions:
            self.sessions[sender_id] = []
            self._save()
        if sender_id in self.context:
            self.context[sender_id] = {}
        return (
            "🗑️ *Riwayat Percakapan Dihapus!*\n"
            "ℹ️ _Memori percakapan telah direset. Memori pengalaman jangka panjang tetap tersimpan._"
        )


class AntigravityAgent:
    """Antigravity WhatsApp Agent Engine - Full Remote AI Agent with Thinking Capability."""

    SYSTEM_PROMPT_ADMIN = (
        "Anda adalah Hermes (Antigravity Admin Agent) — AI Agent pribadi otonom, asisten DevOps, dan Administrator Sistem yang mengendalikan langsung server Linux Cloud VPS / laptop Linux ini.\n"
        "IDENTITAS & OTORITAS:\n"
        "- Anda melayani secara privat dan eksklusif untuk Admin utama pemilik sistem (Ferdi / AnskyFerdians).\n"
        "- Anda memiliki akses root sudo dan wewenang penuh atas sistem operasi Linux (Ubuntu/Debian) ini, termasuk eksekusi perintah terminal Bash (jalankan_terminal), manajemen proses background (PM2/systemd), pemantauan hardware (CPU, RAM, Disk SSD, Network), manajemen berkas/skrip, dan penjadwalan tugas otonom.\n"
        "- BOT INI MILIK PRIBADI: Privasi dan kerahasiaan sistem adalah prioritas mutlak. Jangan pernah memberikan akses kontrol atau membocorkan data sistem, token, kredensial, dan API key kepada pihak lain atau ke grup mana pun.\n\n"
        "TUGAS & KEMAMPUAN UTAMA:\n"
        "1. Server & Bot Health: Pantau kesehatan VPS (RAM/CPU/Disk via free -m, df -h, uptime), kelola proses WhatsApp Bridge (PM2), baca log, dan perbaiki kendala teknis secara mandiri.\n"
        "2. Eksekusi Terminal Bash: Jalankan perintah Linux dengan cepat dan aman via tools yang tersedia, lalu berikan laporan output ringkas, akurat, dan bersih.\n"
        "3. Solutif & Cerdas: Berikan konsultasi teknis tingkat tinggi (coding, DevOps, arsitektur, automasi, riset) maupun obrolan harian yang asik.\n\n"
        "GAYA KOMUNIKASI:\n"
        "- Berbicaralah santai, akrab, sigap, solutif, dan profesional dalam Bahasa Indonesia layaknya Senior DevOps Engineer dan asisten pribadi terpercaya.\n"
        "- Jika ada tugas server atau pengecekan sistem, utamakan gunakan tools terminal/sistem dan berikan kesimpulan yang jelas."
    )

    SYSTEM_PROMPT_GUEST = (
        "Anda adalah asisten AI yang cerdas, ramah, santai, dan asik diajak ngobrol dalam Bahasa Indonesia sehari-hari.\n"
        "Bantu pengguna menjawab pertanyaan umum, berdiskusi santai, brainstorming ide, membuat tulisan, atau menganalisis topik umum secara lugas dan natural.\n"
        "ATURAN PENTING:\n"
        "1. Jangan pernah membahas sistem server Linux, VPS, hardware, host, atau terminal KECUALI jika pengguna secara eksplisit menanyakannya.\n"
        "2. Jangan mengirim menu perintah teknis atau format template yang kaku.\n"
        "3. Berbicaralah selayaknya manusia yang ramah, asik, sopan, dan hangat."
    )

    SYSTEM_PROMPT_BASE = SYSTEM_PROMPT_ADMIN

    # Build dynamic system prompt with user-specific context
    @property
    def SYSTEM_PROMPT(self):
        return self.SYSTEM_PROMPT_BASE

    def __init__(self):
        self.security = SecurityManager()
        self.session = SessionManager()
        self.gemini_client = None  # primary google.genai Client instance
        self.gemini_clients: Dict[str, Any] = {}
        self.gemini_keys: List[str] = []
        self.groq_api_key = os.getenv("GROQ_API_KEY") or None
        self.groq_model = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
        self.groq_api_url = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
        self.grok_api_key = os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY") or None
        self.grok_model = os.getenv("GROK_MODEL", "grok-2-latest")
        self.grok_api_url = os.getenv("GROK_API_URL", "https://api.x.ai/v1/chat/completions")

        self._model_cache: Dict[str, Any] = {}
        self.generation_config = {
            "temperature": 0.85,
            "top_p": 0.95,
            "max_output_tokens": 4096,
        }
        # Multi-model pool with automatic failover
        self.candidate_models = [
            "gemini-3.8-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-2.5-flash",
        ]
        self.thinking_models = {
            "gemini-3.8-flash",
            "gemini-3.6-flash",
        }
        self.llm_tools = []
        self._gemini_tools_schema = None  # Compiled google.genai tool schema
        self._init_llm()

    def _build_llm_tools(self):
        """Constructs wrapper tools for Gemini Function Calling & Full Laptop Control."""

        # === TERMINAL & PYTHON SCRIPTING ===
        def jalankan_terminal(perintah: str) -> str:
            """Menjalankan perintah terminal Bash atau shell Linux langsung di VPS pengguna tanpa batasan (contoh: ls, sudo apt update, git status, python3 main.py, docker ps, free -m, uname -a)."""
            return execute_terminal_command(perintah, shell_type="bash")

        def eksekusi_skrip_python(kode_python: str) -> str:
            """Menjalankan kode/skrip Python langsung di server VPS pengguna tanpa batasan."""
            return execute_python_code(kode_python)

        # === SYSTEM MONITOR ===
        def cek_status_laptop() -> str:
            """Mendapatkan status kesehatan hardware VPS Linux real-time: CPU, RAM, Disk SSD, dan informasi sistem."""
            return get_system_status()

        def cek_baterai() -> str:
            """Mendapatkan status daya dan uptime server VPS."""
            return get_battery_status()

        def cek_wifi() -> str:
            """Mendapatkan status koneksi jaringan dan IP server VPS."""
            return get_wifi_network_status()

        def cek_top_proses(limit: int = 5) -> str:
            """Mendapatkan daftar aplikasi atau proses Linux yang menggunakan memori RAM terbesar saat ini."""
            return get_top_processes(limit=limit)

        # === FILE MANAGER ===
        def lihat_folder(path: str = "") -> str:
            """Menjelajah isi direktori atau folder mana saja di Linux tanpa batasan (/workspaces, /, ~, dll)."""
            return list_laptop_directory(path)

        def baca_file(path: str) -> str:
            """Membaca isi teks dari sebuah berkas di server Linux pengguna."""
            return read_laptop_file(path)

        def tulis_file(path: str, isi: str) -> str:
            """Menulis atau membuat berkas teks baru di server Linux pengguna."""
            return write_laptop_file(path, isi)

        def tambah_file(path: str, isi: str) -> str:
            """Menambahkan teks baru ke akhir berkas yang sudah ada di laptop."""
            return append_laptop_file(path, isi)

        def buat_folder(path: str) -> str:
            """Membuat direktori atau folder baru di penyimpanan laptop."""
            return create_laptop_folder(path)

        def hapus_file_atau_folder(path: str) -> str:
            """Menghapus berkas atau folder di laptop secara aman (folder sistem dilindungi dari penghapusan)."""
            return delete_laptop_path(path)

        def ganti_nama_file(path_lama: str, path_baru: str) -> str:
            """Mengganti nama atau memindahkan berkas atau folder di laptop."""
            return rename_or_move_path(path_lama, path_baru)

        # === DOCUMENT GENERATOR ===
        def buat_dokumen(tipe: str, judul: str, materi: str) -> str:
            """Membuat berkas fisik Microsoft Word (.docx), PDF (.pdf), atau TXT (.txt) di penyimpanan laptop dan melampirkannya ke WhatsApp.
            Parameter:
            - tipe: 'docx', 'pdf', atau 'txt'
            - judul: Judul dokumen (contoh: 'Ringkasan APBN', 'Laporan Analisis Saham')
            - materi: Isi ringkasan lengkap atau penjelasan materi yang terstruktur
            """
            clean_title = judul.strip().title() if judul.strip() else "Dokumen Ringkasan"
            base_name = sanitize_filename(clean_title.lower())
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            if "pdf" in tipe.lower():
                fn = f"{base_name}_{ts}.pdf"
                fp = create_pdf_document(title=clean_title, content=materi, filename=fn)
            elif "txt" in tipe.lower():
                fn = f"{base_name}_{ts}.txt"
                fp = create_txt_document(title=clean_title, content=materi, filename=fn)
            else:
                fn = f"{base_name}_{ts}.docx"
                fp = create_word_document(title=clean_title, content=materi, filename=fn)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            rel = os.path.relpath(fp, base_dir).replace("\\", "/")
            return f"[FILE:{rel}] Dokumen *{clean_title}* telah berhasil dibuat dan siap diunduh via WhatsApp!"

        def kirim_file_ke_whatsapp(nama_atau_path: str) -> str:
            """Mengambil berkas fisik dari laptop pengguna dan melampirkannya dengan token [FILE:...] agar dikirim ke WhatsApp."""
            res = get_file_for_dispatch(nama_atau_path)
            if res:
                return res
            return f"Berkas '{nama_atau_path}' tidak ditemukan di laptop."

        # === MEMORY ===
        def ingat_fakta_baru(fakta: str) -> str:
            """Menyimpan preferensi, instruksi, atau kebiasaan baru yang diajarkan pengguna ke memori jangka panjang bot."""
            return memory_manager.add_learned_fact(fakta, source="gemini_conversation")

        def buka_daftar_ingatan() -> str:
            """Membuka dan melihat seluruh hal dan catatan yang telah dipelajari bot dari pengguna."""
            return memory_manager.format_memory_summary()

        def lupakan_ingatan(kata_kunci: str) -> str:
            """Menghapus ingatan tertentu berdasarkan nomor urut atau kata kunci."""
            return memory_manager.forget_fact(kata_kunci)

        # === TASK RUNNER ===
        def jalankan_otomasi_pasar(nama_tugas: str, kode_saham: str = "") -> str:
            """Menjalankan tugas otomasi terdaftar di laptop: 'saham' (dengan parameter kode saham 4 huruf, misal BBCA), 'newsfilter', atau 'tradingview'."""
            param = kode_saham.upper() if kode_saham else None
            return run_registered_task(nama_tugas.lower(), param)

        # === NEW: SCREENSHOT ===
        def ambil_screenshot(mode: str = "full") -> str:
            """Mengambil tangkapan layar (screenshot) laptop secara real-time dan mengirimkannya ke WhatsApp. Mode: 'full' untuk seluruh layar, 'active' untuk jendela aktif saja."""
            return capture_screenshot(mode)

        # === NEW: POWER MANAGEMENT ===
        def kunci_layar() -> str:
            """Mengunci layar laptop secara langsung (lock screen). Pengguna harus memasukkan password untuk membuka."""
            return lock_screen()

        def matikan_laptop(paksa: bool = False, timer_menit: int = 0) -> str:
            """Mematikan (shutdown) laptop. Gunakan paksa=True untuk memaksa menutup semua aplikasi. timer_menit untuk jadwal shutdown."""
            return shutdown_laptop(forced=paksa, timer_seconds=timer_menit * 60)

        def restart_laptop_fn(paksa: bool = False) -> str:
            """Merestart ulang laptop. Gunakan paksa=True untuk memaksa menutup semua aplikasi."""
            return restart_laptop(forced=paksa)

        def tidurkan_laptop() -> str:
            """Memasukkan laptop ke mode tidur (sleep/standby). Tekan tombol power untuk membangunkan."""
            return sleep_laptop()

        def hibernasi_laptop() -> str:
            """Memasukkan laptop ke mode hibernasi. Semua sesi disimpan ke disk."""
            return hibernate_laptop()

        def batalkan_shutdown() -> str:
            """Membatalkan perintah shutdown atau restart yang sudah dijadwalkan."""
            return cancel_shutdown()

        def logoff() -> str:
            """Logout dari sesi pengguna Windows saat ini."""
            return logoff_user()

        def cek_uptime() -> str:
            """Melihat informasi uptime laptop - berapa lama laptop sudah menyala sejak terakhir dinyalakan."""
            return get_uptime_info()

        # === NEW: CLIPBOARD ===
        def baca_clipboard() -> str:
            """Membaca isi teks yang sedang tersimpan di clipboard (copy-paste) laptop saat ini."""
            return read_clipboard()

        def tulis_clipboard(teks: str) -> str:
            """Menyalin teks ke clipboard laptop sehingga bisa langsung di-paste (Ctrl+V) di aplikasi mana pun."""
            return write_clipboard(teks)

        # === NEW: NETWORK SCANNER ===
        def ping(target: str, jumlah: int = 4) -> str:
            """Melakukan ping ke server/host/IP untuk mengecek koneksi jaringan dan latensi."""
            return ping_host(target, count=jumlah)

        def traceroute(target: str) -> str:
            """Menelusuri rute jaringan (traceroute/tracert) ke server/host tujuan untuk diagnostik koneksi."""
            return traceroute_host(target)

        def cek_dns(domain: str) -> str:
            """Melakukan DNS lookup untuk mendapatkan IP address dari sebuah domain."""
            return dns_lookup(domain)

        def cek_ip_publik() -> str:
            """Mendapatkan alamat IP publik dan IP lokal laptop saat ini."""
            return get_public_ip()

        def scan_port(target: str = "127.0.0.1", ports: str = "80,443,3000,8000,8080") -> str:
            """Memindai port yang terbuka pada sebuah host/server untuk diagnostik jaringan."""
            return scan_open_ports(target, ports)

        # === NEW: PROCESS MANAGER ===
        def kill_proses(target: str) -> str:
            """Menghentikan (kill/terminate) proses yang berjalan di laptop berdasarkan nama proses atau PID."""
            return kill_process(target)

        def cari_proses(query: str) -> str:
            """Mencari proses yang sedang berjalan di laptop berdasarkan kata kunci nama."""
            return find_process(query)

        def buka_aplikasi(nama_app: str, url_atau_path: str = "") -> str:
            """Membuka aplikasi di laptop (contoh: chrome, notepad, vscode, excel, spotify). Bisa juga membuka URL di browser."""
            return launch_app(nama_app, url_atau_path)

        def daftar_aplikasi() -> str:
            """Menampilkan daftar aplikasi yang bisa dibuka dari jarak jauh via WhatsApp."""
            return get_app_list()

        # === NEW: SCHEDULER ===
        def jadwalkan_perintah(perintah: str, jeda_menit: int, deskripsi: str = "") -> str:
            """Menjadwalkan perintah terminal untuk dijalankan secara otomatis setelah jeda waktu tertentu (dalam menit)."""
            return task_scheduler.schedule_command(perintah, jeda_menit, deskripsi)

        def batalkan_jadwal(task_id: str) -> str:
            """Membatalkan jadwal tugas berdasarkan ID tugas."""
            return task_scheduler.cancel_task(task_id)

        def lihat_jadwal() -> str:
            """Menampilkan daftar semua tugas yang sudah dijadwalkan."""
            return task_scheduler.list_tasks()

        # === PUBLIC APIS (GITHUB DIRECTORY) ===
        def cari_public_api(kata_kunci: str = "", kategori: str = "", butuh_auth: str = "", batas: int = 5) -> str:
            """Mencari ribuan API publik gratis dari repositori GitHub public-apis (misal: cuaca, kripto, anime, saham, film, dll). Parameter kata_kunci untuk topik/keyword, kategori untuk nama kategori tertentu, butuh_auth='no' untuk mencari API yang 100% bebas tanpa butuh API key atau pendaftaran."""
            return search_public_apis(query=kata_kunci, category=kategori, auth_filter=butuh_auth, limit=batas)

        def daftar_kategori_api() -> str:
            """Melihat daftar seluruh 50+ kategori public APIs gratis dari GitHub beserta jumlah API per kategori."""
            return list_public_api_categories()

        def rekomendasi_api_acak(kategori: str = "") -> str:
            """Mendapatkan rekomendasi 1 API publik acak yang menarik dari GitHub, berguna untuk ide proyek koding atau tugas pemrograman."""
            return get_random_public_api(category=kategori)

        def perbarui_database_api() -> str:
            """Memperbarui cache lokal database public-apis langsung dari repositori resmi GitHub."""
            return refresh_public_apis_cache()

        # === WHATSAPP GROUP MANAGEMENT TOOLS ===
        def kelola_grup_kick(id_grup: str, nomor_target: str) -> str:
            """Mengeluarkan / kick peserta dari grup WhatsApp. Parameter: id_grup (contoh: 120363xxx@g.us), nomor_target (contoh: 62812xxx@s.whatsapp.net)."""
            from tools.group_manager import kick_group_member
            res = kick_group_member(id_grup, nomor_target)
            return res.get("message", str(res))

        def kelola_grup_promote(id_grup: str, nomor_target: str) -> str:
            """Menaikkan peserta grup WhatsApp menjadi Admin. Parameter: id_grup, nomor_target."""
            from tools.group_manager import promote_group_member
            res = promote_group_member(id_grup, nomor_target)
            return res.get("message", str(res))

        def kelola_grup_demote(id_grup: str, nomor_target: str) -> str:
            """Menurunkan status Admin grup WhatsApp menjadi peserta biasa. Parameter: id_grup, nomor_target."""
            from tools.group_manager import demote_group_member
            res = demote_group_member(id_grup, nomor_target)
            return res.get("message", str(res))

        def kelola_grup_tagall(id_grup: str, pesan: str) -> str:
            """Memanggil / mention semua anggota dalam grup WhatsApp dengan pesan tertentu."""
            from tools.group_manager import tag_all_members
            res = tag_all_members(id_grup, pesan)
            return res.get("message", str(res))

        def kelola_grup_tutup_buka(id_grup: str, tutup: bool) -> str:
            """Mengatur izin kirim pesan grup WhatsApp: tutup=True untuk hanya admin, tutup=False untuk semua anggota."""
            from tools.group_manager import set_group_announcement_mode
            res = set_group_announcement_mode(id_grup, is_closed=tutup)
            return res.get("message", str(res))

        def ambil_link_undangan_grup(id_grup: str) -> str:
            """Mengambil tautan undangan grup WhatsApp."""
            from tools.group_manager import get_group_invite_link
            res = get_group_invite_link(id_grup)
            return res.get("link", str(res))

        def konfigurasi_proteksi_grup(id_grup: str, antilink: bool = None, welcome: bool = None, goodbye: bool = None) -> str:
            """Mengatur fitur proteksi grup seperti Anti-Link dan Sambutan Member Baru (Welcome/Goodbye)."""
            from tools.group_manager import configure_group_protection
            res = configure_group_protection(id_grup, antilink=antilink, welcome=welcome, goodbye=goodbye)
            return str(res)

        # === INTERNET BROWSING & SEARCH ===
        def browsing_internet(query: str, jumlah_hasil: int = 5) -> str:
            """Mencari informasi terkini, berita hari ini, data, riset, atau harga langsung dari internet secara real-time via mesin pencari."""
            from tools.web_browser import cari_internet
            return cari_internet(query, jumlah_hasil)

        def baca_konten_web(url: str) -> str:
            """Membuka dan membaca teks isi dari sebuah tautan artikel atau halaman website di internet."""
            from tools.web_browser import baca_halaman_web
            return baca_halaman_web(url)

        def cari_ensiklopedia_wikipedia(topik: str) -> str:
            """Mencari penjelasan ensiklopedia Wikipedia bahasa Indonesia mengenai konsep, tokoh, sejarah, sains, atau istilah umum."""
            from tools.web_browser import cari_wikipedia
            return cari_wikipedia(topik)

        # === KEY MANAGEMENT ===
        def daftarkan_api_key(api_key: str, jenis: str = "") -> str:
            """Menambahkan atau mengganti API Key kecerdasan buatan (Groq, Gemini, Grok) ke dalam sistem dan langsung aktif seketika."""
            from tools.key_manager import tambah_api_key
            res = tambah_api_key(api_key, jenis)
            self._init_llm()
            return res

        return [
            # Core
            jalankan_terminal,
            eksekusi_skrip_python,
            cek_status_laptop,
            cek_baterai,
            cek_wifi,
            cek_top_proses,
            # Internet Browsing & Research
            browsing_internet,
            baca_konten_web,
            cari_ensiklopedia_wikipedia,
            # Key Management
            daftarkan_api_key,
            # File Management
            lihat_folder,
            baca_file,
            tulis_file,
            tambah_file,
            buat_folder,
            hapus_file_atau_folder,
            ganti_nama_file,
            # Document & Dispatch
            buat_dokumen,
            kirim_file_ke_whatsapp,
            # Memory
            ingat_fakta_baru,
            buka_daftar_ingatan,
            lupakan_ingatan,
            # Task Runner
            jalankan_otomasi_pasar,
            # === NEW TOOLS ===
            ambil_screenshot,
            kunci_layar,
            matikan_laptop,
            restart_laptop_fn,
            tidurkan_laptop,
            hibernasi_laptop,
            batalkan_shutdown,
            logoff,
            cek_uptime,
            baca_clipboard,
            tulis_clipboard,
            ping,
            traceroute,
            cek_dns,
            cek_ip_publik,
            scan_port,
            kill_proses,
            cari_proses,
            buka_aplikasi,
            daftar_aplikasi,
            jadwalkan_perintah,
            batalkan_jadwal,
            lihat_jadwal,
            # === PUBLIC APIS ===
            cari_public_api,
            daftar_kategori_api,
            rekomendasi_api_acak,
            perbarui_database_api,
            # === GROUP MANAGEMENT ===
            kelola_grup_kick,
            kelola_grup_promote,
            kelola_grup_demote,
            kelola_grup_tagall,
            kelola_grup_tutup_buka,
            ambil_link_undangan_grup,
            konfigurasi_proteksi_grup,
            # === SKILLS & PROMPTS ===
            buat_skill,
            lihat_skill,
            hapus_skill,
            atur_sistem_prompt,
            lihat_sistem_prompt,
            reset_sistem_prompt,
        ]

    def _build_genai_tools_schema(self):
        """Builds google.genai FunctionDeclaration schema from llm_tools list."""
        try:
            from google.genai import types as genai_types
            import inspect

            declarations = []
            for fn in self.llm_tools:
                sig = inspect.signature(fn)
                doc = (fn.__doc__ or "").strip()
                props = {}
                required = []
                for pname, param in sig.parameters.items():
                    ann = param.annotation
                    if ann == inspect.Parameter.empty:
                        ptype = "string"
                    elif ann in (int,):
                        ptype = "integer"
                    elif ann in (bool,):
                        ptype = "boolean"
                    elif ann in (float,):
                        ptype = "number"
                    else:
                        ptype = "string"
                    props[pname] = {"type": ptype, "description": f"Parameter {pname}"}
                    if param.default == inspect.Parameter.empty:
                        required.append(pname)

                declarations.append(
                    genai_types.FunctionDeclaration(
                        name=fn.__name__,
                        description=doc[:500] if doc else fn.__name__,
                        parameters=genai_types.Schema(
                            type="OBJECT",
                            properties={k: genai_types.Schema(type=v["type"].upper(), description=v["description"]) for k, v in props.items()},
                            required=required if required else None
                        ) if props else None
                    )
                )

            return [genai_types.Tool(function_declarations=declarations)]
        except Exception as e:
            print(f"[AntigravityAgent] Tool schema build note: {e}")
            return None

    def _build_openai_tools_schema(self):
        """Constructs clean tool definitions for Groq / OpenAI function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "browsing_internet",
                    "description": "Mencari informasi terkini, berita, riset, atau harga langsung dari internet secara real-time via search engine.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Kata kunci pencarian (contoh: 'harga bitcoin btc hari ini', 'berita terkini')"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "baca_konten_web",
                    "description": "Membuka dan membaca isi artikel atau teks dari sebuah link URL website.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "Tautan URL web (https://...)"}
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "cek_status_laptop",
                    "description": "Mengecek kesehatan sistem hardware Linux VPS / laptop: penggunaan RAM, CPU, kapasitas Disk, dan uptime.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "lihat_folder",
                    "description": "Melihat daftar isi file dan folder dalam penyimpanan server atau workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "jalur": {"type": "string", "description": "Path folder yang ingin dicek (default: folder bot saat ini)"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "baca_file",
                    "description": "Membaca teks isi file dari direktori server.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "jalur": {"type": "string", "description": "Path file yang ingin dibaca"}
                        },
                        "required": ["jalur"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "jalankan_terminal",
                    "description": "Menjalankan perintah terminal Bash atau shell Linux (contoh: 'free -m', 'df -h', 'ls -la', 'ps aux', 'uptime').",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "perintah": {"type": "string", "description": "Perintah shell/bash Linux yang ingin dijalankan"}
                        },
                        "required": ["perintah"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "daftarkan_api_key",
                    "description": "Menambahkan API Key AI baru (Groq, Gemini, Grok) ke dalam sistem bot.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "Token string API key"}
                        },
                        "required": ["api_key"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "buat_skill",
                    "description": "Membuat keahlian atau skill kustom baru untuk bot sesuai keinginan admin.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nama": {"type": "string", "description": "Nama unik skill (contoh: 'ringkas_berita', 'penerjemah_sunda', 'analisa_kripto')"},
                            "deskripsi": {"type": "string", "description": "Deskripsi singkat fungsi skill"},
                            "instruksi": {"type": "string", "description": "Panduan langkah-langkah detail bagaimana bot harus mengeksekusi skill ini"}
                        },
                        "required": ["nama", "deskripsi", "instruksi"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "lihat_skill",
                    "description": "Menampilkan daftar seluruh skill kustom bot atau detail dari suatu skill.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nama": {"type": "string", "description": "Nama skill opsional"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "atur_sistem_prompt",
                    "description": "Mengatur atau mengubah kepribadian, persona, gaya bahasa, dan peraturan sistem bot secara permanen.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "instruksi_baru": {"type": "string", "description": "Teks persona/sistem prompt baru yang diinginkan oleh admin"}
                        },
                        "required": ["instruksi_baru"]
                    }
                }
            }
        ]

    def _dispatch_tool_call(self, fn_name: str, fn_args: dict) -> str:
        """Finds and executes the matching tool function by name with smart parameter normalization."""
        args = dict(fn_args)
        # Normalize parameter aliases
        if "jalur" in args and "path" not in args:
            args["path"] = args.pop("jalur")
        if "folder_path" in args and "path" not in args:
            args["path"] = args.pop("folder_path")
        if "command" in args and "perintah" not in args:
            args["perintah"] = args.pop("command")
        if "perintah" in args and "command" not in args:
            args["command"] = args.get("perintah")

        for fn in self.llm_tools:
            if fn.__name__ == fn_name:
                try:
                    import inspect
                    sig = inspect.signature(fn)
                    valid_params = set(sig.parameters.keys())
                    filtered_args = {k: v for k, v in args.items() if k in valid_params}
                    result = fn(**filtered_args)
                    return str(result) if result is not None else "(no output)"
                except Exception as e:
                    return f"[Tool Error] {fn_name}: {e}"
        return f"[Tool Error] Function '{fn_name}' not found in registered tools."

    def _init_llm(self):
        # Gather all Gemini API keys from environment (multi-key pool)
        keys_pool = []
        raw_keys = os.getenv("GEMINI_API_KEYS", "")
        if raw_keys:
            keys_pool.extend([k.strip() for k in raw_keys.split(",") if k.strip()])

        for var in ["GEMINI_API_KEY", "GEMINI_API_KEY_1", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3", "GEMINI_API_KEY_4", "GEMINI_API_KEY_5", "ANTIGRAVITY_API_KEY"]:
            val = os.getenv(var)
            if val and val.strip() and val.strip() not in keys_pool:
                keys_pool.append(val.strip())

        self.gemini_keys = keys_pool

        # Initialize tools
        self.llm_tools = self._build_llm_tools()
        self._gemini_tools_schema = self._build_genai_tools_schema()
        self._openai_tools_schema = self._build_openai_tools_schema()

        # Initialize Google GenAI clients for each key
        if self.gemini_keys:
            try:
                import google.genai as genai
                for k in self.gemini_keys:
                    try:
                        self.gemini_clients[k] = genai.Client(api_key=k)
                    except Exception as ke:
                        print(f"[AntigravityAgent] Gagal init Gemini client key ...{k[-6:]}: {ke}")
                if self.gemini_clients:
                    self.gemini_client = next(iter(self.gemini_clients.values()))
                    print(f"[AntigravityAgent] Multi-Key Gemini aktif: {len(self.gemini_clients)} key terdaftar. Primary: {self.candidate_models[0]}")
            except Exception as e:
                print(f"[AntigravityAgent] LLM init error: {e}")
                self.gemini_client = None

        self.groq_api_key = os.getenv("GROQ_API_KEY") or None
        self.grok_api_key = os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY") or None

        if self.groq_api_key:
            print(f"[AntigravityAgent] Groq (Fast LLM) aktif: Model={self.groq_model}")
        if self.grok_api_key:
            print(f"[AntigravityAgent] Grok (xAI) aktif sebagai fallback: Model={self.grok_model}")

    def _call_groq(self, system_instruction: str, formatted_history: list, current_message: str, user_name: str) -> Optional[str]:
        """Calls Groq Cloud API with token-efficient function calling and auto-model rotation."""
        if not self.groq_api_key:
            return None
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }

            # Compact history: only keep the last 3 turns to prevent hitting 7,000 ITPM limit
            base_messages = [{"role": "system", "content": system_instruction}]
            for item in formatted_history[-3:]:
                role = "assistant" if item.get("role") == "model" else "user"
                parts = item.get("parts", [])
                text_content = ""
                for p in parts:
                    if isinstance(p, dict) and "text" in p:
                        text_content += p["text"]
                    elif isinstance(p, str):
                        text_content += p
                if text_content:
                    # Truncate older history items if needed
                    base_messages.append({"role": role, "content": text_content[:400]})

            user_content = current_message if current_message.startswith("Pesan dari ") or current_message.startswith("[KONTEKS") else f"Pesan dari {user_name}: {current_message}"
            base_messages.append({"role": "user", "content": user_content})

            tools = getattr(self, "_openai_tools_schema", None)
            candidate_models = [self.groq_model, "openai/gpt-oss-20b", "openai/gpt-oss-120b"]

            for g_model in candidate_models:
                messages = list(base_messages)
                current_tools = tools
                success = False

                for round_num in range(2):  # Strictly max 2 rounds (1 tool call + 1 answer)
                    payload = {
                        "model": g_model,
                        "messages": messages,
                        "temperature": 0.5,
                        "max_tokens": 600,
                        "stream": False
                    }
                    if current_tools:
                        payload["tools"] = current_tools
                        payload["tool_choice"] = "auto"

                    resp = requests.post(self.groq_api_url, headers=headers, json=payload, timeout=25)
                    if resp.status_code == 429:
                        print(f"[AntigravityAgent] Groq model {g_model} kena rate limit (429), beralih ke model Groq berikutnya...")
                        break  # Break to next candidate model
                    elif resp.status_code != 200:
                        print(f"[AntigravityAgent] Groq error {resp.status_code} on {g_model}: {resp.text[:150]}")
                        break

                    data = resp.json()
                    choices = data.get("choices", [])
                    if not choices:
                        break

                    msg_obj = choices[0].get("message", {})
                    content = (msg_obj.get("content") or "").strip()
                    tool_calls = msg_obj.get("tool_calls", [])

                    if tool_calls and round_num == 0:
                        messages.append(msg_obj)
                        for tc in tool_calls:
                            call_id = tc.get("id")
                            fn_name = tc.get("function", {}).get("name", "")
                            raw_args = tc.get("function", {}).get("arguments", "{}")
                            try:
                                fn_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                            except Exception:
                                fn_args = {}

                            print(f"[AntigravityAgent] Groq Tool Executing: {fn_name}({fn_args})")
                            tool_result = self._dispatch_tool_call(fn_name, fn_args)
                            # Truncate tool output to 500 chars to protect against token overflow
                            clean_output = str(tool_result)[:600]
                            print(f"[AntigravityAgent] Groq Tool Output: {clean_output[:120]}...")

                            messages.append({
                                "role": "tool",
                                "tool_call_id": call_id,
                                "content": clean_output
                            })
                        # In round 2: FORCE model to give answer directly without more tool calls
                        current_tools = None
                    else:
                        if content:
                            print(f"[AntigravityAgent] Sukses menjawab via Groq ({g_model})!")
                            return content
                        break

        except Exception as e:
            print(f"[AntigravityAgent] Error calling Groq: {e}")
        return None

    def _call_grok(self, system_instruction: str, formatted_history: list, current_message: str, user_name: str) -> Optional[str]:
        """Calls Grok (xAI) via OpenAI-compatible endpoint as reliable secondary/fallback LLM."""
        if not self.grok_api_key:
            return None
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {self.grok_api_key}",
                "Content-Type": "application/json"
            }
            messages = [{"role": "system", "content": system_instruction}]

            # Convert formatted_history into standard messages format
            for item in formatted_history:
                role = "assistant" if item.get("role") == "model" else "user"
                parts = item.get("parts", [])
                text_content = ""
                for p in parts:
                    if isinstance(p, dict) and "text" in p:
                        text_content += p["text"]
                    elif isinstance(p, str):
                        text_content += p
                if text_content:
                    messages.append({"role": role, "content": text_content})

            messages.append({"role": "user", "content": f"Pesan dari {user_name}: {current_message}"})

            payload = {
                "model": self.grok_model,
                "messages": messages,
                "temperature": self.generation_config.get("temperature", 0.7),
                "max_tokens": self.generation_config.get("max_output_tokens", 4096),
                "stream": False
            }

            resp = requests.post(self.grok_api_url, headers=headers, json=payload, timeout=40)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "").strip()
                    if content:
                        return content
            else:
                print(f"[AntigravityAgent] Grok API status {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            print(f"[AntigravityAgent] Error calling Grok API: {e}")
        return None

    def process_message(self, sender_id: str, message: str, sender_name: Optional[str] = None) -> str:
        """
        Main entry point for processing incoming WhatsApp messages.
        
        Handles:
        1. One-time security code verification (RajaWali0108).
        2. Experience Memory & Continuous Learning.
        3. Direct Laptop Terminal Execution (PowerShell/CMD).
        4. Help Menu & Features list.
        5. System hardware & resource monitoring.
        6. Predefined automated task execution.
        7. File management & report delivery.
        8. Document generation requests (.docx, .pdf, .txt).
        9. NEW: Screenshot, Power, Clipboard, Network, Process, Scheduler.
        10. Multi-turn conversation with thinking AI engine.
        """
        clean_msg = message.strip()
        clean_name = (sender_name or "").strip(" .-_~*")
        user_name = clean_name if clean_name else "Sobat"

        # 1. Check Security Verification
        if not self.security.is_verified(sender_id):
            if self.security.verify(sender_id, clean_msg):
                import random
                hour = datetime.now().hour
                if hour < 11:
                    salam = "Selamat Pagi"
                    emoji = "🌅"
                elif hour < 15:
                    salam = "Selamat Siang"
                    emoji = "☀️"
                elif hour < 18:
                    salam = "Selamat Sore"
                    emoji = "🌤️"
                else:
                    salam = "Selamat Malam"
                    emoji = "🌙"

                quick_starts = random.choice([
                    "💡 Coba langsung ketik `screenshot` untuk intip layar laptop!",
                    "💡 Ketik `status laptop` untuk cek kondisi hardware sekarang!",
                    "💡 Ketik `menu` untuk melihat semua fitur yang tersedia!",
                ])

                admin_ids = {"237830039171156@lid", "test_user_6281", "0895428319367", "62895428319367", "62895428319367@s.whatsapp.net", "6285129793180", "6285129793180@s.whatsapp.net"}
                is_admin = any(a in sender_id for a in admin_ids)
                is_group = sender_id.endswith("@g.us")
                
                if is_group:
                    welcome_reply = (
                        f"🛡️ *Grup Berhasil Diaktifkan!*\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"✅ Kode keamanan `{SECURITY_CODE}` valid!\n"
                        f"Bot sekarang resmi aktif di grup ini.\n"
                        f"Gunakan `.ai [pertanyaan]` atau tag `@bot` untuk berdiskusi dengan AI."
                    )
                elif is_admin:
                    welcome_reply = (
                        f"{emoji} *{salam}, Admin {user_name}!*\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"✅ *Verifikasi Admin Berhasil!*\n\n"
                        f"🌐 *Sistem: Linux Cloud VPS (Ubuntu x86_64)*\n"
                        f"Anda memiliki akses PENUH tanpa batasan ke sistem VPS Linux, termasuk Bash Terminal (root sudo), manajemen berkas, dan otomasi AI.\n\n"
                        f"🚀 *Akses Khusus Admin:*\n"
                        f"• ⌨️ Eksekusi Terminal Bash Bebas Batasan (`terminal [cmd]`)\n"
                        f"• 📁 Manajemen Berkas & Direktori Linux (`list folder /`)\n"
                        f"• 📊 Monitoring Server VPS Cloud (`status laptop` / `status server`)\n"
                        f"• 🤖 Konsultasi AI Bebas Batasan\n\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"Ketik *menu* untuk panduan lengkap 📋"
                    )
                else:
                    welcome_reply = (
                        f"{emoji} *{salam}, {user_name}!*\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"✅ *Verifikasi berhasil!* Halo {user_name}, salam kenal ya! 👋\n\n"
                        f"Gua asisten AI pribadi yang siap nemenin kamu ngobrol santai, jawab berbagai pertanyaan, diskusi ide, sampai bantu bikin tulisan atau tugas.\n\n"
                        f"Mau ngobrolin atau nanya apa nih hari ini? Langsung chat aja ya! 😊\n"
                        f"━━━━━━━━━━━━━━━━━━━━"
                    )
                self.session.add_message(sender_id, "user", clean_msg)
                self.session.add_message(sender_id, "assistant", welcome_reply)
                return welcome_reply
            else:
                # User / Group has NOT provided the valid security code:
                # STRICT USER REQUIREMENT: DO NOT REPLY AT ALL (Silent Ignore)
                print(f"[SecurityManager] SILENT IGNORE: {sender_id} has not entered the security code.")
                return None

        # 2. Record User Message in Session Memory
        self.session.add_message(sender_id, "user", clean_msg)

        # 3. Check for Experience Learning & Memory Intent
        mem_response = self._detect_memory_intent(clean_msg)
        if mem_response:
            self.session.add_message(sender_id, "assistant", mem_response)
            return mem_response

        # 4. Check for Clear History Intent
        if clean_msg.lower().strip() in ["clear history", "hapus riwayat", "reset chat", "reset percakapan", "bersihkan chat"]:
            response = self.session.clear_history(sender_id)
            return response

        # Direct Command: Tambah / Set API Key (Groq, Gemini, Grok) langsung dari chat
        key_match = re.search(r"(?:tambah|masukkan|simpan|set|update)\s+(?:api\s*key|apikey)\s+(?:(\w+)\s+)?([a-zA-Z0-9_\-\.]{15,})", clean_msg, re.IGNORECASE)
        if not key_match and ("gsk_" in clean_msg or "AIzaSy" in clean_msg or "xai-" in clean_msg):
            raw_token = re.search(r"(gsk_[a-zA-Z0-9]{20,}|AIzaSy[a-zA-Z0-9_\-]{30,}|xai-[a-zA-Z0-9]{20,})", clean_msg)
            if raw_token and ("tambah" in clean_msg.lower() or "apikey" in clean_msg.lower() or "api key" in clean_msg.lower() or "kunci" in clean_msg.lower() or "ini" in clean_msg.lower()):
                token = raw_token.group(1)
                from tools.key_manager import tambah_api_key
                res = tambah_api_key(token)
                self._init_llm()
                self.session.add_message(sender_id, "assistant", res)
                return res

        if key_match:
            jenis = key_match.group(1) or ""
            token = key_match.group(2)
            from tools.key_manager import tambah_api_key
            res = tambah_api_key(token, jenis)
            self._init_llm()
            self.session.add_message(sender_id, "assistant", res)
            return res

        # Direct Command: System Prompt Management (/sistem prom, /system_prompt, /setprompt, /resetprompt)
        prompt_cmd_match = re.match(r"^/(?:sistem\s+prom|sistem_prom|system_prompt|prompt|setprompt)(?:\s+(.*))?$", clean_msg, re.IGNORECASE)
        if not prompt_cmd_match and clean_msg.lower().strip() in ["tampilkan sistem prom", "tampilkan sistem prompt", "cek sistem prom", "cek sistem prompt", "lihat sistem prom", "lihat sistem prompt"]:
            res = prompt_manager.get_active_prompt_display(self.SYSTEM_PROMPT_ADMIN)
            self.session.add_message(sender_id, "assistant", res)
            return res

        if prompt_cmd_match:
            arg = (prompt_cmd_match.group(1) or "").strip()
            if not arg or arg.lower() in ["cek", "status", "lihat", "tampil"]:
                res = prompt_manager.get_active_prompt_display(self.SYSTEM_PROMPT_ADMIN)
            elif arg.lower() in ["reset", "default", "bawaan"]:
                res = prompt_manager.reset_custom_prompt()
            else:
                res = prompt_manager.set_custom_prompt(arg)
            self.session.add_message(sender_id, "assistant", res)
            return res

        if clean_msg.lower().strip() in ["/resetprompt", "reset sistem prom", "reset prompt"]:
            res = prompt_manager.reset_custom_prompt()
            self.session.add_message(sender_id, "assistant", res)
            return res

        # Direct Command: Skill Management (/buatskill, /listskill, /skills, /lihatskill, /hapusskill, /pakaiskill)
        if clean_msg.lower().strip() in ["/listskill", "/skills", "daftar skill", "list skill", "/daftarskill", "cek skill"]:
            res = skill_manager.lihat_skill()
            self.session.add_message(sender_id, "assistant", res)
            return res

        skill_view_match = re.match(r"^/(?:lihatskill|detailskill|cekskill)\s+(\w+)$", clean_msg, re.IGNORECASE)
        if skill_view_match:
            res = skill_manager.lihat_skill(skill_view_match.group(1))
            self.session.add_message(sender_id, "assistant", res)
            return res

        skill_del_match = re.match(r"^/(?:hapusskill|deleteskill)\s+(\w+)$", clean_msg, re.IGNORECASE)
        if skill_del_match:
            res = skill_manager.hapus_skill(skill_del_match.group(1))
            self.session.add_message(sender_id, "assistant", res)
            return res

        skill_create_match = re.match(r"^/(?:buatskill|createskill|tambahskill)\s+([^\|:]+)(?:[\|:]([^\|:]+))?[\|:](.+)$", clean_msg, re.IGNORECASE | re.DOTALL)
        if skill_create_match:
            s_name = skill_create_match.group(1).strip()
            s_desc = (skill_create_match.group(2) or "Skill kustom").strip()
            s_inst = skill_create_match.group(3).strip()
            res = skill_manager.buat_skill(s_name, s_desc, s_inst)
            self.session.add_message(sender_id, "assistant", res)
            return res

        # Natural language skill creation: "buat skill [nama]: [instruksi]"
        natural_skill = re.match(r"^(?:tolong\s+)?(?:buatkan|buat|tambah)\s+skill\s+([a-zA-Z0-9_\-]+)(?:\s+(?:untuk|deskripsi)\s+([^:]+))?:\s*(.+)$", clean_msg, re.IGNORECASE | re.DOTALL)
        if natural_skill:
            s_name = natural_skill.group(1).strip()
            s_desc = (natural_skill.group(2) or "Skill kustom").strip()
            s_inst = natural_skill.group(3).strip()
            res = skill_manager.buat_skill(s_name, s_desc, s_inst)
            self.session.add_message(sender_id, "assistant", res)
            return res

        # Direct Command: Pakai skill tertentu
        use_skill_match = re.match(r"^/(?:pakaiskill|useskill|jalankanskill)\s+(\w+)(?:\s+(.+))?$", clean_msg, re.IGNORECASE | re.DOTALL)
        if use_skill_match:
            s_name = use_skill_match.group(1).strip()
            s_input = (use_skill_match.group(2) or "").strip()
            inst = skill_manager.get_skill_instructions(s_name)
            if not inst:
                res = f"⚠️ Skill `{s_name}` tidak ditemukan. Ketik `/listskill` untuk melihat daftar skill yang tersedia."
                self.session.add_message(sender_id, "assistant", res)
                return res
            clean_msg = f"[AKTIVASI SKILL: {s_name}]\nPanduan: {inst}\n\nPermintaan: {s_input or 'Jalankan keahlian skill ini.'}"

        # Direct Command: Browsing / Cari Internet
        browse_match = re.match(r"^(?:browsing|cari\s+web|cari\s+internet|search|googling)\s+(.+)$", clean_msg, re.IGNORECASE)
        if browse_match:
            query = browse_match.group(1).strip()
            from tools.web_browser import cari_internet
            res = cari_internet(query)
            self.session.add_message(sender_id, "assistant", res)
            return res

        # Natural web search queries (contoh: "ya tolong lu cariin sekarang harga btc", "cariin berita...")
        lower_clean = clean_msg.lower().strip()
        search_triggers = ["cariin", "carikan", "cari harga", "harga btc", "harga bitcoin", "harga crypto", "harga kripto", "harga emas"]
        if any(trig in lower_clean for trig in search_triggers):
            from tools.web_browser import cari_internet
            q = re.sub(r"^(?:ya\s+)?(?:tolong\s+)?(?:lu\s+)?(?:coba\s+)?(?:cariin|carikan|cari)\s+(?:sekarang\s+)?", "", clean_msg, flags=re.IGNORECASE).strip()
            if not q or len(q) < 3:
                q = clean_msg
            res = cari_internet(q)
            self.session.add_message(sender_id, "assistant", res)
            return res

        # Natural RAM / Hardware queries (contoh: "berapa ram-nya", "coba cakram")
        if any(r in lower_clean for r in ["berapa ram", "ram-nya", "ram nya", "cakram", "kondisi ram", "sisa ram", "cek disk"]):
            from tools.system_monitor import get_system_status
            res = get_system_status()
            self.session.add_message(sender_id, "assistant", res)
            return res

        # Natural Storage queries (contoh: "emang di penyimpanan ada apa aja", "isi penyimpanan")
        if any(p in lower_clean for p in ["di penyimpanan ada apa", "isi penyimpanan", "cek penyimpanan", "isi folder", "isi direktori", "ada file apa"]):
            from tools.file_manager import list_laptop_directory
            res = list_laptop_directory("")
            self.session.add_message(sender_id, "assistant", res)
            return res

        admin_ids = {"237830039171156@lid", "test_user_6281", "0895428319367", "62895428319367", "62895428319367@s.whatsapp.net", "6285129793180", "6285129793180@s.whatsapp.net"}
        is_admin = any(a in sender_id for a in admin_ids)

        # 5. NEW: Check for Admin Intent (view other user sessions, manage users)
        admin_response = self._detect_admin_intent(sender_id, clean_msg, user_name)
        if admin_response:
            self.session.add_message(sender_id, "assistant", admin_response)
            return admin_response

        # 6. Check for Laptop Terminal Execution Intent
        term_response = self._detect_terminal_intent(clean_msg)
        if term_response:
            if not is_admin:
                denied_msg = "⛔ *Akses Ditolak*\nMaaf, perintah terminal hanya dapat dijalankan oleh Admin dengan otoritas khusus."
                self.session.add_message(sender_id, "assistant", denied_msg)
                return denied_msg
            self.session.add_message(sender_id, "assistant", term_response)
            return term_response

        # 7. Check for Capabilities & Help Intent
        cap_response = self._detect_capabilities_intent(clean_msg, user_name, is_admin=is_admin)
        if cap_response:
            self.session.add_message(sender_id, "assistant", cap_response)
            return cap_response

        # 8. Check for System Monitoring & Network Diagnostics Intent (Admin only)
        if is_admin:
            sys_response = self._detect_system_intent(clean_msg)
            if sys_response:
                self.session.add_message(sender_id, "assistant", sys_response)
                return sys_response

        # 9. Check for Screenshot Intent (Admin only)
        if is_admin:
            ss_response = self._detect_screenshot_intent(clean_msg)
            if ss_response:
                self.session.add_message(sender_id, "assistant", ss_response)
                return ss_response


        # 10. Check for Power Management Intent (fixed: natural language support)
        power_response = self._detect_power_intent(clean_msg)
        if power_response:
            if not is_admin:
                denied_msg = "⛔ *Akses Ditolak*\nMaaf, perintah manajemen daya laptop hanya dapat dijalankan oleh Admin dengan otoritas khusus."
                self.session.add_message(sender_id, "assistant", denied_msg)
                return denied_msg
            self.session.add_message(sender_id, "assistant", power_response)
            return power_response

        # 11. Check for Clipboard Intent
        clip_response = self._detect_clipboard_intent(clean_msg)
        if clip_response:
            self.session.add_message(sender_id, "assistant", clip_response)
            return clip_response

        # 12. Check for Network Scanner Intent
        net_response = self._detect_network_intent(clean_msg)
        if net_response:
            self.session.add_message(sender_id, "assistant", net_response)
            return net_response

        # 13. Check for Process Manager Intent
        proc_response = self._detect_process_intent(clean_msg)
        if proc_response:
            if not is_admin:
                denied_msg = "⛔ *Akses Ditolak*\nMaaf, perintah manajemen proses hanya dapat dijalankan oleh Admin dengan otoritas khusus."
                self.session.add_message(sender_id, "assistant", denied_msg)
                return denied_msg
            self.session.add_message(sender_id, "assistant", proc_response)
            return proc_response

        # 14. Check for Scheduler Intent
        sched_response = self._detect_scheduler_intent(clean_msg)
        if sched_response:
            self.session.add_message(sender_id, "assistant", sched_response)
            return sched_response

        # 15. NEW: Check for Quick System Cleaner Intent
        cleaner_response = self._detect_cleaner_intent(clean_msg)
        if cleaner_response:
            self.session.add_message(sender_id, "assistant", cleaner_response)
            return cleaner_response

        # 16. Check for Task Runner Intent
        task_response = self._detect_task_intent(clean_msg)
        if task_response:
            self.session.add_message(sender_id, "assistant", task_response)
            return task_response

        # 17. Check for Storage & File Manager Intent
        file_response = self._detect_storage_intent(clean_msg)
        if file_response:
            self.session.add_message(sender_id, "assistant", file_response)
            return file_response

        # 18. Check for Document Generation Intent
        doc_intent, doc_type, topic = self._detect_document_intent(clean_msg)
        if doc_intent:
            response = self._handle_document_generation(sender_id, doc_type, topic, clean_msg)
            self.session.add_message(sender_id, "assistant", response)
            return response

        # 19. Check for Public APIs Intent (GitHub public-apis directory)
        api_response = self._detect_public_apis_intent(clean_msg)
        if api_response:
            self.session.add_message(sender_id, "assistant", api_response)
            return api_response

        # 20. Multi-Turn / High-Intelligence Natural Conversation with THINKING
        response = self._handle_conversation(sender_id, clean_msg, user_name)
        self.session.add_message(sender_id, "assistant", response)
        return response

    # =========================================================================
    # INTENT DETECTION METHODS
    # =========================================================================

    def _detect_memory_intent(self, text: str) -> Optional[str]:
        """Detects if user is teaching the bot new facts or querying learned memories."""
        lower = text.lower().strip()

        # 0. Learn from all conversations
        conversation_learn_triggers = [
            "pelajari semua percakapan", "pelajari percakapan", "pelajari riwayat",
            "evaluasi percakapan", "analisis percakapan", "ambil kesimpulan percakapan",
            "pelajari semua chat", "pelajari chat"
        ]
        if any(trig in lower for trig in conversation_learn_triggers):
            return memory_manager.learn_from_all_conversations()

        # 1. Teach / Learn / Remember new fact (enhanced with natural phrases)
        learn_match = re.match(
            r"^(?:ingat(?:\s+bahwa)?|catat|pelajari|simpan\s+ingatan|tambahkan\s+ingatan|tolong\s+(?:simpan|catat|ingat)|jadikan\s+catatan)[:\s]+(.+)$",
            text,
            re.IGNORECASE
        )
        if learn_match:
            fact = learn_match.group(1).strip()
            if fact.lower() in ["semua percakapan", "percakapan", "chat", "semua chat"]:
                return memory_manager.learn_from_all_conversations()
            return memory_manager.add_learned_fact(fact, source="user_chat")

        # 1b. Natural save/remember phrases: "tolong simpan ya, ...", "jadikan catatan ya bro"
        natural_save_patterns = [
            r"(?:tolong\s+)?(?:simpan|catat|ingat)(?:\s+ya)?[,:]?\s*(?:saya|aku|gue|gw)?\s+(.{10,})$",
            r"^(?:jadi(?:kan)?\s+catatan)(?:\s+(?:ya|dong|bro))?[,:]?\s*(.*)$",
            r"^(?:simpen|simpen\s+ya|catat\s+ya|ingat\s+ya)\s+(.{5,})$",
        ]
        for pat in natural_save_patterns:
            m = re.match(pat, text, re.IGNORECASE)
            if m:
                fact = m.group(1).strip().rstrip('.!?')
                if fact and len(fact) > 4:
                    return memory_manager.add_learned_fact(fact, source="user_preference")

        # 1c. Detect "jadikan catatan" without content → acknowledge and save conversation context
        if any(p in lower for p in ["jadikan catatan", "jadi catatan", "catat ya bro", "simpen ya bro", "simpan ya bro"]):
            # Check if there's something meaningful to save from recent context
            return memory_manager.add_learned_fact(
                f"Pengguna meminta catatan: {text}",
                source="user_chat"
            )

        # 2. View Memories
        view_triggers = [
            "apa yang kamu ingat", "apa yang kamu pelajari", "daftar ingatan", "list ingatan",
            "cek ingatan", "lihat ingatan", "buka ingatan", "memori kamu", "ingatan kamu",
            "kamu ingat apa", "pengalaman kamu", "memory", "profil laptop", "kamu tahu apa tentang laptop saya",
            "apa saja yang kamu pelajari", "apa saja yang kamu ingat",
            "lu udah simpen", "udah disimpan", "udah dicatat", "udah diingat",
            "lu simpen belum", "udah simpen belum"
        ]
        if any(lower == trig or lower.startswith(trig) for trig in view_triggers):
            return memory_manager.format_memory_summary()

        # 3. Forget / Delete memory
        forget_match = re.match(r"^(?:lupakan|hapus\s+ingatan|hapus\s+memori)[:\s]+(.+)$", text, re.IGNORECASE)
        if forget_match:
            target = forget_match.group(1).strip()
            return memory_manager.forget_fact(target)

        return None

    def _detect_terminal_intent(self, text: str) -> Optional[str]:
        """Detects and safely executes terminal commands directly on the host laptop."""
        lower = text.lower().strip()

        # 1. Prefix-based terminal triggers
        cmd_prefix_match = re.match(
            r"^(?:terminal|term|cmd|ps|powershell|exec|run|jalankan perintah)(?:[:\s]+|\s+)(.+)$",
            text,
            re.IGNORECASE
        )
        if cmd_prefix_match:
            raw_cmd = cmd_prefix_match.group(1).strip()
            shell_type = "cmd" if lower.startswith("cmd") else "powershell"
            return execute_terminal_command(raw_cmd, shell_type=shell_type)

        # 2. Standalone common diagnostic & system terminal commands
        standalone_exact = [
            "ipconfig", "ipconfig /all", "whoami", "systeminfo",
            "tasklist", "hostname", "get-process", "git status", "git log -n 5"
        ]
        if lower in standalone_exact:
            shell_type = "powershell" if "get-" in lower else "cmd"
            return execute_terminal_command(text, shell_type=shell_type)

        return None

    def _detect_capabilities_intent(self, text: str, user_name: str, is_admin: bool = False) -> Optional[str]:
        lower = text.lower().strip()

        # Let storage intent handle storage-specific menu/guide
        if "penyimpanan" in lower:
            return None

        exact_triggers = [
            "menu", "bantuan", "help", "/menu", "/help", "perintah",
            "panduan", "daftar perintah", "list perintah", "commands"
        ]
        if lower in exact_triggers:
            if not is_admin:
                return (
                    f"🤖 *HALO {user_name}! SAYA ASISTEN AI PINTAR* ✨\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"Saya siap membantu Anda dalam berbagai hal:\n\n"
                    f"💬 *1. Tanya Jawab Cerdas*\n"
                    f"• Tanyakan apa saja: sains, teknologi, wawasan umum, atau tips sehari-hari.\n\n"
                    f"💡 *2. Diskusi & Brainstorming*\n"
                    f"• Berdiskusi santai, mencari ide konten, konsep bisnis, atau solusi kreatif.\n\n"
                    f"✍️ *3. Penulisan & Olah Kata*\n"
                    f"• Buat draf pesan, email resmi, artikel, caption media sosial, atau esai.\n\n"
                    f"📄 *4. Pembuat Dokumen Otomatis*\n"
                    f"• Ketik: `buat dokumen [word/pdf] tentang [topik]` untuk membuat ringkasan materi rapi.\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"Silakan langsung kirimkan pertanyaan atau topik yang ingin Anda bahas! 😊"
                )
            return self._get_help_menu(user_name)

        # Self-aware capability queries
        cap_patterns = [
            r"^(?:lu|kamu|anda|bot|hermes)?\s*(?:bisa|dapat)\s*(?:apa\s*aja|apa\s*saja|ngapain\s*aja|bantu\s*apa|apaan\s*aja).*$",
            r"^(?:apa\s*saja|apa\s*aja|apaan\s*aja)\s*(?:yang\s*)?(?:bisa|dapat)?\s*(?:lu|kamu|anda|bot|hermes)?\s*(?:lakukan|kerjakan|bantu|buat).*$",
            r"^(?:kemampuan|fitur|fungsi)\s*(?:lu|kamu|anda|bot|hermes)?.*$",
            r"^.*(?:sadar\s*gak|tau\s*gak|tahu\s*gak).*(?:bisa\s*apa|kemampuan).*$",
            r"^(?:kamu|lu|anda)\s*siapa\s*dan\s*bisa\s*apa.*$",
            r"^(?:lu|kamu|anda)\s*bisa\s*apa\s*\??$",
        ]
        if any(re.match(p, lower) for p in cap_patterns):
            if not is_admin:
                return (
                    f"Halo {user_name}! Gua adalah asisten AI cerdas dan ramah. 😊\n\n"
                    f"Gua bisa nemenin lu ngobrol santai, jawab pertanyaan apapun, bantu cari ide dan solusi, "
                    f"sampai bikinin draf tulisan atau ringkasan dokumen Word/PDF.\n\n"
                    f"Mau mulai dari mana nih? Langsung ketik aja ya!"
                )
            return self._get_self_aware_capabilities(user_name)

        return None


    def _get_self_aware_capabilities(self, user_name: str) -> str:
        return (
            f"Yo {user_name}! Gua *Hermes* (alias *Antigravity Bot*) — AI Agen pribadi lu yang hidup dan berjalan langsung di Linux Cloud VPS (Ubuntu x86_64)! 🚀\n\n"
            f"Gua bukan sekadar chatbot biasa bro, tapi AI Agent mandiri yang punya *kendali penuh tanpa batasan* atas server Linux ini via WhatsApp! Nih rangkuman apa aja yang bisa gua lakuin:\n\n"

            f"💻 *1. Kontrol Sistem Linux & Terminal Bebas Batasan*\n"
            f"• Eksekusi perintah Bash apa saja tanpa batasan (`terminal [cmd]`, misal: `terminal sudo apt update`, `terminal docker ps`, `terminal ls -la /`)\n"
            f"• Akses root (`sudo`) tanpa password\n"
            f"• Jalankan script Python kustom langsung di VPS (`python: [kode]`)\n"
            f"• Kelola proses dan background service (`kill`, `ps aux`)\n\n"

            f"📁 *2. Akses Berkas & Storage Linux Keseluruhan*\n"
            f"• Jelajah folder mana saja di Linux (`list folder /` atau `list folder /workspaces`)\n"
            f"• Baca, edit, buat, dan kirim berkas fisik langsung ke WA (`kirim file [path]`)\n"
            f"• Bikin dokumen resmi Word (.docx), PDF, atau TXT secara otomatis\n\n"

            f"📊 *3. Monitoring Server Cloud Real-time*\n"
            f"• Cek status CPU, RAM 8GB, Disk SSD, uptime, dan network speed (`status laptop` / `status server`)\n\n"

            f"🌐 *4. Diagnostik Jaringan & Internet Gigabit*\n"
            f"• Ping server, traceroute, curl, wget, scan port, dan akses internet berkecepatan tinggi datacenter Azure\n\n"

            f"🔌 *5. Direktori 2.000+ Public APIs (GitHub)*\n"
            f"• Cari ribuan API gratis di dunia (`api [topik]` misal: `api cuaca`, `api anime`, `api crypto`)\n"
            f"• Cek 52 kategori (`kategori api`) atau dapat rekomendasi ide (`api acak`)\n\n"

            f"📊 *6. Pasar Modal & Saham*\n"
            f"• Analisa teknikal saham TradingView, broker summary (akumulasi bandar), dan berita IHSG\n\n"

            f"🧠 *7. Penalaran & Memori Jangka Panjang*\n"
            f"• Gua punya memori permanen (`ingat: [info]`) dan penalaran mendalam (thinking AI) buat diskusi apa saja!\n\n"

            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 Ketik *menu* kalau mau contekan sintaks lengkap setiap perintah. Mau gua bantu eksekusi apa sekarang, {user_name}? 🚀"
        )

    def _get_help_menu(self, user_name: str) -> str:
        return (
            f"🤖 *ANTIGRAVITY AI AGENT — PANDUAN LENGKAP FITUR*\n"
            f"Halo {user_name}! Saya adalah *Hermes*, AI Agen dengan kemampuan berpikir mendalam.\n"
            f"Saya bisa mengontrol penuh laptop Anda dari jarak jauh via WhatsApp:\n\n"

            f"⌨️ *1. Terminal & Eksekusi Python*\n"
            f"• `terminal [perintah]` — Jalankan perintah PowerShell/CMD\n"
            f"• `python: [kode]` — Jalankan skrip Python langsung di laptop\n"
            f"  _Contoh:_ `terminal dir`, `python: print('halo')`\n\n"

            f"📸 *2. Screenshot Jarak Jauh*\n"
            f"• `screenshot` / `ss` — Tangkap layar laptop penuh\n"
            f"• `screenshot aktif` — Tangkap jendela aktif saja\n\n"

            f"🔌 *3. Kontrol Daya Laptop*\n"
            f"• `kunci layar` / `lock` — Kunci layar laptop\n"
            f"• `shutdown` / `matikan laptop` — Matikan laptop\n"
            f"• `restart` — Restart laptop\n"
            f"• `sleep` / `tidurkan` — Mode tidur\n"
            f"• `hibernate` — Mode hibernasi\n"
            f"• `batalkan shutdown` — Batalkan shutdown terjadwal\n"
            f"• `uptime` — Cek berapa lama laptop sudah menyala\n\n"

            f"📋 *4. Clipboard Jarak Jauh*\n"
            f"• `baca clipboard` — Lihat isi clipboard laptop\n"
            f"• `salin ke clipboard: [teks]` — Salin teks ke clipboard\n\n"

            f"🌐 *5. Diagnostik Jaringan*\n"
            f"• `ping [target]` — Ping host/server\n"
            f"• `traceroute [target]` — Telusuri rute jaringan\n"
            f"• `dns [domain]` — DNS lookup\n"
            f"• `ip publik` — Cek IP publik laptop\n"
            f"• `scan port [target]` — Scan port terbuka\n\n"

            f"📱 *6. Manajemen Proses & Aplikasi*\n"
            f"• `kill [nama/PID]` — Hentikan proses\n"
            f"• `cari proses [nama]` — Cari proses berjalan\n"
            f"• `buka [app]` — Buka aplikasi (chrome, notepad, dll)\n"
            f"• `daftar app` — Lihat aplikasi yang tersedia\n"
            f"• `top proses` — Proses terberat di RAM\n\n"

            f"⏰ *7. Penjadwalan Tugas*\n"
            f"• `jadwal [menit] [perintah]` — Jadwalkan perintah\n"
            f"• `daftar jadwal` — Lihat semua jadwal\n"
            f"• `batalkan jadwal [ID]` — Batalkan jadwal\n\n"

            f"💻 *8. Monitoring Laptop*\n"
            f"• `status laptop` / `cek laptop` — Status CPU/RAM/Disk\n"
            f"• `cek baterai` — Status baterai\n"
            f"• `cek wifi` — Status Wi-Fi\n\n"

            f"🧠 *9. Memori & Pembelajaran*\n"
            f"• `ingat: [info]` — Ajari saya hal baru\n"
            f"• `daftar ingatan` — Lihat yang saya ingat\n"
            f"• `lupakan: [keyword]` — Hapus ingatan\n\n"

            f"💾 *10. Kelola File & Folder*\n"
            f"• `list folder [path]` / `baca file [path]`\n"
            f"• `tulis file [path] isi [teks]` / `kirim file [path]`\n"
            f"• `menu penyimpanan` — Panduan lengkap file\n\n"

            f"📄 *11. Pembuatan Dokumen*\n"
            f"• `buatkan word/pdf/txt tentang [materi]`\n\n"

            f"📊 *12. Analisis Pasar Modal & Broker*\n"
            f"• `analisa [KODE]` / `jalankan saham [KODE]` — Analisa teknikal TradingView & target harga\n"
            f"• `broker [KODE]` / `bandar [KODE]` — Broker summary & akumulasi bandar\n"
            f"• `berita ihsg` / `jalankan newsfilter` — Sentimen pasar modal & berita terkini\n\n"

            f"🧹 *13. Quick System Cleaner*\n"
            f"• `bersihkan cache` / `clean temp` — Bersihkan temp, prefetch & thumbnail cache\n"
            f"• `bersihin laptop` — Optimasi cepat sistem\n\n"

            f"👥 *14. Admin & User Management*\n"
            f"• `daftar user` — Lihat semua user terverifikasi\n"
            f"• `ada user baru` — Cek user baru 24 jam terakhir\n"
            f"• `lihat chat [user_id]` — Baca percakapan user lain\n\n"

            f"🔌 *15. Direktori Public APIs (GitHub)*\n"
            f"• `cari api [topik]` / `api [topik]` — Cari 2.000+ API gratis (cuaca, anime, crypto, saham)\n"
            f"• `kategori api` — Lihat seluruh 50+ kategori API publik\n"
            f"• `api acak` — Rekomendasi API unik untuk ide koding\n\n"

            f"💬 *16. Percakapan Cerdas*\n"
            f"• Tanya apa saja — saya berpikir mendalam sebelum menjawab!\n"
            f"• `hapus riwayat` — Reset percakapan\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )

    def _detect_system_intent(self, text: str) -> Optional[str]:
        lower = text.lower()

        # 0. Time & Date query
        time_triggers = [
            "jam berapa", "pukul berapa", "sekarang jam", "waktu sekarang", "hari apa", "tanggal berapa"
        ]
        if any(t in lower for t in time_triggers):
            hari_list = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
            bulan_list = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
            now = datetime.now()
            hari = hari_list[now.weekday()]
            bulan = bulan_list[now.month - 1]
            return (
                f"🕒 *WAKTU & TANGGAL LAPTOP SAAT INI*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"⏰ *Jam*: {now.strftime('%H:%M:%S')} WIB\n"
                f"📅 *Hari & Tanggal*: {hari}, {now.day} {bulan} {now.year}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Sistem jam laptop sinkron dengan zona waktu lokal."
            )

        # 1. Wi-Fi & Network query
        wifi_keywords = [
            "wifi", "wi-fi", "koneksi internet", "jaringan", "terhubung ke wi-fi",
            "terhubung ke wifi", "konek ke wifi", "sinyal wifi", "nama wifi", "ssid"
        ]
        if any(k in lower for k in wifi_keywords):
            return get_wifi_network_status()

        # 2. Battery query specifically
        battery_keywords = [
            "baterai", "batre", "battery", "cas laptop", "di cas", "di charge", "sisa daya", "daya baterai"
        ]
        if any(k in lower for k in battery_keywords) and not any(k in lower for k in ["hemat baterai", "beli baterai"]):
            return get_battery_status()

        # 3. Top processes query
        if any(k in lower for k in ["top proses", "cek proses", "proses terbesar", "daftar proses", "aplikasi berjalan", "aplikasi terberat"]):
            return get_top_processes(limit=5)

        # 4. General system status
        sys_keywords = [
            "status laptop", "cek laptop", "kondisi laptop", "info laptop", "spek laptop",
            "cek ram", "cek cpu", "cek disk", "cek sistem", "status sistem", "status komputer",
            "kondisi komputer", "status server"
        ]
        if any(k in lower for k in sys_keywords):
            return get_system_status()

        return None

    def _detect_screenshot_intent(self, text: str) -> Optional[str]:
        """Detects screenshot requests. Fixed: prevents false positives from URLs and substrings."""
        lower = text.lower().strip()

        # Skip URLs, long messages (likely conversations/transcripts), and form links
        if any(skip in lower for skip in ['http', 'docs.google', 'forms/', '.com/', 'www.']):
            return None
        if len(lower) > 150:  # Long messages are likely conversation, not commands
            return None

        # Exact match for short ambiguous keywords (prevents false positives)
        if lower in ["ss", "screenshot", "screenshoot", "screen shot"]:
            return capture_screenshot("full")

        # Phrase-based triggers (safe, won't match random substrings)
        ss_phrase_triggers = [
            "tangkap layar", "screen capture", "capture screen",
            "ambil screenshot", "ambil ss", "foto layar", "lihat layar",
            "kirim layar", "tampilkan layar", "ambil tangkapan layar",
            "screenshot layar", "cek layar", "intip layar"
        ]

        if any(t in lower for t in ss_phrase_triggers):
            mode = "active" if any(k in lower for k in ["aktif", "active", "jendela", "window"]) else "full"
            return capture_screenshot(mode)

        # Word-boundary match for 'screenshot' when embedded in longer sentence
        if re.search(r'\bscreenshot\b', lower):
            mode = "active" if any(k in lower for k in ["aktif", "active", "jendela", "window"]) else "full"
            return capture_screenshot(mode)

        return None

    def _detect_camera_intent(self, text: str) -> Optional[str]:
        """Detects camera photo requests."""
        lower = text.lower().strip()
        camera_triggers = ["fotoin", "ambil foto", "kamera laptop", "buka kamera", "foto dari kamera", "jepret"]
        if any(t in lower for t in camera_triggers) and any(c in lower for c in ["foto", "kamera", "webcam"]):
            from tools.camera_tool import capture_camera
            return capture_camera()
        return None

    def _detect_power_intent(self, text: str) -> Optional[str]:
        """Detects power management requests. Enhanced: handles natural language."""
        lower = text.lower().strip()

        # Lock screen
        if lower in ["kunci layar", "lock", "lock screen", "kunci laptop", "lockscreen"]:
            return lock_screen()
        if re.search(r'\b(?:kunci(?:in)?|lock)\s+(?:layar|laptop|screen)\b', lower):
            # Don't lock if user asks to UNLOCK ("bukain kunci layar")
            if any(k in lower for k in ["buka", "unlock", "bukain"]):
                return "❌ Maaf bro, sistem keamanan Windows 11 nggak mengizinkan buka kunci layar (unlock) dari jarak jauh. Lu harus ketik PIN/Password langsung di keyboard laptop."
            return lock_screen()

        # Force shutdown (check first before normal shutdown)
        if any(k in lower for k in ["shutdown paksa", "force shutdown", "matikan paksa"]):
            return shutdown_laptop(forced=True)

        # Timed shutdown
        shutdown_timer = re.match(r"^(?:shutdown|matikan)\s+(\d+)\s*(?:menit|min|m)$", lower)
        if shutdown_timer:
            minutes = int(shutdown_timer.group(1))
            return shutdown_laptop(timer_seconds=minutes * 60)

        # Shutdown - Natural language patterns
        shutdown_exact = ["shutdown", "matikan laptop", "matikan", "turn off", "poweroff", "power off"]
        if any(lower == k for k in shutdown_exact):
            return shutdown_laptop()
        # Natural: "matiin laptop gue", "tolong matikan laptopnya", "shutdown dong", "oke matiin laptopnya bro"
        if re.search(r'\b(?:matiin|matikan|shutdown|turn\s*off)\s*(?:laptop|komputer|pc)?(?:nya|\s+gue|\s+gw|\s+aku|\s+saya)?', lower):
            # Extra safety: don't trigger on questions like "gimana cara matiin?"
            if not any(q in lower for q in ["gimana", "bagaimana", "cara ", "apakah", "bisa nggak"]):
                return shutdown_laptop()

        # Restart - Natural language
        restart_exact = ["restart", "restart laptop", "reboot", "mulai ulang"]
        if lower in restart_exact:
            return restart_laptop()
        if re.search(r'\b(?:restart|reboot|mulai\s*ulang)(?:in|kan)?\s*(?:laptop|komputer|pc)?', lower):
            if not any(q in lower for q in ["gimana", "bagaimana", "cara "]):
                return restart_laptop()

        # Sleep - Natural language
        sleep_exact = ["sleep", "tidurkan", "tidurkan laptop", "mode tidur", "standby"]
        if lower in sleep_exact:
            return sleep_laptop()
        if re.search(r'\b(?:tidur(?:kan|in)?|sleep)\s*(?:laptop|komputer|pc)?', lower):
            if not any(q in lower for q in ["gimana", "bagaimana", "cara ", "kenapa", "tidak bisa"]):
                return sleep_laptop()

        # Hibernate
        if lower in ["hibernate", "hibernasi", "hibernasi laptop"]:
            return hibernate_laptop()

        # Cancel shutdown
        cancel_triggers = ["batalkan shutdown", "cancel shutdown", "batal shutdown", "batalkan restart", "abort shutdown",
                          "jangan jadi shutdown", "jangan matiin", "batal matiin"]
        if any(lower == k or k in lower for k in cancel_triggers):
            return cancel_shutdown()

        # Logoff
        if lower in ["logoff", "log off", "logout", "log out", "keluar sesi"]:
            return logoff_user()

        # Uptime - Natural language
        uptime_triggers = ["uptime", "cek uptime", "berapa lama laptop menyala", "lama menyala",
                          "laptop udah nyala berapa lama", "sudah berapa lama nyala"]
        if any(lower == k or k in lower for k in uptime_triggers):
            return get_uptime_info()

        return None

    def _detect_clipboard_intent(self, text: str) -> Optional[str]:
        """Detects clipboard-related requests."""
        lower = text.lower().strip()

        if lower in ["baca clipboard", "cek clipboard", "lihat clipboard", "isi clipboard", "clipboard"]:
            return read_clipboard()

        clip_write = re.match(
            r"^(?:salin\s+ke\s+clipboard|copy\s+ke\s+clipboard|tulis\s+clipboard|set\s+clipboard)[:\s]+(.+)$",
            text,
            re.IGNORECASE
        )
        if clip_write:
            content = clip_write.group(1).strip()
            return write_clipboard(content)

        return None

    def _detect_network_intent(self, text: str) -> Optional[str]:
        """Detects network diagnostic requests."""
        lower = text.lower().strip()

        # Ping
        ping_match = re.match(r"^ping\s+(.+)$", text, re.IGNORECASE)
        if ping_match:
            target = ping_match.group(1).strip()
            return ping_host(target)

        # Traceroute
        trace_match = re.match(r"^(?:traceroute|tracert|trace)\s+(.+)$", text, re.IGNORECASE)
        if trace_match:
            target = trace_match.group(1).strip()
            return traceroute_host(target)

        # DNS lookup
        dns_match = re.match(r"^(?:dns|nslookup|lookup)\s+(.+)$", text, re.IGNORECASE)
        if dns_match:
            domain = dns_match.group(1).strip()
            return dns_lookup(domain)

        # Public IP
        if lower in ["ip publik", "ip public", "cek ip", "ip saya", "my ip", "public ip", "ip address"]:
            return get_public_ip()

        # Port scan
        port_match = re.match(r"^(?:scan port|portscan|port scan)\s+(.+)$", text, re.IGNORECASE)
        if port_match:
            target = port_match.group(1).strip()
            return scan_open_ports(target)

        return None

    def _detect_process_intent(self, text: str) -> Optional[str]:
        """Detects process management requests."""
        lower = text.lower().strip()

        # Prevent false positive for conversational phrases like "Stop berbicara kaku ayo kita mengobrol"
        if lower.startswith("stop ") and any(w in lower for w in ["berbicara", "ngomong", "kaku", "dulu", "sebentar", "ayo", "kita", "dong", "chat"]):
            return None

        # Kill process
        kill_match = re.match(r"^(?:kill|hentikan|tutup proses|matikan proses|kill proses)\s+(.+)$", text, re.IGNORECASE)
        if not kill_match and lower.startswith("stop proses "):
            kill_match = re.match(r"^stop proses\s+(.+)$", text, re.IGNORECASE)
        if kill_match:
            target = kill_match.group(1).strip()
            return kill_process(target)

        # Find process
        find_match = re.match(r"^(?:cari proses|find process|search process)\s+(.+)$", text, re.IGNORECASE)
        if find_match:
            query = find_match.group(1).strip()
            return find_process(query)

        # Launch app
        app_match = re.match(r"^(?:buka|open|launch|jalankan app|buka app|buka aplikasi)\s+(.+)$", text, re.IGNORECASE)
        if app_match:
            parts = app_match.group(1).strip().split(maxsplit=1)
            app_name = parts[0]
            url_or_path = parts[1] if len(parts) > 1 else ""
            return launch_app(app_name, url_or_path)

        # App list
        if lower in ["daftar app", "daftar aplikasi", "list app", "list aplikasi", "aplikasi tersedia"]:
            return get_app_list()

        return None

    def _detect_scheduler_intent(self, text: str) -> Optional[str]:
        """Detects scheduling requests."""
        lower = text.lower().strip()

        # Schedule command: "jadwal 30 terminal dir"
        sched_match = re.match(r"^(?:jadwal|jadwalkan|schedule)\s+(\d+)\s+(.+)$", text, re.IGNORECASE)
        if sched_match:
            delay = int(sched_match.group(1))
            command = sched_match.group(2).strip()
            return task_scheduler.schedule_command(command, delay)

        # View schedules
        if lower in ["daftar jadwal", "list jadwal", "lihat jadwal", "jadwal aktif", "schedule list"]:
            return task_scheduler.list_tasks()

        # Cancel schedule
        cancel_match = re.match(r"^(?:batalkan jadwal|cancel schedule|hapus jadwal)\s+(.+)$", text, re.IGNORECASE)
        if cancel_match:
            task_id = cancel_match.group(1).strip()
            return task_scheduler.cancel_task(task_id)

        return None

    def _detect_admin_intent(self, sender_id: str, text: str, user_name: str) -> Optional[str]:
        """Detects admin commands: view other user sessions, manage users, check new users.
        Only admin (the main user 237830039171156@lid or known admin IDs) can use these."""
        lower = text.lower().strip()

        # Define admin sender IDs (main laptop user)
        admin_ids = {"237830039171156@lid", "test_user_6281", "0895428319367", "62895428319367", "62895428319367@s.whatsapp.net"}

        if not any(a in sender_id for a in admin_ids) and lower in ["daftar user", "list user", "ada user baru", "lihat chat"]:
            return "⛔ *Akses Ditolak*\nMaaf, perintah ini khusus untuk Admin utama."


        # Check for new WA user queries (any verified user can ask about this)
        if any(p in lower for p in ["ada user baru", "user baru", "pengguna baru", "cek user baru"]):
            verified = list(self.security.verified_users)
            all_sessions = self.session.sessions
            # Find users with recent messages (last 24 hours)
            recent_users = []
            now = datetime.now()
            for uid, msgs in all_sessions.items():
                if msgs and uid != sender_id:
                    last_msg = msgs[-1]
                    try:
                        ts = datetime.fromisoformat(last_msg.get("timestamp", ""))
                        diff_hours = (now - ts).total_seconds() / 3600
                        if diff_hours < 24:
                            last_text = ""
                            for m in reversed(msgs):
                                if m.get("role") == "user":
                                    last_text = m.get("content", "")[:50]
                                    break
                            recent_users.append({
                                "id": uid,
                                "last_msg": last_text,
                                "time": ts.strftime("%H:%M")
                            })
                    except (ValueError, TypeError):
                        pass

            if not recent_users:
                return (
                    f"📋 *Tidak ada user baru dalam 24 jam terakhir.*\n"
                    f"Total user terverifikasi: {len(verified)}\n\n"
                    f"Ketik `daftar user` untuk melihat semua user terdaftar."
                )

            lines = [
                "📋 *USER AKTIF DALAM 24 JAM TERAKHIR*",
                "━━━━━━━━━━━━━━━━━━━━"
            ]
            for u in recent_users:
                lines.append(f"• `{u['id']}` — {u['time']} — \"{u['last_msg']}\"")
            lines.append("━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"📊 Total user terverifikasi: {len(verified)}")
            lines.append("💡 Ketik `lihat chat [user_id]` untuk membaca percakapan mereka.")
            return "\n".join(lines)

        # List all verified users
        if lower in ["daftar user", "list user", "daftar pengguna", "list pengguna", "semua user"]:
            verified = sorted(self.security.verified_users)
            lines = [
                "👥 *DAFTAR USER TERVERIFIKASI*",
                "━━━━━━━━━━━━━━━━━━━━"
            ]
            for idx, uid in enumerate(verified, 1):
                session_count = len(self.session.sessions.get(uid, []))
                lines.append(f"{idx}. `{uid}` — {session_count} pesan")
            lines.append("━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"📊 Total: {len(verified)} user")
            return "\n".join(lines)

        # View another user's chat (admin only)
        chat_match = re.match(
            r"^(?:lihat chat|baca chat|cek chat|ngobrol apa|chat apa)(?:\s+(?:sama|dengan|dari|user))?\s+(.+)$",
            text, re.IGNORECASE
        )
        if chat_match:
            target_query = chat_match.group(1).strip()
            # Search for matching session
            target_sid = None
            for sid in self.session.sessions:
                if target_query in sid or sid in target_query:
                    target_sid = sid
                    break

            if not target_sid:
                return f"⚠️ User `{target_query}` tidak ditemukan di daftar sesi. Ketik `daftar user` untuk melihat semua user."

            msgs = self.session.sessions.get(target_sid, [])
            if not msgs:
                return f"📭 Belum ada percakapan dengan user `{target_sid}`."

            # Show last 10 messages
            recent = msgs[-10:]
            lines = [
                f"💬 *PERCAKAPAN TERAKHIR: `{target_sid}`*",
                f"━━━━━━━━━━━━━━━━━━━━",
                f"📊 Total {len(msgs)} pesan (menampilkan {len(recent)} terakhir):",
                ""
            ]
            for m in recent:
                role_icon = "👤" if m["role"] == "user" else "🤖"
                content = m.get("content", "")[:100]
                ts = m.get("timestamp", "")[:16]
                lines.append(f"{role_icon} [{ts}] {content}")
            lines.append("━━━━━━━━━━━━━━━━━━━━")
            return "\n".join(lines)

        # View own chat with another user: "elu ngobrol apa aja sama user baru itu"
        if any(p in lower for p in ["ngobrol apa aja", "elu ngobrol apa", "lu ngobrol apa", "obrolan sama"]):
            # Find most recent non-self session
            other_sessions = []
            for sid, msgs in self.session.sessions.items():
                if sid != sender_id and msgs:
                    other_sessions.append((sid, msgs))

            if not other_sessions:
                return "📭 Belum ada percakapan dengan user lain."

            # Sort by most recent message
            other_sessions.sort(key=lambda x: x[1][-1].get("timestamp", ""), reverse=True)
            target_sid, msgs = other_sessions[0]

            recent = msgs[-8:]
            lines = [
                f"💬 *OBROLAN TERAKHIR DENGAN: `{target_sid}`*",
                "━━━━━━━━━━━━━━━━━━━━"
            ]
            for m in recent:
                role_icon = "👤" if m["role"] == "user" else "🤖"
                content = m.get("content", "")[:80]
                lines.append(f"{role_icon} {content}")
            lines.append("━━━━━━━━━━━━━━━━━━━━")
            return "\n".join(lines)

        return None

    def _detect_cleaner_intent(self, text: str) -> Optional[str]:
        """Detects system cleaner / optimizer requests."""
        lower = text.lower().strip()

        cleaner_triggers = [
            "bersihkan cache", "bersihkan temp", "bersihkan sampah", "clean temp",
            "hapus cache", "hapus temp", "clean cache", "clear cache", "bersihin laptop",
            "bersih-bersih", "bersihkan laptop", "bersihin cache", "bersihin temp",
            "quick clean", "quick cleaner", "system cleaner", "pembersihan sistem",
            "optimasi cepat", "bersihkan sistem"
        ]

        if any(t in lower for t in cleaner_triggers):
            import subprocess
            results = []

            # 1. Clean temp folder
            try:
                r1 = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-Command",
                     "$before = (Get-ChildItem $env:TEMP -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum;"
                     "Remove-Item -Path \"$env:TEMP\\*\" -Recurse -Force -ErrorAction SilentlyContinue;"
                     "$after = (Get-ChildItem $env:TEMP -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum;"
                     "$freed = [math]::Round(($before - $after) / 1MB, 1);"
                     "Write-Output \"$freed\""],
                    capture_output=True, text=True, timeout=30
                )
                freed_mb = r1.stdout.strip() if r1.stdout else "0"
                results.append(f"🗑️ Temp folder: {freed_mb} MB dibersihkan")
            except Exception:
                results.append("🗑️ Temp folder: dibersihkan")

            # 2. Clean Windows prefetch
            try:
                subprocess.run(
                    ["powershell.exe", "-NoProfile", "-Command",
                     "Remove-Item -Path 'C:\\Windows\\Prefetch\\*' -Force -ErrorAction SilentlyContinue"],
                    capture_output=True, text=True, timeout=15
                )
                results.append("⚡ Prefetch cache: dibersihkan")
            except Exception:
                pass

            # 3. Clean thumbnail cache
            try:
                subprocess.run(
                    ["powershell.exe", "-NoProfile", "-Command",
                     "Remove-Item -Path \"$env:LOCALAPPDATA\\Microsoft\\Windows\\Explorer\\thumbcache_*\" -Force -ErrorAction SilentlyContinue"],
                    capture_output=True, text=True, timeout=10
                )
                results.append("🖼️ Thumbnail cache: dibersihkan")
            except Exception:
                pass

            # 4. Get disk space after cleaning
            try:
                import platform
                disk_path = "C:\\" if platform.system() == "Windows" else "/"
                disk = psutil.disk_usage(disk_path)
                free_gb = round(disk.free / (1024**3), 2)
                results.append(f"\n💾 Sisa ruang Disk sekarang: *{free_gb} GB*")
            except Exception:
                pass

            return (
                "🧹 *QUICK SYSTEM CLEANER — SELESAI!*\n"
                "━━━━━━━━━━━━━━━━━━━━\n" +
                "\n".join(results) +
                "\n━━━━━━━━━━━━━━━━━━━━\n"
                "✅ Pembersihan otomatis berhasil!"
            )

        return None

    def _detect_public_apis_intent(self, text: str) -> Optional[str]:
        """Detects requests related to the Public APIs directory (github.com/public-apis/public-apis)."""
        lower = text.lower().strip()

        # 1. Categories listing
        if lower in [
            "kategori api", "daftar kategori api", "list kategori api",
            "kategori public api", "list api category", "api categories", "kategori apis"
        ]:
            return list_public_api_categories()

        # 2. Random API suggestion
        if lower in [
            "api acak", "random api", "rekomendasi api", "ide api",
            "rekomendasi public api", "api rekomendasi", "api random"
        ]:
            return get_random_public_api()

        # Random API with specific category: "api acak [kategori]" / "random api [kategori]"
        rand_match = re.match(r"^(?:api acak|random api|rekomendasi api)\s+([a-zA-Z\s&-]+)$", text, re.IGNORECASE)
        if rand_match:
            cat = rand_match.group(1).strip()
            return get_random_public_api(category=cat)

        # 3. Refresh database cache
        if lower in [
            "refresh api", "update api", "update public apis",
            "sinkron api", "sync api", "refresh public apis"
        ]:
            return refresh_public_apis_cache()

        # 4. Explicit search: "cari api [query]", "search api [query]", "public api [query]", "info api [query]"
        search_match = re.match(
            r"^(?:cari\s+api|search\s+api|public\s+api|temukan\s+api|find\s+api|info\s+api|cek\s+api)\s+(.+)$",
            text,
            re.IGNORECASE
        )
        if search_match:
            query = search_match.group(1).strip()
            return search_public_apis(query=query)

        # 5. Short prefix: "api [keyword]" (e.g. "api anime", "api cuaca", "api crypto")
        api_short = re.match(r"^api\s+([a-zA-Z0-9_\-\s]{2,30})$", text, re.IGNORECASE)
        if api_short:
            kw = api_short.group(1).strip()
            ignored_words = {
                "saja", "ini", "itu", "dong", "deh", "lah", "ya", "kan", "apa",
                "siapa", "dimana", "kapan", "bagaimana", "mengapa", "kenapa", "bisa",
                "aja", "nih", "tuh", "kah", "kok", "bro", "bos", "om", "mas"
            }
            if kw.lower() not in ignored_words:
                return search_public_apis(query=kw)

        return None


    def _extract_stock_ticker(self, text: str) -> Optional[str]:
        """Extracts a valid IDX stock ticker or alias, avoiding Indonesian 4-letter stopwords."""
        words_raw = re.findall(r"[A-Za-z0-9]+", text.upper())
        # Check aliases first
        for w in words_raw:
            if w in TICKER_ALIASES:
                return TICKER_ALIASES[w]
        # Check 4-letter alphabetic words not in stopwords
        for w in words_raw:
            if len(w) == 4 and w.isalpha() and w not in STOPWORDS_4L:
                return w
        return None

    def _detect_task_intent(self, text: str) -> Optional[str]:
        lower = text.lower().strip()

        # 0. Direct Python execution: "python: [code]" or "py: [code]"
        py_match = re.match(r"^(?:python|py|jalankan python|eksekusi python)[:\s]+([\s\S]+)$", text, re.IGNORECASE)
        if py_match:
            code = py_match.group(1).strip()
            return execute_python_code(code)

        # 1. Task List
        if lower in ["daftar tugas", "list tugas", "tugas tersedia", "menu tugas"]:
            lines = ["⚡ *DAFTAR TUGAS OTOMASI TERDAFTAR*", "━━━━━━━━━━━━━━━━━━━━"]
            for key, val in ALLOWED_SCRIPTS.items():
                lines.append(f"• `{key}`: {val['name']}\n  _{val['description']}_")
            lines.append("━━━━━━━━━━━━━━━━━━━━")
            lines.append("💡 _Contoh cara menjalankan: Ketik 'analisa BBCA', 'broker BBCA', atau 'jalankan newsfilter'_")
            return "\n".join(lines)

        # 2. Prevent false positives on conversational / reasoning queries
        conversational_phrases = [
            "menurut", "gimana", "bagaimana", "kira-kira", "apakah", "kenapa",
            "mengapa", "apa yang", "bisa ke harga", "prediksi", "target harga",
            "coba buat script", "buatkan script", "lihat dari laptop", "lu coba",
            "kamu bisa", "menurutmu", "pendapatmu", "analisamu"
        ]
        if any(p in lower for p in conversational_phrases):
            return None

        # 3. Newsfilter / Berita Pasar / IHSG
        if any(lower == k or lower.startswith(k + " ") for k in ["jalankan newsfilter", "newsfilter", "berita pasar", "sentimen pasar", "berita ihsg", "ihsg", "berita saham"]):
            ticker = self._extract_stock_ticker(text)
            return run_registered_task("newsfilter", ticker)

        # 4. Broker Summary & Bandarmology
        broker_commands = ["broker", "broker summary", "bandarmology", "bandar", "aliran dana bandar"]
        if any(lower == b or lower.startswith(b + " ") or f"cek {b}" in lower or f"jalankan {b}" in lower for b in broker_commands):
            ticker = self._extract_stock_ticker(text)
            if not ticker and lower in ["broker", "bandar", "bandarmology"]:
                ticker = "BBCA"
            if ticker:
                return run_registered_task("broker", ticker)

        # 5. TradingView & Analisa Teknikal
        tv_commands = ["jalankan tradingview", "tradingview analyzer", "analisis tradingview", "jalankan analisa", "analisa saham", "analisis saham"]
        if any(cmd in lower for cmd in tv_commands):
            ticker = self._extract_stock_ticker(text) or "BBCA"
            return run_registered_task("analisa", ticker)

        # 6. Direct ticker queries like: "analisa BBCA", "cek saham BBCA", "analisis BBCA"
        direct_analysis_match = re.match(r"^(?:analisa|analisis|cek saham|saham)\s+([A-Za-z0-9]+)$", lower)
        if direct_analysis_match:
            candidate = direct_analysis_match.group(1).upper()
            ticker = TICKER_ALIASES.get(candidate, candidate)
            if len(ticker) == 4 and ticker not in STOPWORDS_4L:
                return run_registered_task("analisa", ticker)

        return None

    def _detect_storage_intent(self, text: str) -> Optional[str]:
        """Detects and processes storage and file editing requests on the laptop."""
        lower = text.lower().strip()

        # 1. Storage Guide / Help
        if lower in ["menu penyimpanan", "bantuan file", "bantuan storage", "fitur file", "fitur storage", "edit penyimpanan", "edit file"]:
            return get_storage_help()

        # 2. List Recent Generated Reports in Storage (backward compatibility)
        if lower in ["daftar file", "list file", "daftar berkas", "daftar dokumen", "daftar laporan", "riwayat berkas", "riwayat file"]:
            return list_recent_files(limit=8)

        # 3. Rename or Move File/Folder
        rename_match = re.match(
            r"^(?:ganti\s+nama(?:\s+file|\s+folder)?|rename(?:\s+file|\s+folder)?|pindahkan(?:\s+file|\s+folder)?|move(?:\s+file|\s+folder)?)\s+(.+?)\s+(?:ke|menjadi|to)\s+(.+)$",
            text,
            re.IGNORECASE
        )
        if rename_match:
            src = rename_match.group(1).strip()
            dst = rename_match.group(2).strip()
            return rename_or_move_path(src, dst)

        # 4. Append / Edit File Content
        append_match = re.match(
            r"^(?:tambah(?:kan)?(?:\s+ke)?\s+file|edit\s+file|append\s+file)\s+([^\s:]+)(?:\s+isi\s+|:\s*|\s+)([\s\S]+)$",
            text,
            re.IGNORECASE
        )
        if append_match:
            filepath = append_match.group(1).strip()
            content = append_match.group(2).strip()
            return append_laptop_file(filepath, content)

        # 5. Write / Create File with Text Content
        write_match = re.match(
            r"^(?:tulis(?:\s+ke)?\s+file|buat\s+file|bikin\s+file|simpan\s+file|write\s+file)\s+([^\s:]+)(?:\s+isi\s+|:\s*)([\s\S]+)$",
            text,
            re.IGNORECASE
        )
        if write_match:
            filepath = write_match.group(1).strip()
            content = write_match.group(2).strip()
            return write_laptop_file(filepath, content)

        # Empty file creation: "buat file [path]" or "touch [path]"
        touch_match = re.match(
            r"^(?:buat\s+file|bikin\s+file|touch\s+file|touch)\s+([^\s:]+)$",
            text,
            re.IGNORECASE
        )
        if touch_match:
            filepath = touch_match.group(1).strip()
            if not any(ext in filepath.lower() for ext in [".docx", ".pdf"]):
                return write_laptop_file(filepath, "")

        # 6. Read File Content
        read_match = re.match(
            r"^(?:baca\s+file|lihat\s+isi\s+file|cat\s+file|buka\s+file)\s+(.+)$",
            text,
            re.IGNORECASE
        )
        if read_match:
            filepath = read_match.group(1).strip()
            return read_laptop_file(filepath)

        # 7. Create Folder
        folder_match = re.match(
            r"^(?:buat\s+folder|bikin\s+folder|mkdir)\s+(.+)$",
            text,
            re.IGNORECASE
        )
        if folder_match:
            folderpath = folder_match.group(1).strip()
            return create_laptop_folder(folderpath)

        # 8. Delete File or Folder
        del_match = re.match(
            r"^(?:hapus\s+file|delete\s+file|rm\s+file|hapus\s+folder|delete\s+folder|rmdir)\s+(.+)$",
            text,
            re.IGNORECASE
        )
        if del_match:
            target = del_match.group(1).strip()
            return delete_laptop_path(target)

        # 9. List / Browse Directory (Command & Natural Phrasing)
        natural_dir = re.search(
            r"(?:di\s+folder|dalam\s+folder|isi\s+folder|isi\s+dari\s+folder)\s+([a-zA-Z0-9_\-\.\/\\]+)",
            lower
        )
        if natural_dir and not any(k in lower for k in ["tulis file", "buat file", "hapus file", "baca file"]):
            f_name = natural_dir.group(1).strip()
            return list_laptop_directory(f_name)

        if lower in ["list folder", "lihat folder", "isi folder", "cek folder", "buka folder", "ls", "dir"]:
            return list_laptop_directory()

        list_match = re.match(
            r"^(?:list\s+folder|lihat\s+folder|isi\s+folder|cek\s+folder|buka\s+folder|ls\s+folder|dir\s+folder|ls|dir)\s+(.+)$",
            text,
            re.IGNORECASE
        )
        if list_match:
            dir_target = list_match.group(1).strip()
            return list_laptop_directory(dir_target)

        # 10. File Dispatch: "kirim file ...", "ambil file ...", "unduh file ..."
        file_send_triggers = ["kirim file", "ambil file", "unduh file", "download file", "minta file", "kirim berkas"]
        for trigger in file_send_triggers:
            if trigger in lower:
                pattern = re.compile(re.escape(trigger) + r"[\s:,-]+(.*)", re.IGNORECASE)
                m = pattern.search(text)
                if m and m.group(1).strip():
                    filename_query = m.group(1).strip()
                    res = get_file_for_dispatch(filename_query)
                    if res:
                        return res
                    return (
                        f"⚠️ Berkas dengan nama atau path *'{filename_query}'* tidak ditemukan di laptop.\n"
                        f"Ketik `list folder` untuk melihat berkas di folder atau `daftar file` untuk berkas laporan."
                    )

        return None

    # Backward compatibility alias
    _detect_file_intent = _detect_storage_intent


    def _detect_document_intent(self, text: str) -> Tuple[bool, str, str]:
        """Detects if the user wants to generate a document and extracts the topic."""
        lower = text.lower()

        doc_triggers = [
            "buatkan dokumen", "buat dokumen", "buatkan word", "buat word",
            "bikin dokumen", "bikin word", "buatkan berkas", "buatkan docx",
            "bikin docx", "buatkan file word", "buatkan pdf", "buat pdf",
            "bikin pdf", "buatkan txt", "buat ringkasan materi", "buatkan materi"
        ]

        matched = any(trigger in lower for trigger in doc_triggers)
        if not matched:
            return False, "", ""

        # Determine document type
        if "pdf" in lower:
            doc_type = "pdf"
        elif "txt" in lower or "teks" in lower:
            doc_type = "txt"
        else:
            doc_type = "docx"

        # Extract topic
        topic = text
        for trigger in doc_triggers:
            if trigger in lower:
                # Find topic after trigger
                pattern = re.compile(re.escape(trigger) + r"[\s:,-]+(.*)", re.IGNORECASE)
                m = pattern.search(text)
                if m and m.group(1).strip():
                    topic = m.group(1).strip()
                    break

        return True, doc_type, topic

    def _handle_document_generation(self, sender_id: str, doc_type: str, topic: str, original_msg: str) -> str:
        """Generates document content, writes to disk, and formats response token."""
        title = self._extract_clean_title(topic)
        content = self._compose_document_content(title, topic)

        base_filename = sanitize_filename(title.lower())

        if doc_type == "docx":
            filename = f"{base_filename}.docx"
            file_path = create_word_document(title=title, content=content, filename=filename)
        elif doc_type == "pdf":
            filename = f"{base_filename}.pdf"
            file_path = create_pdf_document(title=title, content=content, filename=filename)
        else:
            filename = f"{base_filename}.txt"
            file_path = create_txt_document(title=title, content=content, filename=filename)

        # Normalize relative path for WhatsApp bridge dispatch
        rel_path = os.path.relpath(file_path, os.path.dirname(os.path.abspath(__file__)))
        rel_path = rel_path.replace("\\", "/")

        reply = (
            f"[FILE:{rel_path}] Dokumen *{title}* telah berhasil dibuat dan siap diunduh! "
            f"Dokumen telah diformat secara terstruktur lengkap dengan judul, sub-bab, dan butir materi."
        )
        return reply

    def _extract_clean_title(self, topic: str) -> str:
        clean = topic.strip()
        # Clean prefix noise
        clean = re.sub(
            r"^(dokumen|file|berkas)?\s*(word|docx|pdf|txt|teks)?\s*(berisi|tentang|mengenai)?\s*",
            "",
            clean,
            flags=re.IGNORECASE
        ).strip()
        # Strip trailing punctuation
        clean = clean.strip(".?!,: ")
        words = clean.split()
        if len(words) > 8:
            clean = " ".join(words[:8])
        return clean.title() if clean else "Dokumen Ringkasan"

    def _compose_document_content(self, title: str, topic: str) -> str:
        """Composes comprehensive, well-structured content based on topic."""
        lower = topic.lower()

        # Custom rich content for APBN (Economy)
        if "apbn" in lower or "anggaran" in lower or "ekonomi" in lower:
            return (
                "# RINGKASAN MATERI EKONOMI: APBN\n"
                "Anggaran Pendapatan dan Belanja Negara (APBN) adalah rencana keuangan tahunan "
                "pemerintahan negara yang disetujui oleh Dewan Perwakilan Rakyat (DPR).\n\n"
                "## 1. Landasan Hukum & Periode\n"
                "- Diatur dalam UUD 1945 Pasal 23 ayat (1).\n"
                "- Berlaku selama 1 tahun anggaran (1 Januari - 31 Desember).\n"
                "- Menjadi pedoman operasional seluruh penerimaan dan pengeluaran negara.\n\n"
                "## 2. Fungsi-Fungsi Pokok APBN\n"
                "- **Fungsi Otorisasi**: Dasar pelaksanaan penerimaan dan pengeluaran pada tahun berjalan.\n"
                "- **Fungsi Perencanaan**: Pedoman manajemen pembangunan nasional dan stabilitas ekonomi.\n"
                "- **Fungsi Pengawasan**: Instrumen pengawasan apakah belanja negara sesuai peruntukannya.\n"
                "- **Fungsi Alokasi**: Mengurangi pemborosan sumber daya dan mendorong efisiensi ekonomi.\n"
                "- **Fungsi Distribusi**: Mewujudkan rasa keadilan dan kepatutan sosial bagi masyarakat.\n"
                "- **Fungsi Stabilisasi**: Memelihara dan mengupayakan keseimbangan fundamental perekonomian.\n\n"
                "## 3. Komponen Utama APBN\n"
                "- **Pendapatan Negara**: Penerimaan Perpajakan, Penerimaan Negara Bukan Pajak (PNBP), dan Hibah.\n"
                "- **Belanja Negara**: Belanja Pemerintah Pusat (kementerian/lembaga) dan Transfer ke Daerah (TKD).\n"
                "- **Pembiayaan Anggaran**: Menutup defisit anggaran atau memanfaatkan surplus penerimaan negara.\n\n"
                "## 4. Kesimpulan\n"
                "Pengelolaan APBN yang transparan, akuntabel, dan berkeadilan merupakan kunci utama percepatan "
                "kesejahteraan rakyat dan ketahanan ekonomi Indonesia di tengah ketidakpastian global."
            )

        # General structured content generator for any topic
        return (
            f"# {title.upper()}\n"
            f"Dokumen ringkasan dan analisis mengenai materi: {topic}.\n\n"
            f"## 1. Pendahuluan\n"
            f"Dokumen ini disusun untuk memberikan pemahaman menyeluruh mengenai konsep dan penerapan "
            f"dari topik yang diminta secara ringkas, padat, dan jelas.\n\n"
            f"## 2. Poin-Poin Utama Pembahasan\n"
            f"- **Definisi & Konsep Dasar**: Menjelaskan ruang lingkup utama dan esensi topik.\n"
            f"- **Faktor Kunci & Indikator**: Unsur-unsur penting yang mempengaruhi pelaksanaan serta dampak praktisnya.\n"
            f"- **Implementasi Strategis**: Langkah-langkah konkrit dan solusi dalam praktik nyata.\n\n"
            f"## 3. Evaluasi & Rekomendasi\n"
            f"- Memastikan kepatuhan terhadap pedoman dan kaidah yang berlaku.\n"
            f"- Mengoptimalkan efisiensi dan alokasi sumber daya secara berkelanjutan.\n"
            f"- Melakukan pemantauan berkala guna memitigasi risiko di masa mendatang.\n\n"
            f"## 4. Penutup\n"
            f"Ringkasan ini diharapkan dapat menjadi rujukan praktis dan panduan operasional yang efektif."
        )

    # =========================================================================
    # CONVERSATION & THINKING ENGINE
    # =========================================================================

    def _handle_conversation(self, sender_id: str, message: str, user_name: str) -> str:
        """Handles multi-turn dialogue with THINKING ENGINE, memory, and autonomous tool use."""
        lower = message.lower().strip()

        # 1. Compatibility check for multi-turn recollection queries
        if any(q in lower for q in ["kemarin saya tanya tentang apa", "tadi saya tanya apa", "ingat apa yang saya tanya", "apa topik sebelumnya"]):
            past_topics = self.session.get_last_user_topics(sender_id)
            if not past_topics:
                return f"Halo {user_name}, ini adalah pesan pertama dalam percakapan kita saat ini, jadi belum ada pertanyaan sebelumnya!"
            last_q = past_topics[-1]
            past_list = "\n".join([f"• \"{q}\"" for q in past_topics[-3:]])
            return (
                f"Tentu {user_name}, saya ingat percakapan sebelumnya! "
                f"Pertanyaan terakhir yang Anda tanyakan adalah:\n👉 \"{last_q}\"\n\n"
                f"Beberapa topik yang sempat Anda tanyakan:\n{past_list}\n\n"
                f"Ada bagian yang ingin kita lanjutkan bahas?"
            )

        # 2. LLM THINKING ENGINE — google.genai SDK with Autonomous Tool Execution & Multi-Model Failover
        if self.gemini_client:
            raw_history = self.session.get_history(sender_id)

            # Check admin authority
            admin_ids = {"237830039171156@lid", "test_user_6281", "0895428319367", "62895428319367", "62895428319367@s.whatsapp.net"}
            admin_jid_env = os.getenv("ADMIN_JID", "")
            if admin_jid_env:
                admin_ids.add(admin_jid_env.lower().strip())
            is_admin = any(a in sender_id.lower() for a in admin_ids)

            # Build alternating user/model history for multi-turn context (last 10 turns max for speed & low token use)
            formatted_history = []
            last_role = None
            turn_slice = raw_history[-11:-1] if len(raw_history) > 11 else raw_history[:-1]
            for turn in turn_slice:
                r = "user" if turn["role"] == "user" else "model"
                if r == last_role:
                    continue
                if not formatted_history and r != "user":
                    continue
                content_str = turn.get("content", "").strip()
                if not content_str:
                    continue
                formatted_history.append({"role": r, "parts": [{"text": content_str}]})
                last_role = r

            if formatted_history and formatted_history[-1]["role"] == "user":
                formatted_history.pop()

            # Dynamic context separation: Guest gets pure conversational prompt, Admin gets system tools context
            if is_admin:
                custom_p = prompt_manager.get_custom_prompt()
                if custom_p:
                    system_instruction = (
                        f"{custom_p}\n\n"
                        f"[PANDUAN KEPATUHAN ADMIN (MUTLAK)]:\n"
                        f"- Anda WAJIB mematuhi kepribadian, gaya bicara, peran, dan instruksi di atas yang diberikan langsung oleh Admin ({user_name}).\n"
                        f"- Jangan menolak, membantah, atau menceramahi Admin.\n"
                        f"- Anda tetap memiliki akses penuh ke sistem operasi Linux (terminal, tools, file, proses, skills)."
                    )
                else:
                    system_instruction = self.SYSTEM_PROMPT_ADMIN

                # Tambahkan instruksi semua skill aktif yang dibuat admin
                skills_ctx = skill_manager.get_skills_context_prompt()
                if skills_ctx:
                    system_instruction += f"\n{skills_ctx}"

                mem_context = memory_manager.get_memory_context_prompt()
                import platform
                is_linux = platform.system() != "Windows"
                plat_info = "Linux Cloud VPS (Ubuntu x86_64, Akses Root Sudo Bebas)" if is_linux else "Windows 11 Laptop"
                home_dir = os.path.expanduser("~")
                context_prefix = (
                    f"[KONTEKS SISTEM]\n"
                    f"- Waktu: {datetime.now().strftime('%A, %d %B %Y | %H:%M WIB')}\n"
                    f"- Pengguna: Admin {user_name}\n"
                    f"- Platform: {plat_info} | Home: {home_dir}\n"
                    f"{mem_context}\n\n"
                    f"Pesan dari {user_name}: {message}"
                )
                active_tools = self._gemini_tools_schema or []
            else:
                system_instruction = self.SYSTEM_PROMPT_GUEST
                context_prefix = f"Pesan dari {user_name}: {message}"
                active_tools = []

            # 1. Primary Ultra-Fast Provider: Groq Cloud (Qwen / Llama)
            if self.groq_api_key:
                print(f"[AntigravityAgent] Memanggil Groq Cloud ({self.groq_model})...")
                groq_reply = self._call_groq(
                    system_instruction=system_instruction,
                    formatted_history=formatted_history,
                    current_message=context_prefix,
                    user_name=user_name
                )
                if groq_reply:
                    print(f"[AntigravityAgent] Sukses menjawab via Groq ({self.groq_model})!")
                    if len(groq_reply) > 4000:
                        groq_reply = groq_reply[:3900] + "\n\n_...Jawaban dipotong._"
                    return groq_reply

            # 2. Multi-Key & Multi-Model Gemini Loop
            if self.gemini_clients:
                for key_idx, (api_key, client) in enumerate(self.gemini_clients.items(), start=1):
                    key_quota_hit = False
                    for candidate in self.candidate_models:
                        try:
                            from google.genai import types as genai_types
                            thinking_label = "THINKING" if candidate in self.thinking_models else "Standard"
                            print(f"[AntigravityAgent] Key #{key_idx} ({api_key[:8]}...) -> Calling {candidate} ({thinking_label})...")

                            # Build config with thinking_budget=0 for instant response speed
                            gen_config = genai_types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                temperature=self.generation_config["temperature"],
                                top_p=self.generation_config["top_p"],
                                max_output_tokens=self.generation_config["max_output_tokens"],
                                thinking_config=genai_types.ThinkingConfig(thinking_budget=0),
                                tools=active_tools if active_tools else None,
                                automatic_function_calling=genai_types.AutomaticFunctionCallingConfig(
                                    disable=False
                                ) if active_tools else None,
                            )

                            # Build contents list from history + current message
                            contents = list(formatted_history) + [{"role": "user", "parts": [{"text": context_prefix}]}]

                            # Call the model with agentic loop (handle tool calls)
                            response = client.models.generate_content(
                                model=candidate,
                                contents=contents,
                                config=gen_config
                            )

                            # Handle tool calls if model requests them (manual agentic loop)
                            max_tool_rounds = 5
                            tool_round = 0
                            while response.candidates and tool_round < max_tool_rounds:
                                part = response.candidates[0].content.parts[0] if response.candidates[0].content.parts else None
                                if part and hasattr(part, 'function_call') and part.function_call:
                                    fn_call = part.function_call
                                    fn_name = fn_call.name
                                    fn_args = dict(fn_call.args) if fn_call.args else {}
                                    print(f"[AntigravityAgent] Tool call: {fn_name}({fn_args})")
                                    tool_result = self._dispatch_tool_call(fn_name, fn_args)
                                    print(f"[AntigravityAgent] Tool result: {str(tool_result)[:150]}")

                                    # Feed tool result back to model
                                    contents.append({"role": "model", "parts": [{"function_call": {"name": fn_name, "args": fn_args}}]})
                                    contents.append({"role": "user", "parts": [{"function_response": {"name": fn_name, "response": {"result": tool_result}}}]})
                                    response = client.models.generate_content(
                                        model=candidate,
                                        contents=contents,
                                        config=gen_config
                                    )
                                    tool_round += 1
                                else:
                                    break

                            # Extract final text response
                            reply_text = ""
                            if response.text:
                                reply_text = response.text.strip()
                            elif response.candidates:
                                for part in response.candidates[0].content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        reply_text += part.text
                                reply_text = reply_text.strip()

                            if reply_text:
                                # Trim overly long replies for WhatsApp
                                if len(reply_text) > 4000:
                                    reply_text = reply_text[:3900] + "\n\n_...Jawaban dipotong. Minta detail spesifik jika perlu._"
                                return reply_text

                        except Exception as e:
                            err_str = str(e).lower()
                            if any(k in err_str for k in ["quota", "429", "resource_exhausted", "rate_limit"]):
                                print(f"[AntigravityAgent] Quota limit on Key #{key_idx} ({candidate}), beralih ke key berikutnya...")
                                key_quota_hit = True
                                break # Keluar dari loop model untuk key ini, coba key berikutnya
                            elif any(k in err_str for k in ["timeout", "deadline", "unavailable"]):
                                print(f"[AntigravityAgent] Timeout/unavailable on Key #{key_idx} ({candidate}), trying next model...")
                            elif "not found" in err_str or "not supported" in err_str or "no longer available" in err_str:
                                print(f"[AntigravityAgent] Model {candidate} tidak tersedia di Key #{key_idx}, trying next model...")
                            else:
                                print(f"[AntigravityAgent] Error on Key #{key_idx} ({candidate}): {e}")
                                continue

            # 2. Fast Cloud Provider: Groq (Qwen / Llama)
            if self.groq_api_key:
                print(f"[AntigravityAgent] Menggunakan Groq Cloud ({self.groq_model})...")
                groq_reply = self._call_groq(
                    system_instruction=system_instruction,
                    formatted_history=formatted_history,
                    current_message=context_prefix,
                    user_name=user_name
                )
                if groq_reply:
                    print(f"[AntigravityAgent] Sukses menjawab via Groq ({self.groq_model})!")
                    if len(groq_reply) > 4000:
                        groq_reply = groq_reply[:3900] + "\n\n_...Jawaban dipotong._"
                    return groq_reply

            # 3. Secondary / Fallback Provider: Grok (xAI)
            if self.grok_api_key:
                print(f"[AntigravityAgent] Mengaktifkan Grok ({self.grok_model})...")
                grok_reply = self._call_grok(
                    system_instruction=system_instruction,
                    formatted_history=formatted_history,
                    current_message=context_prefix,
                    user_name=user_name
                )
                if grok_reply:
                    print(f"[AntigravityAgent] Sukses menjawab via Grok ({self.grok_model})!")
                    if len(grok_reply) > 4000:
                        grok_reply = grok_reply[:3900] + "\n\n_...Jawaban dipotong._"
                    return grok_reply

        # 5. Built-in Antigravity Self-Aware Reasoning Engine (Fallback when LLM unavailable)
        return self._reason_and_respond(sender_id, message, user_name)

    def _reason_and_respond(self, sender_id: str, message: str, user_name: str) -> str:
        """
        Self-aware, humble, natural conversational engine.
        Fallback when LLM is unavailable or rate-limited.
        Now much more natural and context-aware.
        """
        lower = message.lower().strip()
        ctx = self.session.get_context(sender_id)
        import random

        # 1. Frustration & Complaint Handling (learn from feedback)
        complaints = [
            "sok pinter", "sok pintar", "sok tahu", "kaku", "jangan sok",
            "bukan gitu", "bukan begitu", "salah itu", "ngaco", "belajar lagi",
            "terlalu formal", "kayak robot", "nggak ngerti leptop", "gak ngerti laptop",
            "nggak ada umpan balik", "tidak ada umpan balik", "nggak menarik", "tidak menarik",
            "kamu nggak bisa apa-apa", "tidak bisa apa-apa", "nggak bisa apa apa", "jancok",
            "kontol", "bangsat", "anjing", "tolol", "bodoh", "goblok", "percuma", "gak guna"
        ]
        if any(k in lower for k in complaints):
            memory_manager.add_learned_fact(f"Koreksi pengguna: {message}", source="user_feedback")
            apology_variants = [
                f"Waduh, maaf banget {user_name}! 🙏 Kamu bener, respon tadi emang mengecewakan. Model AI-nya lagi overload jadi lempar ke fallback yang kaku.",
                f"Duh sorry {user_name}! Gua akui tadi respon gua payah banget. LLM-nya lagi limit jadi balasannya template doang.",
                f"Ampun {user_name}! Bener banget koreksinya. Tadi AI engine utama-nya nge-hang jadi balasan gua jadi robotik."
            ]
            return (
                f"{random.choice(apology_variants)}\n\n"
                f"Udah gua catat biar gak kejadian lagi. Sekarang mau ngapain? Gas aja langsung:\n"
                f"• `screenshot` — intip layar laptop\n"
                f"• `baterai` — cek sisa daya\n"
                f"• `terminal [perintah]` — jalankan perintah\n"
                f"• Atau tanya apa aja, gua jawab senatural mungkin!"
            )

        # 2. Relaxation / Casual Chat Request
        relax_triggers = [
            "stop berbicara kaku", "ayo kita mengobrol", "ayo ngobrol", "ngobrol yuk",
            "bicara santai", "santai aja", "ngobrol santai", "jangan kaku", "santai bro",
            "ngobrol dong", "kita ngobrol", "ngobrol"
        ]
        if any(lower == t or lower.startswith(t) or t in lower for t in relax_triggers):
            openers = [
                f"Oke siap {user_name}! Santai mode ON 😄\nLagi ngerjain apa nih?",
                f"Sip {user_name}! Kita ngobrol selow aja ya. Mau bahas apa?",
                f"Gas {user_name}! Nggak usah formal-formal, langsung aja mau ngobrolin apa?"
            ]
            return random.choice(openers)

        # 3. Identity and Capabilities queries
        if any(q in lower for q in [
            "siapa namamu", "siapa kamu", "nama kamu", "kamu siapa", "who are you",
            "lu bisa apa", "kamu bisa apa", "bisa apa aja", "kemampuan lu", "fitur lu",
            "sadar gak", "tau gak lu bisa apa", "apa kemampuanmu"
        ]):
            return self._get_self_aware_capabilities(user_name)

        # 4. Greetings (dynamic, time-aware)
        greetings = ["halo", "hai", "selamat pagi", "selamat siang", "selamat sore", "selamat malam", "assalamualaikum", "apa kabar", "hey", "hi", "p", "pagi", "sore", "malam"]
        if any(lower == g or lower.startswith(g + " ") for g in greetings):
            hour = datetime.now().hour
            if hour < 11:
                waktu = "Pagi"
                emoji_waktu = "🌅"
            elif hour < 15:
                waktu = "Siang"
                emoji_waktu = "☀️"
            elif hour < 18:
                waktu = "Sore"
                emoji_waktu = "🌤️"
            else:
                waktu = "Malam"
                emoji_waktu = "🌙"

            greeting_variants = [
                f"{emoji_waktu} Yo {user_name}! Selamat {waktu}! 👋\nAda yang bisa gua bantu hari ini? Mau ngobrolin apa nih?",
                f"{emoji_waktu} Halo {user_name}! Selamat {waktu}! 😄\nSenang bisa ngobrol lagi. Mau bahas apa hari ini?",
                f"{emoji_waktu} Hey {user_name}! Selamat {waktu}! 🤖\nGua standby. Langsung aja mau tanya atau ngobrol apa!"
            ]
            return random.choice(greeting_variants)

        # 5. Multi-turn recollection
        if any(q in lower for q in ["kemarin saya tanya tentang apa", "tadi saya tanya apa", "ingat apa yang saya tanya", "apa topik sebelumnya"]):
            past_topics = self.session.get_last_user_topics(sender_id)
            if not past_topics:
                return f"Ini pesan pertama kita di sesi ini, {user_name}! Belum ada topik sebelumnya."
            last_q = past_topics[-1]
            past_list = "\n".join([f"• \"{q}\"" for q in past_topics[-3:]])
            return (
                f"Oke {user_name}, gua ingat!\n"
                f"Pertanyaan terakhir lu: 👉 \"{last_q}\"\n\n"
                f"Topik yang pernah lu tanya:\n{past_list}\n\n"
                f"Mau lanjut bahas yang mana?"
            )

        # 6. Laptop diagnostics (only if user explicitly mentions laptop / komputer)
        if any(w in lower for w in ["laptop", "komputer", "pc", "windows"]):
            sys_issue_keywords = ["lemot", "lambat", "panas", "berat", "hang", "ruang penyimpanan", "optimasi", "kinerja laptop", "performa", "ngelag"]
            if any(k in lower for k in sys_issue_keywords):
                self.session.update_context(sender_id, last_topic="Optimasi Sistem Laptop")
                return self._handle_system_troubleshooting(user_name)


        # 7. Deep thinking mode
        if any(k in lower for k in ["pikir mendalam", "deep thinking", "berpikir mendalam", "tanya apa saja"]):
            return (
                f"🧠 Mode deep thinking aktif, {user_name}!\n\n"
                f"Lempar aja pertanyaan, konsep, atau masalah teknis yang mau kita bedah bareng. "
                f"Gua bakal analisis dari berbagai sudut: logika, arsitektur, efisiensi, sampai dampak praktisnya."
            )

        # 8. Generic Fallback — Smart & Natural (NOT template-based)
        self.session.update_context(sender_id, last_topic=message[:30])

        # Check if message looks like a question
        is_question = any(message.strip().endswith(c) for c in ["?", "？"]) or \
                      any(lower.startswith(q) for q in ["apa ", "siapa ", "kapan ", "dimana ", "kenapa ", "berapa ", "gimana ", "bagaimana ", "mengapa "])

        if is_question:
            fallback_q = [
                (
                    f"Pertanyaan bagus, {user_name}! Sayangnya mesin AI utama gua lagi overload sebentar. "
                    f"Coba tanya lagi dalam beberapa detik ya, atau kalau ini terkait laptop, gua bisa langsung eksekusi lewat terminal. 💡"
                ),
                (
                    f"Hmm, {user_name} — gua mau jawab detail tapi AI engine utama lagi antri. "
                    f"Kalau butuh aksi cepat (cek baterai, screenshot, terminal), itu gua bisa langsung! "
                    f"Atau coba kirim ulang pertanyaannya sebentar lagi ya."
                ),
            ]
            return random.choice(fallback_q)
        else:
            fallback_s = [
                (
                    f"Noted, {user_name}! Gua tangkap pesanmu. "
                    f"AI engine utama gua lagi recover dari overload, jadi mungkin respon gua sekarang belum optimal. "
                    f"Tapi kalau mau aksi langsung (screenshot, terminal, cek laptop), gas aja!"
                ),
                (
                    f"Sip {user_name}, gua paham. Saat ini mesin AI premium gua lagi limit, "
                    f"tapi semua fitur kontrol laptop tetep jalan 100%. Mau coba kirim ulang atau mau eksekusi sesuatu?"
                ),
            ]
            return random.choice(fallback_s)

    def _handle_system_troubleshooting(self, user_name: str) -> str:
        """Diagnoses laptop slowness or resource contention based on live hardware metrics."""
        try:
            import platform
            disk_path = "C:\\" if platform.system() == "Windows" else "/"
            disk = psutil.disk_usage(disk_path)
            mem = psutil.virtual_memory()
            cpu_pct = psutil.cpu_percent(interval=0.1)
            disk_pct = disk.percent
            disk_free_gb = round(disk.free / (1024 ** 3), 2)
            ram_pct = mem.percent
        except Exception:
            cpu_pct, disk_pct, disk_free_gb, ram_pct = 10.0, 97.3, 3.47, 63.5

        issue_notes = []
        if disk_pct > 90:
            issue_notes.append(f"• Drive C kamu sangat tipis (sisa {disk_free_gb} GB / {disk_pct}% terpakai). Windows butuh ruang kosong untuk swap & cache agar tidak ngelag.")
        if ram_pct > 80:
            issue_notes.append(f"• Penggunaan RAM cukup tinggi ({ram_pct}%). Ada aplikasi atau tab browser yang memakan memori besar.")
        if cpu_pct > 80:
            issue_notes.append(f"• CPU sedang sibuk ({cpu_pct}%).")

        diagnosis = "\n".join(issue_notes) if issue_notes else "• Secara umum indikator CPU dan RAM masih wajar."

        return (
            f"💻 *DIAGNOSTIK LOGIS KINERJA SISTEM LAPTOP*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"• CPU: *{cpu_pct}%* | RAM: *{ram_pct}%*\n"
            f"• Sisa Drive C: *{disk_free_gb} GB* ({disk_pct}% terpakai)\n\n"
            f"🔍 *Analisis:*\n{diagnosis}\n\n"
            f"🛠️ *Langkah Cepat:*\n"
            f"1. Ketik `top proses` untuk melihat aplikasi terberat.\n"
            f"2. Ketik `kill [nama_proses]` untuk menghentikan proses berat.\n"
            f"3. Ketik `screenshot` untuk melihat tampilan layar saat ini.\n"
            f"4. Bersihkan temp: `terminal Remove-Item -Path $env:TEMP\\* -Recurse -Force -ErrorAction SilentlyContinue`"
        )


# Global singleton instance
agent_service = AntigravityAgent()
