import cv2
import os
from datetime import datetime

# Base storage directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)

def capture_camera() -> str:
    """Takes a photo from the default webcam."""
    try:
        # Initialize the camera
        cap = cv2.VideoCapture(0)
        
        # Check if camera opened successfully
        if not cap.isOpened():
            return "❌ Gagal mengakses kamera laptop. Pastikan kamera tidak sedang digunakan oleh aplikasi lain atau izin kamera diaktifkan."
            
        # Read a frame
        ret, frame = cap.read()
        
        # Release the camera immediately
        cap.release()
        
        if not ret:
            return "❌ Gagal mengambil gambar dari kamera."
            
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"kamera_{timestamp}.png"
        filepath = os.path.join(STORAGE_DIR, filename)
        
        # Save the image
        cv2.imwrite(filepath, frame)
        
        rel_path = f"storage/{filename}"
        
        return (
            f"[FILE:{rel_path}] 📸 *Foto Kamera Berhasil Diambil!*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📄 *File*: `{filename}`\n"
            f"🕐 *Waktu*: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        
    except Exception as e:
        return f"❌ Terjadi kesalahan saat mengakses kamera: {str(e)}"
