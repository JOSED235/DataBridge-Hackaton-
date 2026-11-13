"""Descarga capas de OpenStreetMap para Cali (Overpass API) y las guarda como GeoJSON en data/externos/.

Por qué OSM: datos.cali.gov.co y los WFS de la IDESC están fuera de línea desde el 21-oct-2026
(comunicado de la Alcaldía), así que OSM es la fuente abierta disponible para comunas,
barrios, servicios de emergencia y vías.

Uso:  python scripts/descargar_osm.py      (requiere shapely)
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

from shapely.geometry import LineString, Point, mapping
from shapely.ops import polygonize, unary_union

OUT = Path(__file__).resolve().parent.parent / "data" / "externos"
URL = "https://overpass-api.de/api/interpreter"
BBOX = "3.30,-76.62,3.52,-76.45"  # sur,oeste,norte,este: casco urbano de Cali

CAPAS = {
    "osm_comunas": f'rel["boundary"="administrative"]["admin_level"="8"]["name"~"^Comuna"]({BBOX});out geom;',
    "osm_barrios": f'rel["boundary"="administrative"]["admin_level"="9"]({BBOX});out geom;',
    "osm_salud": f'nwr["amenity"~"^(hospital|clinic)$"]({BBOX});out center tags;',
    "osm_emergencia": f'nwr["amenity"~"^(fire_station|police)$"]({BBOX});out center tags;',
    "osm_puntos_encuentro": f'nwr["emergency"="assembly_point"]({BBOX});out center tags;',
    "osm_educacion": f'nwr["amenity"~"^(school|university|college)$"]({BBOX});out center tags;',
    "osm_vias_principales": f'way["highway"~"^(motorway|trunk|primary|secondary)(_link)?$"]({BBOX});out geom tags;',
}


def overpass(q, intentos=4):
    data = urllib.parse.urlencode({"data": f"[out:json][timeout:180];{q}"}).encode()
    req = urllib.request.Request(URL, data=data, headers={"User-Agent": "hackathon-research-client"})
    for i in range(intentos):
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                return json.load(r)["elements"]
        except urllib.error.HTTPError as err:  # 429/502/504: servidor público saturado
            if i == intentos - 1:
                raise
            print(f"  HTTP {err.code}, reintento en {30 * (i + 1)} s")
            time.sleep(30 * (i + 1))


def geom(e):
    if e["type"] == "node":
        return Point(e["lon"], e["lat"])
    if "center" in e:  # way/rel de POI: usamos el centroide que da Overpass
        return Point(e["center"]["lon"], e["center"]["lat"])
    if e["type"] == "way":
        return LineString([(p["lon"], p["lat"]) for p in e["geometry"]])
    # relación de límite: unir los trazos externos y poligonizar
    lines = [LineString([(p["lon"], p["lat"]) for p in m["geometry"]])
             for m in e.get("members", []) if m["type"] == "way" and m.get("role") != "inner" and "geometry" in m]
    polys = list(polygonize(unary_union(lines)))
    return unary_union(polys) if polys else None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for nombre, q in CAPAS.items():
        path = OUT / f"{nombre}.geojson"
        if path.exists():  # borrar el archivo para forzar una nueva descarga
            print(f"{nombre}: ya existe, se omite")
            continue
        feats = []
        for e in overpass(q):
            g = geom(e)
            if g is None or g.is_empty:
                continue
            props = {"osm_id": f'{e["type"]}/{e["id"]}', **e.get("tags", {})}
            feats.append({"type": "Feature", "geometry": mapping(g), "properties": props})
        path.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False), encoding="utf-8")
        print(f"{nombre}: {len(feats)} elementos -> {path.name}")
        time.sleep(5)  # cortesía con el servidor público de Overpass


if __name__ == "__main__":
    main()
