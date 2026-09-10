"""Farben und gemeinsames Stylesheet der Oberflaeche."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette

from ..models import Status

#: Akzentfarbe je Status -- verwendet in Kanban-Spalten, Karten und Diagrammen.
STATUS_FARBEN: dict[Status, str] = {
    Status.BEWORBEN: "#3b82f6",
    Status.INTERVIEW: "#a855f7",
    Status.ZUSAGE: "#22c55e",
    Status.ABSAGE: "#ef4444",
    Status.GHOSTING: "#94a3b8",
}

#: Farben der Dashboard-Gruppen (Abschnitt 8, Kreisdiagramm).
GRUPPEN_FARBEN: dict[str, str] = {
    "Zusage": "#22c55e",
    "Absage": "#ef4444",
    "Offen": "#3b82f6",
    "Ghosting": "#94a3b8",
}

BALKEN_FARBE = "#6366f1"
WARNFARBE = "#f59e0b"

HINTERGRUND = "#f1f5f9"
FLAECHE = "#ffffff"
RAHMEN = "#dbe2ea"
TEXT = "#0f172a"
TEXT_GEDAEMPFT = "#64748b"
TEXT_DEAKTIVIERT = "#94a3b8"
#: Grund gesperrter Eingabefelder -- ohne ihn sehen sie aus wie bedienbare.
FLAECHE_DEAKTIVIERT = "#f8fafc"

#: Auswahlfarben fuer Popups (Dropdown-Liste, Kalender, Menues).
AUSWAHL = "#2563eb"
AUSWAHL_TEXT = "#ffffff"
#: Hellere Auswahl fuer markierten Text in Eingabefeldern.
TEXTAUSWAHL = "#bfdbfe"
SCHWEBEN = "#eff6ff"


def palette() -> QPalette:
    """Feste helle Palette -- erst nach dem QApplication-Start aufrufen.

    Ohne das erben Popups (QComboBox-Liste, QCalendarWidget, QMenu) unter
    Windows im Dunkelmodus die dunkle Systempalette samt Systemakzentfarbe,
    waehrend das Stylesheet die uebrigen Widgets hell haelt -- Ergebnis war
    dunkler Text auf dunklem Grund.
    """
    p = QPalette()
    p.setColor(QPalette.Window, QColor(HINTERGRUND))
    p.setColor(QPalette.WindowText, QColor(TEXT))
    p.setColor(QPalette.Base, QColor(FLAECHE))
    p.setColor(QPalette.AlternateBase, QColor("#f8fafc"))
    p.setColor(QPalette.Text, QColor(TEXT))
    p.setColor(QPalette.PlaceholderText, QColor(TEXT_GEDAEMPFT))
    p.setColor(QPalette.Button, QColor(FLAECHE))
    p.setColor(QPalette.ButtonText, QColor(TEXT))
    p.setColor(QPalette.BrightText, QColor("#ffffff"))
    p.setColor(QPalette.ToolTipBase, QColor(FLAECHE))
    p.setColor(QPalette.ToolTipText, QColor(TEXT))
    p.setColor(QPalette.Highlight, QColor(AUSWAHL))
    p.setColor(QPalette.HighlightedText, QColor(AUSWAHL_TEXT))
    p.setColor(QPalette.Link, QColor(AUSWAHL))
    p.setColor(QPalette.Mid, QColor(RAHMEN))
    p.setColor(QPalette.Dark, QColor(TEXT_GEDAEMPFT))
    for rolle in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
        p.setColor(QPalette.Disabled, rolle, QColor(TEXT_DEAKTIVIERT))
    return p


STYLESHEET = f"""
QMainWindow, QDialog {{
    background: {HINTERGRUND};
}}
QWidget {{
    color: {TEXT};
    font-size: 13px;
}}
QLabel[rolle="titel"] {{
    font-size: 20px;
    font-weight: 600;
}}
QLabel[rolle="untertitel"] {{
    font-size: 15px;
    font-weight: 600;
}}
QLabel[rolle="gedaempft"] {{
    color: {TEXT_GEDAEMPFT};
}}
QFrame[rolle="karte"] {{
    background: {FLAECHE};
    border: 1px solid {RAHMEN};
    border-radius: 10px;
}}
QPushButton {{
    background: {FLAECHE};
    border: 1px solid {RAHMEN};
    border-radius: 6px;
    padding: 6px 12px;
}}
QPushButton:hover {{
    border-color: #94a3b8;
}}
QPushButton:disabled {{
    color: {TEXT_GEDAEMPFT};
}}
QPushButton[rolle="primaer"] {{
    background: #2563eb;
    border-color: #2563eb;
    color: #ffffff;
    font-weight: 600;
}}
QPushButton[rolle="primaer"]:hover {{
    background: #1d4ed8;
}}
QLineEdit, QComboBox, QDateEdit, QTextEdit, QPlainTextEdit, QSpinBox, QListWidget {{
    background: {FLAECHE};
    border: 1px solid {RAHMEN};
    border-radius: 6px;
    padding: 4px 6px;
    selection-background-color: {TEXTAUSWAHL};
    selection-color: {TEXT};
}}
/* Ohne diese Regel faerbt `QWidget {{ color }}` oben auch gesperrte Felder
   voll durch -- sie wirken dann bedienbar, reagieren aber auf keinen Klick. */
QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled, QTextEdit:disabled,
QPlainTextEdit:disabled, QSpinBox:disabled, QListWidget:disabled,
QCheckBox:disabled, QLabel:disabled {{
    background: {FLAECHE_DEAKTIVIERT};
    color: {TEXT_DEAKTIVIERT};
    border-color: #e8edf3;
}}
QCheckBox:disabled, QLabel:disabled {{
    background: transparent;
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
QTabWidget::pane {{
    border: none;
}}
QTabBar::tab {{
    background: transparent;
    padding: 8px 16px;
    margin-right: 4px;
    border-radius: 6px;
}}
QTabBar::tab:selected {{
    background: {FLAECHE};
    font-weight: 600;
}}

/* --- Popups: eigene Fenster, die sonst die Systempalette erben --- */
/* Die Auswahlfarbe der Eingabefelder vererbt sich in die Popup-Liste und
   uebersteuert eine hier gesetzte kraeftige Farbe -- deshalb bewusst
   dieselbe helle Markierung mit dunklem Text. */
QComboBox QAbstractItemView {{
    background: {FLAECHE};
    color: {TEXT};
    border: 1px solid {RAHMEN};
    border-radius: 6px;
    padding: 4px;
    outline: none;
    selection-background-color: {TEXTAUSWAHL};
    selection-color: {TEXT};
}}
QComboBox QAbstractItemView::item {{
    min-height: 26px;
    padding: 2px 8px;
    border-radius: 4px;
}}
QComboBox QAbstractItemView::item:hover {{
    background: {SCHWEBEN};
    color: {TEXT};
}}
QComboBox QAbstractItemView::item:selected {{
    background: {TEXTAUSWAHL};
    color: {TEXT};
}}
QMenu {{
    background: {FLAECHE};
    color: {TEXT};
    border: 1px solid {RAHMEN};
    border-radius: 8px;
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background: {AUSWAHL};
    color: {AUSWAHL_TEXT};
}}
QMenu::item:disabled {{
    color: {TEXT_DEAKTIVIERT};
}}
QMenu::separator {{
    height: 1px;
    background: {RAHMEN};
    margin: 4px 8px;
}}
QToolTip {{
    background: {FLAECHE};
    color: {TEXT};
    border: 1px solid {RAHMEN};
    padding: 4px 6px;
}}

/* --- Kalender-Popup der Datumsfelder --- */
QCalendarWidget QWidget {{
    background: {FLAECHE};
    color: {TEXT};
}}
QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background: {HINTERGRUND};
    border-bottom: 1px solid {RAHMEN};
}}
QCalendarWidget QToolButton {{
    background: transparent;
    color: {TEXT};
    font-weight: 600;
    border: none;
    border-radius: 6px;
    padding: 4px 10px;
    margin: 2px;
}}
QCalendarWidget QToolButton:hover {{
    background: {SCHWEBEN};
}}
QCalendarWidget QSpinBox {{
    background: {FLAECHE};
    color: {TEXT};
    border: 1px solid {RAHMEN};
    border-radius: 4px;
}}
QCalendarWidget QAbstractItemView {{
    background: {FLAECHE};
    color: {TEXT};
    outline: none;
    selection-background-color: {AUSWAHL};
    selection-color: {AUSWAHL_TEXT};
}}
QCalendarWidget QAbstractItemView:enabled {{
    color: {TEXT};
}}
QCalendarWidget QAbstractItemView:disabled {{
    color: {TEXT_DEAKTIVIERT};
}}
"""


def anwenden(anwendung) -> None:
    """Stil, Palette und Stylesheet in der richtigen Reihenfolge setzen."""
    anwendung.setStyle("Fusion")
    anwendung.setPalette(palette())
    anwendung.setStyleSheet(STYLESHEET)
