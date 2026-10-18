// Cererile HTTP către serverul FastAPI. Fiecare funcție întoarce JSON-ul
// răspunsului sau aruncă o eroare cu un mesaj lizibil.

import { API } from "./config.js";

async function cerere(cale, optiuni = {}) {
  const raspuns = await fetch(API + cale, {
    headers: { "Content-Type": "application/json" },
    ...optiuni,
  });
  const date = await raspuns.json().catch(() => ({}));
  if (!raspuns.ok) {
    let detaliu = date.detail ?? `Eroare ${raspuns.status}`;
    if (Array.isArray(detaliu)) {           // erorile de validare pydantic (422)
      detaliu = detaliu.map((d) => d.msg.replace(/^Value error, /, "")).join("; ");
    }
    throw new Error(detaliu);
  }
  return date;
}

const post = (cale, corp, signal) =>
  cerere(cale, { method: "POST", body: JSON.stringify(corp), signal });

export const sanatate = () => cerere("/api/sanatate");

export const planifica = (corp, signal) => post("/api/planifica", corp, signal);

export const compara = (corp) => post("/api/compara", corp);

export const listaHarti = async () => (await cerere("/api/harti")).harti;

export const incarcaHarta = (nume) => cerere(`/api/harti/${encodeURIComponent(nume)}`);

export const salveazaHarta = (nume, harta) =>
  cerere(`/api/harti/${encodeURIComponent(nume)}`, { method: "PUT", body: JSON.stringify(harta) });
