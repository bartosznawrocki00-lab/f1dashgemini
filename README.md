# 🏎️ F1 Car Upgrades Tracker (100% Darmowy Dashboard)

Statyczny serwis WWW śledzący oficjalne modyfikacje i pakiety aerodynamiczne bolidów Formuły 1 na podstawie dokumentów FIA (*Car Presentation Submissions*).

Projekt jest w **100% darmowy**:
- **0 zł za modele AI:** parsujemy czyste tabele PDF w Pythonie (`pdfplumber`).
- **0 zł za hosting:** strona to ultralekki statyczny HTML + Tailwind CSS + Alpine.js serwowany przez darmowe **GitHub Pages**.
- **0 zł za bazę danych:** dane leżą bezpośrednio w pliku `data/upgrades.json` w repozytorium.
- **0 zł za automatyzację:** GitHub Actions sprawdza stronę FIA co 4 godziny w czwartki i piątki.

---

## 🚀 Szybki start lokalnie

1. Zainstaluj wymagane pakiety:
   ```bash
   pip install -r requirements.txt
   ```

2. Wygeneruj stronę do folderu `dist/`:
   ```bash
   python src/build.py
   ```

3. Otwórz plik `dist/index.html` bezpośrednio w dowolnej przeglądarce internetowej!

---

## 🛠️ Jak dodać własnego PDF-a z FIA?

Gdy pobierzesz ze strony FIA plik PDF (np. `2026_melbourne_car_presentation_submissions.pdf`):
```bash
python src/update.py sciezka_do_pliku.pdf
```
Skrypt automatycznie wyciągnie tabele z podziałem na zespoły, dopisze nowe elementy do bazy `data/upgrades.json` i natychmiast przebuduje `dist/index.html`.

---

## 🌐 Wdrożenie na GitHub Pages (Krok po kroku)

1. Stwórz nowe, publiczne repozytorium na swoim GitHubie.
2. Wypchnij cały projekt:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/TWOJ_USER/TWOJE_REPO.git
   git push -u origin main
   ```
3. W ustawieniach repozytorium na GitHubie:
   - Przejdź do: **Settings** -> **Pages**.
   - W sekcji **Build and deployment** -> **Source** wybierz opcję: **GitHub Actions**.
4. W zakładce **Actions** uruchom ręcznie workflow `Update F1 Data & Deploy to GitHub Pages` (przycisk *Run workflow*).
5. Twoja strona będzie dostępna pod adresem:
   `https://TWOJ_USER.github.io/TWOJE_REPO/`
