"""Storage and File Manager Tool for WhatsApp Antigravity Bot.

Allows full control and editing of laptop storage:
- Listing and browsing laptop directories and folders.
- Reading text/code/config files.
- Writing / creating new files.
- Appending / editing existing files.
- Creating new folders (directories).
- Deleting files and folders safely.
- Renaming or moving files and directories.
- Locating and dispatching any laptop files via WhatsApp.
"""

import os
import shutil
from datetime import datetime
from typing import List, Dict, Optional, Tuple

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage")
DEFAULT_BASE_DIR = os.path.expanduser("~")

# Unrestricted access mode: no paths blocked from management
PROTECTED_PATHS = set()


def resolve_laptop_path(path_str: Optional[str]) -> str:
    """Resolves relative or shorthand paths to an absolute normalized Windows path."""
    if not path_str or not path_str.strip():
        return os.path.normpath(DEFAULT_BASE_DIR)

    clean = path_str.strip().strip('"\'`')

    # Handle ~ shortcut
    if clean.startswith("~"):
        clean = os.path.expanduser(clean)

    # Shorthand aliases for common user folders
    lower_clean = clean.lower()
    if lower_clean in ["desktop", "dokumen", "document", "documents", "download", "downloads", "unduhan", "storage"]:
        if lower_clean == "desktop":
            clean = os.path.join(DEFAULT_BASE_DIR, "Desktop")
        elif lower_clean in ["dokumen", "document", "documents"]:
            clean = os.path.join(DEFAULT_BASE_DIR, "Documents")
        elif lower_clean in ["download", "downloads", "unduhan"]:
            clean = os.path.join(DEFAULT_BASE_DIR, "Downloads")
        elif lower_clean == "storage":
            clean = STORAGE_DIR

    # If relative, resolve relative to DEFAULT_BASE_DIR (or current bot dir if in storage)
    if not os.path.isabs(clean):
        # Check if exists in current project first, else in base dir
        bot_relative = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), clean)
        user_relative = os.path.join(DEFAULT_BASE_DIR, clean)
        if os.path.exists(bot_relative):
            clean = bot_relative
        else:
            clean = user_relative

    return os.path.normpath(clean)


def list_laptop_directory(dir_path: Optional[str] = None, max_items: int = 30) -> str:
    """Lists files and folders inside the specified directory on the laptop."""
    target_dir = resolve_laptop_path(dir_path)

    if not os.path.exists(target_dir):
        return f"⚠️ Direktori tidak ditemukan:\n`{target_dir}`"

    if not os.path.isdir(target_dir):
        return f"⚠️ Path ini bukan direktori/folder melainkan berkas:\n`{target_dir}`\n💡 _Gunakan `baca file {target_dir}` untuk membaca isinya._"

    try:
        entries = os.listdir(target_dir)
    except PermissionError:
        return f"🚫 Akses ditolak: Tidak memiliki izin untuk membuka direktori `{target_dir}`."
    except Exception as e:
        return f"⚠️ Gagal membaca direktori `{target_dir}`: {str(e)}"

    folders: List[Dict[str, str]] = []
    files: List[Dict[str, str]] = []

    for name in entries:
        full_path = os.path.join(target_dir, name)
        try:
            is_dir = os.path.isdir(full_path)
            mtime = os.path.getmtime(full_path)
            time_str = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")

            if is_dir:
                folders.append({
                    "name": name,
                    "time": time_str,
                    "mtime": mtime
                })
            else:
                size_bytes = os.path.getsize(full_path)
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{round(size_bytes / 1024, 1)} KB"
                else:
                    size_str = f"{round(size_bytes / (1024 * 1024), 1)} MB"

                files.append({
                    "name": name,
                    "time": time_str,
                    "size": size_str,
                    "mtime": mtime
                })
        except Exception:
            continue

    # Sort alphabetically
    folders.sort(key=lambda x: x["name"].lower())
    files.sort(key=lambda x: x["name"].lower())

    total_folders = len(folders)
    total_files = len(files)

    lines = [
        f"📁 *ISI FOLDER LAPTOP*",
        f"📍 `{target_dir}`",
        f"📊 Total: *{total_folders} folder*, *{total_files} berkas*",
        "━━━━━━━━━━━━━━━━━━━━"
    ]

    shown_count = 0
    # Show subfolders
    for item in folders:
        if shown_count >= max_items:
            break
        lines.append(f"📁 `{item['name']}/`")
        shown_count += 1

    # Show files
    for item in files:
        if shown_count >= max_items:
            break
        lines.append(f"📄 `{item['name']}` ({item['size']})")
        shown_count += 1

    if (total_folders + total_files) > max_items:
        remaining = (total_folders + total_files) - max_items
        lines.append(f"... _dan {remaining} item lainnya._")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 *Perintah cepat:*")
    lines.append("• `baca file [nama_atau_path]` untuk melihat teks")
    lines.append("• `tulis file [path] isi [teks]` untuk membuat/mengedit")
    lines.append("• `kirim file [nama_atau_path]` untuk mengirim fisik via WhatsApp")
    return "\n".join(lines)


def read_laptop_file(file_path: str, max_chars: int = 2500) -> str:
    """Reads the text content of a file on the laptop."""
    target_file = resolve_laptop_path(file_path)

    if not os.path.exists(target_file):
        return f"⚠️ Berkas tidak ditemukan:\n`{target_file}`"

    if os.path.isdir(target_file):
        return f"⚠️ Path ini adalah folder/direktori, bukan berkas:\n`{target_file}`\n💡 _Gunakan `list folder {target_file}`._"

    try:
        size_bytes = os.path.getsize(target_file)
        # Prevent reading huge binary files as text
        if size_bytes > 5 * 1024 * 1024:
            return (
                f"⚠️ Ukuran berkas terlalu besar ({round(size_bytes / (1024*1024), 2)} MB) untuk dibaca sebagai teks.\n"
                f"Gunakan `kirim file {target_file}` untuk mengunduhnya langsung."
            )

        content = None
        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                with open(target_file, "r", encoding=enc) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            return f"⚠️ Berkas `{os.path.basename(target_file)}` berformat biner dan tidak dapat dibaca sebagai teks biasa. Gunakan `kirim file` untuk mengunduhnya."

        total_chars = len(content)
        total_lines = content.count("\n") + 1

        is_truncated = False
        if total_chars > max_chars:
            content = content[:max_chars]
            is_truncated = True

        mtime = os.path.getmtime(target_file)
        time_str = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")

        res_lines = [
            f"📄 *BERKAS:* `{os.path.basename(target_file)}`",
            f"📍 `{target_file}`",
            f"📅 Dimodifikasi: {time_str} | 📏 {total_lines} baris, {total_chars} karakter",
            "━━━━━━━━━━━━━━━━━━━━",
            "```",
            content,
            "```",
            "━━━━━━━━━━━━━━━━━━━━"
        ]

        if is_truncated:
            res_lines.append(f"ℹ️ _Konten dipotong ({max_chars} dari {total_chars} karakter) agar sesuai batas WhatsApp._")

        return "\n".join(res_lines)

    except PermissionError:
        return f"🚫 Akses ditolak: Tidak memiliki izin membaca `{target_file}`."
    except Exception as e:
        return f"⚠️ Gagal membaca berkas `{target_file}`: {str(e)}"


def write_laptop_file(file_path: str, content: str) -> str:
    """Creates or overwrites a file on the laptop storage with the given text content."""
    if not file_path or not file_path.strip():
        return "⚠️ Nama berkas atau path tidak boleh kosong."

    target_file = resolve_laptop_path(file_path)

    # Protect writing directly into system directories
    parent_dir = os.path.dirname(target_file)
    if os.path.normpath(parent_dir).lower() in PROTECTED_PATHS:
        return f"🚫 Tindakan dicegah: Tidak diperbolehkan membuat berkas langsung di folder sistem `{parent_dir}`."

    try:
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)

        size_bytes = os.path.getsize(target_file)
        return (
            f"✅ *Berkas Berhasil Ditulis / Disimpan!*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📄 *Nama Berkas*: `{os.path.basename(target_file)}`\n"
            f"📍 *Lokasi*: `{target_file}`\n"
            f"📦 *Ukuran*: {size_bytes} bytes\n"
            f"✏️ *Isi ({len(content)} karakter)*:\n"
            f"```\n{content[:300]}{'...' if len(content) > 300 else ''}\n```\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 _Ketik `baca file {target_file}` untuk melihat isi penuh atau `kirim file {target_file}` untuk mengunduh._"
        )
    except PermissionError:
        return f"🚫 Akses ditolak saat mencoba menulis ke `{target_file}`."
    except Exception as e:
        return f"⚠️ Gagal menulis berkas `{target_file}`: {str(e)}"


def append_laptop_file(file_path: str, content: str) -> str:
    """Appends new text content to an existing or new file on the laptop."""
    if not file_path or not file_path.strip():
        return "⚠️ Nama berkas atau path tidak boleh kosong."

    target_file = resolve_laptop_path(file_path)

    try:
        parent_dir = os.path.dirname(target_file)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        file_existed = os.path.exists(target_file)

        with open(target_file, "a", encoding="utf-8") as f:
            if file_existed and os.path.getsize(target_file) > 0:
                f.write("\n" + content)
            else:
                f.write(content)

        new_size = os.path.getsize(target_file)
        action_name = "Ditambahkan ke Berkas" if file_existed else "Dibuat (Berkas Baru)"

        return (
            f"✅ *Teks Berhasil {action_name}!*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📄 *Nama Berkas*: `{os.path.basename(target_file)}`\n"
            f"📍 *Lokasi*: `{target_file}`\n"
            f"📦 *Ukuran Sekarang*: {new_size} bytes\n"
            f"➕ *Teks Baru Ditambahkan*:\n"
            f"```\n{content[:250]}{'...' if len(content) > 250 else ''}\n```\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
    except PermissionError:
        return f"🚫 Akses ditolak saat mengedit `{target_file}`."
    except Exception as e:
        return f"⚠️ Gagal mengedit berkas `{target_file}`: {str(e)}"


def create_laptop_folder(folder_path: str) -> str:
    """Creates a new directory/folder on the laptop."""
    if not folder_path or not folder_path.strip():
        return "⚠️ Nama folder atau path tidak boleh kosong."

    target_dir = resolve_laptop_path(folder_path)

    if os.path.exists(target_dir):
        return f"ℹ️ Folder sudah ada sebelumnya di:\n`{target_dir}`"

    try:
        os.makedirs(target_dir, exist_ok=True)
        return (
            f"✅ *Folder Berhasil Dibuat!*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📁 *Folder*: `{os.path.basename(target_dir)}`\n"
            f"📍 *Lokasi*: `{target_dir}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 _Gunakan `list folder {target_dir}` untuk melihat isinya._"
        )
    except PermissionError:
        return f"🚫 Akses ditolak saat membuat folder `{target_dir}`."
    except Exception as e:
        return f"⚠️ Gagal membuat folder `{target_dir}`: {str(e)}"


def delete_laptop_path(target_path: str) -> str:
    """Safely deletes a file or directory from the laptop."""
    if not target_path or not target_path.strip():
        return "⚠️ Path berkas atau folder yang akan dihapus tidak boleh kosong."

    resolved = resolve_laptop_path(target_path)
    norm = os.path.normpath(resolved).lower()

    # Safety checks against system root or user profile root deletion
    if norm in PROTECTED_PATHS or len(norm) <= 3:
        return f"⛔ Tindakan Berbahaya Dicegah: Anda tidak dapat menghapus folder sistem atau folder induk `{resolved}`!"

    if not os.path.exists(resolved):
        return f"⚠️ Berkas atau folder tidak ditemukan:\n`{resolved}`"

    try:
        if os.path.isfile(resolved):
            filename = os.path.basename(resolved)
            os.remove(resolved)
            return (
                f"🗑️ *Berkas Berhasil Dihapus!*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📄 *Nama Berkas*: `{filename}`\n"
                f"📍 *Lokasi Sebelumnya*: `{resolved}`\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
        elif os.path.isdir(resolved):
            dirname = os.path.basename(resolved)
            shutil.rmtree(resolved)
            return (
                f"🗑️ *Folder Berhasil Dihapus!*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📁 *Nama Folder*: `{dirname}`\n"
                f"📍 *Lokasi Sebelumnya*: `{resolved}`\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
        else:
            return f"⚠️ Objek tidak dapat dikenali untuk dihapus: `{resolved}`."
    except PermissionError:
        return f"🚫 Akses ditolak saat menghapus `{resolved}`. Berkas/folder mungkin sedang digunakan oleh aplikasi lain."
    except Exception as e:
        return f"⚠️ Gagal menghapus `{resolved}`: {str(e)}"


def rename_or_move_path(src_path: str, dst_path: str) -> str:
    """Renames or moves a file or folder on the laptop."""
    src = resolve_laptop_path(src_path)

    if not os.path.exists(src):
        return f"⚠️ Berkas/folder sumber tidak ditemukan:\n`{src}`"

    dst = resolve_laptop_path(dst_path)

    try:
        parent_dst = os.path.dirname(dst)
        if parent_dst and not os.path.exists(parent_dst):
            os.makedirs(parent_dst, exist_ok=True)

        shutil.move(src, dst)
        return (
            f"🔄 *Berhasil Mengganti Nama / Memindahkan!*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 *Dari*: `{src}`\n"
            f"👉 *Ke*: `{dst}`\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
    except PermissionError:
        return f"🚫 Akses ditolak saat memindahkan/mengganti nama `{src}`."
    except Exception as e:
        return f"⚠️ Gagal memindahkan/mengganti nama: {str(e)}"


def list_recent_files(limit: int = 8) -> str:
    """Lists recent documents and reports stored in the storage directory."""
    if not os.path.exists(STORAGE_DIR):
        return "📁 Direktori penyimpanan dokumen kosong."

    files: List[Dict[str, str]] = []
    for f in os.listdir(STORAGE_DIR):
        # Exclude internal session / config json files
        if f.endswith((".docx", ".pdf", ".txt", ".xlsx", ".csv")):
            full_path = os.path.join(STORAGE_DIR, f)
            mtime = os.path.getmtime(full_path)
            size_kb = round(os.path.getsize(full_path) / 1024, 1)
            files.append({
                "filename": f,
                "time": datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M"),
                "size": f"{size_kb} KB",
                "mtime": mtime
            })

    if not files:
        return "📁 Belum ada dokumen atau berkas laporan yang dibuat."

    # Sort descending by last modified
    files.sort(key=lambda x: x["mtime"], reverse=True)
    top_files = files[:limit]

    lines = [
        "📂 *DAFTAR BERKAS TERAKHIR*",
        "━━━━━━━━━━━━━━━━━━━━"
    ]
    for idx, item in enumerate(top_files, 1):
        lines.append(f"{idx}. 📄 `{item['filename']}`\n   └ 📅 {item['time']} | 📦 {item['size']}")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 _Ketik 'Kirim file [nama_file]' untuk mengunduh berkas fisik via WhatsApp._")
    return "\n".join(lines)


def get_file_for_dispatch(filename_query: str) -> Optional[str]:
    """
    Finds a matching file in laptop storage or storage directory,
    and formats token [FILE:path] for WhatsApp dispatch.
    """
    query = filename_query.strip().strip('"\'`')
    if not query:
        return None

    # 1. Direct path check (absolute or relative)
    resolved = resolve_laptop_path(query)
    if os.path.isfile(resolved):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        try:
            rel_path = os.path.relpath(resolved, base_dir).replace("\\", "/")
        except ValueError:
            rel_path = resolved.replace("\\", "/")
        return f"[FILE:{rel_path}] Berkas *{os.path.basename(resolved)}* ditemukan dan siap dikirimkan ke WhatsApp Anda."

    # 2. Check in bot STORAGE_DIR
    if os.path.exists(STORAGE_DIR):
        query_lower = query.lower()
        for f in os.listdir(STORAGE_DIR):
            if query_lower in f.lower():
                full_path = os.path.join(STORAGE_DIR, f)
                if os.path.isfile(full_path):
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    rel_path = os.path.relpath(full_path, base_dir).replace("\\", "/")
                    return f"[FILE:{rel_path}] Berkas *{f}* ditemukan dan siap dikirimkan ke WhatsApp Anda."

    # 3. Check common laptop user directories
    search_dirs = [
        DEFAULT_BASE_DIR,
        os.path.join(DEFAULT_BASE_DIR, "Desktop"),
        os.path.join(DEFAULT_BASE_DIR, "Documents"),
        os.path.join(DEFAULT_BASE_DIR, "Downloads")
    ]
    query_lower = query.lower()
    for sdir in search_dirs:
        if os.path.isdir(sdir):
            try:
                for f in os.listdir(sdir):
                    if query_lower in f.lower():
                        full_path = os.path.join(sdir, f)
                        if os.path.isfile(full_path):
                            clean_disp = full_path.replace("\\", "/")
                            return f"[FILE:{clean_disp}] Berkas *{f}* ditemukan dan siap dikirimkan ke WhatsApp Anda."
            except Exception:
                continue

    return None


def get_storage_help() -> str:
    """Returns guide for laptop storage management and file editing features."""
    return (
        "💾 *PANDUAN LENGKAP PENGELOLAAN & EDIT PENYIMPANAN LAPTOP*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Anda dapat mengontrol, membaca, dan mengedit penyimpanan laptop langsung dari WhatsApp:\n\n"
        "📁 *1. Jelajah Folder (List Folder)*\n"
        "• `list folder` / `lihat folder`\n"
        "  _Melihat isi folder utama pengguna (`C:\\Users\\HP`)._\n"
        "• `list folder [path]` (contoh: `list folder Desktop` atau `list folder C:\\Users\\HP\\Documents`)\n\n"
        "📖 *2. Membaca Berkas (Read File)*\n"
        "• `baca file [path/nama]` (contoh: `baca file catatan.txt` atau `baca file C:\\Users\\HP\\wa.bat`)\n\n"
        "✍️ *3. Menulis & Membuat Berkas Baru (Write/Create)*\n"
        "• `tulis file [path] isi [teks]`\n"
        "  _Contoh_: `tulis file catatan.txt isi Belanja: Beras, Telur, Minyak`\n\n"
        "➕ *4. Mengedit / Menambah Isi Berkas (Append)*\n"
        "• `tambah file [path] isi [teks]` atau `edit file [path] isi [teks]`\n"
        "  _Contoh_: `tambah file catatan.txt isi - Catatan tambahan sore hari`\n\n"
        "📂 *5. Membuat Folder Baru (Make Directory)*\n"
        "• `buat folder [path]` (contoh: `buat folder backup_data` atau `buat folder C:\\Users\\HP\\projek`)\n\n"
        "🗑️ *6. Menghapus Berkas atau Folder (Delete)*\n"
        "• `hapus file [path]` (contoh: `hapus file catatan.txt`)\n"
        "• `hapus folder [path]` (contoh: `hapus folder backup_data`)\n\n"
        "🔄 *7. Mengganti Nama / Memindahkan (Rename/Move)*\n"
        "• `ganti nama [lama] ke [baru]`\n"
        "  _Contoh_: `ganti nama lama.txt ke baru.txt`\n\n"
        "📥 *8. Mengunduh Berkas Fisik ke WhatsApp*\n"
        "• `kirim file [nama/path]`\n"
        "  _Contoh_: `kirim file catatan.txt` atau `kirim file C:\\Users\\HP\\laporan.pdf`\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )


def clean_stale_storage(max_age_hours: int = 48) -> int:
    """Deletes temporary generated files in storage older than max_age_hours."""
    if not os.path.exists(STORAGE_DIR):
        return 0
    now = datetime.now().timestamp()
    max_age_secs = max_age_hours * 3600
    cleaned = 0
    preserve = {"verified_users.json", "sessions.json", "experience_memory.json", "dynamic_script.py"}
    try:
        for fname in os.listdir(STORAGE_DIR):
            if fname in preserve or fname.startswith("."):
                continue
            fpath = os.path.join(STORAGE_DIR, fname)
            if os.path.isfile(fpath):
                mtime = os.path.getmtime(fpath)
                if (now - mtime) > max_age_secs:
                    try:
                        os.remove(fpath)
                        cleaned += 1
                    except Exception:
                        pass
    except Exception as e:
        print(f"[StorageCleaner] Warning cleaning storage: {e}")
    return cleaned

