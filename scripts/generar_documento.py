"""Genera el Word con el contenido del correo de entrega, en Arial 12 y sin negritas.

Incluye solo lo que se envía: capturas del Catalog, decisiones, respuesta a las dos preguntas, fuentes y enlace al mapa.
El texto se toma de docs/ENTREGA.md para que el Word no se desactualice. La presentación se adjunta aparte.

Uso:  python scripts/generar_documento.py
"""
from pathlib import Path
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "data" / "oficiales" / "salidas" / "Entrega_icesixuao.docx"
URL_MAPA = "https://josed235.github.io/DataBridge-Hackaton-/"
CAPTURAS = [
    ("capturas/primeracatalog.png", "Figura 1. Tablas bronze del equipo en workspace.default."),
    ("capturas/segundacatalog.png", "Figura 2. Tablas gold del equipo y comienzo de las silver."),
    ("capturas/terceracatalog.png", "Figura 3. Tablas silver del equipo. En total, 45 tablas."),
]


def seccion_md(inicio, fin):
    t = (RAIZ / "docs" / "ENTREGA.md").read_text(encoding="utf-8")
    a = t.index(inicio) + len(inicio)
    return t[a:t.index(fin, a)]


def plano(texto):
    """Quita las marcas de Markdown (negrita, cursiva, código) y deja el texto tal cual."""
    return re.sub(r"\*\*(.+?)\*\*|`([^`]+)`|\*([^*\s][^*]*)\*", lambda m: next(g for g in m.groups() if g), texto)


def parrafo(doc, texto, sangria=None):
    p = doc.add_paragraph(plano(texto))
    if sangria:
        p.paragraph_format.left_indent = Cm(sangria)
        p.paragraph_format.first_line_indent = Cm(-sangria / 2)
    return p


def titulo(doc, texto):
    p = doc.add_heading(texto, 1)
    return p


def bloques(doc, md):
    for linea in md.strip().splitlines():
        s = linea.strip()
        if not s or s == "---" or s.startswith(">"):
            continue
        parrafo(doc, s, sangria=1.0 if re.match(r"^\d+\.\s", s) else None)


def enlace(p, url):
    rel = p.part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    h = OxmlElement("w:hyperlink"); h.set(qn("r:id"), rel)
    r = OxmlElement("w:r"); rpr = OxmlElement("w:rPr")
    for etiqueta, val in (("w:color", "0563C1"), ("w:u", "single")):
        e = OxmlElement(etiqueta); e.set(qn("w:val"), val); rpr.append(e)
    r.append(rpr)
    t = OxmlElement("w:t"); t.text = url; r.append(t)
    h.append(r); p._p.append(h)


def estilos(doc):
    for nombre in ("Normal", "Heading 1", "Caption"):
        e = doc.styles[nombre]
        e.font.name = "Arial"; e.font.size = Pt(12); e.font.bold = False; e.font.italic = False
        e.font.color.rgb = RGBColor(0, 0, 0)
        fuentes = e.element.rPr.rFonts
        for atributo in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):  # el tema pisaría Arial
            fuentes.attrib.pop(qn(atributo), None)
        fuentes.set(qn("w:eastAsia"), "Arial")
        e.paragraph_format.space_before = Pt(18 if nombre == "Heading 1" else 0)
        e.paragraph_format.space_after = Pt(8)
        e.paragraph_format.line_spacing = 1.15
    doc.styles["Heading 1"].paragraph_format.keep_with_next = True


def main():
    doc = Document()
    estilos(doc)
    s = doc.sections[0]
    s.page_width, s.page_height = Cm(21.59), Cm(27.94)  # carta
    s.left_margin = s.right_margin = Cm(2.5); s.top_margin = s.bottom_margin = Cm(2.5)
    props = doc.core_properties
    props.author = props.last_modified_by = "Equipo icesixuao"
    props.title = "DataBridge Hack 2026, equipo icesixuao"
    props.comments = props.keywords = props.subject = props.category = ""

    parrafo(doc, "DataBridge Hack 2026. Equipo icesixuao: Nicolas Zapato (Universidad Autónoma de Occidente) y José David Rodríguez Pinilla (Universidad Icesi).")
    parrafo(doc, "Pregunta: ¿qué afectaciones generó el sismo del 10 de agosto en Cali y qué factores contribuyen a reducir "
                 "el impacto de las réplicas sobre la población, la infraestructura y los servicios urbanos?")
    parrafo(doc, "Se adjunta la presentación de 3 diapositivas.")

    titulo(doc, "1. Capas en Databricks")
    parrafo(doc, "Catálogo workspace, esquema default: 16 tablas bronze, 16 silver y 13 gold con el prefijo de equipo icesixuao.")
    for ruta, pie in CAPTURAS:
        doc.add_picture(str(RAIZ / ruta), width=Cm(15))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        p = doc.add_paragraph(pie, style="Caption"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    titulo(doc, "2. Decisiones en silver y gold")
    bloques(doc, seccion_md("## 2. Decisiones en silver y gold (≤ 200 palabras)", "> Notas"))

    titulo(doc, "3. Respuesta a las dos preguntas")
    bloques(doc, seccion_md("## 3. Respuesta a las dos preguntas (≤ 500 palabras)", "> Notas"))

    titulo(doc, "4. Fuentes externas")
    bloques(doc, seccion_md("## 4. Fuentes externas", "---"))

    titulo(doc, "5. Mapa interactivo y dashboard")
    p = parrafo(doc, "El mapa se puede consultar en ")
    enlace(p, URL_MAPA)
    p = parrafo(doc, "El dashboard de resultados está en ")
    enlace(p, URL_MAPA + "dashboard.html")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    doc.save(SALIDA)
    print(f"Documento: {SALIDA}")


if __name__ == "__main__":
    main()
