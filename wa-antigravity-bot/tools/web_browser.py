"""Web Browsing & Internet Search Tool for WhatsApp Antigravity Bot.

Provides capabilities for:
1. cari_internet(query): Search the live web using search engine (Bing/DuckDuckGo) and return real-time titles, links, and snippets.
2. baca_halaman_web(url): Fetch and extract clean article/content text from any public webpage.
3. cari_wikipedia(query): Quick encyclopedia search for definitions, history, figures, and technical topics.
"""

import re
import urllib.parse
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
}

def cari_internet(query: str, jumlah_hasil: int = 5) -> str:
    """Mencari informasi terkini, berita, data, atau referensi langsung dari internet secara real-time.
    
    Args:
        query: Kata kunci pencarian (contoh: 'harga emas hari ini', 'berita terbaru AI', 'jadwal pertandingan').
        jumlah_hasil: Batas jumlah tautan dan ringkasan yang dikembalikan (default 5).
    """
    if not query or not query.strip():
        return "⚠️ Query pencarian tidak boleh kosong."

    clean_query = query.strip()
    encoded = urllib.parse.quote_plus(clean_query)
    url = f"https://www.bing.com/search?q={encoded}"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return f"⚠️ Gagal melakukan pencarian (HTTP Status {res.status_code})."

        soup = BeautifulSoup(res.text, "html.parser")
        items = []

        for li in soup.select("li.b_algo"):
            h2 = li.find("h2")
            if not h2:
                continue
            title = h2.get_text(strip=True)
            a_tag = h2.find("a")
            link = a_tag["href"] if a_tag and "href" in a_tag.attrs else ""
            
            p = li.find("p")
            snippet = p.get_text(strip=True) if p else ""
            
            if title and link:
                items.append({
                    "title": title,
                    "link": link,
                    "snippet": snippet
                })
                if len(items) >= jumlah_hasil:
                    break

        if not items:
            # Fallback to Wikipedia search if no web results found
            return cari_wikipedia(clean_query)

        output = [f"🌐 *Hasil Pencarian Internet:* `{clean_query}`\n━━━━━━━━━━━━━━━━━━━━"]
        for idx, item in enumerate(items, 1):
            snippet_text = f"\n   _{item['snippet']}_" if item['snippet'] else ""
            output.append(f"{idx}. *{item['title']}*{snippet_text}\n   🔗 {item['link']}")

        output.append("━━━━━━━━━━━━━━━━━━━━\n💡 _Gunakan `baca_halaman_web(url)` jika ingin membaca artikel lengkap dari salah satu tautan di atas._")
        return "\n".join(output)

    except Exception as e:
        return f"⚠️ Terjadi kesalahan saat mencari di internet: {e}"


def baca_halaman_web(url: str, batas_karakter: int = 3000) -> str:
    """Membuka dan membaca isi teks dari sebuah halaman web atau artikel berita.
    
    Args:
        url: Alamat link website yang ingin dibaca (contoh: 'https://kompas.com/...').
        batas_karakter: Maksimal karakter teks yang diambil (default 3000 agar muat di WhatsApp).
    """
    if not url or not url.startswith("http"):
        return "⚠️ URL tidak valid. Pastikan dimulai dengan http:// atau https://"

    try:
        res = requests.get(url.strip(), headers=HEADERS, timeout=12)
        if res.status_code != 200:
            return f"⚠️ Gagal membuka halaman web (HTTP {res.status_code})."

        soup = BeautifulSoup(res.text, "html.parser")

        # Buang elemen yang tidak relevan
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "aside", "svg"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else "Halaman Web"

        # Kumpulkan paragraf
        paragraphs = [p.get_text(strip=True) for p in soup.find_all(["p", "article", "h1", "h2", "h3"]) if len(p.get_text(strip=True)) > 20]
        content = "\n\n".join(paragraphs)

        if not content:
            content = soup.get_text(separator=" ", strip=True)

        if len(content) > batas_karakter:
            content = content[:batas_karakter] + "\n\n_(...teks dipotong sesuai batas maksimal WhatsApp)_"

        return (
            f"📄 *Konten Web:* {title}\n"
            f"🔗 {url}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{content}"
        )

    except Exception as e:
        return f"⚠️ Gagal membaca halaman web {url}: {e}"


def cari_wikipedia(topik: str) -> str:
    """Mencari ringkasan ensiklopedia Wikipedia bahasa Indonesia atau Inggris."""
    if not topik or not topik.strip():
        return "⚠️ Topik Wikipedia tidak boleh kosong."

    clean_topik = topik.strip()
    api_url = "https://id.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": clean_topik,
        "format": "json",
        "utf8": 1,
        "srlimit": 3
    }

    try:
        res = requests.get(api_url, params=params, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            data = res.json()
            search_results = data.get("query", {}).get("search", [])
            if search_results:
                best = search_results[0]
                title = best.get("title", "")
                snippet = BeautifulSoup(best.get("snippet", ""), "html.parser").get_text()
                page_url = f"https://id.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"

                # Ambil intro artikel jika memungkinkan
                intro_params = {
                    "action": "query",
                    "prop": "extracts",
                    "exintro": 1,
                    "explaintext": 1,
                    "titles": title,
                    "format": "json"
                }
                intro_res = requests.get(api_url, params=intro_params, headers=HEADERS, timeout=8)
                intro_text = ""
                if intro_res.status_code == 200:
                    pages = intro_res.json().get("query", {}).get("pages", {})
                    for p_id, p_val in pages.items():
                        intro_text = p_val.get("extract", "")
                        break

                body = intro_text[:1500] if intro_text else snippet
                return (
                    f"📚 *Wikipedia:* *{title}*\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"{body}\n\n"
                    f"🔗 Selengkapnya: {page_url}"
                )

        return f"ℹ️ Tidak ditemukan hasil Wikipedia untuk: '{clean_topik}'."
    except Exception as e:
        return f"⚠️ Error Wikipedia: {e}"
