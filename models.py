from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship

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