# TrackTix – Requirement Traceability System

Ein Ticket-System mit vollständiger Traceability von der Anforderung bis zum Systemtest,
inklusive Git-Commit-Verlinkung je beteiligter Person im Entwicklungsprozess.

## Kernkonzept: Traceability-Kette

```
Anforderung (SRS-001, URL zur Spezifikation)
    └── Ticket (PROJ-42)
            ├── Git Commits (SHA + URL zu beliebigem Git-Server)
            │       └── Autor (Person mit Git-Server-URL)
            ├── Tests (Unit / Integration / System)
            │       └── Tester (Person)
            └── Kommentare (Entwickler / Tester)
```

## Features

- **Projekte** mit Schlüssel (z.B. `PROJ`) und Git-Basis-URL
- **Anforderungen** mit eindeutigem Schlüssel (z.B. `SRS-001`), Beschreibung und Hyperlink zur externen Spezifikation
- **Tickets** verknüpfbar mit 1..n Anforderungen (Teil einer Anforderung, ganze Anforderung, Menge von Anforderungen)
- **Personen** mit individuellem Git-Server-Link (GitHub, GitLab, Gitea, …)
- **Git Commits** mit SHA, Commit-Nachricht, Autor, direktem URL zum Commit auf dem Git-Server
- **Tests** (Unit, Integration, System) mit Ergebnis (pending / passed / failed) und Tester
- **Kommentare** am Ticket für Entwicklungs- und Testnotizen
- **Traceability-Ansicht** im Ticket: vollständige Kette von Anforderung → Commit → Test auf einen Blick
- Status-Workflow: `open → in_progress → in_review → testing → closed / rejected`
- Prioritäten: `low / medium / high / critical`

## Schnellstart (Docker)

```bash
docker compose up --build
# → http://localhost:8000
```

## Lokaler Start (ohne Docker)

### Variante A: PostgreSQL ist bereits global installiert (Linux/macOS)

```bash
# PostgreSQL muss laufen
createdb tracktix
createuser tracktix -P  # Passwort: tracktix

pip install -r requirements.txt

export DATABASE_URL=postgresql://tracktix:tracktix@localhost:5432/tracktix
uvicorn app.main:app --reload
# → http://localhost:8000
```

### Variante B: Windows ohne Admin-Rechte (portable PostgreSQL-Binaries)

Diese Variante benötigt keine Installation mit Admin-Rechten, da sowohl PostgreSQL
als auch die Python-Umgebung vollständig im eigenen Benutzerprofil laufen.

#### 1. PostgreSQL einmalig einrichten

1. ZIP-Binaries von [postgresql.org/download/windows](https://www.postgresql.org/download/windows/)
   herunterladen (Variante „binaries", **kein** Installer) und z.B. nach
   `C:\Users\<Benutzer>\Downloads\postgresql-<version>-windows-x64-binaries\pgsql` entpacken.
2. Datenverzeichnis initialisieren (einmalig, legt den Datenbank-Superuser an):

   ```powershell
   cd C:\Users\<Benutzer>\Downloads\postgresql-<version>-windows-x64-binaries\pgsql
   .\bin\initdb.exe -D .\data -U dbuser -W
   # nach einem Passwort für den Superuser "dbuser" fragen lassen und merken
   ```

3. In `data\pg_hba.conf` stehen die lokalen Verbindungen standardmäßig auf
   `trust` (siehe Zeilen für `127.0.0.1/32` und `::1/128`) – damit ist für
   lokale Verbindungen kein Passwort nötig, ein Login als beliebiger
   existierender Rolle reicht aus.

#### 2. PostgreSQL-Server starten / stoppen / neu starten

```powershell
cd C:\Users\<Benutzer>\Downloads\postgresql-<version>-windows-x64-binaries\pgsql\bin

# Starten
.\pg_ctl.exe -D ..\data -l logfile start

# Stoppen
.\pg_ctl.exe -D ..\data stop

# Neu starten (z.B. nach Konfigurationsänderung in postgresql.conf/pg_hba.conf)
.\pg_ctl.exe -D ..\data restart
```

Der Server muss laufen, bevor die App gestartet wird.

#### 3. Datenbank und Rolle für die App anlegen (einmalig)

```powershell
.\psql.exe -U dbuser -d postgres -c "CREATE USER tracktix WITH PASSWORD 'tracktix';" -c "CREATE DATABASE tracktix OWNER tracktix;"
```

#### 4. Python-Umgebung einrichten (einmalig)

Im Projektordner (`tracktix`):

```powershell
python -m venv venv
.\venv\Scripts\pip.exe install -r requirements.txt
```

#### 5. App starten

```powershell
$env:DATABASE_URL = "postgresql://tracktix:tracktix@localhost:5432/tracktix"
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
# → http://localhost:8000
```

Beim Start wird das Datenbankschema automatisch angelegt
(`app/database.py` → `init_db()` ruft `Base.metadata.create_all()` auf;
es ist also **kein** manuelles SQL-Schema oder Alembic-Migrationsschritt nötig).

#### 6. Nach einer Codeänderung neu starten

- Mit dem Flag `--reload` lädt uvicorn Änderungen an `.py`-Dateien automatisch
  neu – ein manueller Neustart ist für reinen Python-Code in der Regel nicht
  nötig.
- Falls doch ein manueller Neustart gewünscht ist (z.B. nach Änderungen an
  Umgebungsvariablen): den laufenden Prozess mit `Strg+C` im Terminal beenden
  und Schritt 5 erneut ausführen.
- Bei Änderungen am Datenmodell (`app/models.py`): App neu starten reicht,
  `create_all()` legt fehlende Tabellen/Spalten **nur für neue Tabellen** an;
  bestehende Tabellen werden nicht automatisch migriert. Für Schemaänderungen
  an bestehenden Tabellen wird eine echte Migration (z.B. mit Alembic) benötigt.
- Den PostgreSQL-Server selbst muss man für Codeänderungen **nicht** neu
  starten – nur uvicorn.

#### 7. Alles wieder herunterfahren

```powershell
# uvicorn: Strg+C im Terminal-Fenster

# PostgreSQL stoppen
cd C:\Users\<Benutzer>\Downloads\postgresql-<version>-windows-x64-binaries\pgsql\bin
.\pg_ctl.exe -D ..\data stop
```

## Tests & Coverage

Die Test-Abhängigkeiten (`pytest`, `pytest-asyncio`, `pytest-cov`) sind **nicht**
in `requirements.txt` enthalten, sondern in `requirements-dev.txt`, da sie nur
zur Entwicklung und nicht für den Betrieb der App benötigt werden.

### Einmalig: Test-Abhängigkeiten installieren

```bash
# Windows (venv)
.\venv\Scripts\pip.exe install -r requirements-dev.txt

# Linux/macOS
pip install -r requirements-dev.txt
```

`requirements-dev.txt` zieht über `-r requirements.txt` automatisch auch die
Produktions-Abhängigkeiten mit.

### Tests ausführen

```bash
# Windows (venv)
.\venv\Scripts\python.exe -m pytest

# Linux/macOS
pytest
```

`pytest.ini` ist so konfiguriert, dass bei jedem Lauf automatisch:

- `tests/test_e2e_playwright.py` übersprungen wird (benötigt das separate,
  nicht in `requirements-dev.txt` enthaltene `playwright`-Paket inkl.
  Browser-Binaries),
- ein Coverage-Report für `app/` in der Konsole ausgegeben wird,
- ein **HTML-Coverage-Report nach `doc/coverage/`** geschrieben wird
  (`doc/coverage/index.html` im Browser öffnen).

Ziel ist 100 % Testabdeckung (mindestens 90 % gelten als ausreichend).

### Playwright-E2E-Tests separat ausführen (optional)

Die Playwright-Tests (`tests/test_e2e_playwright.py`) starten intern einen
echten Uvicorn-Server (siehe `live_server`-Fixture in `tests/conftest.py`)
und steuern ihn über einen headless Chromium-Browser. Dafür wird zusätzlich
das `playwright`-Paket samt Browser-Binary benötigt – beides **nicht** in
`requirements.txt`/`requirements-dev.txt` enthalten, da es nur für diese
optionale Testklasse gebraucht wird.

#### Einmalig: Playwright + Browser installieren

```bash
# Windows (venv)
.\venv\Scripts\pip.exe install playwright
.\venv\Scripts\python.exe -m playwright install chromium

# Linux/macOS
pip install playwright
playwright install chromium
```

Der Browser wird ohne Admin-Rechte ins Benutzerprofil installiert
(Windows: `%LOCALAPPDATA%\ms-playwright`, Linux/macOS: `~/.cache/ms-playwright`).

#### Playwright-Tests ausführen

```bash
# Windows (venv)
.\venv\Scripts\python.exe -m pytest tests\test_e2e_playwright.py --no-cov

# Linux/macOS
pytest tests/test_e2e_playwright.py --no-cov
```

Hinweise:

- Die Datei wird explizit als Pfad übergeben – das `--ignore` aus den
  Standard-`addopts` in `pytest.ini` greift dann nicht, da ein explizit
  benannter Pfad Vorrang vor `--ignore` hat.
- `--no-cov` deaktiviert die Coverage-Messung/den HTML-Report aus den
  Standard-`addopts`, da Coverage für reine Browser-UI-Tests nicht sinnvoll
  ist und den Lauf nur verlangsamt.
- Laufzeit liegt bei ca. 4–5 Minuten für die gesamte Playwright-Suite
  (94 Tests, headless Chromium).

## API-Dokumentation

```
http://localhost:8000/docs        # Swagger UI
http://localhost:8000/redoc       # ReDoc
```

## Datenmodell (vereinfacht)

| Tabelle           | Beschreibung                                      |
|-------------------|---------------------------------------------------|
| projects          | Projekt mit Schlüssel und Git-Basis-URL           |
| requirements      | Anforderung mit Schlüssel, Text, URL              |
| tickets           | Ticket (n:m zu requirements)                      |
| persons           | Entwickler / Tester mit individuellem Git-Server  |
| commits           | Git-Commit mit SHA, URL, Autor                    |
| tests             | Test (unit/integration/system) mit Ergebnis       |
| comments          | Kommentare am Ticket                              |
| ticket_requirement| n:m Verknüpfung Ticket ↔ Anforderung             |
| ticket_commit     | n:m Verknüpfung Ticket ↔ Commit                  |
| ticket_test       | n:m Verknüpfung Ticket ↔ Test                    |
