"""
Descompunere prin metoda arborelui (quadtree).

Dreptunghiul hărții este împărțit recursiv în 4 sferturi egale, dar numai
acolo unde e nevoie: o celulă LIBERĂ sau OCUPATĂ rămâne întreagă (frunză),
iar una MIXTĂ se împarte mai departe. Împărțirea se oprește la adâncimea
maximă sau când sferturile ar deveni mai mici decât latura minimă; frunzele
mixte rămase sunt tratate ca ocupate, ca la grila uniformă.

Rezultatul: celule mari în zonele goale și celule mici doar lângă obstacole,
deci mult mai puține noduri decât o grilă uniformă de aceeași finețe.

Implementează aceeași interfață de graf ca GrilaUniforma (vezi grila.py),
așa că algoritmii de căutare și netezirea funcționează nemodificați.
Nodurile grafului sunt indicii frunzelor.
"""

import math

from .geometrie import Stare, clasifica_dreptunghi, distanta

EPS = 1e-9
DELTA = 1e-6        # pas mic lângă un colț, pentru a afla celulele din jurul lui


class PreaMulteCelule(ValueError):
    pass


class _Nod:
    __slots__ = ("xmin", "ymin", "xmax", "ymax", "copii", "frunza")

    def __init__(self, xmin, ymin, xmax, ymax):
        self.xmin, self.ymin, self.xmax, self.ymax = xmin, ymin, xmax, ymax
        self.copii = None       # [SV, SE, NV, NE] pentru un nod interior
        self.frunza = None      # indicele frunzei, pentru o frunză


class QuadTree:
    tip = "quadtree"

    def __init__(self, harta, latura, vecinatate=4, adancime_max=6, max_frunze=None):
        if vecinatate not in (4, 8):
            raise ValueError("vecinatate trebuie să fie 4 sau 8")
        self.harta = harta
        self.latura = float(latura)         # latura minimă a unei celule
        self.vecinatate = vecinatate
        self.adancime_max = adancime_max
        self.max_frunze = max_frunze
        self.frunze = []                    # (xmin, ymin, xmax, ymax) pentru fiecare frunză
        self.stare = []                     # Stare pentru fiecare frunză
        self.adancime = []                  # adâncimea fiecărei frunze
        self.radacina = self._construieste(0.0, 0.0, float(harta.latime), float(harta.inaltime),
                                           0, harta.obstacole)
        self._vecini = {i: self._calculeaza_vecini(i)
                        for i in range(len(self.frunze)) if self.stare[i] == Stare.LIBER}

    # ------------------------------------------------------------------
    # Construirea arborelui
    # ------------------------------------------------------------------
    def _construieste(self, xmin, ymin, xmax, ymax, adancime, obstacole):
        stare = Stare.LIBER
        atinse = []             # obstacolele care ating celula: doar ele contează pentru copii
        for poligon in obstacole:
            s = clasifica_dreptunghi(xmin, ymin, xmax, ymax, poligon)
            if s == Stare.OCUPAT:
                stare = Stare.OCUPAT
                break
            if s == Stare.MIXT:
                stare = Stare.MIXT
                atinse.append(poligon)

        nod = _Nod(xmin, ymin, xmax, ymax)
        se_poate_imparti = (adancime < self.adancime_max and
                            min(xmax - xmin, ymax - ymin) / 2 >= self.latura - EPS)
        if stare == Stare.MIXT and se_poate_imparti:
            xm, ym = (xmin + xmax) / 2, (ymin + ymax) / 2
            nod.copii = [self._construieste(*d, adancime + 1, atinse)
                         for d in ((xmin, ymin, xm, ym), (xm, ymin, xmax, ym),
                                   (xmin, ym, xm, ymax), (xm, ym, xmax, ymax))]
            return nod

        nod.frunza = len(self.frunze)
        self.frunze.append((xmin, ymin, xmax, ymax))
        self.stare.append(stare)
        self.adancime.append(adancime)
        if self.max_frunze is not None and len(self.frunze) > self.max_frunze:
            raise PreaMulteCelule(f"Quadtree-ul depășește {self.max_frunze} celule. "
                                  "Mărește latura minimă sau scade adâncimea maximă.")
        return nod

    def _frunza_pentru_punct(self, p):
        if not self.harta.in_limite(p):
            return None
        nod = self.radacina
        while nod.copii:
            xm, ym = (nod.xmin + nod.xmax) / 2, (nod.ymin + nod.ymax) / 2
            nod = nod.copii[(p[0] >= xm) + 2 * (p[1] >= ym)]
        return nod.frunza

    def _frunze_care_ating(self, xmin, ymin, xmax, ymax):
        """Frunzele care au cel puțin un punct comun cu dreptunghiul (închis)."""
        rezultat = []
        stiva = [self.radacina]
        while stiva:
            nod = stiva.pop()
            if (nod.xmax < xmin - EPS or nod.xmin > xmax + EPS or
                    nod.ymax < ymin - EPS or nod.ymin > ymax + EPS):
                continue
            if nod.copii:
                stiva.extend(nod.copii)
            else:
                rezultat.append(nod.frunza)
        return rezultat

    def _calculeaza_vecini(self, i):
        """Vecinii unei frunze libere: cele cu o latură comună (4 și 8) și,
        pentru vecinătatea 8, cele care ating doar un colț, dacă diagonala
        nu taie colțul unui obstacol (celelalte două celule din jurul colțului sunt libere)."""
        axmin, aymin, axmax, aymax = self.frunze[i]
        ca = self.pozitie(i)
        rezultat = []
        for j in self._frunze_care_ating(axmin, aymin, axmax, aymax):
            if j == i or self.stare[j] != Stare.LIBER:
                continue
            bxmin, bymin, bxmax, bymax = self.frunze[j]
            suprapunere_x = min(axmax, bxmax) - max(axmin, bxmin)
            suprapunere_y = min(aymax, bymax) - max(aymin, bymin)
            if suprapunere_x > EPS or suprapunere_y > EPS:
                rezultat.append((j, distanta(ca, self.pozitie(j))))   # latură comună
            elif self.vecinatate == 8:
                # se ating doar într-un colț
                cx = axmax if abs(axmax - bxmin) < EPS else axmin
                cy = aymax if abs(aymax - bymin) < EPS else aymin
                sx = 1 if ca[0] > cx else -1
                sy = 1 if ca[1] > cy else -1
                laterale = ((cx + sx * DELTA, cy - sy * DELTA), (cx - sx * DELTA, cy + sy * DELTA))
                if all(self._este_libera(self._frunza_pentru_punct(p)) for p in laterale):
                    rezultat.append((j, distanta(ca, self.pozitie(j))))
        return rezultat

    def _este_libera(self, frunza):
        return frunza is not None and self.stare[frunza] == Stare.LIBER

    # ------------------------------------------------------------------
    # Interfața de graf
    # ------------------------------------------------------------------
    def nod_pentru_punct(self, p):
        f = self._frunza_pentru_punct(p)
        return f if self._este_libera(f) else None

    def pozitie(self, nod):
        xmin, ymin, xmax, ymax = self.frunze[nod]
        return ((xmin + xmax) / 2, (ymin + ymax) / 2)

    def vecini(self, nod):
        return self._vecini.get(nod, [])

    def euristica(self, a, b):
        # costurile sunt distanțe euclidiene între centre, deci euristica e consistentă
        return distanta(self.pozitie(a), self.pozitie(b))

    def segment_liber(self, p, q):
        """True dacă segmentul [p, q] atinge doar frunze libere."""
        stiva = [self.radacina]
        while stiva:
            nod = stiva.pop()
            if not _segment_atinge_dreptunghi(p, q, nod.xmin, nod.ymin, nod.xmax, nod.ymax):
                continue
            if nod.copii:
                stiva.extend(nod.copii)
            elif self.stare[nod.frunza] != Stare.LIBER:
                return False
        return True

    # ------------------------------------------------------------------
    # Statistici și export pentru frontend
    # ------------------------------------------------------------------
    def statistici(self):
        return {
            "celule_total": len(self.frunze),
            "celule_libere": sum(1 for s in self.stare if s == Stare.LIBER),
            "celule_ocupate": sum(1 for s in self.stare if s == Stare.OCUPAT),
            "celule_mixte": sum(1 for s in self.stare if s == Stare.MIXT),
        }

    def index(self, nod):
        return nod

    def celule_compacte(self):
        return [[xmin, ymin, xmax - xmin, ymax - ymin, int(s)]
                for (xmin, ymin, xmax, ymax), s in zip(self.frunze, self.stare)]


def _segment_atinge_dreptunghi(p, q, xmin, ymin, xmax, ymax):
    """Decupare Liang-Barsky: segmentul are vreun punct comun cu dreptunghiul închis?
    Atingerea pe margine contează (abordare conservatoare)."""
    t0, t1 = 0.0, 1.0
    for v, d, lo, hi in ((p[0], q[0] - p[0], xmin - EPS, xmax + EPS),
                         (p[1], q[1] - p[1], ymin - EPS, ymax + EPS)):
        if abs(d) < EPS:
            if v < lo or v > hi:
                return False
            continue
        ta, tb = (lo - v) / d, (hi - v) / d
        if ta > tb:
            ta, tb = tb, ta
        t0, t1 = max(t0, ta), min(t1, tb)
        if t0 > t1:
            return False
    return True
