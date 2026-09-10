"""Farben und gemeinsames Stylesheet der Oberflaeche."""

from __future__ import annotations

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
    selection-background-color: #bfdbfe;
    selection-color: {TEXT};
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
"""
