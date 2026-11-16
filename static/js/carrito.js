// carrito.js
// Carrito con cantidad, precios, total y paso de confirmación.
// El pedido se manda por WhatsApp con el detalle; el medio de pago
// se coordina directamente en la conversación (no se fija en la web).

const NUMERO_WHATSAPP = "5491124038046";

// ¿Quién está comprando? Lo dice el <body data-tipo-cliente="..."> que arma Jinja.
// Si la página no lo tiene, se toma como público (así no se rompe ninguna página vieja).
const ES_PROFESIONAL = document.body.dataset.tipoCliente === "profesional";

// Un carrito separado para cada tipo de cliente, guardado con distinto nombre en el
// navegador. Si fuera el mismo, un producto agregado a precio público seguiría con
// ese precio después de loguearse como profesional (y al revés).
// El del público conserva el nombre de siempre, así nadie pierde lo que ya tenía cargado.
const CARRITO_KEY = ES_PROFESIONAL ? "carritoAC_profesional" : "carritoAC";

// --- Funciones de datos ---

function obtenerCarrito() {
  const data = localStorage.getItem(CARRITO_KEY);
  return data ? JSON.parse(data) : [];
}

function guardarCarrito(carrito) {
  localStorage.setItem(CARRITO_KEY, JSON.stringify(carrito));
}

// precioContado: precio en efectivo/transferencia, o null si el producto no tiene
function agregarProducto(nombre, precio, cantidad, precioContado = null) {
  const carrito = obtenerCarrito();
  const existente = carrito.find((item) => item.nombre === nombre);

  if (existente) {
    existente.cantidad += cantidad;
    // Actualizamos los precios por si cambiaron desde la última vez que lo agregó
    existente.precio = precio;
    existente.precioContado = precioContado;
  } else {
    carrito.push({ nombre: nombre, precio: precio, cantidad: cantidad, precioContado: precioContado });
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

// Total pagando en efectivo/transferencia. Si un producto no tiene precio de contado
// (o es un item viejo guardado antes de este cambio), se suma con su precio de lista.
function calcularTotalContado(carrito) {
  return carrito.reduce((acc, item) => acc + (item.precioContado || item.precio) * item.cantidad, 0);
}

// ¿Vale la pena mostrar el segundo total? Solo si algún producto tiene precio de contado
function hayPrecioContado(carrito) {
  return carrito.some((item) => item.precioContado);
}

// Crea (una sola vez) la fila "Efectivo / transferencia" debajo de una fila de total
// que ya existe en el HTML. Se hace desde acá para no tener que tocar cada página.
function filaTotalContado(idTotalExistente) {
  const idNuevo = idTotalExistente + "-contado";
  let fila = document.getElementById("fila-" + idNuevo);
  if (!fila) {
    const filaExistente = document.getElementById(idTotalExistente).parentElement;
    fila = filaExistente.cloneNode(false); // misma clase/estilo, pero vacía
    fila.id = "fila-" + idNuevo;
    fila.innerHTML = `<span>Efectivo / transferencia</span><span id="${idNuevo}"></span>`;
    filaExistente.after(fila);
  }
  return fila;
}

// Pone los dos totales (o uno solo) en una de las dos pantallas del carrito
function mostrarTotales(carrito, idTotal) {
  const filaLista = document.getElementById(idTotal).parentElement;
  const etiquetaLista = filaLista.querySelector("span");
  const filaContado = filaTotalContado(idTotal);

  document.getElementById(idTotal).textContent = `$${formatearPrecio(calcularTotal(carrito))}`;

  if (hayPrecioContado(carrito)) {
    etiquetaLista.textContent = "Débito / crédito";
    document.getElementById(idTotal + "-contado").textContent = `$${formatearPrecio(calcularTotalContado(carrito))}`;
    filaContado.style.display = "";
  } else {
    etiquetaLista.textContent = "Total";
    filaContado.style.display = "none";
  }
}

function formatearPrecio(numero) {
  return numero.toLocaleString("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// --- Interfaz: lista del carrito ---

function renderizarCarrito() {
  const carrito = obtenerCarrito();
  const contador = document.getElementById("contador-carrito");
  const lista = document.getElementById("lista-carrito");

  const totalItems = carrito.reduce((acc, item) => acc + item.cantidad, 0);
  contador.textContent = totalItems;

  lista.innerHTML = "";

  if (carrito.length === 0) {
    lista.innerHTML = "<li class='carrito-vacio'>El carrito está vacío</li>";
    mostrarTotales(carrito, "total-carrito");
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

  mostrarTotales(carrito, "total-carrito");
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

  mostrarTotales(carrito, "total-confirmacion");
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

  const inputNombre = document.getElementById("nombre-cliente");
  const nombre = inputNombre.value.trim();

  if (!nombre) {
    alert("Contanos tu nombre antes de enviar el pedido.");
    inputNombre.focus();
    return;
  }

  // El mensaje se arma como texto normal (con \n para los saltos de línea)
  // y recién al final se "codifica" para la URL con encodeURIComponent.
  // Antes los nombres iban sin codificar: un producto como "Vit-C & Resveratrol"
  // cortaba el mensaje en el "&", y el "+" de "Niacinamide + Zinc" se convertía en espacio.
  let mensaje = ES_PROFESIONAL ? "*PEDIDO PROFESIONAL*\n" : "";
  mensaje += `Hola! Soy ${nombre}, este es mi pedido:\n`;
  carrito.forEach((item) => {
    mensaje += `- ${item.nombre} x${item.cantidad}\n`;
  });
  if (hayPrecioContado(carrito)) {
    mensaje += `Total débito/crédito: $${formatearPrecio(calcularTotal(carrito))}\n`;
    mensaje += `Total efectivo/transferencia: $${formatearPrecio(calcularTotalContado(carrito))}`;
  } else {
    mensaje += `Total: $${formatearPrecio(calcularTotal(carrito))}`;
  }

  const url = `https://wa.me/${NUMERO_WHATSAPP}?text=${encodeURIComponent(mensaje)}`;
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
      // data-precio-contado viene vacío si no hay precio de contado: parseFloat("") da NaN -> null
      const precioContado = parseFloat(boton.dataset.precioContado) || null;
      const tarjeta = boton.closest(".producto");
      const cantidadEl = tarjeta ? tarjeta.querySelector(".cantidad-valor") : null;
      const cantidad = cantidadEl ? parseInt(cantidadEl.textContent, 10) : 1;

      agregarProducto(nombre, precio, cantidad, precioContado);

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