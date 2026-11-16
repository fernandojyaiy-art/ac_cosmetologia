"""
Migracion: agrega a la tabla "productos" (que YA EXISTE) las columnas nuevas:
  - de la distribuidora Libra: precio_profesional, costo y solo_profesionales
  - precio_contado (efectivo/transferencia; el precio de lista sigue siendo "precio")

Mismo motivo que agregar_columna_stock.py: Base.metadata.create_all() solo crea
tablas nuevas (por eso "profesionales" ya se creo sola al levantar el server),
pero NO le agrega columnas a una tabla que ya existe.

Uso local (con el venv activado, SIN nada seteado en DATABASE_URL):
    python agregar_columnas_profesional.py

Uso en produccion (mismo mecanismo del tunel que usamos con stock):
    railway connect Postgres --tunnel-only        (dejar esa terminal abierta)
    # en OTRA terminal:
    $env:DATABASE_URL="postgresql://postgres:TU_PASSWORD@127.0.0.1:EL_PUERTO_DEL_TUNEL/railway"
    python agregar_columnas_profesional.py
    Remove-Item Env:DATABASE_URL   (al terminar, para no dejarla pegada)

Es seguro correrlo mas de una vez: las columnas que ya existen se saltean.
"""
from sqlalchemy import text
from database import engine

# (nombre de la columna, definicion SQL)
# - Los precios van sin NOT NULL: un producto puede no tener precio profesional cargado todavia.
# - solo_profesionales lleva DEFAULT FALSE: asi todos los productos que ya existen
#   quedan visibles para el publico, igual que hasta hoy.
COLUMNAS = [
    ("precio_profesional", "FLOAT"),
    ("costo", "FLOAT"),
    ("solo_profesionales", "BOOLEAN NOT NULL DEFAULT FALSE"),
    ("precio_contado", "FLOAT"),
]

for nombre, definicion in COLUMNAS:
    try:
        # engine.begin() abre una transaccion y hace commit solo si no hubo error.
        # Va una por columna porque en Postgres, si un ALTER falla, la transaccion
        # entera queda "rota" y los siguientes tambien fallarian.
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE productos ADD COLUMN {nombre} {definicion}"))
        print(f"Columna '{nombre}' agregada.")
    except Exception as e:
        mensaje = str(e).lower()
        if "duplicate column" in mensaje or "already exists" in mensaje:
            print(f"La columna '{nombre}' ya existia, se saltea (todo bien).")
        else:
            raise

print("Migracion terminada.")
