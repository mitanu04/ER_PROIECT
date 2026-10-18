"""
Algoritmi de căutare a drumului pe graful celulelor libere.

Funcționează pe orice descompunere care implementează interfața de graf
(vezi grila.py): nod_pentru_punct, pozitie, vecini, euristica.

    BFS      - drumul cu cele mai puține celule (ignoră distanțele)
    Dijkstra - drumul cel mai scurt, explorează în toate direcțiile
    A*       - drumul cel mai scurt, ghidat spre țintă de euristică
    Greedy   - foarte rapid, dar drumul nu e garantat optim
"""

import heapq
import itertools
import time
from collections import deque
from dataclasses import dataclass, field

from .geometrie import lungime_drum, numar_viraje

METODE = ("bfs", "dijkstra", "astar", "greedy")


@dataclass
class Rezultat:
    metoda: str
    gasit: bool
    motiv: str = ""
    noduri: list = field(default_factory=list)          # celulele drumului
    puncte: list = field(default_factory=list)          # start, centrele celulelor, țintă
    cost: float = 0.0                                   # costul în graf
    noduri_vizitate: int = 0                            # noduri extinse
    ordine_vizitare: list = field(default_factory=list) # pentru animație
    timp_ms: float = 0.0

    @property
    def lungime(self):
        return lungime_drum(self.puncte) if self.puncte else 0.0

    @property
    def viraje(self):
        return numar_viraje(self.puncte) if self.puncte else 0


def _reconstruieste(parinte, tinta):
    drum = [tinta]
    while parinte[drum[-1]] is not None:
        drum.append(parinte[drum[-1]])
    drum.reverse()
    return drum


def bfs(graf, start, tinta):
    """Căutare în lățime. Returnează (drum, ordine_vizitare)."""
    parinte = {start: None}
    coada = deque([start])
    ordine = []
    while coada:
        nod = coada.popleft()
        ordine.append(nod)
        if nod == tinta:
            return _reconstruieste(parinte, tinta), ordine
        for vecin, _cost in graf.vecini(nod):
            if vecin not in parinte:
                parinte[vecin] = nod
                coada.append(vecin)
    return None, ordine


def _cautare_cu_prioritate(graf, start, tinta, prioritate):
    """
    Schelet comun pentru Dijkstra, A* și Greedy. Diferă doar prioritatea:
        Dijkstra: f = g
        A*:       f = g + h
        Greedy:   f = h
    unde g = costul de la start, h = euristica până la țintă.
    """
    contor = itertools.count()          # departajare stabilă între priorități egale
    g = {start: 0.0}
    parinte = {start: None}
    inchise = set()
    deschise = [(prioritate(0.0, graf.euristica(start, tinta)), next(contor), start)]
    ordine = []

    while deschise:
        _f, _, nod = heapq.heappop(deschise)
        if nod in inchise:
            continue                    # intrare veche din coadă, ignorată
        inchise.add(nod)
        ordine.append(nod)
        if nod == tinta:
            return _reconstruieste(parinte, tinta), ordine
        for vecin, cost in graf.vecini(nod):
            if vecin in inchise:
                continue
            g_nou = g[nod] + cost
            if g_nou < g.get(vecin, float("inf")):
                g[vecin] = g_nou
                parinte[vecin] = nod
                f = prioritate(g_nou, graf.euristica(vecin, tinta))
                heapq.heappush(deschise, (f, next(contor), vecin))
    return None, ordine


def dijkstra(graf, start, tinta):
    return _cautare_cu_prioritate(graf, start, tinta, lambda g, h: g)


def astar(graf, start, tinta):
    return _cautare_cu_prioritate(graf, start, tinta, lambda g, h: g + h)


def greedy(graf, start, tinta):
    return _cautare_cu_prioritate(graf, start, tinta, lambda g, h: h)


_ALGORITMI = {"bfs": bfs, "dijkstra": dijkstra, "astar": astar, "greedy": greedy}


def cost_drum(graf, noduri):
    """Suma costurilor muchiilor de-a lungul drumului."""
    total = 0.0
    for a, b in zip(noduri, noduri[1:]):
        total += next(c for v, c in graf.vecini(a) if v == b)
    return total


def cauta_drum(graf, start_punct, tinta_punct, metoda="astar"):
    """
    Punctul de intrare principal: găsește celulele de start și țintă,
    rulează algoritmul ales și construiește rezultatul.
    """
    if metoda not in _ALGORITMI:
        raise ValueError(f"Metodă necunoscută: {metoda}. Alege din {METODE}")

    start = graf.nod_pentru_punct(start_punct)
    tinta = graf.nod_pentru_punct(tinta_punct)
    if start is None:
        return Rezultat(metoda, False, "Startul nu se află într-o celulă liberă la această rezoluție")
    if tinta is None:
        return Rezultat(metoda, False, "Ținta nu se află într-o celulă liberă la această rezoluție")

    t0 = time.perf_counter()
    noduri, ordine = _ALGORITMI[metoda](graf, start, tinta)
    timp_ms = (time.perf_counter() - t0) * 1000

    if noduri is None:
        return Rezultat(metoda, False, "Nu există drum între celulele libere la această rezoluție",
                        noduri_vizitate=len(ordine), ordine_vizitare=ordine, timp_ms=timp_ms)

    # Drumul real: punctul exact de start, centrele celulelor intermediare, punctul exact țintă
    puncte = [tuple(start_punct)] + [graf.pozitie(n) for n in noduri[1:-1]] + [tuple(tinta_punct)]
    return Rezultat(metoda, True, "", noduri=noduri, puncte=puncte,
                    cost=cost_drum(graf, noduri), noduri_vizitate=len(ordine),
                    ordine_vizitare=ordine, timp_ms=timp_ms)
