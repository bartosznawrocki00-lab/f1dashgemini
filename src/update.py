#!/usr/bin/env python3
"""
Główny skrypt aktualizacyjny:
Pobiera nowe PDF-y z FIA, parsuje je, aktualizuje plik data/upgrades.json i odpala generator strony.
"""
import json
import os
import sys
import io
import re
import pdfplumber
from pathlib import Path
from datetime import datetime

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

def extract_pdf_date(pdf_bytes: bytes) -> str:
    """Odczytuje datę wydania bezpośrednio z tekstu wydrukowanego na dokumencie."""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            first_page = pdf.pages[0].extract_text()
            
            # 1. Szukamy oficjalnej daty z nagłówka, np. "Date | 02 October 2026"
            match = re.search(r"Date\s*\|?\s*(\d{1,2}\s+[a-zA-Z]+\s+\d{4})", first_page)
            if match:
                date_str = match.group(1)
                try:
                    # Tłumaczy angielską datę na format sortowalny, np. 20261002
                    date_obj = datetime.strptime(date_str, "%d %B %Y")
                    return date_obj.strftime("%Y%m%d")
                except ValueError:
                    pass
                    
            # 2. Plan B: Szukamy daty z weekendu, np. "02-04 October 2026"
            match_weekend = re.search(r"(\d{1,2})\s*-\s*\d{1,2}\s+([a-zA-Z]+\s+\d{4})", first_page)
            if match_weekend:
                date_str = f"{match_weekend.group(1)} {match_weekend.group(2)}"
                try:
                    date_obj = datetime.strptime(date_str, "%d %B %Y")
                    return date_obj.strftime("%Y%m%d")
                except ValueError:
                    pass

            # 3. Plan C (Awaryjny): Szukamy w ukrytych metadanych PDF-a
            creation_date = pdf.metadata.get("CreationDate", "")
            match_meta = re.search(r"D:(\d{8})", creation_date)
            if match_meta:
                return match_meta.group(1)
                
    except Exception as e:
        print(f"⚠️ Nie udało się odczytać daty z PDF: {e}")
        
    return "99999999"

def slug_to_gp_name(slug: str) -> str:
    special_cases = {
        "barcelona-catalunya": "Barcelona-Catalunya Grand Prix",
        "emilia-romagna": "Emilia Romagna Grand Prix",
        "sao-paulo": "São Paulo Grand Prix",
        "mexico-city": "Mexico City Grand Prix",
        "las-vegas": "Las Vegas Grand Prix",
        "abu-dhabi": "Abu Dhabi Grand Prix",
        "saudi-arabian": "Saudi Arabian Grand Prix"
    }
    if slug in special_cases:
        return special_cases[slug]
    return slug.replace("-", " ").title() + " Grand Prix"

def clean_database(upgrades: list[dict]) -> list[dict]:
    """Funkcja samonaprawiająca - ujednolica tylko błędy w nazwach, datę załatwia czytnik PDF."""
    for item in upgrades:
        gp = item.get("grand_prix", "").strip()
        
        # Unifikacja nazewnictwa dla starych i dziwnych plików FIA
        if gp == "Grand Prix":
            item["grand_prix"] = "Barcelona-Catalunya Grand Prix"
        elif any(x in gp for x in ["Bahrain", "Sepang", "Malaysia"]):
            item["grand_prix"] = "Bahrain Grand Prix"
            
    return upgrades

def run_update(manual_pdf: str = None, year: int = 2026):
    existing = load_upgrades()
    existing_ids = {u["id"] for u in existing}
    new_count = 0

    if manual_pdf and os.path.exists(manual_pdf):
        print(f"📂 Wczytywanie lokalnego pliku PDF: {manual_pdf}")
        with open(manual_pdf, "rb") as f:
            content = f.read()
            pdf_date = extract_pdf_date(content)
            parsed = parse_car_presentation_pdf(content, source_url="local_file")
            for item in parsed:
                item["pdf_date"] = pdf_date
                if item["id"] not in existing_ids:
                    existing.append(item)
                    existing_ids.add(item["id"])
                    new_count += 1
    else:
        print("🌐 Sprawdzanie dostępności dokumentów na serwerach FIA...")
        for slug in GP_SLUGS:
            url = URL_TEMPLATE.format(year=year, slug=slug)
            content = download_pdf(url)
            if content:
                print(f"✅ Znaleziono dokument dla: {slug}")
                pdf_date = extract_pdf_date(content)
                parsed = parse_car_presentation_pdf(content, source_url=url)
                for item in parsed:
                    item["pdf_date"] = pdf_date
                    item["grand_prix"] = slug_to_gp_name(slug)
                    
                    if item["id"] not in existing_ids:
                        existing.append(item)
                        existing_ids.add(item["id"])
                        new_count += 1

    # PRZEPUSZCZAMY DANE PRZEZ FILTR NAPRAWCZY
    existing = clean_database(existing)
    
    print(f"Dodano {new_count} nowych pozycji do bazy.")
    save_upgrades(existing)
    
    # Przebudowanie plików HTML
    build()

if __name__ == "__main__":
    local_file = sys.argv[1] if len(sys.argv) > 1 else None
    run_update(manual_pdf=local_file)
