#!/usr/bin/env python3
"""
Handelsdaten für das Weltmodell aufbereiten.

Das Skript liest die BACI-Datenbank des CEPII (Handelsströme zwischen allen Ländern,
nach Produkt, pro Jahr) und fasst sie zusammen zu:

    Exporteur-Kontinent  ->  Importeur-Kontinent  ->  Warengruppe  ->  Wert in Mrd. US-Dollar

Ergebnis ist die Datei flows.json im Format, das die Seite verwendet.

--------------------------------------------------------------------------
SO BENUTZT DU ES
--------------------------------------------------------------------------
1. Daten herunterladen (kostenlos, ohne Konto):
   https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37
   Lade EINE Jahresdatei der aktuellsten HS-Version herunter (zum Beispiel HS22)
   und die Datei mit den Ländercodes (country_codes_V....csv). Beide stecken
   in derselben ZIP-Datei. Entpacke sie in einen Ordner.

2. Skript starten (Python 3.8 oder neuer, keine zusätzlichen Pakete nötig):
   python trade_aggregate.py BACI_HS22_Y2023_V202401.csv country_codes_V202401.csv --year 2023

   Optional: --out flows.json   Name der Ausgabedatei
             --min 2            Warengruppen unter 2 Mrd. $ je Richtung weglassen

3. Schicke mir die erzeugte flows.json (oder ihren Inhalt). Ich setze sie in die Seite ein.

Die Datei ist groß (mehrere Millionen Zeilen). Der Lauf dauert je nach Rechner
ein bis drei Minuten.

--------------------------------------------------------------------------
WIE DIE ZUORDNUNG FUNKTIONIERT
--------------------------------------------------------------------------
Kontinent:    Jedes Land wird über seinen ISO3-Code einem der sechs Kontinente
              der Karte zugeordnet (siehe KONTINENT unten). Russland zählt, wie
              in der UN-Systematik, zu Europa, die Türkei zu Asien.
Warengruppe:  Das BACI-Produkt hat einen sechsstelligen HS-Code. Die ersten zwei
              Stellen sind das "Kapitel". Aus den Kapiteln bilden wir die neun
              Warengruppen der Seite (siehe GRUPPEN unten). Das ist eine grobe,
              bewusste Vereinfachung. Wer Flugzeuge lieber bei den Maschinen sehen
              will, ändert nur die Zuordnung in GRUPPEN.
Handel innerhalb eines Kontinents (zum Beispiel Deutschland -> Frankreich) wird
nicht gezählt, weil die Karte nur Ströme zwischen Kontinenten zeigt.
"""
import argparse
import csv
import json
import sys
from collections import defaultdict

# ISO3-Ländercode -> Kontinent-Kürzel der Seite
KONTINENT = {
    "ABW": "na", "AFG": "as", "AGO": "af", "AIA": "na", "ALA": "eu", "ALB": "eu", "AND": "eu",
    "ARE": "as", "ARG": "sa", "ARM": "as", "ASM": "oc", "ATG": "na", "AUS": "oc", "AUT": "eu",
    "AZE": "as", "BDI": "af", "BEL": "eu", "BEN": "af", "BES": "na", "BFA": "af", "BGD": "as",
    "BGR": "eu", "BHR": "as", "BHS": "na", "BIH": "eu", "BLM": "na", "BLR": "eu", "BLZ": "na",
    "BMU": "na", "BOL": "sa", "BRA": "sa", "BRB": "na", "BRN": "as", "BTN": "as", "BWA": "af",
    "CAF": "af", "CAN": "na", "CCK": "as", "CHE": "eu", "CHL": "sa", "CHN": "as", "CIV": "af",
    "CMR": "af", "COD": "af", "COG": "af", "COK": "oc", "COL": "sa", "COM": "af", "CPV": "af",
    "CRI": "na", "CUB": "na", "CUW": "na", "CXR": "as", "CYM": "na", "CYP": "as", "CZE": "eu",
    "DEU": "eu", "DJI": "af", "DMA": "na", "DNK": "eu", "DOM": "na", "DZA": "af", "ECU": "sa",
    "EGY": "af", "ERI": "af", "ESP": "eu", "EST": "eu", "ETH": "af", "FIN": "eu", "FJI": "oc",
    "FLK": "sa", "FRA": "eu", "FRO": "eu", "FSM": "oc", "GAB": "af", "GBR": "eu", "GEO": "as",
    "GGY": "eu", "GHA": "af", "GIB": "eu", "GIN": "af", "GLP": "na", "GMB": "af", "GNB": "af",
    "GNQ": "af", "GRC": "eu", "GRD": "na", "GRL": "na", "GTM": "na", "GUF": "sa", "GUM": "oc",
    "GUY": "sa", "HKG": "as", "HND": "na", "HRV": "eu", "HTI": "na", "HUN": "eu", "IDN": "as",
    "IMN": "eu", "IND": "as", "IOT": "as", "IRL": "eu", "IRN": "as", "IRQ": "as", "ISL": "eu",
    "ISR": "as", "ITA": "eu", "JAM": "na", "JEY": "eu", "JOR": "as", "JPN": "as", "KAZ": "as",
    "KEN": "af", "KGZ": "as", "KHM": "as", "KIR": "oc", "KNA": "na", "KOR": "as", "KWT": "as",
    "LAO": "as", "LBN": "as", "LBR": "af", "LBY": "af", "LCA": "na", "LIE": "eu", "LKA": "as",
    "LSO": "af", "LTU": "eu", "LUX": "eu", "LVA": "eu", "MAC": "as", "MAF": "na", "MAR": "af",
    "MCO": "eu", "MDA": "eu", "MDG": "af", "MDV": "as", "MEX": "na", "MHL": "oc", "MKD": "eu",
    "MLI": "af", "MLT": "eu", "MMR": "as", "MNE": "eu", "MNG": "as", "MNP": "oc", "MOZ": "af",
    "MRT": "af", "MSR": "na", "MTQ": "na", "MUS": "af", "MWI": "af", "MYS": "as", "MYT": "af",
    "NAM": "af", "NCL": "oc", "NER": "af", "NFK": "oc", "NGA": "af", "NIC": "na", "NIU": "oc",
    "NLD": "eu", "NOR": "eu", "NPL": "as", "NRU": "oc", "NZL": "oc", "OMN": "as", "PAK": "as",
    "PAN": "na", "PER": "sa", "PHL": "as", "PLW": "oc", "PNG": "oc", "POL": "eu", "PRI": "na",
    "PRK": "as", "PRT": "eu", "PRY": "sa", "PSE": "as", "PYF": "oc", "QAT": "as", "REU": "af",
    "ROU": "eu", "RUS": "eu", "RWA": "af", "SAU": "as", "SDN": "af", "SEN": "af", "SGP": "as",
    "SGS": "sa", "SHN": "af", "SJM": "eu", "SLB": "oc", "SLE": "af", "SLV": "na", "SMR": "eu",
    "SOM": "af", "SPM": "na", "SRB": "eu", "SSD": "af", "STP": "af", "SUR": "sa", "SVK": "eu",
    "SVN": "eu", "SWE": "eu", "SWZ": "af", "SYC": "af", "SYR": "as", "TCA": "na", "TCD": "af",
    "TGO": "af", "THA": "as", "TJK": "as", "TKL": "oc", "TKM": "as", "TON": "oc", "TTO": "na",
    "TUN": "af", "TUR": "as", "TUV": "oc", "TWN": "as", "TZA": "af", "UGA": "af", "UKR": "eu",
    "URY": "sa", "USA": "na", "UZB": "as", "VCT": "na", "VEN": "sa", "VGB": "na", "VIR": "na",
    "VNM": "as", "VUT": "oc", "WLF": "oc", "WSM": "oc", "YEM": "as", "ZAF": "af", "ZMB": "af",
    "ZWE": "af",
    # Ergänzungen, die in der Standardliste fehlen oder in BACI anders heißen
    "XKX": "eu",  # Kosovo
    "TLS": "as",  # Timor-Leste
    "VAT": "eu",  # Vatikanstadt
    "ESH": "af",  # Westsahara
    "S19": "as",  # BACI-Sammelcode für Taiwan ("Other Asia, nes")
}

# HS-Kapitel (die ersten zwei Stellen des Produktcodes) -> Warengruppe der Seite
GRUPPEN = {}
def _gruppe(name, kapitel):
    for k in kapitel:
        GRUPPEN[k] = name

_gruppe("Agrar", range(1, 25))                                   # Tiere, Pflanzen, Nahrung, Getränke, Tabak
_gruppe("Energie", [27])                                         # Kohle, Erdöl, Erdgas und Produkte
_gruppe("Metalle & Erze", [25, 26] + list(range(71, 84)))        # Steine, Erze, Edelmetalle, Eisen, Stahl, Kupfer ...
_gruppe("Pharma", [30])
_gruppe("Chemie", [28, 29] + list(range(31, 41)))                # Chemikalien, Dünger, Kunststoffe, Gummi (ohne Pharma)
_gruppe("Textilien & Konsum", list(range(41, 71)) + list(range(92, 93)) + list(range(94, 98)))
_gruppe("Elektronik", [85, 90, 91])                              # Elektrotechnik, Optik, Medizintechnik, Uhren
_gruppe("Maschinen", [84, 93])
_gruppe("Fahrzeuge", [86, 87, 88, 89])                           # Schiene, Straße, Luft, Wasser
# Kapitel 98 und 99 (Sonderfälle) werden bewusst nicht gezählt.

GRUPPEN_REIHENFOLGE = ["Elektronik", "Maschinen", "Fahrzeuge", "Pharma", "Chemie",
                       "Textilien & Konsum", "Energie", "Metalle & Erze", "Agrar"]


def lade_laender(pfad):
    """Liest die Ländercode-Datei von BACI: numerischer Code -> Kontinent."""
    code_zu_kontinent = {}
    ohne_zuordnung = {}
    with open(pfad, newline="", encoding="utf-8", errors="replace") as f:
        leser = csv.DictReader(f)
        spalten = leser.fieldnames or []
        if "country_code" not in spalten or "country_iso3" not in spalten:
            sys.exit("Die Ländercode-Datei hat nicht die erwarteten Spalten "
                     "(country_code, country_iso3). Gefunden: %s" % spalten)
        for z in leser:
            code = z["country_code"].strip()
            iso3 = z["country_iso3"].strip()
            if iso3 in KONTINENT:
                code_zu_kontinent[code] = KONTINENT[iso3]
            else:
                ohne_zuordnung[code] = "%s (%s)" % (z.get("country_name", "?").strip(), iso3)
    return code_zu_kontinent, ohne_zuordnung


def aggregiere(baci_pfad, code_zu_kontinent):
    """Summiert Wert (in Tsd. US-Dollar) je (von, nach, Warengruppe)."""
    summen = defaultdict(float)
    nicht_gezaehlt = defaultdict(float)   # Wert je Grund, für den Prüfbericht
    gesamt = 0.0
    zeilen = 0
    with open(baci_pfad, newline="", encoding="utf-8", errors="replace") as f:
        leser = csv.reader(f)
        kopf = next(leser)
        try:
            i_von, i_nach, i_prod, i_wert = (kopf.index("i"), kopf.index("j"),
                                             kopf.index("k"), kopf.index("v"))
        except ValueError:
            sys.exit("Die BACI-Datei hat nicht die erwarteten Spalten (t, i, j, k, v, q). "
                     "Gefunden: %s" % kopf)
        for z in leser:
            zeilen += 1
            try:
                wert = float(z[i_wert])
            except ValueError:
                continue
            gesamt += wert
            von = code_zu_kontinent.get(z[i_von])
            nach = code_zu_kontinent.get(z[i_nach])
            if von is None or nach is None:
                nicht_gezaehlt["Land ohne Kontinent-Zuordnung"] += wert
                continue
            if von == nach:
                nicht_gezaehlt["innerhalb eines Kontinents"] += wert
                continue
            # Produktcode ist eine Zahl wie 10121; die führende Null fehlt, daher // 10000
            kapitel = int(z[i_prod]) // 10000
            gruppe = GRUPPEN.get(kapitel)
            if gruppe is None:
                nicht_gezaehlt["Kapitel 98/99 oder unbekannt"] += wert
                continue
            summen[(von, nach, gruppe)] += wert
    return summen, nicht_gezaehlt, gesamt, zeilen


def baue_flows(summen, minimum_mrd):
    """Macht aus den Summen die Liste, die die Seite verwendet."""
    je_strom = defaultdict(dict)
    for (von, nach, gruppe), tsd in summen.items():
        je_strom[(von, nach)][gruppe] = tsd / 1_000_000.0   # Tsd. $ -> Mrd. $
    flows = []
    for (von, nach), gruppen in sorted(je_strom.items()):
        liste = [[g, round(w)] for g, w in gruppen.items() if round(w) >= minimum_mrd]
        liste.sort(key=lambda x: x[1], reverse=True)
        if liste:
            flows.append({"f": von, "t": nach, "g": liste})
    return flows


def main():
    p = argparse.ArgumentParser(description="BACI-Handelsdaten nach Kontinent und Warengruppe zusammenfassen.")
    p.add_argument("baci", help="BACI-Jahresdatei, zum Beispiel BACI_HS22_Y2023_V202401.csv")
    p.add_argument("laender", help="Ländercode-Datei, zum Beispiel country_codes_V202401.csv")
    p.add_argument("--year", type=int, required=True, help="Jahr der Daten (wird in die Ausgabe geschrieben)")
    p.add_argument("--out", default="flows.json", help="Ausgabedatei (Standard: flows.json)")
    p.add_argument("--min", type=int, default=2, dest="minimum",
                   help="Warengruppen unter diesem Wert in Mrd. $ je Richtung weglassen (Standard: 2)")
    a = p.parse_args()
    if not 1990 <= a.year <= 2100:
        sys.exit("Bitte das Jahr vierstellig angeben, zum Beispiel --year 2023 (eingegeben: %d)." % a.year)

    print("Lese Länder ...")
    code_zu_kontinent, ohne = lade_laender(a.laender)
    print("  %d Länder zugeordnet, %d ohne Zuordnung" % (len(code_zu_kontinent), len(ohne)))

    print("Lese Handelsdaten (das dauert etwas) ...")
    summen, nicht_gezaehlt, gesamt, zeilen = aggregiere(a.baci, code_zu_kontinent)
    print("  %d Zeilen gelesen" % zeilen)

    flows = baue_flows(summen, a.minimum)
    ergebnis = {
        "quelle": "CEPII BACI",
        "jahr": a.year,
        "einheit": "Mrd. US-Dollar pro Jahr",
        "flows": flows,
    }
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(ergebnis, f, ensure_ascii=False, indent=1)

    # Prüfbericht: Was ist nicht in der Ausgabe gelandet und wie viel ist das?
    print("\nPrüfbericht (Anteil am gesamten Welthandel dieser Datei)")
    for grund, wert in sorted(nicht_gezaehlt.items(), key=lambda x: -x[1]):
        print("  nicht gezählt: %-34s %5.1f %%" % (grund, 100 * wert / gesamt if gesamt else 0))
    gezaehlt = sum(summen.values())
    print("  gezählt (zwischen Kontinenten):     %5.1f %%" % (100 * gezaehlt / gesamt if gesamt else 0))
    if ohne:
        print("\nLänder ohne Kontinent-Zuordnung (bei Bedarf in KONTINENT oben ergänzen):")
        for code, name in sorted(ohne.items(), key=lambda x: x[1]):
            print("  %s  %s" % (code, name))
    print("\nFertig: %d Ströme in %s geschrieben." % (len(flows), a.out))


if __name__ == "__main__":
    main()
