// nav.js
// Menú hamburguesa con panel desplegable, que a su vez puede
// contener submenús de categorías (Servicios/Productos).

document.addEventListener("DOMContentLoaded", () => {
  const boton = document.getElementById("btn-menu-hamburguesa");
  const panel = document.getElementById("menu-panel");

  if (boton && panel) {
    boton.addEventListener("click", (e) => {
      e.stopPropagation();
      panel.classList.toggle("abierto");
    });
  }

  // Submenús de categorías (Servicios ▾ / Productos ▾) dentro del panel
  document.querySelectorAll(".nav-dropdown").forEach((item) => {
    const toggle = item.querySelector(".nav-dropdown-toggle");
    if (!toggle) return;

    toggle.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      item.classList.toggle("abierto");
    });
  });

  // Cerrar todo si se hace click afuera
  document.addEventListener("click", (e) => {
    if (panel && !panel.contains(e.target) && e.target !== boton) {
      panel.classList.remove("abierto");
    }
  });
});