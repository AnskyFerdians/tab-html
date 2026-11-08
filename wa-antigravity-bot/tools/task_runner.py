"""Task Runner Tool for WhatsApp Antigravity Bot.

Executes predefined, authorized background tasks and tools:
- Analisis Saham (saham_reporter)
- NewsFilter (Market News & Sentiment)
- TradingView Analyzer
"""

import os
import subprocess
import shlex
import re
from typing import Dict, Any, Optional

ALLOWED_SCRIPTS: Dict[str, Dict[str, Any]] = {
    "saham": {
        "name": "Analisis Saham & Laporan Keuangan",
        "cmd": ["python", r"C:\Users\HP\saham_reporter\saham_reporter.py"],
        "cwd": r"C:\Users\HP\saham_reporter",
        "description": "Menjalankan analisis fundamental dan laporan keuangan emiten saham."
    },
    "newsfilter": {
        "name": "NewsFilter Pasar Modal & Sentimen",
        "cmd": ["python", r"C:\Users\HP\.gemini\antigravity-ide\scratch\newsfilter\newsfilter.py", "--no-color"],
        "cwd": r"C:\Users\HP\.gemini\antigravity-ide\scratch\newsfilter",
        "description": "Mengambil update berita pasar modal dan sentimen IDX/BEI."
    },
    "tradingview": {
        "name": "TradingView Analyzer",
        "cmd": [r"C:\Users\HP\tradingview_analyzer\.venv\Scripts\python.exe", r"C:\Users\HP\tradingview_analyzer\main.py", "--no-browser"],
        "cwd": r"C:\Users\HP\tradingview_analyzer",
        "description": "Menjalankan pemindaian indikator teknikal TradingView."
    },
    "broker": {
        "name": "IDX Broker Summary & Bandarmology",
        "cmd": [r"C:\Users\HP\tradingview_analyzer\.venv\Scripts\python.exe", r"C:\Users\HP\tradingview_analyzer\broker_terminal.py"],
        "cwd": r"C:\Users\HP\tradingview_analyzer",
        "description": "Menjalankan analisis Broker Summary dan akumulasi/distribusi bandar."
    },
    "bandar": {
        "name": "IDX Bandarmology",
        "cmd": [r"C:\Users\HP\tradingview_analyzer\.venv\Scripts\python.exe", r"C:\Users\HP\tradingview_analyzer\broker_terminal.py"],
        "cwd": r"C:\Users\HP\tradingview_analyzer",
        "description": "Analisis aliran dana bandar dan foreign flow."
    },
    "analisa": {
        "name": "TradingView Analisa Saham",
        "cmd": [r"C:\Users\HP\tradingview_analyzer\.venv\Scripts\python.exe", r"C:\Users\HP\tradingview_analyzer\main.py", "--no-browser"],
        "cwd": r"C:\Users\HP\tradingview_analyzer",
        "description": "Menjalankan batch analisa teknikal TradingView."
    }
}


def sanitize_argument(arg: str) -> str:
    """Sanitizes user input argument to allow only alphanumeric stock tickers/keywords."""
    return re.sub(r"[^a-zA-Z0-9_-]", "", arg.strip())


def run_registered_task(task_key: str, param: Optional[str] = None) -> str:
    """Runs an authorized task and returns its output formatted for WhatsApp."""
    task_key = task_key.lower().strip()
    if task_key not in ALLOWED_SCRIPTS:
        available = ", ".join([f"`{k}`" for k in ALLOWED_SCRIPTS.keys()])
        return (
            f"⚠️ Tugas *'{task_key}'* tidak terdaftar.\n"
            f"Tugas yang tersedia: {available}"
        )

    task_info = ALLOWED_SCRIPTS[task_key]
    clean_param = sanitize_argument(param) if param else ""

    if task_key == "newsfilter":
        cmd = ["python", r"C:\Users\HP\.gemini\antigravity-ide\scratch\newsfilter\newsfilter.py", "--no-color"]
        if clean_param:
            cmd.extend(["--ticker", clean_param])
        else:
            cmd.append("--watchlist")
    elif task_key in ["analisa", "tradingview"]:
        ticker = clean_param if clean_param else "BBCA"
        cmd = [r"C:\Users\HP\tradingview_analyzer\.venv\Scripts\python.exe", r"C:\Users\HP\tradingview_analyzer\main.py", ticker, "--no-browser"]
    elif task_key in ["broker", "bandar"]:
        ticker = clean_param if clean_param else "BBCA"
        cmd = [r"C:\Users\HP\tradingview_analyzer\.venv\Scripts\python.exe", r"C:\Users\HP\tradingview_analyzer\broker_terminal.py", ticker]
    else:
        cmd = list(task_info["cmd"])
        if clean_param:
            cmd.append(clean_param)

    try:
        # Run with safe timeout and capture output
        res = subprocess.run(
            cmd,
            cwd=task_info.get("cwd", None),
            capture_output=True,
            text=True,
            timeout=45,
            encoding="utf-8",
            errors="replace"
        )
        output = (res.stdout or res.stderr or "Tugas selesai tanpa output teks.").strip()
        
        # Check if an HTML report was generated in Downloads/StockReports
        file_attachment = ""
        stock_reports_dir = r"C:\Users\HP\Downloads\StockReports"
        storage_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage")
        if os.path.exists(stock_reports_dir):
            import shutil, glob, time
            now_time = time.time()
            # Look for html files modified in the last 60 seconds
            pattern = os.path.join(stock_reports_dir, f"*{clean_param}*.html") if clean_param else os.path.join(stock_reports_dir, "*.html")
            recent_files = [f for f in glob.glob(pattern) if now_time - os.path.getmtime(f) < 60]
            if recent_files:
                recent_files.sort(key=os.path.getmtime, reverse=True)
                latest_report = recent_files[0]
                dest_name = os.path.basename(latest_report)
                dest_path = os.path.join(storage_dir, dest_name)
                try:
                    shutil.copy2(latest_report, dest_path)
                    file_attachment = f"\n\n[FILE:storage/{dest_name}] 📊 *Laporan Visual HTML*: Berkas laporan interaktif telah dikirim dan siap dibuka di ponsel/browser Anda!"
                except Exception:
                    pass

        # Limit response length for WhatsApp
        if len(output) > 2000:
            output = output[:2000] + "\n\n... _(output dipotong untuk keterbacaan WhatsApp)_"

        return (
            f"✅ *Tugas Selesai*: {task_info['name']}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{output}"
            f"{file_attachment}"
        )
    except subprocess.TimeoutExpired:
        return f"⏱️ *Batas Waktu Terlampaui*: Tugas '{task_info['name']}' membutuhkan waktu lebih dari 90 detik dan telah dihentikan secara aman."
    except Exception as e:
        return f"⚠️ *Gagal Menjalankan Tugas*: {str(e)}"
