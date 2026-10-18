"""
Logica aplicației, independentă de FastAPI.

api.py doar primește cererile HTTP și apelează funcțiile de aici, așa că
totul se poate testa și refolosi fără server (de ex. din experimente).
"""

import math
import os
import re
import time

from core import GrilaUniforma, Harta, QuadTree, cauta_drum, netezeste
from core.quadtree import PreaMulteCelule
from core.geometrie import lungime_drum, numar_viraje

AICI = os.path.dirname(os.path.abspath(__file__))
DIRECTOR_HARTI = os.path.join(AICI, "..", "harti")

MAX_CELULE = 250_000            # protecție: o latură prea mică ar bloca serverul
_NUME_VALID = re.compile(r"^[A-Za-z0-9_-]{1,50}$")
HARTI_PROTEJATE = {"exemplu", "culoar_ingust", "demo"}    # generate de demo_etapa1.py
EPS = 1e-9


class EroareCerere(Exception):
    """Eroare cu cod HTTP, transformată în răspuns JSON de api.py."""

    def __init__(self, mesaj, cod=400):
        super().__init__(mesaj)
        self.cod = cod


# ----------------------------------------------------------------------
# Descompunere
# ----------------------------------------------------------------------
def construieste_descompunere(harta: Harta, tip="grila", latura=2.0, vecinatate=4,
                              adancime_max=6):
    """Returnează (descompunerea, timpul de construire în ms)."""
    if tip == "grila":
        # aceeași rotunjire ca în GrilaUniforma
        nr_celule = (math.ceil(harta.latime / latura - EPS) *
                     math.ceil(harta.inaltime / latura - EPS))
        if nr_celule > MAX_CELULE:
            raise EroareCerere(f"Latura de {latura:g} cm ar produce {nr_celule} celule "
                               f"(maxim {MAX_CELULE}). Mărește latura celulei.")
        t0 = time.perf_counter()
        graf = GrilaUniforma(harta, latura, vecinatate)
    elif tip == "quadtree":
        # numărul de frunze nu se știe dinainte: construcția se oprește dacă depășește limita
        t0 = time.perf_counter()
        try:
            graf = QuadTree(harta, latura, vecinatate, adancime_max, max_frunze=MAX_CELULE)
        except PreaMulteCelule as e:
            raise EroareCerere(str(e)) from e
    else:
        raise EroareCerere(f"Tip de descompunere necunoscut: {tip}")
    return graf, (time.perf_counter() - t0) * 1000


def descriere_descompunere(graf, timp_ms, include_celule=True):
    return {
        "tip": graf.tip,
        "latura": graf.latura,
        "vecinatate": graf.vecinatate,
        "adancime_max": graf.adancime_max if graf.tip == "quadtree" else None,
        "statistici": graf.statistici(),
        "timp_ms": round(timp_ms, 3),
        "celule": graf.celule_compacte() if include_celule else None,
    }


def descompune(harta: Harta, **parametri):
    graf, timp_ms = construieste_descompunere(harta, **parametri)
    return descriere_descompunere(graf, timp_ms)


# ----------------------------------------------------------------------
# Planificare
# ----------------------------------------------------------------------
def _descriere_drum(graf, rez, netezire, include_ordine):
    d = {
        "metoda": rez.metoda, "gasit": rez.gasit, "motiv": rez.motiv,
        "puncte": rez.puncte, "cost": round(rez.cost, 3),
        "lungime": round(rez.lungime, 3), "viraje": rez.viraje,
        "noduri_vizitate": rez.noduri_vizitate, "timp_ms": round(rez.timp_ms, 3),
        "puncte_netezite": None, "lungime_netezita": None, "viraje_netezite": None,
        "ordine_vizitare": None,
    }
    if rez.gasit and netezire:
        netezit = netezeste(graf, rez.puncte)
        d["puncte_netezite"] = netezit
        d["lungime_netezita"] = round(lungime_drum(netezit), 3)
        d["viraje_netezite"] = numar_viraje(netezit)
    if include_ordine:
        d["ordine_vizitare"] = [graf.index(n) for n in rez.ordine_vizitare]
    return d


def planifica(harta: Harta, metoda="astar", netezire=True, include_celule=True,
              include_ordine=True, **parametri):
    graf, timp_ms = construieste_descompunere(harta, **parametri)
    rez = cauta_drum(graf, harta.start, harta.tinta, metoda)
    return {
        "descompunere": descriere_descompunere(graf, timp_ms, include_celule),
        "drum": _descriere_drum(graf, rez, netezire, include_ordine),
    }


def compara(harta: Harta, metode, vecinatati, tip="grila", latura=2.0, adancime_max=6,
            **_ignorat):
    """Rulează fiecare algoritm pentru fiecare vecinătate, pe aceeași hartă."""
    rezultate = []
    statistici = None
    for vecinatate in vecinatati:
        graf, _ = construieste_descompunere(harta, tip, latura, vecinatate, adancime_max)
        statistici = graf.statistici()
        for metoda in metode:
            rez = cauta_drum(graf, harta.start, harta.tinta, metoda)
            d = _descriere_drum(graf, rez, netezire=True, include_ordine=False)
            rezultate.append({
                "vecinatate": vecinatate, "metoda": metoda, "gasit": rez.gasit,
                "lungime": d["lungime"], "lungime_netezita": d["lungime_netezita"],
                "viraje": d["viraje"], "viraje_netezite": d["viraje_netezite"],
                "noduri_vizitate": d["noduri_vizitate"], "timp_ms": d["timp_ms"],
            })
    if statistici is None:
        raise EroareCerere("Alege cel puțin o vecinătate")
    return {"tip": tip, "latura": latura, "statistici": statistici, "rezultate": rezultate}


# ----------------------------------------------------------------------
# Hărți salvate
# ----------------------------------------------------------------------
def _cale_harta(nume):
    if not _NUME_VALID.match(nume):
        raise EroareCerere("Numele hărții poate conține doar litere, cifre, '_' și '-' "
                           "(maxim 50 de caractere)")
    return os.path.join(DIRECTOR_HARTI, f"{nume}.json")


def lista_harti():
    if not os.path.isdir(DIRECTOR_HARTI):
        return []
    return sorted(f[:-5] for f in os.listdir(DIRECTOR_HARTI) if f.endswith(".json"))


def incarca_harta(nume) -> Harta:
    cale = _cale_harta(nume)
    if not os.path.isfile(cale):
        raise EroareCerere(f"Harta '{nume}' nu există", 404)
    return Harta.incarca(cale)


def salveaza_harta(nume, harta: Harta):
    cale = _cale_harta(nume)
    if nume in HARTI_PROTEJATE:
        raise EroareCerere(f"Harta '{nume}' face parte din exemple și nu poate fi "
                           "suprascrisă. Salveaz-o sub alt nume.", 403)
    os.makedirs(DIRECTOR_HARTI, exist_ok=True)
    harta.salveaza(cale)
