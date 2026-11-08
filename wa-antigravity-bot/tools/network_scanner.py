"""Network Scanner Tool for WhatsApp Antigravity Bot.

Provides network diagnostics and scanning capabilities:
- Ping remote hosts
- Traceroute
- DNS lookup
- Port scan (basic)
- Public IP lookup
- Speed test info
"""

import os
import subprocess
import socket
import re
from datetime import datetime


def ping_host(target: str, count: int = 4) -> str:
    """Pings a remote host and returns latency results."""
    clean_target = re.sub(r"[^a-zA-Z0-9.\-:]", "", target.strip())
    if not clean_target:
        return "⚠️ Target ping tidak valid."

    try:
        result = subprocess.run(
            ["ping", "-n", str(min(count, 10)), clean_target],
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace"
        )

        output = result.stdout.strip() or result.stderr.strip() or "Tidak ada output."
        if len(output) > 1500:
            output = output[:1500] + "\n... (dipotong)"

        status = "✅ Berhasil" if result.returncode == 0 else "❌ Gagal / Host Tidak Merespons"

        return (
            f"🏓 *PING KE {clean_target.upper()}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📡 *Status*: {status}\n"
            f"🕐 *Waktu*: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"```\n{output}\n```\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
    except subprocess.TimeoutExpired:
        return f"⏱️ Ping ke {clean_target} timeout (lebih dari 30 detik)."
    except Exception as e:
        return f"❌ Gagal ping: {str(e)}"


def traceroute_host(target: str) -> str:
    """Runs traceroute (tracert) to a target host."""
    clean_target = re.sub(r"[^a-zA-Z0-9.\-:]", "", target.strip())
    if not clean_target:
        return "⚠️ Target traceroute tidak valid."

    try:
        result = subprocess.run(
            ["tracert", "-d", "-h", "15", clean_target],
            capture_output=True,
            text=True,
            timeout=60,
            encoding="utf-8",
            errors="replace"
        )

        output = result.stdout.strip() or result.stderr.strip() or "Tidak ada output."
        if len(output) > 2000:
            output = output[:2000] + "\n... (dipotong)"

        return (
            f"🌐 *TRACEROUTE KE {clean_target.upper()}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"```\n{output}\n```\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
    except subprocess.TimeoutExpired:
        return f"⏱️ Traceroute ke {clean_target} timeout."
    except Exception as e:
        return f"❌ Gagal traceroute: {str(e)}"


def dns_lookup(domain: str) -> str:
    """Performs DNS lookup for a domain name."""
    clean_domain = re.sub(r"[^a-zA-Z0-9.\-]", "", domain.strip())
    if not clean_domain:
        return "⚠️ Domain tidak valid."

    try:
        result = subprocess.run(
            ["nslookup", clean_domain],
            capture_output=True,
            text=True,
            timeout=15,
            encoding="utf-8",
            errors="replace"
        )

        output = result.stdout.strip() or result.stderr.strip() or "Tidak ada output."

        return (
            f"🔍 *DNS LOOKUP: {clean_domain.upper()}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"```\n{output}\n```\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
    except Exception as e:
        return f"❌ Gagal DNS lookup: {str(e)}"


def get_public_ip() -> str:
    """Gets the public IP address of the laptop."""
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command",
             "(Invoke-WebRequest -Uri 'https://api.ipify.org?format=json' -UseBasicParsing).Content"],
            capture_output=True,
            text=True,
            timeout=15,
            encoding="utf-8",
            errors="replace"
        )

        output = result.stdout.strip()
        import json
        try:
            data = json.loads(output)
            public_ip = data.get("ip", "Unknown")
        except Exception:
            public_ip = output or "Tidak dapat dideteksi"

        # Also get local IP
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except Exception:
            local_ip = "127.0.0.1"

        return (
            f"🌍 *INFORMASI IP ADDRESS LAPTOP*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 *IP Publik*: `{public_ip}`\n"
            f"🏠 *IP Lokal*: `{local_ip}`\n"
            f"🏷️ *Hostname*: `{hostname}`\n"
            f"🕐 *Waktu*: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
    except Exception as e:
        return f"❌ Gagal mendapatkan IP publik: {str(e)}"


def scan_open_ports(target: str = "127.0.0.1", ports: str = "80,443,3000,8000,8080,3306,5432") -> str:
    """Scans common ports on a target host."""
    clean_target = re.sub(r"[^a-zA-Z0-9.\-:]", "", target.strip())
    port_list = [int(p.strip()) for p in ports.split(",") if p.strip().isdigit()]

    if not port_list:
        port_list = [80, 443, 3000, 8000, 8080]

    results = []
    for port in port_list[:20]:  # Max 20 ports
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.5)
            conn = s.connect_ex((clean_target, port))
            status = "🟢 OPEN" if conn == 0 else "🔴 CLOSED"
            results.append(f"  Port {port:>5}: {status}")
            s.close()
        except Exception:
            results.append(f"  Port {port:>5}: ⚠️ ERROR")

    port_results = "\n".join(results)
    return (
        f"🔍 *PORT SCAN: {clean_target}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"```\n{port_results}\n```\n"
        f"🕐 Waktu: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
