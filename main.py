from fastapi import FastAPI, Depends, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
import shutil
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

from database import engine, Base, get_db
import models


os.makedirs("static/uploads", exist_ok=True)

app = FastAPI(title="Tienda Estética")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SECRET_KEY", "clave-desarrollo-estetica")
)

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

Base.metadata.create_all(bind=engine)


@app.get("/")
def inicio():
    return FileResponse("index.html")


@app.get("/servicios")
def ver_servicios(request: Request, db: Session = Depends(get_db)):
    categorias = db.query(models.CategoriaServicio).all()
    return templates.TemplateResponse(request, "servicios.html", {"categorias": categorias})


@app.get("/contacto")
def contacto():
    return FileResponse("contacto-html/contacto.html")


@app.get("/productos")
def ver_productos(request: Request, db: Session = Depends(get_db)):
    categorias = db.query(models.Categoria).all()
    return templates.TemplateResponse(request, "productos.html", {"categorias": categorias})


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
    imagen: UploadFile = File(None),
    disponible: str = Form("true"),
    db: Session = Depends(get_db)
):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")

    ruta_imagen = None
    if imagen and imagen.filename:
        extensiones_permitidas = {"jpg", "jpeg", "png", "webp"}
        extension = imagen.filename.split(".")[-1].lower()
        if extension not in extensiones_permitidas:
            return {"error": f"Archivo no válido. Subí una imagen (jpg, png, webp), no un .{extension}"}
        nombre_archivo = f"{uuid.uuid4()}.{extension}"
        ruta_destino = f"static/uploads/{nombre_archivo}"
        with open(ruta_destino, "wb") as buffer:
            shutil.copyfileobj(imagen.file, buffer)
        ruta_imagen = f"/static/uploads/{nombre_archivo}"

    nuevo_producto = models.Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        categoria_id=categoria_id,
        marca_id=int(marca_id) if marca_id else None,
        imagen=ruta_imagen,
        disponible=(disponible == "true"),
    )
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)

    return RedirectResponse("/admin/panel", status_code=303)


@app.get("/admin/panel")
def ver_panel(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    productos = db.query(models.Producto).all()
    return templates.TemplateResponse(request, "admin/panel.html", {"productos": productos})


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
    disponible: str = Form("true"),
    imagen: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")

    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()

    producto.nombre = nombre
    producto.descripcion = descripcion
    producto.precio = precio
    producto.categoria_id = categoria_id
    producto.marca_id = int(marca_id) if marca_id else None
    producto.disponible = (disponible == "true")

    if imagen and imagen.filename:
        extensiones_permitidas = {"jpg", "jpeg", "png", "webp"}
        extension = imagen.filename.split(".")[-1].lower()
        if extension in extensiones_permitidas:
            nombre_archivo = f"{uuid.uuid4()}.{extension}"
            ruta_destino = f"static/uploads/{nombre_archivo}"
            with open(ruta_destino, "wb") as buffer:
                shutil.copyfileobj(imagen.file, buffer)
            producto.imagen = f"/static/uploads/{nombre_archivo}"

    db.commit()
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


@app.get("/admin/categorias")
def ver_categorias(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")
    categorias = db.query(models.Categoria).all()
    marcas = db.query(models.Marca).all()
    categorias_servicios = db.query(models.CategoriaServicio).all()
    return templates.TemplateResponse(
        request,
        "admin/categorias.html",
        {"categorias": categorias, "marcas": marcas, "categorias_servicios": categorias_servicios}
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
        return RedirectResponse("/admin/categorias", status_code=303)
    categoria = db.query(models.Categoria).filter(models.Categoria.id == categoria_id).first()
    if categoria:
        db.delete(categoria)
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
        return RedirectResponse("/admin/categorias", status_code=303)
    marca = db.query(models.Marca).filter(models.Marca.id == marca_id).first()
    if marca:
        db.delete(marca)
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
    return templates.TemplateResponse(request, "admin/panel_servicios.html", {"servicios": servicios})


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
    imagen: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")

    ruta_imagen = None
    if imagen and imagen.filename:
        extensiones_permitidas = {"jpg", "jpeg", "png", "webp"}
        extension = imagen.filename.split(".")[-1].lower()
        if extension not in extensiones_permitidas:
            return {"error": f"Archivo no válido. Subí una imagen (jpg, png, webp), no un .{extension}"}
        nombre_archivo = f"{uuid.uuid4()}.{extension}"
        ruta_destino = f"static/uploads/{nombre_archivo}"
        with open(ruta_destino, "wb") as buffer:
            shutil.copyfileobj(imagen.file, buffer)
        ruta_imagen = f"/static/uploads/{nombre_archivo}"

    nuevo = models.Servicio(
        nombre=nombre,
        descripcion=descripcion,
        categoria_id=categoria_id,
        imagen=ruta_imagen,
        disponible=(disponible == "true"),
    )
    db.add(nuevo)
    db.commit()
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
    imagen: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    if not request.session.get("logueado"):
        return RedirectResponse("/admin/login")

    servicio = db.query(models.Servicio).filter(models.Servicio.id == servicio_id).first()
    servicio.nombre = nombre
    servicio.descripcion = descripcion
    servicio.categoria_id = categoria_id
    servicio.disponible = (disponible == "true")

    if imagen and imagen.filename:
        extensiones_permitidas = {"jpg", "jpeg", "png", "webp"}
        extension = imagen.filename.split(".")[-1].lower()
        if extension in extensiones_permitidas:
            nombre_archivo = f"{uuid.uuid4()}.{extension}"
            ruta_destino = f"static/uploads/{nombre_archivo}"
            with open(ruta_destino, "wb") as buffer:
                shutil.copyfileobj(imagen.file, buffer)
            servicio.imagen = f"/static/uploads/{nombre_archivo}"

    db.commit()
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
        return RedirectResponse("/admin/categorias", status_code=303)
    categoria = db.query(models.CategoriaServicio).filter(models.CategoriaServicio.id == categoria_id).first()
    if categoria:
        db.delete(categoria)
        db.commit()
    return RedirectResponse("/admin/categorias", status_code=303)