# seed.py — correr UNA sola vez: python seed.py
from database import SessionLocal, Base, engine
import models

Base.metadata.create_all(bind=engine)
db = SessionLocal()

categorias_nombres = ["Cremas de Limpieza", "Serums", "Cremas Hidratantes"]
categorias = {}
for nombre in categorias_nombres:
    existente = db.query(models.Categoria).filter(models.Categoria.nombre == nombre).first()
    if not existente:
        existente = models.Categoria(nombre=nombre)
        db.add(existente)
        db.commit()
        db.refresh(existente)
    categorias[nombre] = existente

productos_iniciales = [
    {"nombre": "Pieles sensibles y mixtas", "categoria": "Cremas de Limpieza", "imagen": "piel_sensible_y_mixta.jpg"},
    {"nombre": "Pieles para control sebo", "categoria": "Cremas de Limpieza", "imagen": "sebo_control.jpg"},
    {"nombre": "Cicabost", "categoria": "Serums", "imagen": "cicabost.jpg"},
    {"nombre": "Hyaluronico B5", "categoria": "Serums", "imagen": "hyalu_b5.jpg"},
    {"nombre": "Retinol", "categoria": "Serums", "imagen": "retinol.jpg"},
    {"nombre": "Vitamina C", "categoria": "Serums", "imagen": "vita_c.jpg"},
    {"nombre": "Niacinamida", "categoria": "Serums", "imagen": "niacinamida.jpg"},
    {"nombre": "Anti age y nutri protect", "categoria": "Cremas Hidratantes", "imagen": "anti_age_y_nutri_protect.jpg"},
    {"nombre": "Hidratante facial", "categoria": "Cremas Hidratantes", "imagen": "hidra_protect.jpg"},
]

for datos in productos_iniciales:
    ya_existe = db.query(models.Producto).filter(models.Producto.nombre == datos["nombre"]).first()
    if ya_existe:
        continue
    db.add(models.Producto(
        nombre=datos["nombre"],
        descripcion="",
        precio=0,
        categoria_id=categorias[datos["categoria"]].id,
        imagen=f"/static/imagenes/{datos['imagen']}",
        disponible=True,
    ))

db.commit()
db.close()
print("Listo.")# seed.py — correr UNA sola vez: python seed.py
from database import SessionLocal, Base, engine
import models

Base.metadata.create_all(bind=engine)
db = SessionLocal()

categorias_nombres = ["Cremas de Limpieza", "Serums", "Cremas Hidratantes"]
categorias = {}
for nombre in categorias_nombres:
    existente = db.query(models.Categoria).filter(models.Categoria.nombre == nombre).first()
    if not existente:
        existente = models.Categoria(nombre=nombre)
        db.add(existente)
        db.commit()
        db.refresh(existente)
    categorias[nombre] = existente

productos_iniciales = [
    {"nombre": "Pieles sensibles y mixtas", "categoria": "Cremas de Limpieza", "imagen": "piel_sensible_y_mixta.jpg"},
    {"nombre": "Pieles para control sebo", "categoria": "Cremas de Limpieza", "imagen": "sebo_control.jpg"},
    {"nombre": "Cicabost", "categoria": "Serums", "imagen": "cicabost.jpg"},
    {"nombre": "Hyaluronico B5", "categoria": "Serums", "imagen": "hyalu_b5.jpg"},
    {"nombre": "Retinol", "categoria": "Serums", "imagen": "retinol.jpg"},
    {"nombre": "Vitamina C", "categoria": "Serums", "imagen": "vita_c.jpg"},
    {"nombre": "Niacinamida", "categoria": "Serums", "imagen": "niacinamida.jpg"},
    {"nombre": "Anti age y nutri protect", "categoria": "Cremas Hidratantes", "imagen": "anti_age_y_nutri_protect.jpg"},
    {"nombre": "Hidratante facial", "categoria": "Cremas Hidratantes", "imagen": "hidra_protect.jpg"},
]

for datos in productos_iniciales:
    ya_existe = db.query(models.Producto).filter(models.Producto.nombre == datos["nombre"]).first()
    if ya_existe:
        continue
    db.add(models.Producto(
        nombre=datos["nombre"],
        descripcion="",
        precio=0,
        categoria_id=categorias[datos["categoria"]].id,
        imagen=f"/static/imagenes/{datos['imagen']}",
        disponible=True,
    ))

db.commit()
db.close()
print("Listo.")