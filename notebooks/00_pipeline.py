# Databricks notebook source
# Lógica del pipeline silver/gold en funciones puras (pandas/GeoPandas), sin Spark.
# Así se prueba en local con datos sintéticos (scripts/simular_pipeline.py) y en Databricks
# los notebooks 02 y 03 solo leen/escriben tablas y llaman a estas funciones.
# Requiere haber cargado antes 00_utils_espacial.

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------------------------
# CONFIGURACIÓN (datos oficiales: Datosprediales.json, 5.146 edificios, guía del evento)
# ---------------------------------------------------------------------------------------------
EQUIPO = "icesixuao"                       # la guía exige el nombre del equipo en tablas y volumen
ESQUEMA = "workspace.default"              # la guía pide trabajar en workspace.default
VOL = f"/Volumes/workspace/default/{EQUIPO}"  # volumen del equipo: edificios + capas externas
VOL_OUT = f"{VOL}/salidas"                 # GeoJSON exportados para el mapa


def tabla(capa, contenido):
    """Nombre completo según la guía: workspace.default.<capa>_<equipo>_<contenido>."""
    return f"{ESQUEMA}.{capa}_{EQUIPO}_{contenido}"


COLS = {                      # nombre estándar -> nombre en los datos oficiales (None si no viene)
    "id": "OBJECTID",                  # ID_PREDIO es nulo en 1.509 filas; OBJECTID es único
    "estado": "Estado_Estructural",
    "pisos": "NPISOS",
    "escombros": None,                 # no hay probabilidad: Indice_Escombros es un puntaje con signo (ver abajo)
    "indice_escombros": "Indice_Escombros",
    "comuna": "COMUNA",
    "barrio_cod": "BARRIO",            # el código se repite entre comunas: solo sirve junto con COMUNA
    "lon": None,
    "lat": None,
    "geom_wkt": "geom_wkt",            # contorno del edificio en WKT (lo crea bronze desde el GeoJSON)
}

# Severidad 0..1 de cada valor de Estado_Estructural (minúsculas, sin tildes).
# Indice_Escombros tiene dos colas de daño: > 4,3 escombros y < -10,8 techo desaparecido; por eso se usa la categoría.
SEVERIDAD_ESTADO = {
    "alta probabilidad de escombros": 1.0,
    "posible desaparicion de techo": 0.7,       # falla visible de la cubierta, menos que escombros
    "sin cambio aparente / dano interno": 0.1,  # la guía: "sin cambio aparente" no significa "sin daño"
}
ESTADOS_SIN_DATO = {"sin datos satelitales", "sin dato", "sin datos", "sin informacion", "no disponible", "nd", "n/a", ""}
ESCOMBROS_CATEGORIA = {"muy alta": 1.0, "alta": 0.8, "media": 0.5, "moderada": 0.5, "baja": 0.2, "muy baja": 0.05, "nula": 0.0}
UMBRAL_ALTA_ESCOMBROS = 0.7   # prob >= umbral cuenta como "alta probabilidad de escombros"
METROS_POR_PISO = 3.0         # altura típica de entrepiso en vivienda colombiana

# Pesos del índice de riesgo ante réplicas (se re-escalan a suma 1). Justificación en docs/INDICE_RIESGO.md
PESOS = {
    "c_danio": 0.25,          # daño observado desde el satélite (categoría de Estado_Estructural)
    "c_vulnerabilidad": 0.20, # prob. de ductilidad baja o nula según la tipología (GEM exposición)
    "c_exposicion": 0.15,     # ocupantes del edificio (GEM, censo 2018)
    "c_suelo": 0.10,          # amplificación en el período del edificio + susceptibilidad a licuación (GEM)
    "c_altura": 0.10,         # más pisos = más masa que puede caer
    "c_acceso_salud": 0.10,   # lejanía al centro de salud más cercano (OSM)
    "c_bloqueo_via": 0.10,    # sus escombros podrían bloquear una vía principal (OSM)
}
# Borradores anteriores: quedan como escenarios para mostrar cuánto cambia el ranking.
PESOS_SIN_SUELO = {"c_danio": 0.35, "c_altura": 0.20, "c_exposicion": 0.15, "c_acceso_salud": 0.15, "c_bloqueo_via": 0.15}
ESCENARIOS_SENSIBILIDAD = {
    "base": PESOS,
    "solo_datos_oficiales": {"c_danio": 0.6, "c_altura": 0.4},
    "sin_fuentes_gem": {k: v for k, v in PESOS.items() if k not in ("c_vulnerabilidad", "c_suelo")},
    "sin_suelo": PESOS_SIN_SUELO,
    "pesos_iguales": {k: 1 for k in PESOS},
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


def bronze_desde_geojson(g):
    """GeoDataFrame -> pandas para bronze: copia fiel, todo como texto, con nulos reales (no 'nan'/'None')
    y la geometría en WKT. Los tipos se corrigen en silver. Columnas 100 % nulas también pasan (como texto)."""
    # Evitar que el redondeo predeterminado cree autointersecciones o pegue anillos.
    df = pd.DataFrame(g.drop(columns="geometry")).assign(geom_wkt=g.geometry.to_wkt(rounding_precision=-1))
    return df.apply(lambda s: s.map(lambda v: None if v is None or (isinstance(v, float) and np.isnan(v)) else str(v)))


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
    if "indice_escombros" in c:
        df["indice_escombros"] = pd.to_numeric(raw[c["indice_escombros"]], errors="coerce")
    if "barrio_cod" in c:  # strip: la guía avisa de valores con solo espacios
        df["barrio_cod"] = raw[c["barrio_cod"]].astype("string").str.strip().replace("", pd.NA)

    # Sin dato = categoría "Sin datos satelitales" (o sin estado ni probabilidad). No se borran: se verifican en terreno.
    df["sin_dato_satelital"] = estado_norm.isin(ESTADOS_SIN_DATO).fillna(False) | (df["sev_estado"].isna() & df["prob_escombros"].isna())
    df["alta_escombros"] = (df["prob_escombros"] >= UMBRAL_ALTA_ESCOMBROS) | (df["sev_estado"] >= 1.0)

    reporte = {"filas_bronze": len(raw)}
    # NPISOS = 0: según los organizadores, predio sin edificación registrada en catastro (no es error de carga).
    # Se conserva el predio (el satélite sí ve daño en muchos), pero sin pisos: no se imputa ni entra al promedio de altura.
    df["sin_construccion_registrada"] = df["pisos"].eq(0)
    reporte["predios_sin_construccion_registrada"] = int(df["sin_construccion_registrada"].sum())
    # Pisos fuera de rango físico en Cali (edificio más alto ~ 45 pisos): se anulan, no se borra el edificio.
    malos = (df["pisos"] > 60) | (df["pisos"] < 0)
    reporte["pisos_invalidos_anulados"] = int(malos.sum())
    df.loc[malos | df["sin_construccion_registrada"], "pisos"] = np.nan
    # Solo los nulos (o inválidos) con construcción registrada se imputan: GEM en silver y, si no, mediana de la comuna.
    df["pisos_imputado"] = df["pisos"].isna() & ~df["sin_construccion_registrada"]
    reporte["pisos_nulos_a_imputar"] = int(df["pisos_imputado"].sum())
    mediana = df.groupby("comuna")["pisos"].transform("median").fillna(df["pisos"].median())
    df.loc[df["pisos_imputado"], "pisos"] = mediana[df["pisos_imputado"]]

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
    """Silver a GeoDataFrame. Los polígonos inválidos (autointersecciones) se reparan con make_valid
    en vez de borrarse, y se agrega el área real en m² (Shape__Area viene en grados)."""
    if "geom_wkt" not in df:
        return a_gdf(df)
    g = gpd.GeoDataFrame(df, geometry=gpd.GeoSeries.from_wkt(df["geom_wkt"]), crs=CRS_GEO)
    g["geom_reparada"] = ~g.is_valid
    g.loc[g["geom_reparada"], "geometry"] = g.loc[g["geom_reparada"]].make_valid()
    g["geom_wkt"] = g.geometry.to_wkt(rounding_precision=-1)
    g["area_m2"] = g.to_crs(CRS_METROS).area.round(1)
    return g


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


# Suelo: microzonificación INGEOMINAS-DAGMA (2005) con las funciones de amplificación de GEM TREQ.
NIVEL_AF = 0.2267   # aceleración en roca (g) con la que se lee la función de amplificación (fila del CSV de GEM)
PERIODOS_AF = np.array([0.1, 0.2, 0.3, 0.6, 1.0, 2.0])  # períodos (s) que trae el CSV de GEM


def leer_suelo(carpeta):
    """(grilla de microzonas como GeoDataFrame, funciones de amplificación) desde los CSV de GEM en `carpeta`."""
    grilla = pd.read_csv(f"{carpeta}/gem_microzonas_grilla.csv", dtype={"ampcode": str})
    amplif = pd.read_csv(f"{carpeta}/gem_amplificacion_suelo.csv", comment="#", dtype={"ampcode": str})
    return a_gdf(grilla), amplif


def asignar_suelo(gdf, grilla, amplif):
    """Agrega `microzona` (punto más cercano de la grilla GEM, ~750 m), `periodo_s` (período propio del
    edificio, T ≈ pisos/10 s) y `amplif_suelo`: cuánto amplifica su microzona justo en ese período.
    Fuera de la microzonificación ('noaf') el factor es 1, como en el modelo de GEM."""
    j = gpd.sjoin_nearest(gdf[["geometry"]].to_crs(CRS_METROS), grilla[["ampcode", "geometry"]].to_crs(CRS_METROS), how="left")
    out = gdf.copy()
    out["microzona"] = j.groupby(level=0)["ampcode"].first().reindex(gdf.index).astype(str)
    t = (out["pisos"].fillna(1) / 10).to_numpy()[:, None]  # sin pisos registrados: se lee como 1 piso (período corto)
    out["periodo_s"] = PERIODOS_AF[np.abs(t - PERIODOS_AF).argmin(axis=1)]
    fila = amplif[np.isclose(amplif["level"], NIVEL_AF)]
    af = {(str(r["ampcode"]), p): r[f"SA({p})"] for _, r in fila.iterrows() for p in PERIODOS_AF}
    out["amplif_suelo"] = [round(af.get((z, p), 1.0), 3) for z, p in zip(out["microzona"], out["periodo_s"])]
    return out


# Fuentes sísmicas y de exposición (scripts/descargar_externos.py; detalle en docs/FUENTES.md).
DIST_MAX_GEM_M = 15  # el 95 % de los edificios oficiales tiene un punto GEM a menos de 9 m
PISOS_GEM = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6-10": 8, "11+": 12}
SUSC_LICUACION = {"vh": 1.0, "h": 0.8, "m": 0.5, "l": 0.25, "vl": 0.1, "n": 0.0}  # muy alta ... nula (GEM)


def _mas_cercano(gdf, puntos, cols, max_m=None):
    """Copia `cols` del punto más cercano (si es un polígono y el punto cae dentro, la distancia es 0).
    Para grillas regulares (sitio, ShakeMap) los empates exactos son raros y vecinos casi idénticos."""
    j = gpd.sjoin_nearest(gdf[["geometry"]].to_crs(CRS_METROS), puntos[cols + ["geometry"]].to_crs(CRS_METROS),
                          how="left", max_distance=max_m, distance_col="_d")
    return j[~j.index.duplicated(keep="first")].reindex(gdf.index)


def cruzar_externos(gdf, carpeta):
    """Une a cada edificio:
    - GEM exposición (edificio GEM dentro del polígono o a <= 15 m): año, estrato, uso, pisos, ocupantes, valor y vulnerabilidad.
      En 1.669 edificios hay varios registros GEM empatados (mismo punto o varios dentro del polígono): los ocupantes
      se suman y los atributos salen del registro con más ocupantes (desempate por id). Así el resultado no depende
      del orden interno del índice espacial y es igual en local y en Databricks.
      Si NPISOS era nulo, se toman los pisos de GEM antes que la mediana de la comuna (NPISOS = 0 no se imputa).
    - GEM sitio: susceptibilidad a licuación y pendiente del sitio más cercano.
    - USGS ShakeMap: intensidad y aceleraciones del nodo más cercano (~1 km)."""
    out = gdf.copy()
    ex = a_gdf(pd.read_csv(f"{carpeta}/gem_exposicion.csv", dtype={"MICROZONE": str, "FLOORS": str}))
    cols = ["id", "CONSTRUCTION_PERIOD", "INCOME_LEVEL", "FLOORS", "OCCUPANCY", "night", "structural",
            "p_ductilidad_baja", "p_mamposteria_no_reforzada"]
    todos = gpd.sjoin_nearest(out[["geometry"]].to_crs(CRS_METROS), ex[cols + ["geometry"]].to_crs(CRS_METROS),
                              how="left", max_distance=DIST_MAX_GEM_M, distance_col="_d")
    ocupantes = todos.groupby(level=0)["night"].sum(min_count=1)
    valor = todos.groupby(level=0)["structural"].sum(min_count=1)
    j = (todos.assign(_n=todos["night"].fillna(-1)).sort_values(["_n", "id"], ascending=[False, True], kind="mergesort")
         .pipe(lambda d: d[~d.index.duplicated(keep="first")]).reindex(out.index))
    out["n_registros_gem"] = todos["id"].notna().groupby(level=0).sum().reindex(out.index)
    out["dist_gem_m"] = j["_d"].round(1)
    out["periodo_construccion"] = j["CONSTRUCTION_PERIOD"]
    out["estrato"] = j["INCOME_LEVEL"].astype("Int64")
    out["uso"] = j["OCCUPANCY"]
    out["pisos_gem"] = j["FLOORS"].map(PISOS_GEM)
    out["ocupantes_noche"] = ocupantes.reindex(out.index)
    out["valor_reemplazo_usd"] = valor.reindex(out.index).round(0)
    out["p_ductilidad_baja"] = j["p_ductilidad_baja"]
    out["p_mamposteria_no_reforzada"] = j["p_mamposteria_no_reforzada"]
    usar_gem = out["pisos_imputado"] & out["pisos_gem"].notna()
    out["pisos_fuente"] = np.select([out["sin_construccion_registrada"], ~out["pisos_imputado"], usar_gem],
                                    ["sin_construccion_registrada", "oficial", "gem"], "mediana_comuna")
    out.loc[usar_gem, "pisos"] = out.loc[usar_gem, "pisos_gem"]

    sitio = a_gdf(pd.read_csv(f"{carpeta}/gem_sitio_licuacion_ladera.csv"))
    j = _mas_cercano(out, sitio, ["liq_susc_cat", "pendiente_grados"])
    out["licuacion_cat"] = j["liq_susc_cat"]
    out["licuacion"] = j["liq_susc_cat"].map(SUSC_LICUACION)
    out["pendiente_grados"] = j["pendiente_grados"]

    sm = a_gdf(pd.read_csv(f"{carpeta}/usgs_shakemap_cali.csv"))
    j = _mas_cercano(out, sm, ["mmi", "pga", "psa10"])
    out["mmi"] = j["mmi"]
    out["pga_g"] = (j["pga"] / 100).round(3)    # ShakeMap entrega %g
    out["psa10_g"] = (j["psa10"] / 100).round(3)
    return out


def calcular_indice(gdf, pesos=PESOS):
    g = gdf.copy()
    g["c_danio"] = g[["prob_escombros", "sev_estado"]].mean(axis=1, skipna=True)  # NaN si no hay ninguno
    # Sin una capa externa, su componente queda NaN y su peso se reparte entre los demás.
    g["c_vulnerabilidad"] = g["p_ductilidad_baja"] if "p_ductilidad_baja" in g else np.nan
    suelo = [normalizar(g["amplif_suelo"])] if "amplif_suelo" in g else []
    suelo += [g["licuacion"]] if "licuacion" in g else []
    g["c_suelo"] = pd.concat(suelo, axis=1).mean(axis=1) if suelo else np.nan
    g["c_altura"] = normalizar(g["pisos"])
    g["c_exposicion"] = normalizar(g["ocupantes_noche"]) if "ocupantes_noche" in g else normalizar(g["n_edif_100m"])
    g["c_acceso_salud"] = normalizar(g["dist_salud_m"])
    g["c_bloqueo_via"] = g["puede_bloquear_via"].astype(float)
    g["indice_riesgo"] = indice_riesgo(g, pesos)
    # El ranking de inspección es de edificios con dato satelital. Los predios sin dato y los sin construcción
    # registrada (NPISOS = 0) quedan fuera del percentil, con su propia categoría para verificar en terreno.
    lote = g["sin_construccion_registrada"] if "sin_construccion_registrada" in g else False
    g["en_ranking"] = ~g["sin_dato_satelital"] & ~lote
    q = g.loc[g["en_ranking"], "indice_riesgo"].rank(pct=True).reindex(g.index)
    # Plata usa tipos nullable: NumPy requiere booleanos puros y no acepta pd.NA en condiciones.
    condiciones = [(q > corte).to_numpy(dtype=bool, na_value=False) for corte in (0.95, 0.85, 0.60)]
    g["prioridad"] = np.select(condiciones, ["Muy alta", "Alta", "Media"], "Baja")
    g.loc[g["en_ranking"].eq(False) & lote, "prioridad"] = "Sin construcción registrada: verificar"
    g.loc[g["sin_dato_satelital"], "prioridad"] = "Sin dato: verificar en terreno"
    return g


def gold_comunas(g, comunas, salud, bomberos):
    agg = g.groupby("comuna").agg(
        n_edificios=("id", "size"),
        n_alta_escombros=("alta_escombros", "sum"),
        pct_alta_escombros=("alta_escombros", lambda s: round(100 * s.mean(), 2)),
        pct_sin_dato=("sin_dato_satelital", lambda s: round(100 * s.mean(), 2)),
        pisos_prom=("pisos", lambda s: round(s.mean(), 2)),
        # Índice de la comuna solo con edificios del ranking: sin dato y lotes tienen categoría propia.
        indice_prom=("indice_riesgo", lambda s: round(s[g.loc[s.index, "en_ranking"].astype(bool)].mean(), 4)),
        indice_p90=("indice_riesgo", lambda s: round(s[g.loc[s.index, "en_ranking"].astype(bool)].quantile(0.9), 4)),
        n_prioridad_muy_alta=("prioridad", lambda s: int((s == "Muy alta").sum())),
        n_puede_bloquear_via=("puede_bloquear_via", "sum"),
        dist_salud_prom_m=("dist_salud_m", lambda s: round(s.mean(), 0)),
        amplif_suelo_prom=("amplif_suelo", lambda s: round(s.mean(), 3)),
        microzona_predominante=("microzona", lambda s: s.mode().iat[0]),
    ).reset_index()
    if "ocupantes_noche" in g:  # fuentes GEM y USGS
        ext = g.groupby("comuna").agg(
            ocupantes_noche=("ocupantes_noche", "sum"),
            ocupantes_en_edif_con_danio=("ocupantes_noche", lambda s: s[g.loc[s.index, "sev_estado"] >= 0.7].sum()),
            pct_antes_1985=("periodo_construccion", lambda s: round(100 * s.isin(["<= 1960", "1961 - 1985"]).mean(), 1)),
            p_ductilidad_baja_prom=("p_ductilidad_baja", lambda s: round(s.mean(), 3)),
            pct_licuacion_alta=("licuacion", lambda s: round(100 * (s >= 0.8).mean(), 1)),
            mmi_prom=("mmi", lambda s: round(s.mean(), 2)),
        ).reset_index()
        agg = agg.merge(ext, on="comuna", how="left")
    if "area_m2" in g:  # la guía: los edificios sin dato pesan mucho más en área que en número
        area = g.groupby("comuna").apply(lambda d: round(100 * d.loc[d["sin_dato_satelital"], "area_m2"].sum() / d["area_m2"].sum(), 2))
        agg = agg.merge(area.rename("pct_area_sin_dato"), on="comuna", how="left")
    poli = comunas.assign(comuna=comunas["name"].str.extract(r"(\d+)")[0].astype(int))[["comuna", "geometry"]]
    for nombre, capa in (("n_salud", salud), ("n_bomberos", bomberos)):
        j = gpd.sjoin(capa[["geometry"]].to_crs(CRS_GEO), poli, predicate="within")
        agg = agg.merge(j.groupby("comuna").size().rename(nombre), on="comuna", how="left")
    agg[["n_salud", "n_bomberos"]] = agg[["n_salud", "n_bomberos"]].fillna(0).astype(int)
    agg["edif_alta_escombros_por_centro_salud"] = (agg["n_alta_escombros"] / agg["n_salud"].replace(0, np.nan)).round(1)
    agg["ranking"] = agg["indice_p90"].rank(ascending=False, method="min").astype(int)
    out = poli.merge(agg, on="comuna", how="inner").sort_values("ranking")  # solo comunas con edificios
    return gpd.GeoDataFrame(out, geometry="geometry", crs=CRS_GEO)


def para_spark(gdf):
    """GeoDataFrame -> pandas listo para spark.createDataFrame: geometría a WKT y pd.NA a None
    (los tipos 'string'/'Int64'/'boolean' de pandas con nulos pueden fallar en la conversión Arrow)."""
    df = pd.DataFrame(gdf.drop(columns="geometry")).assign(geom_wkt=gdf.geometry.to_wkt(rounding_precision=-1)) if "geometry" in gdf else gdf.copy()
    for c in df.columns:
        if isinstance(df[c].dtype, pd.api.extensions.ExtensionDtype):
            df[c] = df[c].astype(object).where(df[c].notna(), None)
    return df


COLS_VISOR = ["id", "comuna", "barrio", "estado", "sev_estado", "area_m2", "pisos", "sin_construccion_registrada", "prob_escombros", "alta_escombros", "sin_dato_satelital",
              "dist_salud_m", "dist_via_principal_m", "puede_bloquear_via", "microzona", "amplif_suelo",
              "periodo_construccion", "estrato", "ocupantes_noche", "p_ductilidad_baja", "licuacion_cat", "mmi",
              "indice_riesgo", "prioridad", "pisos_observados", "pisos_estimados", "pisos_fuente",
              "motivos_principales", "peso_base_disponible", "posicion", "cola_trabajo", "gem_ambiguo", "gem_reutilizado"]


def exportar_visor(g, gc, carpeta):
    """Escribe los GeoJSON que consume visor/ (edificios.geojson y comunas.geojson)."""
    import os
    os.makedirs(carpeta, exist_ok=True)
    e = g[[c for c in COLS_VISOR if c in g] + ["geometry"]].to_crs(CRS_GEO).copy()
    e["pisos"] = pd.to_numeric(e["pisos"], errors="coerce").round(0).astype("float64")  # NULL conserva desconocido/lote; ver bandera predial
    e["comuna"] = e["comuna"].astype("float")  # Int64 con nulos no serializa en GeoJSON
    e.to_file(f"{carpeta}/edificios.geojson", driver="GeoJSON", COORDINATE_PRECISION=6)
    gc.to_file(f"{carpeta}/comunas.geojson", driver="GeoJSON", COORDINATE_PRECISION=6)
