from core import GrilaUniforma, Harta, Stare, harta_exemplu


def harta_simpla():
    # perete vertical la x in [4, 6], de la y = 0 la y = 8, pe o hartă 10 x 10
    return Harta(10, 10, (1, 1), (9, 1), [[(4, 0), (6, 0), (6, 8), (4, 8)]])


def test_dimensiuni():
    g = GrilaUniforma(harta_simpla(), 1)
    assert (g.nr_randuri, g.nr_coloane) == (10, 10)
    g = GrilaUniforma(harta_simpla(), 3)        # 10 / 3 -> 4 celule, ultima iese din hartă
    assert (g.nr_randuri, g.nr_coloane) == (4, 4)
    assert g.stare[3, 0] == Stare.MIXT


def test_stari_celule():
    g = GrilaUniforma(harta_simpla(), 1)
    assert g.stare[2, 4] == Stare.MIXT or g.stare[2, 4] == Stare.OCUPAT
    assert g.stare[9, 5] == Stare.LIBER         # deasupra peretelui
    assert g.stare[2, 1] == Stare.LIBER


def test_nod_pentru_punct():
    g = GrilaUniforma(harta_simpla(), 1)
    assert g.nod_pentru_punct((1.5, 2.5)) == (2, 1)
    assert g.nod_pentru_punct((5, 2)) is None          # în obstacol
    assert g.nod_pentru_punct((-1, 2)) is None         # în afara hărții
    assert g.nod_pentru_punct((10, 10)) == (9, 9)      # colțul hărții


def test_diagonala_nu_taie_coltul():
    h = Harta(4, 4, (0.5, 0.5), (3.5, 3.5), [[(1.2, 0.2), (1.8, 0.2), (1.8, 0.8), (1.2, 0.8)]])
    g = GrilaUniforma(h, 1, vecinatate=8)
    vecini = [n for n, _ in g.vecini((0, 0))]
    assert (1, 1) not in vecini       # celula (0,1) e blocată, diagonala ar tăia colțul
    assert (1, 0) in vecini


def test_segment_liber():
    g = GrilaUniforma(harta_simpla(), 1)
    assert g.segment_liber((1, 1), (1, 9))
    assert not g.segment_liber((1, 1), (9, 1))         # traversează peretele
    assert g.segment_liber((1, 9.5), (9, 9.5))         # pe deasupra


def test_harta_exemplu_se_construieste():
    g = GrilaUniforma(harta_exemplu(), 2)
    s = g.statistici()
    assert s["celule_total"] == s["celule_libere"] + s["celule_ocupate"] + s["celule_mixte"]
    assert s["celule_ocupate"] > 0 and s["celule_mixte"] > 0
