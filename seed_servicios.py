# seed_servicios.py — correr UNA sola vez: python seed_servicios.py
# Migra las categorías y servicios que ya tenías escritos a mano en serv.html

from database import SessionLocal, Base, engine
import models

Base.metadata.create_all(bind=engine)
db = SessionLocal()

categorias_nombres = [
    "Limpiezas faciales",
    "Renovación celular y exfoliación profesional",
    "Tratamientos con aparatología",
    "Tratamientos de labios",
    "Tratamientos con exosomas (premium)",
]
categorias = {}
for nombre in categorias_nombres:
    existente = db.query(models.CategoriaServicio).filter(models.CategoriaServicio.nombre == nombre).first()
    if not existente:
        existente = models.CategoriaServicio(nombre=nombre)
        db.add(existente)
        db.commit()
        db.refresh(existente)
    categorias[nombre] = existente

servicios_iniciales = [
    {
        "nombre": "Limpieza facial básica",
        "categoria": "Limpiezas faciales",
        "imagen": "limpieza_facial.jpg",
        "descripcion": "Cuidado esencial para limpiar suavemente tu piel, manteniéndola fresca y saludable.\nIncluye: higiene, exfoliación, extracción, mascara e hidratación\n$37.500/$30.000 efectivo",
    },
    {
        "nombre": "Limpieza facial profunda",
        "categoria": "Limpiezas faciales",
        "imagen": "limpieza_facial_hombres.jpeg",
        "descripcion": "Además de los cuidados tradicionales de una limpieza facial combinamos enzimas que disuelven impurezas y ondas eléctricas de alta frecuencia para estimular la circulación y mejorar la textura de tu piel.\nIncluye: higiene, exfoliación enzimática o mecánica, extracción profunda, alta frecuencia, mascarilla, hidratación y protección solar\n$43.750/$35.000 efectivo",
    },
    {
        "nombre": "Cuello y escote",
        "categoria": "Limpiezas faciales",
        "imagen": None,
        "descripcion": "Incluye: exfoliación, mascara, activos hidratantes y reafirmantes según el tipo de piel\n$28.750/$23.000 efectivo",
    },
    {
        "nombre": "Espalda y glúteos",
        "categoria": "Limpiezas faciales",
        "imagen": "aparotologia.jpeg",
        "descripcion": "Limpieza profunda que elimina impurezas y células muertas, ayudando a mejorar la textura de la piel.\n$31.250/$25.000 efectivo",
    },
    {
        "nombre": "Peeling químico personalizado",
        "categoria": "Renovación celular y exfoliación profesional",
        "imagen": "peeling.jpeg",
        "descripcion": "Ideal para manchas de acné, textura irregular o líneas finas.\nIncluye: limpieza, aplicación de ácidos específicos y mascara post peeling.\n1 Sesión $43.750/$35.000 efectivo\n3 Sesiones $118.750/$95.000 efectivo",
    },
    {
        "nombre": "Peeling de algas",
        "categoria": "Renovación celular y exfoliación profesional",
        "imagen": "algas.jpeg",
        "descripcion": "Se puede realizar todo el año y es apto para embarazadas. Estimula la renovación celular profunda con ingredientes naturales.\n1 Sesión $43.750/$35.000 efectivo",
    },
    {
        "nombre": "Dermaplaning",
        "categoria": "Renovación celular y exfoliación profesional",
        "imagen": "dermaplaning.jpeg",
        "descripcion": "Exfoliación suave que elimina células muertas y vello fino, dejando la piel lisa y luminosa.\nIncluye: exfoliación y luminosidad instantánea.\n$43.750/$35.000 efectivo",
    },
    {
        "nombre": "Glow intenso",
        "categoria": "Tratamientos con aparatología",
        "imagen": "foto_aparato.jpeg",
        "descripcion": "Electroporación que aumenta la absorción de activos en la piel, potenciando hidratación y renovación, sumado a mascara LED.\n$43.750/$35.000 efectivo",
    },
    {
        "nombre": "Lifting sin agujas",
        "categoria": "Tratamientos con aparatología",
        "imagen": None,
        "descripcion": "Electroporación + radiofrecuencia para mejorar firmeza y elasticidad de la piel.\nRostro $43.750/$35.000 efectivo\nRostro, cuello y escote $50.000/$40.000 efectivo",
    },
    {
        "nombre": "Acne control",
        "categoria": "Tratamientos con aparatología",
        "imagen": "acnex.jpeg",
        "descripcion": "Desinflama, regula el sebo y mejora brotes con alta frecuencia y mascara LED.\n$43.750/$35.000 efectivo",
    },
    {
        "nombre": "Renovación celular pro (microneedling)",
        "categoria": "Tratamientos con aparatología",
        "imagen": None,
        "descripcion": "Con micro agujas se estimula la producción de colágeno mejorando textura, poros, manchas y líneas finas.\n1 Sesión $43.750/$35.000 efectivo\n3 Sesiones $118.750/$95.000 efectivo",
    },
    {
        "nombre": "Hilos",
        "categoria": "Tratamientos con aparatología",
        "imagen": None,
        "descripcion": "NO APTO CELIACOS. Hilos biodegradables que tensan y revitalizan la piel, mejorando su firmeza.\n$50.000/$40.000 efectivo",
    },
    {
        "nombre": "Hydralips express",
        "categoria": "Tratamientos de labios",
        "imagen": "hydralips.jpg",
        "descripcion": "Hidratación rápida y profunda para labios suaves y voluminosos.\nIncluye: nutrición, exfoliación y bálsamo\n$25.000/$20.000 efectivo",
    },
    {
        "nombre": "Hydralips estándar",
        "categoria": "Tratamientos de labios",
        "imagen": None,
        "descripcion": "Incluye: hidratación profunda y electroporación con ácido hialurónico.\n$31.250/$25.000 efectivo",
    },
    {
        "nombre": "Hydralips con microneedling",
        "categoria": "Tratamientos de labios",
        "imagen": None,
        "descripcion": "Define contorno y mejora textura, hidrata en profundidad y da efecto visual de volumen.\n1 Sesión $37.500/$30.000 efectivo\n3 Sesiones $100.000/$80.000 efectivo",
    },
    {
        "nombre": "Glow detox",
        "categoria": "Tratamientos con exosomas (premium)",
        "imagen": "exosomas.jpeg",
        "descripcion": "Ideal para pieles opacas, con manchas o engrosadas. Renovación total.\nIncluye: higienización, dermaplaning, microneedling con Exosomas, mascara LED, sellado con hidratación y protector solar.\n$62.500/$50.000 efectivo",
    },
    {
        "nombre": "Lift and glow",
        "categoria": "Tratamientos con exosomas (premium)",
        "imagen": None,
        "descripcion": "Rejuvenecimiento facial para pieles con flacidez, líneas finas o pérdida de luminosidad.\nIncluye: higienización, dermaplaning, microneedling con Exosomas, mascara LED, masaje tensor, hidratación y protección solar\n$62.500/$50.000 efectivo",
    },
]

for datos in servicios_iniciales:
    ya_existe = db.query(models.Servicio).filter(models.Servicio.nombre == datos["nombre"]).first()
    if ya_existe:
        continue
    imagen_path = f"/static/imagenes/{datos['imagen']}" if datos["imagen"] else None
    db.add(models.Servicio(
        nombre=datos["nombre"],
        descripcion=datos["descripcion"],
        categoria_id=categorias[datos["categoria"]].id,
        imagen=imagen_path,
        disponible=True,
    ))

db.commit()
db.close()
print("Listo. Servicios cargados.")