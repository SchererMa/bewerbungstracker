"""Formular-Dialoge zum Anlegen und Bearbeiten von Datensaetzen."""

from __future__ import annotations

import sqlite3
from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor, QTextCharFormat
from PySide6.QtWidgets import (
    QButtonGroup,
    QCalendarWidget,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .. import database, repository
from ..models import (
    ABSAGEGRUND_KATEGORIEN,
    BEWERBUNGSWEGE,
    INTERVIEW_ERGEBNISSE,
    INTERVIEW_TYPEN,
    Bewerbung,
    InterviewRunde,
    Rueckmeldung,
)
from . import theme


# --- Hilfsfunktionen ---------------------------------------------------------


def zu_qdate(wert: date | None) -> QDate:
    if wert is None:
        return QDate.currentDate()
    return QDate(wert.year, wert.month, wert.day)


def aus_qdate(wert: QDate) -> date | None:
    if not wert.isValid():
        return None
    return date(wert.year(), wert.month(), wert.day())


def datumsfeld(wert: date | None = None) -> QDateEdit:
    feld = QDateEdit()
    feld.setCalendarPopup(True)
    feld.setDisplayFormat("dd.MM.yyyy")
    feld.setDate(zu_qdate(wert))
    _kalender_gestalten(feld.calendarWidget())
    return feld


def _kalender_gestalten(kalender: QCalendarWidget | None) -> None:
    """Kalender-Popup lesbar machen: kein Gitter, gedaempftes Wochenende.

    Qt faerbt Samstag und Sonntag per Voreinstellung knallrot -- zusammen mit
    dem hellen Grund schlecht lesbar und ohne Bedeutung fuer diese App.
    """
    if kalender is None:
        return
    kalender.setGridVisible(False)
    kalender.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
    kalender.setHorizontalHeaderFormat(QCalendarWidget.ShortDayNames)

    kopfzeile = QTextCharFormat()
    kopfzeile.setForeground(QColor(theme.TEXT_GEDAEMPFT))
    kopfzeile.setFontWeight(600)
    kalender.setHeaderTextFormat(kopfzeile)

    werktag = QTextCharFormat()
    werktag.setForeground(QColor(theme.TEXT))
    wochenende = QTextCharFormat()
    wochenende.setForeground(QColor(theme.TEXT_GEDAEMPFT))
    for tag in (Qt.Monday, Qt.Tuesday, Qt.Wednesday, Qt.Thursday, Qt.Friday):
        kalender.setWeekdayTextFormat(tag, werktag)
    for tag in (Qt.Saturday, Qt.Sunday):
        kalender.setWeekdayTextFormat(tag, wochenende)


def _dateiauswahl(zeile: QLineEdit, titel: str, eltern: QWidget) -> None:
    pfad, _ = QFileDialog.getOpenFileName(eltern, titel, zeile.text() or "")
    if pfad:
        zeile.setText(pfad)


def _pfadzeile(titel: str, eltern: QWidget) -> tuple[QWidget, QLineEdit]:
    behaelter = QWidget()
    layout = QHBoxLayout(behaelter)
    layout.setContentsMargins(0, 0, 0, 0)
    zeile = QLineEdit()
    knopf = QPushButton("Durchsuchen …")
    knopf.clicked.connect(lambda: _dateiauswahl(zeile, titel, eltern))
    layout.addWidget(zeile, 1)
    layout.addWidget(knopf)
    return behaelter, zeile


# --- Interview-Runde ---------------------------------------------------------


class InterviewRundeDialog(QDialog):
    def __init__(self, runde: InterviewRunde, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Interview-Runde")
        self.setMinimumWidth(420)
        self.runde = runde

        self._nummer = QSpinBox()
        self._nummer.setRange(1, 99)
        self._nummer.setValue(runde.runde_nummer)

        self._typ = QComboBox()
        self._typ.addItems(INTERVIEW_TYPEN)
        if runde.typ:
            self._typ.setCurrentText(runde.typ)

        self._datum = datumsfeld(runde.datum or date.today())

        self._ergebnis = QComboBox()
        self._ergebnis.addItems(INTERVIEW_ERGEBNISSE)
        if runde.ergebnis:
            self._ergebnis.setCurrentText(runde.ergebnis)

        self._notizen = QPlainTextEdit(runde.notizen)
        self._notizen.setMinimumHeight(90)

        formular = QFormLayout()
        formular.addRow("Runde", self._nummer)
        formular.addRow("Typ", self._typ)
        formular.addRow("Datum", self._datum)
        formular.addRow("Ergebnis", self._ergebnis)
        formular.addRow("Notizen", self._notizen)

        knoepfe = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        knoepfe.accepted.connect(self.accept)
        knoepfe.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(formular)
        layout.addWidget(knoepfe)

    def accept(self) -> None:
        self.runde.runde_nummer = self._nummer.value()
        self.runde.typ = self._typ.currentText()
        self.runde.datum = aus_qdate(self._datum.date())
        self.runde.ergebnis = self._ergebnis.currentText()
        self.runde.notizen = self._notizen.toPlainText().strip()
        super().accept()


# --- Rueckmeldung ------------------------------------------------------------


class RueckmeldungTab(QWidget):
    """Erfassung der finalen Rueckmeldung inkl. Absagegruenden (Abschnitt 6)."""

    def __init__(self, bewerbung: Bewerbung, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._keine = QRadioButton("Noch keine Rückmeldung")
        self._zusage = QRadioButton("Zusage")
        self._absage = QRadioButton("Absage")
        gruppe = QButtonGroup(self)
        for knopf in (self._keine, self._zusage, self._absage):
            gruppe.addButton(knopf)
        gruppe.setExclusive(True)

        if bewerbung.rueckmeldung_typ is Rueckmeldung.ZUSAGE:
            self._zusage.setChecked(True)
        elif bewerbung.rueckmeldung_typ is Rueckmeldung.ABSAGE:
            self._absage.setChecked(True)
        else:
            self._keine.setChecked(True)

        auswahl = QHBoxLayout()
        auswahl.addWidget(self._keine)
        auswahl.addWidget(self._zusage)
        auswahl.addWidget(self._absage)
        auswahl.addStretch(1)

        self._datum = datumsfeld(bewerbung.rueckmeldung_am or date.today())

        self._kategorien: list[QCheckBox] = []
        kategoriebox = QGroupBox("Absagegründe (Mehrfachauswahl möglich)")
        kategorielayout = QVBoxLayout(kategoriebox)
        for kategorie in ABSAGEGRUND_KATEGORIEN:
            haken = QCheckBox(kategorie)
            haken.setChecked(kategorie in bewerbung.absagegrund_kategorien)
            kategorielayout.addWidget(haken)
            self._kategorien.append(haken)
        self._kategoriebox = kategoriebox

        self._details = QLineEdit(bewerbung.absagegrund_details)
        self._details.setPlaceholderText("Kurze Zusammenfassung der Begründung")
        self._rohtext = QPlainTextEdit(bewerbung.absage_rohtext)
        self._rohtext.setPlaceholderText("Originaltext der erhaltenen Rückmeldung")
        self._rohtext.setMinimumHeight(110)

        formular = QFormLayout()
        formular.addRow("Rückmeldung", auswahl)
        formular.addRow("Datum", self._datum)
        formular.addRow("Details", self._details)
        formular.addRow("Rohtext", self._rohtext)

        hinweis = QLabel(
            "Der Gesamtstatus wird automatisch abgeleitet: eine eingetragene "
            "Rückmeldung setzt die Bewerbung auf Zusage bzw. Absage."
        )
        hinweis.setProperty("rolle", "gedaempft")
        hinweis.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addLayout(formular)
        layout.addWidget(kategoriebox)
        layout.addWidget(hinweis)
        layout.addStretch(1)

        for knopf in (self._keine, self._zusage, self._absage):
            knopf.toggled.connect(self._felder_aktualisieren)
        self._felder_aktualisieren()

    def _felder_aktualisieren(self) -> None:
        ist_absage = self._absage.isChecked()
        hat_rueckmeldung = not self._keine.isChecked()
        self._kategoriebox.setEnabled(ist_absage)
        self._details.setEnabled(ist_absage)
        self._rohtext.setEnabled(hat_rueckmeldung)
        self._datum.setEnabled(hat_rueckmeldung)

    def in_bewerbung_schreiben(self, bewerbung: Bewerbung) -> None:
        if self._zusage.isChecked():
            bewerbung.rueckmeldung_typ = Rueckmeldung.ZUSAGE
        elif self._absage.isChecked():
            bewerbung.rueckmeldung_typ = Rueckmeldung.ABSAGE
        else:
            bewerbung.rueckmeldung_typ = None

        if bewerbung.rueckmeldung_typ is None:
            bewerbung.rueckmeldung_am = None
            bewerbung.absagegrund_kategorien = []
            bewerbung.absagegrund_details = ""
            bewerbung.absage_rohtext = ""
            return

        bewerbung.rueckmeldung_am = aus_qdate(self._datum.date())
        bewerbung.absage_rohtext = self._rohtext.toPlainText().strip()
        if bewerbung.rueckmeldung_typ is Rueckmeldung.ABSAGE:
            bewerbung.absagegrund_kategorien = [
                h.text() for h in self._kategorien if h.isChecked()
            ]
            bewerbung.absagegrund_details = self._details.text().strip()
        else:
            bewerbung.absagegrund_kategorien = []
            bewerbung.absagegrund_details = ""

    def zusage_vorbelegen(self, datum: date | None = None) -> None:
        self._zusage.setChecked(True)
        if datum:
            self._datum.setDate(zu_qdate(datum))
        self._felder_aktualisieren()

    def absage_vorbelegen(
        self, kategorien: list[str], details: str, rohtext: str, datum: date | None
    ) -> None:
        """Uebernimmt Werte aus einem Absage-Import (Format B)."""
        self._absage.setChecked(True)
        for haken in self._kategorien:
            haken.setChecked(haken.text() in kategorien)
        if details:
            self._details.setText(details)
        if rohtext:
            self._rohtext.setPlainText(rohtext)
        if datum:
            self._datum.setDate(zu_qdate(datum))
        self._felder_aktualisieren()


# --- Bewerbung ---------------------------------------------------------------


class BewerbungDialog(QDialog):
    """Anlegen/Bearbeiten inkl. Interview-Runden und Rueckmeldung."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        bewerbung: Bewerbung | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.conn = conn
        self.bewerbung = bewerbung or Bewerbung(beworben_am=date.today())
        self.ist_neu = self.bewerbung.id is None
        self.setWindowTitle("Neue Bewerbung" if self.ist_neu else "Bewerbung bearbeiten")
        self.setMinimumSize(620, 560)

        self._runden: list[InterviewRunde] = list(self.bewerbung.interview_runden)
        self._geloeschte_runden: list[int] = []

        self._tabs = QTabWidget()
        self._tabs.addTab(self._stammdaten_tab(), "Stammdaten")
        self._tabs.addTab(self._runden_tab(), "Interview-Runden")
        self._rueckmeldung = RueckmeldungTab(self.bewerbung)
        self._tabs.addTab(self._rueckmeldung, "Rückmeldung")

        knoepfe = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        knoepfe.button(QDialogButtonBox.Save).setText("Speichern")
        knoepfe.button(QDialogButtonBox.Save).setProperty("rolle", "primaer")
        knoepfe.button(QDialogButtonBox.Cancel).setText("Abbrechen")
        knoepfe.accepted.connect(self.accept)
        knoepfe.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self._tabs)
        layout.addWidget(knoepfe)

    # -- Vorbelegung von aussen --

    def absage_uebernehmen(
        self, kategorien: list[str], details: str, rohtext: str, datum: date | None
    ) -> None:
        """Uebernimmt Werte aus einem Absage-Import und zeigt den Reiter an."""
        self._rueckmeldung.absage_vorbelegen(kategorien, details, rohtext, datum)
        self._tabs.setCurrentWidget(self._rueckmeldung)

    def zusage_uebernehmen(self, datum: date | None = None) -> None:
        self._rueckmeldung.zusage_vorbelegen(datum)
        self._tabs.setCurrentWidget(self._rueckmeldung)

    def runden_reiter_anzeigen(self) -> None:
        self._tabs.setCurrentIndex(1)

    def reiter_anzeigen(self, widget: QWidget) -> None:
        self._tabs.setCurrentWidget(widget)

    @property
    def rueckmeldung_tab(self) -> "RueckmeldungTab":
        return self._rueckmeldung

    # -- Tabs --

    def _stammdaten_tab(self) -> QWidget:
        b = self.bewerbung
        self._firma = QLineEdit(b.firma)
        self._position = QLineEdit(b.position)
        self._weg = QComboBox()
        self._weg.addItems(BEWERBUNGSWEGE)
        if b.bewerbungsweg in BEWERBUNGSWEGE:
            self._weg.setCurrentText(b.bewerbungsweg)
        self._beworben_am = datumsfeld(b.beworben_am or date.today())
        self._skills = QLineEdit(", ".join(b.skills))
        self._skills.setPlaceholderText("Kommagetrennt, z. B. Python, SQL, Projektleitung")
        self._gehalt = QLineEdit(b.gehaltsangabe)
        self._quelle = QLineEdit(b.quelle_url)

        cv_widget, self._cv = _pfadzeile("Lebenslauf auswählen", self)
        self._cv.setText(b.cv_pfad)
        anschreiben_widget, self._anschreiben = _pfadzeile("Anschreiben auswählen", self)
        self._anschreiben.setText(b.anschreiben_pfad)

        self._notizen = QPlainTextEdit(b.notizen)
        self._notizen.setMinimumHeight(90)

        seite = QWidget()
        formular = QFormLayout(seite)
        formular.addRow("Firma *", self._firma)
        formular.addRow("Position *", self._position)
        formular.addRow("Bewerbungsweg", self._weg)
        formular.addRow("Beworben am", self._beworben_am)
        formular.addRow("Skills", self._skills)
        formular.addRow("Gehaltsangabe", self._gehalt)
        formular.addRow("Quelle (URL)", self._quelle)
        formular.addRow("Lebenslauf", cv_widget)
        formular.addRow("Anschreiben", anschreiben_widget)
        formular.addRow("Notizen", self._notizen)
        return seite

    def _runden_tab(self) -> QWidget:
        seite = QWidget()
        layout = QVBoxLayout(seite)

        self._rundenliste = QListWidget()
        self._rundenliste.itemDoubleClicked.connect(lambda _: self._runde_bearbeiten())
        layout.addWidget(self._rundenliste, 1)

        knoepfe = QHBoxLayout()
        hinzufuegen = QPushButton("Runde hinzufügen")
        hinzufuegen.clicked.connect(self._runde_hinzufuegen)
        bearbeiten = QPushButton("Bearbeiten")
        bearbeiten.clicked.connect(self._runde_bearbeiten)
        entfernen = QPushButton("Entfernen")
        entfernen.clicked.connect(self._runde_entfernen)
        knoepfe.addWidget(hinzufuegen)
        knoepfe.addWidget(bearbeiten)
        knoepfe.addWidget(entfernen)
        knoepfe.addStretch(1)
        layout.addLayout(knoepfe)

        hinweis = QLabel(
            "Mindestens eine Runde setzt den Status automatisch auf "
            "„Im Interview-Prozess“. Das Datum der letzten Runde startet außerdem "
            "den Nachfrage-Zähler neu."
        )
        hinweis.setProperty("rolle", "gedaempft")
        hinweis.setWordWrap(True)
        layout.addWidget(hinweis)

        self._runden_anzeigen()
        return seite

    # -- Interview-Runden --

    def _runden_anzeigen(self) -> None:
        self._rundenliste.clear()
        for index, runde in enumerate(sorted(self._runden, key=lambda r: r.runde_nummer)):
            text = runde.anzeigename()
            if runde.ergebnis:
                text += f" · {runde.ergebnis}"
            eintrag = QListWidgetItem(text)
            eintrag.setData(Qt.UserRole, index)
            self._rundenliste.addItem(eintrag)

    def _ausgewaehlte_runde(self) -> InterviewRunde | None:
        eintrag = self._rundenliste.currentItem()
        if eintrag is None:
            return None
        sortiert = sorted(self._runden, key=lambda r: r.runde_nummer)
        return sortiert[eintrag.data(Qt.UserRole)]

    def _runde_hinzufuegen(self) -> None:
        nummer = max((r.runde_nummer for r in self._runden), default=0) + 1
        runde = InterviewRunde(
            bewerbung_id=self.bewerbung.id, runde_nummer=nummer, datum=date.today()
        )
        if InterviewRundeDialog(runde, self).exec() == QDialog.Accepted:
            self._runden.append(runde)
            self._runden_anzeigen()

    def _runde_bearbeiten(self) -> None:
        runde = self._ausgewaehlte_runde()
        if runde is None:
            return
        if InterviewRundeDialog(runde, self).exec() == QDialog.Accepted:
            self._runden_anzeigen()

    def _runde_entfernen(self) -> None:
        runde = self._ausgewaehlte_runde()
        if runde is None:
            return
        if runde.id is not None:
            self._geloeschte_runden.append(runde.id)
        self._runden.remove(runde)
        self._runden_anzeigen()

    # -- Speichern --

    def accept(self) -> None:
        firma = self._firma.text().strip()
        position = self._position.text().strip()
        if not firma or not position:
            QMessageBox.warning(
                self, "Pflichtfelder", "Firma und Position müssen ausgefüllt sein."
            )
            self._tabs.setCurrentIndex(0)
            return

        b = self.bewerbung
        b.firma = firma
        b.position = position
        b.bewerbungsweg = self._weg.currentText()
        b.beworben_am = aus_qdate(self._beworben_am.date())
        b.skills = [t.strip() for t in self._skills.text().split(",") if t.strip()]
        b.gehaltsangabe = self._gehalt.text().strip()
        b.quelle_url = self._quelle.text().strip()
        b.cv_pfad = self._cv.text().strip()
        b.anschreiben_pfad = self._anschreiben.text().strip()
        b.notizen = self._notizen.toPlainText().strip()
        self._rueckmeldung.in_bewerbung_schreiben(b)
        b.interview_runden = self._runden

        bewerbung_id = repository.bewerbung_speichern(self.conn, b)
        for runde_id in self._geloeschte_runden:
            repository.runde_loeschen(self.conn, runde_id)
        for runde in self._runden:
            runde.bewerbung_id = bewerbung_id
            repository.runde_speichern(self.conn, runde)

        # Status haengt von den gerade gespeicherten Runden ab -> neu ableiten.
        aktualisiert = repository.bewerbung_laden(self.conn, bewerbung_id)
        if aktualisiert is not None:
            self.bewerbung = aktualisiert
        super().accept()


# --- Einstellungen -----------------------------------------------------------


class EinstellungenDialog(QDialog):
    def __init__(self, conn: sqlite3.Connection, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.conn = conn
        self.setWindowTitle("Einstellungen")
        self.setMinimumWidth(520)

        self._reminder = QSpinBox()
        self._reminder.setRange(1, 365)
        self._reminder.setSuffix(" Tage")
        self._reminder.setValue(database.einstellung_int(conn, "reminder_tage", 14))

        self._ghosting = QSpinBox()
        self._ghosting.setRange(1, 365)
        self._ghosting.setSuffix(" Tage")
        self._ghosting.setValue(database.einstellung_int(conn, "ghosting_tage", 30))

        ordner_widget = QWidget()
        ordner_layout = QHBoxLayout(ordner_widget)
        ordner_layout.setContentsMargins(0, 0, 0, 0)
        self._ordner = QLineEdit(database.einstellung_lesen(conn, "import_ordner"))
        ordner_knopf = QPushButton("Durchsuchen …")
        ordner_knopf.clicked.connect(self._ordner_waehlen)
        ordner_layout.addWidget(self._ordner, 1)
        ordner_layout.addWidget(ordner_knopf)

        self._api_key = QLineEdit(database.einstellung_lesen(conn, "anthropic_api_key"))
        self._api_key.setEchoMode(QLineEdit.Password)
        self._api_key.setPlaceholderText("Optional – noch ohne Funktion")

        formular = QFormLayout()
        formular.addRow("Nachfragen empfehlen nach", self._reminder)
        formular.addRow("Als Ghosting werten nach", self._ghosting)
        formular.addRow("Überwachter Import-Ordner", ordner_widget)
        formular.addRow("Anthropic API-Key", self._api_key)

        hinweis = QLabel(
            "Beide Schwellenwerte gelten global für alle Bewerbungen und zählen ab "
            "dem letzten Ereignis ohne Reaktion (Bewerbung bzw. letzte "
            "Interview-Runde). Auf denselben Wert gesetzt verhalten sie sich wie ein "
            "einziger Schwellenwert."
        )
        hinweis.setProperty("rolle", "gedaempft")
        hinweis.setWordWrap(True)

        knoepfe = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        knoepfe.accepted.connect(self.accept)
        knoepfe.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(formular)
        layout.addWidget(hinweis)
        layout.addWidget(knoepfe)

    def _ordner_waehlen(self) -> None:
        pfad = QFileDialog.getExistingDirectory(
            self, "Import-Ordner wählen", self._ordner.text() or ""
        )
        if pfad:
            self._ordner.setText(pfad)

    def accept(self) -> None:
        if self._ghosting.value() < self._reminder.value():
            QMessageBox.warning(
                self,
                "Schwellenwerte",
                "Die Ghosting-Schwelle darf nicht kleiner sein als die "
                "Nachfrage-Schwelle.",
            )
            return
        database.einstellung_schreiben(self.conn, "reminder_tage", str(self._reminder.value()))
        database.einstellung_schreiben(self.conn, "ghosting_tage", str(self._ghosting.value()))
        database.einstellung_schreiben(self.conn, "import_ordner", self._ordner.text().strip())
        database.einstellung_schreiben(
            self.conn, "anthropic_api_key", self._api_key.text().strip()
        )
        super().accept()
