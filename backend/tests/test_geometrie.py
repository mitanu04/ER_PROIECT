from core.geometrie import (Stare, clasifica_dreptunghi, lungime_drum, numar_viraje,
                            punct_in_poligon, segmente_se_intersecteaza)

PATRAT = [(0, 0), (10, 0), (10, 10), (0, 10)]
TRIUNGHI = [(0, 0), (10, 0), (5, 10)]


def test_punct_in_poligon():
    assert punct_in_poligon((5, 5), PATRAT)
    assert not punct_in_poligon((15, 5), PATRAT)
    assert punct_in_poligon((5, 2), TRIUNGHI)
    assert not punct_in_poligon((1, 8), TRIUNGHI)


def test_segmente():
    assert segmente_se_intersecteaza((0, 0), (10, 10), (0, 10), (10, 0))
    assert not segmente_se_intersecteaza((0, 0), (1, 1), (2, 2), (3, 0))
    assert segmente_se_intersecteaza((0, 0), (5, 0), (5, 0), (5, 5))       # atingere în capăt
    assert segmente_se_intersecteaza((0, 0), (4, 0), (2, 0), (6, 0))       # coliniare suprapuse


def test_clasificare_celule():
    assert clasifica_dreptunghi(20, 20, 22, 22, PATRAT) == Stare.LIBER
    assert clasifica_dreptunghi(2, 2, 4, 4, PATRAT) == Stare.OCUPAT
    assert clasifica_dreptunghi(9, 9, 11, 11, PATRAT) == Stare.MIXT
    # poligonul întreg în interiorul celulei
    assert clasifica_dreptunghi(-5, -5, 15, 15, PATRAT) == Stare.MIXT
    # celula doar atinge obstacolul pe margine -> conservator, MIXT
    assert clasifica_dreptunghi(10, 2, 12, 4, PATRAT) == Stare.MIXT


def test_lungime_si_viraje():
    drum = [(0, 0), (3, 0), (3, 4)]
    assert lungime_drum(drum) == 7
    assert numar_viraje(drum) == 1
    assert numar_viraje([(0, 0), (1, 0), (2, 0)]) == 0
