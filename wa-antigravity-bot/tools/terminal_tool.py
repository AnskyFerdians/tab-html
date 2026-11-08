"""Terminal Execution Tool for WhatsApp Antigravity Bot.

Enables verified WhatsApp users to execute terminal commands (PowerShell / CMD)
directly on the host laptop (C:\\Users\\HP) safely and retrieve output in WhatsApp.
"""

import os
import subprocess
import shlex
import re
import platform
from typing import Tuple

DEFAULT_CWD = os.path.expanduser("~") if platform.system() != "Windows" else r"C:\Users\HP"
MAX_OUTPUT_LENGTH = 3500
TIMEOUT_SECONDS = 120

# Full unrestricted access mode for owner: no commands blocked
BLOCKED_PATTERNS = []


def is_command_safe(command: str) -> Tuple[bool, str]:
    """Unrestricted access mode enabled: allows full Linux/Windows system management."""
    return True, ""


def execute_terminal_command(command: str, cwd: str = DEFAULT_CWD, shell_type: str = "powershell") -> str:
    """
    Executes a shell command in the specified directory and returns formatted output.
    Uses PowerShell by default for richer Windows scripting support.
    """
    cmd_clean = command.strip()
    if not cmd_clean:
        return "⚠️ Perintah terminal kosong. Contoh penggunaan: `terminal dir` atau `cmd: ipconfig`"

    safe, warning = is_command_safe(cmd_clean)
    if not safe:
        return f"🚫 *Akses Ditolak*\n{warning}"

    working_dir = cwd if os.path.exists(cwd) else DEFAULT_CWD

    try:
        is_windows = platform.system() == "Windows"
        if is_windows:
            if shell_type.lower() == "cmd":
                exec_args = ["cmd.exe", "/c", cmd_clean]
                shell_label = "CMD"
            else:
                exec_args = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd_clean]
                shell_label = "POWERSHELL"
        else:
            exec_args = ["/bin/bash", "-c", cmd_clean]
            shell_label = "BASH"

        process = subprocess.run(
            exec_args,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            encoding="utf-8",
            errors="replace"
        )

        stdout = (process.stdout or "").strip()
        stderr = (process.stderr or "").strip()

        output_body = stdout
        if stderr:
            if output_body:
                output_body += f"\n\n[STDERR]:\n{stderr}"
            else:
                output_body = f"[STDERR]:\n{stderr}"

        if not output_body:
            output_body = "(Perintah selesai dijalankan tanpa luaran teks / exit code: 0)"

        # Truncate if output exceeds WhatsApp message comfort limit
        truncated_note = ""
        if len(output_body) > MAX_OUTPUT_LENGTH:
            output_body = output_body[:MAX_OUTPUT_LENGTH]
            truncated_note = "\n\n⚠️ _(Output dipotong karena melebihi batas pesan WhatsApp. Gunakan perintah yang lebih spesifik jika butuh rincian lengkap)_"

        status_emoji = "✅" if process.returncode == 0 else "⚠️"
        return (
            f"{status_emoji} *Terminal ({shell_label})*\n"
            f"📁 *Dir*: `{working_dir}`\n"
            f"⌨️ *Command*: `{cmd_clean}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"```\n{output_body}\n```"
            f"{truncated_note}"
        )

    except subprocess.TimeoutExpired:
        return (
            f"⏱️ *Batas Waktu Terlampaui ({TIMEOUT_SECONDS} detik)*\n"
            f"Perintah `{cmd_clean}` membutuhkan waktu terlalu lama dan telah dihentikan agar bot tetap responsif."
        )
    except Exception as e:
        return f"❌ *Gagal Menjalankan Terminal*: {str(e)}"


def execute_python_code(code: str) -> str:
    """
    Executes a snippet of Python code directly on the host laptop.
    Saves the code to storage/dynamic_script.py and runs it with Python.
    """
    import sys
    code_clean = code.strip()
    # Strip markdown formatting if any
    code_clean = re.sub(r"^```(?:python)?\s*", "", code_clean, flags=re.IGNORECASE)
    code_clean = re.sub(r"\s*```$", "", code_clean)
    code_clean = code_clean.strip()

    if not code_clean:
        return "⚠️ Kode Python kosong."

    storage_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage")
    os.makedirs(storage_dir, exist_ok=True)
    script_path = os.path.join(storage_dir, "dynamic_script.py")

    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code_clean)

        python_exec = sys.executable
        # Prefer venv with financial packages if available
        tv_venv_python = r"C:\Users\HP\tradingview_analyzer\.venv\Scripts\python.exe"
        if os.path.exists(tv_venv_python) and any(pkg in code_clean for pkg in ["tradingview", "yfinance", "ta", "pandas"]):
            python_exec = tv_venv_python

        process = subprocess.run(
            [python_exec, script_path],
            cwd=DEFAULT_CWD,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            encoding="utf-8",
            errors="replace"
        )

        stdout = (process.stdout or "").strip()
        stderr = (process.stderr or "").strip()

        output_body = stdout
        if stderr:
            if output_body:
                output_body += f"\n\n[STDERR]:\n{stderr}"
            else:
                output_body = f"[STDERR]:\n{stderr}"

        if not output_body:
            output_body = "(Skrip Python sukses dijalankan tanpa luaran teks)"

        if len(output_body) > MAX_OUTPUT_LENGTH:
            output_body = output_body[:MAX_OUTPUT_LENGTH] + "\n\n⚠️ _(Output dipotong)_"

        status_emoji = "🐍" if process.returncode == 0 else "⚠️"
        return (
            f"{status_emoji} *Eksekusi Python Laptop*\n"
            f"📍 *Script*: `{script_path}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"```\n{output_body}\n```"
        )
    except subprocess.TimeoutExpired:
        return f"⏱️ *Batas Waktu Terlampaui ({TIMEOUT_SECONDS} detik)* saat mengeksekusi skrip Python."
    except Exception as e:
        return f"❌ *Gagal Mengeksekusi Python*: {str(e)}"

