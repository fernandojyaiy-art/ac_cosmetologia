// carrito.js
// Carrito con cantidad, precios, total y paso de confirmación.
// El pedido se manda por WhatsApp con el detalle; el medio de pago
// se coordina directamente en la conversación (no se fija en la web).

const CARRITO_KEY = "carritoAC";
const NUMERO_WHATSAPP = "5491124038046";

// --- Funciones de datos ---

function obtenerCarrito() {
  const data = localStorage.getItem(CARRITO_KEY);
  return data ? JSON.parse(data) : [];
}

function guardarCarrito(carrito) {
  localStorage.setItem(CARRITO_KEY, JSON.stringify(carrito));
}

function agregarProducto(nombre, precio, cantidad) {
  const carrito = obtenerCarrito();
  const existente = carrito.find((item) => item.nombre === nombre);

  if (existente) {
    existente.cantidad += cantidad;
  } else {
    carrito.push({ nombre: nombre, precio: precio, cantidad: cantidad });
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
  volverAlCarrito();
}

function calcularTotal(carrito) {
  return carrito.reduce((acc, item) => acc + item.precio * item.cantidad, 0);
}

function formatearPrecio(numero) {
  return numero.toLocaleString("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// --- Interfaz: lista del carrito ---

function renderizarCarrito() {
  const carrito = obtenerCarrito();
  const contador = document.getElementById("contador-carrito");
  const lista = document.getElementById("lista-carrito");
  const totalTexto = document.getElementById("total-carrito");

  const totalItems = carrito.reduce((acc, item) => acc + item.cantidad, 0);
  contador.textContent = totalItems;

  lista.innerHTML = "";

  if (carrito.length === 0) {
    lista.innerHTML = "<li class='carrito-vacio'>El carrito está vacío</li>";
    totalTexto.textContent = "$0,00";
    return;
  }

  carrito.forEach((item) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <span>${item.nombre} x${item.cantidad} — $${formatearPrecio(item.precio * item.cantidad)}</span>
      <button class="btn-quitar" data-nombre="${item.nombre}" aria-label="Quitar ${item.nombre}">✕</button>
    `;
    lista.appendChild(li);
  });

  totalTexto.textContent = `$${formatearPrecio(calcularTotal(carrito))}`;
}

function toggleCarrito() {
  document.getElementById("panel-carrito").classList.toggle("abierto");
  volverAlCarrito();
}

// --- Paso de confirmación ---

function irAConfirmacion() {
  const carrito = obtenerCarrito();
  if (carrito.length === 0) {
    alert("Tu carrito está vacío. Agregá algún producto antes de confirmar.");
    return;
  }

  document.getElementById("panel-carrito-lista").style.display = "none";
  document.getElementById("panel-carrito-confirmacion").style.display = "flex";

  const resumen = document.getElementById("resumen-confirmacion");
  resumen.innerHTML = "";
  carrito.forEach((item) => {
    const p = document.createElement("p");
    p.textContent = `${item.nombre} x${item.cantidad} — $${formatearPrecio(item.precio * item.cantidad)}`;
    resumen.appendChild(p);
  });

  document.getElementById("total-confirmacion").textContent = `$${formatearPrecio(calcularTotal(carrito))}`;
}

function volverAlCarrito() {
  const listaEl = document.getElementById("panel-carrito-lista");
  const confirmEl = document.getElementById("panel-carrito-confirmacion");
  if (listaEl) listaEl.style.display = "flex";
  if (confirmEl) confirmEl.style.display = "none";
}

function generarMensajeWhatsappPedido() {
  const carrito = obtenerCarrito();
  if (carrito.length === 0) return;

  let mensaje = "Hola! Este es mi pedido:%0A";
  carrito.forEach((item) => {
    mensaje += `- ${item.nombre} x${item.cantidad}%0A`;
  });
  mensaje += `Total: $${formatearPrecio(calcularTotal(carrito))}`;

  const url = `https://wa.me/${NUMERO_WHATSAPP}?text=${mensaje}`;
  window.open(url, "_blank");
}

// --- Selector de cantidad por producto (+/-) ---

function inicializarSelectoresCantidad() {
  document.querySelectorAll(".selector-cantidad").forEach((selector) => {
    const valor = selector.querySelector(".cantidad-valor");

    selector.querySelectorAll(".btn-cantidad").forEach((boton) => {
      boton.addEventListener("click", () => {
        let actual = parseInt(valor.textContent, 10);
        if (boton.dataset.accion === "sumar") {
          actual += 1;
        } else if (actual > 1) {
          actual -= 1;
        }
        valor.textContent = actual;
      });
    });
  });
}

// --- Conectar todo ---

document.addEventListener("DOMContentLoaded", () => {
  renderizarCarrito();
  inicializarSelectoresCantidad();

  document.querySelectorAll(".btn-agregar-carrito").forEach((boton) => {
    boton.addEventListener("click", () => {
      const nombre = boton.dataset.nombre;
      const precio = parseFloat(boton.dataset.precio) || 0;
      const tarjeta = boton.closest(".producto");
      const cantidadEl = tarjeta ? tarjeta.querySelector(".cantidad-valor") : null;
      const cantidad = cantidadEl ? parseInt(cantidadEl.textContent, 10) : 1;

      agregarProducto(nombre, precio, cantidad);

      if (cantidadEl) cantidadEl.textContent = "1";
    });
  });

  document.getElementById("lista-carrito").addEventListener("click", (e) => {
    if (e.target.classList.contains("btn-quitar")) {
      quitarProducto(e.target.dataset.nombre);
    }
  });

  document.getElementById("boton-carrito-flotante").addEventListener("click", toggleCarrito);
  document.getElementById("btn-vaciar-carrito").addEventListener("click", vaciarCarrito);
  document.getElementById("btn-confirmar-pedido").addEventListener("click", irAConfirmacion);
  document.getElementById("btn-volver-carrito").addEventListener("click", volverAlCarrito);
  document.getElementById("btn-enviar-pedido-final").addEventListener("click", generarMensajeWhatsappPedido);
});