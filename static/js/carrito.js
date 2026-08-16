// carrito.js
// Carrito de compras simple, sin backend.
// Usamos localStorage del navegador para que el carrito no se pierda
// si el cliente navega entre páginas o recarga (es como guardar
// una variable, pero persiste aunque cierre la pestaña).

const CARRITO_KEY = "carritoAC";
const NUMERO_WHATSAPP = "5491124038046";

// --- Funciones de datos (leer/escribir el carrito) ---

function obtenerCarrito() {
  const data = localStorage.getItem(CARRITO_KEY);
  // Si nunca se guardó nada, devolvemos un array vacío (como una lista vacía en Python)
  return data ? JSON.parse(data) : [];
}

function guardarCarrito(carrito) {
  localStorage.setItem(CARRITO_KEY, JSON.stringify(carrito));
}

function agregarProducto(nombre) {
  const carrito = obtenerCarrito();
  // Buscamos si el producto ya está en el carrito (equivalente a un "for" buscando coincidencia)
  const existente = carrito.find((item) => item.nombre === nombre);

  if (existente) {
    existente.cantidad += 1;
  } else {
    carrito.push({ nombre: nombre, cantidad: 1 });
  }

  guardarCarrito(carrito);
  renderizarCarrito();
}

function quitarProducto(nombre) {
  let carrito = obtenerCarrito();
  carrito = carrito.filter((item) => item.nombre !== nombre);
  guardarCarrito(carrito);
  renderizarCarrito();
}

function vaciarCarrito() {
  guardarCarrito([]);
  renderizarCarrito();
}

// --- Funciones de interfaz (mostrar el carrito en pantalla) ---

function renderizarCarrito() {
  const carrito = obtenerCarrito();
  const contador = document.getElementById("contador-carrito");
  const lista = document.getElementById("lista-carrito");

  // Sumamos cantidades (ej: 2 cremas + 1 serum = 3, no 2 líneas)
  const totalItems = carrito.reduce((acc, item) => acc + item.cantidad, 0);
  contador.textContent = totalItems;

  lista.innerHTML = "";

  if (carrito.length === 0) {
    lista.innerHTML = "<li class='carrito-vacio'>El carrito está vacío</li>";
    return;
  }

  carrito.forEach((item) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <span>${item.nombre} x${item.cantidad}</span>
      <button class="btn-quitar" data-nombre="${item.nombre}" aria-label="Quitar ${item.nombre}">✕</button>
    `;
    lista.appendChild(li);
  });
}

function toggleCarrito() {
  document.getElementById("panel-carrito").classList.toggle("abierto");
}

// --- Armado del pedido final por WhatsApp ---

function generarMensajeWhatsapp() {
  const carrito = obtenerCarrito();

  if (carrito.length === 0) {
    alert("Tu carrito está vacío. Agregá algún producto antes de enviar el pedido.");
    return;
  }

  let mensaje = "Hola! Quiero consultar por estos productos:%0A";
  carrito.forEach((item) => {
    mensaje += `- ${item.nombre} x${item.cantidad}%0A`;
  });

  const url = `https://wa.me/${NUMERO_WHATSAPP}?text=${mensaje}`;
  window.open(url, "_blank");
}

// --- Conectar todo cuando la página termina de cargar ---

document.addEventListener("DOMContentLoaded", () => {
  renderizarCarrito();

  // Un botón "Agregar al carrito" por cada producto
  document.querySelectorAll(".btn-agregar-carrito").forEach((boton) => {
    boton.addEventListener("click", () => {
      agregarProducto(boton.dataset.nombre);
    });
  });

  // Delegación de eventos: en vez de poner un listener por cada botón "✕"
  // (que todavía no existen al cargar la página), escuchamos clics en la
  // lista completa y revisamos qué se clickeó.
  document.getElementById("lista-carrito").addEventListener("click", (e) => {
    if (e.target.classList.contains("btn-quitar")) {
      quitarProducto(e.target.dataset.nombre);
    }
  });

  document.getElementById("boton-carrito-flotante").addEventListener("click", toggleCarrito);
  document.getElementById("btn-vaciar-carrito").addEventListener("click", vaciarCarrito);
  document.getElementById("btn-enviar-pedido").addEventListener("click", generarMensajeWhatsapp);
});