// Transformări între centimetri (originea stânga-jos, y în sus) și pixeli
// (originea stânga-sus, y în jos), plus câteva teste geometrice pentru mouse.

import { PAD, PAS_ROTUNJIRE } from "./config.js";
import { stare, vedere } from "./stare.js";

export const laEcran = ([x, y]) =>
  [PAD + x * vedere.scara, PAD + (stare.harta.inaltime - y) * vedere.scara];

export const dinEcran = (px, py) =>
  [(px - PAD) / vedere.scara, stare.harta.inaltime - (py - PAD) / vedere.scara];

export const rotunjeste = (v) => Math.round(v / PAS_ROTUNJIRE) * PAS_ROTUNJIRE;

/** Celula [x, y, lățime, înălțime] ca dreptunghi în pixeli [x, y, lățime, înălțime]. */
export function dreptunghiCelula([x, y, w, h]) {
  const s = vedere.scara;
  return [PAD + x * s, PAD + (stare.harta.inaltime - y - h) * s, w * s, h * s];
}

/** Aduce punctul în interiorul hărții. */
export function limiteaza([x, y]) {
  const { latime, inaltime } = stare.harta;
  return [Math.min(Math.max(x, 0), latime), Math.min(Math.max(y, 0), inaltime)];
}

export function punctInPoligon([x, y], poligon) {
  let interior = false;
  for (let i = 0, j = poligon.length - 1; i < poligon.length; j = i++) {
    const [xi, yi] = poligon[i];
    const [xj, yj] = poligon[j];
    if ((yi > y) !== (yj > y) && x < xi + ((y - yi) * (xj - xi)) / (yj - yi)) interior = !interior;
  }
  return interior;
}

/** Distanța în pixeli dintre un punct al hărții și o poziție de pe ecran. */
export function distantaEcran(punct, px, py) {
  const [x, y] = laEcran(punct);
  return Math.hypot(x - px, y - py);
}
