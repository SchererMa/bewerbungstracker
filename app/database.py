"""SQLite-Anbindung: Speicherort, Schema, Migrationen und Einstellungen."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

APP_NAME = "Bewerbungstracker"

#: Aktuelle Schema-Version (PRAGMA user_version).
SCHEMA_VERSION = 1

#: Standardwerte der globalen Einstellungen (Abschnitt 5, 7).
STANDARD_EINSTELLUNGEN: dict[str, str] = {
    # Abschnitt 7: ab wie vielen Tagen ohne Reaktion "Nachfragen?" empfohlen wird.
    "reminder_tage": "14",
    # Ab wie vielen Tagen ohne Reaktion automatisch auf "Ghosting" gesetzt wird.
    # Auf denselben Wert wie reminder_tage setzen, um exakt ein Schwellenwert zu haben.
    "ghosting_tage": "30",
    # Abschnitt 5: überwachter Ordner für KI-JSON-Exporte.
    "import_ordner": "",
    # Abschnitt 11 (später): optionaler API-Key für direkte Extraktion.
    "anthropic_api_key": "",
}


def daten_verzeichnis() -> Path:
    """Verzeichnis für die Datenbank -- überschreibbar via BEWERBUNGSTRACKER_DIR."""
    override = os.environ.get("BEWERBUNGSTRACKER_DIR")
    if override:
        return Path(override)
    basis = os.environ.get("APPDATA") or str(Path.home())
    return Path(basis) / APP_NAME


def datenbank_pfad() -> Path:
    return daten_verzeichnis() / "bewerbungstracker.db"


def verbinden(pfad: Path | str | None = None) -> sqlite3.Connection:
    """Öffnet die Datenbank, legt sie bei Bedarf an und migriert das Schema."""
    ziel = Path(pfad) if pfad else datenbank_pfad()
    if str(ziel) != ":memory:":
        ziel.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(ziel), detect_types=0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    _migrieren(conn)
    return conn


# --- Schema ------------------------------------------------------------------

_SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS bewerbungen (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    profil_id              INTEGER NOT NULL DEFAULT 1,
    firma                  TEXT    NOT NULL DEFAULT '',
    position               TEXT    NOT NULL DEFAULT '',
    bewerbungsweg          TEXT    NOT NULL DEFAULT 'Jobportal',
    beworben_am            TEXT,
    status                 TEXT    NOT NULL DEFAULT 'Beworben',
    skills                 TEXT    NOT NULL DEFAULT '[]',
    gehaltsangabe          TEXT    NOT NULL DEFAULT '',
    cv_pfad                TEXT    NOT NULL DEFAULT '',
    anschreiben_pfad       TEXT    NOT NULL DEFAULT '',
    absagegrund_kategorien TEXT    NOT NULL DEFAULT '[]',
    absagegrund_details    TEXT    NOT NULL DEFAULT '',
    absage_rohtext         TEXT    NOT NULL DEFAULT '',
    notizen                TEXT    NOT NULL DEFAULT '',
    quelle_url             TEXT    NOT NULL DEFAULT '',
    rueckmeldung_typ       TEXT,
    rueckmeldung_am        TEXT,
    letzte_aktualisierung  TEXT
);

CREATE TABLE IF NOT EXISTS interview_runden (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    bewerbung_id  INTEGER NOT NULL REFERENCES bewerbungen(id) ON DELETE CASCADE,
    runde_nummer  INTEGER NOT NULL DEFAULT 1,
    typ           TEXT    NOT NULL DEFAULT 'Telefon',
    datum         TEXT,
    ergebnis      TEXT    NOT NULL DEFAULT 'Offen',
    notizen       TEXT    NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS einstellungen (
    schluessel TEXT PRIMARY KEY,
    wert       TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_runden_bewerbung ON interview_runden(bewerbung_id);
CREATE INDEX IF NOT EXISTS idx_bewerbungen_firma ON bewerbungen(firma);
CREATE INDEX IF NOT EXISTS idx_bewerbungen_profil ON bewerbungen(profil_id);
"""


def _migrieren(conn: sqlite3.Connection) -> None:
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version < 1:
        conn.executescript(_SCHEMA_V1)
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    # Künftige Migrationen: if version < 2: ...
    _einstellungen_initialisieren(conn)
    conn.commit()


def _einstellungen_initialisieren(conn: sqlite3.Connection) -> None:
    for schluessel, wert in STANDARD_EINSTELLUNGEN.items():
        conn.execute(
            "INSERT OR IGNORE INTO einstellungen (schluessel, wert) VALUES (?, ?)",
            (schluessel, wert),
        )


# --- Einstellungen -----------------------------------------------------------


def einstellung_lesen(conn: sqlite3.Connection, schluessel: str, standard: str = "") -> str:
    zeile = conn.execute(
        "SELECT wert FROM einstellungen WHERE schluessel = ?", (schluessel,)
    ).fetchone()
    if zeile is None:
        return STANDARD_EINSTELLUNGEN.get(schluessel, standard)
    return zeile["wert"]


def einstellung_int(conn: sqlite3.Connection, schluessel: str, standard: int) -> int:
    try:
        return int(einstellung_lesen(conn, schluessel, str(standard)))
    except (TypeError, ValueError):
        return standard


def einstellung_schreiben(conn: sqlite3.Connection, schluessel: str, wert: str) -> None:
    conn.execute(
        "INSERT INTO einstellungen (schluessel, wert) VALUES (?, ?) "
        "ON CONFLICT(schluessel) DO UPDATE SET wert = excluded.wert",
        (schluessel, str(wert)),
    )
    conn.commit()
