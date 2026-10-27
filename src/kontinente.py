"""Zuordnung der Länder (ISO3-Code) zu den sechs Kontinenten der Karte.
Russland zählt zu Europa, die Türkei zu Asien (wie in der UN-Systematik)."""

NAMEN = {"eu": "Europa", "as": "Asien", "na": "Nordamerika", "sa": "Südamerika", "af": "Afrika", "oc": "Ozeanien"}

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
    "EGY": "af", "ERI": "af", "ESH": "af", "ESP": "eu", "EST": "eu", "ETH": "af", "FIN": "eu",
    "FJI": "oc", "FLK": "sa", "FRA": "eu", "FRO": "eu", "FSM": "oc", "GAB": "af", "GBR": "eu",
    "GEO": "as", "GGY": "eu", "GHA": "af", "GIB": "eu", "GIN": "af", "GLP": "na", "GMB": "af",
    "GNB": "af", "GNQ": "af", "GRC": "eu", "GRD": "na", "GRL": "na", "GTM": "na", "GUF": "sa",
    "GUM": "oc", "GUY": "sa", "HKG": "as", "HND": "na", "HRV": "eu", "HTI": "na", "HUN": "eu",
    "IDN": "as", "IMN": "eu", "IND": "as", "IOT": "as", "IRL": "eu", "IRN": "as", "IRQ": "as",
    "ISL": "eu", "ISR": "as", "ITA": "eu", "JAM": "na", "JEY": "eu", "JOR": "as", "JPN": "as",
    "KAZ": "as", "KEN": "af", "KGZ": "as", "KHM": "as", "KIR": "oc", "KNA": "na", "KOR": "as",
    "KWT": "as", "LAO": "as", "LBN": "as", "LBR": "af", "LBY": "af", "LCA": "na", "LIE": "eu",
    "LKA": "as", "LSO": "af", "LTU": "eu", "LUX": "eu", "LVA": "eu", "MAC": "as", "MAF": "na",
    "MAR": "af", "MCO": "eu", "MDA": "eu", "MDG": "af", "MDV": "as", "MEX": "na", "MHL": "oc",
    "MKD": "eu", "MLI": "af", "MLT": "eu", "MMR": "as", "MNE": "eu", "MNG": "as", "MNP": "oc",
    "MOZ": "af", "MRT": "af", "MSR": "na", "MTQ": "na", "MUS": "af", "MWI": "af", "MYS": "as",
    "MYT": "af", "NAM": "af", "NCL": "oc", "NER": "af", "NFK": "oc", "NGA": "af", "NIC": "na",
    "NIU": "oc", "NLD": "eu", "NOR": "eu", "NPL": "as", "NRU": "oc", "NZL": "oc", "OMN": "as",
    "PAK": "as", "PAN": "na", "PER": "sa", "PHL": "as", "PLW": "oc", "PNG": "oc", "POL": "eu",
    "PRI": "na", "PRK": "as", "PRT": "eu", "PRY": "sa", "PSE": "as", "PYF": "oc", "QAT": "as",
    "REU": "af", "ROU": "eu", "RUS": "eu", "RWA": "af", "S19": "as", "SAU": "as", "SDN": "af",
    "SEN": "af", "SGP": "as", "SGS": "sa", "SHN": "af", "SJM": "eu", "SLB": "oc", "SLE": "af",
    "SLV": "na", "SMR": "eu", "SOM": "af", "SPM": "na", "SRB": "eu", "SSD": "af", "STP": "af",
    "SUR": "sa", "SVK": "eu", "SVN": "eu", "SWE": "eu", "SWZ": "af", "SYC": "af", "SYR": "as",
    "TCA": "na", "TCD": "af", "TGO": "af", "THA": "as", "TJK": "as", "TKL": "oc", "TKM": "as",
    "TLS": "as", "TON": "oc", "TTO": "na", "TUN": "af", "TUR": "as", "TUV": "oc", "TWN": "as",
    "TZA": "af", "UGA": "af", "UKR": "eu", "URY": "sa", "USA": "na", "UZB": "as", "VAT": "eu",
    "VCT": "na", "VEN": "sa", "VGB": "na", "VIR": "na", "VNM": "as", "VUT": "oc", "WLF": "oc",
    "WSM": "oc", "XKX": "eu", "YEM": "as", "ZAF": "af", "ZMB": "af", "ZWE": "af",
}


# Stichwoerter, mit denen Schlagzeilen einem Kontinent zugeordnet werden (Naeherung, Kleinbuchstaben).
STICHWORTE = {
    "eu": ["europe", "europa", "eu ", "ukraine", "russia", "russland", "germany", "deutschland", "france", "frankreich",
           "britain", "uk ", "italy", "spain", "poland", "polen", "netherlands", "brussels", "brüssel", "ecb", "ezb",
           "nato", "kremlin", "moscow", "kyiv", "kiew", "berlin", "baltic", "ostsee", "norway", "sweden", "finland"],
    "as": ["asia", "asien", "china", "chinese", "beijing", "taiwan", "japan", "india", "indien", "korea", "iran", "israel",
           "gaza", "saudi", "gulf", "golf", "hormuz", "hormus", "iraq", "irak", "yemen", "jemen", "houthi", "huthi",
           "red sea", "rotes meer", "turkey", "türkei", "pakistan", "indonesia", "vietnam", "singapore", "opec",
           "opec+", "middle east", "nahost", "syria", "syrien", "lebanon", "libanon", "qatar", "emirates", "south china sea"],
    "na": ["united states", "u.s.", "us ", "usa", "american", "washington", "trump", "fed ", "federal reserve", "canada",
           "kanada", "mexico", "mexiko", "panama", "wall street", "white house", "weißes haus", "pentagon", "texas"],
    "sa": ["south america", "südamerika", "brazil", "brasilien", "argentina", "argentinien", "chile", "peru", "colombia",
           "kolumbien", "venezuela", "bolivia", "ecuador", "lithium triangle", "amazon"],
    "af": ["africa", "afrika", "nigeria", "egypt", "ägypten", "suez", "ethiopia", "äthiopien", "sudan", "congo", "kongo",
           "south africa", "südafrika", "kenya", "kenia", "libya", "libyen", "sahel", "morocco", "marokko", "algeria", "algerien"],
    "oc": ["australia", "australien", "new zealand", "neuseeland", "pacific", "pazifik", "oceania", "ozeanien", "fiji", "papua"],
}


def kontinent_aus_text(text):
    """Kontinent mit den meisten Stichwort-Treffern im Text, oder None bei keinem Treffer oder Gleichstand."""
    t = " " + text.lower() + " "
    best, bester = 0, None
    gleich = False
    for k, woerter in STICHWORTE.items():
        n = sum(1 for w in woerter if w in t)
        if n > best:
            best, bester, gleich = n, k, False
        elif n == best and n > 0:
            gleich = True
    return None if gleich or not best else bester
