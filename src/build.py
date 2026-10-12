#!/usr/bin/env python3
import json
import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "upgrades.json"
TEMPLATES_DIR = BASE_DIR / "templates"
DIST_DIR = BASE_DIR / "dist"

def build():
    DIST_DIR.mkdir(exist_ok=True, parents=True)

    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            upgrades = json.load(f)
    else:
        upgrades = []

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
