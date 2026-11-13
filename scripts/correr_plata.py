"""Materializa y valida plata en data/oficiales/plata/, sin tocar bronze ni el mapa.

Uso desde la raíz: python scripts/correr_plata.py
Requiere pandas, GeoPandas, Shapely y pyarrow.
"""
from pathlib import Path
import hashlib
import json

RAIZ = Path(__file__).resolve().parents[1]


def cargar_api():
    api = {"__name__": "pipeline_plata"}
    for nombre in ("00_utils_espacial.py", "00_pipeline.py", "00_silver.py"):
        ruta = RAIZ / "notebooks" / nombre
        exec(compile(ruta.read_text(encoding="utf-8"), str(ruta), "exec"), api)
    return api


def ejecutar_plata_local():
    api = cargar_api()
    origen = RAIZ / "data/oficiales/Datosprediales.json"
    carpeta = RAIZ / "data/externos"
    rutas = {"predios": origen, **{k: carpeta / v for k, v in api["ARCHIVOS_PLATA"].items()}}
    def huella(ruta):
        with ruta.open("rb") as archivo:
            return hashlib.file_digest(archivo, "sha256").hexdigest()

    hashes = {k: huella(p) for k, p in rutas.items()}
    raw = api["bronze_desde_geojson"](api["gpd"].read_file(origen))
    fuentes = api["leer_fuentes_plata"](carpeta)
    tablas, reporte = api["construir_plata"](raw, fuentes)
    manifiesto = tablas["fuentes"]
    manifiesto["sha256_archivo"] = manifiesto.fuente.map(hashes)
    manifiesto["modo_lectura"] = "archivo_local"
    reporte["fuentes_sin_modificacion"] = all(
        huella(p) == hashes[k] for k, p in rutas.items())
    if not reporte["fuentes_sin_modificacion"]:
        raise RuntimeError("Una fuente cambió durante el procesamiento; no publicar esta corrida")
    destino = RAIZ / "data/oficiales/plata"
    api["escribir_plata_local"](tablas, reporte, destino)
    return tablas, reporte, destino


if __name__ == "__main__":
    tablas, reporte, destino = ejecutar_plata_local()
    print(json.dumps(reporte, ensure_ascii=False, indent=2))
    print(f"Plata local guardada en {destino}")
