# Bewerbungstracker

Desktop-App zum Verwalten von Bewerbungen: Kanban-Board nach Status, automatisch
abgeleiteter Bearbeitungsstand, Nachfrage-Erinnerungen, Auswertung der
häufigsten Absagegründe und JSON-Import aus einem KI-Chat.

Umgesetzt nach [`docs/bewerbungstracker_spezifikation.md`](docs/bewerbungstracker_spezifikation.md).
Stack: **Python 3.12 + PySide6 (Qt) + SQLite**, keine weiteren Laufzeit-Abhängigkeiten.

### Dokumentation

| Datei | Für wen |
|---|---|
| dieses README | Entwicklung: Aufsetzen, Tests, Build, Architektur |
| [`docs/anleitung.md`](docs/anleitung.md) | **Endnutzer**, die nur die `.exe` bekommen |
| [`docs/ki_prompts.md`](docs/ki_prompts.md) | Prompt-Vorlagen für den JSON-Import |
| [`docs/bewerbungstracker_spezifikation.md`](docs/bewerbungstracker_spezifikation.md) | Ursprüngliche Anforderungen |

> **Wer die Oberfläche ändert, pflegt bitte
> [`docs/anleitung.md`](docs/anleitung.md) mit.** Sie beschreibt sichtbares
> Verhalten – Menüs, Beschriftungen, Dialoge, Statusregeln, Standardwerte – und
> geht an Leute, die nicht in den Code schauen können. Am Ende der Datei steht
> eine Checkliste, welcher Abschnitt von welcher Änderung betroffen ist.

---

## Schnellstart

```powershell
cd C:\dev\bewerbungstracker
.venv\Scripts\python.exe main.py
```

Beispieldaten zum Ausprobieren anlegen (legt 7 Bewerbungen über alle fünf Status an):

```powershell
.venv\Scripts\python.exe testdaten.py
```

Umgebung neu aufsetzen, falls `.venv` fehlt:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

## Tests

```powershell
.venv\Scripts\python.exe -m pytest -q
```

29 Tests: Statusableitung, Reminder-Berechnung, CRUD, Filter, JSON-Import,
CSV-Export und Smoke-Tests der Oberfläche (laufen offscreen, öffnen kein Fenster).

## Als .exe verpacken

```powershell
.venv\Scripts\pyinstaller.exe bewerbungstracker.spec
```

Ergebnis: `dist\bewerbungstracker.exe` – eine Datei, ohne Konsolenfenster, ohne
installiertes Python auf dem Zielrechner.

Wird die exe weitergegeben, gehört [`docs/anleitung.md`](docs/anleitung.md) dazu –
und vorher ein Blick darauf, ob sie noch zum Stand der App passt. Sie erklärt
unter anderem die SmartScreen-Warnung beim ersten Start, die sonst jeden
Empfänger ausbremst (die exe ist nicht signiert).

---

## Bedienung

### Dashboard (Startansicht)

Beim Start öffnet sich das Dashboard mit Kennzahlen, dem Verhältnis
Zusage/Absage/Offen/Ghosting, den häufigsten Absagegründen sowie den Listen
*Aktuell offene Bewerbungen* und *Nachfragen empfohlen*. Doppelklick auf einen
Listeneintrag öffnet die Bewerbung.

### Kanban-Board

Über **Bewerbungen** in der Werkzeugleiste. Fünf Spalten, eine je Status.

Der Status wird **nie direkt gesetzt**, sondern immer aus den Daten abgeleitet
(Spezifikation Abschnitt 4). Ein Drop auf eine Spalte löst deshalb die passende
Aktion aus, statt die Karte nur zu verschieben:

| Ziel-Spalte | Was passiert |
|---|---|
| Beworben | fragt, ob eine eingetragene Rückmeldung entfernt werden soll |
| Im Interview-Prozess | öffnet den Dialog für eine neue Interview-Runde |
| Zusage | öffnet die Rückmeldung-Erfassung, vorbelegt auf Zusage |
| Absage | öffnet die Rückmeldung-Erfassung inkl. Absagegrund-Kategorien |
| Ghosting | nicht manuell setzbar – ergibt sich aus dem Schwellenwert |

Weitere Bedienung: **Doppelklick** öffnet eine Karte, **Rechtsklick** bietet
Bearbeiten, Interview-Runde, Rückmeldung, Lebenslauf/Anschreiben/Stellenanzeige
öffnen und Löschen.

Die Filterleiste sucht über Firma, Position und Skills und filtert nach Status
und Bewerbungszeitraum.

### Status-Ableitung

1. Eingetragene Rückmeldung → **Zusage** bzw. **Absage**
2. sonst: Tage ohne Reaktion ≥ Ghosting-Schwelle → **Ghosting/Keine Rückmeldung**
3. sonst: mindestens eine Interview-Runde → **Im Interview-Prozess**
4. sonst → **Beworben**

„Tage ohne Reaktion“ zählt ab dem letzten Ereignis: dem Bewerbungsdatum oder,
falls vorhanden, der letzten Interview-Runde. Eine neue Runde setzt den Zähler
also zurück und holt eine Karte auch wieder aus *Ghosting* heraus.

### JSON-Import aus dem KI-Chat

Stellenanzeige bzw. Absagetext in einen KI-Chat kopieren, die JSON-Antwort als
Datei speichern und in der App importieren – per **JSON importieren …** oder
automatisch über den überwachten Ordner (Einstellungen → *Überwachter
Import-Ordner*; neue `.json`-Dateien werden dort erkannt und angeboten).

* **Format A (Stellenanzeige)** legt eine neue Bewerbung an.
* **Format B (Absage)** wird beim Import manuell einer bestehenden Bewerbung
  zugeordnet – die Datei enthält bewusst keine Referenz.

Fertige Prompt-Vorlagen: [`docs/ki_prompts.md`](docs/ki_prompts.md).
Beispieldateien: [`beispiel_importe/`](beispiel_importe/).

### Einstellungen

* **Nachfragen empfehlen nach** – ab wie vielen Tagen ohne Reaktion eine
  Bewerbung in der Nachfassliste erscheint und die Karte eine orange Markierung
  bekommt (Standard: 14 Tage).
* **Als Ghosting werten nach** – ab wie vielen Tagen der Status automatisch auf
  *Ghosting/Keine Rückmeldung* springt (Standard: 30 Tage).
* **Überwachter Import-Ordner** – Ordner für die KI-JSON-Dateien.
* **Anthropic API-Key** – Platzhalter für die spätere Direkt-Extraktion
  (Spezifikation Abschnitt 11), aktuell ohne Funktion.

### CSV-Export

**CSV-Export** in der Werkzeugleiste schreibt alle Bewerbungen mit Semikolon als
Trennzeichen und UTF-8-BOM – so öffnet Excel die Datei unter Windows direkt
korrekt.

---

## Datenspeicher

Die Datenbank liegt außerhalb des Projektordners unter

```
%APPDATA%\Bewerbungstracker\bewerbungstracker.db
```

damit sie ein Update der App (oder ein neues `git clone`) überlebt. Für Tests
lässt sich der Ort über die Umgebungsvariable `BEWERBUNGSTRACKER_DIR`
umbiegen. Ein Backup ist ein simples Kopieren dieser einen Datei.

---

## Projektstruktur

```
main.py                    Einstiegspunkt (QApplication, Fenster)
testdaten.py               Beispieldatensätze anlegen
bewerbungstracker.spec     PyInstaller-Konfiguration
app/
  models.py                Dataclasses, Enums, Kategorien-Katalog
  database.py              SQLite-Verbindung, Schema, Migrationen, Einstellungen
  repository.py            CRUD, Filter, Statusabgleich beim Laden
  status.py                Statusableitung + Reminder-Berechnung
  importer.py              JSON-Formate A und B lesen und prüfen
  statistik.py             Dashboard-Auswertungen
  export.py                CSV-Export
  ui/
    hauptfenster.py        Werkzeugleiste, Seitenumschaltung, Filter, Aktionen
    dashboard.py           Startansicht
    kanban.py              Board, Spalten, Karten, Drag & Drop
    dialoge.py             Bewerbung, Interview-Runde, Rückmeldung, Einstellungen
    import_dialog.py       JSON-Import
    charts.py              Ring- und Balkendiagramm (selbst gezeichnet)
    theme.py               Farben und Stylesheet
tests/                     pytest-Suite (Logik + UI-Smoke-Tests)
docs/                      Anleitung (Endnutzer), Spezifikation, KI-Prompts
beispiel_importe/          Beispiel-JSONs für beide Import-Formate
```

---

## Abweichungen von der Spezifikation

Zwei bewusste Ergänzungen, beide abwärtskompatibel zum spezifizierten Verhalten:

1. **Zwei Schwellenwerte statt einem.** Abschnitt 4 nennt den Reminder-Schwellenwert
   als Ghosting-Auslöser. Damit wären die Dashboard-Listen *Nachfragen empfohlen*
   und der Status *Ghosting* immer identisch belegt. Deshalb gibt es zwei globale
   Werte (14 / 30 Tage). Auf denselben Wert gesetzt verhalten sie sich exakt wie
   in der Spezifikation beschrieben.
2. **Zusätzliche Spalten `rueckmeldung_typ` und `rueckmeldung_am`.** Abschnitt 4
   verlangt einen „expliziten Rückmeldungs-Eintrag durch den Nutzer“ als Auslöser
   für Zusage/Absage; dafür ist ein eigenes Feld nötig, das die Feldliste in
   Abschnitt 3 nicht enthält. `absagegrund_kategorien` und `absage_rohtext`
   bleiben unverändert bestehen.

Ebenfalls ergänzt, weil die Spezifikation es offenlässt: `quelle_url` und
`absagegrund_details` aus den Import-Formaten werden dauerhaft gespeichert, und
`bewerbungen` hat eine Spalte `profil_id` (fest 1), damit Multi-Profil später
ohne Schema-Bruch nachrüstbar ist (Abschnitt 11).

Nicht umgesetzt, wie in Abschnitt 11 als „später“ markiert: Multi-Profil-Betrieb
und die direkte KI-Extraktion per API-Key.
