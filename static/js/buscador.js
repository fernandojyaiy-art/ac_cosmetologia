// buscador.js
// Buscador reutilizable: filtra lo que YA está en la página, sin ir al servidor.
// Se usa con un input así:
//   <input class="buscador" data-items=".item-busqueda" data-grupos=".grupo-busqueda" data-sin-resultados="id-del-mensaje">
//   - data-items: qué elementos se filtran (cada producto).
//   - data-grupos: (opcional) contenedores que se esconden si se quedan sin items (cada categoría).
//   - data-sin-resultados: (opcional) id de un mensaje "No encontramos nada" para mostrar.
// Cada item puede tener data-texto="..." con lo que se busca; si no, usa su texto visible.

// "Máscara" -> "mascara": saca tildes y pasa a minúsculas, para que buscar
// "mascara" encuentre "Máscara" y "ACIDO" encuentre "Ácido".
function normalizarTexto(texto) {
  return texto.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

function inicializarBuscador(input) {
  const items = Array.from(document.querySelectorAll(input.dataset.items));
  const grupos = input.dataset.grupos ? Array.from(document.querySelectorAll(input.dataset.grupos)) : [];
  const sinResultados = input.dataset.sinResultados
    ? document.getElementById(input.dataset.sinResultados)
    : null;

  // Guardamos el texto normalizado de cada item UNA vez, no en cada tecla
  items.forEach((item) => {
    item.dataset.textoBusqueda = normalizarTexto(item.dataset.texto || item.textContent);
  });

  input.addEventListener("input", () => {
    // "mascara 500" -> ["mascara", "500"]: el producto tiene que tener TODAS las palabras
    const palabras = normalizarTexto(input.value).split(/\s+/).filter(Boolean);

    let hayAlguno = false;
    items.forEach((item) => {
      const coincide = palabras.every((p) => item.dataset.textoBusqueda.includes(p));
      // style.display y no el atributo "hidden": las tarjetas tienen display:flex en el CSS,
      // y eso le gana a "hidden". "" = volver a lo que diga el CSS.
      item.style.display = coincide ? "" : "none";
      if (coincide) hayAlguno = true;
    });

    // Una categoría se esconde si no le quedó ningún producto visible
    grupos.forEach((grupo) => {
      const visibles = Array.from(grupo.querySelectorAll(input.dataset.items))
        .some((item) => item.style.display !== "none");
      grupo.style.display = visibles ? "" : "none";
    });

    if (sinResultados) sinResultados.style.display = hayAlguno ? "none" : "";
  });
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("input.buscador").forEach(inicializarBuscador);
});
