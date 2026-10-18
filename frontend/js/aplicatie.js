// Logica aplicației: cererea drumului, comparația, încărcarea / salvarea
// hărților și modificările hărții. Leagă serverul (api.js) de desen și de panou.

import * as api from "./api.js";
import { opresteAnimatia } from "./animatie.js";
import { limiteaza } from "./coordonate.js";
import { deseneaza, deseneazaCelule, deseneazaVizitate, redimensioneaza } from "./desen.js";
import { $, optiuniCautare, parametriDescompunere } from "./dom.js";
import {
  actualizeazaButoane, afiseazaComparatie, afiseazaMesaj, afiseazaRezultat, ascundeComparatia,
  ascundeMesaj, marcheazaRandComparatie,
} from "./panou.js";
import { stare } from "./stare.js";

// ======================================================================
// Planificarea drumului
// ======================================================================
let temporizatorPlanificare = null;
let controlerPlanificare = null;

/** Planifică după o mică pauză: mai multe modificări rapide produc o singură cerere. */
export function programeazaPlanificare(intarziere = 150) {
  clearTimeout(temporizatorPlanificare);
  temporizatorPlanificare = setTimeout(planifica, intarziere);
}

/** Celulele depind doar de hartă (fără start / țintă) și de parametrii descompunerii. */
function cheieDescompunere() {
  const h = stare.harta;
  return JSON.stringify([h.latime, h.inaltime, h.obstacole, parametriDescompunere()]);
}

export async function planifica() {
  if (!stare.harta) return;
  const cheie = cheieDescompunere();
  const cuCelule = cheie !== stare.cheieCelule || !stare.celule;
  controlerPlanificare?.abort();          // o cerere mai veche nu mai e utilă
  controlerPlanificare = new AbortController();
  try {
    const r = await api.planifica({
      harta: stare.harta,
      descompunere: parametriDescompunere(),
      ...optiuniCautare(),
      include_celule: cuCelule,           // nu le cerem din nou dacă nu s-au schimbat
      include_ordine: true,
    }, controlerPlanificare.signal);
    if (cuCelule) {
      stare.celule = r.descompunere.celule;
      stare.cheieCelule = cheie;
      stare.tipCelule = r.descompunere.tip;
      deseneazaCelule();
    }
    stare.rezultat = r;
    opresteAnimatia();
    deseneazaVizitate(r.drum.ordine_vizitare ?? []);
    afiseazaRezultat(r);
    ascundeMesaj();
    marcheazaRandComparatie();
    deseneaza();
  } catch (e) {
    if (e.name === "AbortError") return;
    afiseazaMesaj(e.message);
  }
}

export async function compara() {
  const buton = $("compara");
  buton.disabled = true;
  try {
    stare.comparatie = await api.compara({
      harta: stare.harta,
      descompunere: parametriDescompunere(),
      metode: ["bfs", "dijkstra", "astar", "greedy"],
      vecinatati: [4, 8],
    });
    afiseazaComparatie(stare.comparatie);
  } catch (e) {
    afiseazaMesaj(e.message);
  } finally {
    buton.disabled = false;
  }
}

// ======================================================================
// Hărțile salvate
// ======================================================================
export async function incarcaListaHarti(selectata) {
  const harti = await api.listaHarti();
  $("harti").innerHTML = '<option value="">— alege o hartă —</option>' +
    harti.map((h) => `<option value="${h}">${h}</option>`).join("");
  if (selectata && harti.includes(selectata)) $("harti").value = selectata;
  return harti;
}

export async function incarcaHarta(nume) {
  try {
    seteazaHarta(await api.incarcaHarta(nume), nume);
  } catch (e) {
    afiseazaMesaj(e.message);
  }
}

export async function salveazaHarta() {
  const nume = $("nume-harta").value.trim();
  if (!nume) {
    afiseazaMesaj("Scrie un nume pentru hartă.");
    return;
  }
  try {
    await api.salveazaHarta(nume, stare.harta);
    await incarcaListaHarti(nume);
    afiseazaMesaj(`Harta „${nume}” a fost salvată.`, "info");
  } catch (e) {
    afiseazaMesaj(e.message);
  }
}

// ======================================================================
// Modificarea hărții
// ======================================================================
/** Înlocuiește harta curentă și resetează tot ce depindea de cea veche. */
export function seteazaHarta(h, nume = "") {
  stare.harta = {
    latime: h.latime,
    inaltime: h.inaltime,
    start: [...h.start],
    tinta: [...h.tinta],
    obstacole: h.obstacole.map((p) => p.map((v) => [...v])),
  };
  stare.selectat = -1;
  stare.poligonNou = [];
  stare.celule = null;
  stare.rezultat = null;
  ascundeComparatia();
  $("latime").value = h.latime;
  $("inaltime").value = h.inaltime;
  $("nume-harta").value = nume;
  actualizeazaButoane();
  redimensioneaza();
  planifica();
}

export function hartaNoua() {
  const latime = Number($("latime").value) || 100;
  const inaltime = Number($("inaltime").value) || 70;
  $("harti").value = "";
  seteazaHarta({
    latime, inaltime,
    start: [Math.min(5, latime / 2), Math.min(5, inaltime / 2)],
    tinta: [Math.max(latime - 5, latime / 2), Math.max(inaltime - 5, inaltime / 2)],
    obstacole: [],
  });
}

export function schimbaDimensiunile() {
  const latime = Number($("latime").value);
  const inaltime = Number($("inaltime").value);
  if (!(latime > 0 && inaltime > 0)) return;
  const h = stare.harta;
  h.latime = latime;
  h.inaltime = inaltime;
  h.start = limiteaza(h.start);
  h.tinta = limiteaza(h.tinta);
  redimensioneaza();
  programeazaPlanificare();
}

/** De apelat după orice modificare a obstacolelor. */
export function modificareHarta() {
  if (stare.comparatie) ascundeComparatia();     // comparația veche nu mai e valabilă
  programeazaPlanificare(80);
}

export function adaugaObstacol(poligon) {
  stare.harta.obstacole.push(poligon);
  stare.selectat = stare.harta.obstacole.length - 1;
  actualizeazaButoane();
  modificareHarta();
  deseneaza();
}

export function stergeObstacolSelectat() {
  if (stare.selectat < 0) return;
  stare.harta.obstacole.splice(stare.selectat, 1);
  stare.selectat = -1;
  actualizeazaButoane();
  modificareHarta();
  deseneaza();
}

export function golesteHarta() {
  stare.harta.obstacole = [];
  stare.selectat = -1;
  actualizeazaButoane();
  modificareHarta();
  deseneaza();
}
