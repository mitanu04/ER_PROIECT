"""
Mediul de lucru al robotului: dimensiuni, obstacole poligonale, start și țintă.
Unitatea de măsură este centimetrul. Harta se poate salva / încărca din JSON,
același format pe care îl va folosi și frontend-ul JavaScript.
"""

import json
import math
from dataclasses import dataclass, field

from .geometrie import punct_in_poligon


@dataclass
class Harta:
    latime: float
    inaltime: float
    start: tuple
    tinta: tuple
    obstacole: list = field(default_factory=list)   # listă de poligoane

    def __post_init__(self):
        self.start = tuple(self.start)
        self.tinta = tuple(self.tinta)
        self.obstacole = [[tuple(v) for v in poligon] for poligon in self.obstacole]
        for poligon in self.obstacole:
            if len(poligon) < 3:
                raise ValueError("Un obstacol trebuie să aibă cel puțin 3 vârfuri")

    def in_limite(self, p):
        return 0 <= p[0] <= self.latime and 0 <= p[1] <= self.inaltime

    def punct_in_obstacol(self, p):
        return any(punct_in_poligon(p, poligon) for poligon in self.obstacole)

    # ---------- JSON ----------
    def to_dict(self):
        return {
            "latime": self.latime,
            "inaltime": self.inaltime,
            "start": list(self.start),
            "tinta": list(self.tinta),
            "obstacole": [[list(v) for v in poligon] for poligon in self.obstacole],
        }

    @classmethod
    def from_dict(cls, d):
        return cls(d["latime"], d["inaltime"], d["start"], d["tinta"], d.get("obstacole", []))

    def salveaza(self, cale):
        with open(cale, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def incarca(cls, cale):
        with open(cale, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


def harta_exemplu():
    """Mediu inspirat din figura „Descompunere omogenă” din temă:
    bara orizontală a lui T, piciorul lui T, obstacolul în formă de pană
    și vârful ascuțit din dreapta. Dimensiuni: 100 x 70 cm."""
    return Harta(
        latime=100,
        inaltime=70,
        start=(36, 45),
        tinta=(93, 9),
        obstacole=[
            [(20, 52), (90, 52), (90, 60), (20, 60)],          # bara T
            [(51, 28), (59, 28), (59, 52), (51, 52)],          # piciorul T
            [(14, 34), (50, 37), (49, 28), (38, 16)],          # pana
            [(72, 0), (80, 0), (76, 46)],                      # vârful
        ],
    )


def _poligon_regulat(cx, cy, raza, n):
    return [(round(cx + raza * math.cos(2 * math.pi * k / n + math.pi / n), 3),
             round(cy + raza * math.sin(2 * math.pi * k / n + math.pi / n), 3))
            for k in range(n)]


def harta_demo():
    """Hartă pentru frontend: un „apartament” de 120 x 80 cm cu trei camere
    legate prin uși, mobilier de diverse forme (dreptunghiuri, triunghi,
    octogon, un obstacol concav în formă de U) și o trecere de 6 cm spre țintă,
    care există la celule de 2 cm, dar dispare la 4 cm."""
    return Harta(
        latime=120,
        inaltime=80,
        start=(6, 8),
        tinta=(112, 70),
        obstacole=[
            # pereți: ușa din stânga la y 52-64, ușa din dreapta la y 14-26
            [(38, 0), (41, 0), (41, 52), (38, 52)],
            [(38, 64), (41, 64), (41, 80), (38, 80)],
            [(79, 0), (82, 0), (82, 14), (79, 14)],
            [(79, 26), (82, 26), (82, 80), (79, 80)],
            # camera 1: masă și scaun
            [(10, 30), (26, 30), (26, 44), (10, 44)],
            [(28, 12), (34, 16), (29, 22)],
            # camera 2: masă rotundă și un dulap în formă de U (capcană pentru Greedy)
            _poligon_regulat(60, 60, 7, 8),
            [(48, 10), (72, 10), (72, 36), (67, 36), (67, 15), (53, 15), (53, 36), (48, 36)],
            # camera 3: ghiveci, pat și două corpuri cu o trecere de 6 cm între ele
            [(90, 6), (98, 6), (94, 16)],
            [(82, 44), (100, 44), (100, 50), (82, 50)],
            [(106, 44), (120, 44), (120, 50), (106, 50)],
            [(86, 62), (100, 62), (100, 76), (86, 76)],
        ],
    )


def harta_culoar_ingust():
    """Două blocuri separate de un culoar de 3 cm. La rezoluție mare
    drumul există, la rezoluție mică culoarul „dispare” (metoda e aproximativă)."""
    return Harta(
        latime=60,
        inaltime=40,
        start=(8, 20),
        tinta=(52, 20),
        obstacole=[
            [(25, 0), (35, 0), (35, 18.5), (25, 18.5)],
            [(25, 21.5), (35, 21.5), (35, 40), (25, 40)],
        ],
    )
