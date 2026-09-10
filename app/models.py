"""Datenmodell: Enums, Konstanten und Dataclasses (Spezifikation Abschnitt 3, 4, 6)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum


# --- Abschnitt 3: bewerbungsweg ---------------------------------------------

BEWERBUNGSWEGE: list[str] = [
    "Jobportal",
    "E-Mail",
    "Initiativbewerbung",
    "Empfehlung",
]


# --- Abschnitt 4: Status-Workflow -------------------------------------------


class Status(str, Enum):
    BEWORBEN = "Beworben"
    INTERVIEW = "Im Interview-Prozess"
    ZUSAGE = "Zusage"
    ABSAGE = "Absage"
    GHOSTING = "Ghosting/Keine Rückmeldung"


#: Spaltenreihenfolge im Kanban-Board.
STATUS_REIHENFOLGE: list[Status] = [
    Status.BEWORBEN,
    Status.INTERVIEW,
    Status.ZUSAGE,
    Status.ABSAGE,
    Status.GHOSTING,
]

#: Status, bei denen die Bewerbung noch als "offen" gilt.
OFFENE_STATUS: set[Status] = {Status.BEWORBEN, Status.INTERVIEW, Status.GHOSTING}


class Rueckmeldung(str, Enum):
    """Explizit vom Nutzer eingetragene finale Rückmeldung."""

    ZUSAGE = "Zusage"
    ABSAGE = "Absage"


# --- Abschnitt 6: Absagegrund-Kategorien ------------------------------------

ABSAGEGRUND_KATEGORIEN: list[str] = [
    "Erfahrung/Seniorität",
    "Fachliche Skills",
    "Gehaltsvorstellung",
    "Kultureller Fit",
    "Position anderweitig besetzt",
    "Zu späte Bewerbung",
    "Formale Gründe",
    "Kein Feedback erhalten",
    "Sonstiges",
]


# --- Interview-Runden --------------------------------------------------------

INTERVIEW_TYPEN: list[str] = [
    "Telefon",
    "Video",
    "Vor-Ort",
    "Assessment-Center",
    "Sonstiges",
]

INTERVIEW_ERGEBNISSE: list[str] = [
    "Offen",
    "Weiter in nächste Runde",
    "Zusage",
    "Absage",
    "Abgebrochen",
]


@dataclass
class InterviewRunde:
    id: int | None = None
    bewerbung_id: int | None = None
    runde_nummer: int = 1
    typ: str = INTERVIEW_TYPEN[0]
    datum: date | None = None
    ergebnis: str = INTERVIEW_ERGEBNISSE[0]
    notizen: str = ""

    def anzeigename(self) -> str:
        datum = self.datum.strftime("%d.%m.%Y") if self.datum else "ohne Datum"
        return f"Runde {self.runde_nummer} · {self.typ} · {datum}"


@dataclass
class Bewerbung:
    id: int | None = None
    firma: str = ""
    position: str = ""
    bewerbungsweg: str = BEWERBUNGSWEGE[0]
    beworben_am: date | None = None
    status: Status = Status.BEWORBEN
    skills: list[str] = field(default_factory=list)
    gehaltsangabe: str = ""
    cv_pfad: str = ""
    anschreiben_pfad: str = ""
    absagegrund_kategorien: list[str] = field(default_factory=list)
    absage_rohtext: str = ""
    notizen: str = ""
    letzte_aktualisierung: datetime | None = None
    quelle_url: str = ""
    # Explizite Rückmeldung -- Voraussetzung für die Statusableitung nach
    # Abschnitt 4 ("expliziter Rückmeldungs-Eintrag durch den Nutzer").
    rueckmeldung_typ: Rueckmeldung | None = None
    rueckmeldung_am: date | None = None
    absagegrund_details: str = ""
    # Vorbereitet für spätere Multi-Profil-Unterstützung (Abschnitt 11).
    profil_id: int = 1
    # Nicht persistiert -- zur Laufzeit aus interview_runden befüllt.
    interview_runden: list[InterviewRunde] = field(default_factory=list)

    def anzeigename(self) -> str:
        teile = [t for t in (self.firma, self.position) if t]
        return " – ".join(teile) or "(ohne Bezeichnung)"
