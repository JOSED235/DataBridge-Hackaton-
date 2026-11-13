"""Genera las 3 diapositivas de la entrega (guía oficial: arquitectura, respuesta, mapa).

Las cifras son las de las tablas gold validadas en Databricks (docs/ENTREGA.md).
La imagen del mapa se pasa como argumento (pantallazo del visor con datos oficiales).
La salida contiene un mapa derivado de los datos oficiales: va a data/oficiales/salidas/, fuera de git.

Uso:  python scripts/generar_presentacion.py [ruta_mapa.png]
"""
import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

RAIZ = Path(__file__).resolve().parent.parent
MAPA = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "data" / "oficiales" / "salidas" / "mapa.png"
SALIDA = RAIZ / "data" / "oficiales" / "salidas" / "presentacion_icesixuao.pptx"

FONDO, PANEL, LINEA = "0E1013", "171B21", "2A3039"
TEXTO, TENUE, ACENTO, NARANJA, VERDE, AZUL = "ECEAE5", "9AA1AB", "FF5A36", "FF9500", "3ECF8E", "5AAADC"
FUENTE = "Calibri"


def rgb(h):
    return RGBColor.from_string(h)


prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANCO = prs.slide_layouts[6]


def fondo(slide):
    f = slide.background.fill
    f.solid()
    f.fore_color.rgb = rgb(FONDO)


def caja(slide, x, y, w, h, color=PANEL, borde=LINEA, forma=MSO_SHAPE.RECTANGLE, nombre=None):
    s = slide.shapes.add_shape(forma, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = rgb(color)
    if borde:
        s.line.color.rgb = rgb(borde)
        s.line.width = Pt(0.75)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    if nombre:
        s.name = nombre
    return s


def texto(slide, x, y, w, h, parrafos, ancla=MSO_ANCHOR.TOP, margen=0.0, nombre=None):
    """parrafos: lista de (texto | [(texto, opciones)], opciones_parrafo)."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if nombre:
        tb.name = nombre
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = ancla
    for lado in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, lado, Inches(margen))
    for i, (contenido, op) in enumerate(parrafos):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = op.get("align", PP_ALIGN.LEFT)
        p.space_after = Pt(op.get("despues", 0))
        p.space_before = Pt(op.get("antes", 0))
        p.line_spacing = op.get("interlineado", 1.0)
        runs = contenido if isinstance(contenido, list) else [(contenido, {})]
        for t, ro in runs:
            r = p.add_run()
            r.text = t
            f = r.font
            f.name = FUENTE
            f.size = Pt(ro.get("tam", op.get("tam", 14)))
            f.bold = ro.get("negrita", op.get("negrita", False))
            f.italic = ro.get("cursiva", False)
            f.color.rgb = rgb(ro.get("color", op.get("color", TEXTO)))
    return tb


def titulo(slide, kicker, frase):
    texto(slide, 0.5, 0.32, 12.3, 0.3, [(kicker.upper(), {"tam": 12, "negrita": True, "color": ACENTO})], nombre="Kicker")
    texto(slide, 0.5, 0.6, 12.3, 0.75, [(frase, {"tam": 30, "negrita": True})], nombre="Título")


def pie(slide, t):
    texto(slide, 0.5, 7.02, 12.3, 0.3, [(t, {"tam": 10, "color": TENUE})], nombre="Pie")


# ------------------------------------------------------------------------------------------------
# Diapositiva 1: arquitectura y fuentes
# ------------------------------------------------------------------------------------------------
s1 = prs.slides.add_slide(BLANCO)
fondo(s1)
titulo(s1, "1 · Arquitectura bronze → silver → gold", "De 5.146 polígonos satelitales a una lista de inspección")

capas = [
    ("BRONZE", "Guardar tal como llegó", AZUL, [
        "Datosprediales.json: 5.146 × 21, todo como texto y con los nulos y espacios intactos",
        "15 capas externas sin modificar (GEM, USGS, SGC, OSM)",
        "Geometría en WKT sin redondear: redondear creaba 13 polígonos inválidos",
    ]),
    ("SILVER", "Limpiar y cruzar", NARANJA, [
        "Llave OBJECTID (ID_PREDIO tiene 1.509 nulos)",
        "NPISOS = 0 → predio sin construcción registrada (1.234): se conserva, sin pisos",
        "4 polígonos reparados; área en m² (EPSG:9377)",
        "Cada edificio cruzado con GEM (98,9 %, ≤ 15 m), suelo, ShakeMap y OSM",
    ]),
    ("GOLD", "Responder la pregunta", ACENTO, [
        "Índice 0–1 por edificio y prioridad por percentil",
        "Ranking de comunas por percentil 90",
        "Chi-cuadrado con ajuste Holm: ¿qué se asocia con el daño?",
        "Sensibilidad: 7 escenarios frente al base",
    ]),
]
x0, ancho, sep = 0.5, 3.95, 0.225
for i, (nom, sub, color, items) in enumerate(capas):
    x = x0 + i * (ancho + sep)
    caja(s1, x, 1.55, ancho, 2.85, nombre=f"Capa {nom}")
    texto(s1, x + 0.25, 1.7, ancho - 0.5, 0.3, [(nom, {"tam": 13, "negrita": True, "color": color})])
    texto(s1, x + 0.25, 1.98, ancho - 0.5, 0.35, [(sub, {"tam": 17, "negrita": True})])
    texto(s1, x + 0.25, 2.45, ancho - 0.5, 1.9,
          [(t, {"tam": 12.5, "despues": 5, "color": "D5D8DD"}) for t in items])
    if i < 2:
        flecha = s1.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + ancho + 0.01), Inches(2.82), Inches(0.2), Inches(0.3))
        flecha.fill.solid(); flecha.fill.fore_color.rgb = rgb(TENUE); flecha.line.fill.background()

texto(s1, 0.5, 4.6, 12.3, 0.3, [("FUENTES EXTERNAS: QUÉ APORTA CADA UNA QUE LOS DATOS BASE NO DICEN", {"tam": 12, "negrita": True, "color": ACENTO})])
fuentes = [
    ("GEM TREQ · exposición", "Año, estrato, uso, ocupantes y vulnerabilidad de cada edificio (catastro 2021, censo 2018)", "Población y vulnerabilidad"),
    ("GEM TREQ · microzonas", "Microzonificación INGEOMINAS-DAGMA 2005: amplificación del suelo y licuación", "Suelo ante la réplica"),
    ("USGS ShakeMap + SGC", "MMI 6,4–7,1 y PGA 0,19–0,23 g en los edificios; validado con el acelerógrafo RAC2C (6,9)", "Sacudida recibida"),
    ("USGS réplicas", "67 réplicas M ≥ 4 hasta el 3-nov; 47 en septiembre", "La amenaza sigue"),
    ("OpenStreetMap", "439 centros de salud, bomberos y 4.070 tramos de vías principales", "Servicios urbanos"),
]
anchoF, sepF = 2.38, 0.1
for i, (nom, que, para) in enumerate(fuentes):
    x = 0.5 + i * (anchoF + sepF)
    caja(s1, x, 4.98, anchoF, 1.9, nombre=f"Fuente {i + 1}")
    texto(s1, x + 0.15, 5.08, anchoF - 0.3, 1.75, [
        (nom, {"tam": 13, "negrita": True, "despues": 4}),
        (que, {"tam": 11, "color": "C9CDD3", "despues": 6}),
        (f"→ {para}", {"tam": 11, "negrita": True, "color": VERDE}),
    ])
pie(s1, "Tablas: workspace.default.bronze_icesixuao_* · silver_icesixuao_predios · gold_icesixuao_{predios, comunas, factores, resumen_sensibilidad} (13 tablas). Cruce con GEM por cercanía, no por llave catastral.")
s1.notes_slide.notes_text_frame.text = (
    "(1:15) Organizamos el trabajo en tres capas. En bronze guardamos el archivo tal como llegó: 5.146 predios y 21 columnas, "
    "todo como texto, sin corregir nada, y además 15 capas externas. Descubrimos que redondear la geometría al guardarla creaba "
    "13 polígonos inválidos que no estaban en la fuente, así que la guardamos con precisión completa.\n"
    "En silver tomamos las decisiones de limpieza: OBJECTID como llave porque ID_PREDIO tiene 1.509 nulos; los 1.234 predios con "
    "NPISOS igual a cero son, según la organización, predios sin construcción registrada, así que no les inventamos pisos, pero no "
    "los borramos porque el satélite ve daño en 342 de ellos. Reparamos los 4 polígonos inválidos de la fuente y calculamos el área "
    "en metros. Y cruzamos cada edificio con las fuentes externas.\n"
    "Abajo está lo que aporta cada fuente: el modelo de exposición de GEM nos dice quién vive en cada edificio y qué tan frágil es; "
    "la microzonificación, cómo responde el suelo; el ShakeMap del USGS, cuánto se sacudió, y lo validamos con el acelerógrafo del "
    "Servicio Geológico Colombiano en Cali; el catálogo de réplicas muestra que la amenaza sigue; y OpenStreetMap nos da los servicios.\n"
    "En gold calculamos el índice por edificio, el ranking de comunas y dos pruebas: qué explica el daño y qué tan estable es el ranking."
)

# ------------------------------------------------------------------------------------------------
# Diapositiva 2: la respuesta, en las tres dimensiones
# ------------------------------------------------------------------------------------------------
s2 = prs.slides.add_slide(BLANCO)
fondo(s2)
titulo(s2, "2 · Respuesta a la pregunta", "Unos 5.500 ocupantes modelados en edificios dañados")

# Encabezados de la matriz
texto(s2, 2.35, 1.48, 4.9, 0.3, [("¿QUÉ AFECTACIONES GENERÓ EL SISMO?", {"tam": 12, "negrita": True, "color": ACENTO})])
texto(s2, 7.45, 1.48, 5.4, 0.3, [("¿QUÉ REDUCE EL IMPACTO DE LAS RÉPLICAS?", {"tam": 12, "negrita": True, "color": VERDE})])
filas = [
    ("Infraestructura",
     [("1.354", {"tam": 30, "negrita": True, "color": ACENTO}), ("  predios con daño visible (26 %)", {"tam": 13})],
     "296 con escombros y 1.058 con techo desaparecido (342 sin construcción registrada); 435 sin dato satelital",
     "Inspeccionar primero los 179 de prioridad muy alta: 99 % con daño, 69 % construidos hasta 1985. Empezar por la comuna 3: 2 de cada 3 edificios son de 1985 o antes"),
    ("Población",
     [("5.494", {"tam": 30, "negrita": True, "color": ACENTO}), ("  ocupantes modelados", {"tam": 13})],
     "GEM (censo 2018), cada registro contado una vez; 6.950 sumando por predio. Más de la mitad en la comuna 19. Otros 2.298 en edificios sin dato",
     "Verificar en terreno los 435 edificios sin dato y los 342 predios sin construcción registrada con daño. A mediano plazo, reforzar el parque construido hasta 1985 (Japón y Chile)"),
    ("Servicios urbanos",
     [("626", {"tam": 30, "negrita": True, "color": ACENTO}), ("  predios dañados a < 200 m de un centro de salud", {"tam": 13})],
     "430 a más de 1 km de urgencias (solo 23 de 439 centros de OSM las declaran); 5 podrían bloquear una vía principal",
     "Revisar primero los dañados junto a centros de salud y vías principales, para mantener el acceso de ambulancias y bomberos durante la próxima réplica"),
]
y = 1.82
for nom, cifra, detalle, accion in filas:
    caja(s2, 0.5, y, 1.7, 1.15, color="1E232B", nombre=f"Fila {nom}")
    texto(s2, 0.62, y, 1.54, 1.15, [(nom, {"tam": 13, "negrita": True})], ancla=MSO_ANCHOR.MIDDLE)
    caja(s2, 2.3, y, 5.0, 1.15)
    texto(s2, 2.45, y + 0.05, 4.75, 1.05, [(cifra, {"despues": 2}), (detalle, {"tam": 11.5, "color": "C9CDD3"})], ancla=MSO_ANCHOR.MIDDLE)
    caja(s2, 7.4, y, 5.43, 1.15)
    texto(s2, 7.55, y + 0.05, 5.15, 1.05, [(accion, {"tam": 12.5, "color": "DDE0E4"})], ancla=MSO_ANCHOR.MIDDLE)
    y += 1.25

# Hallazgo y evidencia
caja(s2, 0.5, 5.65, 7.7, 1.25, color="22191A", borde="5A2A22", nombre="Hallazgo")
texto(s2, 0.7, 5.72, 7.35, 1.15, [
    ("HALLAZGO", {"tam": 11, "negrita": True, "color": ACENTO, "despues": 3}),
    ([("El daño satelital no muestra un patrón claro: ", {"negrita": True}),
      ("con esta muestra no detectamos asociación con época, uso, suelo, licuación ni comuna (menor p ajustado por Holm 0,27; V de Cramér ≤ 0,06). No prueba que no influyan, pero la señal sola no basta para priorizar.", {})],
     {"tam": 12.5}),
], ancla=MSO_ANCHOR.MIDDLE)
caja(s2, 8.4, 5.65, 4.43, 1.25, nombre="Evidencia")
texto(s2, 8.6, 5.72, 4.1, 1.15, [
    ([("40 %", {"tam": 26, "negrita": True, "color": VERDE}), ("  del top 50", {"tam": 13})], {}),
    ("se mantiene si se quitan las fuentes externas: ellas cambian a quién se inspecciona primero", {"tam": 11.5, "color": "C9CDD3"}),
], ancla=MSO_ANCHOR.MIDDLE)
pie(s2, "Límites: el daño es inferencia satelital, no inspección; vulnerabilidad y ocupantes son modelados (GEM); pruebas exploratorias, sin causalidad. Cifras: gold_icesixuao_predios, _comunas, _exposicion_gem, _factores, _resumen_sensibilidad. Priorizar ≠ declarar seguro.")
s2.notes_slide.notes_text_frame.text = (
    "(2:15) Esta diapositiva responde las dos preguntas en las tres dimensiones que pide el reto.\n"
    "Infraestructura: el satélite ve daño en 1.354 de los 5.146 predios, el 26 %: 296 con escombros y 1.058 sin techo; 342 sin construcción registrada. 435 no tienen dato, "
    "y eso no significa que estén bien.\n"
    "Población: cruzando cada edificio con el modelo de exposición de GEM, unos 5.500 ocupantes nocturnos modelados viven en edificios con daño visible, "
    "más de la mitad en la comuna 19. Es un modelo, no un conteo de personas: un registro GEM puede quedar cerca de varios predios.\n"
    "Servicios: 626 predios dañados están a menos de 200 metros de un centro de salud.\n"
    "Antes de recomendar, probamos qué se asocia con el daño, y con esta muestra no detectamos asociación con la época, el suelo ni la comuna. "
    "No decimos que no influyan, pero el daño satelital no muestra un patrón claro, así que no basta para decidir a quién inspeccionar primero. Por eso el índice combina el daño "
    "observado con lo que sí sabemos de cada edificio: qué tan frágil es, cuánta gente tiene, su suelo y su cercanía a salud y vías.\n"
    "De ahí salen las acciones de la columna verde: 179 edificios de prioridad muy alta, casi todos dañados y construidos hasta 1985; "
    "empezar por la comuna 3; verificar en terreno los que no tienen dato; y proteger el acceso a salud y vías.\n"
    "Y la prueba de que las fuentes externas aportan: si las quitamos, solo el 40 % de los 50 edificios más urgentes sigue en la lista.\n"
    "Límite: son inferencias satelitales y modelos; sirven para priorizar, no para declarar un edificio seguro."
)

# ------------------------------------------------------------------------------------------------
# Diapositiva 3: el mapa
# ------------------------------------------------------------------------------------------------
s3 = prs.slides.add_slide(BLANCO)
fondo(s3)
titulo(s3, "3 · El mapa", "Dónde inspeccionar primero ante la próxima réplica")
if MAPA.exists():
    anchoM = 8.6
    altoM = anchoM * 900 / 1600
    pic = s3.shapes.add_picture(str(MAPA), Inches(0.5), Inches(1.55), Inches(anchoM), Inches(altoM))
    pic.name = "Pantallazo del mapa"
    pic.line.color.rgb = rgb(LINEA)
else:
    caja(s3, 0.5, 1.55, 8.6, 4.84, nombre="Espacio para el pantallazo")
    texto(s3, 0.5, 1.55, 8.6, 4.84, [("Pegar aquí el pantallazo del mapa", {"tam": 18, "color": TENUE, "align": PP_ALIGN.CENTER})], ancla=MSO_ANCHOR.MIDDLE)

bloques = [
    ("QUÉ MUESTRA", [
        [("Color = prioridad del índice: ", {"negrita": True}), ("rojo muy alta, naranja alta, amarillo media, gris baja; morado sin dato y azul sin construcción registrada", {})],
        [("Rótulo = comuna y su puesto: ", {"negrita": True}), ("C3 · #1 es la más urgente", {})],
        [("Puntos verdes = salud; líneas = vías principales", {"negrita": True})],
    ]),
    ("POR QUÉ ASÍ", [
        [("Une las dos respuestas en una vista: dónde hubo daño y a quién inspeccionar primero, junto a los servicios que una réplica pondría en riesgo", {})],
    ]),
    ("CÓMO SE HIZO", [
        [("gold_icesixuao_predios y _comunas → GeoJSON (EPSG:4326) → visor propio con MapLibre GL + deck.gl. Al pasar el cursor, cada edificio muestra su ficha: daño, pisos, suelo, índice", {})],
    ]),
]
yb = 1.55
for cab, items in bloques:
    texto(s3, 9.35, yb, 3.5, 0.3, [(cab, {"tam": 11, "negrita": True, "color": ACENTO})])
    tb = texto(s3, 9.35, yb + 0.3, 3.5, 1.5, [(it, {"tam": 12, "despues": 4, "color": "D5D8DD"}) for it in items])
    yb += {"QUÉ MUESTRA": 2.3, "POR QUÉ ASÍ": 1.35}.get(cab, 0)
texto(s3, 0.5, 6.5, 8.6, 0.45, [([("Lectura en 30 segundos: ", {"negrita": True, "color": ACENTO}),
                                   ("los puntos rojos se concentran en las comunas 3 y 9 (puestos 1 y 2) y en el centro de la 19, con la mayor ocupación modelada en edificios dañados.", {})],
                                  {"tam": 12.5})])
pie(s3, "Mapa base © OpenStreetMap, © CARTO. Datos: organización DataBridge Hack (satelital), GEM TREQ, USGS, SGC, OpenStreetMap.")
s3.notes_slide.notes_text_frame.text = (
    "(1:15) El mapa resume la respuesta. Cada edificio tiene el color de su prioridad: rojo los que hay que inspeccionar primero. "
    "Los rótulos dicen la comuna y su puesto en el ranking: la comuna 3 es la primera y la 9 la segunda, por la combinación de daño y "
    "construcción de 1985 o antes. En la 19 está la mayor ocupación modelada en edificios dañados.\n"
    "Encima van los centros de salud y las vías principales, que son los servicios que una réplica pondría en riesgo.\n"
    "Lo construimos desde las tablas gold, exportadas a GeoJSON, en un visor propio con MapLibre y deck.gl; cada edificio muestra su ficha "
    "al pasar el cursor.\n"
    "Cierre: no podemos evitar la próxima réplica, pero sí decidir dónde llegar primero."
)

prs.save(SALIDA)
print(f"Presentación: {SALIDA}")
