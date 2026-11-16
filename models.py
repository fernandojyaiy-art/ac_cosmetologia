from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, LargeBinary
from sqlalchemy.orm import relationship, deferred

from database import Base


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)

    productos = relationship("Producto", back_populates="categoria")


class Marca(Base):
    __tablename__ = "marcas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)

    productos = relationship("Producto", back_populates="marca")


class CategoriaServicio(Base):
    __tablename__ = "categorias_servicios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)

    servicios = relationship("Servicio", back_populates="categoria")


class Servicio(Base):
    __tablename__ = "servicios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)  # incluye precios, como en el sitio original
    imagen = Column(String, nullable=True)  # portada: se mantiene sincronizada con la primera de "imagenes"
    disponible = Column(Boolean, default=True)

    categoria_id = Column(Integer, ForeignKey("categorias_servicios.id"), nullable=False)
    categoria = relationship("CategoriaServicio", back_populates="servicios")

    imagenes = relationship(
        "ImagenServicio",
        back_populates="servicio",
        order_by="ImagenServicio.orden",
        cascade="all, delete-orphan",
    )


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)

    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    precio = Column(Float, nullable=False)
    imagen = Column(String, nullable=True)  # portada: se mantiene sincronizada con la primera de "imagenes"
    disponible = Column(Boolean, default=True)
    stock = Column(Integer, default=0, nullable=False)  # cantidad disponible, la carga Anto a mano

    # --- Precios al público ---
    # "precio" de arriba es el PRECIO DE LISTA (débito/crédito).
    precio_contado = Column(Float, nullable=True)  # efectivo/transferencia; vacío = solo se muestra el de lista

    # --- Distribuidora Libra ---
    precio_profesional = Column(Float, nullable=True)  # solo lo ven profesionales aprobadas
    costo = Column(Float, nullable=True)  # precio distribuidor: lo ve SOLO el panel admin, nunca el catalogo
    solo_profesionales = Column(Boolean, default=False, nullable=False)  # productos de gabinete (ej: crema x 4,9 kg)

    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    marca_id = Column(Integer, ForeignKey("marcas.id"), nullable=True)

    categoria = relationship("Categoria", back_populates="productos")
    marca = relationship("Marca", back_populates="productos")

    imagenes = relationship(
        "ImagenProducto",
        back_populates="producto",
        order_by="ImagenProducto.orden",
        cascade="all, delete-orphan",
    )


class ImagenProducto(Base):
    __tablename__ = "imagenes_productos"

    id = Column(Integer, primary_key=True, index=True)
    ruta_imagen = Column(String, nullable=False)
    orden = Column(Integer, default=0)

    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    producto = relationship("Producto", back_populates="imagenes")


class ImagenServicio(Base):
    __tablename__ = "imagenes_servicios"

    id = Column(Integer, primary_key=True, index=True)
    ruta_imagen = Column(String, nullable=False)
    orden = Column(Integer, default=0)

    servicio_id = Column(Integer, ForeignKey("servicios.id"), nullable=False)
    servicio = relationship("Servicio", back_populates="imagenes")


class Profesional(Base):
    """Cosmetologa/esteticista que se registra para comprar a precio profesional.
    Arranca en estado "pendiente"; Mati la aprueba desde el panel despues de ver el diploma."""
    __tablename__ = "profesionales"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    telefono = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)  # NUNCA la contraseña en texto plano

    # "pendiente" | "aprobada" | "rechazada"
    estado = Column(String, default="pendiente", nullable=False)
    creada_en = Column(DateTime, default=datetime.utcnow, nullable=False)

    # La foto del diploma se guarda DENTRO de la base (no en static/uploads),
    # asi no queda accesible por URL publica y persiste en Postgres sin depender del Volume.
    # deferred(): no se trae de la base salvo que la pidas explicitamente,
    # para que listar profesionales no cargue todas las fotos en memoria.
    diploma_archivo = deferred(Column(LargeBinary, nullable=False))
    diploma_tipo = Column(String, nullable=False)  # ej: "image/jpeg", para servirla bien despues
