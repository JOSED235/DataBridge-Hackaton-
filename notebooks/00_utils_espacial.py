# Databricks notebook source
# Funciones espaciales compartidas. En los otros notebooks: %run ./00_utils_espacial
# Todas reciben y devuelven GeoDataFrames. Las distancias se calculan en metros con
# MAGNA-SIRGAS Origen Nacional (EPSG:9377), el CRS oficial de Colombia.

import geopandas as gpd
import numpy as np
import pandas as pd

CRS_GEO = 4326     # lat/lon (WGS84), lo que usa el visor
CRS_METROS = 9377  # MAGNA-SIRGAS Origen Nacional, para distancias y áreas
EPICENTRO = (-76.2558, 4.8601)  # USGS us7000... M7.4, 10-ago-2026, 4 km SSW de San José del Palmar


def a_gdf(df, lon="lon", lat="lat", crs=CRS_GEO):
    """DataFrame con columnas lon/lat -> GeoDataFrame de puntos. Descarta filas sin coordenadas."""
    df = df.dropna(subset=[lon, lat])
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[lon], df[lat]), crs=crs)


def asignar_zona(gdf, zonas, campo, nuevo=None):
    """Unión espacial: copia `campo` de la zona (polígono) que contiene cada geometría.
    Si son polígonos, usa el centroide para que cada edificio caiga en una sola zona."""
    nuevo = nuevo or campo
    pts = gdf.copy()
    pts["_geom_orig"] = pts.geometry
    pts = pts.set_geometry(pts.to_crs(CRS_METROS).centroid.to_crs(gdf.crs))
    z = zonas[[campo, "geometry"]].to_crs(gdf.crs).rename(columns={campo: nuevo})
    out = gpd.sjoin(pts, z, how="left", predicate="within").drop(columns="index_right")
    out = out[~out.index.duplicated(keep="first")]  # bordes compartidos
    out = out.set_geometry("_geom_orig").drop(columns="geometry")
    return out.rename_geometry("geometry").set_crs(gdf.crs, allow_override=True)


def distancia_mas_cercana(gdf, objetivos, nombre):
    """Agrega `dist_<nombre>_m`: distancia en metros a la geometría más cercana de `objetivos`."""
    a = gdf.to_crs(CRS_METROS)
    b = objetivos[["geometry"]].to_crs(CRS_METROS)
    j = gpd.sjoin_nearest(a[["geometry"]], b, how="left", distance_col="_d")
    out = gdf.copy()
    out[f"dist_{nombre}_m"] = j.groupby(level=0)["_d"].first().reindex(gdf.index).round(1)
    return out


def contar_en_radio(gdf, objetivos, radio_m, nombre):
    """Agrega `n_<nombre>_<radio>m`: cuántos objetivos hay a menos de `radio_m` metros."""
    a = gdf.to_crs(CRS_METROS)
    buf = gpd.GeoDataFrame(geometry=a.buffer(radio_m), index=a.index, crs=CRS_METROS)
    j = gpd.sjoin(buf, objetivos[["geometry"]].to_crs(CRS_METROS), how="inner", predicate="intersects")
    out = gdf.copy()
    out[f"n_{nombre}_{radio_m}m"] = j.groupby(level=0).size().reindex(gdf.index, fill_value=0)
    return out


def distancia_epicentro_km(gdf):
    epi = gpd.GeoSeries(gpd.points_from_xy([EPICENTRO[0]], [EPICENTRO[1]]), crs=CRS_GEO).to_crs(CRS_METROS).iloc[0]
    return (gdf.to_crs(CRS_METROS).centroid.distance(epi) / 1000).round(2)


def normalizar(s, invertir=False, recorte=(0.01, 0.99)):
    """Min-max a 0..1 recortando percentiles extremos para que un valor atípico no aplaste al resto."""
    # Los cuantiles de Int64 nullable pueden ser decimales; clip sobre enteros los rechaza.
    s = s.astype("float64")
    lo, hi = s.quantile(recorte[0]), s.quantile(recorte[1])
    x = ((s.clip(lo, hi) - lo) / (hi - lo)) if hi > lo else s * 0.0
    return 1 - x if invertir else x


def indice_riesgo(df, pesos):
    """Suma ponderada de componentes ya normalizados a 0..1. `pesos`: {columna: peso}; se re-escalan a suma 1.
    Si un componente falta en un edificio, se reparte su peso entre los disponibles (no se castiga ni premia el faltante)."""
    w = pd.Series(pesos, dtype=float)
    w = w / w.sum()
    comp = df[list(w.index)]
    pesos_validos = comp.notna().mul(w, axis=1)
    return (comp.fillna(0).mul(w, axis=1).sum(axis=1) / pesos_validos.sum(axis=1)).round(4)


def sensibilidad(df, escenarios, top=50, id_col="id"):
    """Compara rankings bajo distintos pesos. Devuelve, por escenario, la correlación de Spearman con el
    escenario base (el primero) y el % del top-N que se mantiene. Si el top se mantiene, la priorización es robusta."""
    nombres = list(escenarios)
    scores = pd.DataFrame({n: indice_riesgo(df, p) for n, p in escenarios.items()})
    base = scores[nombres[0]]
    ids = df[id_col].astype(str)

    def top_ids(s):  # empates en el corte: se desempata por id para que el resultado no dependa del orden de filas
        return set(pd.DataFrame({"s": s, "id": ids}).sort_values(["s", "id"], ascending=[False, True], kind="mergesort").head(top)["id"])

    top_base = top_ids(base)
    filas = []
    for n in nombres:
        top_n = top_ids(scores[n])
        filas.append({"escenario": n,
                      "spearman_vs_base": round(base.rank().corr(scores[n].rank()), 3),  # Spearman sin scipy
                      f"top{top}_coincide_%": round(100 * len(top_base & top_n) / top, 1)})
    return pd.DataFrame(filas)


def autoprueba():
    """Prueba con datos sintéticos (sin red). Ejecutar antes del evento y al cargar el notebook."""
    zonas = gpd.GeoDataFrame({"comuna": [1, 2]}, geometry=gpd.GeoSeries.from_wkt(
        ["POLYGON((-76.55 3.40,-76.53 3.40,-76.53 3.42,-76.55 3.42,-76.55 3.40))",
         "POLYGON((-76.53 3.40,-76.51 3.40,-76.51 3.42,-76.53 3.42,-76.53 3.40))"]), crs=CRS_GEO)
    ed = a_gdf(pd.DataFrame({"id": [1, 2, 3], "lon": [-76.54, -76.52, -76.60], "lat": [3.41, 3.41, 3.41]}))
    hosp = a_gdf(pd.DataFrame({"lon": [-76.54], "lat": [3.41]}))

    r = asignar_zona(ed, zonas, "comuna")
    assert r["comuna"].tolist()[:2] == [1, 2] and pd.isna(r["comuna"].iloc[2]), r
    r = distancia_mas_cercana(r, hosp, "hospital")
    assert r["dist_hospital_m"].iloc[0] < 1 and 2000 < r["dist_hospital_m"].iloc[1] < 2400, r["dist_hospital_m"]
    r = contar_en_radio(r, hosp, 500, "hosp")
    assert r["n_hosp_500m"].tolist() == [1, 0, 0]
    assert 160 < distancia_epicentro_km(r).iloc[0] < 175  # Cali queda a ~165 km del epicentro

    df = pd.DataFrame({"id": range(4), "a": [0, 0.5, 1, np.nan], "b": [1, 0.5, 0, 1]})
    s = indice_riesgo(df, {"a": 3, "b": 1})
    assert list(s.round(3)) == [0.25, 0.5, 0.75, 1.0], s
    assert normalizar(pd.Series([0, 5, 10]), recorte=(0, 1)).tolist() == [0, 0.5, 1]
    sens = sensibilidad(df, {"base": {"a": 3, "b": 1}, "igual": {"a": 1, "b": 1}}, top=2)
    assert sens["spearman_vs_base"].iloc[0] == 1
    print("autoprueba OK")


autoprueba()
