"""Teste HTTP pentru api.py (necesită fastapi și httpx instalate)."""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("fastapi.testclient")       # are nevoie de httpx2 (sau httpx, pe versiuni vechi)

from fastapi.testclient import TestClient  # noqa: E402

from api import app  # noqa: E402
from core import harta_exemplu  # noqa: E402

client = TestClient(app)
HARTA = harta_exemplu().to_dict()


def test_sanatate():
    r = client.get("/api/sanatate")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_planifica():
    r = client.post("/api/planifica", json={
        "harta": HARTA, "metoda": "astar",
        "descompunere": {"tip": "grila", "latura": 2, "vecinatate": 8}})
    assert r.status_code == 200
    drum = r.json()["drum"]
    assert drum["gasit"] and len(drum["puncte_netezite"]) >= 2


def test_descompune_valori_implicite():
    r = client.post("/api/descompune", json={"harta": HARTA})
    assert r.status_code == 200
    assert r.json()["latura"] == 2.0


def test_planifica_quadtree():
    r = client.post("/api/planifica", json={
        "harta": HARTA, "metoda": "astar",
        "descompunere": {"tip": "quadtree", "latura": 1, "adancime_max": 7, "vecinatate": 8}})
    assert r.status_code == 200
    j = r.json()
    assert j["descompunere"]["tip"] == "quadtree" and j["drum"]["gasit"]


def test_compara():
    r = client.post("/api/compara", json={"harta": HARTA, "metode": ["astar", "greedy"],
                                          "vecinatati": [4]})
    assert r.status_code == 200 and len(r.json()["rezultate"]) == 2


def test_erori():
    assert client.post("/api/planifica", json={"harta": HARTA, "metoda": "dfs"}).status_code == 422
    r = client.post("/api/descompune", json={"harta": HARTA, "descompunere": {"latura": 0.01}})
    assert r.status_code == 400 and "detail" in r.json()
    assert client.put("/api/harti/exemplu", json=HARTA).status_code == 403
    assert client.get("/api/harti/nu_exista").status_code == 404


def test_harti_salvate():
    r = client.get("/api/harti")
    assert "exemplu" in r.json()["harti"]
    r = client.get("/api/harti/exemplu")
    assert r.status_code == 200 and r.json()["latime"] == 100
