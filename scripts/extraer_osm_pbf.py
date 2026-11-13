"""Plan B de descargar_osm.py: extrae capas de OSM desde un PBF de Geofabrik
sin depender de Overpass (los espejos públicos de Overpass están caídos desde
el 13-nov-2026: overpass-api.de rechaza conexiones y los demás dan 504).

Descarga previa del extracto (una sola vez):
  curl -4 -L -C - -o data/cache/colombia-261112.osm.pbf \
    https://download.geofabrik.de/south-america/colombia-latest.osm.pbf

Uso:  python scripts/extraer_osm_pbf.py [capa ...]   (sin argumentos: las que falten)

El formato de salida es idéntico al de descargar_osm.py: osm_id + todos los tags,
geometrías "out center" (centro del bbox) para POI y geometría completa para vías.
El pre-filtrado por llave se hace en C (KeyFilter) para no iterar millones de
objetos en Python; las relaciones se resuelven con los ways miembro (IdFilter).
"""
import json
import sys
import time
from pathlib import Path

import osmium
from shapely.geometry import LineString, Point, mapping

RAIZ = Path(__file__).resolve().parent.parent
PBF = RAIZ / "data" / "cache" / "colombia-261112.osm.pbf"
OUT = RAIZ / "data" / "externos"
BBOX = (3.30, -76.62, 3.52, -76.45)  # sur, oeste, norte, este: casco urbano de Cali

# mimetiza las consultas de descargar_osm.py (out center tags / out geom tags)
CAPAS = {
    "osm_puntos_encuentro": {"llave": "emergency", "geometria": "center",
                             "valores": {"assembly_point"}},
    "osm_educacion": {"llave": "amenity", "geometria": "center",
                      "valores": {"school", "university", "college"}},
    "osm_vias_principales": {"llave": "highway", "geometria": "linea",
                             "valores": {"motorway", "trunk", "primary", "secondary",
                                         "motorway_link", "trunk_link",
                                         "primary_link", "secondary_link"}},
}


def centro(coords):
    xs = [p[0] for p in coords]
    ys = [p[1] for p in coords]
    return Point((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)


def en_bbox(coords):
    s, o, n, e = BBOX
    return any(o <= x <= e and s <= y <= n for x, y in coords)


def extraer(capa, cfg):
    llave, valores, modo = cfg["llave"], cfg["valores"], cfg["geometria"]
    filtro = lambda t: t.get(llave) in valores
    feats = []
    ways_filtrados = {}   # id way filtrado -> coords (para centros de relaciones)
    rel_pendientes = []   # (osm_id, tags, refs de ways miembro)
    t0 = time.time()

    def agregar(osm_id, tags, coords):
        if not coords or not en_bbox(coords):
            return
        g = centro(coords) if modo == "center" else LineString(coords)
        feats.append({"type": "Feature", "geometry": mapping(g),
                      "properties": {"osm_id": osm_id, **tags}})

    # el caché de ubicaciones va PRIMERO: necesita ver todos los nodos del archivo
    fp = osmium.FileProcessor(str(PBF)).with_locations()\
        .with_filter(osmium.filter.KeyFilter(llave))
    print(f"{capa}: recorriendo PBF (pasada 1, filtro llave={llave})...", flush=True)
    for obj in fp:
        tags = {k: v for k, v in obj.tags}
        if not filtro(tags):
            continue
        if obj.type_str() == "n":
            agregar(f"node/{obj.id}", tags, [(obj.location.lon, obj.location.lat)])
        elif obj.type_str() == "w":
            coords = [(nd.location.lon, nd.location.lat) for nd in obj.nodes]
            agregar(f"way/{obj.id}", tags, coords)
            if modo == "center":
                ways_filtrados[obj.id] = coords
        else:  # relación: se resuelve al final con sus ways miembro
            rel_pendientes.append((f"relation/{obj.id}", tags,
                                   [m.ref for m in obj.members if m.type == "w"]))

    # pasada 2: coords de ways miembro no filtrados (miembros de multipolígonos)
    faltan = {ref for _, _, refs in rel_pendientes for ref in refs} - set(ways_filtrados)
    if faltan:
        print(f"{capa}: pasada 2 para {len(faltan)} ways miembro de relaciones...", flush=True)
        fp2 = osmium.FileProcessor(str(PBF)).with_locations()\
            .with_filter(osmium.filter.IdFilter(faltan))
        for obj in fp2:
            if obj.type_str() == "w":
                ways_filtrados[obj.id] = [(nd.location.lon, nd.location.lat) for nd in obj.nodes]

    for osm_id, tags, refs in rel_pendientes:
        coords = []
        for ref in refs:
            coords.extend(ways_filtrados.get(ref, []))
        if coords:
            agregar(osm_id, tags, coords)
        else:
            print(f"{capa}: {osm_id} sin geometría resoluble, se omite", file=sys.stderr)

    ways_filtrados.clear()
    (OUT / f"{capa}.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False),
        encoding="utf-8")
    print(f"{capa}: {len(feats)} elementos -> {capa}.geojson ({time.time() - t0:.0f} s)")


def main():
    if not PBF.exists():
        sys.exit(f"No existe {PBF}. Descárgalo con el curl del docstring del script.")
    OUT.mkdir(parents=True, exist_ok=True)
    pedidas = sys.argv[1:] or [c for c in CAPAS if not (OUT / f"{c}.geojson").exists()]
    for capa in pedidas:
        if capa not in CAPAS:
            sys.exit(f"Capa desconocida: {capa}. Disponibles: {', '.join(CAPAS)}")
        path = OUT / f"{capa}.geojson"
        if path.exists():
            print(f"{capa}: ya existe, se omite")
            continue
        extraer(capa, CAPAS[capa])


if __name__ == "__main__":
    main()
