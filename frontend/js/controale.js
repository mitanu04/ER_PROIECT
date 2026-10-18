// Legarea panoului de comenzi (din stânga) la acțiunile aplicației.

import { comutaAnimatia } from "./animatie.js";
import {
  compara, golesteHarta, hartaNoua, incarcaHarta, programeazaPlanificare, salveazaHarta,
  schimbaDimensiunile, stergeObstacolSelectat,
} from "./aplicatie.js";
import { deseneaza, redimensioneaza } from "./desen.js";
import { $ } from "./dom.js";
import { seteazaUnealta } from "./editor.js";

const laSchimbare = (selector, functie) => {
  for (const el of document.querySelectorAll(selector)) el.addEventListener("change", functie);
};

export function initControale() {
  // Hartă
  $("harti").addEventListener("change", (ev) => ev.target.value && incarcaHarta(ev.target.value));
  $("salveaza").addEventListener("click", salveazaHarta);
  $("harta-noua").addEventListener("click", hartaNoua);
  $("goleste").addEventListener("click", golesteHarta);
  laSchimbare("#latime, #inaltime", schimbaDimensiunile);

  // Editare
  laSchimbare("input[name=unealta]", (ev) => seteazaUnealta(ev.target.value));
  $("sterge-obstacol").addEventListener("click", stergeObstacolSelectat);

  // Descompunere
  laSchimbare("input[name=tip]", (ev) => {
    const quadtree = ev.target.value === "quadtree";
    $("camp-adancime").hidden = !quadtree;
    $("eticheta-latura").textContent = quadtree ? "Latura minimă (cm)" : "Latura celulei (cm)";
    programeazaPlanificare(0);
  });
  laSchimbare("input[name=vecinatate]", () => programeazaPlanificare(0));
  for (const id of ["latura", "adancime"]) {
    $(id).addEventListener("input", () => programeazaPlanificare(300));
  }

  // Căutare și afișare
  laSchimbare("#metoda, #netezire", () => programeazaPlanificare(0));
  laSchimbare("#arata-celule, #arata-vizitate", deseneaza);
  $("durata").addEventListener("input", () => {
    $("eticheta-durata").textContent = `${$("durata").value} s`;
  });
  $("animeaza").addEventListener("click", comutaAnimatia);
  $("compara").addEventListener("click", compara);

  // Click pe un rând din tabelul comparativ -> acel algoritm pe hartă
  $("tabel-comparatie").addEventListener("click", (ev) => {
    const tr = ev.target.closest("tbody tr");
    if (!tr) return;
    $("metoda").value = tr.dataset.metoda;
    document.querySelector(`input[name=vecinatate][value="${tr.dataset.vecinatate}"]`).checked = true;
    programeazaPlanificare(0);
  });

  let temporizator = null;
  window.addEventListener("resize", () => {
    clearTimeout(temporizator);
    temporizator = setTimeout(redimensioneaza, 100);
  });
}
