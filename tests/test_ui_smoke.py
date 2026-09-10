"""Smoke-Tests der Oberflaeche: Fenster und Dialoge muessen sich bauen lassen.

Laeuft mit dem Qt-Plattform-Plugin "offscreen", damit kein Fenster erscheint und
die Tests auch ohne Desktop-Sitzung durchlaufen.
"""

from __future__ import annotations

import os
from datetime import date, timedelta

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from app import database, repository  # noqa: E402
from app.models import Bewerbung, InterviewRunde, Rueckmeldung, Status  # noqa: E402
from app.ui.dialoge import BewerbungDialog, EinstellungenDialog  # noqa: E402
from app.ui.hauptfenster import Hauptfenster  # noqa: E402
from app.ui.import_dialog import ImportDialog  # noqa: E402


@pytest.fixture(scope="session")
def qapp():
    anwendung = QApplication.instance() or QApplication([])
    yield anwendung


@pytest.fixture()
def conn(tmp_path):
    verbindung = database.verbinden(tmp_path / "ui.db")
    repository.bewerbung_speichern(
        verbindung,
        Bewerbung(
            firma="Nordlicht Energie",
            position="Projektmanager",
            beworben_am=date.today() - timedelta(days=20),
            skills=["Projektmanagement"],
        ),
    )
    mit_runde = repository.bewerbung_speichern(
        verbindung,
        Bewerbung(
            firma="Hansa Logistik",
            position="Teamleiter",
            beworben_am=date.today() - timedelta(days=10),
        ),
    )
    repository.runde_speichern(
        verbindung,
        InterviewRunde(bewerbung_id=mit_runde, runde_nummer=1, datum=date.today()),
    )
    yield verbindung
    verbindung.close()


def test_hauptfenster_baut_und_fuellt_board(qapp, conn):
    fenster = Hauptfenster(conn)
    fenster.ansicht_aktualisieren()
    bewerbungen = repository.alle_bewerbungen(conn)
    assert len(bewerbungen) == 2
    assert {b.status for b in bewerbungen} == {Status.BEWORBEN, Status.INTERVIEW}
    fenster.close()


def test_filter_wirkt_auf_board(qapp, conn):
    fenster = Hauptfenster(conn)
    fenster._filterleiste.suche.setText("hansa")
    gefiltert = [
        b
        for b in repository.alle_bewerbungen(conn)
        if fenster._filterleiste.filter_bauen().passt(b)
    ]
    assert [b.firma for b in gefiltert] == ["Hansa Logistik"]
    fenster.close()


def test_bewerbung_dialog_speichert(qapp, conn):
    dialog = BewerbungDialog(conn, None)
    dialog._firma.setText("Testfirma")
    dialog._position.setText("Testposition")
    dialog._skills.setText("Python, SQL")
    dialog.accept()
    gespeichert = repository.bewerbung_laden(conn, dialog.bewerbung.id)
    assert gespeichert.firma == "Testfirma"
    assert gespeichert.skills == ["Python", "SQL"]


def test_rueckmeldung_tab_setzt_absage(qapp, conn):
    bewerbung = repository.alle_bewerbungen(conn)[0]
    dialog = BewerbungDialog(conn, bewerbung)
    dialog.absage_uebernehmen(["Gehaltsvorstellung"], "zu teuer", "Rohtext", date.today())
    dialog.accept()
    geladen = repository.bewerbung_laden(conn, bewerbung.id)
    assert geladen.rueckmeldung_typ is Rueckmeldung.ABSAGE
    assert geladen.status is Status.ABSAGE
    assert geladen.absagegrund_kategorien == ["Gehaltsvorstellung"]


def test_einstellungen_dialog_speichert(qapp, conn):
    dialog = EinstellungenDialog(conn)
    dialog._reminder.setValue(21)
    dialog._ghosting.setValue(45)
    dialog.accept()
    assert database.einstellung_int(conn, "reminder_tage", 0) == 21
    assert database.einstellung_int(conn, "ghosting_tage", 0) == 45


def test_import_dialog_zeigt_beide_formate(qapp, conn):
    from pathlib import Path

    ordner = Path(__file__).resolve().parent.parent / "beispiel_importe"
    for datei in sorted(ordner.glob("*.json")):
        dialog = ImportDialog(conn, datei)
        assert dialog.windowTitle() == "JSON-Import"
