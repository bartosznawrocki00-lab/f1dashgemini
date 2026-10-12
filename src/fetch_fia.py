#!/usr/bin/env python3
"""
Skrypt pobierający pliki 'Car Presentation Submissions' z portalu FIA (Decision Documents).
"""
import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}

# Szablon URL dokumentów FIA (standardowa konwencja nazewnictwa)
URL_TEMPLATE = "https://www.fia.com/system/files/decision-document/{year}_{slug}_grand_prix_-_car_presentation_submissions.pdf"

GP_SLUGS = [
    "australian", "chinese", "japanese", "bahrain", "saudi_arabian", "miami",
    "canadian", "monaco", "barcelona-catalunya", "austrian", "british", "belgian",
    "hungarian", "dutch", "italian", "spanish", "azerbaijan", "singapore",
    "united_states", "mexico_city", "sao_paulo", "las_vegas", "qatar", "abu_dhabi"
]

def find_documents_on_page(page_url: str) -> list[dict]:
    found = []
    try:
        r = requests.get(page_url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = urljoin(page_url, a["href"])
            text = a.get_text(" ", strip=True).lower()
            if href.lower().endswith(".pdf") and ("car presentation" in text or "car_presentation" in href.lower()):
                found.append({"url": href, "title": text})
    except Exception as e:
        print(f"⚠️ Błąd podczas parsowania strony {page_url}: {e}")
    return found

def download_pdf(url: str) -> bytes | None:
    time.sleep(1) # Kulturalny odstęp
    try:
        resp = requests.get(url, headers=HEADERS, timeout=45)
        if resp.status_code == 200 and resp.content.startswith(b"%PDF"):
            return resp.content
    except requests.RequestException as e:
        print(f"Nie udało się pobrać {url}: {e}")
    return None
