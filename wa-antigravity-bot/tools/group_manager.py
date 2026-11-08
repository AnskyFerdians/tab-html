"""Group Manager Tool for WhatsApp Antigravity Bot.
Provides Python interface and Agent Tooling for WhatsApp Group Management:
- Anti-Link configuration
- Welcome/Goodbye greeting settings
- Kick / Promote / Demote participants
- TagAll / Mention All members
- Open / Close group chat (announcement mode)
- Group invite link retrieval and group inspection
"""

import os
import requests
from typing import Dict, Any, Optional, List

BRIDGE_URL = os.getenv("WHATSAPP_BRIDGE_URL", "http://localhost:3000").rstrip("/")

def list_bot_groups() -> Dict[str, Any]:
    """Retrieve list of all groups that the bot is currently a member of."""
    try:
        res = requests.get(f"{BRIDGE_URL}/groups", timeout=10.0)
        if res.status_code == 200:
            return {"status": "success", "groups": res.json()}
        return {"status": "error", "message": f"Bridge error HTTP {res.status_code}: {res.text}"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal menghubungi bridge: {e}"}

def get_group_metadata(group_jid: str) -> Dict[str, Any]:
    """Get metadata for a specific WhatsApp group (subject, owner, participants, settings)."""
    try:
        res = requests.post(f"{BRIDGE_URL}/group/metadata", json={"groupJid": group_jid}, timeout=10.0)
        if res.status_code == 200:
            return {"status": "success", "data": res.json()}
        return {"status": "error", "message": f"Bridge error HTTP {res.status_code}: {res.text}"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal menghubungi bridge: {e}"}

def kick_group_member(group_jid: str, user_jid: str) -> Dict[str, Any]:
    """Kick / remove a participant from a WhatsApp group."""
    try:
        res = requests.post(
            f"{BRIDGE_URL}/group/kick",
            json={"groupJid": group_jid, "userJid": user_jid},
            timeout=10.0
        )
        if res.status_code == 200:
            return {"status": "success", "message": f"Berhasil mengeluarkan {user_jid} dari grup."}
        return {"status": "error", "message": f"Gagal kick member: {res.text}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def promote_group_member(group_jid: str, user_jid: str) -> Dict[str, Any]:
    """Promote a participant to group admin."""
    try:
        res = requests.post(
            f"{BRIDGE_URL}/group/promote",
            json={"groupJid": group_jid, "userJid": user_jid},
            timeout=10.0
        )
        if res.status_code == 200:
            return {"status": "success", "message": f"Berhasil mempromosikan {user_jid} menjadi Admin."}
        return {"status": "error", "message": f"Gagal mempromosikan admin: {res.text}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def demote_group_member(group_jid: str, user_jid: str) -> Dict[str, Any]:
    """Demote a group admin back to regular member."""
    try:
        res = requests.post(
            f"{BRIDGE_URL}/group/demote",
            json={"groupJid": group_jid, "userJid": user_jid},
            timeout=10.0
        )
        if res.status_code == 200:
            return {"status": "success", "message": f"Berhasil menurunkan {user_jid} dari status Admin."}
        return {"status": "error", "message": f"Gagal menurunkan status admin: {res.text}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def set_group_announcement_mode(group_jid: str, is_closed: bool) -> Dict[str, Any]:
    """Set group to announcement only (only admins can send messages) or open for everyone."""
    action = "close" if is_closed else "open"
    try:
        res = requests.post(
            f"{BRIDGE_URL}/group/settings",
            json={"groupJid": group_jid, "action": action},
            timeout=10.0
        )
        if res.status_code == 200:
            status_text = "ditutup (hanya admin)" if is_closed else "dibuka untuk semua peserta"
            return {"status": "success", "message": f"Grup berhasil {status_text}."}
        return {"status": "error", "message": f"Gagal mengatur setelan grup: {res.text}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_group_invite_link(group_jid: str) -> Dict[str, Any]:
    """Get group invite link."""
    try:
        res = requests.post(
            f"{BRIDGE_URL}/group/invite-code",
            json={"groupJid": group_jid},
            timeout=10.0
        )
        if res.status_code == 200:
            data = res.json()
            return {"status": "success", "link": data.get("link", "")}
        return {"status": "error", "message": f"Gagal mengambil link grup: {res.text}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def tag_all_members(group_jid: str, message: str) -> Dict[str, Any]:
    """Mention all members in a group with a custom broadcast message."""
    try:
        res = requests.post(
            f"{BRIDGE_URL}/group/tagall",
            json={"groupJid": group_jid, "message": message},
            timeout=15.0
        )
        if res.status_code == 200:
            return {"status": "success", "message": "Berhasil memanggil semua anggota grup."}
        return {"status": "error", "message": f"Gagal tag all: {res.text}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def configure_group_protection(
    group_jid: str,
    antilink: Optional[bool] = None,
    antilink_action: Optional[str] = None,
    welcome: Optional[bool] = None,
    goodbye: Optional[bool] = None
) -> Dict[str, Any]:
    """Configure anti-link and greeting options for a group."""
    updates = {}
    if antilink is not None:
        updates["antilink"] = antilink
    if antilink_action in ["warn", "delete", "kick"]:
        updates["antilink_action"] = antilink_action
    if welcome is not None:
        updates["welcome"] = welcome
    if goodbye is not None:
        updates["goodbye"] = goodbye

    try:
        res = requests.post(
            f"{BRIDGE_URL}/group/config",
            json={"groupJid": group_jid, "updates": updates},
            timeout=10.0
        )
        if res.status_code == 200:
            return {"status": "success", "config": res.json()}
        return {"status": "error", "message": f"Gagal update config: {res.text}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
