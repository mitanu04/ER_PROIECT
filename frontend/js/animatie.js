// Animația căutării: celulele vizitate apar în ordinea în care algoritmul
// le-a extins (drum.ordine_vizitare), pe durata aleasă din panou.

import { deseneaza, deseneazaAcum, deseneazaVizitate } from "./desen.js";
import { $ } from "./dom.js";
import { stare } from "./stare.js";

export function pornesteAnimatia() {
  const ordine = stare.rezultat?.drum.ordine_vizitare;
  if (!ordine?.length) return;
  opresteAnimatia();
  const durata = Number($("durata").value) * 1000;
  const t0 = performance.now();
  let desenate = 0;
  deseneazaVizitate(ordine, 0, 0);
  stare.animatie = { id: 0 };
  $("animeaza").textContent = "■ Oprește";

  const pas = (t) => {
    const pana = Math.min(ordine.length, Math.ceil((ordine.length * (t - t0)) / durata));
    if (pana > desenate) {
      deseneazaVizitate(ordine, desenate, pana);     // doar celulele noi
      desenate = pana;
    }
    $("coordonate").textContent = `vizitate ${desenate} / ${ordine.length}`;
    if (desenate < ordine.length) {
      stare.animatie.id = requestAnimationFrame(pas);
      deseneazaAcum();
    } else {
      opresteAnimatia();
    }
  };
  stare.animatie.id = requestAnimationFrame(pas);
}

export function opresteAnimatia() {
  if (!stare.animatie) return;
  cancelAnimationFrame(stare.animatie.id);
  stare.animatie = null;
  $("animeaza").textContent = "▶ Animează";
  deseneazaVizitate(stare.rezultat?.drum.ordine_vizitare ?? []);
  deseneaza();
}

export function comutaAnimatia() {
  if (stare.animatie) opresteAnimatia();
  else pornesteAnimatia();
}
