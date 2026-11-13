"""Ejecuta únicamente oro desde Parquet de plata. Datos y derivados privados."""
from pathlib import Path
import hashlib
import json

RAIZ = Path(__file__).resolve().parents[1]


def cargar_api():
    api = {"__name__": "pipeline_oro"}
    for nombre in ("00_utils_espacial.py", "00_pipeline.py", "00_silver.py", "00_gold.py"):
        ruta = RAIZ / "notebooks" / nombre
        exec(compile(ruta.read_text(encoding="utf-8"), str(ruta), "exec"), api)
    return api


def ejecutar_oro_local():
    api = cargar_api()
    origen = RAIZ / "data/oficiales/plata"
    rutas = sorted(origen.glob("silver_*.parquet"))
    def huella(ruta):
        with ruta.open("rb") as f:
            return hashlib.file_digest(f, "sha256").hexdigest()
    hashes = {p.name: huella(p) for p in rutas}
    plata = api["leer_plata_oro"](origen)
    tablas, reporte = api["construir_oro"](plata)
    if hashes != {p.name: huella(p) for p in rutas}:
        raise RuntimeError("Plata cambió durante la corrida; no publicar oro")
    reporte["sha256_entradas_plata"] = hashes
    reporte["sha256_codigo"] = {n: huella(RAIZ / "notebooks" / n) for n in
                               ("00_utils_espacial.py", "00_pipeline.py", "00_silver.py", "00_gold.py")}
    destino = RAIZ / "data/oficiales/oro"
    api["escribir_oro_local"](tablas, reporte, destino, plata)
    return tablas, reporte, destino


if __name__ == "__main__":
    _, reporte, destino = ejecutar_oro_local()
    print(json.dumps(reporte, ensure_ascii=False, indent=2))
    print(destino)
