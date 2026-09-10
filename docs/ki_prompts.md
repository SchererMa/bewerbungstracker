# Prompt-Vorlagen für den JSON-Import

Der Import läuft ohne API-Key (Spezifikation Abschnitt 5): Text in einen KI-Chat
kopieren, die Antwort als `.json` speichern, in der App importieren – entweder
über **JSON importieren …** oder über den überwachten Import-Ordner
(Einstellungen → *Überwachter Import-Ordner*).

Wichtig: Die KI soll **nur** das JSON ausgeben, ohne erklärenden Text und ohne
Markdown-Codefence, damit die Datei direkt einlesbar ist.

---

## Format A — Stellenanzeige

> Lies die folgende Stellenanzeige und gib **ausschließlich** ein JSON-Objekt
> in genau dieser Struktur zurück – keine Erklärung, kein Markdown:
>
> ```
> {
>   "firma": "string",
>   "position": "string",
>   "skills": ["string", "string"],
>   "gehaltsangabe": "string oder null",
>   "bewerbungsweg_hinweis": "string oder null",
>   "quelle_url": "string oder null"
> }
> ```
>
> Regeln:
> - `skills`: die 5–12 wichtigsten geforderten Fähigkeiten, je ein kurzer Begriff.
> - `gehaltsangabe`: nur übernehmen, wenn die Anzeige eine Spanne oder Zahl nennt, sonst `null`.
> - `bewerbungsweg_hinweis`: wie beworben werden soll (Jobportal, E-Mail, Initiativbewerbung, Empfehlung), sonst `null`.
> - Nichts erfinden – was nicht in der Anzeige steht, ist `null` bzw. eine leere Liste.
>
> Stellenanzeige:
> ```
> [hier den Text oder Link einfügen]
> ```

Der Import legt daraus eine **neue** Bewerbung an und öffnet das Formular zur
Kontrolle.

---

## Format B — Absage

> Lies die folgende Absage-E-Mail und gib **ausschließlich** ein JSON-Objekt
> in genau dieser Struktur zurück – keine Erklärung, kein Markdown:
>
> ```
> {
>   "absagegrund_kategorien": ["string", "string"],
>   "absagegrund_details": "string",
>   "rohtext": "string",
>   "datum": "YYYY-MM-DD"
> }
> ```
>
> Regeln:
> - `absagegrund_kategorien` darf **ausschließlich** Werte aus diesem Katalog enthalten
>   (Mehrfachnennung erlaubt):
>   `Erfahrung/Seniorität`, `Fachliche Skills`, `Gehaltsvorstellung`,
>   `Kultureller Fit`, `Position anderweitig besetzt`, `Zu späte Bewerbung`,
>   `Formale Gründe`, `Kein Feedback erhalten`, `Sonstiges`.
> - Nennt die Absage keinen erkennbaren Grund, nimm `Kein Feedback erhalten`.
> - `absagegrund_details`: ein bis zwei Sätze, was konkret genannt wurde.
> - `rohtext`: der Originaltext der Absage, unverändert.
> - `datum`: Datum der Absage im Format YYYY-MM-DD.
>
> Absage:
> ```
> [hier den Text einfügen]
> ```

Beim Import wird die Absage **manuell einer bestehenden Bewerbung zugeordnet** –
die Datei enthält bewusst keine Referenz. Unbekannte Kategorien landen
automatisch unter `Sonstiges`; der Dialog weist darauf hin.

---

## Beispieldateien

Unter [`../beispiel_importe/`](../beispiel_importe/) liegen je eine gültige
Datei pro Format zum Ausprobieren.
