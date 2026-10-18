"""
Modelele de date ale API-ului (pydantic). Ele validează automat JSON-ul
primit de la frontend și apar documentate în pagina /docs.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from core.harta import Harta

Punct = tuple[float, float]
Metoda = Literal["bfs", "dijkstra", "astar", "greedy"]
TipDescompunere = Literal["grila", "quadtree"]


# ----------------------------------------------------------------------
# Cereri
# ----------------------------------------------------------------------
class HartaModel(BaseModel):
    latime: float = Field(gt=0, le=10_000, description="Lățimea mediului, în cm")
    inaltime: float = Field(gt=0, le=10_000, description="Înălțimea mediului, în cm")
    start: Punct
    tinta: Punct
    obstacole: list[list[Punct]] = Field(default_factory=list, max_length=200,
                                         description="Poligoane, fiecare ca listă de vârfuri")

    @field_validator("obstacole")
    @classmethod
    def verifica_poligoane(cls, obstacole):
        for i, poligon in enumerate(obstacole):
            if not 3 <= len(poligon) <= 100:
                raise ValueError(f"Obstacolul {i} trebuie să aibă între 3 și 100 de vârfuri")
        return obstacole

    @model_validator(mode="after")
    def verifica_capete(self):
        for nume, (x, y) in (("start", self.start), ("tinta", self.tinta)):
            if not (0 <= x <= self.latime and 0 <= y <= self.inaltime):
                raise ValueError(f"Punctul de {nume} este în afara hărții")
        return self

    def to_harta(self) -> Harta:
        return Harta(self.latime, self.inaltime, self.start, self.tinta, self.obstacole)

    @classmethod
    def din_harta(cls, h: Harta) -> "HartaModel":
        return cls(**h.to_dict())


class ParametriDescompunere(BaseModel):
    tip: TipDescompunere = "grila"
    latura: float = Field(2.0, gt=0, description="Latura celulei (grilă) sau "
                                                  "latura minimă (quadtree), în cm")
    vecinatate: Literal[4, 8] = 4
    adancime_max: int = Field(6, ge=1, le=12, description="Doar pentru quadtree")


class CerereDescompunere(BaseModel):
    harta: HartaModel
    descompunere: ParametriDescompunere = ParametriDescompunere()


class CererePlanificare(CerereDescompunere):
    metoda: Metoda = "astar"
    netezire: bool = True
    include_celule: bool = Field(True, description="Trimite celulele pentru desenare")
    include_ordine: bool = Field(True, description="Trimite ordinea vizitării (animație)")


class CerereComparatie(CerereDescompunere):
    metode: list[Metoda] = ["bfs", "dijkstra", "astar", "greedy"]
    vecinatati: list[Literal[4, 8]] = [4, 8]


# ----------------------------------------------------------------------
# Răspunsuri
# ----------------------------------------------------------------------
class Statistici(BaseModel):
    celule_total: int
    celule_libere: int
    celule_ocupate: int
    celule_mixte: int


class DescompunereRaspuns(BaseModel):
    tip: TipDescompunere
    latura: float
    vecinatate: int
    adancime_max: Optional[int] = Field(None, description="Doar pentru quadtree")
    statistici: Statistici
    timp_ms: float
    celule: Optional[list[tuple[float, float, float, float, int]]] = Field(
        None, description="[x, y, lățime, înălțime, stare]; stare: 0 liberă, 1 ocupată, 2 mixtă")


class DrumRaspuns(BaseModel):
    metoda: Metoda
    gasit: bool
    motiv: str = ""
    puncte: list[Punct] = []
    cost: float = 0
    lungime: float = 0
    viraje: int = 0
    noduri_vizitate: int = 0
    timp_ms: float = 0
    puncte_netezite: Optional[list[Punct]] = None
    lungime_netezita: Optional[float] = None
    viraje_netezite: Optional[int] = None
    ordine_vizitare: Optional[list[int]] = Field(
        None, description="Indicii celulelor vizitate, în ordine (indici în lista 'celule')")


class PlanificareRaspuns(BaseModel):
    descompunere: DescompunereRaspuns
    drum: DrumRaspuns


class RandComparatie(BaseModel):
    vecinatate: int
    metoda: Metoda
    gasit: bool
    lungime: float
    lungime_netezita: Optional[float]
    viraje: int
    viraje_netezite: Optional[int]
    noduri_vizitate: int
    timp_ms: float


class ComparatieRaspuns(BaseModel):
    tip: TipDescompunere
    latura: float
    statistici: Statistici
    rezultate: list[RandComparatie]
