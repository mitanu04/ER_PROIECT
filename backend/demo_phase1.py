"""
Etapa 1 - demonstrație: descompunere omogenă + 4 algoritmi de căutare.

Rulare (din folderul backend):
    python demo_etapa1.py

Generează în ../figuri:
    1_descompunere_omogena.png  - harta, grila și drumul A* (ca figura din temă)
    2_comparatie_algoritmi.png  - BFS / Dijkstra / A* / Greedy, vecinătate 4 și 8
    3_culoar_ingust.png         - efectul rezoluției (metoda e aproximativă)
    4_quadtree.png              - grilă uniformă vs. metoda arborelui, pe harta demo
și afișează un tabel comparativ în consolă. Salvează și hărțile-exemplu în ../harti.
"""

import os

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from core import (GrilaUniforma, METODE, QuadTree, cauta_drum, harta_culoar_ingust,
                  harta_demo, harta_exemplu, netezeste)
from core.geometrie import lungime_drum, numar_viraje
from vizualizare import (CULOARE_DRUM, CULOARE_NETEZIT, CULOARE_VIZITAT,
                         deseneaza_capete, deseneaza_celule, deseneaza_drum, deseneaza_grila,
                         deseneaza_obstacole, deseneaza_vizitate, pregateste_axe)

AICI = os.path.dirname(os.path.abspath(__file__))
FIGURI = os.path.join(AICI, "..", "figuri")
HARTI = os.path.join(AICI, "..", "harti")
NUME_METODE = {"bfs": "BFS", "dijkstra": "Dijkstra", "astar": "A*", "greedy": "Greedy"}
LATURA = 2.0   # cm


def figura_descompunere(harta):
    grila = GrilaUniforma(harta, LATURA, vecinatate=4)
    rez = cauta_drum(grila, harta.start, harta.tinta, "astar")
    fig, ax = plt.subplots(figsize=(8, 5.8))
    deseneaza_grila(ax, grila)
    deseneaza_obstacole(ax, harta)
    deseneaza_drum(ax, rez.puncte, lw=2.5)
    deseneaza_capete(ax, harta)
    s = grila.statistici()
    pregateste_axe(ax, harta, f"Descompunere omogenă - celulă {LATURA:g} cm, "
                              f"{s['celule_libere']} libere / {s['celule_mixte']} mixte / "
                              f"{s['celule_ocupate']} ocupate · drum A*")
    fig.tight_layout()
    cale = os.path.join(FIGURI, "1_descompunere_omogena.png")
    fig.savefig(cale, dpi=150)
    plt.close(fig)
    return cale


def figura_comparatie(harta):
    fig, axe = plt.subplots(2, 4, figsize=(18, 7.6))
    randuri_tabel = []
    for i, vecinatate in enumerate((4, 8)):
        grila = GrilaUniforma(harta, LATURA, vecinatate=vecinatate)
        for j, metoda in enumerate(METODE):
            ax = axe[i, j]
            rez = cauta_drum(grila, harta.start, harta.tinta, metoda)
            deseneaza_grila(ax, grila, linii=False)
            deseneaza_vizitate(ax, grila, rez.ordine_vizitare)
            deseneaza_obstacole(ax, harta)
            if rez.gasit:
                netezit = netezeste(grila, rez.puncte)
                deseneaza_drum(ax, rez.puncte, lw=2)
                deseneaza_drum(ax, netezit, culoare=CULOARE_NETEZIT, stil="--", lw=2)
                titlu = (f"{NUME_METODE[metoda]}, {vecinatate} vecini\n"
                         f"lungime {rez.lungime:.1f} cm → {lungime_drum(netezit):.1f} cm netezit · "
                         f"{rez.noduri_vizitate} vizitate")
                randuri_tabel.append((NUME_METODE[metoda], vecinatate, rez.lungime,
                                      lungime_drum(netezit), rez.viraje,
                                      numar_viraje(netezit), rez.noduri_vizitate, rez.timp_ms))
            else:
                titlu = f"{NUME_METODE[metoda]}, {vecinatate} vecini\n{rez.motiv}"
            deseneaza_capete(ax, harta)
            pregateste_axe(ax, harta, titlu)

    legenda = [Line2D([], [], color=CULOARE_DRUM, lw=2, label="drum pe celule"),
               Line2D([], [], color=CULOARE_NETEZIT, lw=2, ls="--", label="drum netezit"),
               Line2D([], [], marker="s", ls="", ms=10, color=CULOARE_VIZITAT,
                      label="celule vizitate")]
    fig.legend(handles=legenda, loc="lower center", ncol=3, frameon=False, fontsize=10)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    cale = os.path.join(FIGURI, "2_comparatie_algoritmi.png")
    fig.savefig(cale, dpi=130)
    plt.close(fig)
    return cale, randuri_tabel


def figura_culoar_ingust():
    harta = harta_culoar_ingust()
    fig, axe = plt.subplots(1, 3, figsize=(15, 4.2))
    rezumat = []
    for ax, latura in zip(axe, (1.0, 1.5, 2.0)):
        grila = GrilaUniforma(harta, latura, vecinatate=4)
        rez = cauta_drum(grila, harta.start, harta.tinta, "astar")
        deseneaza_grila(ax, grila)
        deseneaza_obstacole(ax, harta)
        deseneaza_drum(ax, rez.puncte, lw=2.5)
        deseneaza_capete(ax, harta)
        stare = f"drum găsit, {rez.lungime:.1f} cm" if rez.gasit else "drum NEGĂSIT"
        pregateste_axe(ax, harta, f"Celulă {latura:g} cm - {stare}")
        rezumat.append((latura, rez.gasit))
    fig.suptitle("Culoar de 3 cm: la rezoluție mică drumul dispare, deși există",
                 fontsize=11, x=0.01, ha="left")
    fig.tight_layout()
    cale = os.path.join(FIGURI, "3_culoar_ingust.png")
    fig.savefig(cale, dpi=150)
    plt.close(fig)
    return cale, rezumat


def figura_quadtree():
    """Aceeași finețe minimă (1 cm), cu grilă uniformă și cu quadtree."""
    harta = harta_demo()
    descompuneri = [("Grilă uniformă, celulă 1 cm", GrilaUniforma(harta, 1.0, vecinatate=8)),
                    ("Quadtree, latură minimă 1 cm", QuadTree(harta, 1.0, 8, adancime_max=7))]
    fig, axe = plt.subplots(1, 2, figsize=(16, 5.8))
    rezumat = []
    for ax, (nume, graf) in zip(axe, descompuneri):
        rez = cauta_drum(graf, harta.start, harta.tinta, "astar")
        netezit = netezeste(graf, rez.puncte)
        deseneaza_celule(ax, graf, rez.ordine_vizitare)
        deseneaza_obstacole(ax, harta)
        deseneaza_drum(ax, rez.puncte, lw=2)
        deseneaza_drum(ax, netezit, culoare=CULOARE_NETEZIT, stil="--", lw=2)
        n = graf.statistici()["celule_total"]
        pregateste_axe(ax, harta, f"{nume}: {n} celule · A* vizitează {rez.noduri_vizitate} · "
                                  f"drum {rez.lungime:.1f} → {lungime_drum(netezit):.1f} cm netezit")
        rezumat.append((nume, n, rez.noduri_vizitate, rez.lungime, lungime_drum(netezit)))
    fig.tight_layout()
    cale = os.path.join(FIGURI, "4_quadtree.png")
    fig.savefig(cale, dpi=130)
    plt.close(fig)
    return cale, rezumat


def main():
    os.makedirs(FIGURI, exist_ok=True)
    os.makedirs(HARTI, exist_ok=True)
    harta = harta_exemplu()
    harta.salveaza(os.path.join(HARTI, "exemplu.json"))
    harta_culoar_ingust().salveaza(os.path.join(HARTI, "culoar_ingust.json"))
    harta_demo().salveaza(os.path.join(HARTI, "demo.json"))

    print("Figura:", figura_descompunere(harta))
    cale, tabel = figura_comparatie(harta)
    print("Figura:", cale)
    cale, rezumat = figura_culoar_ingust()
    print("Figura:", cale)
    cale, rezumat_quadtree = figura_quadtree()
    print("Figura:", cale)

    print(f"\nComparație pe harta exemplu (celulă {LATURA:g} cm)\n")
    antet = f"{'Algoritm':<9}{'Vecini':>7}{'Lungime':>10}{'Netezit':>10}" \
            f"{'Viraje':>8}{'→ net.':>8}{'Vizitate':>10}{'Timp ms':>10}"
    print(antet)
    print("-" * len(antet))
    for nume, vec, lung, lung_n, vir, vir_n, viz, t in tabel:
        print(f"{nume:<9}{vec:>7}{lung:>10.1f}{lung_n:>10.1f}{vir:>8}{vir_n:>8}{viz:>10}{t:>10.2f}")

    print("\nCuloar îngust:")
    for latura, gasit in rezumat:
        print(f"  celulă {latura:g} cm: {'drum găsit' if gasit else 'fără drum'}")

    print("\nGrilă vs. quadtree pe harta demo (A*, 8 vecini):")
    for nume, n, vizitate, lung, lung_n in rezumat_quadtree:
        print(f"  {nume:<30} {n:>6} celule {vizitate:>6} vizitate   "
              f"drum {lung:.1f} cm → {lung_n:.1f} cm netezit")


if __name__ == "__main__":
    main()
