"""Screenshot Tool for WhatsApp Antigravity Bot.

Captures the laptop screen remotely and returns the image path
for dispatch via WhatsApp. Supports full screen and active window capture.
"""

import os
import subprocess
from datetime import datetime

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage")


def capture_screenshot(mode: str = "full") -> str:
    """
    Captures a screenshot of the laptop screen.
    
    Args:
        mode: 'full' for entire screen, 'active' for active window only.
    
    Returns:
        Formatted response with [FILE:path] token for WhatsApp dispatch.
    """
    os.makedirs(STORAGE_DIR, exist_ok=True)
    import platform
    if platform.system() != "Windows":
        return (
            "ℹ️ *Fitur Screenshot Layar Fisik Tidak Tersedia*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Bot saat ini beroperasi di lingkungan *Headless Linux Cloud VPS* (tanpa layar grafis/monitor fisik).\n"
            "Gunakan perintah `status laptop` atau `terminal [command]` untuk memantau server."
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{mode}_{timestamp}.png"
    filepath = os.path.join(STORAGE_DIR, filename)

    try:
        # Use PowerShell to capture screen via .NET
        if mode == "active":
            # Capture active window
            ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$hwnd = (Get-Process | Where-Object {{$_.MainWindowHandle -ne 0}} | Sort-Object -Property CPU -Descending | Select-Object -First 1).MainWindowHandle

Add-Type @'
using System;
using System.Runtime.InteropServices;
public class Win32 {{
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT {{
        public int Left, Top, Right, Bottom;
    }}
}}
'@

$fgHwnd = [Win32]::GetForegroundWindow()
$rect = New-Object Win32+RECT
[Win32]::GetWindowRect($fgHwnd, [ref]$rect) | Out-Null
$width = $rect.Right - $rect.Left
$height = $rect.Bottom - $rect.Top
if ($width -le 0) {{ $width = 800 }}
if ($height -le 0) {{ $height = 600 }}

$bitmap = New-Object System.Drawing.Bitmap($width, $height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, (New-Object System.Drawing.Size($width, $height)))
$bitmap.Save('{filepath}')
$graphics.Dispose()
$bitmap.Dispose()
"""
        else:
            # Full screen capture
            ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
$bitmap.Save('{filepath}')
$graphics.Dispose()
$bitmap.Dispose()
"""

        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=15,
            encoding="utf-8",
            errors="replace"
        )

        if os.path.exists(filepath):
            size_kb = round(os.path.getsize(filepath) / 1024, 1)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            rel_path = os.path.relpath(filepath, base_dir).replace("\\", "/")
            mode_label = "Layar Penuh" if mode == "full" else "Jendela Aktif"
            return (
                f"[FILE:{rel_path}] 📸 *Screenshot {mode_label} Berhasil!*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📄 *File*: `{filename}`\n"
                f"📦 *Ukuran*: {size_kb} KB\n"
                f"🕐 *Waktu*: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
        else:
            stderr = result.stderr.strip() if result.stderr else "Unknown error"
            return f"⚠️ Gagal mengambil screenshot: {stderr}"

    except subprocess.TimeoutExpired:
        return "⏱️ Screenshot timeout - proses mengambil terlalu lama."
    except Exception as e:
        return f"❌ Gagal mengambil screenshot: {str(e)}"
