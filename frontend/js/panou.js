// Tot ce se afișează în afara hărții: metricile drumului, tabelul comparativ,
// mesajele de eroare / informare și starea butoanelor.

import { NUME_METODE } from "./config.js";
import { canvas } from "./desen.js";
import { $, optiuniCautare, parametriDescompunere } from "./dom.js";
import { stare } from "./stare.js";

export const format = (v, zecimale = 1) => (v == null ? "–" : Number(v).toFixed(zecimale));

// ----------------------------------------------------------------------
// Rezultatul planificării
// ----------------------------------------------------------------------
export function afiseazaRezultat({ drum, descompunere: d }) {
  const s = d.statistici;
  const caseta = $("stare-drum");
  caseta.className = `stare-drum ${drum.gasit ? "gasit" : "negasit"}`;
  caseta.innerHTML = drum.gasit
    ? `Drum găsit cu ${NUME_METODE[drum.metoda]}`
    : `Nu s-a găsit drum <small>${drum.motiv}</small>`;

  const cm = (v) => (v != null ? `${format(v)} <small>cm</small>` : "–");
  const viraje = drum.viraje_netezite != null ? ` <small>→ ${drum.viraje_netezite} netezit</small>` : "";
  const metrici = [
    ["Lungimea drumului", drum.gasit ? cm(drum.lungime) : "–"],
    ["Lungimea netezită", cm(drum.lungime_netezita)],
    ["Viraje", drum.gasit ? `${drum.viraje}${viraje}` : "–"],
    ["Celule vizitate", `${drum.noduri_vizitate}`],
    ["Timp căutare", `${format(drum.timp_ms, 2)} <small>ms</small>`],
    ["Timp descompunere", `${format(d.timp_ms, 1)} <small>ms</small>`],
    ["Celule", `${s.celule_total}`],
    ["Libere / mixte / ocupate", `${s.celule_libere} <small>/ ${s.celule_mixte} / ${s.celule_ocupate}</small>`],
  ];
  $("metrici").innerHTML = metrici.map(([t, v]) => `<div><dt>${t}</dt><dd>${v}</dd></div>`).join("");
}

// ----------------------------------------------------------------------
// Tabelul comparativ
// ----------------------------------------------------------------------
export function afiseazaComparatie({ rezultate }) {
  const gasite = rezultate.filter((x) => x.gasit);
  const minim = (cheie) => Math.min(...gasite.map((x) => x[cheie]));
  const celeMaiBune = {
    lungime: minim("lungime"),
    lungime_netezita: minim("lungime_netezita"),
    noduri_vizitate: minim("noduri_vizitate"),
  };
  // valorile cele mai bune din fiecare coloană sunt evidențiate
  const celula = (x, cheie, zecimale = 1) => {
    const bun = x.gasit && x[cheie] === celeMaiBune[cheie] ? ' class="cel-mai-bun"' : "";
    const valoare = cheie === "noduri_vizitate" ? x[cheie] : x.gasit ? format(x[cheie], zecimale) : "–";
    return `<td${bun}>${valoare}</td>`;
  };
  $("tabel-comparatie").innerHTML = `
    <thead><tr>
      <th>Algoritm</th><th>Vecini</th><th>Lungime (cm)</th><th>Netezit (cm)</th>
      <th>Viraje</th><th>Vizitate</th><th>Timp (ms)</th>
    </tr></thead>
    <tbody>${rezultate.map((x) => `
      <tr data-metoda="${x.metoda}" data-vecinatate="${x.vecinatate}">
        <td>${NUME_METODE[x.metoda]}</td><td>${x.vecinatate}</td>
        ${celula(x, "lungime")}${celula(x, "lungime_netezita")}
        <td>${x.gasit ? `${x.viraje} → ${x.viraje_netezite}` : "–"}</td>
        ${celula(x, "noduri_vizitate")}
        <td>${format(x.timp_ms, 2)}</td>
      </tr>`).join("")}
    </tbody>`;
  $("comparatie").hidden = false;
  marcheazaRandComparatie();
}

export function ascundeComparatia() {
  stare.comparatie = null;
  $("comparatie").hidden = true;
}

/** Evidențiază în tabel rândul care corespunde setărilor curente. */
export function marcheazaRandComparatie() {
  const { vecinatate } = parametriDescompunere();
  const { metoda } = optiuniCautare();
  for (const tr of document.querySelectorAll("#tabel-comparatie tbody tr")) {
    tr.classList.toggle("activ", tr.dataset.metoda === metoda && Number(tr.dataset.vecinatate) === vecinatate);
  }
}

// ----------------------------------------------------------------------
// Mesaje și butoane
// ----------------------------------------------------------------------
export function afiseazaMesaj(text, tip = "eroare") {
  const m = $("mesaj");
  m.textContent = text;
  m.className = `mesaj ${tip === "info" ? "info" : ""}`;
  m.hidden = false;
}

/** Ascunde mesajele de eroare; cele de informare rămân până la următorul mesaj. */
export function ascundeMesaj() {
  if (!$("mesaj").classList.contains("info")) $("mesaj").hidden = true;
}

export function actualizeazaButoane() {
  $("sterge-obstacol").disabled = stare.selectat < 0;
  $("ajutor-unealta").textContent = stare.unealta === "muta"
    ? "Trage startul (S), ținta (T) sau un obstacol. La obstacolul selectat poți trage și vârfurile. Delete îl șterge."
    : "Click pentru fiecare vârf. Închide poligonul cu click pe primul vârf, dublu-click sau Enter. Esc anulează.";
  canvas.style.cursor = stare.unealta === "deseneaza" ? "crosshair" : "default";
}
