"""Statusableitung (Abschnitt 4) und Nachfrage-/Reminder-Logik (Abschnitt 7).

Der Gesamtstatus einer Bewerbung wird nie manuell gesetzt, sondern immer aus
den vorhandenen Daten berechnet:

* explizite Rückmeldung  -> Zusage / Absage
* Tage ohne Reaktion > Ghosting-Schwelle -> Ghosting/Keine Rückmeldung
* mindestens eine Interview-Runde -> Im Interview-Prozess
* sonst -> Beworben
"""

from __future__ import annotations

from datetime import date

from .models import OFFENE_STATUS, Bewerbung, Rueckmeldung, Status


def letztes_ereignis(bewerbung: Bewerbung) -> date | None:
    """Datum des letzten Ereignisses, auf das keine Reaktion folgte.

    Ohne Interview-Runden ist das der Bewerbungstag, sonst die letzte Runde
    (Abschnitt 7: der Zähler startet nach der letzten Interview-Runde neu).
    """
    kandidaten = [d for d in (r.datum for r in bewerbung.interview_runden) if d]
    if bewerbung.beworben_am:
        kandidaten.append(bewerbung.beworben_am)
    return max(kandidaten) if kandidaten else None


def tage_ohne_reaktion(bewerbung: Bewerbung, heute: date | None = None) -> int | None:
    """Tage seit dem letzten Ereignis; None, wenn kein Datum bekannt ist."""
    basis = letztes_ereignis(bewerbung)
    if basis is None:
        return None
    return max(0, ((heute or date.today()) - basis).days)


def status_berechnen(
    bewerbung: Bewerbung,
    ghosting_tage: int,
    heute: date | None = None,
) -> Status:
    if bewerbung.rueckmeldung_typ == Rueckmeldung.ZUSAGE:
        return Status.ZUSAGE
    if bewerbung.rueckmeldung_typ == Rueckmeldung.ABSAGE:
        return Status.ABSAGE

    tage = tage_ohne_reaktion(bewerbung, heute)
    if tage is not None and ghosting_tage > 0 and tage >= ghosting_tage:
        return Status.GHOSTING
    if bewerbung.interview_runden:
        return Status.INTERVIEW
    return Status.BEWORBEN


def nachfragen_empfohlen(
    bewerbung: Bewerbung,
    reminder_tage: int,
    heute: date | None = None,
) -> bool:
    """True, wenn die Bewerbung offen ist und der Schwellenwert erreicht wurde."""
    if bewerbung.status not in OFFENE_STATUS:
        return False
    tage = tage_ohne_reaktion(bewerbung, heute)
    return tage is not None and reminder_tage > 0 and tage >= reminder_tage
