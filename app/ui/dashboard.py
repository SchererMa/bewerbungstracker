"""Dashboard als Startansicht (Spezifikation Abschnitt 8)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .. import statistik
from ..models import Bewerbung
from . import theme
from .charts import BalkenDiagramm, KreisDiagramm


def _karte(titel: str) -> tuple[QFrame, QVBoxLayout]:
    rahmen = QFrame()
    rahmen.setProperty("rolle", "karte")
    layout = QVBoxLayout(rahmen)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(8)
    beschriftung = QLabel(titel)
    beschriftung.setProperty("rolle", "untertitel")
    layout.addWidget(beschriftung)
    return rahmen, layout


class Kennzahlkachel(QFrame):
    def __init__(self, titel: str, farbe: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("rolle", "karte")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(0)
        self._wert = QLabel("0")
        self._wert.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {farbe};")
        beschriftung = QLabel(titel)
        beschriftung.setStyleSheet(f"color: {theme.TEXT_GEDAEMPFT};")
        layout.addWidget(self._wert)
        layout.addWidget(beschriftung)

    def wert_setzen(self, wert: int) -> None:
        self._wert.setText(str(wert))


class Dashboard(QScrollArea):
    """Startbildschirm mit Kennzahlen, Diagrammen und Arbeitslisten."""

    bewerbung_geoeffnet = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)

        inhalt = QWidget()
        self.setWidget(inhalt)
        layout = QVBoxLayout(inhalt)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        titel = QLabel("Dashboard")
        titel.setProperty("rolle", "titel")
        layout.addWidget(titel)

        # -- Kennzahlen --
        self._kacheln = {
            "gesamt": Kennzahlkachel("Bewerbungen gesamt", theme.TEXT),
            "offen": Kennzahlkachel("Offen", theme.GRUPPEN_FARBEN["Offen"]),
            "zusagen": Kennzahlkachel("Zusagen", theme.GRUPPEN_FARBEN["Zusage"]),
            "absagen": Kennzahlkachel("Absagen", theme.GRUPPEN_FARBEN["Absage"]),
            "nachfassen": Kennzahlkachel("Nachfassen", theme.WARNFARBE),
        }
        kachelzeile = QHBoxLayout()
        kachelzeile.setSpacing(12)
        for kachel in self._kacheln.values():
            kachelzeile.addWidget(kachel, 1)
        layout.addLayout(kachelzeile)

        # -- Diagramme --
        gitter = QGridLayout()
        gitter.setSpacing(12)

        kreis_karte, kreis_layout = _karte("Verhältnis Zusage / Absage / Offen / Ghosting")
        self._kreis = KreisDiagramm()
        kreis_layout.addWidget(self._kreis, 1)
        gitter.addWidget(kreis_karte, 0, 0)

        balken_karte, balken_layout = _karte("Häufigste Absagegründe")
        self._balken = BalkenDiagramm()
        balken_layout.addWidget(self._balken, 1)
        gitter.addWidget(balken_karte, 0, 1)

        # -- Listen --
        offen_karte, offen_layout = _karte("Aktuell offene Bewerbungen")
        self._offen = self._liste()
        offen_layout.addWidget(self._offen, 1)
        gitter.addWidget(offen_karte, 1, 0)

        nachfass_karte, nachfass_layout = _karte("Nachfragen empfohlen")
        self._nachfass = self._liste()
        nachfass_layout.addWidget(self._nachfass, 1)
        gitter.addWidget(nachfass_karte, 1, 1)

        gitter.setColumnStretch(0, 1)
        gitter.setColumnStretch(1, 1)
        gitter.setRowMinimumHeight(0, 230)
        gitter.setRowMinimumHeight(1, 250)
        layout.addLayout(gitter, 1)

    def _liste(self) -> QListWidget:
        liste = QListWidget()
        liste.setAlternatingRowColors(False)
        liste.setTextElideMode(Qt.ElideRight)
        liste.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        liste.setWordWrap(False)
        liste.itemDoubleClicked.connect(self._eintrag_geoeffnet)
        liste.setToolTip("Doppelklick öffnet die Bewerbung")
        return liste

    def _eintrag_geoeffnet(self, eintrag: QListWidgetItem) -> None:
        bewerbung_id = eintrag.data(Qt.UserRole)
        if bewerbung_id is not None:
            self.bewerbung_geoeffnet.emit(int(bewerbung_id))

    # -- Aktualisierung --

    def aktualisieren(self, bewerbungen: list[Bewerbung], reminder_tage: int) -> None:
        werte = statistik.kennzahlen(bewerbungen, reminder_tage)
        for schluessel, kachel in self._kacheln.items():
            kachel.wert_setzen(werte[schluessel])

        verteilung = statistik.status_verteilung(bewerbungen)
        self._kreis.daten_setzen(
            [
                (gruppe, anzahl, theme.GRUPPEN_FARBEN[gruppe])
                for gruppe, anzahl in verteilung.items()
            ]
        )

        gruende = statistik.absagegruende(bewerbungen)
        self._balken.daten_setzen(
            [(kategorie, anzahl, theme.BALKEN_FARBE) for kategorie, anzahl in gruende]
        )

        self._offen.clear()
        for bewerbung, tage in statistik.offene_bewerbungen(bewerbungen):
            alter = f"{tage} Tage ohne Reaktion" if tage is not None else "ohne Datum"
            eintrag = QListWidgetItem(
                f"{bewerbung.anzeigename()}  ·  {bewerbung.status.value}  ·  {alter}"
            )
            eintrag.setData(Qt.UserRole, bewerbung.id)
            self._offen.addItem(eintrag)
        if self._offen.count() == 0:
            self._offen.addItem(QListWidgetItem("Keine offenen Bewerbungen"))

        self._nachfass.clear()
        for bewerbung, tage in statistik.nachfassliste(bewerbungen, reminder_tage):
            eintrag = QListWidgetItem(
                f"{bewerbung.anzeigename()}  ·  seit {tage} Tagen keine Reaktion"
            )
            eintrag.setData(Qt.UserRole, bewerbung.id)
            eintrag.setForeground(Qt.darkRed)
            self._nachfass.addItem(eintrag)
        if self._nachfass.count() == 0:
            self._nachfass.addItem(
                QListWidgetItem(f"Nichts zu tun – Schwelle: {reminder_tage} Tage")
            )
