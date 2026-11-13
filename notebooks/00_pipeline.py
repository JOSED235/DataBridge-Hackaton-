# Databricks notebook source
# Lógica del pipeline silver/gold en funciones puras (pandas/GeoPandas), sin Spark.
# Así se prueba en local con datos sintéticos (scripts/simular_pipeline.py) y en Databricks
# los notebooks 02 y 03 solo leen/escriben tablas y llaman a estas funciones.
# Requiere haber cargado antes 00_utils_espacial.

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------------------------
# CONFIGURACIÓN. TODO-VIERNES: ajustar al diccionario real de los datos oficiales.
# ---------------------------------------------------------------------------------------------
COLS = {                      # nombre estándar -> nombre en los datos oficiales (None si no viene)
    "id": "ID",
    "estado": "Estado_Estructural",
    "pisos": "NPISOS",
    "escombros": "Prob_Escombros",   # puede ser numérica (0..1 o 0..100) o categórica (Alta/Media/Baja)
    "comuna": "Comuna",
    "lon": "lon",
    "lat": "lat",
    "geom_wkt": None,                # si traen geometría en WKT (polígonos), poner aquí la columna
}

# Severidad 0..1 de cada valor de Estado_Estructural (minúsculas, sin tildes). TODO-VIERNES: valores reales.
SEVERIDAD_ESTADO = {
    "colapsado": 1.0, "destruido": 1.0, "dano severo": 0.85, "dano alto": 0.85,
    "dano moderado": 0.55, "dano medio": 0.55, "dano leve": 0.25, "dano bajo": 0.25,
    "sin dano": 0.0, "sin dano aparente": 0.0,
}
ESTADOS_SIN_DATO = {"sin dato", "sin datos", "sin informacion", "no disponible", "nd", "n/a", ""}
ESCOMBROS_CATEGORIA = {"muy alta": 1.0, "alta": 0.8, "media": 0.5, "moderada": 0.5, "baja": 0.2, "muy baja": 0.05, "nula": 0.0}
UMBRAL_ALTA_ESCOMBROS = 0.7   # prob >= umbral cuenta como "alta probabilidad de escombros"
METROS_POR_PISO = 3.0         # altura típica de entrepiso en vivienda colombiana

# Pesos del índice de riesgo ante réplicas (se re-escalan a suma 1). Justificación en docs/INDICE_RIESGO.md
PESOS = {
    "c_danio": 0.35,        # daño observado (prob. de escombros + estado estructural)
    "c_altura": 0.20,       # más pisos = más masa que puede caer y más ocupantes
    "c_exposicion": 0.15,   # densidad de edificios alrededor (proxy de población expuesta)
    "c_acceso_salud": 0.15, # lejanía al centro de salud más cercano
    "c_bloqueo_via": 0.15,  # sus escombros podrían bloquear una vía principal
}
ESCENARIOS_SENSIBILIDAD = {
    "base": PESOS,
    "pesos_iguales": {k: 1 for k in PESOS},
    "solo_danio_altura": {"c_danio": 0.6, "c_altura": 0.4},
    "enfasis_servicios": {**PESOS, "c_acceso_salud": 0.3, "c_bloqueo_via": 0.3},
    "enfasis_poblacion": {**PESOS, "c_exposicion": 0.35},
}


def _texto(s):
    """Minúsculas, sin tildes ni espacios sobrantes, para comparar categorías."""
    return (s.astype("string").str.strip().str.lower()
             .str.normalize("NFKD").str.encode("ascii", "ignore").str.decode("ascii")
             .str.replace(r"\s+", " ", regex=True))


def _prob_escombros(s):
    num = pd.to_numeric(s, errors="coerce")
    if num.notna().mean() > 0.5:                 # columna numérica
        return (num / 100 if num.max() > 1 else num).clip(0, 1)
    return _texto(s).map(ESCOMBROS_CATEGORIA)    # columna categórica


def limpiar(raw, cols=COLS):
    """bronze -> silver (sin cruces espaciales). Devuelve (DataFrame estándar, reporte de limpieza)."""
    c = {k: v for k, v in cols.items() if v and v in raw.columns}
    faltan = [k for k in ("id", "pisos") if k not in c] + ([] if "geom_wkt" in c or {"lon", "lat"} <= c.keys() else ["lon/lat o geom_wkt"])
    if faltan:
        raise KeyError(f"Columnas no encontradas: {faltan}. Revisar COLS contra: {list(raw.columns)}")

    df = pd.DataFrame(index=raw.index)
    df["id"] = raw[c["id"]].astype("string")
    df["pisos"] = pd.to_numeric(raw[c["pisos"]], errors="coerce")
    df["estado"] = raw[c["estado"]].astype("string") if "estado" in c else pd.NA
    estado_norm = _texto(df["estado"]) if "estado" in c else pd.Series(pd.NA, index=raw.index, dtype="string")
    df["sev_estado"] = estado_norm.map(SEVERIDAD_ESTADO)
    df["prob_escombros"] = _prob_escombros(raw[c["escombros"]]) if "escombros" in c else np.nan
    df["comuna"] = pd.to_numeric(raw[c["comuna"]].astype("string").str.extract(r"(\d+)")[0], errors="coerce").astype("Int64") if "comuna" in c else pd.NA
    for k in ("lon", "lat"):
        df[k] = pd.to_numeric(raw[c[k]], errors="coerce") if k in c else np.nan
    if "geom_wkt" in c:
        df["geom_wkt"] = raw[c["geom_wkt"]].astype("string")

    # TODO-VIERNES: confirmar cómo marcan los datos "sin datos satelitales".
    df["sin_dato_satelital"] = estado_norm.isin(ESTADOS_SIN_DATO).fillna(False) | (df["sev_estado"].isna() & df["prob_escombros"].isna())
    df["alta_escombros"] = df["prob_escombros"] >= UMBRAL_ALTA_ESCOMBROS

    reporte = {"filas_bronze": len(raw)}
    # Pisos fuera de rango físico en Cali (edificio más alto ~ 45 pisos): se anulan, no se borra el edificio.
    malos = ~df["pisos"].between(1, 60)
    reporte["pisos_invalidos_anulados"] = int((malos & df["pisos"].notna()).sum())
    df.loc[malos, "pisos"] = np.nan
    reporte["pisos_faltantes_imputados_mediana_comuna"] = int(df["pisos"].isna().sum())
    df["pisos_imputado"] = df["pisos"].isna()
    df["pisos"] = df["pisos"].fillna(df.groupby("comuna")["pisos"].transform("median")).fillna(df["pisos"].median())

    dup = df["id"].duplicated()
    reporte["duplicados_eliminados"] = int(dup.sum())
    df = df[~dup]
    sin_geo = df["lon"].isna() | df["lat"].isna() if "geom_wkt" not in df else df["geom_wkt"].isna()
    reporte["sin_coordenadas_eliminados"] = int(sin_geo.sum())
    df = df[~sin_geo]
    reporte["filas_silver"] = len(df)
    reporte["pct_sin_dato_satelital"] = round(100 * float(df["sin_dato_satelital"].mean()), 2)
    reporte["valores_estado_sin_mapear"] = sorted(set(estado_norm.dropna().unique()) - SEVERIDAD_ESTADO.keys() - ESTADOS_SIN_DATO)
    return df.reset_index(drop=True), reporte


def a_geo(df):
    if "geom_wkt" in df:
        return gpd.GeoDataFrame(df, geometry=gpd.GeoSeries.from_wkt(df["geom_wkt"]), crs=CRS_GEO)
    return a_gdf(df)


def enriquecer(gdf, comunas, barrios, salud, bomberos, vias):
    """Cruces espaciales con capas externas (OSM). Todas en EPSG:4326."""
    if gdf["comuna"].isna().any():  # completar comuna faltante con el polígono de OSM
        comunas = comunas.assign(comuna_osm=comunas["name"].str.extract(r"(\d+)")[0].astype(int))
        gdf = asignar_zona(gdf, comunas, "comuna_osm")
        gdf["comuna"] = gdf["comuna"].fillna(gdf.pop("comuna_osm")).astype("Int64")
    gdf = asignar_zona(gdf, barrios.rename(columns={"name": "barrio"}), "barrio")
    gdf = distancia_mas_cercana(gdf, salud, "salud")
    gdf = distancia_mas_cercana(gdf, bomberos, "bomberos")
    gdf = distancia_mas_cercana(gdf, vias, "via_principal")
    gdf = contar_en_radio(gdf, gdf, 100, "edif")  # incluye al propio edificio
    # Regla práctica: los escombros caen hasta una distancia similar a la altura del edificio.
    gdf["puede_bloquear_via"] = gdf["alta_escombros"].fillna(False) & (gdf["dist_via_principal_m"] <= gdf["pisos"] * METROS_POR_PISO)
    return gdf


def calcular_indice(gdf, pesos=PESOS):
    g = gdf.copy()
    g["c_danio"] = g[["prob_escombros", "sev_estado"]].mean(axis=1, skipna=True)  # NaN si no hay ninguno
    g["c_altura"] = normalizar(g["pisos"])
    g["c_exposicion"] = normalizar(g["n_edif_100m"])
    g["c_acceso_salud"] = normalizar(g["dist_salud_m"])
    g["c_bloqueo_via"] = g["puede_bloquear_via"].astype(float)
    g["indice_riesgo"] = indice_riesgo(g, pesos)
    q = g["indice_riesgo"].rank(pct=True)
    g["prioridad"] = np.select([q > 0.95, q > 0.85, q > 0.60], ["Muy alta", "Alta", "Media"], "Baja")
    g.loc[g["sin_dato_satelital"], "prioridad"] = "Sin dato: verificar en terreno"
    return g


def gold_comunas(g, comunas, salud, bomberos):
    agg = g.groupby("comuna").agg(
        n_edificios=("id", "size"),
        n_alta_escombros=("alta_escombros", "sum"),
        pct_alta_escombros=("alta_escombros", lambda s: round(100 * s.mean(), 2)),
        pct_sin_dato=("sin_dato_satelital", lambda s: round(100 * s.mean(), 2)),
        pisos_prom=("pisos", lambda s: round(s.mean(), 2)),
        indice_prom=("indice_riesgo", lambda s: round(s.mean(), 4)),
        indice_p90=("indice_riesgo", lambda s: round(s.quantile(0.9), 4)),
        n_prioridad_muy_alta=("prioridad", lambda s: int((s == "Muy alta").sum())),
        n_puede_bloquear_via=("puede_bloquear_via", "sum"),
        dist_salud_prom_m=("dist_salud_m", lambda s: round(s.mean(), 0)),
    ).reset_index()
    poli = comunas.assign(comuna=comunas["name"].str.extract(r"(\d+)")[0].astype(int))[["comuna", "geometry"]]
    for nombre, capa in (("n_salud", salud), ("n_bomberos", bomberos)):
        j = gpd.sjoin(capa[["geometry"]].to_crs(CRS_GEO), poli, predicate="within")
        agg = agg.merge(j.groupby("comuna").size().rename(nombre), on="comuna", how="left")
    agg[["n_salud", "n_bomberos"]] = agg[["n_salud", "n_bomberos"]].fillna(0).astype(int)
    agg["edif_alta_escombros_por_centro_salud"] = (agg["n_alta_escombros"] / agg["n_salud"].replace(0, np.nan)).round(1)
    agg["ranking"] = agg["indice_p90"].rank(ascending=False, method="min").astype(int)
    out = poli.merge(agg, on="comuna", how="left").sort_values("ranking")
    return gpd.GeoDataFrame(out, geometry="geometry", crs=CRS_GEO)


def para_spark(gdf):
    """GeoDataFrame -> pandas listo para spark.createDataFrame: geometría a WKT y pd.NA a None
    (los tipos 'string'/'Int64'/'boolean' de pandas con nulos pueden fallar en la conversión Arrow)."""
    df = pd.DataFrame(gdf.drop(columns="geometry")).assign(geom_wkt=gdf.geometry.to_wkt()) if "geometry" in gdf else gdf.copy()
    for c in df.columns:
        if isinstance(df[c].dtype, pd.api.extensions.ExtensionDtype):
            df[c] = df[c].astype(object).where(df[c].notna(), None)
    return df


COLS_VISOR = ["id", "comuna", "barrio", "estado", "pisos", "prob_escombros", "alta_escombros", "sin_dato_satelital",
              "dist_salud_m", "dist_via_principal_m", "puede_bloquear_via", "indice_riesgo", "prioridad"]


def exportar_visor(g, gc, carpeta):
    """Escribe los GeoJSON que consume visor/ (edificios.geojson y comunas.geojson)."""
    import os
    os.makedirs(carpeta, exist_ok=True)
    e = g[COLS_VISOR + ["geometry"]].to_crs(CRS_GEO).copy()
    e["pisos"] = e["pisos"].round(0).astype(int)
    e["comuna"] = e["comuna"].astype("float")  # Int64 con nulos no serializa en GeoJSON
    e.to_file(f"{carpeta}/edificios.geojson", driver="GeoJSON", COORDINATE_PRECISION=6)
    gc.to_file(f"{carpeta}/comunas.geojson", driver="GeoJSON", COORDINATE_PRECISION=6)
