// Mini-carrusel de fotos por tarjeta (producto o servicio), estilo Mercado Libre.
// Cada tarjeta con más de una foto tiene su propio carrusel independiente,
// controlado con las flechitas ‹ ›.

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.carrusel-fotos').forEach(function (carrusel) {
        const fotos = carrusel.querySelectorAll('.foto-carrusel');
        if (fotos.length <= 1) return; // con una sola foto no hace falta carrusel

        let indiceActual = 0;

        function mostrarFoto(indice) {
            fotos.forEach(function (foto, i) {
                foto.classList.toggle('activa', i === indice);
            });
        }

        const btnAnterior = carrusel.querySelector('.btn-carrusel-anterior');
        const btnSiguiente = carrusel.querySelector('.btn-carrusel-siguiente');

        if (btnAnterior) {
            btnAnterior.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                indiceActual = (indiceActual - 1 + fotos.length) % fotos.length;
                mostrarFoto(indiceActual);
            });
        }

        if (btnSiguiente) {
            btnSiguiente.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                indiceActual = (indiceActual + 1) % fotos.length;
                mostrarFoto(indiceActual);
            });
        }
    });
});// Mini-carrusel de fotos por tarjeta (producto o servicio), estilo Mercado Libre.
// Cada tarjeta con más de una foto tiene su propio carrusel independiente,
// controlado con las flechitas ‹ ›.

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.carrusel-fotos').forEach(function (carrusel) {
        const fotos = carrusel.querySelectorAll('.foto-carrusel');
        if (fotos.length <= 1) return; // con una sola foto no hace falta carrusel

        let indiceActual = 0;

        function mostrarFoto(indice) {
            fotos.forEach(function (foto, i) {
                foto.classList.toggle('activa', i === indice);
            });
        }

        const btnAnterior = carrusel.querySelector('.btn-carrusel-anterior');
        const btnSiguiente = carrusel.querySelector('.btn-carrusel-siguiente');

        if (btnAnterior) {
            btnAnterior.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                indiceActual = (indiceActual - 1 + fotos.length) % fotos.length;
                mostrarFoto(indiceActual);
            });
        }

        if (btnSiguiente) {
            btnSiguiente.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                indiceActual = (indiceActual + 1) % fotos.length;
                mostrarFoto(indiceActual);
            });
        }
    });
});