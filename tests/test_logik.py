"""Tests der Kernlogik: Statusableitung, Reminder, Import, Export, CRUD."""

from __future__ import annotations

import json
from datetime import date, timedelta

import pytest

from app import database, export, repository, statistik
from app.importer import ImportFehler, ImportFormat, datei_lesen, format_erkennen
from app.models import Bewerbung, InterviewRunde, Rueckmeldung, Status
from app.status import nachfragen_empfohlen, status_berechnen, tage_ohne_reaktion

HEUTE = date(2026, 9, 10)


def tage_vor(anzahl: int) -> date:
    return HEUTE - timedelta(days=anzahl)


@pytest.fixture()
def conn(tmp_path):
    verbindung = database.verbinden(tmp_path / "test.db")
    yield verbindung
    verbindung.close()


# --- Statusableitung (Abschnitt 4) ------------------------------------------


def test_ohne_runden_und_rueckmeldung_ist_beworben():
    bewerbung = Bewerbung(beworben_am=tage_vor(3))
    assert status_berechnen(bewerbung, ghosting_tage=30, heute=HEUTE) is Status.BEWORBEN


def test_mit_runde_ist_im_interview_prozess():
    bewerbung = Bewerbung(
        beworben_am=tage_vor(20),
        interview_runden=[InterviewRunde(datum=tage_vor(5))],
    )
    assert status_berechnen(bewerbung, ghosting_tage=30, heute=HEUTE) is Status.INTERVIEW


def test_rueckmeldung_schlaegt_runden():
    bewerbung = Bewerbung(
        beworben_am=tage_vor(40),
        rueckmeldung_typ=Rueckmeldung.ABSAGE,
        interview_runden=[InterviewRunde(datum=tage_vor(35))],
    )
    assert status_berechnen(bewerbung, ghosting_tage=30, heute=HEUTE) is Status.ABSAGE


def test_zusage_auch_nach_langer_stille():
    bewerbung = Bewerbung(beworben_am=tage_vor(200), rueckmeldung_typ=Rueckmeldung.ZUSAGE)
    assert status_berechnen(bewerbung, ghosting_tage=30, heute=HEUTE) is Status.ZUSAGE


def test_ghosting_ab_schwellenwert():
    bewerbung = Bewerbung(beworben_am=tage_vor(30))
    assert status_berechnen(bewerbung, ghosting_tage=30, heute=HEUTE) is Status.GHOSTING


def test_neue_runde_setzt_ghosting_zurueck():
    bewerbung = Bewerbung(
        beworben_am=tage_vor(90),
        interview_runden=[InterviewRunde(datum=tage_vor(2))],
    )
    assert status_berechnen(bewerbung, ghosting_tage=30, heute=HEUTE) is Status.INTERVIEW


# --- Reminder (Abschnitt 7) --------------------------------------------------


def test_zaehler_startet_ab_letzter_runde():
    bewerbung = Bewerbung(
        beworben_am=tage_vor(60),
        interview_runden=[InterviewRunde(datum=tage_vor(12))],
    )
    assert tage_ohne_reaktion(bewerbung, HEUTE) == 12


def test_nachfragen_nur_fuer_offene_bewerbungen():
    offen = Bewerbung(status=Status.BEWORBEN, beworben_am=tage_vor(20))
    geschlossen = Bewerbung(
        status=Status.ABSAGE,
        beworben_am=tage_vor(20),
        rueckmeldung_typ=Rueckmeldung.ABSAGE,
    )
    assert nachfragen_empfohlen(offen, reminder_tage=14, heute=HEUTE)
    assert not nachfragen_empfohlen(geschlossen, reminder_tage=14, heute=HEUTE)


def test_kein_reminder_ohne_datum():
    assert tage_ohne_reaktion(Bewerbung(), HEUTE) is None
    assert not nachfragen_empfohlen(Bewerbung(), reminder_tage=14, heute=HEUTE)


# --- Persistenz --------------------------------------------------------------


def test_speichern_und_laden_mit_runden(conn):
    bewerbung = Bewerbung(
        firma="Nordlicht Energie",
        position="Projektmanager",
        beworben_am=tage_vor(5),
        skills=["Python", "SQL"],
    )
    bewerbung_id = repository.bewerbung_speichern(conn, bewerbung)
    repository.runde_speichern(
        conn,
        InterviewRunde(bewerbung_id=bewerbung_id, runde_nummer=1, datum=tage_vor(1)),
    )

    geladen = repository.bewerbung_laden(conn, bewerbung_id)
    assert geladen is not None
    assert geladen.firma == "Nordlicht Energie"
    assert geladen.skills == ["Python", "SQL"]
    assert len(geladen.interview_runden) == 1
    assert geladen.status is Status.INTERVIEW


def test_rueckmeldung_setzen_aendert_status(conn):
    bewerbung_id = repository.bewerbung_speichern(
        conn, Bewerbung(firma="A", position="B", beworben_am=tage_vor(5))
    )
    repository.rueckmeldung_setzen(
        conn,
        bewerbung_id,
        Rueckmeldung.ABSAGE,
        am=date.today(),
        kategorien=["Fachliche Skills"],
        details="zu wenig Erfahrung mit X",
    )
    geladen = repository.bewerbung_laden(conn, bewerbung_id)
    assert geladen.status is Status.ABSAGE
    assert geladen.absagegrund_kategorien == ["Fachliche Skills"]

    repository.rueckmeldung_setzen(conn, bewerbung_id, None)
    geladen = repository.bewerbung_laden(conn, bewerbung_id)
    assert geladen.status is Status.BEWORBEN
    assert geladen.absagegrund_kategorien == []


def test_loeschen_entfernt_runden(conn):
    bewerbung_id = repository.bewerbung_speichern(
        conn, Bewerbung(firma="A", position="B", beworben_am=tage_vor(2))
    )
    repository.runde_speichern(conn, InterviewRunde(bewerbung_id=bewerbung_id))
    repository.bewerbung_loeschen(conn, bewerbung_id)
    assert repository.bewerbung_laden(conn, bewerbung_id) is None
    uebrig = conn.execute("SELECT COUNT(*) AS n FROM interview_runden").fetchone()["n"]
    assert uebrig == 0


def test_filter_nach_firma_status_und_zeitraum(conn):
    repository.bewerbung_speichern(
        conn, Bewerbung(firma="Nordlicht", position="PM", beworben_am=tage_vor(3))
    )
    repository.bewerbung_speichern(
        conn, Bewerbung(firma="Hansa", position="Disponent", beworben_am=tage_vor(200))
    )

    nur_nordlicht = repository.alle_bewerbungen(conn, repository.Filter(suchtext="nordl"))
    assert [b.firma for b in nur_nordlicht] == ["Nordlicht"]

    nur_ghosting = repository.alle_bewerbungen(
        conn, repository.Filter(status={Status.GHOSTING})
    )
    assert [b.firma for b in nur_ghosting] == ["Hansa"]

    zeitraum = repository.alle_bewerbungen(
        conn, repository.Filter(von=date.today() - timedelta(days=10))
    )
    assert [b.firma for b in zeitraum] == ["Nordlicht"]


def test_einstellungen_werden_persistiert(conn):
    assert database.einstellung_int(conn, "reminder_tage", 14) == 14
    database.einstellung_schreiben(conn, "reminder_tage", "21")
    assert database.einstellung_int(conn, "reminder_tage", 14) == 21


# --- Import (Abschnitt 5) ----------------------------------------------------


def test_format_a_wird_erkannt_und_gelesen(tmp_path):
    pfad = tmp_path / "a.json"
    pfad.write_text(
        json.dumps(
            {
                "firma": "Nordlicht",
                "position": "PM",
                "skills": ["Python"],
                "gehaltsangabe": None,
                "bewerbungsweg_hinweis": "Bewerbung per E-Mail",
                "quelle_url": "https://example.org",
            }
        ),
        encoding="utf-8",
    )
    format_, daten = datei_lesen(pfad)
    assert format_ is ImportFormat.STELLENANZEIGE
    assert daten.firma == "Nordlicht"
    assert daten.gehaltsangabe == ""
    assert daten.bewerbungsweg() == "E-Mail"


def test_format_b_mappt_unbekannte_kategorie_auf_sonstiges(tmp_path):
    pfad = tmp_path / "b.json"
    pfad.write_text(
        json.dumps(
            {
                "absagegrund_kategorien": ["Gehaltsvorstellung", "Mondphase"],
                "absagegrund_details": "zu teuer",
                "rohtext": "…",
                "datum": "2026-08-28",
            }
        ),
        encoding="utf-8",
    )
    format_, daten = datei_lesen(pfad)
    assert format_ is ImportFormat.ABSAGE
    assert daten.absagegrund_kategorien == ["Gehaltsvorstellung", "Sonstiges"]
    assert daten.datum == date(2026, 8, 28)
    assert daten.hinweise


def test_unbekanntes_format_wirft_fehler():
    with pytest.raises(ImportFehler):
        format_erkennen({"irgendwas": 1})


def test_kaputte_datei_wirft_fehler(tmp_path):
    pfad = tmp_path / "kaputt.json"
    pfad.write_text("{ kein json", encoding="utf-8")
    with pytest.raises(ImportFehler):
        datei_lesen(pfad)


def test_beispieldateien_sind_gueltig():
    from pathlib import Path

    ordner = Path(__file__).resolve().parent.parent / "beispiel_importe"
    formate = {datei_lesen(p)[0] for p in ordner.glob("*.json")}
    assert formate == {ImportFormat.STELLENANZEIGE, ImportFormat.ABSAGE}


# --- Auswertung & Export -----------------------------------------------------


def _auswertungsdaten() -> list[Bewerbung]:
    return [
        Bewerbung(id=1, status=Status.BEWORBEN, beworben_am=tage_vor(3)),
        Bewerbung(id=2, status=Status.GHOSTING, beworben_am=tage_vor(60)),
        Bewerbung(id=3, status=Status.ZUSAGE, rueckmeldung_typ=Rueckmeldung.ZUSAGE),
        Bewerbung(
            id=4,
            status=Status.ABSAGE,
            rueckmeldung_typ=Rueckmeldung.ABSAGE,
            absagegrund_kategorien=["Gehaltsvorstellung", "Fachliche Skills"],
        ),
        Bewerbung(
            id=5,
            status=Status.ABSAGE,
            rueckmeldung_typ=Rueckmeldung.ABSAGE,
            absagegrund_kategorien=["Gehaltsvorstellung"],
        ),
    ]


def test_status_verteilung_und_absagegruende():
    daten = _auswertungsdaten()
    assert statistik.status_verteilung(daten) == {
        "Zusage": 1,
        "Absage": 2,
        "Offen": 1,
        "Ghosting": 1,
    }
    assert statistik.absagegruende(daten) == [
        ("Gehaltsvorstellung", 2),
        ("Fachliche Skills", 1),
    ]


def test_offene_liste_enthaelt_ghosting():
    offen = statistik.offene_bewerbungen(_auswertungsdaten(), heute=HEUTE)
    assert {b.id for b, _ in offen} == {1, 2}


def test_csv_export_enthaelt_alle_zeilen(tmp_path):
    ziel = tmp_path / "export.csv"
    anzahl = export.csv_schreiben(ziel, _auswertungsdaten())
    inhalt = ziel.read_text(encoding="utf-8-sig")
    assert anzahl == 5
    assert inhalt.count("\n") == 6  # Kopfzeile + 5 Datenzeilen
    assert "Gehaltsvorstellung; Fachliche Skills" in inhalt
