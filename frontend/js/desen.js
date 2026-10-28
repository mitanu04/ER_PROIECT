// Desenarea hărții pe canvas, pe patru straturi:
//   - stratCelule:    descompunerea (se redesenează doar când se schimbă celulele)
//   - stratVizitate:  celulele vizitate de algoritm (și pentru animație)
//   - stratImpartire: quadtree-ul pe parcursul animației împărțirii
//   - canvas-ul principal: straturile de mai sus + obstacole, drumuri, start, țintă
// Astfel, la tragerea cu mouse-ul se redesenează doar elementele vectoriale,
// chiar dacă descompunerea are zeci de mii de celule.

import { CULORI, PAD, RAZA_PUNCT } from "./config.js";
import { dreptunghiCelula, laEcran } from "./coordonate.js";
import { $ } from "./dom.js";
import { stare, vedere } from "./stare.js";

export const canvas = $("canvas");
const ctx = canvas.getContext("2d");
const stratCelule = document.createElement("canvas");
const stratVizitate = document.createElement("canvas");
const stratImpartire = document.createElement("canvas");

/** Potrivește canvas-ul la spațiul disponibil și la proporțiile hărții. */
export function redimensioneaza() {
  if (!stare.harta) return;
  const { latime: W, inaltime: H } = stare.harta;
  const latimeDisponibila = $("suprafata").clientWidth - 16;
  const inaltimeMaxima = Math.max(320, window.innerHeight - 260);
  vedere.scara = Math.max(0.05, Math.min((latimeDisponibila - 2 * PAD) / W, (inaltimeMaxima - 2 * PAD) / H));
  vedere.latime = Math.round(W * vedere.scara + 2 * PAD);
  vedere.inaltime = Math.round(H * vedere.scara + 2 * PAD);
  vedere.dpr = window.devicePixelRatio || 1;
  for (const c of [canvas, stratCelule, stratVizitate, stratImpartire]) {
    c.width = Math.round(vedere.latime * vedere.dpr);
    c.height = Math.round(vedere.inaltime * vedere.dpr);
  }
  canvas.style.width = `${vedere.latime}px`;
  canvas.style.height = `${vedere.inaltime}px`;
  deseneazaCelule();
  deseneazaVizitate(stare.rezultat?.drum.ordine_vizitare ?? []);
  deseneaza();
}

// ----------------------------------------------------------------------
// Straturile pregătite dinainte
// ----------------------------------------------------------------------
export function deseneazaCelule() {
  const c = stratCelule.getContext("2d");
  c.setTransform(vedere.dpr, 0, 0, vedere.dpr, 0, 0);
  c.clearRect(0, 0, vedere.latime, vedere.inaltime);
  if (!stare.celule || !stare.harta) return;

  // un singur Path2D pe stare: mult mai rapid decât un fillRect pentru fiecare celulă
  const umpleri = CULORI.stari.map(() => new Path2D());
  const contur = new Path2D();
  let latimeMinimaPx = Infinity;
  for (const celula of stare.celule) {
    const [x, y, w, h] = dreptunghiCelula(celula);
    umpleri[celula[4]].rect(x, y, w, h);
    contur.rect(x, y, w, h);
    latimeMinimaPx = Math.min(latimeMinimaPx, w, h);
  }
  umpleri.forEach((p, i) => {
    c.fillStyle = CULORI.stari[i];
    c.fill(p);
  });
  // la grila uniformă liniile se văd doar dacă celulele nu sunt prea mici
  if (stare.tipCelule === "quadtree" || latimeMinimaPx >= 4) {
    c.strokeStyle = CULORI.linie;
    c.lineWidth = stare.tipCelule === "quadtree" ? 0.6 : 0.4;
    c.stroke(contur);
  }
}

/** Colorează celulele ordine[de..pana). Cu de = 0, stratul se golește întâi. */
export function deseneazaVizitate(ordine, de = 0, pana = ordine.length) {
  const c = stratVizitate.getContext("2d");
  c.setTransform(vedere.dpr, 0, 0, vedere.dpr, 0, 0);
  if (de === 0) c.clearRect(0, 0, vedere.latime, vedere.inaltime);
  if (!stare.celule) return;
  const cale = new Path2D();
  for (let i = de; i < pana; i++) {
    const celula = stare.celule[ordine[i]];
    if (celula) cale.rect(...dreptunghiCelula(celula));
  }
  c.fillStyle = CULORI.vizitat;
  c.fill(cale);
}

/** Desenează celulele apărute la pașii pasi[de..pana) ai împărțirii quadtree-ului
 *  (vezi pasiImpartire din animatie.js). Cu de = 0, stratul se golește întâi. */
export function deseneazaImpartire(pasi, de = 0, pana = pasi.length) {
  const c = stratImpartire.getContext("2d");
  c.setTransform(vedere.dpr, 0, 0, vedere.dpr, 0, 0);
  if (de === 0) c.clearRect(0, 0, vedere.latime, vedere.inaltime);
  if (!stare.harta) return;
  // copiii acoperă părintele, deci ajunge să-i desenăm peste el
  const umpleri = CULORI.stari.map(() => new Path2D());
  const contur = new Path2D();
  for (let i = de; i < pana; i++) {
    for (const celula of pasi[i].copii) {
      const [x, y, w, h] = dreptunghiCelula(celula);
      umpleri[celula[4]].rect(x, y, w, h);
      contur.rect(x, y, w, h);
    }
  }
  umpleri.forEach((p, i) => {
    c.fillStyle = CULORI.stari[i];
    c.fill(p);
  });
  c.strokeStyle = CULORI.linie;
  c.lineWidth = 0.6;
  c.stroke(contur);
}

// ----------------------------------------------------------------------
// Canvas-ul principal
// ----------------------------------------------------------------------
let cadruProgramat = false;

/** Cere o redesenare la următorul cadru (mai multe cereri în același cadru se comasează). */
export function deseneaza() {
  if (cadruProgramat) return;
  cadruProgramat = true;
  requestAnimationFrame(() => {
    cadruProgramat = false;
    deseneazaAcum();
  });
}

export function deseneazaAcum() {
  const h = stare.harta;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (!h) return;

  // 1. celulele și celulele vizitate
  ctx.fillStyle = "#FFFFFF";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  if (stare.animatie?.tip === "impartire") {
    ctx.drawImage(stratImpartire, 0, 0);
  } else {
    if ($("arata-celule").checked) ctx.drawImage(stratCelule, 0, 0);
    if ($("arata-vizitate").checked || stare.animatie) ctx.drawImage(stratVizitate, 0, 0);
  }
  ctx.setTransform(vedere.dpr, 0, 0, vedere.dpr, 0, 0);

  // 2. obstacolele
  h.obstacole.forEach((poligon, i) => {
    caleaPoligonului(poligon);
    ctx.fillStyle = CULORI.obstacol;
    ctx.fill();
    ctx.lineWidth = i === stare.selectat ? 2.5 : 1;
    ctx.strokeStyle = i === stare.selectat ? CULORI.selectat : CULORI.margineObstacol;
    ctx.stroke();
  });

  // celula împărțită cel mai recent, în timpul animației împărțirii
  if (stare.animatie?.evidentiat) {
    ctx.lineWidth = 2;
    ctx.strokeStyle = CULORI.selectat;
    ctx.strokeRect(...dreptunghiCelula(stare.animatie.evidentiat));
  }

  // 3. marginea hărții
  ctx.lineWidth = 3;
  ctx.strokeStyle = CULORI.obstacol;
  ctx.strokeRect(PAD, PAD, h.latime * vedere.scara, h.inaltime * vedere.scara);

  // 4. drumurile (ascunse în timpul animației)
  const drum = stare.rezultat?.drum;
  if (drum?.gasit && !stare.animatie) {
    linieDrum(drum.puncte, CULORI.drum, 2.5);
    linieDrum(drum.puncte_netezite, CULORI.netezit, 2.5, true);
  }

  // 5. vârfurile obstacolului selectat (se pot trage)
  if (stare.selectat >= 0 && stare.unealta === "muta") {
    for (const v of h.obstacole[stare.selectat]) {
      const [x, y] = laEcran(v);
      ctx.fillStyle = "#FFFFFF";
      ctx.strokeStyle = CULORI.selectat;
      ctx.lineWidth = 2;
      ctx.fillRect(x - 4, y - 4, 8, 8);
      ctx.strokeRect(x - 4, y - 4, 8, 8);
    }
  }

  // 6. obstacolul în curs de desenare
  if (stare.poligonNou.length) deseneazaPoligonNou();

  // 7. startul și ținta
  cerc(h.start, CULORI.start, "S");
  cerc(h.tinta, CULORI.tinta, "T");
}

function caleaPoligonului(poligon) {
  ctx.beginPath();
  poligon.forEach((v, i) => (i ? ctx.lineTo(...laEcran(v)) : ctx.moveTo(...laEcran(v))));
  ctx.closePath();
}

function linieDrum(puncte, culoare, latime, punctat = false) {
  if (!puncte || puncte.length < 2) return;
  ctx.save();
  ctx.strokeStyle = culoare;
  ctx.lineWidth = latime;
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  if (punctat) ctx.setLineDash([8, 6]);
  ctx.beginPath();
  puncte.forEach((p, i) => (i ? ctx.lineTo(...laEcran(p)) : ctx.moveTo(...laEcran(p))));
  ctx.stroke();
  ctx.restore();
}

function cerc(punct, culoare, eticheta) {
  const [x, y] = laEcran(punct);
  ctx.beginPath();
  ctx.arc(x, y, RAZA_PUNCT, 0, 2 * Math.PI);
  ctx.fillStyle = culoare;
  ctx.fill();
  ctx.lineWidth = 2;
  ctx.strokeStyle = "#FFFFFF";
  ctx.stroke();
  ctx.fillStyle = "#FFFFFF";
  ctx.font = "bold 10px system-ui, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(eticheta, x, y + 0.5);
}

function deseneazaPoligonNou() {
  const puncte = stare.cursor ? [...stare.poligonNou, stare.cursor] : stare.poligonNou;
  ctx.save();
  ctx.strokeStyle = CULORI.poligonNou;
  ctx.fillStyle = "rgba(232, 89, 12, 0.12)";
  ctx.lineWidth = 2;
  ctx.setLineDash([5, 4]);
  caleaPoligonului(puncte);
  ctx.fill();
  ctx.stroke();
  ctx.restore();
  // primul vârf e mai mare: click pe el închide poligonul
  stare.poligonNou.forEach((v, i) => {
    const [x, y] = laEcran(v);
    ctx.beginPath();
    ctx.arc(x, y, i === 0 ? 6 : 4, 0, 2 * Math.PI);
    ctx.fillStyle = i === 0 ? CULORI.poligonNou : "#FFFFFF";
    ctx.strokeStyle = CULORI.poligonNou;
    ctx.lineWidth = 2;
    ctx.fill();
    ctx.stroke();
  });
}
