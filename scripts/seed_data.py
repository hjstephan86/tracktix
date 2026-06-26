"""
Füllt die TrackTix-Datenbank mit realistischen Beispieldaten
(Projekte, Anforderungen, Personen, Tickets, Commits, Tests, Kommentare).

Verbindet sich über DATABASE_URL (siehe app/database.py) mit einer echten
PostgreSQL-Datenbank und schreibt die Daten dauerhaft in die DB.

Verwendung:
    python -m scripts.seed_data            # nur füllen, bricht ab wenn DB nicht leer ist
    python -m scripts.seed_data --reset    # alle Tabellen leeren und neu befüllen
"""
import argparse
import random
import secrets
import sys
from datetime import datetime, timedelta, timezone

from app.database import SessionLocal, engine
from app.models import (
    Base, Project, Requirement, Person, Ticket, Commit, Test, Comment,
    TicketStatus, TicketPriority, TestType, TestResult,
)

random.seed(42)

NOW = datetime.now(timezone.utc)


def days_ago(n: int) -> datetime:
    return NOW - timedelta(days=n, hours=random.randint(0, 23), minutes=random.randint(0, 59))


def random_sha() -> str:
    return secrets.token_hex(20)


# ── Stammdaten ──────────────────────────────────────────────────────────────

PERSONS = [
    dict(username="msommer",   full_name="Mara Sommer",     email="mara.sommer@acme.dev",     git_server="https://github.com/msommer"),
    dict(username="jkeller",   full_name="Jonas Keller",    email="jonas.keller@acme.dev",     git_server="https://github.com/jkeller"),
    dict(username="lweber",    full_name="Lena Weber",      email="lena.weber@acme.dev",       git_server="https://gitlab.com/lweber"),
    dict(username="tbrandt",   full_name="Tobias Brandt",   email="tobias.brandt@acme.dev",    git_server="https://github.com/tbrandt"),
    dict(username="sfischer",  full_name="Sophie Fischer",  email="sophie.fischer@acme.dev",   git_server="https://gitea.acme.dev/sfischer"),
    dict(username="dkoenig",   full_name="David König",     email="david.koenig@acme.dev",     git_server="https://github.com/dkoenig"),
    dict(username="anagel",    full_name="Anna Nagel",      email="anna.nagel@acme.dev",       git_server="https://gitlab.com/anagel"),
    dict(username="phartmann", full_name="Paul Hartmann",   email="paul.hartmann@acme.dev",    git_server="https://github.com/phartmann"),
]

PROJECTS = [
    dict(
        key="WEBSHOP", name="Online-Shop Relaunch",
        description="Neuentwicklung des Acme-Online-Shops mit Checkout, Produktsuche und Zahlungsanbindung.",
        git_base_url="https://github.com/acme/webshop",
    ),
    dict(
        key="MOBILE", name="Mobile App iOS/Android",
        description="Cross-Platform App für Bestellverfolgung und Push-Benachrichtigungen.",
        git_base_url="https://github.com/acme/mobile-app",
    ),
    dict(
        key="INFRA", name="Cloud-Infrastruktur Migration",
        description="Migration der On-Premise-Systeme in die Cloud inkl. CI/CD-Pipeline.",
        git_base_url="https://gitlab.com/acme/infra",
    ),
]

REQUIREMENTS = {
    "WEBSHOP": [
        dict(key="SRS-001", title="Das System muss eine Produktsuche mit Filtern bereitstellen",
             description="Volltextsuche über Produktname, Kategorie und Beschreibung mit Filterung nach Preis und Verfügbarkeit.",
             url="https://spec.acme.dev/webshop/SRS-001"),
        dict(key="SRS-002", title="Das System muss einen mehrstufigen Checkout-Prozess unterstützen",
             description="Warenkorb, Adresseingabe, Zahlungsart, Bestellbestätigung.",
             url="https://spec.acme.dev/webshop/SRS-002"),
        dict(key="SRS-003", title="Das System muss Zahlungen über mindestens drei Anbieter abwickeln",
             description="Anbindung von Kreditkarte, PayPal und Rechnungskauf.",
             url="https://spec.acme.dev/webshop/SRS-003"),
        dict(key="SRS-004", title="Das System muss Bestandsänderungen in Echtzeit anzeigen",
             description="Lagerbestand wird über Webhooks aus dem ERP synchronisiert.",
             url=""),
    ],
    "MOBILE": [
        dict(key="SRS-101", title="Die App muss Push-Benachrichtigungen für Bestellstatus senden",
             description="Statusänderungen (versandt, zugestellt) lösen eine Push-Nachricht aus.",
             url="https://spec.acme.dev/mobile/SRS-101"),
        dict(key="SRS-102", title="Die App muss offline funktionsfähig sein",
             description="Zuletzt geladene Bestellübersicht bleibt ohne Internetverbindung verfügbar.",
             url="https://spec.acme.dev/mobile/SRS-102"),
        dict(key="SRS-103", title="Die App muss Biometrische Anmeldung unterstützen",
             description="Face ID / Fingerabdruck als Alternative zum Passwort.",
             url=""),
    ],
    "INFRA": [
        dict(key="SRS-201", title="Die Plattform muss automatisiertes Deployment unterstützen",
             description="Jeder Merge auf main löst Build, Test und Deployment in Staging aus.",
             url="https://spec.acme.dev/infra/SRS-201"),
        dict(key="SRS-202", title="Die Plattform muss zentrales Logging bereitstellen",
             description="Alle Services schreiben strukturierte Logs an einen zentralen Collector.",
             url="https://spec.acme.dev/infra/SRS-202"),
        dict(key="SRS-203", title="Die Plattform muss Datenbank-Backups täglich automatisiert erstellen",
             description="Tägliches Backup mit 30 Tagen Aufbewahrung und Restore-Test.",
             url=""),
    ],
}

TICKET_TEMPLATES = {
    "WEBSHOP": [
        ("Produktsuche liefert bei Sonderzeichen keine Ergebnisse", TicketStatus.in_progress, TicketPriority.high, ["SRS-001"]),
        ("Filter nach Preis funktioniert nicht mit Komma-Werten", TicketStatus.open, TicketPriority.medium, ["SRS-001"]),
        ("Checkout: Adressformular validiert PLZ aus Österreich falsch", TicketStatus.in_review, TicketPriority.high, ["SRS-002"]),
        ("PayPal-Zahlung schlägt bei Beträgen über 1000€ fehl", TicketStatus.testing, TicketPriority.critical, ["SRS-003"]),
        ("Rechnungskauf: Bonitätsprüfung dauert zu lange", TicketStatus.open, TicketPriority.medium, ["SRS-003"]),
        ("Lagerbestand aktualisiert sich nicht nach ERP-Webhook-Timeout", TicketStatus.closed, TicketPriority.high, ["SRS-004"]),
        ("Warenkorb verliert Inhalte nach Session-Timeout", TicketStatus.open, TicketPriority.low, ["SRS-002"]),
        ("Checkout-Button bleibt auf Mobilgeräten ausgegraut", TicketStatus.rejected, TicketPriority.low, ["SRS-002"]),
    ],
    "MOBILE": [
        ("Push-Benachrichtigung kommt doppelt an", TicketStatus.in_progress, TicketPriority.medium, ["SRS-101"]),
        ("Offline-Modus zeigt veraltete Bestellliste ohne Hinweis", TicketStatus.open, TicketPriority.medium, ["SRS-102"]),
        ("Face-ID-Anmeldung schlägt auf älteren iPhones fehl", TicketStatus.testing, TicketPriority.high, ["SRS-103"]),
        ("App-Absturz beim Wechsel zwischen Tabs unter Android 12", TicketStatus.in_review, TicketPriority.critical, []),
        ("Benachrichtigungstext ist auf Englisch trotz deutscher Spracheinstellung", TicketStatus.open, TicketPriority.low, ["SRS-101"]),
    ],
    "INFRA": [
        ("Deployment-Pipeline bricht bei Migrations-Skripten ab", TicketStatus.in_progress, TicketPriority.critical, ["SRS-201"]),
        ("Zentrales Logging verliert Einträge unter hoher Last", TicketStatus.open, TicketPriority.high, ["SRS-202"]),
        ("Backup-Job läuft zweimal parallel und blockiert die DB", TicketStatus.testing, TicketPriority.high, ["SRS-203"]),
        ("Staging-Umgebung hat abweichende Umgebungsvariablen", TicketStatus.closed, TicketPriority.medium, ["SRS-201"]),
        ("Restore-Test für Backup vom Vormonat schlägt fehl", TicketStatus.open, TicketPriority.critical, ["SRS-203"]),
        ("Log-Collector benötigt zu viel Arbeitsspeicher", TicketStatus.rejected, TicketPriority.low, ["SRS-202"]),
    ],
}

COMMIT_MESSAGES = [
    "fix: korrigiere Validierung für Sonderzeichen in der Suche",
    "feat: füge Preisfilter mit Komma-Unterstützung hinzu",
    "fix: PLZ-Validierung für österreichische Adressen",
    "fix: Timeout bei PayPal-Zahlungen über 1000€ erhöht",
    "feat: Bonitätsprüfung asynchron auslagern",
    "fix: ERP-Webhook-Retry bei Timeout implementiert",
    "fix: Warenkorb-Session-Handling überarbeitet",
    "feat: Push-Benachrichtigungen deduplizieren",
    "fix: Offline-Cache-Hinweis im Bestellverlauf ergänzt",
    "fix: Face-ID-Fallback für ältere iOS-Versionen",
    "fix: Tab-Wechsel-Absturz unter Android 12 behoben",
    "feat: Migrations-Skripte in Pipeline robuster gemacht",
    "fix: Logging-Pufferung unter Lastspitzen verbessert",
    "fix: Backup-Job Lock hinzugefügt gegen Doppelausführung",
    "feat: Restore-Test automatisiert in Backup-Pipeline integriert",
]

TEST_TEMPLATES = [
    ("Unit-Test: Suchindex mit Sonderzeichen", TestType.unit, TestResult.passed),
    ("Unit-Test: Preisfilter mit Komma-Werten", TestType.unit, TestResult.failed),
    ("Integrationstest: Checkout mit österreichischer Adresse", TestType.integration, TestResult.passed),
    ("Systemtest: PayPal-Zahlung über 1000€", TestType.system, TestResult.failed),
    ("Integrationstest: Bonitätsprüfung Antwortzeit", TestType.integration, TestResult.pending),
    ("Systemtest: ERP-Webhook-Synchronisation", TestType.system, TestResult.passed),
    ("Unit-Test: Push-Benachrichtigung Deduplizierung", TestType.unit, TestResult.passed),
    ("Integrationstest: Offline-Cache Bestellliste", TestType.integration, TestResult.pending),
    ("Systemtest: Face-ID-Anmeldung auf älteren Geräten", TestType.system, TestResult.failed),
    ("Systemtest: Deployment-Pipeline mit Migrationen", TestType.system, TestResult.passed),
    ("Integrationstest: Zentrales Logging unter Last", TestType.integration, TestResult.failed),
    ("Systemtest: Backup- und Restore-Vorgang", TestType.system, TestResult.pending),
]

COMMENT_TEMPLATES = [
    "Kann das Problem reproduzieren, schaue mir das heute noch an.",
    "Fix ist in Review, sollte morgen deploybar sein.",
    "Betrifft offenbar nur Nutzer mit aktiviertem Cache.",
    "Habe Logs angehängt, siehe Link im Ticket.",
    "Nach Rücksprache mit dem Kunden ist das kein Blocker mehr.",
    "Test in Staging erfolgreich, bitte für Produktion freigeben.",
    "Brauchen wir hierfür ein Hotfix-Release?",
    "Ursache gefunden: Race Condition beim parallelen Zugriff.",
]


def get_or_create_person(db, data: dict) -> Person:
    p = db.query(Person).filter_by(username=data["username"]).first()
    if p:
        return p
    p = Person(**data)
    db.add(p)
    db.flush()
    return p


def seed(db) -> None:
    persons = [get_or_create_person(db, data) for data in PERSONS]

    projects: dict[str, Project] = {}
    requirements: dict[str, dict[str, Requirement]] = {}

    for pdata in PROJECTS:
        project = Project(**pdata)
        db.add(project)
        db.flush()
        projects[pdata["key"]] = project

        requirements[pdata["key"]] = {}
        for rdata in REQUIREMENTS[pdata["key"]]:
            req = Requirement(project_id=project.id, **rdata)
            db.add(req)
            db.flush()
            requirements[pdata["key"]][rdata["key"]] = req

    all_commits: list[Commit] = []
    all_tests: list[Test] = []

    for i, msg in enumerate(COMMIT_MESSAGES):
        author = random.choice(persons)
        sha = random_sha()
        commit = Commit(
            sha=sha,
            message=msg,
            author_id=author.id,
            git_url=f"{random.choice(PROJECTS)['git_base_url']}/commit/{sha}",
            committed_at=days_ago(random.randint(1, 60)),
        )
        db.add(commit)
        db.flush()
        all_commits.append(commit)

    for title, ttype, result in TEST_TEMPLATES:
        tester = random.choice(persons)
        test = Test(
            title=title,
            description=f"Automatisierter {ttype.value}-Test im Rahmen der QA-Pipeline.",
            test_type=ttype,
            result=result,
            tester_id=tester.id,
            run_at=days_ago(random.randint(0, 30)) if result != TestResult.pending else None,
        )
        db.add(test)
        db.flush()
        all_tests.append(test)

    commit_pool = list(all_commits)
    test_pool = list(all_tests)

    for project_key, tickets in TICKET_TEMPLATES.items():
        project = projects[project_key]
        for idx, (title, status, priority, req_keys) in enumerate(tickets, start=1):
            assignee = random.choice(persons) if random.random() > 0.1 else None
            ticket = Ticket(
                project_id=project.id,
                key=f"{project.key}-{idx}",
                title=title,
                description=f"Gemeldet im Rahmen von {project.name}. Priorität: {priority.value}.",
                status=status,
                priority=priority,
                assignee_id=assignee.id if assignee else None,
                requirements=[requirements[project_key][k] for k in req_keys],
            )
            db.add(ticket)
            db.flush()

            if status in (TicketStatus.in_review, TicketStatus.testing, TicketStatus.closed):
                if commit_pool:
                    ticket.commits.append(commit_pool.pop(0))
            if status in (TicketStatus.testing, TicketStatus.closed):
                if test_pool:
                    ticket.tests.append(test_pool.pop(0))

            for _ in range(random.randint(0, 3)):
                author = random.choice(persons) if random.random() > 0.2 else None
                comment = Comment(
                    ticket_id=ticket.id,
                    author_id=author.id if author else None,
                    body=random.choice(COMMENT_TEMPLATES),
                )
                db.add(comment)

    db.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true",
                         help="Alle Tabellen vor dem Befüllen leeren (DESTRUKTIV)")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing_projects = db.query(Project).count()
        if existing_projects > 0 and not args.reset:
            print(f"Datenbank enthält bereits {existing_projects} Projekt(e). "
                  "Mit --reset alle Daten löschen und neu befüllen, oder "
                  "manuell aufräumen.", file=sys.stderr)
            sys.exit(1)

        if args.reset:
            print("Leere alle Tabellen (--reset)...")
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)

        print("Befülle Datenbank mit Beispieldaten...")
        seed(db)
        print(
            f"Fertig: {len(PROJECTS)} Projekte, "
            f"{sum(len(r) for r in REQUIREMENTS.values())} Anforderungen, "
            f"{len(PERSONS)} Personen, "
            f"{sum(len(t) for t in TICKET_TEMPLATES.values())} Tickets, "
            f"{len(COMMIT_MESSAGES)} Commits, {len(TEST_TEMPLATES)} Tests angelegt."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
