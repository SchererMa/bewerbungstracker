# Bewerbungstracker — Technische Spezifikation

Dieses Dokument ist eine vollständige Übergabe-Spezifikation für den Bau einer Desktop-App zum Tracken von Bewerbungen. Es enthält alle getroffenen Entscheidungen inklusive Begründung, damit ein beliebiges AI-Coding-Tool (oder ein menschlicher Entwickler) die App ohne Rückfragen umsetzen kann.

---

## 1. Ziel & Kontext

Eine persönliche Desktop-App, mit der eine einzelne Person (kein Multi-User zum jetzigen Zeitpunkt) ihre Bewerbungen verwaltet. Kernidee: Stellenanzeigen und Absage-Feedback werden (halb-automatisiert) strukturiert erfasst, damit sich daraus Muster ableiten lassen — insbesondere die häufigsten Absagegründe und der aktuelle Bearbeitungsstatus offener Bewerbungen.

**Aktueller Scope:** Einzelnutzer-App. Mehrere Profile (z. B. für weitere Familienmitglieder) sind bewusst **nicht** Teil des aktuellen Scopes, sollten aber bei der Architektur nicht explizit ausgeschlossen werden, falls das später sinnvoll ergänzt wird.

---

## 2. Technologie-Entscheidung

**Stack: Python + PySide6 (Qt) für die GUI + SQLite als lokale Datenbank.**

Begründung:
- Ein einziger Sprach-Stack für GUI, Logik und Datenzugriff — `sqlite3` ist in Python eingebaut, kein zusätzliches Datenbank-Setup nötig.
- PySide6-Apps sind deutlich leichtgewichtiger als Electron-basierte Alternativen (kein eingebetteter Chromium-Browser).
- Native Widgets (Tabellen, Dialoge) passen gut zu einer datenlastigen App.
- Einfaches Packaging zu einer eigenständigen `.exe` via PyInstaller, ohne Node/npm-Ökosystem.

Die Wahl wurde **unabhängig von den Vorkenntnissen des Auftraggebers** getroffen — er wird selbst keinen Code schreiben, sondern nur Features vorgeben und die fertige App testen. Das Bauen soll komplett von einer KI übernommen werden.

**Einzige bekannte Einschränkung dieser Wahl:** PySide6 bietet kein fertiges Kanban-Board-Widget mit Drag & Drop (siehe Abschnitt 8). Das muss selbst gebaut werden — mehr Aufwand als andere Teile der App, aber technisch unproblematisch.

---

## 3. Datenmodell

### Tabelle `bewerbungen`

| Feld | Typ | Beschreibung |
|---|---|---|
| id | INTEGER (PK) | Eindeutige ID |
| firma | TEXT | Arbeitgeber |
| position | TEXT | Stellenbezeichnung |
| bewerbungsweg | TEXT | Enum: Jobportal, E-Mail, Initiativbewerbung, Empfehlung |
| beworben_am | DATE | Datum der Bewerbung |
| status | TEXT | Automatisch abgeleitet (siehe Abschnitt 4) |
| skills | TEXT/JSON | Liste extrahierter Skills aus der Stellenanzeige |
| gehaltsangabe | TEXT | Optional, falls in der Anzeige genannt |
| cv_pfad | TEXT | Dateipfad zur verwendeten CV-Version dieser Bewerbung |
| anschreiben_pfad | TEXT | Dateipfad zum Anschreiben dieser Bewerbung |
| absagegrund_kategorien | TEXT/JSON | Liste (Mehrfachauswahl möglich, siehe Abschnitt 6) |
| absage_rohtext | TEXT | Freitext der erhaltenen Rückmeldung |
| notizen | TEXT | Freitext |
| letzte_aktualisierung | DATETIME | Für Reminder-Logik relevant |

**Wichtig:** CV/Anschreiben werden **nicht innerhalb einer Bewerbung versioniert**. Unterschiedliche CV-Varianten entstehen nur zwischen verschiedenen Bewerbungen (eine Bewerbung referenziert genau eine CV-Datei und ein Anschreiben).

### Tabelle `interview_runden`

Mehrere Zeilen pro Bewerbung, verknüpft über `bewerbung_id` (Fremdschlüssel).

| Feld | Typ | Beschreibung |
|---|---|---|
| id | INTEGER (PK) | Eindeutige ID |
| bewerbung_id | INTEGER (FK) | Verweis auf `bewerbungen.id` |
| runde_nummer | INTEGER | Fortlaufend pro Bewerbung |
| typ | TEXT | z. B. Telefon, Video, Vor-Ort, Assessment-Center |
| datum | DATE | Datum der Runde |
| ergebnis | TEXT | Status/Ergebnis der Runde |
| notizen | TEXT | Freitext |

---

## 4. Status-Workflow

**Mögliche Gesamtstatus-Werte:** `Beworben`, `Im Interview-Prozess`, `Zusage`, `Absage`, `Ghosting/Keine Rückmeldung`

Der Gesamtstatus wird **automatisch abgeleitet**, nicht manuell gesetzt:

- **Beworben**: Keine Interview-Runde vorhanden, keine Rückmeldung eingetragen.
- **Im Interview-Prozess**: Mindestens eine Interview-Runde vorhanden, noch keine finale Rückmeldung (Zusage/Absage) eingetragen.
- **Zusage / Absage**: Wird gesetzt, sobald eine Rückmeldung eingetragen und entsprechend kategorisiert wird (kein reiner Interview-Runden-Trigger, sondern ein expliziter Rückmeldungs-Eintrag durch den Nutzer).
- **Ghosting/Keine Rückmeldung**: Automatisch, wenn der globale Reminder-Schwellenwert (siehe Abschnitt 7) überschritten wird, ohne dass eine Rückmeldung eingetroffen ist.

---

## 5. Datenimport per JSON (KI-gestützte Extraktion ohne API-Anbindung)

**Entscheidung:** Für die KI-gestützte Extraktion (Stellenanzeige → Kernfelder, Absage-Text → Gründe) wird **kein eigener Anthropic-API-Key** in der App hinterlegt. Stattdessen manueller Workflow:

1. Nutzer postet Link/Text der Stellenanzeige (bzw. später den Absage-Text) in einem separaten KI-Chat.
2. Die KI liefert eine JSON-Datei mit den strukturierten Feldern zurück.
3. Nutzer speichert die Datei in einen von der App überwachten Ordner oder importiert sie manuell über einen Button.
4. Die App liest die JSON, befüllt ein Formular zur Kontrolle, Nutzer bestätigt/speichert.

**Es gibt zwei getrennte Import-Formate** (keine gemeinsame Struktur), und die Datei enthält **keine** Referenz auf eine bestehende Bewerbung — die Zuordnung erfolgt manuell beim Import über die App (Auswahl aus einer Liste bestehender Bewerbungen).

### Format A: Stellenanzeige-Import

```json
{
  "firma": "string",
  "position": "string",
  "skills": ["string", "string"],
  "gehaltsangabe": "string oder null",
  "bewerbungsweg_hinweis": "string oder null",
  "quelle_url": "string oder null"
}
```

### Format B: Absage-Import

```json
{
  "absagegrund_kategorien": ["string", "string"],
  "absagegrund_details": "string",
  "rohtext": "string",
  "datum": "YYYY-MM-DD"
}
```

**Geplante spätere Erweiterung (Fallback, niedrige Priorität):** Ein optionales Einstellungsfeld für einen Anthropic-API-Key. Ist dieser gesetzt, ruft die App die Extraktion direkt per API auf; ist er nicht gesetzt, bleibt der manuelle JSON-Import-Weg aktiv. Beide Pfade sollen intern dieselbe Datenstruktur (siehe Format A/B) befüllen — die Umsetzung ist als zweite Codepfad-Verzweigung gedacht, keine grundlegend andere Architektur.

---

## 6. Absagegrund-Kategorisierung

- Eine Absage kann **mehrere Gründe gleichzeitig** haben (z. B. Gehalt UND Erfahrung) — keine Beschränkung auf einen Hauptgrund.
- Ansatz: **Feste, vordefinierte Kategorien + "Sonstiges"-Fallback**, damit das Dashboard vergleichbare Trends zeigen kann (statt einer unüberschaubaren Menge frei formulierter Einzelkategorien). Der Rohtext der Rückmeldung bleibt zusätzlich immer gespeichert (`absage_rohtext`).

**Kategorien-Katalog:**
1. Erfahrung/Seniorität
2. Fachliche Skills
3. Gehaltsvorstellung
4. Kultureller Fit
5. Position anderweitig besetzt
6. Zu späte Bewerbung
7. Formale Gründe (z. B. fehlende Unterlagen)
8. Kein Feedback erhalten
9. Sonstiges

---

## 7. Nachfrage-/Reminder-Logik

- Der Schwellenwert (Anzahl Tage, ab der ein "Nachfragen?"-Hinweis erscheint) ist **global** — eine Einstellung für alle Bewerbungen, nicht pro Bewerbung individuell konfigurierbar.
- Der Tage-Zähler bezieht sich auf das **letzte Ereignis ohne Reaktion**:
  - Falls noch keine Reaktion kam: Zähler ab `beworben_am`.
  - Falls es bereits Interview-Runden gab, aber danach wieder tagelang nichts kam: Zähler ab dem Datum der letzten Interview-Runde.
- Der Reminder ist also nicht nur auf die Erstphase (vor jeder Reaktion) beschränkt, sondern greift auch nach der letzten Interview-Runde erneut.

---

## 8. Dashboard (Startbildschirm)

Das Dashboard ist die **Startansicht der App** (nicht ein separater Tab) und enthält:

1. Liste "aktuell offene Bewerbungen" mit Alter (Tage seit Bewerbung/letzter Aktivität)
2. Kreisdiagramm: Verhältnis Zusage / Absage / Offen / Ghosting
3. Balkendiagramm: häufigste Absagegründe (basierend auf Kategorien aus Abschnitt 6)
4. Liste "Nachfragen empfohlen" (basierend auf Reminder-Logik aus Abschnitt 7)

---

## 9. UI / Listenansicht

- **Kanban-Board nach Status** (Spalten = die fünf Status-Werte aus Abschnitt 4), keine klassische Tabellenansicht.
  - *Technischer Hinweis:* PySide6 bietet kein fertiges Kanban-Widget mit Drag & Drop — dies muss custom implementiert werden (eigene Spalten, Karten-Widgets, Drag-Handling). Höherer Aufwand als andere UI-Teile, aber machbar.
- **Filter/Suche**: nach Firma, Status und Zeitraum — als wichtig eingestuft, sollte früh mitgeplant werden.
- **CSV-Export**: der gesamten Bewerbungsdaten, für Backup/externe Auswertung.

---

## 10. Nicht mehr offene Punkte (aus vorheriger Planung geklärt)

- Datei-Handling für CV/Anschreiben: Pfad-Referenz, keine Versionierung innerhalb einer Bewerbung (siehe Abschnitt 3).
- Interview-Runden werden einzeln getrackt, nicht nur als ein Gesamtstatus (siehe Abschnitt 3).

## 11. Noch offene/spätere Punkte (bewusst nicht Teil des aktuellen Kern-Scopes)

- Multi-Profil-Unterstützung (weitere Nutzer/innen).
- Anthropic-API-Key-Fallback für direkte KI-Extraktion ohne manuellen JSON-Umweg (siehe Abschnitt 5).

---

## 12. Vorgeschlagene Umsetzungsreihenfolge (Phasenplan)

1. **Projekt-Setup**: Virtualenv, PySide6 installieren, Projektstruktur (`main.py`, `database.py`, `models.py`, `ui/`), Git-Repo.
2. **Datenmodell & SQLite-Anbindung**: Tabellen `bewerbungen` und `interview_runden` gemäß Abschnitt 3 anlegen, CRUD-Funktionen.
3. **GUI-Grundgerüst**: Hauptfenster, zunächst mit Testdaten, um Layout zu prüfen.
4. **CRUD in der GUI**: Formular-Dialoge zum Anlegen/Bearbeiten von Bewerbungen und Interview-Runden.
5. **Status-Ableitungslogik**: Automatische Statusberechnung gemäß Abschnitt 4 implementieren.
6. **JSON-Import**: Einlese-Logik für Format A und B (Abschnitt 5), inkl. manueller Zuordnung zu bestehender Bewerbung.
7. **Absagegrund-Erfassung**: Mehrfachauswahl-Kategorien + Sonstiges-Fallback (Abschnitt 6).
8. **Reminder-Logik**: Globale Schwellenwert-Einstellung, Berechnung gemäß Abschnitt 7.
9. **Kanban-Board-UI**: Custom-Implementierung mit Drag & Drop (Abschnitt 9) — eingeplant als eigener, aufwändigerer Schritt.
10. **Filter/Suche**: Nach Firma, Status, Zeitraum.
11. **Dashboard**: Startbildschirm mit den vier in Abschnitt 8 beschriebenen Elementen (Charts z. B. via `QtCharts` oder `matplotlib`-Einbettung).
12. **CSV-Export**.
13. **Packaging**: Eigenständige `.exe` via PyInstaller.
14. *(Optional, niedrige Priorität)*: API-Key-Fallback für direkte KI-Extraktion.

---

*Ende der Spezifikation. Dieses Dokument kann vollständig als Ausgangspunkt für die Umsetzung in einem beliebigen AI-Coding-Tool verwendet werden — alle Entscheidungen sind final für den aktuellen Scope, sofern nicht in Abschnitt 11 als offen markiert.*
