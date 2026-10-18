import pytest
from pydantic import ValidationError

import service
from core import harta_culoar_ingust, harta_exemplu
from schemas import (CererePlanificare, DescompunereRaspuns, HartaModel,
                     PlanificareRaspuns)


def test_descompune_si_index_celule():
    h = harta_exemplu()
    d = service.descompune(h, latura=2.0, vecinatate=4)
    DescompunereRaspuns(**d)                       # forma răspunsului e validă
    s = d["statistici"]
    assert len(d["celule"]) == s["celule_total"] == 50 * 35
    x, y, w, hh, stare = d["celule"][0]
    assert (x, y, w, hh) == (0, 0, 2.0, 2.0)


def test_planifica_raspuns_complet():
    h = harta_exemplu()
    r = service.planifica(h, metoda="astar", latura=2.0, vecinatate=8)
    PlanificareRaspuns(**r)
    drum = r["drum"]
    assert drum["gasit"]
    assert drum["lungime_netezita"] <= drum["lungime"]
    # indicii din ordinea vizitării trimit la celule libere
    celule = r["descompunere"]["celule"]
    assert all(celule[i][4] == 0 for i in drum["ordine_vizitare"])


def test_planifica_fara_celule_si_ordine():
    h = harta_exemplu()
    r = service.planifica(h, include_celule=False, include_ordine=False, netezire=False)
    assert r["descompunere"]["celule"] is None
    assert r["drum"]["ordine_vizitare"] is None
    assert r["drum"]["puncte_netezite"] is None


def test_fara_drum_nu_e_eroare():
    r = service.planifica(harta_culoar_ingust(), latura=2.0)
    assert r["drum"]["gasit"] is False and r["drum"]["motiv"]


def test_compara():
    r = service.compara(harta_exemplu(), ["bfs", "astar"], [4, 8], latura=2.0)
    assert len(r["rezultate"]) == 4
    astar = {x["vecinatate"]: x for x in r["rezultate"] if x["metoda"] == "astar"}
    assert astar[8]["lungime"] <= astar[4]["lungime"]


def test_quadtree():
    d = service.descompune(harta_exemplu(), tip="quadtree", latura=1.0, adancime_max=7)
    DescompunereRaspuns(**d)
    assert d["tip"] == "quadtree" and d["adancime_max"] == 7
    assert len(d["celule"]) == d["statistici"]["celule_total"]
    # frunzele acoperă exact harta, fără suprapuneri
    assert sum(w * h for _, _, w, h, _ in d["celule"]) == pytest.approx(100 * 70)

    r = service.planifica(harta_exemplu(), tip="quadtree", latura=1.0, adancime_max=7)
    PlanificareRaspuns(**r)
    celule = r["descompunere"]["celule"]
    assert r["drum"]["gasit"]
    assert all(celule[i][4] == 0 for i in r["drum"]["ordine_vizitare"])


def test_quadtree_prea_multe_celule(monkeypatch):
    monkeypatch.setattr(service, "MAX_CELULE", 100)
    with pytest.raises(service.EroareCerere) as e:
        service.descompune(harta_exemplu(), tip="quadtree", latura=0.5, adancime_max=10)
    assert e.value.cod == 400


def test_compara_quadtree():
    r = service.compara(harta_exemplu(), ["astar", "dijkstra"], [8], tip="quadtree",
                         latura=1.0, adancime_max=7)
    a, d = r["rezultate"]
    assert a["lungime"] == pytest.approx(d["lungime"])
    assert a["noduri_vizitate"] <= d["noduri_vizitate"]


def test_prea_multe_celule():
    with pytest.raises(service.EroareCerere) as e:
        service.descompune(harta_exemplu(), latura=0.01)
    assert e.value.cod == 400


def test_harti(tmp_path, monkeypatch):
    monkeypatch.setattr(service, "DIRECTOR_HARTI", str(tmp_path))
    assert service.lista_harti() == []
    service.salveaza_harta("test_1", harta_exemplu())
    assert service.lista_harti() == ["test_1"]
    assert service.incarca_harta("test_1") == harta_exemplu()
    with pytest.raises(service.EroareCerere) as e:
        service.incarca_harta("lipsa")
    assert e.value.cod == 404
    with pytest.raises(service.EroareCerere):
        service.salveaza_harta("../evadare", harta_exemplu())
    with pytest.raises(service.EroareCerere) as e:
        service.salveaza_harta("exemplu", harta_exemplu())     # hărțile-exemplu sunt protejate
    assert e.value.cod == 403


def test_validare_harta():
    ok = harta_exemplu().to_dict()
    HartaModel(**ok)
    with pytest.raises(ValidationError):
        HartaModel(**{**ok, "start": [500, 10]})            # în afara hărții
    with pytest.raises(ValidationError):
        HartaModel(**{**ok, "obstacole": [[[0, 0], [1, 1]]]})  # doar 2 vârfuri
    with pytest.raises(ValidationError):
        HartaModel(**{**ok, "latime": -5})
    with pytest.raises(ValidationError):
        CererePlanificare(harta=ok, metoda="dfs")
    with pytest.raises(ValidationError):
        CererePlanificare(harta=ok, descompunere={"vecinatate": 6})
