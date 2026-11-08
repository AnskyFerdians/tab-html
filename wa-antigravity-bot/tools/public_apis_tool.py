"""Public APIs Tool for WhatsApp Antigravity Bot.

Provides searching and browsing for over 2,000+ public/free APIs from
https://github.com/public-apis/public-apis

Features:
- Search APIs by keyword, category, or authentication requirement (e.g., No Auth, apiKey, OAuth)
- List all 50+ categories with API counts
- Get random API suggestion for inspiration
- Local JSON caching (7-day TTL) with automatic background/fallback loading
"""

import os
import re
import json
import random
import urllib.request
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage")
CACHE_FILE = os.path.join(STORAGE_DIR, "public_apis_cache.json")
README_URL = "https://raw.githubusercontent.com/public-apis/public-apis/master/README.md"
CACHE_EXPIRY_DAYS = 7


def _clean_markdown_text(text: str) -> str:
    """Removes HTML tags and clean badges/markdown syntax."""
    # Remove HTML tags (e.g., <img ...>)
    text = re.sub(r"<[^>]+>", "", text)
    # Remove markdown link formatting e.g., [Text](url) -> Text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove backticks
    text = text.replace("`", "")
    return text.strip()


def _fetch_and_parse_from_github() -> List[Dict[str, Any]]:
    """Fetches the latest README.md from GitHub and parses API tables."""
    req = urllib.request.Request(
        README_URL,
        headers={"User-Agent": "WhatsApp-Antigravity-Bot/1.0 (Python urllib)"}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        content = resp.read().decode("utf-8", errors="replace")

    apis = []
    current_category = "General"

    for line in content.splitlines():
        line_clean = line.strip()
        if line_clean.startswith("### "):
            cat_match = re.match(r"^###\s+([A-Za-z0-9\s/&-]+)", line_clean)
            if cat_match:
                current_category = cat_match.group(1).strip()
            continue

        # Parse table rows: | [Name](url) | Description | Auth | HTTPS | CORS |
        if line_clean.startswith("|") and ("[" in line_clean and "]" in line_clean and "(" in line_clean):
            parts = [p.strip() for p in line_clean.split("|")[1:-1]]
            if len(parts) >= 3:
                link_match = re.search(r"\[([^\]]+)\]\(([^)]+)\)", parts[0])
                if link_match:
                    name = link_match.group(1).strip()
                    api_url = link_match.group(2).strip()
                    desc = parts[1].strip() if len(parts) > 1 else ""
                    auth_raw = parts[2].strip() if len(parts) > 2 else "No"
                    https_raw = parts[3].strip() if len(parts) > 3 else "Yes"
                    cors_raw = parts[4].strip() if len(parts) > 4 else "Unknown"

                    # Clean fields
                    auth = _clean_markdown_text(auth_raw) or "No"
                    if "postman" in auth_raw.lower() or "button" in auth_raw.lower():
                        auth = "apiKey"
                    desc = _clean_markdown_text(desc)
                    https = _clean_markdown_text(https_raw)
                    cors = _clean_markdown_text(cors_raw)

                    # Exclude header or markdown divider rows
                    if name.lower() not in ["api", ":---", "---"]:
                        apis.append({
                            "name": name,
                            "url": api_url,
                            "description": desc,
                            "auth": auth,
                            "https": https,
                            "cors": cors,
                            "category": current_category
                        })

    return apis


def get_all_public_apis(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """Loads all public APIs from local cache, or downloads from GitHub if missing/expired."""
    os.makedirs(STORAGE_DIR, exist_ok=True)

    # Check local cache
    if not force_refresh and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            cached_at = datetime.fromisoformat(data.get("updated_at", "2000-01-01"))
            if datetime.now() - cached_at < timedelta(days=CACHE_EXPIRY_DAYS):
                items = data.get("apis", [])
                if items:
                    return items
        except Exception as e:
            print(f"[PublicAPIs] Cache read note: {e}")

    # Fetch from GitHub
    try:
        apis = _fetch_and_parse_from_github()
        if apis:
            cache_payload = {
                "updated_at": datetime.now().isoformat(),
                "total": len(apis),
                "apis": apis
            }
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache_payload, f, ensure_ascii=False, indent=2)
            return apis
    except Exception as e:
        print(f"[PublicAPIs] Failed to fetch from GitHub: {e}")

    # If GitHub failed, fallback to stale cache if available
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("apis", [])
        except Exception:
            pass

    return []


ID_TO_EN_TERMS = {
    "cuaca": "weather",
    "iklim": "weather",
    "film": "movie",
    "bioskop": "movie",
    "musik": "music",
    "lagu": "music",
    "hewan": "animal",
    "binatang": "animal",
    "kucing": "cat",
    "anjing": "dog",
    "buku": "book",
    "novel": "book",
    "berita": "news",
    "kabar": "news",
    "foto": "photo",
    "gambar": "image",
    "lukisan": "art",
    "kripto": "crypto",
    "saham": "stock",
    "keuangan": "finance",
    "uang": "currency",
    "mata uang": "currency",
    "peta": "geocoding",
    "lokasi": "location",
    "terjemahan": "translation",
    "kamus": "dictionary",
    "keamanan": "security",
    "olahraga": "sport",
    "kendaraan": "vehicle",
    "mobil": "car",
    "makanan": "food",
    "minuman": "drink",
    "kesehatan": "health",
    "medis": "medical",
    "pekerjaan": "job",
    "loker": "job",
    "pemerintah": "government",
    "kalender": "calendar",
    "jadwal": "calendar",
    "video": "video",
    "belanja": "shopping",
    "toko": "shopping",
    "permainan": "game",
    "game": "games",
    "lelucon": "joke",
    "kutipan": "quote",
    "kata mutiara": "quote",
    "anime": "anime",
}


def search_public_apis(
    query: str = "",
    category: str = "",
    auth_filter: str = "",
    limit: int = 5
) -> str:
    """Searches the public-apis repository by keyword, category, or auth requirements.

    Args:
        query: Keyword to search in name or description (e.g. 'crypto', 'anime', 'cuaca', 'weather').
        category: Filter by specific category (e.g. 'Animals', 'Finance', 'Games & Comics').
        auth_filter: Filter by auth type ('no' for no auth required, 'apiKey', 'OAuth').
        limit: Max number of APIs to return (default 5, max 15).
    """
    apis = get_all_public_apis()
    if not apis:
        return "❌ Gagal memuat database Public APIs. Pastikan laptop terkoneksi ke internet."

    query_clean = query.strip().lower()
    cat_clean = category.strip().lower()
    auth_clean = auth_filter.strip().lower()

    # Expand Indonesian search terms to English keywords
    search_targets = [query_clean] if query_clean else []
    if query_clean:
        for id_word, en_word in ID_TO_EN_TERMS.items():
            if id_word in query_clean and en_word not in search_targets:
                search_targets.append(en_word)

    filtered = []
    for item in apis:
        # Category check
        if cat_clean and cat_clean not in item["category"].lower():
            continue

        # Auth check: "no" or "none" means no authentication needed
        if auth_clean:
            item_auth = item["auth"].lower()
            if auth_clean in ["no", "none", "gratis", "free", "tanpa auth"]:
                if item_auth not in ["no", "tidak", "none", ""]:
                    continue
            elif auth_clean not in item_auth:
                continue

        # Query check in name or description
        if search_targets:
            name_desc = f"{item['name']} {item['description']} {item['category']}".lower()
            if not any(target in name_desc for target in search_targets):
                continue

        filtered.append(item)

    if not filtered:
        criteria = []
        if query:
            criteria.append(f"kata kunci *'{query}'*")
        if category:
            criteria.append(f"kategori *'{category}'*")
        if auth_filter:
            criteria.append(f"auth *'{auth_filter}'*")
        filter_str = ", ".join(criteria) or "kriteria yang ditentukan"
        return (
            f"🔍 *Pencarian Public APIs*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Tidak ditemukan API untuk {filter_str}.\n\n"
            f"💡 Ketik *kategori api* untuk melihat daftar kategori yang tersedia."
        )

    limit = max(1, min(limit, 15))
    results = filtered[:limit]
    total_found = len(filtered)

    msg_lines = [
        f"🔌 *DIREKTORI PUBLIC APIs (GitHub)*",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"Ditemukan *{total_found}* API" + (f" untuk '{query}'" if query else "") + f" (Menampilkan {len(results)}):\n"
    ]

    for idx, api in enumerate(results, start=1):
        auth_badge = "🔓 Tanpa Auth (Bebas)" if api["auth"].lower() in ["no", "none", ""] else f"🔑 Auth: {api['auth']}"
        https_badge = "🔒 HTTPS" if api["https"].lower() == "yes" else "⚠️ HTTP"
        cors_badge = f"🌐 CORS: {api['cors']}" if api['cors'] else ""
        
        meta = " • ".join(filter(None, [auth_badge, https_badge, cors_badge]))

        msg_lines.append(
            f"*{idx}. {api['name']}* ({api['category']})\n"
            f"📝 {api['description']}\n"
            f"🔗 {api['url']}\n"
            f"ℹ️ {meta}\n"
        )

    if total_found > limit:
        msg_lines.append(f"_...dan {total_found - limit} API lainnya._")

    msg_lines.append("━━━━━━━━━━━━━━━━━━━━")
    msg_lines.append("💡 *Tips:* Ketik `kategori api` atau `api [keyword]` untuk eksplorasi.")

    return "\n".join(msg_lines)


def list_public_api_categories() -> str:
    """Returns all available API categories with the count of APIs in each."""
    apis = get_all_public_apis()
    if not apis:
        return "❌ Gagal memuat database Public APIs."

    counts: Dict[str, int] = {}
    for item in apis:
        cat = item["category"]
        counts[cat] = counts.get(cat, 0) + 1

    sorted_cats = sorted(counts.items(), key=lambda x: x[0])

    lines = [
        f"📂 *KATEGORI PUBLIC APIs ({len(sorted_cats)} Kategori)*",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"Total *{len(apis):,}* API gratis tersedia:\n"
    ]

    # Format in readable 2-column or bulleted layout
    for cat, count in sorted_cats:
        lines.append(f"• *{cat}* ({count} API)")

    lines.append("\n━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 Ketik `api [nama_kategori]` untuk mencari API di kategori tersebut.")
    lines.append("Contoh: `api anime` atau `api crypto`")

    return "\n".join(lines)


def get_random_public_api(category: str = "") -> str:
    """Returns a random public API suggestion."""
    apis = get_all_public_apis()
    if not apis:
        return "❌ Gagal memuat database Public APIs."

    pool = apis
    if category.strip():
        cat_clean = category.strip().lower()
        pool = [a for a in apis if cat_clean in a["category"].lower()]
        if not pool:
            return f"⚠️ Tidak ada API dalam kategori '{category}'."

    chosen = random.choice(pool)

    auth_badge = "🔓 Tanpa Auth (Langsung Pakai)" if chosen["auth"].lower() in ["no", "none", ""] else f"🔑 Auth: {chosen['auth']}"
    https_badge = "🔒 HTTPS" if chosen["https"].lower() == "yes" else "⚠️ HTTP"

    return (
        f"🎲 *REKOMENDASI PUBLIC API ACAK*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ *Nama*: *{chosen['name']}*\n"
        f"📂 *Kategori*: {chosen['category']}\n"
        f"📝 *Deskripsi*: {chosen['description']}\n"
        f"🔗 *URL*: {chosen['url']}\n"
        f"🔐 *Keamanan*: {auth_badge} | {https_badge} | CORS: {chosen['cors']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 Ketik `api acak` untuk rekomendasi lainnya!"
    )


def refresh_public_apis_cache() -> str:
    """Forces cache refresh from the upstream GitHub repository."""
    apis = get_all_public_apis(force_refresh=True)
    if not apis:
        return "❌ Gagal memperbarui cache dari GitHub."

    return (
        f"✅ *Cache Public APIs Diperbarui!*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📥 Berhasil mengunduh *{len(apis):,}* API dari repository GitHub `public-apis/public-apis`.\n"
        f"🕐 Waktu: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    )


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("Testing get_all_public_apis...")
    items = get_all_public_apis()
    print(f"Loaded {len(items)} items.")
    print("\nSearch test ('weather'):")
    print(search_public_apis(query="weather", limit=2))
    print("\nRandom test:")
    print(get_random_public_api())
