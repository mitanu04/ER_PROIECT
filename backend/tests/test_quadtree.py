import pytest

from core import (METODE, GrilaUniforma, Harta, QuadTree, Stare, cauta_drum, harta_culoar_ingust,
                  harta_demo, harta_exemplu, netezeste)
from core.geometrie import lungime_drum, segment_intersecteaza_poligon
from core.quadtree import PreaMulteCelule
from tests.test_cautare import harta_aleatoare


def harta_simpla():
    # perete vertical la x in [4, 6], de la y = 0 la y = 8, pe o hartă 16 x 16
    return Harta(16, 16, (1, 1), (15, 1), [[(4, 0), (6, 0), (6, 8), (4, 8)]])


def test_harta_goala_e_o_singura_celula():
    q = QuadTree(Harta(16, 16, (1, 1), (15, 15)), 1)
    assert len(q.frunze) == 1 and q.stare == [Stare.LIBER]
    rez = cauta_drum(q, (1, 1), (15, 15))
    assert rez.gasit and rez.puncte == [(1, 1), (15, 15)]


def test_frunzele_acopera_harta():
    h = harta_exemplu()
    q = QuadTree(h, 1, adancime_max=7)
    assert sum(w * hh for _, _, w, hh, _ in q.celule_compacte()) == pytest.approx(h.latime * h.inaltime)
    s = q.statistici()
    assert s["celule_total"] == s["celule_libere"] + s["celule_ocupate"] + s["celule_mixte"]


def test_mai_putine_celule_decat_grila():
    h = harta_exemplu()
    q = QuadTree(h, 1, adancime_max=7)
    g = GrilaUniforma(h, 1)
    assert len(q.frunze) < g.stare.size / 4


def test_latura_minima_si_adancimea():
    h = harta_exemplu()
    q = QuadTree(h, 2, adancime_max=12)
    assert min(min(x1 - x0, y1 - y0) for x0, y0, x1, y1 in q.frunze) >= 2 - 1e-9
    q = QuadTree(h, 0.1, adancime_max=4)
    assert max(q.adancime) <= 4


def test_celulele_libere_nu_ating_obstacole():
    h = harta_exemplu()
    q = QuadTree(h, 1, adancime_max=7)
    for (x0, y0, x1, y1), s in zip(q.frunze, q.stare):
        if s == Stare.LIBER:
            for ob in h.obstacole:
                assert not any(x0 <= x <= x1 and y0 <= y <= y1 for x, y in ob)


def test_nod_pentru_punct():
    q = QuadTree(harta_simpla(), 1)
    assert q.nod_pentru_punct((5, 2)) is None           # în obstacol
    assert q.nod_pentru_punct((-1, 2)) is None          # în afara hărții
    assert q.nod_pentru_punct((16, 16)) is not None     # colțul hărții
    n = q.nod_pentru_punct((12, 12))
    x0, y0, x1, y1 = q.frunze[n]
    assert x0 <= 12 <= x1 and y0 <= 12 <= y1


def test_vecinii_sunt_simetrici():
    for v in (4, 8):
        q = QuadTree(harta_exemplu(), 1, vecinatate=v, adancime_max=7)
        for a in q._vecini:
            for b, cost in q.vecini(a):
                assert (a, pytest.approx(cost)) in [(n, c) for n, c in q.vecini(b)]


def test_diagonala_nu_taie_coltul():
    # obstacol mic în celula din dreapta-jos a pătratului [0,2] x [0,2]
    h = Harta(4, 4, (0.5, 0.5), (3.5, 3.5), [[(1.2, 0.2), (1.8, 0.2), (1.8, 0.8), (1.2, 0.8)]])
    q = QuadTree(h, 1, vecinatate=8)
    a = q.nod_pentru_punct((0.5, 0.5))
    b = q.nod_pentru_punct((1.5, 1.5))
    assert b not in [n for n, _ in q.vecini(a)]
    assert q.nod_pentru_punct((0.5, 1.5)) in [n for n, _ in q.vecini(a)]


def test_segment_liber():
    q = QuadTree(harta_simpla(), 1)
    assert q.segment_liber((1, 1), (1, 15))
    assert not q.segment_liber((1, 1), (15, 1))         # traversează peretele
    assert q.segment_liber((1, 12), (15, 12))           # pe deasupra


@pytest.mark.parametrize("metoda", METODE)
@pytest.mark.parametrize("vecinatate", [4, 8])
def test_toate_metodele_gasesc_drum(metoda, vecinatate):
    h = harta_demo()
    q = QuadTree(h, 1, vecinatate, adancime_max=7)
    rez = cauta_drum(q, h.start, h.tinta, metoda)
    assert rez.gasit
    assert rez.puncte[0] == h.start and rez.puncte[-1] == h.tinta
    netezit = netezeste(q, rez.puncte)
    assert lungime_drum(netezit) <= rez.lungime + 1e-9
    for p, r in zip(netezit, netezit[1:]):
        assert not any(segment_intersecteaza_poligon(p, r, ob) for ob in h.obstacole)


@pytest.mark.parametrize("vecinatate", [4, 8])
@pytest.mark.parametrize("seed", range(8))
def test_astar_optim_ca_dijkstra(seed, vecinatate):
    h = harta_aleatoare(seed)
    q = QuadTree(h, 1, vecinatate, adancime_max=7)
    a = cauta_drum(q, h.start, h.tinta, "astar")
    d = cauta_drum(q, h.start, h.tinta, "dijkstra")
    assert a.gasit == d.gasit
    if a.gasit:
        assert a.cost == pytest.approx(d.cost)
        assert a.noduri_vizitate <= d.noduri_vizitate


def test_culoar_ingust_depinde_de_rezolutie():
    h = harta_culoar_ingust()
    assert cauta_drum(QuadTree(h, 1, adancime_max=8), h.start, h.tinta).gasit
    assert not cauta_drum(QuadTree(h, 2, adancime_max=8), h.start, h.tinta).gasit


def test_limita_de_celule():
    with pytest.raises(PreaMulteCelule):
        QuadTree(harta_exemplu(), 0.1, adancime_max=12, max_frunze=500)
