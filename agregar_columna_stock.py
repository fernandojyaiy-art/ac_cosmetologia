"""
Migracion: agrega la columna 'stock' a la tabla "productos" que YA EXISTE.
Hace falta porque Base.metadata.create_all() (la linea que tiene main.py)
solo crea tablas nuevas -- no modifica una tabla que ya existe agregandole
una columna. Por eso esto se corre aparte, una sola vez.

Funciona tanto contra SQLite (local) como contra Postgres (produccion),
usando el mismo engine que ya tiene database.py.

Uso local (con el venv activado, SIN nada seteado en DATABASE_URL):
    python agregar_columna_stock.py

Uso en produccion (mismo mecanismo del tunel que ya usamos para las fotos):
    railway connect Postgres --tunnel-only        (dejar esa terminal abierta)
    # en OTRA terminal:
    $env:DATABASE_URL="postgresql://postgres:TU_PASSWORD@127.0.0.1:EL_PUERTO_DEL_TUNEL/railway"
    python agregar_columna_stock.py
    Remove-Item Env:DATABASE_URL   (al terminar, para no dejarla pegada)

Es seguro correrlo mas de una vez: si la columna ya existe, avisa y no
rompe nada.
"""
from sqlalchemy import text
from database import engine

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE productos ADD COLUMN stock INTEGER NOT NULL DEFAULT 0"))
        conn.commit()
        print("Columna 'stock' agregada correctamente a la tabla productos.")
    except Exception as e:
        mensaje = str(e).lower()
        if "duplicate column" in mensaje or "already exists" in mensaje:
            print("La columna 'stock' ya existia, no se hizo nada (todo bien).")
        else:
            raise