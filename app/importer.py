"""JSON-Import der KI-Extraktion (Spezifikation Abschnitt 5).

Es gibt zwei getrennte Formate ohne gemeinsame Struktur:

Format A (Stellenanzeige) legt eine **neue** Bewerbung an::

    {"firma": "...", "position": "...", "skills": ["..."],
     "gehaltsangabe": "... oder null", "bewerbungsweg_hinweis": "... oder null",
     "quelle_url": "... oder null"}

Format B (Absage) wird beim Import **manuell** einer bestehenden Bewerbung
zugeordnet -- die Datei enthaelt bewusst keine Referenz::

    {"absagegrund_kategorien": ["..."], "absagegrund_details": "...",
     "rohtext": "...", "datum": "YYYY-MM-DD"}
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path

from .models import ABSAGEGRUND_KATEGORIEN, BEWERBUNGSWEGE


class ImportFehler(Exception):
    """Die Datei ist kein gueltiger Import im Format A oder B."""


class ImportFormat(str, Enum):
    STELLENANZEIGE = "A"
    ABSAGE = "B"


@dataclass
class StellenanzeigeImport:
    firma: str = ""
    position: str = ""
    skills: list[str] = field(default_factory=list)
    gehaltsangabe: str = ""
    bewerbungsweg_hinweis: str = ""
    quelle_url: str = ""
    hinweise: list[str] = field(default_factory=list)

    def bewerbungsweg(self) -> str:
        """Ordnet den Freitext-Hinweis einem der erlaubten Wege zu."""
        hinweis = (self.bewerbungsweg_hinweis or "").casefold()
        if not hinweis:
            return BEWERBUNGSWEGE[0]
        for weg in BEWERBUNGSWEGE:
            if weg.casefold() in hinweis:
                return weg
        if "mail" in hinweis:
            return "E-Mail"
        if "initiativ" in hinweis:
            return "Initiativbewerbung"
        if "empfehl" in hinweis or "referral" in hinweis:
            return "Empfehlung"
        return BEWERBUNGSWEGE[0]


@dataclass
class AbsageImport:
    absagegrund_kategorien: list[str] = field(default_factory=list)
    absagegrund_details: str = ""
    rohtext: str = ""
    datum: date | None = None
    hinweise: list[str] = field(default_factory=list)


def _text(wert: object) -> str:
    if wert is None:
        return ""
    if isinstance(wert, (list, dict)):
        return json.dumps(wert, ensure_ascii=False)
    return str(wert).strip()


def _liste(wert: object) -> list[str]:
    if wert is None:
        return []
    if isinstance(wert, str):
        return [wert.strip()] if wert.strip() else []
    if isinstance(wert, list):
        return [_text(e) for e in wert if _text(e)]
    return []


def format_erkennen(daten: dict) -> ImportFormat:
    if "absagegrund_kategorien" in daten or "rohtext" in daten:
        return ImportFormat.ABSAGE
    if "firma" in daten or "position" in daten or "skills" in daten:
        return ImportFormat.STELLENANZEIGE
    raise ImportFehler(
        "Unbekanntes Format: erwartet werden die Felder aus Format A "
        "(firma/position/skills) oder Format B (absagegrund_kategorien/rohtext)."
    )


def json_laden(pfad: Path | str) -> dict:
    pfad = Path(pfad)
    try:
        rohtext = pfad.read_text(encoding="utf-8-sig")
    except OSError as fehler:
        raise ImportFehler(f"Datei konnte nicht gelesen werden: {fehler}") from fehler
    try:
        daten = json.loads(rohtext)
    except ValueError as fehler:
        raise ImportFehler(f"Ungueltiges JSON: {fehler}") from fehler
    if not isinstance(daten, dict):
        raise ImportFehler("Die JSON-Datei muss ein Objekt auf oberster Ebene enthalten.")
    return daten


def stellenanzeige_lesen(daten: dict) -> StellenanzeigeImport:
    ergebnis = StellenanzeigeImport(
        firma=_text(daten.get("firma")),
        position=_text(daten.get("position")),
        skills=_liste(daten.get("skills")),
        gehaltsangabe=_text(daten.get("gehaltsangabe")),
        bewerbungsweg_hinweis=_text(daten.get("bewerbungsweg_hinweis")),
        quelle_url=_text(daten.get("quelle_url")),
    )
    if not ergebnis.firma:
        ergebnis.hinweise.append("Feld 'firma' fehlt oder ist leer.")
    if not ergebnis.position:
        ergebnis.hinweise.append("Feld 'position' fehlt oder ist leer.")
    if not ergebnis.skills:
        ergebnis.hinweise.append("Keine Skills enthalten.")
    return ergebnis


def absage_lesen(daten: dict) -> AbsageImport:
    kategorien: list[str] = []
    hinweise: list[str] = []
    bekannt = {k.casefold(): k for k in ABSAGEGRUND_KATEGORIEN}
    for rohkategorie in _liste(daten.get("absagegrund_kategorien")):
        treffer = bekannt.get(rohkategorie.casefold())
        if treffer:
            kategorien.append(treffer)
        else:
            hinweise.append(
                f"Kategorie '{rohkategorie}' ist nicht im Katalog "
                "und wurde 'Sonstiges' zugeordnet."
            )
            if "Sonstiges" not in kategorien:
                kategorien.append("Sonstiges")

    datum = None
    rohdatum = _text(daten.get("datum"))
    if rohdatum:
        try:
            datum = date.fromisoformat(rohdatum[:10])
        except ValueError:
            hinweise.append(f"Datum '{rohdatum}' ist kein gueltiges YYYY-MM-DD.")

    ergebnis = AbsageImport(
        absagegrund_kategorien=kategorien,
        absagegrund_details=_text(daten.get("absagegrund_details")),
        rohtext=_text(daten.get("rohtext")),
        datum=datum,
        hinweise=hinweise,
    )
    if not ergebnis.absagegrund_kategorien:
        ergebnis.hinweise.append("Keine Absagegrund-Kategorien enthalten.")
    return ergebnis


def datei_lesen(pfad: Path | str) -> tuple[ImportFormat, StellenanzeigeImport | AbsageImport]:
    """Liest eine Import-Datei und gibt Format plus geparste Daten zurueck."""
    daten = json_laden(pfad)
    format_ = format_erkennen(daten)
    if format_ is ImportFormat.STELLENANZEIGE:
        return format_, stellenanzeige_lesen(daten)
    return format_, absage_lesen(daten)
