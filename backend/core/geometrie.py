"""
Funcții geometrice de bază, fără librării externe.

Toate coordonatele sunt în cm, cu originea în colțul stânga-jos al hărții
(axa y în sus). Un poligon este o listă de vârfuri [(x, y), ...].
"""

from enum import IntEnum

EPS = 1e-9


class Stare(IntEnum):
    """Starea unei celule față de obstacole."""
    LIBER = 0    # nu atinge niciun obstacol
    OCUPAT = 1   # complet în interiorul unui obstacol
    MIXT = 2     # parțial liberă, parțial ocupată (tratată ca ocupată)


def punct_in_poligon(p, poligon):
    """Testul razei (ray casting): numără de câte ori o rază orizontală
    spre dreapta din p traversează laturile poligonului. Impar = interior."""
    x, y = p
    interior = False
    n = len(poligon)
    for i in range(n):
        x1, y1 = poligon[i]
        x2, y2 = poligon[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            x_intersectie = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < x_intersectie:
                interior = not interior
    return interior


def _orientare(a, b, c):
    """>0 dacă a->b->c e în sens trigonometric, <0 orar, 0 coliniare."""
    val = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    if abs(val) < EPS:
        return 0
    return 1 if val > 0 else -1


def _pe_segment(a, b, p):
    """p (coliniar cu a, b) se află între a și b?"""
    return (min(a[0], b[0]) - EPS <= p[0] <= max(a[0], b[0]) + EPS and
            min(a[1], b[1]) - EPS <= p[1] <= max(a[1], b[1]) + EPS)


def segmente_se_intersecteaza(p1, p2, q1, q2):
    """Adevărat dacă segmentele [p1,p2] și [q1,q2] au cel puțin un punct comun
    (inclusiv atingere în capete sau suprapunere coliniară)."""
    o1 = _orientare(p1, p2, q1)
    o2 = _orientare(p1, p2, q2)
    o3 = _orientare(q1, q2, p1)
    o4 = _orientare(q1, q2, p2)

    if o1 != o2 and o3 != o4:
        return True
    if o1 == 0 and _pe_segment(p1, p2, q1):
        return True
    if o2 == 0 and _pe_segment(p1, p2, q2):
        return True
    if o3 == 0 and _pe_segment(q1, q2, p1):
        return True
    if o4 == 0 and _pe_segment(q1, q2, p2):
        return True
    return False


def laturi(poligon):
    """Lista laturilor poligonului ca perechi de puncte."""
    n = len(poligon)
    return [(poligon[i], poligon[(i + 1) % n]) for i in range(n)]


def cutie_incadratoare(poligon):
    xs = [p[0] for p in poligon]
    ys = [p[1] for p in poligon]
    return min(xs), min(ys), max(xs), max(ys)


def clasifica_dreptunghi(xmin, ymin, xmax, ymax, poligon):
    """
    Clasifică dreptunghiul (celula) față de un poligon:
      - LIBER:  nu au niciun punct comun
      - OCUPAT: dreptunghiul este complet în interiorul poligonului
      - MIXT:   se suprapun parțial

    Atingerea la margine contează ca MIXT (abordare conservatoare:
    robotul nu are voie să „atingă” obstacolul).
    """
    pxmin, pymin, pxmax, pymax = cutie_incadratoare(poligon)
    # 1. Test rapid: cutiile încadratoare nu se ating
    if pxmax < xmin - EPS or pxmin > xmax + EPS or pymax < ymin - EPS or pymin > ymax + EPS:
        return Stare.LIBER

    colturi = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]

    # 2. O latură a poligonului taie sau atinge o latură a celulei
    for a, b in laturi(poligon):
        for c, d in laturi(colturi):
            if segmente_se_intersecteaza(a, b, c, d):
                return Stare.MIXT

    # 3. Poligonul este în întregime în interiorul celulei
    x0, y0 = poligon[0]
    if xmin < x0 < xmax and ymin < y0 < ymax:
        return Stare.MIXT

    # 4. Fără intersecții de laturi: celula e fie complet în interior, fie complet în afară
    centru = ((xmin + xmax) / 2, (ymin + ymax) / 2)
    return Stare.OCUPAT if punct_in_poligon(centru, poligon) else Stare.LIBER


def segment_intersecteaza_poligon(p, q, poligon):
    """Segmentul [p,q] are vreun punct comun cu poligonul (laturi sau interior)?"""
    for a, b in laturi(poligon):
        if segmente_se_intersecteaza(p, q, a, b):
            return True
    # segmentul poate fi complet în interior
    return punct_in_poligon(p, poligon)


def distanta(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def lungime_drum(puncte):
    return sum(distanta(puncte[i], puncte[i + 1]) for i in range(len(puncte) - 1))


def numar_viraje(puncte, prag_grade=1.0):
    """Numărul de schimbări de direcție mai mari decât pragul (în grade)."""
    import math
    viraje = 0
    for i in range(1, len(puncte) - 1):
        a, b, c = puncte[i - 1], puncte[i], puncte[i + 1]
        u = (b[0] - a[0], b[1] - a[1])
        v = (c[0] - b[0], c[1] - b[1])
        nu, nv = math.hypot(*u), math.hypot(*v)
        if nu < EPS or nv < EPS:
            continue
        cos_unghi = max(-1.0, min(1.0, (u[0] * v[0] + u[1] * v[1]) / (nu * nv)))
        if math.degrees(math.acos(cos_unghi)) > prag_grade:
            viraje += 1
    return viraje
