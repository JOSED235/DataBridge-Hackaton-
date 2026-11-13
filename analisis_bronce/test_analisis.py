"""Regresión: una columna llamada level no es el atributo interno GroupBy.level."""

from pathlib import Path

import nbformat
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from shapely import from_wkt


def test_matriz_amplificacion_con_columna_level() -> None:
    path = Path(__file__).parent / "notebooks/11_gem_amplificacion.ipynb"
    nb = nbformat.read(path, as_version=4)
    cell = next(c.source for c in nb.cells if c.cell_type == "code" and "conteo=x.groupby" in c.source)
    raw = pd.DataFrame({
        "ampcode": ["1", "1", "noaf", "noaf"],
        "level": [.001, .01, .001, .01],
        "PGA": [1., 1.1, 1., 1.], "SA(0.1)": [1., 1.2, 1., 1.],
        "sigma_PGA": [.3, .3, 0., 0.],
    })
    scope = {"pd": pd, "x": raw, "display": lambda *args: None, "resumen": {}}
    exec(compile(cell, str(path), "exec"), scope)
    assert scope["qa"]["codigos"] == 2
    assert scope["qa"]["niveles"] == 2
    assert scope["qa"]["duplicados_codigo_nivel"] == 0
    assert scope["qa"]["combinaciones_faltantes"] == 0


def test_bronce_preserva_precision_y_validez_de_geometria() -> None:
    root = Path(__file__).resolve().parent.parent
    scope = {"__name__": "prueba_bronce"}
    for name in ["00_utils_espacial.py", "00_pipeline.py"]:
        exec(compile((root / "notebooks" / name).read_text(encoding="utf-8"), name, "exec"), scope)
    # El hueco es válido, pero redondear seis decimales lo pega al contorno.
    poly = Polygon([(-76.5, 3.4), (-76.49, 3.4), (-76.49, 3.41), (-76.5, 3.41)],
                   holes=[[(-76.4999999, 3.402), (-76.499, 3.402),
                           (-76.499, 3.408), (-76.4999999, 3.408)]])
    assert poly.is_valid
    g = gpd.GeoDataFrame({"id": ["prueba"]}, geometry=[poly], crs=4326)
    bronze = scope["bronze_desde_geojson"](g)
    restored = from_wkt(bronze.geom_wkt.iloc[0])
    assert restored.is_valid
    assert restored.equals_exact(poly, 0)
    silver = scope["a_geo"](bronze)
    assert from_wkt(silver.geom_wkt.iloc[0]).equals_exact(poly, 0)
    spark_ready = scope["para_spark"](silver)
    assert from_wkt(spark_ready.geom_wkt.iloc[0]).equals_exact(poly, 0)
