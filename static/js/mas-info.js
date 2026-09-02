// mas-info.js
// Recorta la descripción de productos/servicios a unas pocas líneas,
// con un botón que la despliega/colapsa.

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".btn-mas-info").forEach((boton) => {
    boton.addEventListener("click", () => {
      const parrafo = boton.previousElementSibling;
      if (!parrafo) return;

      parrafo.classList.toggle("expandido");
      boton.textContent = parrafo.classList.contains("expandido") ? "Menos info" : "Más info";
    });
  });
});