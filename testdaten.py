"""Legt Beispieldaten an, um die Oberflaeche mit gefuellten Spalten zu testen.

Aufruf::

    .venv\\Scripts\\python.exe testdaten.py            # in die echte Datenbank
    BEWERBUNGSTRACKER_DIR=... python testdaten.py     # in ein Testverzeichnis

Bereits vorhandene Datensaetze bleiben unberuehrt; das Skript legt nur an.
"""

from __future__ import annotations

from datetime import date, timedelta

from app import database, repository
from app.models import Bewerbung, InterviewRunde, Rueckmeldung

HEUTE = date.today()


def _tage(anzahl: int) -> date:
    return HEUTE - timedelta(days=anzahl)


BEISPIELE: list[tuple[Bewerbung, list[InterviewRunde]]] = [
    (
        Bewerbung(
            firma="Nordlicht Energie GmbH",
            position="Projektmanager Erneuerbare Energien",
            bewerbungsweg="Jobportal",
            beworben_am=_tage(6),
            skills=["Projektmanagement", "MS Project", "Vertragsrecht"],
            gehaltsangabe="65.000 – 78.000 EUR",
            notizen="Stellenanzeige über StepStone gefunden.",
        ),
        [],
    ),
    (
        Bewerbung(
            firma="Hansa Logistik AG",
            position="Teamleiter Disposition",
            bewerbungsweg="Empfehlung",
            beworben_am=_tage(24),
            skills=["Disposition", "SAP TM", "Führung"],
            notizen="Kontakt über ehemaligen Kollegen.",
        ),
        [
            InterviewRunde(runde_nummer=1, typ="Telefon", datum=_tage(17),
                           ergebnis="Weiter in nächste Runde"),
            InterviewRunde(runde_nummer=2, typ="Video", datum=_tage(9),
                           ergebnis="Offen", notizen="Case-Study zur Tourenplanung."),
        ],
    ),
    (
        Bewerbung(
            firma="Stadtwerke Lüneburg",
            position="Referent Netzwirtschaft",
            bewerbungsweg="E-Mail",
            beworben_am=_tage(41),
            skills=["Regulierung", "Excel", "Berichtswesen"],
        ),
        [],
    ),
    (
        Bewerbung(
            firma="Blaupunkt Systems",
            position="Produktmanager Sensorik",
            bewerbungsweg="Jobportal",
            beworben_am=_tage(58),
            skills=["Produktmanagement", "Roadmapping", "Englisch"],
            rueckmeldung_typ=Rueckmeldung.ABSAGE,
            rueckmeldung_am=_tage(31),
            absagegrund_kategorien=["Erfahrung/Seniorität", "Gehaltsvorstellung"],
            absagegrund_details="Mehr Führungserfahrung gewünscht, Gehalt über Budget.",
            absage_rohtext="… haben wir uns für eine Kandidatin mit umfangreicherer "
            "Führungserfahrung entschieden …",
        ),
        [
            InterviewRunde(runde_nummer=1, typ="Video", datum=_tage(44),
                           ergebnis="Weiter in nächste Runde"),
            InterviewRunde(runde_nummer=2, typ="Vor-Ort", datum=_tage(36),
                           ergebnis="Absage"),
        ],
    ),
    (
        Bewerbung(
            firma="Kontor Software",
            position="Business Analyst",
            bewerbungsweg="Initiativbewerbung",
            beworben_am=_tage(75),
            skills=["SQL", "Anforderungsanalyse", "BPMN"],
            rueckmeldung_typ=Rueckmeldung.ABSAGE,
            rueckmeldung_am=_tage(62),
            absagegrund_kategorien=["Position anderweitig besetzt"],
            absagegrund_details="Stelle intern besetzt.",
        ),
        [],
    ),
    (
        Bewerbung(
            firma="Weserwerft Bremen",
            position="Einkäufer Technik",
            bewerbungsweg="Jobportal",
            beworben_am=_tage(90),
            skills=["Einkauf", "Verhandlung", "SAP MM"],
            rueckmeldung_typ=Rueckmeldung.ABSAGE,
            rueckmeldung_am=_tage(70),
            absagegrund_kategorien=["Fachliche Skills", "Kein Feedback erhalten"],
        ),
        [],
    ),
    (
        Bewerbung(
            firma="Marschland Consulting",
            position="Consultant Prozessoptimierung",
            bewerbungsweg="Empfehlung",
            beworben_am=_tage(52),
            skills=["Lean", "Moderation", "Change Management"],
            rueckmeldung_typ=Rueckmeldung.ZUSAGE,
            rueckmeldung_am=_tage(12),
            notizen="Vertrag liegt vor, Start zum Quartalsbeginn.",
        ),
        [
            InterviewRunde(runde_nummer=1, typ="Telefon", datum=_tage(45),
                           ergebnis="Weiter in nächste Runde"),
            InterviewRunde(runde_nummer=2, typ="Assessment-Center", datum=_tage(30),
                           ergebnis="Weiter in nächste Runde"),
            InterviewRunde(runde_nummer=3, typ="Vor-Ort", datum=_tage(18),
                           ergebnis="Zusage"),
        ],
    ),
]


def main() -> None:
    conn = database.verbinden()
    vorhandene = {
        (b.firma, b.position) for b in repository.alle_bewerbungen(conn)
    }
    angelegt = 0
    for bewerbung, runden in BEISPIELE:
        if (bewerbung.firma, bewerbung.position) in vorhandene:
            continue
        bewerbung_id = repository.bewerbung_speichern(conn, bewerbung)
        for runde in runden:
            runde.bewerbung_id = bewerbung_id
            repository.runde_speichern(conn, runde)
        angelegt += 1
    conn.close()
    print(f"{angelegt} Beispiel-Bewerbungen angelegt ({database.datenbank_pfad()}).")


if __name__ == "__main__":
    main()
