"""Hauptfenster: Dashboard als Startansicht plus Kanban-Board."""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QPoint, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QActionGroup, QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .. import database, export, repository
from ..importer import ImportFehler
from ..models import STATUS_REIHENFOLGE, Bewerbung, InterviewRunde, Rueckmeldung, Status
from ..repository import Filter
from . import theme
from .dashboard import Dashboard
from .dialoge import (
    BewerbungDialog,
    EinstellungenDialog,
    InterviewRundeDialog,
    aus_qdate,
    datumsfeld,
)
from .import_dialog import import_starten
from .kanban import KanbanBoard, kontextmenue_bauen

ALLE_STATUS = "Alle Status"


class Filterleiste(QFrame):
    """Suche nach Firma/Position, Status und Zeitraum (Abschnitt 9)."""

    def __init__(self, beim_aendern, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("rolle", "karte")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        self.suche = QLineEdit()
        self.suche.setPlaceholderText("Firma, Position oder Skill suchen …")
        self.suche.setClearButtonEnabled(True)
        self.suche.textChanged.connect(beim_aendern)

        self.status = QComboBox()
        self.status.addItem(ALLE_STATUS)
        for status in STATUS_REIHENFOLGE:
            self.status.addItem(status.value)
        self.status.currentIndexChanged.connect(beim_aendern)

        self.zeitraum_aktiv = QCheckBox("Zeitraum")
        self.zeitraum_aktiv.toggled.connect(self._zeitraum_umschalten)
        self.zeitraum_aktiv.toggled.connect(beim_aendern)

        self.von = datumsfeld(date.today() - timedelta(days=90))
        self.bis = datumsfeld(date.today())
        for feld in (self.von, self.bis):
            feld.setEnabled(False)
            feld.dateChanged.connect(beim_aendern)

        zuruecksetzen = QPushButton("Zurücksetzen")
        zuruecksetzen.clicked.connect(self.zuruecksetzen)

        layout.addWidget(QLabel("Suche"))
        layout.addWidget(self.suche, 2)
        layout.addWidget(self.status, 1)
        layout.addWidget(self.zeitraum_aktiv)
        layout.addWidget(self.von)
        layout.addWidget(QLabel("bis"))
        layout.addWidget(self.bis)
        layout.addWidget(zuruecksetzen)

    def _zeitraum_umschalten(self, aktiv: bool) -> None:
        self.von.setEnabled(aktiv)
        self.bis.setEnabled(aktiv)

    def zuruecksetzen(self) -> None:
        self.suche.clear()
        self.status.setCurrentIndex(0)
        self.zeitraum_aktiv.setChecked(False)

    def filter_bauen(self) -> Filter:
        status_auswahl = None
        if self.status.currentIndex() > 0:
            status_auswahl = {Status(self.status.currentText())}
        von = aus_qdate(self.von.date()) if self.zeitraum_aktiv.isChecked() else None
        bis = aus_qdate(self.bis.date()) if self.zeitraum_aktiv.isChecked() else None
        return Filter(
            suchtext=self.suche.text().strip(),
            status=status_auswahl,
            von=von,
            bis=bis,
        )


class Hauptfenster(QMainWindow):
    def __init__(self, conn: sqlite3.Connection) -> None:
        super().__init__()
        self.conn = conn
        self.setWindowTitle("Bewerbungstracker")
        self.resize(1280, 820)

        self._dashboard = Dashboard()
        self._dashboard.bewerbung_geoeffnet.connect(self.bewerbung_bearbeiten)

        self._board = KanbanBoard()
        self._board.bewerbung_geoeffnet.connect(self.bewerbung_bearbeiten)
        self._board.status_gewuenscht.connect(self._status_wunsch)
        self._board.kontextmenue_gewuenscht.connect(self._kontextmenue)

        self._filterleiste = Filterleiste(self.ansicht_aktualisieren)

        boardseite = QWidget()
        boardlayout = QVBoxLayout(boardseite)
        boardlayout.setContentsMargins(16, 16, 16, 16)
        boardlayout.setSpacing(12)
        titel = QLabel("Bewerbungen")
        titel.setProperty("rolle", "titel")
        boardlayout.addWidget(titel)
        boardlayout.addWidget(self._filterleiste)
        boardlayout.addWidget(self._board, 1)

        self._seiten = QStackedWidget()
        self._seiten.addWidget(self._dashboard)
        self._seiten.addWidget(boardseite)
        self.setCentralWidget(self._seiten)

        self._werkzeugleiste_bauen()
        self._beobachter = QFileSystemWatcher(self)
        self._beobachter.directoryChanged.connect(self._ordner_geaendert)
        self._bekannte_dateien: set[str] = set()
        self._ordner_ueberwachung_einrichten()

        self.statusBar().showMessage(str(database.datenbank_pfad()))
        self.ansicht_aktualisieren()

    # -- Aufbau --

    def _werkzeugleiste_bauen(self) -> None:
        leiste = QToolBar("Hauptmenü")
        leiste.setMovable(False)
        leiste.setStyleSheet(
            f"QToolBar {{ background: {theme.FLAECHE}; border-bottom: 1px solid "
            f"{theme.RAHMEN}; padding: 6px; spacing: 6px; }}"
        )
        self.addToolBar(leiste)

        gruppe = QActionGroup(self)
        gruppe.setExclusive(True)
        self._aktion_dashboard = QAction("Dashboard", self)
        self._aktion_dashboard.setCheckable(True)
        self._aktion_dashboard.setChecked(True)
        self._aktion_dashboard.triggered.connect(lambda: self._seite_zeigen(0))
        self._aktion_board = QAction("Bewerbungen", self)
        self._aktion_board.setCheckable(True)
        self._aktion_board.triggered.connect(lambda: self._seite_zeigen(1))
        for aktion in (self._aktion_dashboard, self._aktion_board):
            gruppe.addAction(aktion)
            leiste.addAction(aktion)

        leiste.addSeparator()
        neu = QAction("Neue Bewerbung", self)
        neu.setShortcut("Ctrl+N")
        neu.triggered.connect(self.bewerbung_anlegen)
        leiste.addAction(neu)

        importieren = QAction("JSON importieren …", self)
        importieren.setShortcut("Ctrl+I")
        importieren.triggered.connect(self.json_importieren)
        leiste.addAction(importieren)

        pruefen = QAction("Import-Ordner prüfen", self)
        pruefen.triggered.connect(lambda: self._ordner_pruefen(nachfragen=True))
        leiste.addAction(pruefen)

        exportieren = QAction("CSV-Export", self)
        exportieren.triggered.connect(self.csv_exportieren)
        leiste.addAction(exportieren)

        platzhalter = QWidget()
        platzhalter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        leiste.addWidget(platzhalter)

        aktualisieren = QAction("Aktualisieren", self)
        aktualisieren.setShortcut("F5")
        aktualisieren.triggered.connect(self.ansicht_aktualisieren)
        leiste.addAction(aktualisieren)

        einstellungen = QAction("Einstellungen", self)
        einstellungen.triggered.connect(self.einstellungen_oeffnen)
        leiste.addAction(einstellungen)

    def _seite_zeigen(self, index: int) -> None:
        self._seiten.setCurrentIndex(index)

    # -- Daten --

    def _reminder_tage(self) -> int:
        return database.einstellung_int(self.conn, "reminder_tage", 14)

    def ansicht_aktualisieren(self, *_args) -> None:
        reminder = self._reminder_tage()
        alle = repository.alle_bewerbungen(self.conn)
        filter_ = self._filterleiste.filter_bauen()
        gefiltert = [b for b in alle if filter_.passt(b)]
        self._dashboard.aktualisieren(alle, reminder)
        self._board.anzeigen(gefiltert, reminder)
        self.statusBar().showMessage(
            f"{len(gefiltert)} von {len(alle)} Bewerbungen angezeigt · "
            f"Datenbank: {database.datenbank_pfad()}"
        )

    def _bewerbung(self, bewerbung_id: int) -> Bewerbung | None:
        return repository.bewerbung_laden(self.conn, bewerbung_id)

    # -- Aktionen --

    def bewerbung_anlegen(self) -> None:
        dialog = BewerbungDialog(self.conn, None, self)
        if dialog.exec() == QDialog.Accepted:
            self.ansicht_aktualisieren()

    def bewerbung_bearbeiten(self, bewerbung_id: int) -> None:
        bewerbung = self._bewerbung(bewerbung_id)
        if bewerbung is None:
            return
        dialog = BewerbungDialog(self.conn, bewerbung, self)
        if dialog.exec() == QDialog.Accepted:
            self.ansicht_aktualisieren()

    def bewerbung_loeschen(self, bewerbung_id: int) -> None:
        bewerbung = self._bewerbung(bewerbung_id)
        if bewerbung is None:
            return
        antwort = QMessageBox.question(
            self,
            "Bewerbung löschen",
            f"„{bewerbung.anzeigename()}“ mit allen Interview-Runden löschen?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if antwort == QMessageBox.Yes:
            repository.bewerbung_loeschen(self.conn, bewerbung_id)
            self.ansicht_aktualisieren()

    def runde_anlegen(self, bewerbung_id: int) -> None:
        runde = InterviewRunde(
            bewerbung_id=bewerbung_id,
            runde_nummer=repository.naechste_rundennummer(self.conn, bewerbung_id),
            datum=date.today(),
        )
        if InterviewRundeDialog(runde, self).exec() == QDialog.Accepted:
            repository.runde_speichern(self.conn, runde)
            self.ansicht_aktualisieren()

    def rueckmeldung_eintragen(
        self, bewerbung_id: int, typ: Rueckmeldung | None = None
    ) -> None:
        bewerbung = self._bewerbung(bewerbung_id)
        if bewerbung is None:
            return
        dialog = BewerbungDialog(self.conn, bewerbung, self)
        if typ is Rueckmeldung.ZUSAGE:
            dialog.zusage_uebernehmen(date.today())
        elif typ is Rueckmeldung.ABSAGE:
            dialog.absage_uebernehmen(
                bewerbung.absagegrund_kategorien,
                bewerbung.absagegrund_details,
                bewerbung.absage_rohtext,
                bewerbung.rueckmeldung_am or date.today(),
            )
        else:
            dialog.reiter_anzeigen(dialog.rueckmeldung_tab)
        if dialog.exec() == QDialog.Accepted:
            self.ansicht_aktualisieren()

    def datei_oeffnen(self, pfad: str) -> None:
        if not pfad:
            return
        if not Path(pfad).exists():
            QMessageBox.warning(self, "Datei fehlt", f"Nicht gefunden:\n{pfad}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(pfad))

    # -- Drag & Drop im Board --

    def _status_wunsch(self, bewerbung_id: int, zielstatus_wert: str) -> None:
        """Ein Drop meldet den gewuenschten Zielstatus -- Status bleibt abgeleitet."""
        bewerbung = self._bewerbung(bewerbung_id)
        if bewerbung is None:
            return
        ziel = Status(zielstatus_wert)
        if ziel is bewerbung.status:
            return

        if ziel is Status.GHOSTING:
            QMessageBox.information(
                self,
                "Automatischer Status",
                "„Ghosting/Keine Rückmeldung“ wird automatisch gesetzt, sobald die "
                "eingestellte Anzahl Tage ohne Reaktion überschritten ist.",
            )
            return

        if ziel is Status.ZUSAGE:
            self.rueckmeldung_eintragen(bewerbung_id, Rueckmeldung.ZUSAGE)
            return

        if ziel is Status.ABSAGE:
            self.rueckmeldung_eintragen(bewerbung_id, Rueckmeldung.ABSAGE)
            return

        # Ziel ist Beworben oder Im Interview-Prozess -> ggf. Rueckmeldung entfernen.
        if bewerbung.rueckmeldung_typ is not None:
            antwort = QMessageBox.question(
                self,
                "Rückmeldung entfernen?",
                "Die Bewerbung wieder öffnen und die eingetragene Rückmeldung "
                "inklusive Absagegründen entfernen?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if antwort != QMessageBox.Yes:
                return
            repository.rueckmeldung_setzen(self.conn, bewerbung_id, None)
            bewerbung = self._bewerbung(bewerbung_id)

        if ziel is Status.INTERVIEW:
            # Eine neue Runde mit aktuellem Datum setzt zugleich den
            # Nachfrage-Zaehler zurueck -- damit verlaesst die Karte auch Ghosting.
            self.runde_anlegen(bewerbung_id)
            return

        if ziel is Status.BEWORBEN and bewerbung and bewerbung.interview_runden:
            QMessageBox.information(
                self,
                "Automatischer Status",
                "Solange Interview-Runden erfasst sind, bleibt der Status "
                "„Im Interview-Prozess“. Entferne die Runden im Bearbeiten-Dialog, "
                "um zurück auf „Beworben“ zu kommen.",
            )
        self.ansicht_aktualisieren()

        aktuell = self._bewerbung(bewerbung_id)
        if aktuell is not None and aktuell.status is Status.GHOSTING and ziel is not Status.GHOSTING:
            self.statusBar().showMessage(
                "Status bleibt „Ghosting/Keine Rückmeldung“ – seit der letzten "
                "Aktivität sind zu viele Tage vergangen.",
                6000,
            )

    def _kontextmenue(self, bewerbung_id: int, punkt: QPoint) -> None:
        bewerbung = self._bewerbung(bewerbung_id)
        if bewerbung is None:
            return
        menue = kontextmenue_bauen(self)
        menue.addAction("Bearbeiten …", lambda: self.bewerbung_bearbeiten(bewerbung_id))
        menue.addAction("Interview-Runde hinzufügen …", lambda: self.runde_anlegen(bewerbung_id))
        menue.addAction(
            "Rückmeldung eintragen …", lambda: self.rueckmeldung_eintragen(bewerbung_id)
        )
        menue.addSeparator()
        cv = menue.addAction("Lebenslauf öffnen", lambda: self.datei_oeffnen(bewerbung.cv_pfad))
        cv.setEnabled(bool(bewerbung.cv_pfad))
        anschreiben = menue.addAction(
            "Anschreiben öffnen", lambda: self.datei_oeffnen(bewerbung.anschreiben_pfad)
        )
        anschreiben.setEnabled(bool(bewerbung.anschreiben_pfad))
        quelle = menue.addAction(
            "Stellenanzeige öffnen",
            lambda: QDesktopServices.openUrl(QUrl(bewerbung.quelle_url)),
        )
        quelle.setEnabled(bool(bewerbung.quelle_url))
        menue.addSeparator()
        menue.addAction("Löschen …", lambda: self.bewerbung_loeschen(bewerbung_id))
        menue.exec(punkt)

    # -- Import / Export / Einstellungen --

    def json_importieren(self) -> None:
        startordner = database.einstellung_lesen(self.conn, "import_ordner")
        pfad, _ = QFileDialog.getOpenFileName(
            self, "Import-Datei wählen", startordner, "JSON-Dateien (*.json)"
        )
        if not pfad:
            return
        self._importieren(pfad)

    def _importieren(self, pfad: str) -> None:
        try:
            bewerbung_id = import_starten(self.conn, pfad, self)
        except ImportFehler as fehler:
            QMessageBox.critical(self, "Import fehlgeschlagen", str(fehler))
            return
        self._bekannte_dateien.add(str(Path(pfad).resolve()))
        if bewerbung_id is not None:
            self.ansicht_aktualisieren()

    def csv_exportieren(self) -> None:
        vorschlag = str(
            Path.home() / f"bewerbungen_{date.today().isoformat()}.csv"
        )
        pfad, _ = QFileDialog.getSaveFileName(
            self, "CSV-Export speichern", vorschlag, "CSV-Dateien (*.csv)"
        )
        if not pfad:
            return
        try:
            anzahl = export.csv_schreiben(pfad, repository.alle_bewerbungen(self.conn))
        except OSError as fehler:
            QMessageBox.critical(self, "Export fehlgeschlagen", str(fehler))
            return
        QMessageBox.information(
            self, "Export abgeschlossen", f"{anzahl} Bewerbungen nach\n{pfad}\ngeschrieben."
        )

    def einstellungen_oeffnen(self) -> None:
        if EinstellungenDialog(self.conn, self).exec() == QDialog.Accepted:
            self._ordner_ueberwachung_einrichten()
            self.ansicht_aktualisieren()

    # -- Ordnerueberwachung (Abschnitt 5) --

    def _ordner_ueberwachung_einrichten(self) -> None:
        for alter_pfad in self._beobachter.directories():
            self._beobachter.removePath(alter_pfad)
        ordner = database.einstellung_lesen(self.conn, "import_ordner")
        if not ordner or not Path(ordner).is_dir():
            return
        self._beobachter.addPath(ordner)
        # Vorhandene Dateien gelten als bereits gesehen -- sonst poppt beim Start
        # fuer jede Altdatei ein Dialog auf.
        self._bekannte_dateien = {
            str(p.resolve()) for p in Path(ordner).glob("*.json")
        }

    def _ordner_geaendert(self, _pfad: str) -> None:
        # Kurz warten, damit die Datei vollstaendig geschrieben ist.
        QTimer.singleShot(600, lambda: self._ordner_pruefen(nachfragen=False))

    def _ordner_pruefen(self, nachfragen: bool) -> None:
        ordner = database.einstellung_lesen(self.conn, "import_ordner")
        if not ordner or not Path(ordner).is_dir():
            if nachfragen:
                QMessageBox.information(
                    self,
                    "Kein Import-Ordner",
                    "In den Einstellungen ist kein gültiger Import-Ordner hinterlegt.",
                )
            return

        neue = [
            p
            for p in sorted(Path(ordner).glob("*.json"))
            if str(p.resolve()) not in self._bekannte_dateien
        ]
        if not neue:
            if nachfragen:
                QMessageBox.information(
                    self, "Import-Ordner", "Keine neuen JSON-Dateien gefunden."
                )
            return

        for datei in neue:
            antwort = QMessageBox.question(
                self,
                "Neue Import-Datei",
                f"„{datei.name}“ jetzt importieren?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if antwort == QMessageBox.Yes:
                self._importieren(str(datei))
            else:
                self._bekannte_dateien.add(str(datei.resolve()))
