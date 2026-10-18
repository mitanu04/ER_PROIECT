// Starea comună a aplicației. Modulele o citesc și o modifică direct;
// după o modificare, cine a schimbat-o cere redesenarea sau o planificare nouă.

export const stare = {
  harta: null,            // {latime, inaltime, start, tinta, obstacole}, în cm
  rezultat: null,         // ultimul răspuns de la /api/planifica
  celule: null,           // celulele descompunerii (refolosite când se mută doar startul / ținta)
  cheieCelule: "",        // pentru ce hartă + parametri au fost calculate celulele
  tipCelule: "grila",
  unealta: "muta",        // "muta" sau "deseneaza"
  selectat: -1,           // indicele obstacolului selectat
  poligonNou: [],         // vârfurile obstacolului în curs de desenare
  tragere: null,          // ce se trage cu mouse-ul
  cursor: null,           // poziția mouse-ului, în cm
  animatie: null,
  comparatie: null,
};

// Cum e așezată harta pe ecran (calculată în redimensioneaza() din desen.js)
export const vedere = { scara: 1, latime: 0, inaltime: 0, dpr: 1 };
