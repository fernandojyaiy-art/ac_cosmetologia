import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# En tu compu (local) no existe DATABASE_URL, así que usa SQLite como siempre.
# En Railway, al agregar el servicio de PostgreSQL, Railway inyecta DATABASE_URL
# solo -- ahí se conecta a Postgres en vez de al archivo estetica.db.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./estetica.db")

# Railway (y otros proveedores) a veces dan la URL como "postgres://",
# pero las versiones nuevas de SQLAlchemy exigen "postgresql://". Lo corregimos acá.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# connect_args con check_same_thread solo hace falta para SQLite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()