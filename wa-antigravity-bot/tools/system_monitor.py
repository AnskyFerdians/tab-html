"""System Monitor Tool for WhatsApp Antigravity Bot.

Provides real-time hardware, resource, and operating system metrics:
- CPU, Memory (RAM), Disk usage
- Battery level & power status
- System uptime & active processes
"""

import os
import socket
import platform
from datetime import datetime, timedelta
import psutil


def get_system_status() -> str:
    """Returns a rich, formatted WhatsApp markdown report of the laptop's health."""
    try:
        # 1. CPU
        cpu_pct = psutil.cpu_percent(interval=0.5)
        cpu_count = psutil.cpu_count(logical=True)

        # 2. Memory / RAM
        mem = psutil.virtual_memory()
        ram_total = round(mem.total / (1024 ** 3), 2)
        ram_used = round(mem.used / (1024 ** 3), 2)
        ram_free = round(mem.available / (1024 ** 3), 2)
        ram_pct = mem.percent

        # 3. Disk Usage
        disk_path = "C:\\" if platform.system() == "Windows" else "/"
        disk = psutil.disk_usage(disk_path)
        disk_total = round(disk.total / (1024 ** 3), 2)
        disk_free = round(disk.free / (1024 ** 3), 2)
        disk_pct = disk.percent

        # 4. Battery
        battery = psutil.sensors_battery()
        if battery:
            bat_pct = battery.percent
            is_plugged = "🔌 Tersambung Charger (Charging)" if battery.power_plugged else "🔋 Menggunakan Baterai"
            bat_status = f"{bat_pct}% ({is_plugged})"
        else:
            bat_status = "Online / Cloud VPS (Tanpa Baterai Fisik)"

        # 5. Uptime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        uptime_hours = int(uptime.total_seconds() // 3600)
        uptime_mins = int((uptime.total_seconds() % 3600) // 60)

        # 6. Host & IP
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except Exception:
            local_ip = "127.0.0.1"

        # 7. Proactive Health Insights
        warnings = []
        if disk_pct >= 90:
            warnings.append(f"⚠️ *Peringatan Kapasitas*: Drive C terpakai {disk_pct}% (tersisa {disk_free} GB). Disarankan membersihkan cache atau memindahkan berkas besar.")
        if ram_pct >= 85:
            warnings.append(f"⚠️ *Beban Memori Tinggi*: RAM terpakai {ram_pct}%. Ketik `top proses` untuk melihat aplikasi terberat.")

        warn_block = ""
        if warnings:
            warn_block = "\n" + "\n".join(warnings) + "\n"

        report = (
            f"💻 *STATUS KESEHATAN LAPTOP*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏷️ *Perangkat*: `{hostname}` ({platform.system()} {platform.release()})\n"
            f"⏱️ *Uptime*: {uptime_hours} jam {uptime_mins} menit\n"
            f"🌐 *IP Lokal*: `{local_ip}`\n\n"
            f"⚡ *CPU*: {cpu_pct}% ({cpu_count} Cores)\n"
            f"🧠 *RAM*: {ram_pct}% (Terpakai: {ram_used} GB / {ram_total} GB | Sisa: {ram_free} GB)\n"
            f"💾 *Drive C*: {disk_pct}% (Sisa: {disk_free} GB / {disk_total} GB)\n"
            f"🔋 *Baterai*: {bat_status}\n"
            f"━━━━━━━━━━━━━━━━━━━━{warn_block}\n"
            f"ℹ️ _Status diperbarui secara real-time._"
        )
        return report
    except Exception as e:
        return f"⚠️ Gagal membaca status sistem: {str(e)}"


def get_battery_status() -> str:
    """Returns focused battery level and charging metrics."""
    try:
        battery = psutil.sensors_battery()
        if not battery:
            return "🔋 Perangkat terdeteksi sebagai PC Desktop atau driver baterai tidak tersedia."

        pct = battery.percent
        plugged = battery.power_plugged
        secs_left = battery.secsleft

        if plugged:
            status_text = "🔌 Tersambung Charger (Mengisi Daya)"
        else:
            status_text = "🔋 Menggunakan Baterai (Tidak Tercolok Charger)"

        time_info = ""
        if 0 < secs_left < 86400 and not plugged:
            hours = secs_left // 3600
            mins = (secs_left % 3600) // 60
            time_info = f"\n⏱️ *Estimasi Sisa Waktu*: ±{hours} jam {mins} menit"

        icon = "🟢" if pct > 50 else ("🟡" if pct > 20 else "🔴")

        return (
            f"🔋 *STATUS DAYA & BATERAI LAPTOP*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{icon} *Persentase*: *{pct}%*\n"
            f"⚡ *Status Sumber Daya*: {status_text}{time_info}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
    except Exception as e:
        return f"⚠️ Gagal membaca status baterai: {str(e)}"


def get_wifi_network_status() -> str:
    """Queries Windows netsh command to get real-time Wi-Fi SSID, signal, and connection details."""
    import subprocess
    import re

    try:
        res = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8",
            errors="replace"
        )
        out = res.stdout

        ssid_match = re.search(r"SSID\s*:\s*(.+)", out)
        state_match = re.search(r"State\s*:\s*(.+)", out)
        signal_match = re.search(r"Signal\s*:\s*(.+)", out)
        adapter_match = re.search(r"Description\s*:\s*(.+)", out)
        band_match = re.search(r"Band\s*:\s*(.+)", out)

        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except Exception:
            local_ip = "127.0.0.1"

        if ssid_match and state_match:
            ssid = ssid_match.group(1).strip()
            state = state_match.group(1).strip()
            signal = signal_match.group(1).strip() if signal_match else "Tidak diketahui"
            adapter = adapter_match.group(1).strip() if adapter_match else "Wi-Fi Adapter"
            band = band_match.group(1).strip() if band_match else "Standar"

            is_connected = "connected" in state.lower() or "terhubung" in state.lower()
            status_icon = "🟢" if is_connected else "🔴"
            status_desc = "Terhubung (Online)" if is_connected else "Terputus"

            return (
                f"📶 *STATUS KONEKSI WI-FI & JARINGAN*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"{status_icon} *Status*: {status_desc}\n"
                f"📡 *Nama Wi-Fi (SSID)*: `{ssid}`\n"
                f"📶 *Kekuatan Sinyal*: {signal}\n"
                f"🌐 *IP Lokal*: `{local_ip}`\n"
                f"📻 *Frekuensi Band*: {band}\n"
                f"🏷️ *Perangkat Adapter*: {adapter}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"ℹ️ _Koneksi jaringan laptop berjalan normal._"
            )
        else:
            return (
                f"📶 *STATUS JARINGAN LAPTOP*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🌐 *IP Lokal*: `{local_ip}`\n"
                f"ℹ️ Wi-Fi tidak terhubung atau laptop menggunakan koneksi Ethernet kabel LAN."
            )
    except Exception as e:
        return f"⚠️ Gagal memeriksa koneksi Wi-Fi: {str(e)}"


def get_top_processes(limit: int = 5) -> str:
    """Returns top active processes by memory consumption."""
    try:
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
            try:
                info = p.info
                if info['memory_percent'] is not None:
                    procs.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Sort by memory percent descending
        procs.sort(key=lambda x: x['memory_percent'] or 0, reverse=True)
        top = procs[:limit]

        lines = [
            f"📊 *TOP {limit} PROSES TERBESAR (RAM)*",
            "━━━━━━━━━━━━━━━━━━━━"
        ]
        for idx, proc in enumerate(top, 1):
            name = proc.get('name', 'Unknown')
            mem_p = round(proc.get('memory_percent') or 0, 1)
            lines.append(f"{idx}. `{name}` — RAM: *{mem_p}%* (PID: {proc.get('pid')})")

        lines.append("━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)
    except Exception as e:
        return f"⚠️ Gagal membaca daftar proses: {str(e)}"
