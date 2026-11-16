"""
Carga la lista de precios de Libra (lista_libra.json) en la tabla de productos.

Que hace con cada producto de la lista:
  - Si NO existe un producto con ese nombre exacto -> lo crea OCULTO
    (disponible=False), con stock 0 y los 3 precios. No aparece en la web
    hasta que lo actives desde el panel (con foto y stock).
  - Si YA existe uno con ese nombre exacto -> solo le actualiza costo y
    precio profesional. El precio publico y si esta visible o no, NO se tocan.

Eso ultimo hace que el script sirva tambien para el futuro: cuando Libra
mande una lista nueva, actualizas lista_libra.json, lo corres de nuevo y se
actualizan los precios sin duplicar nada ni pisar lo que cargo Anto.

Uso local (con el venv activado):
    python cargar_lista_libra.py

En produccion se corre igual que la migracion, con el tunel y $env:DATABASE_URL.
"""
import json

from database import SessionLocal, Base, engine
import models

ARCHIVO_LISTA = "lista_libra.json"
NOMBRE_MARCA = "Libra Cosmética"

# Por si se corre contra una base nueva: crea las tablas que falten.
Base.metadata.create_all(bind=engine)


def buscar_o_crear(db, modelo, nombre):
    """Devuelve la Categoria/Marca con ese nombre; si no existe, la crea.
    Sirve para los dos porque ambos modelos tienen un campo .nombre."""
    objeto = db.query(modelo).filter(modelo.nombre == nombre).first()
    if not objeto:
        objeto = modelo(nombre=nombre)
        db.add(objeto)
        db.flush()  # le pide a la base el id sin cerrar la transaccion todavia
    return objeto


def main():
    # encoding="utf-8" para que los acentos (Óleo, Máscara) se lean bien en Windows
    with open(ARCHIVO_LISTA, encoding="utf-8") as f:
        lista = json.load(f)

    db = SessionLocal()
    creados = actualizados = 0
    try:
        marca = buscar_o_crear(db, models.Marca, NOMBRE_MARCA)

        for item in lista:
            producto = db.query(models.Producto).filter(
                models.Producto.nombre == item["nombre"]
            ).first()

            if producto:
                producto.costo = item["costo"]
                producto.precio_profesional = item["precio_profesional"]
                actualizados += 1
            else:
                categoria = buscar_o_crear(db, models.Categoria, item["categoria"])
                db.add(models.Producto(
                    nombre=item["nombre"],
                    precio=item["precio_publico"],
                    precio_profesional=item["precio_profesional"],
                    costo=item["costo"],
                    categoria_id=categoria.id,
                    marca_id=marca.id,
                    stock=0,
                    disponible=False,  # oculto hasta que lo actives desde el panel
                ))
                creados += 1

        # Un solo commit al final: o se carga la lista entera, o nada.
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(f"Lista de Libra cargada: {creados} productos nuevos (ocultos), {actualizados} actualizados.")


if __name__ == "__main__":
    main()
