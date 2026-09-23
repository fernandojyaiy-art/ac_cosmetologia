"""
Script de migracion (correr UNA sola vez, despues de agregar
ImagenProducto/ImagenServicio a models.py y de que el server haya
arrancado al menos una vez para crear las tablas nuevas).

Copia la foto que ya tenia cargada cada Producto/Servicio en el
campo viejo "imagen" como la primera fila en las tablas nuevas,
para no perder ninguna foto ya subida.

Uso local:
    python migrar_imagenes.py

Uso en Railway (contra la base de produccion):
    railway run python migrar_imagenes.py

Si esto tira error de import en "from database import SessionLocal",
fijate como se llama en tu database.py la funcion/variable para abrir
una sesion fuera de una request de FastAPI (get_db es un generador
pensado para Depends(), aca hace falta una sesion "suelta"), y
ajustá el import de esta primera linea.
"""
from database import SessionLocal
import models

db = SessionLocal()

productos_migrados = 0
for producto in db.query(models.Producto).all():
    if producto.imagen and not producto.imagenes:
        db.add(models.ImagenProducto(producto_id=producto.id, ruta_imagen=producto.imagen, orden=0))
        productos_migrados += 1

servicios_migrados = 0
for servicio in db.query(models.Servicio).all():
    if servicio.imagen and not servicio.imagenes:
        db.add(models.ImagenServicio(servicio_id=servicio.id, ruta_imagen=servicio.imagen, orden=0))
        servicios_migrados += 1

db.commit()
db.close()

print(f"Productos migrados: {productos_migrados}")
print(f"Servicios migrados: {servicios_migrados}")