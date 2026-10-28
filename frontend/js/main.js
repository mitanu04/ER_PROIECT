// Punctul de intrare: leagă evenimentele, verifică serverul și încarcă harta inițială.
//
// Modulele:
//   config.js      constante (adresa serverului, culori, dimensiuni)
//   stare.js       starea comună a aplicației
//   dom.js         elementele paginii și valorile din panou
//   coordonate.js  transformări cm <-> pixeli, teste geometrice
//   api.js         cererile către server
//   desen.js       desenarea pe canvas
//   animatie.js    animația căutării și a împărțirii quadtree-ului
//   panou.js       rezultate, tabelul comparativ, mesaje
//   aplicatie.js   planificarea și operațiile pe hartă
//   editor.js      editarea hărții cu mouse-ul și tastatura
//   controale.js   panoul de comenzi

import * as api from "./api.js";
import { API } from "./config.js";
import { hartaNoua, incarcaHarta, incarcaListaHarti } from "./aplicatie.js";
import { $ } from "./dom.js";
import { initControale } from "./controale.js";
import { initEditor } from "./editor.js";
import { actualizeazaButoane, afiseazaMesaj } from "./panou.js";
import { stare, vedere } from "./stare.js";

// Pentru depanare din consola browserului: aplicatie.stare, aplicatie.vedere
window.aplicatie = { stare, vedere };

async function porneste() {
  initControale();
  initEditor();
  actualizeazaButoane();
  try {
    await api.sanatate();
  } catch {
    afiseazaMesaj(`Nu mă pot conecta la server (${API || location.origin}). ` +
      "Pornește-l din folderul backend cu: uvicorn api:app --reload");
    return;
  }
  const harti = await incarcaListaHarti("demo");
  const initiala = harti.includes("demo") ? "demo" : harti[0];
  if (initiala) {
    await incarcaHarta(initiala);
  } else {
    $("latime").value = 100;
    $("inaltime").value = 70;
    hartaNoua();
  }
}

porneste();
