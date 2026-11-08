"""FastAPI Webhook Server & Dispatch Engine for WhatsApp Antigravity Bot.

Improvements v2.0:
- FAST PRE-REPLY: Bot langsung kirim "Sedang memproses..." sebelum AI menjawab,
  sehingga user tidak bingung mengira bot mati/lambat.
- SERVER ONLINE NOTIFICATION: Saat FastAPI startup, bot otomatis beri tahu admin via WA.
- Smarter dispatch with image/file detection.
- Better error handling dan logging.
"""

import os
import re
import time
import asyncio
import requests
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from starlette.concurrency import run_in_threadpool

from agent_service import agent_service, SECURITY_CODE
from tools.doc_generator import STORAGE_DIR
from tools.file_manager import clean_stale_storage

load_dotenv()

app = FastAPI(
    title="WhatsApp Antigravity Bot",
    description="Integrasi WhatsApp Bot berbasis Antigravity Agent, FastAPI, dan Document Generator",
    version="2.0.0"
)

# Configuration
BRIDGE_URL = os.getenv("WHATSAPP_BRIDGE_URL", "http://localhost:3000").rstrip("/")
ENABLE_LOCAL_DISPATCH = os.getenv("ENABLE_LOCAL_DISPATCH", "true").lower() == "true"
ADMIN_WA_ID = os.getenv("ADMIN_JID", "")  # Admin WhatsApp JID, sama dgn bridge

# Track bot start time for uptime
_BOT_START_TIME = time.time()


class WhatsAppWebhookPayload(BaseModel):
    """Payload model supporting both Baileys, WPPConnect, and standard JSON formats."""
    sender: Optional[str] = Field(None, alias="from", description="Sender phone number or ID")
    sender_id: Optional[str] = Field(None, description="Alternative sender identifier")
    text: Optional[str] = Field(None, description="Message text content")
    message: Optional[str] = Field(None, description="Alternative message text")
    body: Optional[str] = Field(None, description="Alternative message text (WPPConnect/Twilio)")
    sender_name: Optional[str] = Field(None, alias="pushName", description="Sender display name")
    name: Optional[str] = Field(None, description="Alternative sender display name")

    class Config:
        populate_by_name = True


class OutgoingTextMessage(BaseModel):
    to: str
    message: str


class OutgoingFileMessage(BaseModel):
    to: str
    filePath: str
    caption: Optional[str] = None


def extract_file_token(response_text: str) -> tuple[Optional[str], str]:
    """
    Parses [FILE:path/to/file.ext] token from agent response.
    Returns: (file_path or None, clean_message_text)
    """
    pattern = r"\[FILE:(.*?)\]"
    match = re.search(pattern, response_text)
    if match:
        raw_path = match.group(1).strip()
        clean_text = re.sub(pattern, "", response_text).strip()
        # Resolve path to absolute if relative
        if not os.path.isabs(raw_path):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            abs_path = os.path.normpath(os.path.join(base_dir, raw_path))
        else:
            abs_path = os.path.normpath(raw_path)
        return abs_path, clean_text
    return None, response_text


def dispatch_to_bridge(to: str, text: str, file_path: Optional[str] = None, timeout: float = 15.0):
    """
    Dispatches outgoing response to the WhatsApp bridge.
    - If file_path is an image (png/jpg): POST /send-image
    - If file_path is a document: POST /send-file
    - Otherwise: POST /send-message
    """
    if not text and not file_path:
        return

    if file_path and os.path.exists(file_path):
        ext = os.path.splitext(file_path)[1].lower()
        is_image = ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']

        if is_image:
            target_url = f"{BRIDGE_URL}/send-image"
            payload = {
                "to": to,
                "imagePath": os.path.abspath(file_path),
                "caption": text
            }
            print(f"[Dispatch Engine] Sending IMAGE to bridge ({target_url}): {file_path}")
        else:
            target_url = f"{BRIDGE_URL}/send-file"
            payload = {
                "to": to,
                "filePath": os.path.abspath(file_path),
                "caption": text
            }
            print(f"[Dispatch Engine] Sending DOCUMENT to bridge ({target_url}): {file_path}")
    else:
        target_url = f"{BRIDGE_URL}/send-message"
        payload = {
            "to": to,
            "message": text
        }
        print(f"[Dispatch Engine] Sending TEXT to bridge ({target_url}): {text[:80]}...")

    try:
        res = requests.post(target_url, json=payload, timeout=timeout)
        print(f"[Dispatch Engine] Bridge Response ({res.status_code}): {res.text[:150]}")
    except requests.exceptions.RequestException as e:
        print(f"[Dispatch Engine] Note: Bridge at {target_url} not reachable. Reason: {e}")


def notify_bridge_server_online():
    """Called on FastAPI startup to notify admin that the server is online."""
    uptime = round(time.time() - _BOT_START_TIME, 1)

    # Admin notification via bridge webhook (only if ADMIN_WA_ID is configured)
    if not ADMIN_WA_ID:
        return
    try:
        message = (
            f"🚀 *ANTIGRAVITY BOT — FASTAPI SERVER AKTIF!*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ FastAPI Agent Service berhasil dimuat\n"
            f"⏱️ Startup time: {uptime}s\n"
            f"🤖 Model AI: Gemini 3.6 Flash\n"
            f"🌐 Endpoint: /webhook/whatsapp\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Bot siap menerima pesan!"
        )
        res = requests.post(
            f"{BRIDGE_URL}/notify-admin",
            json={"message": message},
            timeout=5.0
        )
        print(f"[Startup Notify] Admin notified: {res.status_code}")
    except Exception as e:
        print(f"[Startup Notify] Could not notify admin (bridge may not be up yet): {e}")


# ─────────────────────────────────────────────────
# FASTAPI EVENTS
# ─────────────────────────────────────────────────

@app.on_event("startup")
async def on_startup():
    """Run background tasks on startup."""
    # Clean stale files in storage older than 48 hours
    try:
        cleaned = clean_stale_storage(max_age_hours=48)
        if cleaned > 0:
            print(f"[FastAPI Startup] Cleaned {cleaned} stale temporary files from storage.")
    except Exception as e:
        print(f"[FastAPI Startup] Storage cleanup error: {e}")

    # Notify admin after a short delay (let bridge connect first)
    async def delayed_notify():
        await asyncio.sleep(8)  # wait 8s for bridge to be ready
        await asyncio.get_event_loop().run_in_executor(None, notify_bridge_server_online)

    asyncio.create_task(delayed_notify())
    print("[FastAPI] Server started successfully. Ready to process messages.")


# ─────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────

@app.get("/")
def root():
    uptime = round(time.time() - _BOT_START_TIME)
    return {
        "status": "online",
        "service": "WhatsApp Antigravity Bot v2.0",
        "security_code_required": True,
        "security_code": SECURITY_CODE,
        "uptime_seconds": uptime,
        "docs_url": "/docs"
    }


@app.get("/health")
def health():
    uptime = round(time.time() - _BOT_START_TIME)
    return {
        "status": "ok",
        "storage_dir": os.path.abspath(STORAGE_DIR),
        "uptime_seconds": uptime
    }


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(payload: WhatsAppWebhookPayload, background_tasks: BackgroundTasks):
    """
    Main webhook receiver for WhatsApp messages.
    Accepts incoming payload from Baileys / WPPConnect bridge, processes via Antigravity Agent,
    and dispatches text / document responses.

    Flow:
    1. Validate payload
    2. (Optional) Pre-reply cepat: bridge handles this via sendPreReply
    3. Process message with AI Agent (in threadpool for non-blocking)
    4. Dispatch final reply back to bridge
    """
    # 1. Resolve sender ID and message text from various possible keys
    sender = payload.sender or payload.sender_id
    text = payload.text or payload.message or payload.body
    sender_name = payload.sender_name or payload.name

    if not sender or not text:
        raise HTTPException(
            status_code=400,
            detail="Payload must include 'from' or 'sender_id' and 'text' or 'message'."
        )

    print(f"\n[Incoming Webhook] From: {sender} ({sender_name or 'Unknown'}) | Text: '{text}'")

    # 2. Process message with Antigravity Agent (Hermes) in threadpool for non-blocking fast response
    try:
        bot_reply = await run_in_threadpool(
            agent_service.process_message,
            sender_id=sender,
            message=text,
            sender_name=sender_name
        )
    except Exception as e:
        print(f"[Webhook] Agent error: {e}")
        bot_reply = (
            "⚠️ Maaf, terjadi kesalahan internal pada AI Agent.\n"
            "Silakan coba lagi dalam beberapa detik. Jika masalah berlanjut, coba kirim `status laptop`."
        )

    # 3. Check if reply is None (ignored unverified user/group)
    if not bot_reply:
        print(f"[Webhook] Pesan diabaikan (kontak/grup {sender} belum diverifikasi kode keamanan).")
        return JSONResponse(content={"status": "ignored", "reply": None})

    # 4. Parse [FILE:...] token
    file_path, clean_text = extract_file_token(bot_reply)

    # 5. Dispatch to WhatsApp Bridge in background
    if ENABLE_LOCAL_DISPATCH:
        background_tasks.add_task(dispatch_to_bridge, sender, clean_text, file_path)

    # Return response payload for easy debugging / cURL testing
    response_data = {
        "status": "success",
        "sender": sender,
        "reply": clean_text,
        "has_file": bool(file_path),
        "file_path": file_path,
        "raw_response": bot_reply
    }
    return JSONResponse(content=response_data)


# ─────────────────────────────────────────────────
# MOCK BRIDGE ENDPOINTS (for local testing without Node.js)
# ─────────────────────────────────────────────────

@app.post("/send-message")
def mock_send_message(payload: OutgoingTextMessage):
    """Simulates WhatsApp Bridge /send-message endpoint."""
    print(f"[Mock Bridge] >>> Delivering TEXT to {payload.to}: {payload.message}")
    return {"status": "delivered", "type": "text", "to": payload.to}


@app.post("/send-file")
def mock_send_file(payload: OutgoingFileMessage):
    """Simulates WhatsApp Bridge /send-file endpoint."""
    print(f"[Mock Bridge] >>> Delivering FILE to {payload.to}: {payload.filePath} (Caption: {payload.caption})")
    return {
        "status": "delivered",
        "type": "file",
        "to": payload.to,
        "filePath": payload.filePath,
        "caption": payload.caption
    }


class NotifyAdminPayload(BaseModel):
    message: Optional[str] = None


@app.post("/notify-admin")
def mock_notify_admin(payload: NotifyAdminPayload):
    """Mock for bridge /notify-admin endpoint."""
    print(f"[Mock Bridge] >>> Admin notification: {payload.message}")
    return {"status": "ok"}


@app.get("/download-file")
def download_generated_file(path: str):
    """Allows downloading a generated file directly via browser or link."""
    clean_path = os.path.normpath(path)
    if not os.path.exists(clean_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(clean_path, filename=os.path.basename(clean_path))


# ─────────────────────────────────────────────────
# GROUP MANAGEMENT API ENDPOINTS
# ─────────────────────────────────────────────────

@app.get("/api/groups")
def api_list_groups():
    from tools.group_manager import list_bot_groups
    return list_bot_groups()


class GroupTargetPayload(BaseModel):
    group_jid: str
    user_jid: str


@app.post("/api/group/kick")
def api_group_kick(payload: GroupTargetPayload):
    from tools.group_manager import kick_group_member
    return kick_group_member(payload.group_jid, payload.user_jid)


@app.post("/api/group/promote")
def api_group_promote(payload: GroupTargetPayload):
    from tools.group_manager import promote_group_member
    return promote_group_member(payload.group_jid, payload.user_jid)


@app.post("/api/group/demote")
def api_group_demote(payload: GroupTargetPayload):
    from tools.group_manager import demote_group_member
    return demote_group_member(payload.group_jid, payload.user_jid)


class GroupTagallPayload(BaseModel):
    group_jid: str
    message: Optional[str] = ""


@app.post("/api/group/tagall")
def api_group_tagall(payload: GroupTagallPayload):
    from tools.group_manager import tag_all_members
    return tag_all_members(payload.group_jid, payload.message)


class GroupSettingsPayload(BaseModel):
    group_jid: str
    is_closed: bool


@app.post("/api/group/settings")
def api_group_settings(payload: GroupSettingsPayload):
    from tools.group_manager import set_group_announcement_mode
    return set_group_announcement_mode(payload.group_jid, payload.is_closed)


class GroupConfigPayload(BaseModel):
    group_jid: str
    antilink: Optional[bool] = None
    antilink_action: Optional[str] = None
    welcome: Optional[bool] = None
    goodbye: Optional[bool] = None


@app.post("/api/group/config")
def api_group_config(payload: GroupConfigPayload):
    from tools.group_manager import configure_group_protection
    return configure_group_protection(
        payload.group_jid,
        antilink=payload.antilink,
        antilink_action=payload.antilink_action,
        welcome=payload.welcome,
        goodbye=payload.goodbye
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"Starting WhatsApp Antigravity Bot v2.0 on http://0.0.0.0:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
