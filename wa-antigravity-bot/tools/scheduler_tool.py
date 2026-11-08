"""Scheduler Tool for WhatsApp Antigravity Bot.

Allows scheduling commands and tasks to run at specific times
or after specific delays, managed via WhatsApp.
"""

import os
import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage")
SCHEDULES_FILE = os.path.join(STORAGE_DIR, "scheduled_tasks.json")


class TaskScheduler:
    """Simple in-memory task scheduler with persistence."""

    def __init__(self):
        self.tasks: List[Dict[str, Any]] = []
        self.active_timers: Dict[str, threading.Timer] = {}
        self._load()

    def _load(self):
        if os.path.exists(SCHEDULES_FILE):
            try:
                with open(SCHEDULES_FILE, "r", encoding="utf-8") as f:
                    self.tasks = json.load(f)
            except Exception:
                self.tasks = []

    def _save(self):
        try:
            os.makedirs(os.path.dirname(SCHEDULES_FILE), exist_ok=True)
            with open(SCHEDULES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Scheduler] Save error: {e}")

    def schedule_command(self, command: str, delay_minutes: int, description: str = "") -> str:
        """Schedules a terminal command to run after a delay."""
        from tools.terminal_tool import execute_terminal_command

        task_id = f"task_{datetime.now().strftime('%H%M%S')}_{len(self.tasks) + 1}"
        execute_at = datetime.now() + timedelta(minutes=delay_minutes)

        task_info = {
            "id": task_id,
            "command": command,
            "description": description or command,
            "scheduled_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "execute_at": execute_at.strftime("%d/%m/%Y %H:%M:%S"),
            "delay_minutes": delay_minutes,
            "status": "pending"
        }
        self.tasks.append(task_info)
        self._save()

        # Set timer
        def run_scheduled():
            try:
                result = execute_terminal_command(command)
                task_info["status"] = "completed"
                task_info["result"] = result[:500]
                self._save()
                print(f"[Scheduler] Task {task_id} completed: {command}")
            except Exception as e:
                task_info["status"] = "failed"
                task_info["result"] = str(e)
                self._save()
                print(f"[Scheduler] Task {task_id} failed: {e}")

        timer = threading.Timer(delay_minutes * 60, run_scheduled)
        timer.daemon = True
        timer.start()
        self.active_timers[task_id] = timer

        return (
            f"⏰ *Tugas Berhasil Dijadwalkan!*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 *ID*: `{task_id}`\n"
            f"⌨️ *Perintah*: `{command}`\n"
            f"⏱️ *Jeda*: {delay_minutes} menit\n"
            f"🕐 *Dijadwalkan*: {task_info['scheduled_at']}\n"
            f"📅 *Eksekusi Pada*: {task_info['execute_at']}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 _Ketik `daftar jadwal` untuk melihat semua jadwal aktif._\n"
            f"💡 _Ketik `batalkan jadwal {task_id}` untuk membatalkan._"
        )

    def cancel_task(self, task_id: str) -> str:
        """Cancels a scheduled task by ID."""
        clean_id = task_id.strip()

        # Try to cancel timer
        if clean_id in self.active_timers:
            self.active_timers[clean_id].cancel()
            del self.active_timers[clean_id]

        # Update task status
        for task in self.tasks:
            if task["id"] == clean_id and task["status"] == "pending":
                task["status"] = "cancelled"
                self._save()
                return (
                    f"✅ *Jadwal Berhasil Dibatalkan!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🆔 *ID*: `{clean_id}`\n"
                    f"⌨️ *Perintah*: `{task['command']}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━"
                )

        return f"⚠️ Jadwal dengan ID `{clean_id}` tidak ditemukan atau sudah selesai/dibatalkan."

    def list_tasks(self) -> str:
        """Lists all scheduled tasks."""
        if not self.tasks:
            return (
                "📋 *Tidak ada jadwal tugas.*\n"
                "💡 _Ketik `jadwal [menit] [perintah]` untuk membuat jadwal baru._\n"
                "  _Contoh: `jadwal 30 terminal git pull`_"
            )

        lines = [
            "📋 *DAFTAR JADWAL TUGAS*",
            "━━━━━━━━━━━━━━━━━━━━"
        ]

        # Show last 10 tasks
        for task in self.tasks[-10:]:
            status_icon = {
                "pending": "⏳",
                "completed": "✅",
                "failed": "❌",
                "cancelled": "🚫"
            }.get(task["status"], "❓")

            lines.append(
                f"{status_icon} `{task['id']}` — `{task['command'][:40]}`\n"
                f"   ⏰ Eksekusi: {task['execute_at']} | Status: *{task['status']}*"
            )

        lines.append("━━━━━━━━━━━━━━━━━━━━")
        pending_count = sum(1 for t in self.tasks if t["status"] == "pending")
        lines.append(f"📊 Total pending: *{pending_count}*")
        return "\n".join(lines)

    def schedule_shutdown(self, delay_minutes: int) -> str:
        """Schedules a system shutdown after delay."""
        from tools.power_manager import shutdown_laptop
        return shutdown_laptop(timer_seconds=delay_minutes * 60)


# Global singleton
task_scheduler = TaskScheduler()
