// Editarea hărții cu mouse-ul și tastatura, direct pe canvas:
//   - unealta „muta”: tragerea startului, țintei, obstacolelor și a vârfurilor
//   - unealta „deseneaza”: obstacole noi, vârf cu vârf

import {
  adaugaObstacol, modificareHarta, programeazaPlanificare, stergeObstacolSelectat,
} from "./aplicatie.js";
import { PRAG_ATINGERE } from "./config.js";
import { dinEcran, distantaEcran, limiteaza, punctInPoligon, rotunjeste } from "./coordonate.js";
import { canvas, deseneaza } from "./desen.js";
import { $ } from "./dom.js";
import { actualizeazaButoane, format } from "./panou.js";
import { stare } from "./stare.js";

export function initEditor() {
  canvas.addEventListener("pointerdown", laApasare);
  canvas.addEventListener("pointermove", laMiscare);
  canvas.addEventListener("pointerup", terminaTragerea);
  canvas.addEventListener("pointercancel", terminaTragerea);
  canvas.addEventListener("pointerleave", () => {
    stare.cursor = null;
    if (!stare.animatie) $("coordonate").textContent = "";
    deseneaza();
  });
  canvas.addEventListener("dblclick", () => {
    if (stare.unealta === "deseneaza" && stare.poligonNou.length >= 3) finalizeazaPoligon();
  });
  document.addEventListener("keydown", laTasta);
}

export function seteazaUnealta(unealta) {
  stare.unealta = unealta;
  stare.poligonNou = [];
  if (unealta === "deseneaza") stare.selectat = -1;
  actualizeazaButoane();
  deseneaza();
}

// ----------------------------------------------------------------------
// Mouse
// ----------------------------------------------------------------------
function pozitieMouse(ev) {
  const r = canvas.getBoundingClientRect();
  const px = ev.clientX - r.left;
  const py = ev.clientY - r.top;
  return { px, py, cm: dinEcran(px, py) };
}

/** Ce se află sub mouse: startul, ținta, un vârf al obstacolului selectat sau un obstacol. */
function elementLa(px, py, cm) {
  const h = stare.harta;
  if (distantaEcran(h.start, px, py) <= PRAG_ATINGERE) return { tip: "start" };
  if (distantaEcran(h.tinta, px, py) <= PRAG_ATINGERE) return { tip: "tinta" };
  if (stare.selectat >= 0) {
    const poligon = h.obstacole[stare.selectat];
    const varf = poligon.findIndex((v) => distantaEcran(v, px, py) <= PRAG_ATINGERE - 2);
    if (varf >= 0) return { tip: "varf", obstacol: stare.selectat, varf };
  }
  // de sus în jos: obstacolul desenat ultimul e deasupra
  for (let i = h.obstacole.length - 1; i >= 0; i--) {
    if (punctInPoligon(cm, h.obstacole[i])) return { tip: "obstacol", obstacol: i };
  }
  return null;
}

function laApasare(ev) {
  if (!stare.harta || ev.button !== 0) return;
  const { px, py, cm } = pozitieMouse(ev);

  if (stare.unealta === "deseneaza") {
    const primul = stare.poligonNou[0];
    if (primul && stare.poligonNou.length >= 3 && distantaEcran(primul, px, py) <= PRAG_ATINGERE) {
      finalizeazaPoligon();
    } else {
      stare.poligonNou.push(limiteaza(cm.map(rotunjeste)));
      deseneaza();
    }
    return;
  }

  const element = elementLa(px, py, cm);
  if (element?.tip === "obstacol" || element?.tip === "varf") {
    stare.selectat = element.obstacol;
  } else if (!element) {
    stare.selectat = -1;
  }
  actualizeazaButoane();
  if (element) {
    const poligon = element.obstacol != null ? stare.harta.obstacole[element.obstacol] : null;
    stare.tragere = { ...element, inceput: cm, original: poligon?.map((v) => [...v]) };
    canvas.setPointerCapture(ev.pointerId);
    canvas.style.cursor = "grabbing";
  }
  deseneaza();
}

function laMiscare(ev) {
  if (!stare.harta) return;
  const { px, py, cm } = pozitieMouse(ev);
  stare.cursor = limiteaza(cm.map(rotunjeste));
  if (!stare.animatie) afiseazaCoordonate(cm);

  if (stare.tragere) {
    trage(stare.tragere, cm);
  } else if (stare.unealta === "muta") {
    canvas.style.cursor = elementLa(px, py, cm) ? "grab" : "default";
  }
  deseneaza();
}

function trage(t, cm) {
  const h = stare.harta;
  if (t.tip === "start" || t.tip === "tinta") {
    h[t.tip] = stare.cursor;
  } else if (t.tip === "varf") {
    h.obstacole[t.obstacol][t.varf] = stare.cursor;
  } else if (t.tip === "obstacol") {
    // translatare, fără să iasă din hartă
    const xs = t.original.map((v) => v[0]);
    const ys = t.original.map((v) => v[1]);
    const dx = Math.min(Math.max(rotunjeste(cm[0] - t.inceput[0]), -Math.min(...xs)), h.latime - Math.max(...xs));
    const dy = Math.min(Math.max(rotunjeste(cm[1] - t.inceput[1]), -Math.min(...ys)), h.inaltime - Math.max(...ys));
    h.obstacole[t.obstacol] = t.original.map(([x, y]) => [x + dx, y + dy]);
  }
  t.mutat = true;
  // startul și ținta nu schimbă celulele, deci răspunsul vine repede: replanificăm des
  if (t.tip === "start" || t.tip === "tinta") programeazaPlanificare(40);
  else modificareHarta();
}

function terminaTragerea() {
  if (!stare.tragere) return;
  const { mutat } = stare.tragere;
  stare.tragere = null;
  canvas.style.cursor = "default";
  if (mutat) programeazaPlanificare(0);
}

function afiseazaCoordonate([x, y]) {
  const inHarta = x >= 0 && y >= 0 && x <= stare.harta.latime && y <= stare.harta.inaltime;
  $("coordonate").textContent = inHarta ? `x ${format(x)} cm · y ${format(y)} cm` : "";
}

// ----------------------------------------------------------------------
// Obstacolul nou
// ----------------------------------------------------------------------
function finalizeazaPoligon() {
  // elimină vârfurile duble (de ex. de la dublu-click) și închiderea pe primul vârf
  const v = stare.poligonNou.filter((p, i, a) =>
    i === 0 || Math.hypot(p[0] - a[i - 1][0], p[1] - a[i - 1][1]) > 1e-6);
  if (v.length > 1 && Math.hypot(v[0][0] - v.at(-1)[0], v[0][1] - v.at(-1)[1]) < 1e-6) v.pop();
  stare.poligonNou = [];
  if (v.length >= 3) adaugaObstacol(v);
  deseneaza();
}

// ----------------------------------------------------------------------
// Tastatura
// ----------------------------------------------------------------------
function laTasta(ev) {
  if (ev.target.matches("input, select, textarea")) return;
  if (ev.key === "Escape" && stare.poligonNou.length) {
    stare.poligonNou = [];
    deseneaza();
  } else if (ev.key === "Enter" && stare.poligonNou.length >= 3) {
    finalizeazaPoligon();
  } else if ((ev.key === "Delete" || ev.key === "Backspace") && stare.selectat >= 0) {
    ev.preventDefault();
    stergeObstacolSelectat();
  }
}
