#!/usr/bin/env python3
"""
Parser dokumentów FIA 'Car Presentation Submissions' oparty wyłącznie na bibliotece pdfplumber (0 zł, bez LLM).
"""
import io
import re
import hashlib
import pdfplumber

TEAM_MAP = {
    "red bull": "Red Bull",
    "mclaren": "McLaren",
    "ferrari": "Ferrari",
    "mercedes": "Mercedes",
    "aston martin": "Aston Martin",
    "alpine": "Alpine",
    "williams": "Williams",
    "racing bulls": "Racing Bulls",
    "rb": "Racing Bulls",
    "audi": "Audi",
    "sauber": "Audi",
    "haas": "Haas",
    "cadillac": "Cadillac"
}

def normalize_team(raw_name: str) -> str:
    cleaned = raw_name.lower().strip()
    for pattern, official in TEAM_MAP.items():
        if pattern in cleaned:
            return official
    return raw_name.strip()

def clean_text(val) -> str:
    if not val:
        return ""
    return re.sub(r"\s+", " ", str(val)).strip()

def make_upgrade_id(year, gp, team, component, idx):
    key = f"{year}-{gp}-{team}-{component}-{idx}".lower().replace(" ", "-")
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]

def parse_car_presentation_pdf(pdf_bytes: bytes, source_url: str = "") -> list[dict]:
    results = []
    
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        year = None
        grand_prix = None

        # Krok 1: Próba detekcji roku i Grand Prix z pierwszej strony
        if len(pdf.pages) > 0:
            first_page_text = pdf.pages[0].extract_text() or ""
            gp_match = re.search(r"(20\d{2})\s+([A-Za-z ]+?)\s+Grand Prix", first_page_text, re.IGNORECASE)
            if gp_match:
                year = int(gp_match.group(1))
                grand_prix = f"{gp_match.group(2).strip().title()} Grand Prix"

        year = year or 2026
        grand_prix = grand_prix or "Grand Prix"

        # Krok 2: Ekstrakcja tabel per zespół
        current_team = None

        for page in pdf.pages:
            text = page.extract_text() or ""
            lines = [l.strip() for l in text.splitlines() if l.strip()]

            # Szukamy nagłówka Car Presentation i zespołu
            for i, line in enumerate(lines):
                if "car presentation" in line.lower() and i + 1 < len(lines):
                    potential_team = lines[i + 1]
                    norm = normalize_team(potential_team)
                    if norm:
                        current_team = norm

            # Szukamy tabel na stronie
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 2:
                    continue

                for row in table:
                    # Oczyszczenie wiersza
                    cells = [clean_text(c) for c in row if c is not None]
                    if not cells or len(cells) < 3:
                        continue

                    # Pomijamy nagłówki tabeli
                    first_cell = cells[0].lower()
                    if "no." in first_cell or "component" in first_cell or "reason" in first_cell:
                        continue

                    # Typowy układ FIA: [No, Component, Primary Reason, Geometric Differences, Description]
                    # lub [Component, Primary Reason, Differences, Description]
                    offset = 1 if cells[0].isdigit() else 0
                    
                    if len(cells) > offset + 1:
                        component = cells[offset] if len(cells) > offset else ""
                        reason = cells[offset + 1] if len(cells) > offset + 1 else ""
                        diff = cells[offset + 2] if len(cells) > offset + 2 else ""
                        desc = cells[offset + 3] if len(cells) > offset + 3 else ""

                        if component and len(component) > 2 and not component.lower().startswith("no update"):
                            uid = make_upgrade_id(year, grand_prix, current_team or "Unknown", component, len(results))
                            results.append({
                                "id": uid,
                                "year": year,
                                "grand_prix": grand_prix,
                                "team": current_team or "Unknown",
                                "component": component,
                                "reason": reason,
                                "change_detail": diff,
                                "description": desc,
                                "source_url": source_url
                            })

    return results

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], "rb") as f:
            data = parse_car_presentation_pdf(f.read())
            print(f"Sparsowano {len(data)} poprawek:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("Użycie testowe: python parse_pdf.py sciezka_do_pliku.pdf")
