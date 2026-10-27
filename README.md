# Weltmodell

Analyse-Werkzeug für die Weltlage nach Kontinenten: Handelsströme auf der Weltkarte, Kennzahlen,
aktuelle Events und eine Schock-Simulation. Die Webseite lädt ihre Daten aus `docs/data/`.
Ein täglicher Lauf bei GitHub holt neue Daten und aktualisiert die Dateien selbstständig.

## Einmalige Einrichtung (ca. 15 Minuten, alles im Browser)

1. **ZIP entpacken.** Rechtsklick auf die ZIP-Datei, "Alle extrahieren".
2. **Repository anlegen.** Auf github.com oben rechts auf **+**, dann **New repository**.
   Name: `weltmodell`. Sichtbarkeit: **Public** (nur dann ist die Webseite kostenlos).
   Kein Häkchen bei "Add a README file". Dann **Create repository**.
3. **Dateien hochladen.** Auf der neuen Seite den Link **uploading an existing file** anklicken.
   Öffne den entpackten Ordner `weltmodell`, markiere **alles darin** (die Ordner `src`, `data`, `docs`,
   `tools`, `workflow-vorlage` und die Dateien `README.md`, `.gitignore`) und ziehe es ins Browserfenster.
   Unten **Commit changes** klicken.
4. **Zeitplan-Datei anlegen.** Versteckte Ordner wie `.github` werden beim Hochladen oft übersehen,
   deshalb legen wir die Datei von Hand an: Im Repository **Add file**, **Create new file**.
   Als Dateinamen `.github/workflows/update.yml` eintippen (jedes `/` erzeugt einen Ordner).
   Den kompletten Inhalt der Datei `workflow-vorlage/update.yml` hineinkopieren, dann **Commit changes**.
5. **Webseite einschalten.** **Settings**, links **Pages**. Unter "Build and deployment":
   Source **Deploy from a branch**, Branch **main**, Ordner **/docs**, **Save**.
   Nach ein bis zwei Minuten steht oben die Adresse `https://DEIN-NAME.github.io/weltmodell/`.
6. **Ersten Lauf starten.** Reiter **Actions**. Falls GitHub fragt, die Workflows aktivieren.
   Links **Daten aktualisieren** wählen, rechts **Run workflow**, **Run workflow**.
   Nach ein bis drei Minuten erscheint ein grüner Haken. Dann die Webseite neu laden.

## Was danach von selbst passiert

* Jeden Morgen gegen 6 bis 7 Uhr deutscher Zeit holt der Lauf neue Daten (Weltbank, IMF PortWatch),
  speichert sie als CSV-Dateien in `data/` und baut die Dateien für die Webseite neu.
* Fällt eine Quelle aus, laufen die anderen weiter. Die Seite zeigt unten, welche Quelle zuletzt fehlgeschlagen ist.
  Schlägt jede Quelle fehl, wird der Lauf rot markiert und GitHub schickt dir eine E-Mail.
* GitHub kann geplante Läufe in öffentlichen Repositories pausieren, wenn 60 Tage lang nichts im Repository
  passiert. Im Reiter Actions lässt sich der Zeitplan mit einem Klick wieder einschalten.

## Von Hand zu pflegen (Ordner `data/manual/`)

| Datei | Inhalt | Wann erneuern |
|---|---|---|
| `flows.json` | Warenströme zwischen den Kontinenten (CEPII BACI) | etwa einmal pro Jahr, wenn BACI ein neues Jahr veröffentlicht |
| `events.json` | Momentaufnahme aktueller Events mit Quellen | nach Bedarf |
| `continents_seed.json` | Startwerte bis zum ersten Lauf | nie |

* **Warenströme erneuern:** Neue BACI-Datei laden, lokal `python tools/trade_aggregate.py ... --year 2024`
  ausführen (Anleitung im Kopf der Datei), die erzeugte `flows.json` im Repository nach `data/manual/` hochladen
  und die alte ersetzen. Der Lauf startet dann automatisch.
* **Events erneuern:** Neue `events.json` im selben Ordner ersetzen.

## Ordner

* `src/` Python-Code. `update_all.py` ist der Einstiegspunkt, `sources/` enthält je Quelle eine Datei.
* `data/` die gesammelten Daten als CSV (`worldbank.csv`, `portwatch.csv`) und `status.json`.
  Beim Lauf entsteht daraus die SQLite-Datenbank `data/weltmodell.db` (wird nicht in Git gespeichert).
* `docs/` die Webseite (`index.html`) und ihre Daten (`docs/data/*.json`).
* `tools/` Hilfsskripte, die du von Hand ausführst.
* `.github/workflows/update.yml` der Zeitplan.

## Lokal ausprobieren

```
python src/update_all.py
cd docs
python -m http.server
```

Dann `http://localhost:8000` im Browser öffnen. Die Seite funktioniert nicht, wenn man `index.html`
direkt per Doppelklick öffnet, weil der Browser dann keine Dateien nachladen darf.

## Neue Datenquelle ergänzen

1. In `src/sources/` eine Datei anlegen mit `NAME = "meinequelle"` und einer Funktion `fetch(vorhanden)`,
   die `(zeilen, warnungen)` zurückgibt. Eine Zeile ist ein Wörterbuch mit `indicator`, `entity`,
   `entity_type`, `date` und `value`. `worldbank.py` ist ein gutes Vorbild.
2. In `src/update_all.py` und `src/export.py` den Namen in die Listen `QUELLEN` eintragen.
3. Für die Anzeige in `export.py` eine Auswertung ergänzen und in `docs/index.html` darstellen.

## So entstehen die Kennzahlen

* Alle Werte kommen je Land von der Weltbank, jeweils der neueste vorhandene Wert, und werden zu Kontinenten zusammengefasst.
* BIP und Bevölkerung werden addiert. Wachstum, Inflation, Handel und Staatsschulden sind nach BIP gewichtete Mittel
  (Inflation je Land bei 100 % gedeckelt). Politische Stabilität ist nach Bevölkerung gewichtet.
* **Stabilität (0 bis 100)** rechnet den Weltbank-Index "Political Stability" (Skala -2,5 bis +2,5) um.
  **Wirtschaftsdynamik (0 bis 100)** rechnet das Wachstum von -2 % bis +6 % um.
  **Ereignisse** zählt die Events pro Kontinent, fünf gelten als voll.
  Die Schwellen für "hoch, mittel, niedrig" (ab 55 und ab 40) sind Darstellungsentscheidungen.
* Länder ohne Wert fehlen in der Summe. Taiwan wird von der Weltbank nicht ausgewiesen.

## Quellen und Nutzungsbedingungen

* Weltbank, World Development Indicators und Worldwide Governance Indicators (api.worldbank.org).
* CEPII, BACI-Handelsdatenbank (cepii.fr), Nutzungsbedingungen dort beachten.
* IMF PortWatch. Zitierhinweis des Anbieters: "Sources: UN Global Platform; IMF PortWatch (portwatch.imf.org)".
  Nutzungsbedingungen: imf.org/external/terms.htm.
* Events: Quellenangaben stehen an jedem Event.
