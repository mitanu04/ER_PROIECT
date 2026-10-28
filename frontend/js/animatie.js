// Animațiile, pe durata aleasă din panou:
//   - căutarea: celulele vizitate apar în ordinea în care algoritmul
//     le-a extins (drum.ordine_vizitare);
//   - împărțirea quadtree-ului: harta pornește ca o singură celulă, iar
//     celulele mixte se împart în 4, nivel cu nivel, până la frunzele finale.

import { deseneaza, deseneazaAcum, deseneazaImpartire, deseneazaVizitate } from "./desen.js";
import { $ } from "./dom.js";
import { stare } from "./stare.js";

const BUTOANE = { cautare: ["animeaza", "▶ Animează"], impartire: ["imparte", "▶ Animează împărțirea"] };

/**
 * Rulează o animație cu `total` pași. deseneazaPasi(de, pana) desenează pașii
 * [de, pana) (cu de = 0 golește întâi stratul), iar eticheta(pana) e textul de sub hartă.
 */
function ruleaza(tip, total, deseneazaPasi, eticheta) {
  opresteAnimatia();
  const durata = Number($("durata").value) * 1000;
  const t0 = performance.now();
  let desenate = 0;
  deseneazaPasi(0, 0);
  stare.animatie = { tip, id: 0, evidentiat: null };
  $(BUTOANE[tip][0]).textContent = "■ Oprește";

  const pas = (t) => {
    const pana = Math.min(total, Math.ceil((total * (t - t0)) / durata));
    if (pana > desenate) {
      deseneazaPasi(desenate, pana);                 // doar pașii noi
      desenate = pana;
    }
    $("coordonate").textContent = eticheta(desenate);
    if (desenate < total) {
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
  const [id, text] = BUTOANE[stare.animatie.tip];
  stare.animatie = null;
  $(id).textContent = text;
  deseneazaVizitate(stare.rezultat?.drum.ordine_vizitare ?? []);
  deseneaza();
}

// ----------------------------------------------------------------------
// Căutarea
// ----------------------------------------------------------------------
export function pornesteAnimatia() {
  const ordine = stare.rezultat?.drum.ordine_vizitare;
  if (!ordine?.length) return;
  ruleaza("cautare", ordine.length,
    (de, pana) => deseneazaVizitate(ordine, de, pana),
    (n) => `vizitate ${n} / ${ordine.length}`);
}

export function comutaAnimatia() {
  if (stare.animatie?.tip === "cautare") opresteAnimatia();
  else pornesteAnimatia();
}

// ----------------------------------------------------------------------
// Împărțirea quadtree-ului
// ----------------------------------------------------------------------
/**
 * Reconstruiește împărțirile din frunzele quadtree-ului. Fiecare pas e
 * {nod, copii}: nodul împărțit (null la primul pas) și celulele care apar
 * în locul lui, ca [x, y, lățime, înălțime, stare]. Un copil care se împarte
 * mai departe e mixt; o frunză își păstrează starea finală.
 *
 * Sferturile au exact jumătate din latura părintelui, deci adâncimea unei
 * frunze e log2(W / w), iar strămoșul de la adâncimea k e celula
 * (W / 2^k) x (H / 2^k) care conține centrul frunzei.
 */
function pasiImpartire(celule, W, H) {
  const cheie = (k, ix, iy) => `${k},${ix},${iy}`;
  const frunze = new Map();
  const interne = new Map();              // în preordine, ca în construcția recursivă
  for (const c of celule) {
    const [x, y, w, h] = c;
    const d = Math.round(Math.log2(W / w));
    const cx = x + w / 2, cy = y + h / 2;
    for (let k = 0; k <= d; k++) {
      const n = 2 ** k;
      const ix = Math.floor((cx * n) / W), iy = Math.floor((cy * n) / H);
      if (k === d) frunze.set(cheie(k, ix, iy), c);
      else if (!interne.has(cheie(k, ix, iy))) interne.set(cheie(k, ix, iy), [k, ix, iy]);
    }
  }
  if (!interne.size) return [{ nod: null, copii: [celule[0]] }];

  const dreptunghi = (k, ix, iy) => {
    const w = W / 2 ** k, h = H / 2 ** k;
    return [ix * w, iy * h, w, h, 2];
  };
  const pasi = [{ nod: null, copii: [dreptunghi(0, 0, 0)] }];
  // nivel cu nivel (sortarea e stabilă, deci în cadrul nivelului rămâne preordinea)
  for (const [k, ix, iy] of [...interne.values()].sort((a, b) => a[0] - b[0])) {
    const copii = [];
    for (const [dx, dy] of [[0, 0], [1, 0], [0, 1], [1, 1]]) {
      const [cx, cy] = [2 * ix + dx, 2 * iy + dy];
      copii.push(frunze.get(cheie(k + 1, cx, cy)) ?? dreptunghi(k + 1, cx, cy));
    }
    pasi.push({ nod: dreptunghi(k, ix, iy), adancime: k, copii });
  }
  return pasi;
}

export function pornesteImpartirea() {
  if (stare.tipCelule !== "quadtree" || !stare.celule?.length) return;
  const { latime, inaltime } = stare.harta;
  const pasi = pasiImpartire(stare.celule, latime, inaltime);
  const total = pasi.length - 1;          // primul pas (harta întreagă) nu e o împărțire
  ruleaza("impartire", pasi.length,
    (de, pana) => {
      deseneazaImpartire(pasi, de, pana);
      if (pana > 0) stare.animatie.evidentiat = pasi[pana - 1].nod;
    },
    (n) => {
      const ultim = pasi[n - 1];
      const adancime = ultim?.nod ? ` · adâncimea ${ultim.adancime + 1}` : "";
      return `împărțiri ${Math.max(0, n - 1)} / ${total}${adancime}`;
    });
}

export function comutaImpartirea() {
  if (stare.animatie?.tip === "impartire") opresteAnimatia();
  else pornesteImpartirea();
}
