"""Comprueba las salidas guardadas, las huellas y la privacidad sin volver a transformar."""
from pathlib import Path
import hashlib
import json
import runpy
import subprocess

import geopandas as gpd
import nbformat
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa

RAIZ = Path(__file__).resolve().parents[1]
carpeta = RAIZ / "analisis_plata"
fuente = carpeta / "notebooks/01_validacion_plata.ipynb"
nb = nbformat.read(fuente, as_version=4)
ejecutado = nbformat.read(carpeta / "ejecutados" / fuente.name, as_version=4)
nbformat.validate(nb)
nbformat.validate(ejecutado)
assert [c.source for c in nb.cells] == [c.source for c in ejecutado.cells]
assert all(c.execution_count is None and not c.outputs for c in nb.cells if c.cell_type == "code")
celdas = [c for c in ejecutado.cells if c.cell_type == "code"]
assert all(c.execution_count is not None for c in celdas)
assert not [o for c in celdas for o in c.outputs if o.output_type == "error"]
recibo = json.loads((carpeta / "ejecutados/ejecucion.json").read_text(encoding="utf-8"))
assert recibo["sha256_notebook_fuente"] == hashlib.sha256(fuente.read_bytes()).hexdigest()
assert (carpeta / "ejecutados/01_validacion_plata.html").stat().st_size > 1000

modulo = runpy.run_path(str(RAIZ / "scripts/correr_plata.py"))
api = modulo["cargar_api"]()
salida = RAIZ / "data/oficiales/plata"
reporte = json.loads((salida / "reporte.json").read_text(encoding="utf-8"))
geograficas = {"predios", "territorios", "servicios", "vias", "sitio_grilla", "exposicion_gem",
               "sitio_licuacion_ladera", "shakemap", "observaciones", "eventos"}
tablas = {}
for nombre, filas in reporte["tablas"].items():
    ruta = salida / f"silver_{api['EQUIPO']}_{nombre}.parquet"
    d = pd.read_parquet(ruta)
    assert len(d) == filas, nombre
    if nombre in geograficas:
        d = gpd.GeoDataFrame(d, geometry=gpd.GeoSeries.from_wkt(d.geom_wkt), crs=4326)
    tablas[nombre] = d
controles = api["validar_plata"](tablas, reporte["filas_bronze"])
assert tablas["calidad"].cumple.all()
assert controles.control.tolist() == tablas["calidad"].control.tolist()

for fila in tablas["fuentes"].itertuples(index=False):
    ruta = (RAIZ / "data/oficiales" if fila.fuente == "predios" else RAIZ / "data/externos") / fila.archivo
    with ruta.open("rb") as f:
        assert hashlib.file_digest(f, "sha256").hexdigest() == fila.sha256_archivo, fila.fuente

schema = pq.read_schema(salida / f"silver_{api['EQUIPO']}_servicios.parquet")
assert pa.types.is_floating(schema.field("capacidad").type)
assert pa.types.is_string(schema.field("operatividad").type) or pa.types.is_large_string(schema.field("operatividad").type)
schema = pq.read_schema(salida / f"silver_{api['EQUIPO']}_fuentes.parquet")
assert pa.types.is_timestamp(schema.field("corte_fuente").type)

privados = ["data/oficiales/plata", "analisis_plata/ejecutados"]
for ruta in privados:
    subprocess.run(["git", "check-ignore", "-q", ruta], cwd=RAIZ, check=True)
assert not subprocess.check_output(["git", "ls-files", "--", *privados], cwd=RAIZ)
print(f"{len(tablas)} tablas Parquet; {len(tablas['predios'])} predios; {len(controles)} controles válidos")
print(f"{len(tablas['fuentes'])} archivos conservan SHA-256; tipos nulos conservados; resultados privados ignorados")
print(f"1 notebook ejecutado; {len(celdas)} celdas; {recibo['figuras']} figuras; 0 errores")
