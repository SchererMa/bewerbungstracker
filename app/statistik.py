"""Auswertungen fuer das Dashboard (Spezifikation Abschnitt 8)."""

from __future__ import annotations

from collections import Counter
from datetime import date

from .models import OFFENE_STATUS, Bewerbung, Status
from .status import nachfragen_empfohlen, tage_ohne_reaktion

#: Gruppierung fuer das Kreisdiagramm "Zusage / Absage / Offen / Ghosting".
KREIS_GRUPPEN: list[str] = ["Zusage", "Absage", "Offen", "Ghosting"]


def kreis_gruppe(status: Status) -> str:
    if status is Status.ZUSAGE:
        return "Zusage"
    if status is Status.ABSAGE:
        return "Absage"
    if status is Status.GHOSTING:
        return "Ghosting"
    return "Offen"


def status_verteilung(bewerbungen: list[Bewerbung]) -> dict[str, int]:
    """Anzahl je Kreisdiagramm-Gruppe -- Gruppen ohne Treffer bleiben auf 0."""
    zaehler = Counter(kreis_gruppe(b.status) for b in bewerbungen)
    return {gruppe: zaehler.get(gruppe, 0) for gruppe in KREIS_GRUPPEN}


def absagegruende(bewerbungen: list[Bewerbung]) -> list[tuple[str, int]]:
    """Haeufigkeit der Absagegrund-Kategorien, absteigend sortiert.

    Mehrfachnennungen pro Absage sind erlaubt (Abschnitt 6), jede Kategorie
    zaehlt daher einzeln.
    """
    zaehler: Counter[str] = Counter()
    for bewerbung in bewerbungen:
        if bewerbung.status is not Status.ABSAGE:
            continue
        for kategorie in bewerbung.absagegrund_kategorien:
            zaehler[kategorie] += 1
    return sorted(zaehler.items(), key=lambda paar: (-paar[1], paar[0]))


def offene_bewerbungen(
    bewerbungen: list[Bewerbung],
    heute: date | None = None,
) -> list[tuple[Bewerbung, int | None]]:
    """Offene Bewerbungen mit Alter in Tagen, aelteste zuerst."""
    offen = [b for b in bewerbungen if b.status in OFFENE_STATUS]
    mit_alter = [(b, tage_ohne_reaktion(b, heute)) for b in offen]
    return sorted(mit_alter, key=lambda paar: (paar[1] is None, -(paar[1] or 0)))


def nachfassliste(
    bewerbungen: list[Bewerbung],
    reminder_tage: int,
    heute: date | None = None,
) -> list[tuple[Bewerbung, int | None]]:
    """Bewerbungen, bei denen Nachfragen empfohlen wird (Abschnitt 7)."""
    treffer = [b for b in bewerbungen if nachfragen_empfohlen(b, reminder_tage, heute)]
    mit_alter = [(b, tage_ohne_reaktion(b, heute)) for b in treffer]
    return sorted(mit_alter, key=lambda paar: -(paar[1] or 0))


def kennzahlen(bewerbungen: list[Bewerbung], reminder_tage: int) -> dict[str, int]:
    verteilung = status_verteilung(bewerbungen)
    return {
        "gesamt": len(bewerbungen),
        "offen": verteilung["Offen"],
        "ghosting": verteilung["Ghosting"],
        "zusagen": verteilung["Zusage"],
        "absagen": verteilung["Absage"],
        "nachfassen": len(nachfassliste(bewerbungen, reminder_tage)),
    }
