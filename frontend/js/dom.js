// Accesul la elementele paginii și la valorile din panoul de comenzi.

export const $ = (id) => document.getElementById(id);

const valoareBifata = (nume) => document.querySelector(`input[name=${nume}]:checked`).value;

export function parametriDescompunere() {
  return {
    tip: valoareBifata("tip"),
    latura: Number($("latura").value) || 2,
    vecinatate: Number(valoareBifata("vecinatate")),
    adancime_max: Number($("adancime").value) || 7,
  };
}

export function optiuniCautare() {
  return { metoda: $("metoda").value, netezire: $("netezire").checked };
}
