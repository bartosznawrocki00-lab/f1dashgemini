#!/usr/bin/env python3
import json
import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "upgrades.json"
TEMPLATES_DIR = BASE_DIR / "templates"
DIST_DIR = BASE_DIR / "dist"

# Słownik najpopularniejszych pojęć technicznych FIA
TRANSLATIONS = {
    # Cele modyfikacji (Reasons)
    "performance - flow conditioning": "Wydajność – Ukierunkowanie strug",
    "performance - local load": "Wydajność – Lokalny docisk",
    "performance - drag reduction": "Wydajność – Redukcja oporu",
    "circuit specific - cooling": "Pod tor – Chłodzenie",
    "circuit specific - drag reduction": "Pod tor – Redukcja oporu",
    "reliability": "Niezawodność",
    
    # Komponenty aerodynamiczne
    "front wing": "Przednie skrzydło",
    "rear wing": "Tylne skrzydło",
    "beam wing": "Skrzydło belkowe",
    "floor body": "Główna część podłogi",
    "floor edge": "Krawędź podłogi",
    "floor fences": "Kierownice podłogi",
    "floor": "Podłoga",
    "sidepod inlet": "Wloty sekcji bocznych",
    "sidepods": "Sekcje boczne",
    "sidepod": "Sekcja boczna",
    "engine cover": "Pokrywa silnika",
    "front suspension": "Przednie zawieszenie",
    "rear suspension": "Tylne zawieszenie",
    "cooling louvres": "Żaluzje chłodzące",
    "diffuser": "Dyfuzor",
    "nose": "Nos bolidu",
    "coke bottle": "Sekcja 'Coke bottle'",
    "halo": "System Halo",
    "endplate": "Płytka brzegowa"
}

def translate_text(text: str) -> str:
    if not text:
        return ""
    translated = text
    # Zamienia wystąpienia ignorując wielkość liter
    for eng, pl in TRANSLATIONS.items():
        translated = re.sub(re.escape(eng), pl, translated, flags=re.IGNORECASE)
    # Prosta poprawka estetyczna (wielka litera na początku)
    return translated[0].upper() + translated[1:] if translated else ""

def build():
    DIST_DIR.mkdir(exist_ok=True, parents=True)

    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw_upgrades = json.load(f)
    else:
        raw_upgrades = []

    # Tworzenie przetłumaczonej kopii danych na potrzeby strony
    upgrades = []
    for u in raw_upgrades:
        item = u.copy()
        item["component"] = translate_text(item["component"])
        item["reason"] = translate_text(item["reason"])
        upgrades.append(item)

    # Unikalne, posortowane listy do filtrów
    grand_prix_list = sorted({u["grand_prix"] for u in upgrades})
    teams_list = sorted({u["team"] for u in upgrades})

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("index.html")

    html_out = template.render(
        upgrades_json=json.dumps(upgrades, ensure_ascii=False),
        grand_prix_list=grand_prix_list,
        teams_list=teams_list
    )

    out_file = DIST_DIR / "index.html"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"✅ Sukces: Wygenerowano {out_file} (Łącznie wpisów: {len(upgrades)})")

if __name__ == "__main__":
    build()
