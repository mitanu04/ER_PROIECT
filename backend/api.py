"""
Serverul web (FastAPI). Pornire, din folderul backend:

    uvicorn api:app --reload
sau
    python api.py

Apoi deschide http://127.0.0.1:8000/docs pentru documentația interactivă,
unde poți trimite cereri direct din browser.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

import service
from schemas import (CerereComparatie, CerereDescompunere, CererePlanificare,
                     ComparatieRaspuns, DescompunereRaspuns, HartaModel,
                     PlanificareRaspuns)

VERSIUNE = "0.3.0"
DIRECTOR_FRONTEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")

app = FastAPI(
    title="Planificarea drumului prin descompunere celulară aproximativă",
    description="Descompunere omogenă / quadtree și algoritmi de căutare (BFS, Dijkstra, A*, Greedy).",
    version=VERSIUNE,
)

# Permite frontend-ului să apeleze API-ul și când e servit de pe alt port
# (de ex. Vite pe 5173 sau Live Server pe 5500). Pentru un proiect local e suficient.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(service.EroareCerere)
def trateaza_eroare(_request, exc: service.EroareCerere):
    return JSONResponse(status_code=exc.cod, content={"detail": str(exc)})


# ----------------------------------------------------------------------
# Informații
# ----------------------------------------------------------------------
@app.get("/api/sanatate", tags=["info"])
def sanatate():
    return {"status": "ok", "versiune": VERSIUNE}


@app.get("/api/metode", tags=["info"])
def metode():
    return {
        "descompuneri": [{"id": "grila", "nume": "Descompunere omogenă", "disponibil": True},
                         {"id": "quadtree", "nume": "Metoda arborelui", "disponibil": True}],
        "algoritmi": [{"id": "bfs", "nume": "BFS"}, {"id": "dijkstra", "nume": "Dijkstra"},
                      {"id": "astar", "nume": "A*"}, {"id": "greedy", "nume": "Greedy"}],
        "vecinatati": [4, 8],
        "stari_celule": {"0": "liberă", "1": "ocupată", "2": "mixtă"},
    }


# ----------------------------------------------------------------------
# Planificare
# ----------------------------------------------------------------------
@app.post("/api/descompune", response_model=DescompunereRaspuns, tags=["planificare"])
def descompune(cerere: CerereDescompunere):
    """Doar descompunerea (fără căutare), de ex. pentru afișare în timp ce muți obstacolele."""
    return service.descompune(cerere.harta.to_harta(), **cerere.descompunere.model_dump())


@app.post("/api/planifica", response_model=PlanificareRaspuns, tags=["planificare"])
def planifica(cerere: CererePlanificare):
    """Descompunere + căutarea drumului + (opțional) netezire.
    Dacă nu există drum, răspunsul are `drum.gasit = false` și motivul în `drum.motiv`."""
    return service.planifica(
        cerere.harta.to_harta(), metoda=cerere.metoda, netezire=cerere.netezire,
        include_celule=cerere.include_celule, include_ordine=cerere.include_ordine,
        **cerere.descompunere.model_dump())


@app.post("/api/compara", response_model=ComparatieRaspuns, tags=["planificare"])
def compara(cerere: CerereComparatie):
    """Rulează mai mulți algoritmi pe aceeași hartă, pentru tabelul comparativ."""
    parametri = cerere.descompunere.model_dump(exclude={"vecinatate"})
    return service.compara(cerere.harta.to_harta(), cerere.metode, cerere.vecinatati,
                            **parametri)


# ----------------------------------------------------------------------
# Hărți salvate
# ----------------------------------------------------------------------
@app.get("/api/harti", tags=["harti"])
def lista_harti():
    return {"harti": service.lista_harti()}


@app.get("/api/harti/{nume}", response_model=HartaModel, tags=["harti"])
def incarca_harta(nume: str):
    return HartaModel.din_harta(service.incarca_harta(nume))


@app.put("/api/harti/{nume}", tags=["harti"])
def salveaza_harta(nume: str, harta: HartaModel):
    service.salveaza_harta(nume, harta.to_harta())
    return {"salvat": nume}


# ----------------------------------------------------------------------
# Frontend: dacă există folderul frontend, e servit direct de la http://127.0.0.1:8000/
# ----------------------------------------------------------------------
class _FaraCache(StaticFiles):
    """Browserul verifică la fiecare încărcare dacă fișierele s-au schimbat
    (altfel poate folosi o versiune veche a JS-ului după o modificare)."""

    async def get_response(self, path, scope):
        raspuns = await super().get_response(path, scope)
        raspuns.headers["Cache-Control"] = "no-cache"
        return raspuns


if os.path.isdir(DIRECTOR_FRONTEND):
    app.mount("/", _FaraCache(directory=DIRECTOR_FRONTEND, html=True), name="frontend")
else:
    @app.get("/", include_in_schema=False)
    def radacina():
        return RedirectResponse("/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
