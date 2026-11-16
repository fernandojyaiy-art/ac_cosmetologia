from fastapi import FastAPI, Depends, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse, FileResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import uuid
import os
import unicodedata
import hashlib
import hmac
import secrets
from dotenv import load_dotenv

load_dotenv()

from database import engine, Base, get_db, SessionLocal
import models


os.makedirs("static/uploads", exist_ok=True)

app = FastAPI(title="Tienda Estética")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SECRET_KEY", "clave-desarrollo-estetica")
)

# ============================================================
# INTERRUPTOR del apartado de profesionales ("feature flag")
# Se prende con la variable de entorno PROFESIONALES_ACTIVO=si
#   - en tu compu: una línea en el .env
#   - en Railway: en Variables del servicio
# Por defecto está APAGADO: si te olvidás de crear la variable, no se publica nada por accidente.
# Apagado = no aparece en el menú, no se puede registrar ni loguear nadie y nadie ve
# precios profesionales. El panel de admin sigue funcionando igual.
# ============================================================
PROFESIONALES_ACTIVO = os.environ.get("PROFESIONALES_ACTIVO", "no").strip().lower() in ("si", "sí", "true", "1")


def datos_de_sesion(request: Request) -> dict:
    """"Context processor": Starlette la llama SOLA cada vez que se arma CUALQUIER
    template, y lo que devuelve queda disponible en el HTML.
    Así el menú de todas las páginas sabe si hay una profesional logueada,
    sin tener que pasar "profesional" a mano en cada ruta."""
    db = SessionLocal()
    try:
        return {
            "profesional": profesional_actual(request, db),
            # Los templates lo usan para mostrar u ocultar "Soy profesional" y el bloque del inicio
            "profesionales_activo": PROFESIONALES_ACTIVO,
        }
    finally:
        db.close()


# directory=["templates", "."]: Jinja busca primero en templates/ y después en la raíz
# del proyecto. Eso permite que index.html y contacto-html/contacto.html (que siguen
# donde estaban) también pasen por Jinja y puedan mostrar el nombre de la profesional.
templates = Jinja2Templates(directory=["templates", "."], context_processors=[datos_de_sesion])

app.mount("/static", StaticFiles(directory="static"), name="static")

Base.metadata.create_all(bind=engine)


# ============================================================
# HELPERS: guardar archivos e imágenes múltiples
# (reemplazan la lógica que antes estaba repetida en cada ruta)
# ============================================================

def guardar_archivo(imagen: UploadFile) -> Optional[str]:
    """Guarda un UploadFile en static/uploads y devuelve la ruta pública, o None si no es válido."""
    if not imagen or not imagen.filename:
        return None
    extensiones_permitidas = {"jpg", "jpeg", "png", "webp"}
    extension = imagen.filename.split(".")[-1].lower()
    if extension not in extensiones_permitidas:
        return None
    nombre_archivo = f"{uuid.uuid4()}.{extension}"
    ruta_destino = f"static/uploads/{nombre_archivo}"
    with open(ruta_destino, "wb") as buffer:
        shutil.copyfileobj(imagen.file, buffer)
    return f"/static/uploads/{nombre_archivo}"


def guardar_imagenes_producto(producto: "models.Producto", imagenes: List[UploadFile], db: Session):
    """Guarda varias fotos nuevas para un producto, SIN borrar las que ya tenía.
    Mantiene producto.imagen (la portada) apuntando siempre a la primera foto,
    para que el catálogo actual (que usa producto.imagen) siga funcionando igual."""
    if not imagenes:
        return
    orden_actual = db.query(models.ImagenProducto).filter(
        models.ImagenProducto.producto_id == producto.id
    ).count()
    for imagen in imagenes:
        ruta = guardar_archivo(imagen)
        if not ruta:
            continue
        db.add(models.ImagenProducto(producto_id=producto.id, ruta_imagen=ruta, orden=orden_actual))
        if orden_actual == 0 or not producto.imagen:
            producto.imagen = ruta
        orden_actual += 1
    db.commit()


def guardar_imagenes_servicio(servicio: "models.Servicio", imagenes: List[UploadFile], db: Session):
    """Igual que guardar_imagenes_producto, pero para servicios."""
    if not imagenes:
        return
    orden_actual = db.query(models.ImagenServicio).filter(
        models.ImagenServicio.servicio_id == servicio.id
    ).count()
    for imagen in imagenes:
        ruta = guardar_archivo(imagen)
        if not ruta:
            continue
        db.add(models.ImagenServicio(servicio_id=servicio.id, ruta_imagen=ruta, orden=orden_actual))
        if orden_actual == 0 or not servicio.imagen:
            servicio.imagen = ruta
        orden_actual += 1
    db.commit()


# ============================================================
# HELPERS: profesionales (contraseñas, sesión y qué productos se ven)
# ============================================================

def hashear_password(password: str) -> str:
    """Convierte la contraseña en un hash que NO se puede volver atrás.
    - "sal": texto al azar distinto para cada usuaria, así dos personas con la
      misma contraseña no quedan con el mismo hash.
    - pbkdf2 repite el cálculo 200.000 veces a propósito: para vos es un
      instante, pero para alguien que quiera adivinar millones de claves es lentísimo.
    Se guarda "sal$hash" en un solo campo, porque para verificar hacen falta los dos."""
    sal = secrets.token_hex(16)
    hash_hex = hashlib.pbkdf2_hmac("sha256", password.encode(), sal.encode(), 200_000).hex()
    return f"{sal}${hash_hex}"


def verificar_password(password: str, guardado: str) -> bool:
    """Repite el mismo cálculo con la sal guardada y compara el resultado."""
    sal, hash_guardado = guardado.split("$", 1)
    hash_hex = hashlib.pbkdf2_hmac("sha256", password.encode(), sal.encode(), 200_000).hex()
    # compare_digest compara sin "cortar antes" al primer caracter distinto,
    # así nadie puede deducir la clave midiendo cuánto tarda la respuesta.
    return hmac.compare_digest(hash_hex, hash_guardado)


def profesional_actual(request: Request, db: Session) -> Optional["models.Profesional"]:
    """Devuelve la profesional logueada SOLO si sigue aprobada; si no, None.
    Se consulta la base en cada pedido (y no se confía solo en la sesión):
    si mañana la rechazás desde el panel, deja de ver precios al instante."""
    # Con el interruptor apagado, para todo el sitio nunca hay profesional logueada:
    # así ninguna página muestra precios profesionales ni productos de gabinete.
    if not PROFESIONALES_ACTIVO:
        return None
    profesional_id = request.session.get("profesional_id")
    if not profesional_id:
        return None
    profesional = db.query(models.Profesional).filter(models.Profesional.id == profesional_id).first()
    if not profesional or profesional.estado != "aprobada":
        request.session.pop("profesional_id", None)
        return None
    return profesional


def puede_ver(producto: "models.Producto", profesional) -> bool:
    """Regla única de visibilidad: tiene que estar disponible, y si es de
    gabinete (solo_profesionales) además tiene que haber una profesional logueada."""
    return producto.disponible and (profesional is not None or not producto.solo_profesionales)


def armar_catalogo(db: Session, profesional):
    """Devuelve [(categoria, [productos visibles])] solo con las categorías que
    tienen algo para mostrar. Así el menú "Productos" ya no lista categorías vacías
    (como las de Libra que todavía están ocultas)."""
    secciones = []
    for categoria in db.query(models.Categoria).all():
        visibles = [p for p in categoria.productos if puede_ver(p, profesional)]
        if visibles:
            secciones.append((categoria, visibles))
    return secciones


def a_float(texto: str) -> Optional[float]:
    """Convierte lo que llega de un input numérico opcional: "" -> None, "1500" -> 1500.0"""
    texto = (texto or "").strip()
    return float(texto) if texto else None


@app.get("/")
def inicio(request: Request):
    # Antes era FileResponse (mandaba el archivo tal cual). Ahora pasa por Jinja
    # para que el menú pueda decir "Hola, Ana" en vez de "Soy profesional".
    return templates.TemplateResponse(request, "index.html", {})


@app.get("/servicios")
def ver_servicios(request: Request, db: Session = Depends(get_db)):
    categorias = db.query(models.CategoriaServicio).all()
    return templates.TemplateResponse(request, "servicios.html", {"categorias": categorias})


@app.get("/servicio/{servicio_id}")
def ver_servicio(servicio_id: int, request: Request, db: Session = Depends(get_db)):
    servicio = db.query(models.Servicio).filter(models.Servicio.id == servicio_id).first()
    if not servicio:
        return RedirectResponse("/servicios")
    categorias = db.query(models.CategoriaServicio).all()
    return templates.TemplateResponse(
        request, "servicio_detalle.html", {"servicio": servicio, "categorias": categorias}
    )


@app.get("/contacto")
def contacto(request: Request):
    # Mismo cambio que en inicio(): de FileResponse a template
    return templates.TemplateResponse(request, "contacto-html/contacto.html", {})


@app.get("/productos")
def ver_productos(request: Request, db: Session = Depends(get_db)):
    profesional = profesional_actual(request, db)
    secciones = armar_catalogo(db, profesional)
    return templates.TemplateResponse(request, "productos.html", {
        "secciones": secciones,
        # "categorias" se sigue mandando para que el template actual funcione igual
        # (menú y listado), pero ahora solo con las que tienen productos visibles.
        "categorias": [categoria for categoria, _ in secciones],
        "profesional": profesional,
    })


@app.get("/producto/{producto_id}")
def ver_producto(producto_id: int, request: Request, db: Session = Depends(get_db)):
    profesional = profesional_actual(request, db)
    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    # Un producto de gabinete no se puede ver ni escribiendo la URL a mano
    if not producto or (producto.solo_profesionales and not profesional):
        return RedirectResponse("/productos")
    secciones = armar_catalogo(db, profesional)
    return templates.TemplateResponse(request, "producto_detalle.html", {
        "producto": producto,
        "categorias": [categoria for categoria, _ in secciones],
        "profesional": profesional,
    })


@app.get("/admin/login")
def mostrar_login(request: Request):
    return templates.TemplateResponse(request, "admin/login.html", {"error": None})


@app.post("/admin/login")
def procesar_login(request: Request, password: str = Form(...)):
    if password == os.environ.get("ADMIN_PASSWORD", "gael1234!"):
        request.session["logueado"] = True
        return RedirectResponse("/admin/panel", status_code=303)

    return templates.TemplateResponse(
        request, "admin/login.html", {"error": "Contraseña incorrecta"}
    )


@app.get("/admin/nuevo-producto")
def form_nuevo_producto(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    categorias = db.query(models.Categoria).all()
    marcas = db.query(models.Marca).all()
    return templates.TemplateResponse(
        request, "admin/nuevo_producto.html", {"categorias": categorias, "marcas": marcas}
    )


@app.post("/admin/nuevo-producto")
def crear_producto_form(
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(""),
    precio: float = Form(...),
    categoria_id: int = Form(...),
    marca_id: str = Form(""),
    stock: int = Form(0),
    imagenes: List[UploadFile] = File(None),
    disponible: str = Form("true"),
    precio_contado: str = Form(""),  # efectivo/transferencia; str porque puede venir vacío
    precio_profesional: str = Form(""),  # str y no float: puede venir vacío
    costo: str = Form(""),
    solo_profesionales: str = Form(""),  # checkbox: si no está tildado, no llega nada
    db: Session = Depends(get_db)
):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")

    nuevo_producto = models.Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        categoria_id=categoria_id,
        marca_id=int(marca_id) if marca_id else None,
        stock=stock,
        disponible=(disponible == "true"),
        precio_contado=a_float(precio_contado),
        precio_profesional=a_float(precio_profesional),
        costo=a_float(costo),
        solo_profesionales=(solo_profesionales == "true"),
    )
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)

    guardar_imagenes_producto(nuevo_producto, imagenes, db)

    return RedirectResponse("/admin/panel", status_code=303)


def clave_orden(texto: Optional[str]) -> str:
    """Clave para ordenar alfabéticamente ignorando mayúsculas y acentos
    (así "Ácido" queda entre las A y no después de la Z)."""
    sin_acentos = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return sin_acentos.lower()


def agrupar_por_categoria(items):
    """Agrupa productos o servicios por categoría y los ordena de la A a la Z.
    Devuelve una lista de pares: [(nombre de categoría, [items ordenados]), ...].
    Sirve para los dos paneles porque productos y servicios tienen ambos
    .categoria y .nombre."""
    por_categoria = {}
    sin_categoria = []
    for item in items:
        if item.categoria:
            por_categoria.setdefault(item.categoria.nombre, []).append(item)
        else:
            sin_categoria.append(item)

    # Categorías de la A a la Z, y dentro de cada una los items también
    grupos = [
        (nombre, sorted(lista, key=lambda i: clave_orden(i.nombre)))
        for nombre, lista in sorted(por_categoria.items(), key=lambda par: clave_orden(par[0]))
    ]
    # Los que no tienen categoría van al final, así no desaparecen del panel
    if sin_categoria:
        grupos.append(("Sin categoría", sorted(sin_categoria, key=lambda i: clave_orden(i.nombre))))
    return grupos


@app.get("/admin/panel")
def ver_panel(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    productos = db.query(models.Producto).all()
    # Cuántas profesionales esperan aprobación, para el contador del botón del panel.
    # .count() le pide a la base solo el número, sin traer las filas.
    pendientes = db.query(models.Profesional).filter(models.Profesional.estado == "pendiente").count()
    return templates.TemplateResponse(
        request, "admin/panel.html", {"grupos": agrupar_por_categoria(productos), "pendientes": pendientes}
    )


@app.get("/admin/eliminar-producto/{producto_id}")
def eliminar_producto(producto_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")

    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    if producto:
        db.delete(producto)
        db.commit()

    return RedirectResponse("/admin/panel", status_code=303)


@app.get("/admin/editar-producto/{producto_id}")
def form_editar_producto(producto_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")

    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    categorias = db.query(models.Categoria).all()
    marcas = db.query(models.Marca).all()

    return templates.TemplateResponse(
        request,
        "admin/editar_producto.html",
        {"producto": producto, "categorias": categorias, "marcas": marcas},
    )


@app.post("/admin/editar-producto/{producto_id}")
def guardar_edicion(
    producto_id: int,
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(""),
    precio: float = Form(...),
    categoria_id: int = Form(...),
    marca_id: str = Form(""),
    stock: int = Form(0),
    disponible: str = Form("true"),
    imagenes: List[UploadFile] = File(None),
    precio_contado: str = Form(""),
    precio_profesional: str = Form(""),
    costo: str = Form(""),
    solo_profesionales: str = Form(""),
    db: Session = Depends(get_db)
):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")

    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()

    producto.precio_contado = a_float(precio_contado)
    producto.precio_profesional = a_float(precio_profesional)
    producto.costo = a_float(costo)
    producto.solo_profesionales = (solo_profesionales == "true")
    producto.nombre = nombre
    producto.descripcion = descripcion
    producto.precio = precio
    producto.categoria_id = categoria_id
    producto.marca_id = int(marca_id) if marca_id else None
    producto.stock = stock
    producto.disponible = (disponible == "true")

    guardar_imagenes_producto(producto, imagenes, db)

    db.commit()
    return RedirectResponse("/admin/panel", status_code=303)


@app.get("/admin/eliminar-imagen-producto/{imagen_id}")
def eliminar_imagen_producto(imagen_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    imagen = db.query(models.ImagenProducto).filter(models.ImagenProducto.id == imagen_id).first()
    if imagen:
        producto_id = imagen.producto_id
        db.delete(imagen)
        db.commit()
        return RedirectResponse(f"/admin/editar-producto/{producto_id}", status_code=303)
    return RedirectResponse("/admin/panel", status_code=303)


@app.get("/admin/toggle-agotado/{producto_id}")
def toggle_agotado(producto_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    if producto:
        producto.disponible = not producto.disponible
        db.commit()
    return RedirectResponse("/admin/panel", status_code=303)


# Qué hace cada botón masivo del panel: accion -> (columna del producto, valor nuevo)
ACCIONES_MASIVAS = {
    "disponibles": ("disponible", True),
    "agotados": ("disponible", False),
    "solo_profesionales": ("solo_profesionales", True),
    "para_todos": ("solo_profesionales", False),
}


@app.post("/admin/categoria/{categoria_id}/masivo")
def accion_masiva_categoria(
    categoria_id: int,
    request: Request,
    accion: str = Form(...),
    db: Session = Depends(get_db),
):
    """Cambia disponible/solo_profesionales de TODOS los productos de una categoría."""
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")

    # Solo aceptamos acciones conocidas: si alguien manda otra cosa, no se toca nada
    if accion in ACCIONES_MASIVAS:
        columna, valor = ACCIONES_MASIVAS[accion]
        # getattr(models.Producto, "disponible") == models.Producto.disponible
        # .update() cambia todas las filas en UNA sola consulta a la base
        # (en vez de traer los productos y cambiarlos de a uno en un for).
        db.query(models.Producto).filter(
            models.Producto.categoria_id == categoria_id
        ).update({getattr(models.Producto, columna): valor}, synchronize_session=False)
        db.commit()

    # "#cat-ID" al final: vuelve al panel scrolleado justo en esa categoría
    return RedirectResponse(f"/admin/panel#cat-{categoria_id}", status_code=303)


@app.get("/admin/categorias")
def ver_categorias(request: Request, error: str = None, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    categorias = db.query(models.Categoria).all()
    marcas = db.query(models.Marca).all()
    categorias_servicios = db.query(models.CategoriaServicio).all()
    return templates.TemplateResponse(
        request,
        "admin/categorias.html",
        {
            "categorias": categorias,
            "marcas": marcas,
            "categorias_servicios": categorias_servicios,
            "error": error,
        },
    )

@app.post("/admin/categorias/nueva")
def crear_categoria(request: Request, nombre: str = Form(...), db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    existe = db.query(models.Categoria).filter(models.Categoria.nombre == nombre).first()
    if not existe:
        db.add(models.Categoria(nombre=nombre))
        db.commit()
    return RedirectResponse("/admin/categorias", status_code=303)


@app.get("/admin/eliminar-categoria/{categoria_id}")
def eliminar_categoria(categoria_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")

    tiene_productos = db.query(models.Producto).filter(models.Producto.categoria_id == categoria_id).first()
    if tiene_productos:
        return RedirectResponse(
            "/admin/categorias?error=No se puede eliminar: esa categoria tiene productos cargados. Reasignalos a otra categoria primero.",
            status_code=303)

    categoria = db.query(models.Categoria).filter(models.Categoria.id == categoria_id).first()
    if categoria:
        db.delete(categoria)
        db.commit()
    return RedirectResponse("/admin/categorias", status_code=303)


@app.get("/admin/editar-categoria/{categoria_id}")
def form_editar_categoria(categoria_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    categoria = db.query(models.Categoria).filter(models.Categoria.id == categoria_id).first()
    return templates.TemplateResponse(request, "admin/editar_categoria.html", {"categoria": categoria})


@app.post("/admin/editar-categoria/{categoria_id}")
def guardar_edicion_categoria(
    categoria_id: int,
    request: Request,
    nombre: str = Form(...),
    db: Session = Depends(get_db),
):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")

    categoria = db.query(models.Categoria).filter(models.Categoria.id == categoria_id).first()
    if categoria:
        categoria.nombre = nombre
        db.commit()

    return RedirectResponse("/admin/categorias", status_code=303)


@app.post("/admin/marcas/nueva")
def crear_marca(request: Request, nombre: str = Form(...), db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    existe = db.query(models.Marca).filter(models.Marca.nombre == nombre).first()
    if not existe:
        db.add(models.Marca(nombre=nombre))
        db.commit()
    return RedirectResponse("/admin/categorias", status_code=303)


@app.get("/admin/eliminar-marca/{marca_id}")
def eliminar_marca(marca_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")

    tiene_productos = db.query(models.Producto).filter(models.Producto.marca_id == marca_id).first()
    if tiene_productos:
        return RedirectResponse(
            "/admin/categorias?error=No se puede eliminar: esa marca tiene productos cargados. Reasignalos a otra marca primero.",
            status_code=303,
        )

    marca = db.query(models.Marca).filter(models.Marca.id == marca_id).first()
    if marca:
        db.delete(marca)
        db.commit()
    return RedirectResponse("/admin/categorias", status_code=303)

# NUEVO: editar marca

@app.get("/admin/editar-marca/{marca_id}")
def form_editar_marca(marca_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    marca = db.query(models.Marca).filter(models.Marca.id == marca_id).first()
    return templates.TemplateResponse(request, "admin/editar_marca.html", {"marca": marca})


@app.post("/admin/editar-marca/{marca_id}")
def guardar_edicion_marca(
    marca_id: int,
    request: Request,
    nombre: str = Form(...),
    db: Session = Depends(get_db),
):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    marca = db.query(models.Marca).filter(models.Marca.id == marca_id).first()
    if marca:
        marca.nombre = nombre
        db.commit()
    return RedirectResponse("/admin/categorias", status_code=303)


# ============================================================
# ADMIN: SERVICIOS (sin carrito, mismo patrón que productos)
# ============================================================

@app.get("/admin/servicios")
def admin_servicios(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    servicios = db.query(models.Servicio).all()
    return templates.TemplateResponse(
        request, "admin/panel_servicios.html", {"grupos": agrupar_por_categoria(servicios)}
    )


@app.get("/admin/nuevo-servicio")
def form_nuevo_servicio(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    categorias = db.query(models.CategoriaServicio).all()
    return templates.TemplateResponse(request, "admin/nuevo_servicio.html", {"categorias": categorias})


@app.post("/admin/nuevo-servicio")
def crear_servicio(
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(""),
    categoria_id: int = Form(...),
    disponible: str = Form("true"),
    imagenes: List[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")

    nuevo = models.Servicio(
        nombre=nombre,
        descripcion=descripcion,
        categoria_id=categoria_id,
        disponible=(disponible == "true"),
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    guardar_imagenes_servicio(nuevo, imagenes, db)

    return RedirectResponse("/admin/servicios", status_code=303)


@app.get("/admin/editar-servicio/{servicio_id}")
def form_editar_servicio(servicio_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    servicio = db.query(models.Servicio).filter(models.Servicio.id == servicio_id).first()
    categorias = db.query(models.CategoriaServicio).all()
    return templates.TemplateResponse(
        request, "admin/editar_servicio.html", {"servicio": servicio, "categorias": categorias}
    )


@app.post("/admin/editar-servicio/{servicio_id}")
def guardar_edicion_servicio(
    servicio_id: int,
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(""),
    categoria_id: int = Form(...),
    disponible: str = Form("true"),
    imagenes: List[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")

    servicio = db.query(models.Servicio).filter(models.Servicio.id == servicio_id).first()
    servicio.nombre = nombre
    servicio.descripcion = descripcion
    servicio.categoria_id = categoria_id
    servicio.disponible = (disponible == "true")

    guardar_imagenes_servicio(servicio, imagenes, db)

    db.commit()
    return RedirectResponse("/admin/servicios", status_code=303)


@app.get("/admin/eliminar-imagen-servicio/{imagen_id}")
def eliminar_imagen_servicio(imagen_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    imagen = db.query(models.ImagenServicio).filter(models.ImagenServicio.id == imagen_id).first()
    if imagen:
        servicio_id = imagen.servicio_id
        db.delete(imagen)
        db.commit()
        return RedirectResponse(f"/admin/editar-servicio/{servicio_id}", status_code=303)
    return RedirectResponse("/admin/servicios", status_code=303)


@app.get("/admin/eliminar-servicio/{servicio_id}")
def eliminar_servicio(servicio_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    servicio = db.query(models.Servicio).filter(models.Servicio.id == servicio_id).first()
    if servicio:
        db.delete(servicio)
        db.commit()
    return RedirectResponse("/admin/servicios", status_code=303)


@app.get("/admin/toggle-servicio/{servicio_id}")
def toggle_servicio(servicio_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    servicio = db.query(models.Servicio).filter(models.Servicio.id == servicio_id).first()
    if servicio:
        servicio.disponible = not servicio.disponible
        db.commit()
    return RedirectResponse("/admin/servicios", status_code=303)


# ============================================================
# ADMIN: CATEGORÍAS DE SERVICIOS
# ============================================================

@app.post("/admin/categorias-servicios/nueva")
def crear_categoria_servicio(request: Request, nombre: str = Form(...), db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    existe = db.query(models.CategoriaServicio).filter(models.CategoriaServicio.nombre == nombre).first()
    if not existe:
        db.add(models.CategoriaServicio(nombre=nombre))
        db.commit()
    return RedirectResponse("/admin/categorias", status_code=303)


@app.get("/admin/eliminar-categoria-servicio/{categoria_id}")
def eliminar_categoria_servicio(categoria_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")

    tiene_servicios = db.query(models.Servicio).filter(models.Servicio.categoria_id == categoria_id).first()
    if tiene_servicios:
        return RedirectResponse(
            "/admin/categorias?error=No se puede eliminar: esa categoria tiene servicios cargados. Reasignalos a otra categoria primero.",
            status_code=303,
        )

    categoria = db.query(models.CategoriaServicio).filter(models.CategoriaServicio.id == categoria_id).first()
    if categoria:
        db.delete(categoria)
        db.commit()
    return RedirectResponse("/admin/categorias", status_code=303)

 # NUEVO: editar categoría de servicio

@app.get("/admin/editar-categoria-servicio/{categoria_id}")
def form_editar_categoria_servicio(categoria_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    categoria = db.query(models.CategoriaServicio).filter(models.CategoriaServicio.id == categoria_id).first()
    return templates.TemplateResponse(request, "admin/editar_categoria_servicio.html", {"categoria": categoria})


@app.post("/admin/editar-categoria-servicio/{categoria_id}")
def guardar_edicion_categoria_servicio(
    categoria_id: int,
    request: Request,
    nombre: str = Form(...),
    db: Session = Depends(get_db),
):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    categoria = db.query(models.CategoriaServicio).filter(models.CategoriaServicio.id == categoria_id).first()
    if categoria:
        categoria.nombre = nombre
        db.commit()
    return RedirectResponse("/admin/categorias", status_code=303)


# ============================================================
# PROFESIONALES: registro, login y salir
# ============================================================

# Extensión del archivo -> tipo que se le avisa al navegador al mostrarlo
TIPOS_DIPLOMA = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                 "webp": "image/webp", "pdf": "application/pdf"}
MAX_DIPLOMA_BYTES = 5 * 1024 * 1024  # 5 MB


@app.get("/profesionales/registro")
def form_registro_profesional(request: Request, db: Session = Depends(get_db)):
    if not PROFESIONALES_ACTIVO:
        return RedirectResponse("/", status_code=303)
    # Si ya está logueada no tiene sentido registrarse de nuevo: directo al catálogo
    if profesional_actual(request, db):
        return RedirectResponse("/productos", status_code=303)
    return templates.TemplateResponse(request, "profesionales/registro.html", {"error": None, "ok": False})


@app.post("/profesionales/registro")
def registrar_profesional(
    request: Request,
    nombre: str = Form(...),
    email: str = Form(...),
    telefono: str = Form(...),
    password: str = Form(...),
    diploma: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # El POST también se bloquea: alguien podría mandar el formulario sin pasar por la página
    if not PROFESIONALES_ACTIVO:
        return RedirectResponse("/", status_code=303)

    def error(mensaje):
        return templates.TemplateResponse(
            request, "profesionales/registro.html", {"error": mensaje, "ok": False}
        )

    email = email.strip().lower()  # "Ana@Gmail.com " y "ana@gmail.com" son la misma cuenta
    if len(password) < 8:
        return error("La contraseña tiene que tener al menos 8 caracteres.")
    if db.query(models.Profesional).filter(models.Profesional.email == email).first():
        return error("Ya hay una cuenta registrada con ese email.")

    extension = (diploma.filename or "").split(".")[-1].lower()
    if extension not in TIPOS_DIPLOMA:
        return error("El diploma tiene que ser una foto (JPG, PNG, WEBP) o un PDF.")
    # Leemos 1 byte de más: si lo consigue, el archivo se pasa del límite
    contenido = diploma.file.read(MAX_DIPLOMA_BYTES + 1)
    if len(contenido) > MAX_DIPLOMA_BYTES:
        return error("El archivo del diploma pesa más de 5 MB.")

    db.add(models.Profesional(
        nombre=nombre.strip(),
        email=email,
        telefono=telefono.strip(),
        password_hash=hashear_password(password),
        diploma_archivo=contenido,
        diploma_tipo=TIPOS_DIPLOMA[extension],
    ))
    db.commit()
    return templates.TemplateResponse(request, "profesionales/registro.html", {"error": None, "ok": True})


@app.get("/profesionales/login")
def form_login_profesional(request: Request, db: Session = Depends(get_db)):
    if not PROFESIONALES_ACTIVO:
        return RedirectResponse("/", status_code=303)
    # Si ya está logueada (por ej. tocó "Soy profesional" desde el inicio), directo al catálogo
    if profesional_actual(request, db):
        return RedirectResponse("/productos", status_code=303)
    return templates.TemplateResponse(request, "profesionales/login.html", {"error": None})


@app.post("/profesionales/login")
def login_profesional(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    if not PROFESIONALES_ACTIVO:
        return RedirectResponse("/", status_code=303)

    def error(mensaje):
        return templates.TemplateResponse(request, "profesionales/login.html", {"error": mensaje})

    profesional = db.query(models.Profesional).filter(
        models.Profesional.email == email.strip().lower()
    ).first()
    # Mismo mensaje si no existe el email o si la clave está mal:
    # así nadie puede averiguar qué emails están registrados.
    if not profesional or not verificar_password(password, profesional.password_hash):
        return error("Email o contraseña incorrectos.")
    # La clave está bien, pero falta que vos la apruebes:
    if profesional.estado == "pendiente":
        return error("Tu cuenta todavía está en revisión. Te avisamos cuando esté aprobada.")
    if profesional.estado == "rechazada":
        return error("Tu cuenta no fue aprobada. Si creés que es un error, escribinos por WhatsApp.")

    request.session["profesional_id"] = profesional.id
    return RedirectResponse("/productos", status_code=303)


@app.get("/profesionales/salir")
def logout_profesional(request: Request):
    request.session.pop("profesional_id", None)
    return RedirectResponse("/productos", status_code=303)


# ============================================================
# ADMIN: aprobar o rechazar profesionales
# ============================================================

@app.get("/admin/profesionales")
def admin_profesionales(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    # Las pendientes primero, y dentro de cada estado las más nuevas arriba
    orden = {"pendiente": 0, "aprobada": 1, "rechazada": 2}
    profesionales = sorted(
        db.query(models.Profesional).all(),
        key=lambda p: (orden.get(p.estado, 3), -p.id),
    )
    return templates.TemplateResponse(request, "admin/profesionales.html", {"profesionales": profesionales})


@app.get("/admin/profesionales/{profesional_id}/diploma")
def ver_diploma(profesional_id: int, request: Request, db: Session = Depends(get_db)):
    """Sirve el diploma desde la base. Solo para el admin: no hay URL pública."""
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    profesional = db.query(models.Profesional).filter(models.Profesional.id == profesional_id).first()
    if not profesional:
        return RedirectResponse("/admin/profesionales")
    # Recién acá se trae la foto de la base (por el deferred() del modelo)
    return Response(content=profesional.diploma_archivo, media_type=profesional.diploma_tipo)


def cambiar_estado_profesional(profesional_id: int, estado: str, request: Request, db: Session):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    profesional = db.query(models.Profesional).filter(models.Profesional.id == profesional_id).first()
    if profesional:
        profesional.estado = estado
        db.commit()
    return RedirectResponse("/admin/profesionales", status_code=303)


@app.post("/admin/profesionales/{profesional_id}/aprobar")
def aprobar_profesional(profesional_id: int, request: Request, db: Session = Depends(get_db)):
    return cambiar_estado_profesional(profesional_id, "aprobada", request, db)


@app.post("/admin/profesionales/{profesional_id}/rechazar")
def rechazar_profesional(profesional_id: int, request: Request, db: Session = Depends(get_db)):
    return cambiar_estado_profesional(profesional_id, "rechazada", request, db)
