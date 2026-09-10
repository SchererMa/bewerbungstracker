"""Leichtgewichtige Diagramme fuer das Dashboard.

Bewusst mit QPainter selbst gezeichnet statt via QtCharts/matplotlib: keine
zusaetzliche Abhaengigkeit, kleineres PyInstaller-Paket und volle Kontrolle
ueber die Darstellung.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from . import theme


class _Diagramm(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._daten: list[tuple[str, float, str]] = []
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def daten_setzen(self, daten: list[tuple[str, float, str]]) -> None:
        """daten: Liste aus (Beschriftung, Wert, Farbe als Hex-String)."""
        self._daten = daten
        self.update()

    def _leer_zeichnen(self, painter: QPainter, text: str) -> None:
        painter.setPen(QPen(QColor(theme.TEXT_GEDAEMPFT)))
        painter.drawText(self.rect(), Qt.AlignCenter, text)


class KreisDiagramm(_Diagramm):
    """Ringdiagramm mit Legende rechts."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(180)

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt-Namenskonvention)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        gesamt = sum(wert for _, wert, _ in self._daten)
        if gesamt <= 0:
            self._leer_zeichnen(painter, "Noch keine Bewerbungen erfasst")
            return

        rand = 12
        groesse = min(self.height() - 2 * rand, max(120, self.width() * 0.45))
        kreis = QRectF(rand, (self.height() - groesse) / 2, groesse, groesse)

        start = 90 * 16
        for _, wert, farbe in self._daten:
            if wert <= 0:
                continue
            spanne = int(round(360 * 16 * wert / gesamt))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(farbe))
            painter.drawPie(kreis, start, -spanne)
            start -= spanne

        # Innenkreis fuer die Ringoptik plus Gesamtzahl.
        loch = kreis.adjusted(
            groesse * 0.27, groesse * 0.27, -groesse * 0.27, -groesse * 0.27
        )
        painter.setBrush(QColor(theme.FLAECHE))
        painter.drawEllipse(loch)

        schrift = QFont(self.font())
        schrift.setPointSizeF(max(10.0, groesse * 0.11))
        schrift.setBold(True)
        painter.setFont(schrift)
        painter.setPen(QPen(QColor(theme.TEXT)))
        painter.drawText(loch, Qt.AlignCenter, str(int(gesamt)))

        self._legende_zeichnen(painter, kreis.right() + 18, gesamt)

    def _legende_zeichnen(self, painter: QPainter, x: float, gesamt: float) -> None:
        painter.setFont(self.font())
        metrik = QFontMetrics(self.font())
        zeilenhoehe = metrik.height() + 8
        eintraege = [(t, w, f) for t, w, f in self._daten]
        y = (self.height() - zeilenhoehe * len(eintraege)) / 2 + zeilenhoehe / 2

        for beschriftung, wert, farbe in eintraege:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(farbe))
            painter.drawRoundedRect(QRectF(x, y - 5, 10, 10), 2, 2)
            painter.setPen(QPen(QColor(theme.TEXT)))
            anteil = 100 * wert / gesamt if gesamt else 0
            text = f"{beschriftung}: {int(wert)} ({anteil:.0f} %)"
            painter.drawText(
                QRectF(x + 16, y - zeilenhoehe / 2, self.width() - x - 20, zeilenhoehe),
                Qt.AlignVCenter | Qt.AlignLeft,
                text,
            )
            y += zeilenhoehe


class BalkenDiagramm(_Diagramm):
    """Horizontale Balken -- geeignet fuer lange Kategorienamen."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(180)
        self._leertext = "Noch keine Absagegruende erfasst"

    def leertext_setzen(self, text: str) -> None:
        self._leertext = text
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt-Namenskonvention)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if not self._daten:
            self._leer_zeichnen(painter, self._leertext)
            return

        metrik = QFontMetrics(self.font())
        beschriftungsbreite = min(
            max(metrik.horizontalAdvance(t) for t, _, _ in self._daten) + 12,
            int(self.width() * 0.45),
        )
        maximum = max(wert for _, wert, _ in self._daten) or 1
        zeilenhoehe = min(34, max(20, self.height() / max(1, len(self._daten))))
        balkenhoehe = zeilenhoehe * 0.6
        y = 4.0

        for beschriftung, wert, farbe in self._daten:
            if y + zeilenhoehe > self.height():
                break
            painter.setPen(QPen(QColor(theme.TEXT)))
            text = metrik.elidedText(beschriftung, Qt.ElideRight, beschriftungsbreite - 8)
            painter.drawText(
                QRectF(0, y, beschriftungsbreite - 8, zeilenhoehe),
                Qt.AlignVCenter | Qt.AlignRight,
                text,
            )

            verfuegbar = self.width() - beschriftungsbreite - 40
            breite = max(3.0, verfuegbar * wert / maximum)
            balken = QRectF(
                beschriftungsbreite,
                y + (zeilenhoehe - balkenhoehe) / 2,
                breite,
                balkenhoehe,
            )
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(farbe))
            painter.drawRoundedRect(balken, 4, 4)

            painter.setPen(QPen(QColor(theme.TEXT_GEDAEMPFT)))
            painter.drawText(
                QRectF(balken.right() + 6, y, 34, zeilenhoehe),
                Qt.AlignVCenter | Qt.AlignLeft,
                str(int(wert)),
            )
            y += zeilenhoehe


def kreis_hoehe_fuer(anzahl_eintraege: int) -> int:
    """Sinnvolle Mindesthoehe, damit die Legende vollstaendig passt."""
    return int(max(180, 40 + 26 * math.ceil(anzahl_eintraege)))
