import random

import pytest

from core import (METODE, GrilaUniforma, Harta, cauta_drum, harta_culoar_ingust,
                  harta_exemplu, netezeste)
from core.geometrie import lungime_drum, segment_intersecteaza_poligon


def harta_aleatoare(seed):
    rnd = random.Random(seed)
    obstacole = []
    for _ in range(6):
        x, y = rnd.uniform(10, 80), rnd.uniform(10, 50)
        w, h = rnd.uniform(4, 15), rnd.uniform(4, 15)
        obstacole.append([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
    return Harta(100, 70, (3, 3), (97, 67), obstacole)


@pytest.mark.parametrize("metoda", METODE)
def test_toate_metodele_gasesc_drum(metoda):
    h = harta_exemplu()
    rez = cauta_drum(GrilaUniforma(h, 2), h.start, h.tinta, metoda)
    assert rez.gasit
    assert rez.puncte[0] == h.start and rez.puncte[-1] == h.tinta


@pytest.mark.parametrize("vecinatate", [4, 8])
@pytest.mark.parametrize("seed", range(8))
def test_astar_optim_ca_dijkstra(seed, vecinatate):
    h = harta_aleatoare(seed)
    g = GrilaUniforma(h, 2, vecinatate)
    a = cauta_drum(g, h.start, h.tinta, "astar")
    d = cauta_drum(g, h.start, h.tinta, "dijkstra")
    assert a.gasit == d.gasit
    if a.gasit:
        assert a.cost == pytest.approx(d.cost)
        assert a.noduri_vizitate <= d.noduri_vizitate


@pytest.mark.parametrize("seed", range(8))
def test_bfs_optim_pe_grila_4(seed):
    """Pe grila cu 4 vecini toți pașii costă la fel, deci BFS e optim."""
    h = harta_aleatoare(seed)
    g = GrilaUniforma(h, 2, 4)
    b = cauta_drum(g, h.start, h.tinta, "bfs")
    a = cauta_drum(g, h.start, h.tinta, "astar")
    if a.gasit:
        assert b.cost == pytest.approx(a.cost)


@pytest.mark.parametrize("seed", range(8))
def test_greedy_nu_e_mai_bun_decat_astar(seed):
    h = harta_aleatoare(seed)
    g = GrilaUniforma(h, 2, 8)
    a = cauta_drum(g, h.start, h.tinta, "astar")
    gr = cauta_drum(g, h.start, h.tinta, "greedy")
    if a.gasit:
        assert gr.cost >= a.cost - 1e-9


def test_drumul_trece_doar_prin_celule_libere():
    h = harta_exemplu()
    g = GrilaUniforma(h, 2, 8)
    rez = cauta_drum(g, h.start, h.tinta, "astar")
    for a, b in zip(rez.noduri, rez.noduri[1:]):
        assert g.este_liber(a) and g.este_liber(b)
        assert max(abs(a[0] - b[0]), abs(a[1] - b[1])) == 1


@pytest.mark.parametrize("metoda", METODE)
def test_netezirea_e_sigura_si_mai_scurta(metoda):
    h = harta_exemplu()
    g = GrilaUniforma(h, 2, 4)
    rez = cauta_drum(g, h.start, h.tinta, metoda)
    netezit = netezeste(g, rez.puncte)
    assert netezit[0] == h.start and netezit[-1] == h.tinta
    assert lungime_drum(netezit) <= rez.lungime + 1e-9
    for p, q in zip(netezit, netezit[1:]):
        assert g.segment_liber(p, q)
        assert not any(segment_intersecteaza_poligon(p, q, ob) for ob in h.obstacole)


def test_culoar_ingust_depinde_de_rezolutie():
    h = harta_culoar_ingust()
    assert cauta_drum(GrilaUniforma(h, 1), h.start, h.tinta).gasit
    rez = cauta_drum(GrilaUniforma(h, 2), h.start, h.tinta)
    assert not rez.gasit and "Nu există drum" in rez.motiv


def test_start_in_obstacol():
    h = harta_exemplu()
    rez = cauta_drum(GrilaUniforma(h, 2), (55, 40), h.tinta)
    assert not rez.gasit and "Startul" in rez.motiv


def test_metoda_necunoscuta():
    h = harta_exemplu()
    with pytest.raises(ValueError):
        cauta_drum(GrilaUniforma(h, 2), h.start, h.tinta, "dfs")


def test_json_dus_intors(tmp_path):
    h = harta_exemplu()
    cale = tmp_path / "h.json"
    h.salveaza(cale)
    assert Harta.incarca(cale) == h
