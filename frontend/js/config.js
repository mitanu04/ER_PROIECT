// Constantele interfeței: adresa serverului, culorile și dimensiunile de desen.

// Servit de FastAPI (portul 8000) -> aceeași origine; altfel (de ex. Live Server) -> serverul local.
export const API = new URLSearchParams(location.search).get("api")
  ?? (location.port === "8000" ? "" : "http://127.0.0.1:8000");

// Aceleași culori ca în figurile matplotlib (backend/vizualizare.py)
export const CULORI = {
  stari: ["#FFFFFF", "#BCD4EE", "#FFF1A8"],     // liberă, ocupată, mixtă
  linie: "#C8C8C8",
  vizitat: "rgba(201, 190, 240, 0.85)",
  obstacol: "rgba(47, 111, 181, 0.9)",
  margineObstacol: "#1B4A80",
  selectat: "#F59F00",
  drum: "#1A1A1A",
  netezit: "#E8590C",
  start: "#1F4FD8",
  tinta: "#D62828",
  poligonNou: "#E8590C",
};

export const NUME_METODE = { bfs: "BFS", dijkstra: "Dijkstra", astar: "A*", greedy: "Greedy" };

export const PAD = 12;                 // margine în jurul hărții, în pixeli
export const RAZA_PUNCT = 8;           // raza startului / țintei, în pixeli
export const PRAG_ATINGERE = 10;       // distanța (px) la care un punct poate fi „prins” cu mouse-ul
export const PAS_ROTUNJIRE = 0.5;      // coordonatele se rotunjesc la 0,5 cm
