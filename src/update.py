#!/usr/bin/env python3
"""
Główny skrypt aktualizacyjny:
Pobiera nowe PDF-y z FIA, parsuje je, aktualizuje plik data/upgrades.json i odpala generator strony.
"""
import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from parse_pdf import parse_car_presentation_pdf
from fetch_fia import download_pdf, URL_TEMPLATE, GP_SLUGS, find_documents_on_page
from build import build

DATA_FILE = BASE_DIR / "data" / "upgrades.json"

def load_upgrades() -> list[dict]:
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []

def save_upgrades(data: list[dict]):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def run_update(manual_pdf: str = None, year: int = 2026):
    existing = load_upgrades()
    existing_ids = {u["id"] for u in existing}
    new_count = 0

    if manual_pdf and os.path.exists(manual_pdf):
        print(f"📂 Wczytywanie lokalnego pliku PDF: {manual_pdf}")
        with open(manual_pdf, "rb") as f:
            parsed = parse_car_presentation_pdf(f.read(), source_url="local_file")
            for item in parsed:
                if item["id"] not in existing_ids:
                    existing.append(item)
                    existing_ids.add(item["id"])
                    new_count += 1
    else:
        print("🌐 Sprawdzanie dostępności dokumentów na serwerach FIA...")
        # Sprawdzamy szablon adresów dla każdego GP
        for slug in GP_SLUGS:
            url = URL_TEMPLATE.format(year=year, slug=slug)
            content = download_pdf(url)
            if content:
                print(f"✅ Znaleziono dokument dla: {slug}")
                parsed = parse_car_presentation_pdf(content, source_url=url)
                for item in parsed:
                    if item["id"] not in existing_ids:
                        existing.append(item)
                        existing_ids.add(item["id"])
                        new_count += 1

    print(f"Dodano {new_count} nowych pozycji do bazy.")
    save_upgrades(existing)
    
    # Przebudowanie plików HTML
    build()

if __name__ == "__main__":
    local_file = sys.argv[1] if len(sys.argv) > 1 else None
    run_update(manual_pdf=local_file)
