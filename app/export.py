"""CSV-Export der gesamten Bewerbungsdaten (Spezifikation Abschnitt 9)."""

from __future__ import annotations

import csv
from pathlib import Path

from .models import Bewerbung
from .status import tage_ohne_reaktion

SPALTEN: list[str] = [
    "id",
    "firma",
    "position",
    "bewerbungsweg",
    "beworben_am",
    "status",
    "tage_ohne_reaktion",
    "skills",
    "gehaltsangabe",
    "cv_pfad",
    "anschreiben_pfad",
    "anzahl_interview_runden",
    "letzte_interview_runde",
    "rueckmeldung_typ",
    "rueckmeldung_am",
    "absagegrund_kategorien",
    "absagegrund_details",
    "absage_rohtext",
    "notizen",
    "quelle_url",
    "letzte_aktualisierung",
]


def _zeile(bewerbung: Bewerbung) -> dict[str, str]:
    runden = bewerbung.interview_runden
    letzte = max((r.datum for r in runden if r.datum), default=None)
    return {
        "id": str(bewerbung.id or ""),
        "firma": bewerbung.firma,
        "position": bewerbung.position,
        "bewerbungsweg": bewerbung.bewerbungsweg,
        "beworben_am": bewerbung.beworben_am.isoformat() if bewerbung.beworben_am else "",
        "status": bewerbung.status.value,
        "tage_ohne_reaktion": str(tage_ohne_reaktion(bewerbung) or ""),
        "skills": "; ".join(bewerbung.skills),
        "gehaltsangabe": bewerbung.gehaltsangabe,
        "cv_pfad": bewerbung.cv_pfad,
        "anschreiben_pfad": bewerbung.anschreiben_pfad,
        "anzahl_interview_runden": str(len(runden)),
        "letzte_interview_runde": letzte.isoformat() if letzte else "",
        "rueckmeldung_typ": (
            bewerbung.rueckmeldung_typ.value if bewerbung.rueckmeldung_typ else ""
        ),
        "rueckmeldung_am": (
            bewerbung.rueckmeldung_am.isoformat() if bewerbung.rueckmeldung_am else ""
        ),
        "absagegrund_kategorien": "; ".join(bewerbung.absagegrund_kategorien),
        "absagegrund_details": bewerbung.absagegrund_details,
        "absage_rohtext": bewerbung.absage_rohtext.replace("\n", " ").strip(),
        "notizen": bewerbung.notizen.replace("\n", " ").strip(),
        "quelle_url": bewerbung.quelle_url,
        "letzte_aktualisierung": (
            bewerbung.letzte_aktualisierung.isoformat(sep=" ", timespec="seconds")
            if bewerbung.letzte_aktualisierung
            else ""
        ),
    }


def csv_schreiben(pfad: Path | str, bewerbungen: list[Bewerbung]) -> int:
    """Schreibt alle Bewerbungen als CSV. Gibt die Anzahl Zeilen zurueck.

    Trennzeichen ist das Semikolon und die Datei bekommt ein UTF-8-BOM, damit
    Excel unter Windows Umlaute und Spalten korrekt erkennt.
    """
    pfad = Path(pfad)
    with pfad.open("w", encoding="utf-8-sig", newline="") as datei:
        writer = csv.DictWriter(datei, fieldnames=SPALTEN, delimiter=";")
        writer.writeheader()
        for bewerbung in bewerbungen:
            writer.writerow(_zeile(bewerbung))
    return len(bewerbungen)
