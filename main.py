"""Einstiegspunkt des Bewerbungstrackers."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app import __version__, database
from app.ui import theme
from app.ui.hauptfenster import Hauptfenster


def main() -> int:
    anwendung = QApplication(sys.argv)
    anwendung.setApplicationName("Bewerbungstracker")
    anwendung.setApplicationVersion(__version__)
    anwendung.setOrganizationName("Bewerbungstracker")
    theme.anwenden(anwendung)

    conn = database.verbinden()
    fenster = Hauptfenster(conn)
    fenster.show()
    try:
        return anwendung.exec()
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
