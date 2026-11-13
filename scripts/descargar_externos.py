"""Descarga y recorta a Cali las fuentes externas sísmicas y de exposición (todas públicas y citadas en docs/FUENTES.md).

Salidas en data/externos/ (pequeñas, para subir al volumen de Databricks):
  gem_exposicion.csv            GEM TREQ: un punto por edificio (349 mil en Cali) con año, estrato, uso, pisos,
                                ocupantes y vulnerabilidad derivada de su tipología. Recortado a las comunas de los datos.
  gem_sitio_licuacion_ladera.csv GEM TREQ: susceptibilidad a licuación y pendiente por sitio.
  usgs_shakemap_cali.csv        USGS ShakeMap v11 del evento us6000tjl2: MMI, PGA, PGV y PSA por nodo (~1 km).
  usgs_estaciones_cali.geojson  Estaciones del ShakeMap en Cali: acelerógrafo del SGC y celdas DYFI.
  usgs_replicas.geojson         Catálogo USGS: sismos M >= 2,5 a 150 km del epicentro, 10-ago a 13-nov-2026.

Uso:  python scripts/descargar_externos.py        (requiere pandas y geopandas; ~80 MB de descarga)
"""
import io
import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
EXT = RAIZ / "data" / "externos"
GEM = "https://raw.githubusercontent.com/gem/treq-riesgo-urbano/master/Cali"
EVENTO = "us6000tjl2"
SHAKEMAP = f"https://earthquake.usgs.gov/product/shakemap/{EVENTO}/us/1791703961532/download"
CALI = (-76.60, 3.33, -76.45, 3.50)          # lon_min, lat_min, lon_max, lat_max (casco urbano)
COMUNAS_DATOS = {3, 9, 10, 17, 18, 19, 20}   # comunas presentes en Datosprediales.json
# Ductilidad en la taxonomía de GEM: DNO nula, DUL baja, DUM media, DUH alta.
DUCTILIDAD_BAJA = ("-DNO", "-DUL")


def bajar(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "databridge-hack"}), timeout=300) as r:
        return r.read()


def en_cali(df, lon="lon", lat="lat"):
    return df[df[lon].between(CALI[0], CALI[2]) & df[lat].between(CALI[1], CALI[3])]


def gem_exposicion():
    ex = pd.read_csv(io.BytesIO(bajar(f"{GEM}/Exposicion/Exposure_Cali_Colombia.csv")), dtype={"MICROZONE": str})
    tax = pd.read_csv(io.BytesIO(bajar(f"{GEM}/Exposicion/taxonomy_mapping_MEAN.csv")))
    # Cada clase de GEM se reparte en tipologías con pesos que suman 1 (criterio de expertos, esquema MEAN).
    tax["baja"] = tax["conversion"].str.contains("|".join(DUCTILIDAD_BAJA), regex=True) * tax["weight"]
    tax["mur"] = tax["conversion"].str.startswith("MUR") * tax["weight"]
    v = tax.groupby("taxonomy")[["baja", "mur"]].sum().rename(columns={"baja": "p_ductilidad_baja", "mur": "p_mamposteria_no_reforzada"})
    ex = ex[ex["COMUNA"].isin(COMUNAS_DATOS)].merge(v, left_on="taxonomy", right_index=True, how="left")
    cols = ["id", "lon", "lat", "CONSTRUCTION_PERIOD", "INCOME_LEVEL", "FLOORS", "OCCUPANCY", "night", "structural",
            "MICROZONE", "COMUNA", "p_ductilidad_baja", "p_mamposteria_no_reforzada"]
    ex[cols].round(4).to_csv(EXT / "gem_exposicion.csv", index=False)
    print("gem_exposicion.csv:", len(ex), "edificios GEM; sin tipología:", int(ex["p_ductilidad_baja"].isna().sum()))


def gem_sitio():
    liq = pd.read_csv(io.BytesIO(bajar(f"{GEM}/Condiciones_Sitio/sites_liquefaction.csv")))
    lad = pd.read_csv(io.BytesIO(bajar(f"{GEM}/Condiciones_Sitio/sites_landslide.csv")))
    assert (liq[["lon", "lat"]].round(5).values == lad[["lon", "lat"]].round(5).values).all(), "los sitios no coinciden"
    s = liq[["lon", "lat", "unit", "liq_susc_cat", "gwd"]].assign(pendiente_grados=lad["slope"].round(1))
    en_cali(s).to_csv(EXT / "gem_sitio_licuacion_ladera.csv", index=False)
    print("gem_sitio_licuacion_ladera.csv:", len(en_cali(s)), "sitios")


def shakemap():
    raiz = ET.fromstring(bajar(f"{SHAKEMAP}/grid.xml"))
    ns = {"s": raiz.tag.split("}")[0].strip("{")}
    campos = [f.get("name").lower() for f in sorted(raiz.findall("s:grid_field", ns), key=lambda f: int(f.get("index")))]
    datos = pd.read_csv(io.StringIO(raiz.find("s:grid_data", ns).text.strip()), sep=r"\s+", header=None, names=campos)
    en_cali(datos).to_csv(EXT / "usgs_shakemap_cali.csv", index=False)
    print("usgs_shakemap_cali.csv:", len(en_cali(datos)), "nodos; versión", raiz.get("shakemap_version"), "; unidades: pga y psa en %g")


def estaciones():
    st = json.loads(bajar(f"{SHAKEMAP}/stationlist.json"))
    fs = [f for f in st["features"] if CALI[0] <= f["geometry"]["coordinates"][0] <= CALI[2] and CALI[1] <= f["geometry"]["coordinates"][1] <= CALI[3]]
    props = ("code", "name", "network", "source", "station_type", "pga", "pgv", "intensity", "distance", "vs30")
    fs = [{"type": "Feature", "geometry": f["geometry"], "properties": {k: f["properties"].get(k) for k in props}} for f in fs]
    (EXT / "usgs_estaciones_cali.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": fs}), encoding="utf-8")
    print("usgs_estaciones_cali.geojson:", len(fs), "estaciones (sísmicas:", sum(f["properties"]["station_type"] == "seismic" for f in fs), ")")


def replicas():
    url = ("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2026-08-10&endtime=2026-11-14"
           "&latitude=4.8601&longitude=-76.2558&maxradiuskm=150&minmagnitude=2.5&orderby=time-asc")
    (EXT / "usgs_replicas.geojson").write_bytes(bajar(url))
    n = len(json.loads((EXT / "usgs_replicas.geojson").read_text(encoding="utf-8"))["features"])
    print("usgs_replicas.geojson:", n, "eventos (incluye el principal)")


if __name__ == "__main__":
    for paso in (gem_exposicion, gem_sitio, shakemap, estaciones, replicas):
        paso()
