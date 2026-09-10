"""CRUD-Zugriff auf bewerbungen und interview_runden."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime

from .database import einstellung_int
from .models import Bewerbung, InterviewRunde, Rueckmeldung, Status
from .status import status_berechnen


# --- Konvertierung -----------------------------------------------------------


def _datum_lesen(wert: str | None) -> date | None:
    if not wert:
        return None
    try:
        return date.fromisoformat(str(wert)[:10])
    except ValueError:
        return None


def _datum_schreiben(wert: date | None) -> str | None:
    return wert.isoformat() if wert else None


def _zeitstempel_lesen(wert: str | None) -> datetime | None:
    if not wert:
        return None
    try:
        return datetime.fromisoformat(str(wert))
    except ValueError:
        return None


def _liste_lesen(wert: str | None) -> list[str]:
    if not wert:
        return []
    try:
        daten = json.loads(wert)
    except (TypeError, ValueError):
        return []
    return [str(e) for e in daten] if isinstance(daten, list) else []


def _zeile_zu_bewerbung(zeile: sqlite3.Row) -> Bewerbung:
    rueckmeldung = zeile["rueckmeldung_typ"]
    return Bewerbung(
        id=zeile["id"],
        profil_id=zeile["profil_id"],
        firma=zeile["firma"] or "",
        position=zeile["position"] or "",
        bewerbungsweg=zeile["bewerbungsweg"] or "",
        beworben_am=_datum_lesen(zeile["beworben_am"]),
        status=Status(zeile["status"]) if zeile["status"] else Status.BEWORBEN,
        skills=_liste_lesen(zeile["skills"]),
        gehaltsangabe=zeile["gehaltsangabe"] or "",
        cv_pfad=zeile["cv_pfad"] or "",
        anschreiben_pfad=zeile["anschreiben_pfad"] or "",
        absagegrund_kategorien=_liste_lesen(zeile["absagegrund_kategorien"]),
        absagegrund_details=zeile["absagegrund_details"] or "",
        absage_rohtext=zeile["absage_rohtext"] or "",
        notizen=zeile["notizen"] or "",
        quelle_url=zeile["quelle_url"] or "",
        rueckmeldung_typ=Rueckmeldung(rueckmeldung) if rueckmeldung else None,
        rueckmeldung_am=_datum_lesen(zeile["rueckmeldung_am"]),
        letzte_aktualisierung=_zeitstempel_lesen(zeile["letzte_aktualisierung"]),
    )


def _zeile_zu_runde(zeile: sqlite3.Row) -> InterviewRunde:
    return InterviewRunde(
        id=zeile["id"],
        bewerbung_id=zeile["bewerbung_id"],
        runde_nummer=zeile["runde_nummer"],
        typ=zeile["typ"] or "",
        datum=_datum_lesen(zeile["datum"]),
        ergebnis=zeile["ergebnis"] or "",
        notizen=zeile["notizen"] or "",
    )


# --- Filter ------------------------------------------------------------------


@dataclass
class Filter:
    """Filter fuer die Kanban-Ansicht (Abschnitt 9): Firma, Status, Zeitraum."""

    suchtext: str = ""
    status: set[Status] | None = None
    von: date | None = None
    bis: date | None = None

    def passt(self, bewerbung: Bewerbung) -> bool:
        if self.suchtext:
            nadel = self.suchtext.casefold()
            heuhaufen = " ".join(
                [bewerbung.firma, bewerbung.position, " ".join(bewerbung.skills)]
            ).casefold()
            if nadel not in heuhaufen:
                return False
        if self.status is not None and bewerbung.status not in self.status:
            return False
        if self.von and (not bewerbung.beworben_am or bewerbung.beworben_am < self.von):
            return False
        if self.bis and (not bewerbung.beworben_am or bewerbung.beworben_am > self.bis):
            return False
        return True


# --- Lesen -------------------------------------------------------------------


def runden_laden(conn: sqlite3.Connection, bewerbung_id: int) -> list[InterviewRunde]:
    zeilen = conn.execute(
        "SELECT * FROM interview_runden WHERE bewerbung_id = ?"
        " ORDER BY runde_nummer, COALESCE(datum, ?), id",
        (bewerbung_id, ""),
    ).fetchall()
    return [_zeile_zu_runde(z) for z in zeilen]


def bewerbung_laden(conn: sqlite3.Connection, bewerbung_id: int) -> Bewerbung | None:
    zeile = conn.execute(
        "SELECT * FROM bewerbungen WHERE id = ?", (bewerbung_id,)
    ).fetchone()
    if zeile is None:
        return None
    bewerbung = _zeile_zu_bewerbung(zeile)
    bewerbung.interview_runden = runden_laden(conn, bewerbung_id)
    if _status_synchronisieren(conn, bewerbung):
        conn.commit()
    return bewerbung


def alle_bewerbungen(
    conn: sqlite3.Connection,
    filter_: Filter | None = None,
    profil_id: int = 1,
) -> list[Bewerbung]:
    """Laedt alle Bewerbungen inkl. Runden und haelt den Status aktuell."""
    zeilen = conn.execute(
        "SELECT * FROM bewerbungen WHERE profil_id = ?"
        " ORDER BY COALESCE(beworben_am, ?) DESC, id DESC",
        (profil_id, ""),
    ).fetchall()
    bewerbungen = [_zeile_zu_bewerbung(z) for z in zeilen]

    runden_je_bewerbung: dict[int, list[InterviewRunde]] = {}
    for zeile in conn.execute(
        "SELECT * FROM interview_runden ORDER BY runde_nummer, COALESCE(datum, ?), id",
        ("",),
    ):
        runde = _zeile_zu_runde(zeile)
        runden_je_bewerbung.setdefault(runde.bewerbung_id, []).append(runde)

    geaendert = False
    for bewerbung in bewerbungen:
        bewerbung.interview_runden = runden_je_bewerbung.get(bewerbung.id, [])
        geaendert |= _status_synchronisieren(conn, bewerbung)
    if geaendert:
        conn.commit()

    if filter_ is None:
        return bewerbungen
    return [b for b in bewerbungen if filter_.passt(b)]


def _status_synchronisieren(conn: sqlite3.Connection, bewerbung: Bewerbung) -> bool:
    """Berechnet den Status neu und schreibt ihn bei Abweichung zurueck."""
    ghosting_tage = einstellung_int(conn, "ghosting_tage", 30)
    neuer_status = status_berechnen(bewerbung, ghosting_tage)
    if neuer_status == bewerbung.status:
        return False
    bewerbung.status = neuer_status
    conn.execute(
        "UPDATE bewerbungen SET status = ? WHERE id = ?",
        (neuer_status.value, bewerbung.id),
    )
    return True


# --- Schreiben ---------------------------------------------------------------

_SPALTEN = [
    "profil_id",
    "firma",
    "position",
    "bewerbungsweg",
    "beworben_am",
    "status",
    "skills",
    "gehaltsangabe",
    "cv_pfad",
    "anschreiben_pfad",
    "absagegrund_kategorien",
    "absagegrund_details",
    "absage_rohtext",
    "notizen",
    "quelle_url",
    "rueckmeldung_typ",
    "rueckmeldung_am",
    "letzte_aktualisierung",
]


def _werte(bewerbung: Bewerbung) -> tuple:
    return (
        bewerbung.profil_id,
        bewerbung.firma,
        bewerbung.position,
        bewerbung.bewerbungsweg,
        _datum_schreiben(bewerbung.beworben_am),
        bewerbung.status.value,
        json.dumps(bewerbung.skills, ensure_ascii=False),
        bewerbung.gehaltsangabe,
        bewerbung.cv_pfad,
        bewerbung.anschreiben_pfad,
        json.dumps(bewerbung.absagegrund_kategorien, ensure_ascii=False),
        bewerbung.absagegrund_details,
        bewerbung.absage_rohtext,
        bewerbung.notizen,
        bewerbung.quelle_url,
        bewerbung.rueckmeldung_typ.value if bewerbung.rueckmeldung_typ else None,
        _datum_schreiben(bewerbung.rueckmeldung_am),
        datetime.now().isoformat(timespec="seconds"),
    )


def bewerbung_speichern(conn: sqlite3.Connection, bewerbung: Bewerbung) -> int:
    """Legt eine Bewerbung an oder aktualisiert sie. Gibt die ID zurueck."""
    ghosting_tage = einstellung_int(conn, "ghosting_tage", 30)
    bewerbung.status = status_berechnen(bewerbung, ghosting_tage)

    if bewerbung.id is None:
        spalten = ", ".join(_SPALTEN)
        platzhalter = ", ".join(["?"] * len(_SPALTEN))
        cursor = conn.execute(
            "INSERT INTO bewerbungen (" + spalten + ") VALUES (" + platzhalter + ")",
            _werte(bewerbung),
        )
        bewerbung.id = int(cursor.lastrowid)
    else:
        zuweisungen = ", ".join(spalte + " = ?" for spalte in _SPALTEN)
        conn.execute(
            "UPDATE bewerbungen SET " + zuweisungen + " WHERE id = ?",
            (*_werte(bewerbung), bewerbung.id),
        )
    conn.commit()
    return bewerbung.id


def bewerbung_loeschen(conn: sqlite3.Connection, bewerbung_id: int) -> None:
    conn.execute("DELETE FROM bewerbungen WHERE id = ?", (bewerbung_id,))
    conn.commit()


def naechste_rundennummer(conn: sqlite3.Connection, bewerbung_id: int) -> int:
    zeile = conn.execute(
        "SELECT COALESCE(MAX(runde_nummer), 0) AS n FROM interview_runden"
        " WHERE bewerbung_id = ?",
        (bewerbung_id,),
    ).fetchone()
    return int(zeile["n"]) + 1


def runde_speichern(conn: sqlite3.Connection, runde: InterviewRunde) -> int:
    if runde.id is None:
        cursor = conn.execute(
            "INSERT INTO interview_runden"
            " (bewerbung_id, runde_nummer, typ, datum, ergebnis, notizen)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                runde.bewerbung_id,
                runde.runde_nummer,
                runde.typ,
                _datum_schreiben(runde.datum),
                runde.ergebnis,
                runde.notizen,
            ),
        )
        runde.id = int(cursor.lastrowid)
    else:
        conn.execute(
            "UPDATE interview_runden SET runde_nummer = ?, typ = ?, datum = ?,"
            " ergebnis = ?, notizen = ? WHERE id = ?",
            (
                runde.runde_nummer,
                runde.typ,
                _datum_schreiben(runde.datum),
                runde.ergebnis,
                runde.notizen,
                runde.id,
            ),
        )
    conn.execute(
        "UPDATE bewerbungen SET letzte_aktualisierung = ? WHERE id = ?",
        (datetime.now().isoformat(timespec="seconds"), runde.bewerbung_id),
    )
    conn.commit()
    return runde.id


def runde_loeschen(conn: sqlite3.Connection, runde_id: int) -> None:
    conn.execute("DELETE FROM interview_runden WHERE id = ?", (runde_id,))
    conn.commit()


def rueckmeldung_setzen(
    conn: sqlite3.Connection,
    bewerbung_id: int,
    typ: Rueckmeldung | None,
    am: date | None = None,
    kategorien: list[str] | None = None,
    details: str = "",
    rohtext: str = "",
) -> None:
    """Traegt eine finale Rueckmeldung ein oder entfernt sie (typ=None)."""
    bewerbung = bewerbung_laden(conn, bewerbung_id)
    if bewerbung is None:
        return
    bewerbung.rueckmeldung_typ = typ
    bewerbung.rueckmeldung_am = am if typ else None
    if typ == Rueckmeldung.ABSAGE:
        bewerbung.absagegrund_kategorien = kategorien or []
        bewerbung.absagegrund_details = details
        bewerbung.absage_rohtext = rohtext
    elif typ is None:
        bewerbung.absagegrund_kategorien = []
        bewerbung.absagegrund_details = ""
        bewerbung.absage_rohtext = ""
    bewerbung_speichern(conn, bewerbung)
