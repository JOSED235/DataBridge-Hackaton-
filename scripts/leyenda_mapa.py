"""Dibuja la leyenda completa del mapa sobre el pantallazo de la diapositiva 3.

Lee data/oficiales/salidas/mapa.png y escribe data/oficiales/salidas/mapa_leyenda.png (fuera de git).
Uso:  python scripts/leyenda_mapa.py  &&  python scripts/generar_presentacion.py data/oficiales/salidas/mapa_leyenda.png
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
ORIGEN = RAIZ / "data" / "oficiales" / "salidas" / "mapa.png"
SALIDA = RAIZ / "data" / "oficiales" / "salidas" / "mapa_leyenda.png"

# Mismos colores que visor/app.js.
PRIORIDAD = [("Muy alta", (255, 59, 48)), ("Alta", (255, 149, 0)), ("Media", (255, 214, 10)), ("Baja", (70, 78, 92)),
             ("Sin dato satelital", (150, 120, 200)), ("Sin construcción registrada", (90, 170, 220))]


def fuente(tam, negrita=False):
    for nombre in (("segoeuib.ttf", "arialbd.ttf") if negrita else ("segoeui.ttf", "arial.ttf")):
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{nombre}", tam)
        except OSError:
            continue
    return ImageFont.load_default()


def main():
    im = Image.open(ORIGEN).convert("RGB")
    W, H = im.size
    esc = H / 877
    t, tt = fuente(round(15 * esc)), fuente(round(15 * esc), negrita=True)
    fila = round(23 * esc)
    ancho, alto = round(330 * esc), round(fila * 15.4)
    x0, y0 = W - ancho - round(14 * esc), H - alto - round(40 * esc)

    caja = Image.new("RGBA", (ancho, alto), (14, 16, 19, 232))
    im.paste(caja, (x0, y0), caja)
    d = ImageDraw.Draw(im)
    d.rectangle([x0, y0, x0 + ancho, y0 + alto], outline=(70, 78, 92), width=1)
    x, y = x0 + round(14 * esc), y0 + round(10 * esc)
    icono, texto_x = round(14 * esc), x + round(26 * esc)

    def titulo(s):
        nonlocal y
        d.text((x, y), s, font=tt, fill=(232, 230, 225)); y += fila

    def item(s, dibujo):
        nonlocal y
        cy = y + fila // 2 - 1
        dibujo(cy)
        d.text((texto_x, y), s, font=t, fill=(201, 205, 211)); y += fila

    titulo("Edificios por prioridad del índice")
    for nombre, color in PRIORIDAD:
        item(nombre, lambda cy, c=color: d.rectangle([x, cy - icono // 2, x + icono, cy + icono // 2], fill=c))
    titulo("Servicios y red vial (OpenStreetMap)")
    r = round(5 * esc)
    item("Centro de salud", lambda cy: d.ellipse([x + 2, cy - r, x + 2 + 2 * r, cy + r], fill=(62, 207, 142), outline=(14, 16, 19)))
    item("Bomberos y policía", lambda cy: d.ellipse([x + 1, cy - r - 1, x + 3 + 2 * r, cy + r + 1], fill=(90, 160, 255), outline=(14, 16, 19)))
    item("Vía principal", lambda cy: d.line([x, cy, x + icono + 4, cy], fill=(200, 205, 215), width=max(2, round(2 * esc))))
    titulo("Capas de análisis")

    def halo(cy):
        capa = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(capa).ellipse([x - 2, cy - icono // 2 - 2, x + icono + 2, cy + icono // 2 + 2], fill=(255, 236, 150, 230))
        capa = capa.filter(ImageFilter.GaussianBlur(round(3 * esc)))
        im.paste(capa, (0, 0), capa)
    item("Concentración de riesgo (calor)", halo)
    item("Comuna: más rojo = mayor índice p90",
         lambda cy: d.rectangle([x, cy - icono // 2, x + icono, cy + icono // 2], fill=(110, 30, 30), outline=(140, 150, 165)))
    item("C3 · #1 = comuna y puesto en el ranking", lambda cy: d.text((x - 2, cy - round(9 * esc)), "C3", font=tt, fill=(255, 255, 255)))
    im.save(SALIDA)
    print(f"Mapa con leyenda: {SALIDA}")


if __name__ == "__main__":
    main()
