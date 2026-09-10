"""Import-Dialog fuer die KI-JSON-Dateien (Spezifikation Abschnitt 5)."""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from .. import repository
from ..importer import (
    AbsageImport,
    ImportFehler,
    ImportFormat,
    StellenanzeigeImport,
    datei_lesen,
)
from ..models import Bewerbung
from .dialoge import BewerbungDialog


class ImportDialog(QDialog):
    """Zeigt den Inhalt einer Import-Datei und uebernimmt ihn nach Bestaetigung.

    Format A legt eine neue Bewerbung an, Format B wird einer bestehenden
    Bewerbung manuell zugeordnet -- die Datei enthaelt dafuer bewusst keine
    Referenz.
    """

    def __init__(
        self,
        conn: sqlite3.Connection,
        pfad: Path | str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.conn = conn
        self.pfad = Path(pfad)
        self.bewerbung_id: int | None = None
        self.setWindowTitle("JSON-Import")
        self.setMinimumWidth(560)

        self.format_, self.daten = datei_lesen(self.pfad)

        layout = QVBoxLayout(self)
        kopf = QLabel(
            ("Format A – Stellenanzeige" if self.format_ is ImportFormat.STELLENANZEIGE
             else "Format B – Absage")
            + f"\n{self.pfad.name}"
        )
        kopf.setProperty("rolle", "untertitel")
        layout.addWidget(kopf)

        formular = QFormLayout()
        self._zuordnung: QComboBox | None = None

        if isinstance(self.daten, StellenanzeigeImport):
            self._stellenanzeige_anzeigen(formular, self.daten)
        else:
            self._absage_anzeigen(formular, self.daten)
        layout.addLayout(formular)

        if self.daten.hinweise:
            hinweis = QLabel("Hinweise:\n• " + "\n• ".join(self.daten.hinweise))
            hinweis.setProperty("rolle", "gedaempft")
            hinweis.setWordWrap(True)
            layout.addWidget(hinweis)

        erklaerung = QLabel(
            "Nach dem Bestätigen öffnet sich das Formular zur Kontrolle. "
            "Gespeichert wird erst dort."
        )
        erklaerung.setProperty("rolle", "gedaempft")
        erklaerung.setWordWrap(True)
        layout.addWidget(erklaerung)

        knoepfe = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        knoepfe.button(QDialogButtonBox.Ok).setText("Übernehmen …")
        knoepfe.button(QDialogButtonBox.Ok).setProperty("rolle", "primaer")
        knoepfe.button(QDialogButtonBox.Cancel).setText("Abbrechen")
        knoepfe.accepted.connect(self.accept)
        knoepfe.rejected.connect(self.reject)
        layout.addWidget(knoepfe)

    # -- Anzeige --

    def _stellenanzeige_anzeigen(
        self, formular: QFormLayout, daten: StellenanzeigeImport
    ) -> None:
        formular.addRow("Firma", QLabel(daten.firma or "—"))
        formular.addRow("Position", QLabel(daten.position or "—"))
        formular.addRow("Skills", QLabel(", ".join(daten.skills) or "—"))
        formular.addRow("Gehaltsangabe", QLabel(daten.gehaltsangabe or "—"))
        formular.addRow("Bewerbungsweg", QLabel(daten.bewerbungsweg()))
        formular.addRow("Quelle", QLabel(daten.quelle_url or "—"))

    def _absage_anzeigen(self, formular: QFormLayout, daten: AbsageImport) -> None:
        self._zuordnung = QComboBox()
        offene = repository.alle_bewerbungen(self.conn)
        for bewerbung in offene:
            self._zuordnung.addItem(
                f"{bewerbung.anzeigename()} ({bewerbung.status.value})", bewerbung.id
            )
        if not offene:
            self._zuordnung.addItem("Keine Bewerbung vorhanden", None)
            self._zuordnung.setEnabled(False)

        formular.addRow("Zuordnen zu *", self._zuordnung)
        formular.addRow(
            "Kategorien", QLabel(", ".join(daten.absagegrund_kategorien) or "—")
        )
        formular.addRow("Details", QLabel(daten.absagegrund_details or "—"))
        formular.addRow(
            "Datum", QLabel(daten.datum.strftime("%d.%m.%Y") if daten.datum else "—")
        )
        rohtext = QPlainTextEdit(daten.rohtext)
        rohtext.setReadOnly(True)
        rohtext.setMinimumHeight(110)
        formular.addRow("Rohtext", rohtext)

    # -- Uebernahme --

    def accept(self) -> None:
        if isinstance(self.daten, StellenanzeigeImport):
            erfolg = self._neue_bewerbung()
        else:
            erfolg = self._absage_zuordnen()
        if erfolg:
            super().accept()

    def _neue_bewerbung(self) -> bool:
        daten: StellenanzeigeImport = self.daten  # type: ignore[assignment]
        entwurf = Bewerbung(
            firma=daten.firma,
            position=daten.position,
            skills=daten.skills,
            gehaltsangabe=daten.gehaltsangabe,
            quelle_url=daten.quelle_url,
            bewerbungsweg=daten.bewerbungsweg(),
            beworben_am=date.today(),
        )
        dialog = BewerbungDialog(self.conn, entwurf, self)
        if dialog.exec() != QDialog.Accepted:
            return False
        self.bewerbung_id = dialog.bewerbung.id
        return True

    def _absage_zuordnen(self) -> bool:
        daten: AbsageImport = self.daten  # type: ignore[assignment]
        bewerbung_id = self._zuordnung.currentData() if self._zuordnung else None
        if bewerbung_id is None:
            QMessageBox.warning(
                self,
                "Zuordnung fehlt",
                "Bitte eine bestehende Bewerbung auswählen, zu der die Absage gehört.",
            )
            return False

        bewerbung = repository.bewerbung_laden(self.conn, int(bewerbung_id))
        if bewerbung is None:
            return False

        dialog = BewerbungDialog(self.conn, bewerbung, self)
        dialog.absage_uebernehmen(
            daten.absagegrund_kategorien,
            daten.absagegrund_details,
            daten.rohtext,
            daten.datum,
        )
        if dialog.exec() != QDialog.Accepted:
            return False
        self.bewerbung_id = dialog.bewerbung.id
        return True


def import_starten(
    conn: sqlite3.Connection, pfad: Path | str, parent: QWidget | None = None
) -> int | None:
    """Oeffnet den Import-Dialog und gibt die betroffene Bewerbungs-ID zurueck."""
    try:
        dialog = ImportDialog(conn, pfad, parent)
    except ImportFehler as fehler:
        QMessageBox.critical(parent, "Import fehlgeschlagen", str(fehler))
        return None
    if dialog.exec() == QDialog.Accepted:
        return dialog.bewerbung_id
    return None
