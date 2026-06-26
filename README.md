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

```bash
# PostgreSQL muss laufen
createdb tracktix
createuser tracktix -P  # Passwort: tracktix

pip install -r requirements.txt

export DATABASE_URL=postgresql://tracktix:tracktix@localhost:5432/tracktix
uvicorn app.main:app --reload
# → http://localhost:8000
```

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
