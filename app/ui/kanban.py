"""Kanban-Board nach Status (Spezifikation Abschnitt 9).

PySide6 bringt kein fertiges Kanban-Widget mit -- Spalten, Karten und das
Drag-&-Drop-Handling sind daher selbst implementiert.

Weil der Gesamtstatus laut Abschnitt 4 immer abgeleitet und nie direkt gesetzt
wird, verschiebt ein Drop die Karte nicht einfach: Das Board meldet den
gewuenschten Zielstatus nach oben, und das Hauptfenster oeffnet die dazu
passende Aktion (Interview-Runde anlegen, Rueckmeldung eintragen, ...).
"""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..models import STATUS_REIHENFOLGE, Bewerbung, Status
from ..status import tage_ohne_reaktion
from . import theme

MIME_TYP = "application/x-bewerbungstracker-id"


class KanbanKarte(QFrame):
    """Eine Bewerbung als Karte. Startet bei Ziehen einen Drag-Vorgang."""

    oeffnen = Signal(int)
    kontextmenue = Signal(int, QPoint)

    def __init__(
        self,
        bewerbung: Bewerbung,
        reminder_tage: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.bewerbung = bewerbung
        self._pressposition: QPoint | None = None
        self.setCursor(Qt.OpenHandCursor)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(
            lambda punkt: self.kontextmenue.emit(bewerbung.id, self.mapToGlobal(punkt))
        )

        farbe = theme.STATUS_FARBEN.get(bewerbung.status, theme.BALKEN_FARBE)
        self.setStyleSheet(
            "KanbanKarte {"
            f" background: {theme.FLAECHE};"
            f" border: 1px solid {theme.RAHMEN};"
            f" border-left: 4px solid {farbe};"
            " border-radius: 8px; }"
            "KanbanKarte:hover { border-color: #94a3b8; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        firma = QLabel(bewerbung.firma or "(ohne Firma)")
        firma.setStyleSheet("font-weight: 600;")
        firma.setWordWrap(True)
        layout.addWidget(firma)

        position = QLabel(bewerbung.position or "(ohne Position)")
        position.setWordWrap(True)
        layout.addWidget(position)

        layout.addWidget(self._metazeile(reminder_tage))

    def _metazeile(self, reminder_tage: int) -> QWidget:
        zeile = QWidget()
        layout = QHBoxLayout(zeile)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)

        b = self.bewerbung
        datum = b.beworben_am.strftime("%d.%m.%Y") if b.beworben_am else "ohne Datum"
        info = QLabel(f"{datum} · {b.bewerbungsweg}")
        info.setProperty("rolle", "gedaempft")
        info.setStyleSheet(f"color: {theme.TEXT_GEDAEMPFT}; font-size: 11px;")
        layout.addWidget(info)
        layout.addStretch(1)

        if b.interview_runden:
            runden = QLabel(f"{len(b.interview_runden)} Runde(n)")
            runden.setStyleSheet(f"color: {theme.TEXT_GEDAEMPFT}; font-size: 11px;")
            layout.addWidget(runden)

        tage = tage_ohne_reaktion(b)
        if tage is not None and b.status in {Status.BEWORBEN, Status.INTERVIEW, Status.GHOSTING}:
            marke = QLabel(f"{tage} T")
            faellig = reminder_tage > 0 and tage >= reminder_tage
            hintergrund = theme.WARNFARBE if faellig else "#e2e8f0"
            schriftfarbe = "#ffffff" if faellig else theme.TEXT_GEDAEMPFT
            marke.setStyleSheet(
                f"background: {hintergrund}; color: {schriftfarbe}; font-size: 11px;"
                " border-radius: 6px; padding: 1px 6px;"
            )
            marke.setToolTip(
                f"{tage} Tage ohne Reaktion"
                + (" – Nachfragen empfohlen" if faellig else "")
            )
            layout.addWidget(marke)
        return zeile

    # -- Drag & Drop --

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self._pressposition = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._pressposition is None or not (event.buttons() & Qt.LeftButton):
            return
        abstand = (event.position().toPoint() - self._pressposition).manhattanLength()
        if abstand < 12:
            return

        drag = QDrag(self)
        nutzdaten = QMimeData()
        nutzdaten.setData(MIME_TYP, str(self.bewerbung.id).encode("ascii"))
        drag.setMimeData(nutzdaten)
        abbild = self.grab()
        drag.setPixmap(abbild)
        drag.setHotSpot(self._pressposition)
        self._pressposition = None
        drag.exec(Qt.MoveAction)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        if self.bewerbung.id is not None:
            self.oeffnen.emit(self.bewerbung.id)


class KanbanSpalte(QFrame):
    """Eine Statusspalte inklusive Drop-Ziel."""

    abgelegt = Signal(int, str)

    def __init__(self, status: Status, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.status = status
        self.setAcceptDrops(True)
        self.setMinimumWidth(230)
        self.setProperty("rolle", "karte")
        self._standardstil = (
            "KanbanSpalte { background: #e9eef5; border: 1px solid "
            f"{theme.RAHMEN}; border-radius: 10px; }}"
        )
        self._hoverstil = (
            "KanbanSpalte { background: #dbeafe; border: 1px dashed "
            f"{theme.STATUS_FARBEN[status]}; border-radius: 10px; }}"
        )
        self.setStyleSheet(self._standardstil)

        aussen = QVBoxLayout(self)
        aussen.setContentsMargins(8, 8, 8, 8)
        aussen.setSpacing(6)

        kopf = QWidget()
        kopflayout = QHBoxLayout(kopf)
        kopflayout.setContentsMargins(2, 0, 2, 0)
        punkt = QLabel("●")
        punkt.setStyleSheet(f"color: {theme.STATUS_FARBEN[status]};")
        titel = QLabel(status.value)
        titel.setStyleSheet("font-weight: 600;")
        titel.setWordWrap(True)
        self._zaehler = QLabel("0")
        self._zaehler.setStyleSheet(
            f"color: {theme.TEXT_GEDAEMPFT}; background: {theme.FLAECHE};"
            " border-radius: 8px; padding: 0px 6px;"
        )
        kopflayout.addWidget(punkt)
        kopflayout.addWidget(titel, 1)
        kopflayout.addWidget(self._zaehler)
        aussen.addWidget(kopf)

        self._bereich = QScrollArea()
        self._bereich.setWidgetResizable(True)
        self._bereich.setFrameShape(QFrame.NoFrame)
        self._bereich.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Viewport transparent halten, sonst liegt ein weisser Block unter den Karten.
        self._bereich.setStyleSheet("QScrollArea, QScrollArea > QWidget { background: transparent; }")
        self._bereich.viewport().setAutoFillBackground(False)
        self._inhalt = QWidget()
        self._inhalt.setStyleSheet("background: transparent;")
        self._inhaltslayout = QVBoxLayout(self._inhalt)
        self._inhaltslayout.setContentsMargins(0, 0, 0, 0)
        self._inhaltslayout.setSpacing(6)
        self._inhaltslayout.addStretch(1)
        self._bereich.setWidget(self._inhalt)
        aussen.addWidget(self._bereich, 1)

        self._leerhinweis = QLabel("Keine Einträge")
        self._leerhinweis.setAlignment(Qt.AlignCenter)
        self._leerhinweis.setStyleSheet(f"color: {theme.TEXT_GEDAEMPFT};")
        self._inhaltslayout.insertWidget(0, self._leerhinweis)

    def karten_leeren(self) -> None:
        while self._inhaltslayout.count() > 1:
            eintrag = self._inhaltslayout.takeAt(0)
            widget = eintrag.widget()
            if widget is not None and widget is not self._leerhinweis:
                widget.deleteLater()
        self._inhaltslayout.insertWidget(0, self._leerhinweis)
        self._leerhinweis.show()
        self._zaehler.setText("0")

    def karte_hinzufuegen(self, karte: KanbanKarte) -> None:
        self._leerhinweis.hide()
        einfuegeposition = max(0, self._inhaltslayout.count() - 2)
        self._inhaltslayout.insertWidget(einfuegeposition, karte)
        self._zaehler.setText(str(int(self._zaehler.text()) + 1))

    # -- Drop-Ziel --

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasFormat(MIME_TYP):
            event.acceptProposedAction()
            self.setStyleSheet(self._hoverstil)

    def dragMoveEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasFormat(MIME_TYP):
            event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self.setStyleSheet(self._standardstil)

    def dropEvent(self, event) -> None:  # noqa: N802
        self.setStyleSheet(self._standardstil)
        if not event.mimeData().hasFormat(MIME_TYP):
            return
        rohwert = bytes(event.mimeData().data(MIME_TYP)).decode("ascii")
        try:
            bewerbung_id = int(rohwert)
        except ValueError:
            return
        event.acceptProposedAction()
        self.abgelegt.emit(bewerbung_id, self.status.value)


class KanbanBoard(QWidget):
    """Fuenf Statusspalten nebeneinander."""

    bewerbung_geoeffnet = Signal(int)
    status_gewuenscht = Signal(int, str)
    kontextmenue_gewuenscht = Signal(int, QPoint)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self._spalten: dict[Status, KanbanSpalte] = {}
        for status in STATUS_REIHENFOLGE:
            spalte = KanbanSpalte(status)
            spalte.abgelegt.connect(self.status_gewuenscht.emit)
            layout.addWidget(spalte, 1)
            self._spalten[status] = spalte

    def anzeigen(self, bewerbungen: list[Bewerbung], reminder_tage: int) -> None:
        for spalte in self._spalten.values():
            spalte.karten_leeren()
        for bewerbung in bewerbungen:
            spalte = self._spalten.get(bewerbung.status)
            if spalte is None:
                continue
            karte = KanbanKarte(bewerbung, reminder_tage)
            karte.oeffnen.connect(self.bewerbung_geoeffnet.emit)
            karte.kontextmenue.connect(self.kontextmenue_gewuenscht.emit)
            spalte.karte_hinzufuegen(karte)


def kontextmenue_bauen(parent: QWidget) -> QMenu:
    """Leeres Menue mit einheitlichem Aussehen -- Aktionen ergaenzt der Aufrufer."""
    menue = QMenu(parent)
    menue.setStyleSheet(
        f"QMenu {{ background: {theme.FLAECHE}; border: 1px solid {theme.RAHMEN}; }}"
        "QMenu::item:selected { background: #dbeafe; }"
    )
    return menue


def heute() -> date:
    return date.today()
