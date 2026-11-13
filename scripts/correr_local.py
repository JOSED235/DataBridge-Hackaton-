"""Pipeline completo en local con los datos OFICIALES (data/oficiales/, fuera de git).

Mismo código que los notebooks: bronze (texto fiel) -> limpiar -> enriquecer -> suelo -> índice -> gold.
Sirve para tener las cifras y el mapa aunque falle Databricks, y para revisar los resultados.
Escribe en data/oficiales/salidas/ y en visor/data/ (ambos ignorados por git: no se redistribuyen).

Uso:  python scripts/correr_local.py
"""
from pathlib import Path
import json

import geopandas as gpd

RAIZ = Path(__file__).resolve().parent.parent
EXT = RAIZ / "data" / "externos"
OFI = RAIZ / "data" / "oficiales"
for nb in ("00_utils_espacial.py", "00_pipeline.py"):  # mismo efecto que %run en Databricks
    exec((RAIZ / "notebooks" / nb).read_text(encoding="utf-8"))

capas = {n: gpd.read_file(EXT / f"osm_{n}.geojson") for n in ("comunas", "barrios", "salud", "emergencia", "vias_principales")}
bomberos = capas["emergencia"][capas["emergencia"]["amenity"] == "fire_station"]

raw = bronze_desde_geojson(gpd.read_file(OFI / "Datosprediales.json"))
assert raw.shape == (5146, 21), raw.shape  # la guía: 5.146 filas y 20 propiedades + geometría

silver, reporte = limpiar(raw)
g = enriquecer(cruzar_externos(a_geo(silver), EXT), capas["comunas"], capas["barrios"], capas["salud"], bomberos, capas["vias_principales"])
g = asignar_suelo(g, *leer_suelo(EXT))
reporte["geometrias_reparadas"] = int(g["geom_reparada"].sum())
reporte["comuna_completada_con_osm"] = int(silver["comuna"].isna().sum())
g = calcular_indice(g)
gc = gold_comunas(g, capas["comunas"], capas["salud"], bomberos)
sens = sensibilidad(g, ESCENARIOS_SENSIBILIDAD)

assert reporte["valores_estado_sin_mapear"] == [], reporte["valores_estado_sin_mapear"]
assert g["indice_riesgo"].between(0, 1).all() and g["comuna"].notna().all()

SAL = OFI / "salidas"
SAL.mkdir(exist_ok=True)
(SAL / "reporte_limpieza.json").write_text(json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8")
exportar_visor(g, gc, SAL)
exportar_visor(g, gc, RAIZ / "visor" / "data")
(RAIZ / "visor" / "data" / "MUESTRA.txt").unlink(missing_ok=True)
g.drop(columns="geometry").to_csv(SAL / "gold_edificios.csv", index=False)
gc.drop(columns="geometry").to_csv(SAL / "gold_comunas.csv", index=False)
sens.to_csv(SAL / "gold_sensibilidad.csv", index=False)

print("Reporte:", json.dumps(reporte, ensure_ascii=False))
print(gc.drop(columns="geometry").to_string(index=False))
print(sens.to_string(index=False))
print(g["prioridad"].value_counts().to_string())
