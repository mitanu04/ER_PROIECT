"""
Descompunere omogenă (grilă uniformă).

Spațiul este împărțit în pătrate de latură egală. Fiecare celulă este
LIBERĂ, OCUPATĂ sau MIXTĂ. Celulele mixte sunt tratate ca ocupate,
ceea ce creează automat o margine de siguranță în jurul obstacolelor
(celulele galbene din figura din temă).

Clasa implementează „interfața de graf” folosită de algoritmii de căutare:
    nod_pentru_punct(p) -> nod sau None
    pozitie(nod)        -> (x, y) centrul celulei
    vecini(nod)         -> [(nod_vecin, cost), ...]
    euristica(a, b)     -> estimarea costului de la a la b
    segment_liber(p, q) -> True dacă segmentul trece doar prin celule libere
Descompunerea quadtree (quadtree.py) implementează aceeași interfață,
astfel încât algoritmii de căutare funcționează pe ambele fără modificări.
"""

import math

import numpy as np

from .geometrie import Stare, clasifica_dreptunghi, cutie_incadratoare

EPS = 1e-9


class GrilaUniforma:
    tip = "grila"

    def __init__(self, harta, latura, vecinatate=4):
        if vecinatate not in (4, 8):
            raise ValueError("vecinatate trebuie să fie 4 sau 8")
        self.harta = harta
        self.latura = float(latura)
        self.vecinatate = vecinatate
        self.nr_coloane = math.ceil(harta.latime / self.latura - EPS)
        self.nr_randuri = math.ceil(harta.inaltime / self.latura - EPS)
        # stare[rand, coloana]; randul 0 este jos (y mic)
        self.stare = np.zeros((self.nr_randuri, self.nr_coloane), dtype=np.int8)
        self._construieste()

    # ------------------------------------------------------------------
    # Construirea descompunerii
    # ------------------------------------------------------------------
    def dreptunghi(self, nod):
        r, c = nod
        L = self.latura
        return c * L, r * L, (c + 1) * L, (r + 1) * L

    def _construieste(self):
        # Fiecare obstacol e testat doar pe celulele din cutia lui încadratoare;
        # restul celulelor rămân libere față de el (mult mai rapid pe grile fine).
        for poligon in self.harta.obstacole:
            pxmin, pymin, pxmax, pymax = cutie_incadratoare(poligon)
            c0, c1 = self._interval(pxmin, pxmax, self.nr_coloane)
            r0, r1 = self._interval(pymin, pymax, self.nr_randuri)
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    if self.stare[r, c] == Stare.OCUPAT:
                        continue
                    s = clasifica_dreptunghi(*self.dreptunghi((r, c)), poligon)
                    if s != Stare.LIBER:
                        self.stare[r, c] = s
        # celulele care ies din hartă (când dimensiunea nu e multiplu de latură):
        # doar ultima coloană / ultimul rând pot depăși
        if self.nr_coloane * self.latura > self.harta.latime + EPS:
            self.stare[:, -1] = Stare.MIXT
        if self.nr_randuri * self.latura > self.harta.inaltime + EPS:
            self.stare[-1, :] = Stare.MIXT
        # copie ca listă Python: accesul element cu element e mult mai rapid decât în numpy,
        # iar este_liber() e apelată de sute de mii de ori în timpul căutării
        self._liber = (self.stare == Stare.LIBER).tolist()

    def _interval(self, vmin, vmax, n):
        """Indicii celulelor (pe o axă) care pot atinge intervalul [vmin, vmax];
        include și celulele doar atinse pe margine."""
        i0 = max(0, math.floor(vmin / self.latura - EPS) - 1)
        i1 = min(n - 1, math.floor(vmax / self.latura + EPS))
        return i0, i1

    # ------------------------------------------------------------------
    # Interfața de graf
    # ------------------------------------------------------------------
    def in_grila(self, nod):
        r, c = nod
        return 0 <= r < self.nr_randuri and 0 <= c < self.nr_coloane

    def este_liber(self, nod):
        r, c = nod
        return 0 <= r < self.nr_randuri and 0 <= c < self.nr_coloane and self._liber[r][c]

    def nod_pentru_punct(self, p):
        """Celula care conține punctul p, sau None dacă e în afara hărții
        sau într-o celulă care nu e liberă."""
        if not self.harta.in_limite(p):
            return None
        c = min(int(p[0] // self.latura), self.nr_coloane - 1)
        r = min(int(p[1] // self.latura), self.nr_randuri - 1)
        return (r, c) if self.este_liber((r, c)) else None

    def pozitie(self, nod):
        r, c = nod
        return ((c + 0.5) * self.latura, (r + 0.5) * self.latura)

    def vecini(self, nod):
        r, c = nod
        L = self.latura
        rezultat = []
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            v = (r + dr, c + dc)
            if self.este_liber(v):
                rezultat.append((v, L))
        if self.vecinatate == 8:
            for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                v = (r + dr, c + dc)
                # diagonala e permisă doar dacă nu „taie colțul” unui obstacol:
                # ambele celule laterale trebuie să fie libere
                if (self.este_liber(v) and self.este_liber((r + dr, c))
                        and self.este_liber((r, c + dc))):
                    rezultat.append((v, L * math.sqrt(2)))
        return rezultat

    def euristica(self, a, b):
        dr = abs(a[0] - b[0])
        dc = abs(a[1] - b[1])
        if self.vecinatate == 4:
            return self.latura * (dr + dc)                                  # Manhattan
        return self.latura * (max(dr, dc) + (math.sqrt(2) - 1) * min(dr, dc))  # octilă

    def celule_traversate(self, p, q):
        """Toate celulele atinse de segmentul [p, q] (acoperire conservatoare:
        și celulele doar atinse pe margine sunt incluse)."""
        L = self.latura
        x0, y0 = p[0] / L, p[1] / L
        x1, y1 = q[0] / L, q[1] / L
        if x0 > x1:
            x0, y0, x1, y1 = x1, y1, x0, y0
        celule = set()
        c_start = math.floor(x0 - EPS)
        c_stop = math.floor(x1 + EPS)
        for c in range(c_start, c_stop + 1):
            xa = max(x0, c)
            xb = min(x1, c + 1)
            if xb < xa:
                continue
            if abs(x1 - x0) < EPS:
                ya, yb = y0, y1
            else:
                panta = (y1 - y0) / (x1 - x0)
                ya = y0 + panta * (xa - x0)
                yb = y0 + panta * (xb - x0)
            r_min = math.floor(min(ya, yb) - EPS)
            r_max = math.floor(max(ya, yb) + EPS)
            for r in range(r_min, r_max + 1):
                celule.add((r, c))
        return celule

    def segment_liber(self, p, q):
        return all(self.este_liber(n) for n in self.celule_traversate(p, q))

    # ------------------------------------------------------------------
    # Statistici
    # ------------------------------------------------------------------
    def statistici(self):
        return {
            "celule_total": int(self.stare.size),
            "celule_libere": int(np.sum(self.stare == Stare.LIBER)),
            "celule_ocupate": int(np.sum(self.stare == Stare.OCUPAT)),
            "celule_mixte": int(np.sum(self.stare == Stare.MIXT)),
        }

    # ------------------------------------------------------------------
    # Export pentru frontend
    # ------------------------------------------------------------------
    def index(self, nod):
        """Poziția celulei în lista din celule_compacte() (ordine pe rânduri)."""
        r, c = nod
        return r * self.nr_coloane + c

    def celule_compacte(self):
        """Toate celulele ca [x, y, latime, inaltime, stare], în ordinea dată de index()."""
        L = self.latura
        return [[c * L, r * L, L, L, int(self.stare[r, c])]
                for r in range(self.nr_randuri) for c in range(self.nr_coloane)]
