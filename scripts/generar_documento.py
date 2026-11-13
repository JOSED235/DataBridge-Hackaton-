"""Genera el documento Word de la entrega: resumen, decisiones, respuesta, guion, preguntas del jurado y capturas.

El texto se toma de docs/ENTREGA.md y docs/GUION_PRESENTACION.md para que el Word no se desactualice.
La salida incluye el pantallazo del mapa (datos oficiales): va a data/oficiales/salidas/, fuera de git.

Uso:  python scripts/generar_documento.py
"""
from datetime import date
from pathlib import Path
import re

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "data" / "oficiales" / "salidas" / "Entrega_icesixuao.docx"
MAPA = RAIZ / "data" / "oficiales" / "salidas" / "mapa.png"
URL_MAPA = "https://josed235.github.io/DataBridge-Hackaton-/"
URL_REPO = "https://github.com/JOSED235/DataBridge-Hackaton-"
URL_DASHBOARD = "https://dbc-e551f016-0416.cloud.databricks.com/dashboardsv3/01f1dfa29c4c12de9387b316865d1b70/published?o=7474649595883820"
OSCURO, ACENTO, GRIS = RGBColor(0x1E, 0x23, 0x2B), RGBColor(0xC8, 0x3C, 0x1E), RGBColor(0x5A, 0x60, 0x6B)
CAPTURAS = [
    ("capturas/primeracatalog.png", "Catalog de Databricks (workspace.default): tablas bronze_icesixuao_*, copia fiel de los datos oficiales y de las 15 capas externas."),
    ("capturas/segundacatalog.png", "Tablas gold_icesixuao_* (13) y comienzo de las silver_icesixuao_*."),
    ("capturas/terceracatalog.png", "Tablas silver_icesixuao_* (16). En total, 45 tablas en el catálogo."),
]


def seccion_md(ruta, inicio, fin=None):
    """Texto de un archivo Markdown entre el encabezado `inicio` y el siguiente `fin` (sin incluirlos)."""
    t = (RAIZ / ruta).read_text(encoding="utf-8")
    a = t.index(inicio) + len(inicio)
    b = t.index(fin, a) if fin else len(t)
    return t[a:b]


def sombrear(elemento, color):
    pr = elemento.get_or_add_tcPr() if hasattr(elemento, "get_or_add_tcPr") else elemento.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    pr.append(shd)


def texto_md(parrafo, texto, base=None):
    """Agrega texto con **negrita**, *cursiva* y `código` como runs con formato."""
    for trozo in re.split(r"(\*\*.+?\*\*|`[^`]+`|\*[^*\s][^*]*\*)", texto):
        if not trozo:
            continue
        if trozo.startswith("**"):
            run = parrafo.add_run(trozo[2:-2]); run.bold = True
        elif trozo.startswith("`"):
            run = parrafo.add_run(trozo[1:-1]); run.font.name = "Consolas"; run.font.size = Pt(9.5)
        elif trozo.startswith("*"):
            run = parrafo.add_run(trozo[1:-1]); run.italic = True
        else:
            run = parrafo.add_run(trozo)
        if base:
            base(run)
    return parrafo


def bloques_md(doc, md, nivel_h=2):
    """Renderiza párrafos, listas y encabezados de un fragmento Markdown; omite notas internas y separadores."""
    for linea in md.strip().splitlines():
        s = linea.strip()
        if not s or s == "---" or s.startswith(">") or s.startswith("|"):
            continue
        if s.startswith("#"):
            nivel = len(s) - len(s.lstrip("#"))
            doc.add_heading(re.sub(r"^#+\s*", "", s).replace("`", ""), min(nivel_h + nivel - 2, 4))
        elif s.startswith("- "):
            texto_md(doc.add_paragraph(style="List Bullet"), s[2:])
        elif re.match(r"^\d+\.\s", s):
            num, resto = s.split(" ", 1)
            p = texto_md(doc.add_paragraph(), f"**{num}** {resto}")
            p.paragraph_format.left_indent = Cm(0.9 if linea.startswith(" ") else 0.5)
            p.paragraph_format.first_line_indent = Cm(-0.5)
        elif s.startswith("**¿") and s.endswith("**"):
            doc.add_heading(s.strip("*"), nivel_h + 1)
        else:
            texto_md(doc.add_paragraph(), s)


def figura(doc, ruta, pie, ancho=16.0):
    doc.add_picture(str(ruta), width=Cm(ancho))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph(style="Caption")
    p.add_run(pie)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER


def tabla(doc, filas, anchos, encabezado=True):
    t = doc.add_table(rows=0, cols=len(anchos))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, fila in enumerate(filas):
        celdas = t.add_row().cells
        for c, (valor, ancho) in enumerate(zip(fila, anchos)):
            celdas[c].width = Cm(ancho)
            p = celdas[c].paragraphs[0]
            if encabezado and i == 0:
                sombrear(celdas[c]._tc, "1E232B")
                run = p.add_run(valor); run.bold = True; run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            else:
                texto_md(p, valor)
    return t


def enlace(parrafo, url, texto=None):
    rel = parrafo.part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    h = OxmlElement("w:hyperlink"); h.set(qn("r:id"), rel)
    r = OxmlElement("w:r"); rpr = OxmlElement("w:rPr")
    for etiqueta, val in (("w:color", "1F5FBF"), ("w:u", "single")):
        e = OxmlElement(etiqueta); e.set(qn("w:val"), val); rpr.append(e)
    r.append(rpr)
    t = OxmlElement("w:t"); t.text = texto or url; t.set(qn("xml:space"), "preserve"); r.append(t)
    h.append(r); parrafo._p.append(h)


def numero_pagina(parrafo):
    for tipo, texto in (("begin", None), (None, "PAGE"), ("end", None)):
        r = OxmlElement("w:r")
        if tipo:
            f = OxmlElement("w:fldChar"); f.set(qn("w:fldCharType"), tipo); r.append(f)
        else:
            i = OxmlElement("w:instrText"); i.set(qn("xml:space"), "preserve"); i.text = texto; r.append(i)
        parrafo._p.append(r)


def preparar_estilos(doc):
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"; normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(6); normal.paragraph_format.line_spacing = 1.12
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    for nombre, tam, color in (("Title", 26, OSCURO), ("Heading 1", 18, OSCURO), ("Heading 2", 14, ACENTO),
                               ("Heading 3", 12, OSCURO), ("Heading 4", 11, OSCURO)):
        e = doc.styles[nombre]
        e.font.name = "Calibri"; e.font.size = Pt(tam); e.font.bold = True; e.font.color.rgb = color
        for atributo in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):  # el tema pisaría Calibri
            e.element.rPr.rFonts.attrib.pop(qn(atributo), None)
        e.paragraph_format.space_before = Pt(14 if nombre != "Title" else 0)
        e.paragraph_format.space_after = Pt(6); e.paragraph_format.keep_with_next = True
    doc.styles["Caption"].font.size = Pt(9); doc.styles["Caption"].font.color.rgb = GRIS


def preguntas_jurado():
    filas = []
    for linea in seccion_md("docs/GUION_PRESENTACION.md", "## Preguntas probables del jurado").splitlines():
        partes = [c.strip() for c in linea.strip().strip("|").split(" | ")]
        if linea.startswith("| ¿") and len(partes) == 2:
            filas.append(partes)
    return filas


def main():
    doc = Document()
    preparar_estilos(doc)
    s = doc.sections[0]
    s.page_width, s.page_height = Cm(21.59), Cm(27.94)  # carta
    s.left_margin = s.right_margin = Cm(2.2); s.top_margin = s.bottom_margin = Cm(2.0)
    pie = s.footer.paragraphs[0]
    pie.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = pie.add_run("Equipo icesixuao · DataBridge Hack 2026 · página "); run.font.size = Pt(8.5); run.font.color.rgb = GRIS
    numero_pagina(pie)

    # --- Portada ---
    p = doc.add_paragraph(); r = p.add_run("DATABRIDGE HACK 2026 · IEEE COMPUTER SOCIETY, COLOMBIA CHAPTER")
    r.bold = True; r.font.size = Pt(10); r.font.color.rgb = ACENTO
    doc.add_heading("¿Dónde inspeccionar primero ante la próxima réplica?", 0)
    p = doc.add_paragraph(); r = p.add_run("Sismo M7,4 del 10 de agosto de 2026 · Cali · Equipo icesixuao")
    r.font.size = Pt(13); r.font.color.rgb = GRIS
    doc.add_paragraph(f"Documento de sustentación, {date.today():%d-%m-%Y}. La presentación de 3 diapositivas se adjunta aparte.")
    t = tabla(doc, [["Recurso", "Enlace"],
                    ["Mapa interactivo (GitHub Pages)", ""],
                    ["Repositorio del código", ""],
                    ["Dashboard en Databricks (requiere acceso al workspace)", ""],
                    ["Tablas en Databricks", "`workspace.default.{bronze, silver, gold}_icesixuao_*`"]], [6.5, 10.6])
    for fila, url, etiqueta in ((1, URL_MAPA, URL_MAPA), (2, URL_REPO, URL_REPO), (3, URL_DASHBOARD, "Réplicas Cali · icesixuao")):
        enlace(t.rows[fila].cells[1].paragraphs[0], url, etiqueta)
    doc.add_paragraph()
    aviso = doc.add_paragraph()
    sombrear(aviso._p, "FBEDE8")
    texto_md(aviso, "**Advertencia.** Los datos de edificios vienen de imágenes satelitales, no de inspección en terreno: sirven para "
                    "priorizar inspecciones y plantear hipótesis, nunca para declarar una edificación segura o insegura. La ocupación "
                    "de GEM es modelada y se cruza por cercanía: se reporta como \"ocupantes modelados\", no como personas afectadas.")

    # --- 1. Resumen ---
    doc.add_heading("1. Resumen", 1)
    for parrafo in (
        "El USGS registró 67 réplicas de magnitud 4 o más después del sismo del 10 de agosto. Por eso no nos quedamos en describir "
        "el daño: construimos una **lista priorizada de qué edificios inspeccionar primero** ante la próxima réplica.",
        "Organizamos los datos en Databricks en tres capas. En **bronze** guardamos el archivo oficial tal como llegó, junto con 15 "
        "capas abiertas (GEM, USGS, SGC y OpenStreetMap). En **silver** limpiamos y cruzamos cada predio con su vulnerabilidad, su "
        "suelo, la sacudida que recibió y los servicios cercanos. En **gold** calculamos un índice explicable de 0 a 1 con siete "
        "componentes y publicamos 13 tablas que pasan 43 controles de calidad, con comentarios en el Catalog, un espacio de Genie y un dashboard.",
        "Un estudio independiente de la Javeriana Cali llega al mismo mecanismo: en Cali el daño fue interior, en edificios de 3 a 6 "
        "pisos anteriores a 1984, que el satélite casi no ve. Nuestro índice recupera ese grupo: es el 8,5 % del ranking y el 32 % de "
        "la prioridad muy alta. El resultado se consulta en un visor propio que filtra por comuna y cola de trabajo y descarga la lista en Excel para las brigadas.",
    ):
        texto_md(doc.add_paragraph(), parrafo)
    doc.add_heading("Cifras clave", 2)
    tabla(doc, [["Indicador", "Valor", "Tabla gold"],
                ["Predios analizados", "5.146 en 7 comunas", "`predios`"],
                ["Alta probabilidad de escombros / daño visible", "5,8 % / 26,3 % (1.354 predios)", "`predios`, `afectaciones`"],
                ["Sin dato satelital (a verificar en terreno)", "435 (8,5 %)", "`predios`"],
                ["Prioridad muy alta / alta", "179 / 357 edificios", "`predios`"],
                ["Ranking de comunas (p90 del índice)", "3, 9, 10, 18, 20, 19, 17", "`comunas`"],
                ["Ocupantes modelados en edificios dañados", "5.494 sin duplicar registros GEM (6.950 por predio)", "`exposicion_gem`, `comunas`"],
                ["Top 50 que se mantiene sin fuentes externas", "40 %", "`resumen_sensibilidad`"],
                ["Controles de calidad", "65 en silver y 43 en gold, todos aprobados", "`calidad`"]], [6.8, 6.1, 4.2])

    # --- 2 y 3. Texto del correo ---
    doc.add_heading("2. Decisiones en silver y gold", 1)
    bloques_md(doc, seccion_md("docs/ENTREGA.md", "## 2. Decisiones en silver y gold (≤ 200 palabras)", "> Notas"))
    doc.add_heading("3. Respuesta a las dos preguntas", 1)
    bloques_md(doc, seccion_md("docs/ENTREGA.md", "## 3. Respuesta a las dos preguntas (≤ 500 palabras)", "> Notas"))

    # --- 4. Guion ---
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    doc.add_heading("4. Guion de la presentación (5 a 7 minutos)", 1)
    texto_md(doc.add_paragraph(), f"La demo sigue el **Recorrido guiado** del mapa: {URL_MAPA}")
    bloques_md(doc, "## 0 · Apertura" + seccion_md("docs/GUION_PRESENTACION.md", "## 0 · Apertura", "---"))

    # --- 5. Preguntas del jurado ---
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    doc.add_heading("5. Preguntas del jurado y respuestas", 1)
    for i, (pregunta, respuesta) in enumerate(preguntas_jurado(), 1):
        doc.add_heading(f"{i}. {pregunta}", 3)
        texto_md(doc.add_paragraph(), respuesta)

    # --- 6. Evidencias ---
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    doc.add_heading("6. Evidencias", 1)
    doc.add_heading("Mapa interactivo", 2)
    texto_md(doc.add_paragraph(), f"Publicado en GitHub Pages con autorización de la organización hasta el cierre del evento: ")
    enlace(doc.paragraphs[-1], URL_MAPA)
    if MAPA.exists():
        figura(doc, MAPA, "Visor propio (MapLibre GL + deck.gl): edificios por prioridad, comunas con su puesto en el ranking, "
                          "salud (verde), bomberos y policía (azul), vías principales y halos de concentración de riesgo.")
    doc.add_heading("Capas en Databricks", 2)
    for ruta, pie_figura in CAPTURAS:
        figura(doc, RAIZ / ruta, pie_figura, ancho=14.5)

    # --- 7. Fuentes ---
    doc.add_heading("7. Fuentes externas", 1)
    bloques_md(doc, seccion_md("docs/ENTREGA.md", "## 4. Fuentes externas", "---"))
    texto_md(doc.add_paragraph(), "Fichas completas, enlaces y discrepancias entre fuentes: `docs/FUENTES.md` del repositorio.")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    doc.save(SALIDA)
    print(f"Documento: {SALIDA}")


if __name__ == "__main__":
    main()
