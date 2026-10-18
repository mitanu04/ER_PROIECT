"""
Desenarea hărții, a descompunerii și a drumurilor cu matplotlib
(figurile statice pentru raport).
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon, Rectangle

from core.geometrie import Stare

CULORI_STARE = {
    Stare.LIBER: "#FFFFFF",
    Stare.OCUPAT: "#BCD4EE",
    Stare.MIXT: "#FFF1A8",       # galben, ca în figura din temă
}
CULOARE_OBSTACOL = "#2F6FB5"
CULOARE_VIZITAT = "#C9BEF0"
CULOARE_DRUM = "#1A1A1A"
CULOARE_NETEZIT = "#E8590C"
CULOARE_START = "#1F4FD8"
CULOARE_TINTA = "#D62828"


def deseneaza_grila(ax, grila, linii=True):
    cmap = ListedColormap([CULORI_STARE[Stare.LIBER], CULORI_STARE[Stare.OCUPAT],
                           CULORI_STARE[Stare.MIXT]])
    L = grila.latura
    extent = (0, grila.nr_coloane * L, 0, grila.nr_randuri * L)
    ax.imshow(grila.stare, cmap=cmap, vmin=0, vmax=2, origin="lower",
              extent=extent, interpolation="nearest", zorder=0)
    if linii:
        for c in range(grila.nr_coloane + 1):
            ax.axvline(c * L, color="#B5B5B5", lw=0.35, zorder=1)
        for r in range(grila.nr_randuri + 1):
            ax.axhline(r * L, color="#B5B5B5", lw=0.35, zorder=1)


def deseneaza_celule(ax, graf, vizitate=()):
    """Desen generic, după celule_compacte(): merge pentru grilă și pentru quadtree."""
    celule = graf.celule_compacte()
    vizitate = {graf.index(n) for n in vizitate}
    dreptunghiuri, culori = [], []
    for i, (x, y, w, h, stare) in enumerate(celule):
        dreptunghiuri.append(Rectangle((x, y), w, h))
        culori.append(CULOARE_VIZITAT if i in vizitate else CULORI_STARE[Stare(stare)])
    ax.add_collection(PatchCollection(dreptunghiuri, facecolor=culori, edgecolor="#B5B5B5",
                                      linewidth=0.35, zorder=0))


def deseneaza_vizitate(ax, grila, ordine):
    masca = np.zeros_like(grila.stare, dtype=float)
    for nod in ordine:
        masca[nod] = 1.0
    culoare = np.zeros((*masca.shape, 4))
    rgb = matplotlib.colors.to_rgb(CULOARE_VIZITAT)
    culoare[..., 0], culoare[..., 1], culoare[..., 2] = rgb
    culoare[..., 3] = masca * 0.75
    L = grila.latura
    ax.imshow(culoare, origin="lower", interpolation="nearest", zorder=2,
              extent=(0, grila.nr_coloane * L, 0, grila.nr_randuri * L))


def deseneaza_obstacole(ax, harta):
    for poligon in harta.obstacole:
        ax.add_patch(Polygon(poligon, closed=True, facecolor=CULOARE_OBSTACOL,
                             edgecolor="#1B4A80", lw=1, alpha=0.9, zorder=3))
    ax.add_patch(Polygon([(0, 0), (harta.latime, 0), (harta.latime, harta.inaltime),
                          (0, harta.inaltime)], closed=True, fill=False,
                         edgecolor=CULOARE_OBSTACOL, lw=3, zorder=3))


def deseneaza_drum(ax, puncte, culoare=CULOARE_DRUM, stil="-", lw=2, eticheta=None):
    if not puncte:
        return
    xs, ys = zip(*puncte)
    ax.plot(xs, ys, stil, color=culoare, lw=lw, zorder=4, label=eticheta,
            solid_capstyle="round")


def deseneaza_capete(ax, harta):
    ax.plot(*harta.start, "o", color=CULOARE_START, ms=9, mec="white", mew=1.5, zorder=5)
    ax.plot(*harta.tinta, "o", color=CULOARE_TINTA, ms=9, mec="white", mew=1.5, zorder=5)


def pregateste_axe(ax, harta, titlu=""):
    ax.set_xlim(-1, harta.latime + 1)
    ax.set_ylim(-1, harta.inaltime + 1)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    if titlu:
        ax.set_title(titlu, fontsize=10, loc="left")
