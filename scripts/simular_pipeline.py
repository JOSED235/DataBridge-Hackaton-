"""Prueba de extremo a extremo del pipeline silver/gold con edificios FICTICIOS.

Genera edificios sintéticos con columnas parecidas a las oficiales, corre limpiar -> enriquecer ->
índice -> gold, imprime el reporte y la sensibilidad, y deja los GeoJSON de muestra en visor/data/.
Ya no escribe en visor/data/ si existen datos reales: usar scripts/correr_local.py.

Uso:  python scripts/simular_pipeline.py      (requiere geopandas)
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
EXT = RAIZ / "data" / "externos"
for nb in ("00_utils_espacial.py", "00_pipeline.py"):  # mismo efecto que %run en Databricks
    exec((RAIZ / "notebooks" / nb).read_text(encoding="utf-8"))

capas = {n: gpd.read_file(EXT / f"osm_{n}.geojson") for n in ("comunas", "barrios", "salud", "emergencia", "vias_principales")}
bomberos = capas["emergencia"][capas["emergencia"]["amenity"] == "fire_station"]

# --- Edificios ficticios: puntos aleatorios dentro de las comunas -------------------------------
rng = np.random.default_rng(42)
N = 6000
pts = capas["comunas"].to_crs(CRS_METROS).sample_points(size=N // 22, rng=rng).explode().to_crs(CRS_GEO)
comuna_de = capas["comunas"]["name"].str.extract(r"(\d+)")[0].astype(int).reindex(pts.index).values
n = len(pts)
pisos = np.clip(rng.lognormal(0.7, 0.6, n).round(), 1, 35)
sesgo_comuna = np.isin(comuna_de, [3, 9, 10, 19, 20]) * 0.15  # zonas ficticias con más daño
prob = np.clip(rng.beta(2, 5, n) + 0.02 * pisos + sesgo_comuna, 0, 1)
# Mismas 4 categorías y nombres de columna que Datosprediales.json; puntos en vez de polígonos.
estado = np.select([prob > 0.85, prob > 0.6], ["Alta probabilidad de escombros", "Posible desaparición de techo"], "Sin cambio aparente / Daño interno")
estado[rng.random(n) < 0.08] = "Sin datos satelitales"
raw = pd.DataFrame({
    "OBJECTID": [str(i) for i in range(n)],
    "Estado_Estructural": estado,
    "NPISOS": pisos,
    "Indice_Escombros": np.where(estado == "Sin datos satelitales", np.nan, (prob * 40 - 20).round(3)),
    "COMUNA": [f"{c:02d}" if rng.random() > 0.05 else " " for c in comuna_de],
    "lon": pts.x.values, "lat": pts.y.values,
})
COLS_SIM = {**COLS, "geom_wkt": None, "lon": "lon", "lat": "lat"}
raw.loc[rng.choice(n, 20, replace=False), "NPISOS"] = 0  # errores de captura

# --- Pipeline ----------------------------------------------------------------------------------
silver, reporte = limpiar(raw, COLS_SIM)
print("Reporte de limpieza:", reporte)
g = enriquecer(cruzar_externos(a_geo(silver), EXT), capas["comunas"], capas["barrios"], capas["salud"], bomberos, capas["vias_principales"])
g = asignar_suelo(g, *leer_suelo(EXT))
g = calcular_indice(g)
gc = gold_comunas(g, capas["comunas"], capas["salud"], bomberos)

assert g["comuna"].notna().mean() > 0.99, "la unión espacial no completó las comunas"
assert g["indice_riesgo"].between(0, 1).all()
assert (g.loc[g["sin_dato_satelital"], "prioridad"] == "Sin dato: verificar en terreno").all()
assert len(gc) == 22
assert g["amplif_suelo"].between(0.3, 4).all() and (g["microzona"] != "noaf").mean() > 0.8, "cruce con microzonas falló"
try:  # misma conversión Arrow que hace spark.createDataFrame
    import pyarrow as pa
    pa.Table.from_pandas(para_spark(g)); pa.Table.from_pandas(para_spark(gc))
except ImportError:
    print("pyarrow no instalado: se omite la prueba de conversión a Spark")

print(g["prioridad"].value_counts().to_string())
print(gc[["comuna", "n_edificios", "pct_alta_escombros", "indice_p90", "n_salud", "ranking"]].head(8).to_string(index=False))
print(sensibilidad(g, ESCENARIOS_SENSIBILIDAD).to_string(index=False))

# --- Datos de muestra para el visor --------------------------------------------------------------
VIS = RAIZ / "visor" / "data"
reales = (VIS / "edificios.geojson").exists() and not (VIS / "MUESTRA.txt").exists()
if not reales:  # nunca pisar el mapa generado con datos oficiales por correr_local.py
    exportar_visor(g, gc, VIS)
s = capas["salud"][["name", "amenity", "geometry"]]
s.to_file(VIS / "salud.geojson", driver="GeoJSON")
capas["emergencia"][["name", "amenity", "geometry"]].to_file(VIS / "emergencia.geojson", driver="GeoJSON")
capas["vias_principales"][["name", "highway", "geometry"]].to_file(VIS / "vias.geojson", driver="GeoJSON", COORDINATE_PRECISION=5)
sis = gpd.read_file(EXT / "usgs_sismos_2026-08.geojson")[["mag", "place", "time", "geometry"]]
sis.to_file(VIS / "sismos.geojson", driver="GeoJSON")
if not reales:
    (VIS / "MUESTRA.txt").write_text("Edificios ficticios generados por scripts/simular_pipeline.py. Borrar al usar datos reales.\n", encoding="utf-8")
print(f"Visor: capas escritas en {VIS}" + (" (edificios reales conservados)" if reales else " (edificios ficticios)"))
