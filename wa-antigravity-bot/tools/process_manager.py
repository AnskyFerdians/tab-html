"""Process Manager Tool for WhatsApp Antigravity Bot.

Provides remote process management capabilities:
- Kill processes by name or PID
- List processes by CPU/RAM usage
- Find processes by name
- Start applications
"""

import os
import subprocess
import re
import psutil
from datetime import datetime
from typing import Optional


# Applications that should NEVER be killed remotely
PROTECTED_PROCESSES = {
    "system", "system idle process", "csrss.exe", "smss.exe", "wininit.exe",
    "services.exe", "lsass.exe", "winlogon.exe", "svchost.exe", "explorer.exe",
    "dwm.exe", "taskhostw.exe", "runtimebroker.exe", "sihost.exe"
}

# Common application launch commands
APP_LAUNCHER = {
    "notepad": {"cmd": "notepad.exe", "name": "Notepad"},
    "calculator": {"cmd": "calc.exe", "name": "Calculator"},
    "kalkulator": {"cmd": "calc.exe", "name": "Calculator"},
    "paint": {"cmd": "mspaint.exe", "name": "Paint"},
    "cmd": {"cmd": "cmd.exe", "name": "Command Prompt"},
    "powershell": {"cmd": "powershell.exe", "name": "PowerShell"},
    "explorer": {"cmd": "explorer.exe", "name": "File Explorer"},
    "task manager": {"cmd": "taskmgr.exe", "name": "Task Manager"},
    "control panel": {"cmd": "control.exe", "name": "Control Panel"},
    "settings": {"cmd": "ms-settings:", "name": "Windows Settings", "use_start": True},
    "chrome": {"cmd": "chrome.exe", "name": "Google Chrome"},
    "firefox": {"cmd": "firefox.exe", "name": "Mozilla Firefox"},
    "edge": {"cmd": "msedge.exe", "name": "Microsoft Edge"},
    "vscode": {"cmd": "code", "name": "Visual Studio Code"},
    "word": {"cmd": "winword.exe", "name": "Microsoft Word"},
    "excel": {"cmd": "excel.exe", "name": "Microsoft Excel"},
    "spotify": {"cmd": r"C:\Users\HP\AppData\Roaming\Spotify\Spotify.exe", "name": "Spotify"},
    "whatsapp": {"cmd": "msedge.exe", "name": "WhatsApp Web", "args": ["https://web.whatsapp.com"]},
    "whatsapp web": {"cmd": "msedge.exe", "name": "WhatsApp Web", "args": ["https://web.whatsapp.com"]},
    "youtube": {"cmd": "msedge.exe", "name": "YouTube", "args": ["https://youtube.com"]},
}


def kill_process(target: str) -> str:
    """Kills a process by name or PID."""
    clean_target = target.strip()
    if not clean_target:
        return "⚠️ Nama proses atau PID tidak boleh kosong."

    # Check if target is PID
    if clean_target.isdigit():
        pid = int(clean_target)
        try:
            proc = psutil.Process(pid)
            proc_name = proc.name()
            if proc_name.lower() in PROTECTED_PROCESSES:
                return f"🛡️ *Akses Ditolak*: Proses `{proc_name}` (PID: {pid}) adalah proses sistem kritis dan tidak boleh dihentikan."

            proc.terminate()
            return (
                f"✅ *Proses Berhasil Dihentikan!*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📛 *Nama*: `{proc_name}`\n"
                f"🔢 *PID*: {pid}\n"
                f"🕐 *Waktu*: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
        except psutil.NoSuchProcess:
            return f"⚠️ Proses dengan PID {pid} tidak ditemukan."
        except psutil.AccessDenied:
            return f"🚫 Akses ditolak untuk menghentikan PID {pid}."
        except Exception as e:
            return f"❌ Gagal menghentikan PID {pid}: {str(e)}"
    else:
        # Kill by name
        proc_name = clean_target.lower()
        if not proc_name.endswith(".exe"):
            proc_name += ".exe"

        if proc_name.lower() in PROTECTED_PROCESSES:
            return f"🛡️ *Akses Ditolak*: `{proc_name}` adalah proses sistem kritis dan tidak boleh dihentikan."

        killed = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == proc_name:
                    proc.terminate()
                    killed.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if killed:
            pid_list = ", ".join([str(p) for p in killed])
            return (
                f"✅ *Proses `{clean_target}` Berhasil Dihentikan!*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🔢 *PID Dihentikan*: {pid_list}\n"
                f"📊 *Total*: {len(killed)} proses\n"
                f"🕐 *Waktu*: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
        else:
            return f"⚠️ Proses `{clean_target}` tidak ditemukan atau sudah tidak berjalan."


def find_process(query: str) -> str:
    """Finds running processes matching a name query."""
    clean_query = query.strip().lower()
    if not clean_query:
        return "⚠️ Kata kunci pencarian proses tidak boleh kosong."

    matches = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
        try:
            if clean_query in proc.info['name'].lower():
                matches.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'mem': round(proc.info.get('memory_percent', 0) or 0, 1),
                    'cpu': round(proc.info.get('cpu_percent', 0) or 0, 1)
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not matches:
        return f"🔍 Tidak ditemukan proses yang cocok dengan *\"{query}\"*."

    matches.sort(key=lambda x: x['mem'], reverse=True)
    top = matches[:15]

    lines = [
        f"🔍 *PROSES COCOK: \"{query.upper()}\"*",
        f"📊 Ditemukan: *{len(matches)} proses*",
        "━━━━━━━━━━━━━━━━━━━━"
    ]
    for p in top:
        lines.append(f"• `{p['name']}` (PID: {p['pid']}) — RAM: {p['mem']}%")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 _Ketik `kill [nama/PID]` untuk menghentikan proses._")
    return "\n".join(lines)


def launch_app(app_name: str, url_or_path: str = "") -> str:
    """Launches an application on the laptop."""
    clean_name = app_name.strip().lower()

    if clean_name in APP_LAUNCHER:
        app_info = APP_LAUNCHER[clean_name]
        try:
            if app_info.get("use_start"):
                os.startfile(app_info["cmd"])
            else:
                cmd = [app_info["cmd"]]
                if "args" in app_info:
                    cmd.extend(app_info["args"])
                if url_or_path:
                    cmd.append(url_or_path)
                subprocess.Popen(cmd, shell=False)

            return (
                f"🚀 *Aplikasi Berhasil Dibuka!*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📱 *Aplikasi*: {app_info['name']}\n"
                f"🕐 *Waktu*: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
        except Exception as e:
            return f"❌ Gagal membuka {app_info['name']}: {str(e)}"
    else:
        # Try to open directly
        try:
            if url_or_path:
                subprocess.Popen([clean_name, url_or_path], shell=False)
            else:
                subprocess.Popen([clean_name], shell=False)
            return f"🚀 Mencoba membuka `{clean_name}`..."
        except FileNotFoundError:
            available = ", ".join([f"`{k}`" for k in APP_LAUNCHER.keys()])
            return (
                f"⚠️ Aplikasi `{app_name}` tidak ditemukan.\n"
                f"📋 *Aplikasi tersedia*: {available}"
            )
        except Exception as e:
            return f"❌ Gagal membuka `{app_name}`: {str(e)}"


def get_app_list() -> str:
    """Returns list of launchable applications."""
    lines = [
        "🚀 *DAFTAR APLIKASI YANG BISA DIBUKA*",
        "━━━━━━━━━━━━━━━━━━━━"
    ]
    for key, info in APP_LAUNCHER.items():
        lines.append(f"• `{key}` → {info['name']}")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 _Ketik `buka [nama_app]` untuk membuka aplikasi._")
    lines.append("💡 _Ketik `buka chrome https://google.com` untuk buka browser dengan URL._")
    return "\n".join(lines)
