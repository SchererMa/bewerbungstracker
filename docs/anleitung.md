<!--
  HINWEIS FÜR DIE WARTUNG
  Diese Datei ist die einzige Doku für Endnutzer, die nur die .exe bekommen.
  Sie beschreibt sichtbares Verhalten: Menüs, Beschriftungen, Dialoge, Abläufe.
  Wer daran etwas ändert, passt bitte auch diese Anleitung an -- siehe die
  Wartungs-Checkliste am Ende der Datei.
-->

# Bewerbungstracker – Anleitung

Ein kleines Windows-Programm, das den Überblick über laufende Bewerbungen behält:
Wo stehe ich gerade, wo sollte ich nachfassen, und woran ist es zuletzt gescheitert.

Es braucht kein installiertes Python und keine Internetverbindung. Alle Daten
bleiben auf dem eigenen Rechner.

> **Auf einem Mac?** Die Abschnitte 1 bis 11 beschreiben die Windows-Version.
> Die App läuft auch auf macOS, wird dort aber anders gestartet – wie, steht in
> [Abschnitt 12](#12-nutzung-auf-einem-mac). Alles zur Bedienung gilt
> unverändert.

---

## 1. Starten

Die Datei `bewerbungstracker.exe` irgendwohin kopieren – Desktop, Dokumente,
USB-Stick, egal – und doppelklicken. Es gibt keine Installation.

### Beim ersten Start meldet sich Windows

Weil das Programm nicht bei Microsoft registriert ist, erscheint beim ersten Mal
ein blaues Fenster:

> **Der Computer wurde durch Windows geschützt**

Das ist kein Fehler und kein Virus, sondern der Standardhinweis für jedes
Programm ohne gekaufte Signatur. So geht es weiter:

1. Auf **Weitere Informationen** klicken (der Text ist leicht zu übersehen).
2. Dann auf **Trotzdem ausführen**.

Ab dem zweiten Start kommt die Meldung nicht mehr.

Falls der Virenscanner die Datei stattdessen still verschiebt: einmal in der
Quarantäne freigeben. Auch das liegt an der fehlenden Signatur.

---

## 2. Der schnellste Weg zur ersten Bewerbung

1. Oben auf **Neue Bewerbung** klicken.
2. **Firma** und **Position** ausfüllen – mehr ist nicht verpflichtend.
3. **Speichern**.

Die Bewerbung liegt jetzt im Board in der Spalte *Beworben*.

Alles Weitere – Interview-Runden, Zu- und Absagen – wird später an derselben
Karte ergänzt.

---

## 3. Die zwei Ansichten

Oben links wird zwischen den beiden Ansichten umgeschaltet.

### Dashboard

Die Startansicht. Sie beantwortet „Wie läuft es gerade?":

* Vier Kacheln: **Bewerbungen gesamt**, **Zusagen**, **Absagen**, **Nachfassen**.
* **Verhältnis Zusage / Absage / Offen / Ghosting** als Ringdiagramm.
* **Häufigste Absagegründe** als Balken – interessant, sobald ein paar Absagen
  erfasst sind.
* **Aktuell offene Bewerbungen** – alles, wo noch keine Rückmeldung da ist.
* **Nachfragen empfohlen** – Bewerbungen, die zu lange still sind.

Ein **Doppelklick** auf einen Listeneintrag öffnet die zugehörige Bewerbung.

### Bewerbungen (Board)

Fünf Spalten, eine je Status: *Beworben*, *Im Interview-Prozess*, *Zusage*,
*Absage*, *Ghosting/Keine Rückmeldung*.

* **Doppelklick** auf eine Karte öffnet sie zum Bearbeiten.
* **Rechtsklick** öffnet das Menü mit: *Bearbeiten*, *Interview-Runde
  hinzufügen*, *Rückmeldung eintragen*, *Lebenslauf öffnen*, *Anschreiben
  öffnen*, *Stellenanzeige öffnen*, *Löschen*. Die drei Öffnen-Einträge sind
  ausgegraut, solange bei der Bewerbung keine Datei bzw. keine Adresse
  hinterlegt ist.

---

## 4. Der Status ergibt sich von selbst

Das ist der wichtigste Punkt zum Verständnis: **der Status lässt sich nicht
direkt setzen.** Er wird jedes Mal neu aus den erfassten Daten berechnet:

1. Ist eine Rückmeldung eingetragen → **Zusage** bzw. **Absage**.
2. Sonst: zu lange keine Reaktion → **Ghosting/Keine Rückmeldung**.
3. Sonst: mindestens eine Interview-Runde erfasst → **Im Interview-Prozess**.
4. Sonst → **Beworben**.

Deshalb passiert beim **Ziehen einer Karte** in eine andere Spalte nicht einfach
ein Verschieben, sondern es öffnet sich die passende Eingabe:

| Karte gezogen auf | Was passiert |
|---|---|
| Beworben | fragt, ob eine eingetragene Rückmeldung entfernt werden soll |
| Im Interview-Prozess | Dialog für eine neue Interview-Runde (eine vorhandene Rückmeldung wird davor auf Rückfrage entfernt) |
| Zusage | Rückmeldung erfassen, vorbelegt auf Zusage |
| Absage | Rückmeldung erfassen, inklusive Absagegründe |
| Ghosting/Keine Rückmeldung | nicht von Hand setzbar – ergibt sich aus der Zeit |

Eine Karte mit erfassten Interview-Runden lässt sich nicht auf *Beworben*
zurückziehen – dafür müssen die Runden erst im Bearbeiten-Dialog raus. Das
Programm sagt das auch, wenn man es versucht.

Landet die Karte nach dem Ausfüllen in der Zielspalte? Ja – aber weil die Daten
es hergeben, nicht weil sie dorthin gezogen wurde. Bricht man den Dialog ab,
bleibt sie, wo sie war.

**„Zu lange keine Reaktion" zählt ab dem letzten Ereignis:** ab dem
Bewerbungsdatum oder, falls vorhanden, ab der letzten Interview-Runde. Eine neu
erfasste Runde setzt den Zähler also zurück und holt eine Karte damit auch
wieder aus *Ghosting* heraus.

---

## 5. Suchen und filtern

Über dem Board liegt die Filterleiste:

* **Suche** – durchsucht Firma, Position und Skills gleichzeitig.
* **Status-Auswahl** – nur eine Spalte anzeigen.
* **Zeitraum** – schränkt auf das Bewerbungsdatum ein. Das Häkchen schaltet den
  Filter ein und aus; die beiden Datumsfelder lassen sich jederzeit anklicken,
  und sobald ein Datum gewählt wird, setzt sich das Häkchen von selbst.
* **Zurücksetzen** – alle drei Filter auf einmal aufheben.

---

## 6. Stellenanzeigen und Absagen per KI übernehmen

Statt jedes Feld abzutippen, lässt sich der Text von einem KI-Chat
(ChatGPT, Claude, Gemini …) in eine Datei umwandeln, die das Programm einliest.
Ein kostenpflichtiger Zugang ist dafür **nicht** nötig – der normale Chat reicht.

Der Ablauf ist immer derselbe:

1. Eine der beiden Vorlagen unten in den KI-Chat kopieren.
2. Darunter den Text der Stellenanzeige bzw. der Absage einfügen.
3. Die Antwort als Datei mit der Endung `.json` speichern.
4. In der App **JSON importieren …** wählen und die Datei öffnen.

Wichtig ist der Satz „nur das JSON, keine Erklärung" in der Vorlage – sonst
schreibt die KI Fließtext drumherum und die Datei lässt sich nicht lesen.

### Vorlage A – aus einer Stellenanzeige eine neue Bewerbung

```
Lies die folgende Stellenanzeige und gib ausschließlich ein JSON-Objekt
in genau dieser Struktur zurück – keine Erklärung, kein Markdown:

{
  "firma": "string",
  "position": "string",
  "skills": ["string", "string"],
  "gehaltsangabe": "string oder null",
  "bewerbungsweg_hinweis": "string oder null",
  "quelle_url": "string oder null"
}

Regeln:
- skills: die 5-12 wichtigsten geforderten Fähigkeiten, je ein kurzer Begriff.
- gehaltsangabe: nur übernehmen, wenn die Anzeige eine Spanne oder Zahl nennt, sonst null.
- bewerbungsweg_hinweis: wie beworben werden soll (Jobportal, E-Mail,
  Initiativbewerbung, Empfehlung), sonst null.
- Nichts erfinden - was nicht in der Anzeige steht, ist null bzw. eine leere Liste.

Stellenanzeige:
[hier den Text oder den Link einfügen]
```

Daraus legt der Import eine **neue** Bewerbung an und öffnet direkt das Formular,
damit sich alles vor dem Speichern prüfen lässt.

### Vorlage B – eine Absage auswerten

```
Lies die folgende Absage-E-Mail und gib ausschließlich ein JSON-Objekt
in genau dieser Struktur zurück – keine Erklärung, kein Markdown:

{
  "absagegrund_kategorien": ["string", "string"],
  "absagegrund_details": "string",
  "rohtext": "string",
  "datum": "YYYY-MM-DD"
}

Regeln:
- absagegrund_kategorien darf ausschließlich Werte aus diesem Katalog enthalten
  (Mehrfachnennung erlaubt): Erfahrung/Seniorität, Fachliche Skills,
  Gehaltsvorstellung, Kultureller Fit, Position anderweitig besetzt,
  Zu späte Bewerbung, Formale Gründe, Kein Feedback erhalten, Sonstiges.
- Nennt die Absage keinen erkennbaren Grund, nimm "Kein Feedback erhalten".
- absagegrund_details: ein bis zwei Sätze, was konkret genannt wurde.
- rohtext: der Originaltext der Absage, unverändert.
- datum: Datum der Absage im Format YYYY-MM-DD.

Absage:
[hier den Text einfügen]
```

Eine Absage-Datei enthält bewusst keinen Verweis auf eine bestimmte Bewerbung –
beim Import wird sie deshalb **von Hand der passenden Bewerbung zugeordnet**.
Kategorien, die nicht im Katalog stehen, landen automatisch unter *Sonstiges*;
der Dialog weist darauf hin.

Die so erfassten Gründe füllen im Dashboard die Auswertung *Häufigste
Absagegründe*.

### Bequemer: der überwachte Ordner

Unter **Einstellungen → Überwachter Import-Ordner** lässt sich ein Ordner
festlegen. Jede neue `.json`-Datei, die dort landet, wird vom Programm bemerkt
und direkt zum Import angeboten – das Suchen über *JSON importieren …* entfällt
dann. Praktisch, wenn man den Download-Ordner einträgt.

**Import-Ordner prüfen** oben in der Leiste schaut sofort nach, ohne auf die
automatische Erkennung zu warten.

---

## 7. Einstellungen

Zu finden über **Einstellungen** in der oberen Leiste.

* **Nachfragen empfehlen nach** (Standard: 14 Tage) – ab wann eine stille
  Bewerbung in der Dashboard-Liste *Nachfragen empfohlen* auftaucht und ihre
  Karte eine orange Markierung bekommt. Es ist nur eine Empfehlung, am Status
  ändert sich dadurch nichts.
* **Als Ghosting werten nach** (Standard: 30 Tage) – ab wann der Status
  tatsächlich auf *Ghosting/Keine Rückmeldung* wechselt.
* **Überwachter Import-Ordner** – siehe oben.
* **Anthropic API-Key** – für eine später geplante Funktion, aktuell ohne
  Wirkung. Das Feld kann leer bleiben.

Die beiden Zeitwerte gelten für alle Bewerbungen gemeinsam. Wer die Trennung
nicht möchte, setzt einfach beide auf denselben Wert.

---

## 8. Daten exportieren

**CSV-Export** in der oberen Leiste schreibt alle Bewerbungen in eine
CSV-Datei, die sich in Excel per Doppelklick korrekt öffnet – auch mit Umlauten.

---

## 9. Wo die Daten liegen und wie man sie sichert

Alles steckt in einer einzigen Datei:

```
%APPDATA%\Bewerbungstracker\bewerbungstracker.db
```

Diesen Pfad direkt in die Adresszeile des Explorers einfügen, dann landet man im
richtigen Ordner. Unten im Programmfenster steht derselbe Pfad.

* **Backup**: diese eine Datei kopieren. Mehr ist nicht nötig.
* **Umzug auf einen neuen Rechner**: die Datei an dieselbe Stelle kopieren,
  fertig – die Bewerbungen sind wieder da.
* Die Datei liegt bewusst **nicht** neben der `.exe`. Eine neuere Programmversion
  überschreibt die Daten dadurch nicht.

---

## 10. Tastenkürzel

| Taste | Wirkung |
|---|---|
| `Strg + N` | Neue Bewerbung |
| `Strg + I` | JSON importieren |
| `F5` | Ansicht aktualisieren |

---

## 11. Wenn etwas nicht funktioniert

**Windows blockt den Start.**
Siehe Abschnitt 1 – *Weitere Informationen* → *Trotzdem ausführen*.

**Der erste Start dauert ein paar Sekunden.**
Normal. Das Programm entpackt sich beim Start selbst; ab dem zweiten Mal geht es
schneller.

**Der JSON-Import meldet einen Fehler.**
Fast immer hat die KI zusätzlichen Text mitgeliefert. Die Datei in einem Editor
öffnen: Sie muss mit `{` beginnen und mit `}` enden. Alles davor und dahinter
löschen – auch Zeilen aus drei Backticks – und erneut importieren.

**Eine Karte lässt sich nicht nach *Ghosting* ziehen.**
Das ist so gewollt: Ghosting entsteht durch Zeitablauf, nicht durch eine
Entscheidung. Siehe Abschnitt 4.

**Eine Karte will nicht zurück auf *Beworben*.**
Dann sind noch Interview-Runden erfasst. Karte öffnen, Runden entfernen,
speichern.

**Eine Karte hängt in der falschen Spalte.**
Der Status folgt immer den erfassten Daten. Die Karte öffnen und prüfen, ob eine
Rückmeldung eingetragen ist, ob Interview-Runden erfasst sind und ob das
Bewerbungsdatum stimmt.

**Die Zahlen im Dashboard wirken veraltet.**
`F5` drücken.

---

## 12. Nutzung auf einem Mac

Die `bewerbungstracker.exe` ist ein reines Windows-Programm. Auf einem Mac
lässt sie sich nicht starten – auch nicht durch Doppelklick oder Umbenennen.
Ein fertiges Mac-Programm zum Doppelklicken gibt es derzeit nicht.

Die App selbst läuft aber problemlos unter macOS: Sie ist plattformunabhängig
geschrieben, es fehlt nur die Verpackung. Der Weg führt deshalb über den
Quellcode – einmal einrichten, danach mit einem Doppelklick starten.

### Was gebraucht wird

* macOS auf Intel oder Apple Silicon – beides funktioniert.
* **Python 3.12** von [python.org](https://www.python.org/downloads/).
  Das bei macOS mitgelieferte Python ist älter und sollte unangetastet bleiben.
* Den Projektordner als ZIP (nicht die `.exe`).

### Einmalig einrichten

ZIP entpacken, dann **Terminal** öffnen (Spotlight mit `Cmd + Leertaste`,
„Terminal" eingeben) und eingeben – Pfad an den eigenen Ordner anpassen:

```
cd ~/Downloads/bewerbungstracker
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Der letzte Schritt lädt einmalig die Oberflächen-Bibliothek herunter und dauert
ein bis zwei Minuten.

### Starten

```
cd ~/Downloads/bewerbungstracker
source .venv/bin/activate
python main.py
```

### Bequemer: Startdatei zum Doppelklicken

Damit das Tippen entfällt, im Projektordner eine Datei `start.command` mit
diesem Inhalt anlegen:

```
#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
python main.py
```

Danach einmal im Terminal freischalten:

```
chmod +x ~/Downloads/bewerbungstracker/start.command
```

Ab da startet ein Doppelklick auf `start.command` die App. Beim ersten Mal
fragt macOS eventuell nach – dann Rechtsklick auf die Datei und *Öffnen*
wählen, das bestätigt sie dauerhaft.

### Unterschiede zur Windows-Version

Die Bedienung ist identisch – Board, Status-Logik, Import, Einstellungen und
Export verhalten sich exakt wie in den Abschnitten 2 bis 8 beschrieben. Anders
sind nur drei Dinge:

| | Windows | macOS |
|---|---|---|
| Tastenkürzel | `Strg + N`, `Strg + I` | `Cmd + N`, `Cmd + I` |
| Ansicht aktualisieren | `F5` | `F5` (je nach Tastatur `Fn + F5`) |
| Datenbank | `%APPDATA%\Bewerbungstracker\` | `~/Bewerbungstracker/` |

Die Warnung aus Abschnitt 1 entfällt: SmartScreen gibt es auf dem Mac nicht.
Das Backup funktioniert genauso – die eine Datei `bewerbungstracker.db` aus dem
Ordner `~/Bewerbungstracker/` kopieren. Im Finder erreichbar über *Gehe zu →
Gehe zum Ordner…* und dort `~/Bewerbungstracker` eingeben.

### Und ein richtiges Mac-Programm?

Technisch möglich, aber deutlich aufwändiger, und zwar aus zwei Gründen:

1. Das Verpackungswerkzeug muss **auf einem Mac** laufen – von Windows aus lässt
   sich kein Mac-Programm erzeugen.
2. macOS stellt Programme aus unbekannter Quelle unter Quarantäne und meldet
   dabei sinngemäß, die Datei sei *beschädigt*. Das klingt nach einem Defekt,
   liegt aber nur an der fehlenden Signatur. Sauber beheben lässt sich das nur
   mit einem kostenpflichtigen Apple-Entwicklerkonto.

Für einzelne Nutzer lohnt dieser Aufwand selten – der Start über die
`start.command` oben leistet dasselbe.

---

<!--
  WARTUNGS-CHECKLISTE
  Diese Anleitung beschreibt die Oberfläche aus Endnutzersicht. Nach Änderungen
  bitte prüfen, ob hier etwas nachgezogen werden muss:

  - Menüs / Schaltflächen der Werkzeugleiste .......... Abschnitte 2, 3, 6, 8
  - Kontextmenü der Karten ........................... Abschnitt 3
  - Regeln der Statusableitung / Drag & Drop .......... Abschnitt 4
  - Filterleiste ..................................... Abschnitt 5
  - JSON-Importformate (Felder, Kategorien-Katalog) ... Abschnitt 6
    -> muss deckungsgleich mit docs/ki_prompts.md bleiben
  - Einstellungen inkl. Standardwerten ................ Abschnitt 7
  - Speicherort der Datenbank ........................ Abschnitte 9 und 12
  - Tastenkürzel ..................................... Abschnitte 10 und 12
  - requirements.txt / Python-Version ................ Abschnitt 12
    -> dort stehen die Einrichtungsbefehle für macOS
-->
