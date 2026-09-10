# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller-Konfiguration fuer eine eigenstaendige bewerbungstracker.exe.

Bauen::

    .venv\\Scripts\\pyinstaller.exe bewerbungstracker.spec

Ergebnis: dist\\bewerbungstracker.exe (One-File, ohne Konsolenfenster).
Die Datenbank liegt unabhaengig davon unter %APPDATA%\\Bewerbungstracker.
"""

# Qt-Module, die nicht gebraucht werden -- spart deutlich Paketgroesse.
AUSSCHLUSS = [
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtQuick",
    "PySide6.QtQml",
    "PySide6.Qt3DCore",
    "PySide6.QtMultimedia",
    "PySide6.QtNetwork",
    "PySide6.QtCharts",
    "tkinter",
    "matplotlib",
    "numpy",
]

analyse = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=AUSSCHLUSS,
    noarchive=False,
)

pyz = PYZ(analyse.pure)

exe = EXE(
    pyz,
    analyse.scripts,
    analyse.binaries,
    analyse.datas,
    [],
    name="bewerbungstracker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
