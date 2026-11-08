"""Power Management Tool for WhatsApp Antigravity Bot.

Allows remote power control of the laptop:
- Shutdown (normal / forced)
- Restart
- Sleep / Hibernate
- Lock screen
- Log off current user
- Schedule shutdown with timer
- Cancel scheduled shutdown
"""

import os
import subprocess
import platform
from datetime import datetime


# Safety confirmation phrases that must be included to execute dangerous commands
CONFIRM_PHRASES = ["konfirmasi", "yakin", "lakukan", "ok", "iya", "setuju", "yes"]


def lock_screen() -> str:
    """Locks the laptop screen immediately."""
    if platform.system() != "Windows":
        return "ℹ️ Perintah kunci layar tidak berlaku di Cloud VPS headless (tanpa GUI)."
    try:
        subprocess.Popen(
            ["rundll32.exe", "user32.dll,LockWorkStation"],
            shell=False
        )
        return (
            "🔒 *Layar Laptop Berhasil Dikunci!*\n"
            f"🕐 Waktu: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            "ℹ️ _Pengguna harus memasukkan password/PIN Windows untuk membuka kembali._"
        )
    except Exception as e:
        return f"❌ Gagal mengunci layar: {str(e)}"


def shutdown_laptop(forced: bool = False, timer_seconds: int = 0) -> str:
    """Shuts down the laptop or VPS server. Use forced=True to force-close all apps."""
    try:
        if platform.system() != "Windows":
            return (
                "⚠️ *Perintah Shutdown Ditolak di Server VPS!*\n"
                "ℹ️ _Bot saat ini berjalan di Cloud VPS Linux. Perintah shutdown fisik laptop dimatikan demi keamanan agar server bot tetap online 24 jam._"
            )

        cmd = ["shutdown", "/s"]
        if forced:
            cmd.append("/f")
        cmd.extend(["/t", str(timer_seconds)])

        subprocess.Popen(cmd, shell=False)

        if timer_seconds > 0:
            mins = timer_seconds // 60
            secs = timer_seconds % 60
            return (
                f"⏱️ *Shutdown Dijadwalkan!*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"⏰ Laptop akan mati dalam *{mins} menit {secs} detik*.\n"
                f"💡 Ketik `batalkan shutdown` untuk membatalkan.\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
        else:
            mode = "Paksa (Force)" if forced else "Normal"
            return (
                f"🔴 *Laptop Sedang Dimatikan ({mode})!*\n"
                f"🕐 Waktu: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                f"ℹ️ _Semua aplikasi akan ditutup dan sistem akan shutdown._"
            )
    except Exception as e:
        return f"❌ Gagal shutdown: {str(e)}"


def restart_laptop(forced: bool = False) -> str:
    """Restarts the laptop."""
    try:
        if platform.system() != "Windows":
            return (
                "⚠️ *Perintah Restart Ditolak di Server VPS!*\n"
                "ℹ️ _Bot saat ini berjalan di Cloud VPS Linux. Restart hanya dapat dilakukan oleh admin secara manual via terminal._"
            )

        cmd = ["shutdown", "/r", "/t", "5"]
        if forced:
            cmd.append("/f")

        subprocess.Popen(cmd, shell=False)
        mode = "Paksa (Force)" if forced else "Normal"
        return (
            f"🔄 *Laptop Sedang Direstart ({mode})!*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🕐 Sistem akan restart dalam 5 detik...\n"
            f"ℹ️ _Bot WA akan otomatis aktif kembali setelah Windows dimulai ulang (jika diatur auto-start)._\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
    except Exception as e:
        return f"❌ Gagal restart: {str(e)}"


def sleep_laptop() -> str:
    """Puts the laptop into sleep/standby mode."""
    try:
        subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-Command",
             "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState('Suspend', $false, $false)"],
            shell=False
        )
        return (
            "😴 *Laptop Memasuki Mode Tidur (Sleep)!*\n"
            f"🕐 Waktu: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            "ℹ️ _Tekan tombol power atau buka layar untuk membangunkan laptop._\n"
            "⚠️ _Bot WA tidak bisa merespons selama mode tidur aktif._"
        )
    except Exception as e:
        return f"❌ Gagal sleep: {str(e)}"


def hibernate_laptop() -> str:
    """Puts the laptop into hibernation mode."""
    try:
        subprocess.Popen(["shutdown", "/h"], shell=False)
        return (
            "💤 *Laptop Memasuki Mode Hibernasi!*\n"
            f"🕐 Waktu: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            "ℹ️ _Semua sesi disimpan ke disk. Tekan tombol power untuk membangunkan._"
        )
    except Exception as e:
        return f"❌ Gagal hibernate: {str(e)}"


def cancel_shutdown() -> str:
    """Cancels any scheduled shutdown/restart."""
    try:
        result = subprocess.run(
            ["shutdown", "/a"],
            capture_output=True,
            text=True,
            timeout=5,
            encoding="utf-8",
            errors="replace"
        )
        return (
            "✅ *Shutdown/Restart Berhasil Dibatalkan!*\n"
            f"🕐 Waktu: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            "ℹ️ _Laptop akan tetap menyala._"
        )
    except Exception as e:
        return f"⚠️ Tidak ada shutdown terjadwal untuk dibatalkan, atau gagal: {str(e)}"


def logoff_user() -> str:
    """Logs off the current Windows user session."""
    try:
        subprocess.Popen(["shutdown", "/l"], shell=False)
        return (
            "👋 *Sesi Pengguna Sedang Di-Logoff!*\n"
            f"🕐 Waktu: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            "ℹ️ _Windows akan kembali ke layar login._"
        )
    except Exception as e:
        return f"❌ Gagal logoff: {str(e)}"


def get_uptime_info() -> str:
    """Returns detailed laptop uptime information."""
    try:
        import psutil
        from datetime import timedelta

        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        days = uptime.days
        hours = int((uptime.total_seconds() % 86400) // 3600)
        mins = int((uptime.total_seconds() % 3600) // 60)

        return (
            f"⏱️ *INFORMASI UPTIME LAPTOP*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🖥️ *Boot Terakhir*: {boot_time.strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"⏰ *Uptime*: {days} hari, {hours} jam, {mins} menit\n"
            f"🕐 *Waktu Sekarang*: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
    except Exception as e:
        return f"⚠️ Gagal membaca uptime: {str(e)}"
