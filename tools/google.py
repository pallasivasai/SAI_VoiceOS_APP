import html
import re
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup
from core.config import GOOGLE_TIMEOUT

def _clean(text: str) -> str:
    text = html.unescape(text or "")
    return re.sub(r"\s+", " ", text).strip()

def search_google(question: str, language: str = "en-IN") -> str:
    lang = "te" if language.startswith("te") else "en"
    url = f"https://www.google.com/search?q={quote_plus(question)}&hl={lang}&gl=in&gbv=1&nfpr=1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/153 Safari/537.36",
        "Accept-Language": "te-IN,te;q=0.9,en-IN;q=0.8,en;q=0.7" if lang == "te" else "en-IN,en;q=0.9",
    }
    response = requests.get(url, headers=headers, timeout=GOOGLE_TIMEOUT)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for selector in ("#wob_dc", "#wob_tm", '[data-attrid="wa:/description"]', ".VwiC3b", ".yXK7lf"):
        node = soup.select_one(selector)
        if node:
            text = _clean(node.get_text(" ", strip=True))
            if len(text) >= 20:
                return text[:900]
    snippets = []
    for node in soup.select("div.VwiC3b, div.yXK7lf"):
        text = _clean(node.get_text(" ", strip=True))
        if len(text) >= 35 and text not in snippets:
            snippets.append(text)
        if len(snippets) == 3:
            break
    if snippets:
        return " ".join(snippets)[:1200]
    visible = _clean(soup.get_text(" ", strip=True))
    return visible[:1000] if visible else "Google did not return a readable answer."
