# Databricks notebook source
# Funciones de plata. Cargar después de 00_utils_espacial y 00_pipeline.
# Sin Spark ni descargas: las mismas transformaciones se ejecutan en local y en 02_silver.
from pathlib import Path
import hashlib
import json
import re
from datetime import datetime, timezone

import geopandas as gpd
import numpy as np
import pandas as pd


ARCHIVOS_PLATA = {
    **{f"osm_{n}": f"osm_{n}.geojson" for n in
       ("comunas", "barrios", "salud", "emergencia", "educacion", "puntos_encuentro", "vias_principales")},
    **{n: f"{n}.csv" for n in ("gem_microzonas_grilla", "gem_amplificacion_suelo", "gem_exposicion",
                              "gem_sitio_licuacion_ladera", "usgs_shakemap_cali")},
    **{n: f"{n}.geojson" for n in ("usgs_sismos_2026_08", "usgs_replicas", "usgs_estaciones_cali")},
}
ARCHIVOS_PLATA["usgs_sismos_2026_08"] = "usgs_sismos_2026-08.geojson"


def texto_plata(s):
    """Normaliza espacios y blancos sin borrar códigos válidos como '00'."""
    return s.astype("string").str.strip().replace("", pd.NA)


def columna_plata(df, nombre):
    return texto_plata(df[nombre]) if nombre in df else pd.Series(pd.NA, index=df.index, dtype="string")


def exigir_identidad(df, columnas, nombre):
    if df[columnas].isna().any().any() or df.duplicated(columnas).any():
        raise ValueError(f"{nombre}: identidad nula o repetida en {columnas}; corregir origen antes de publicar")


def geometria_plata(df):
    """Reconstruye una capa bronze de texto sin redondear el WKT."""
    if isinstance(df, gpd.GeoDataFrame):
        # USGS se lee como EPSG:4979 por incluir profundidad Z; unificar el CRS horizontal
        # sin eliminar la coordenada Z (se conserva también como profundidad_km).
        return df.to_crs(CRS_GEO).copy()
    if "geom_wkt" in df:
        return gpd.GeoDataFrame(df.drop(columns="geom_wkt").copy(),
                                geometry=gpd.GeoSeries.from_wkt(df.geom_wkt, index=df.index), crs=CRS_GEO)
    return a_gdf(df.assign(lon=pd.to_numeric(df.lon, errors="coerce"),
                          lat=pd.to_numeric(df.lat, errors="coerce")))


def leer_fuentes_plata(carpeta):
    """Lectura local equivalente a las tablas bronze; no descarga ni modifica archivos."""
    fuentes = {}
    for nombre, archivo in ARCHIVOS_PLATA.items():
        ruta = Path(carpeta) / archivo
        fuentes[nombre] = (gpd.read_file(ruta) if ruta.suffix == ".geojson" else
                           pd.read_csv(ruta, comment="#", dtype=str, keep_default_na=False).replace("", None))
    return fuentes


def limpiar_predios_plata(raw):
    ids = texto_plata(raw[COLS["id"]])
    exigir_identidad(pd.DataFrame({"id": ids}), ["id"], "predios")
    # No permitir que limpiar() descarte filas sin dejar constancia.
    if columna_plata(raw, "geom_wkt").isna().any():
        raise ValueError("predios: geometría ausente; resolver antes de publicar plata")
    out, reporte = limpiar(raw)
    out["id"] = ids.reset_index(drop=True)
    fuente = raw.reset_index(drop=True)
    out["npisos_original"] = fuente[COLS["pisos"]].astype("string")
    pisos = pd.to_numeric(out.npisos_original, errors="coerce")
    out["pisos_observados"] = pisos.where(pisos.between(1, 60) & pisos.mod(1).eq(0))
    reporte["pisos_invalidos_anulados"] = int((pisos.notna() & ~pisos.eq(0) & out.pisos_observados.isna()).sum())
    out["estado_predial"] = np.select([out.sin_construccion_registrada, out.pisos_observados.notna()],
                                      ["sin_construccion_registrada", "con_pisos_registrados"], "pisos_desconocidos")
    # Pisos efectivos siguen separados de los observados; las estimaciones se resuelven al cruzar GEM.
    out["pisos"] = out.pisos_observados
    out["pisos_imputado"] = False
    out["estado_original"] = fuente[COLS["estado"]].astype("string")
    out["estado"] = texto_plata(out.estado_original)
    out["estado_normalizado"] = _texto(out.estado)
    out["comuna_original"] = columna_plata(fuente, "COMUNA")
    for campo in ("ID_PREDIO", "EDIFPRED"):
        out[campo.lower()] = columna_plata(fuente, campo)
    out["geom_wkt_original"] = fuente.geom_wkt
    out["atributos_originales_json"] = fuente.drop(columns="geom_wkt").apply(
        lambda fila: json.dumps({k: None if pd.isna(v) else str(v) for k, v in fila.items()},
                                ensure_ascii=False, sort_keys=True), axis=1)
    g = a_geo(out)
    if g.geometry.isna().any() or g.is_empty.any() or (~g.is_valid).any():
        raise ValueError("predios: geometría no utilizable después de make_valid; publicación detenida")
    firmas = g.geom_wkt_original
    g["contorno_repetido"] = firmas.duplicated(keep=False)
    estados_por_contorno = g.groupby("geom_wkt_original").estado_original.transform("nunique")
    g["contorno_estado_contradictorio"] = g.contorno_repetido & estados_por_contorno.gt(1)
    g["discrepancia_lote_satelite"] = g.sin_construccion_registrada & g.sev_estado.ge(.7)
    reporte["geometrias_reparadas"] = int(g.geom_reparada.sum())
    return g, reporte


def territorios_plata(fuentes):
    partes = []
    for tipo in ("comunas", "barrios"):
        g = geometria_plata(fuentes[f"osm_{tipo}"])
        t = gpd.GeoDataFrame(index=g.index, geometry=g.geometry, crs=g.crs)
        t["osm_id"] = columna_plata(g, "osm_id")
        t["tipo"] = tipo
        t["id"] = tipo + ":" + t.osm_id
        t["nombre"] = columna_plata(g, "name")
        t["codigo"] = (t.nombre.str.extract(r"(\d+)")[0] if tipo == "comunas" else columna_plata(g, "ref"))
        t["comuna_etiqueta_osm"] = columna_plata(g, "comuna")
        t["fuente"] = f"osm_{tipo}"
        partes.append(t)
    return gpd.GeoDataFrame(pd.concat(partes, ignore_index=True), crs=CRS_GEO)


def servicios_plata(fuentes):
    partes = []
    for nombre in ("osm_salud", "osm_emergencia", "osm_educacion", "osm_puntos_encuentro"):
        if nombre not in fuentes:
            continue
        g = geometria_plata(fuentes[nombre])
        t = gpd.GeoDataFrame(index=g.index, geometry=g.geometry, crs=g.crs)
        t["osm_id"] = columna_plata(g, "osm_id")
        t["id"] = nombre + ":" + t.osm_id
        t["nombre"] = columna_plata(g, "name")
        t["tipo"] = columna_plata(g, "amenity")
        t["urgencias"] = columna_plata(g, "emergency").str.lower().map({"yes": "si", "no": "no"}).fillna("sin_dato")
        t["operatividad"] = columna_plata(g, "operational_status")
        t["capacidad"] = pd.to_numeric(columna_plata(g, "capacity"), errors="coerce")
        t["uso_analitico"] = "contexto_educativo" if nombre == "osm_educacion" else "servicio_mapeado"
        t["fuente"] = nombre
        partes.append(t)
    return gpd.GeoDataFrame(pd.concat(partes, ignore_index=True), crs=CRS_GEO)


def vias_plata(raw):
    g = geometria_plata(raw)
    t = gpd.GeoDataFrame(index=g.index, geometry=g.geometry, crs=g.crs)
    t["osm_id"] = columna_plata(g, "osm_id")
    t["id"] = "via:" + t.osm_id
    for destino, origen in {"nombre": "name", "jerarquia": "highway", "acceso": "access",
                            "sentido_unico": "oneway", "velocidad_etiqueta": "maxspeed"}.items():
        t[destino] = columna_plata(g, origen)
    t["longitud_m"] = t.to_crs(CRS_METROS).length
    t["fuente"] = "osm_vias_principales"
    return t


def puntos_plata(raw, prefijo, renombres, numericas):
    d = pd.DataFrame(raw.drop(columns="geometry", errors="ignore")).copy()
    # La llave de grilla se deriva de coordenadas conservadas, no del orden de filas.
    lon, lat = pd.to_numeric(d.lon, errors="coerce"), pd.to_numeric(d.lat, errors="coerce")
    out = pd.DataFrame({"id": prefijo + ":" + lon.map(repr) + ":" + lat.map(repr), "lon": lon, "lat": lat})
    for origen, destino in renombres.items():
        out[destino] = (pd.to_numeric(d[origen], errors="coerce") if origen in numericas else columna_plata(d, origen))
    out["fuente"] = prefijo
    return gpd.GeoDataFrame(out, geometry=gpd.points_from_xy(lon, lat), crs=CRS_GEO)


def amplificacion_plata(raw):
    d = raw.copy()
    filas = []
    for columna in ("PGA", "SA(0.1)", "SA(0.2)", "SA(0.3)", "SA(0.6)", "SA(1.0)", "SA(2.0)"):
        # 01_bronze sustituye caracteres rechazados por Delta. Aceptar también el CSV original.
        for nombre in (columna, f"sigma_{columna}"):
            if nombre not in d:
                nombre_delta = re.sub(r"[ ,;{}()\n\t=]", "_", nombre).strip("_")
                d[nombre] = d[nombre_delta]
        periodo = 0. if columna == "PGA" else float(columna[3:-1])
        filas.append(pd.DataFrame({"ampcode": texto_plata(d.ampcode),
                                  "nivel_roca_g": pd.to_numeric(d["level"], errors="coerce"),
                                  "imt": "PGA" if columna == "PGA" else "SA", "periodo_s": periodo,
                                  "factor": pd.to_numeric(d[columna], errors="coerce"),
                                  "sigma": pd.to_numeric(d[f"sigma_{columna}"], errors="coerce"),
                                  "vs30_ref_m_s": 800., "fuente": "gem_amplificacion_suelo"}))
    return pd.concat(filas, ignore_index=True)


def exposicion_plata(raw):
    renombres = {"id": "id", "FLOORS": "pisos_categoria", "CONSTRUCTION_PERIOD": "periodo_construccion",
                 "INCOME_LEVEL": "estrato", "OCCUPANCY": "uso", "night": "ocupantes_noche",
                 "structural": "valor_reemplazo_usd", "MICROZONE": "microzona_gem", "COMUNA": "comuna_gem",
                 "p_ductilidad_baja": "p_ductilidad_baja", "p_mamposteria_no_reforzada": "p_mamposteria_no_reforzada"}
    out = puntos_plata(raw, "gem_exposicion", renombres,
                       {"INCOME_LEVEL", "night", "structural", "COMUNA", "p_ductilidad_baja", "p_mamposteria_no_reforzada"})
    categoria = out.pisos_categoria
    out["pisos_min"] = pd.to_numeric(categoria.str.extract(r"^(\d+)")[0], errors="coerce")
    out["pisos_max"] = pd.to_numeric(categoria.str.extract(r"(?:^|-)(\d+)$")[0], errors="coerce")
    # Estimadores heredados, explícitos: 6-10 -> 8 y 11+ -> 12 no son pisos observados.
    out["pisos_gem_estimados"] = categoria.map(PISOS_GEM)
    out["coordenada_compartida"] = out.duplicated(["lon", "lat"], keep=False)
    out["precision_coordenada"] = "extracto_redondeado_4_decimales"
    return out


def cruzar_territorio(predios, zonas):
    pts = gpd.GeoDataFrame(index=predios.index,
                           geometry=predios.to_crs(CRS_METROS).centroid, crs=CRS_METROS)
    j = gpd.sjoin(pts, zonas[["id", "geometry"]].to_crs(CRS_METROS).rename(columns={"id": "id_territorio"}),
                  how="left", predicate="within")
    n = j.id_territorio.notna().groupby(level=0).sum().reindex(predios.index, fill_value=0)
    unica = j[j.id_territorio.notna()].copy()
    unica = unica[unica.index.map(n) == 1]
    out = pd.DataFrame({"n_coincidencias": n, "id_territorio": unica.id_territorio.reindex(predios.index)})
    relaciones = j[j.id_territorio.notna()][["id_territorio"]].copy()
    relaciones.insert(0, "id_predio", predios.id.reindex(relaciones.index).to_numpy())
    return out, relaciones.reset_index(drop=True)


def vecino_plata(predios, objetivos, max_m=None, limitar_cobertura=False):
    """Vecino al contorno; empates por llave estable. Nunca multiplica la tabla de predios."""
    out = pd.DataFrame(index=predios.index, columns=["id_objetivo", "distancia_m", "n_coincidencias"])
    out["distancia_m"] = np.nan
    out["n_coincidencias"] = 0
    out["dentro_cobertura"] = False
    if objetivos.empty:
        return out
    a, b = predios.to_crs(CRS_METROS), objetivos[["id", "geometry"]].to_crs(CRS_METROS)
    j = gpd.sjoin_nearest(a[["geometry"]], b.rename(columns={"id": "id_objetivo"}),
                          how="left", max_distance=max_m, distance_col="distancia_m")
    out["n_coincidencias"] = j.id_objetivo.notna().groupby(level=0).sum().reindex(out.index, fill_value=0)
    elegido = j.sort_values(["distancia_m", "id_objetivo"], kind="stable").loc[lambda d: ~d.index.duplicated()]
    out["dentro_cobertura"] = (a.centroid.covered_by(b.geometry.union_all().convex_hull)
                               if limitar_cobertura else elegido.id_objetivo.notna().reindex(a.index))
    out["id_objetivo"] = elegido.id_objetivo.reindex(a.index).where(out.dentro_cobertura)
    out["distancia_m"] = elegido.distancia_m.reindex(a.index).where(out.dentro_cobertura)
    return out


def candidatos_gem(predios, exposicion):
    columnas = ["id", "ocupantes_noche", "valor_reemplazo_usd", "geometry"]
    j = gpd.sjoin_nearest(predios[["id", "geometry"]].rename(columns={"id": "id_predio"}).to_crs(CRS_METROS),
                          exposicion[columnas].rename(columns={"id": "id_gem"}).to_crs(CRS_METROS),
                          how="left", max_distance=DIST_MAX_GEM_M, distance_col="distancia_m")
    j = pd.DataFrame(j[j.id_gem.notna()].drop(columns=["geometry", "index_right"]))
    j = j.sort_values(["id_predio", "ocupantes_noche", "id_gem"], ascending=[True, False, True],
                      na_position="last", kind="stable").reset_index(drop=True)
    j["n_candidatos"] = j.groupby("id_predio").id_gem.transform("size")
    j["n_predios_por_gem"] = j.groupby("id_gem").id_predio.transform("nunique")
    j["gem_reutilizado"] = j.n_predios_por_gem.gt(1)
    j["seleccionado"] = ~j.id_predio.duplicated()
    j["metodo"] = "cercania_contorno_15m_empates_suma_atributos_max_ocupantes_id"
    return j


def enriquecer_gem_plata(predios, exposicion):
    out = predios.copy()
    cruces = candidatos_gem(out, exposicion)
    elegido = cruces[cruces.seleccionado].set_index("id_predio")
    ids = out.id
    ex = exposicion.set_index("id")
    out["id_gem_seleccionado"] = ids.map(elegido.id_gem)
    out["dist_gem_m"] = ids.map(elegido.distancia_m)
    out["n_registros_gem"] = ids.map(elegido.n_candidatos).fillna(0).astype(int)
    out["gem_ambiguo"] = out.n_registros_gem.gt(1)
    out["gem_reutilizado"] = ids.map(cruces.groupby("id_predio").gem_reutilizado.any()).fillna(False).astype(bool)
    out["gem_metodo"] = "cercania_sin_llave_catastral"
    for col in ("periodo_construccion", "estrato", "uso", "pisos_categoria", "pisos_min", "pisos_max",
                "pisos_gem_estimados", "p_ductilidad_baja", "p_mamposteria_no_reforzada"):
        out[col] = out.id_gem_seleccionado.map(ex[col])
    for col in ("ocupantes_noche", "valor_reemplazo_usd"):
        out[col] = ids.map(cruces.groupby("id_predio")[col].sum(min_count=1))
    desconocidos = out.estado_predial.eq("pisos_desconocidos")
    usar_gem = desconocidos & out.pisos_gem_estimados.notna()
    # La mediana se calcula solo sobre pisos observados positivos, sin lotes ni estimaciones GEM.
    por_comuna = out.groupby("comuna").pisos_observados.transform("median")
    mediana = por_comuna.fillna(out.pisos_observados.median())
    out["pisos_estimados"] = out.pisos_gem_estimados.where(usar_gem, mediana).where(desconocidos)
    out["pisos"] = out.pisos_observados.fillna(out.pisos_estimados)
    out["pisos_imputado"] = desconocidos & out.pisos_estimados.notna()
    out["pisos_fuente"] = np.select([out.sin_construccion_registrada, out.pisos_observados.notna(), usar_gem,
                                    desconocidos & por_comuna.notna(), out.pisos_estimados.notna()],
                                    ["sin_construccion_registrada", "oficial", "gem_estimado", "mediana_comuna", "mediana_muestra"],
                                    "desconocido")
    return out, cruces


def suelo_plata(predios, grilla, amplificacion):
    out = predios.copy()
    j = vecino_plata(out, grilla, limitar_cobertura=True)
    out["dist_microzona_m"] = j.distancia_m
    out["dentro_cobertura_microzona"] = j.dentro_cobertura
    out["id_sitio_microzona"] = j.id_objetivo
    out["n_vecinos_microzona"] = j.n_coincidencias
    out["microzona"] = j.id_objetivo.map(grilla.set_index("id").ampcode)
    out["periodo_s"] = np.nan
    conocidos = out.pisos.notna() & ~out.sin_construccion_registrada
    t = out.loc[conocidos, "pisos"].to_numpy()[:, None] / 10
    out.loc[conocidos, "periodo_s"] = PERIODOS_AF[np.abs(t - PERIODOS_AF).argmin(axis=1)]
    fila = amplificacion[(amplificacion.imt == "SA") & np.isclose(amplificacion.nivel_roca_g, NIVEL_AF)]
    af = fila.set_index(["ampcode", "periodo_s"])
    claves = pd.MultiIndex.from_arrays([out.microzona, out.periodo_s], names=["ampcode", "periodo_s"])
    for destino, origen in (("amplif_suelo", "factor"), ("amplif_sigma", "sigma")):
        out[destino] = af[origen].reindex(claves).to_numpy()
    out["nivel_roca_referencia_g"] = NIVEL_AF
    out["vs30_referencia_m_s"] = 800.
    out["amplificacion_metodo"] = "escenario_referencia_separado_de_shakemap"
    return out


def eventos_plata(catalogos):
    partes = []
    for nombre, raw in catalogos.items():
        g = geometria_plata(raw)
        p = gpd.GeoDataFrame(index=g.index, geometry=g.geometry, crs=g.crs)
        p["id"] = columna_plata(g, "id")
        for origen, destino in (("mag", "magnitud"), ("mmi", "mmi_evento")):
            p[destino] = pd.to_numeric(columna_plata(g, origen), errors="coerce")
        for origen, destino in (("time", "fecha_utc"), ("updated", "actualizado_utc")):
            p[destino] = pd.to_datetime(pd.to_numeric(g[origen], errors="coerce"), unit="ms", utc=True)
        p["magnitud_tipo"] = columna_plata(g, "magType")
        p["lugar"] = columna_plata(g, "place")
        p["profundidad_km"] = p.geometry.map(lambda geo: geo.z if geo.has_z else np.nan)
        p["fuente"] = nombre
        exigir_identidad(p, ["id"], nombre)
        partes.append(p)
    todos = gpd.GeoDataFrame(pd.concat(partes, ignore_index=True), crs=CRS_GEO)
    origen = pd.DataFrame(todos[["id", "fuente", "actualizado_utc"]]).rename(columns={"id": "id_evento"})
    out = todos.sort_values(["id", "actualizado_utc", "fuente"], ascending=[True, False, True],
                            na_position="last", kind="stable").drop_duplicates("id").reset_index(drop=True)
    out["n_catalogos"] = out.id.map(origen.groupby("id_evento").size())
    out["es_evento_principal"] = out.id.eq("us6000tjl2")
    principal = out.loc[out.es_evento_principal, "fecha_utc"]
    out["es_posterior_principal"] = out.fecha_utc.gt(principal.iloc[0]) if len(principal) else False
    out["asociacion_replica"] = "no_evaluada"
    return out, origen


def observaciones_plata(raw):
    g = geometria_plata(raw)
    out = gpd.GeoDataFrame(index=g.index, geometry=g.geometry, crs=g.crs)
    for origen, destino in (("code", "codigo"), ("network", "red"), ("source", "fuente_original"),
                            ("name", "nombre"), ("station_type", "tipo_original")):
        out[destino] = columna_plata(g, origen)
    out["id"] = out.red.fillna("sin_red") + ":" + out.codigo
    out["tipo_observacion"] = out.tipo_original.map({"seismic": "instrumental", "macroseismic": "macrosismica"}).fillna("sin_clasificar")
    for origen, destino in (("pga", "pga_original"), ("pgv", "pgv_original"), ("intensity", "intensidad_mmi")):
        out[destino] = pd.to_numeric(columna_plata(g, origen), errors="coerce")
    out["unidad_pga"] = "%g_segun_producto_stationlist"
    out["unidad_pgv"] = "cm/s_segun_producto_stationlist"
    out["es_insumo_shakemap"] = True
    out["evento_id"] = "us6000tjl2"
    out["fuente"] = "usgs_estaciones_cali"
    return out


def huellas_plata(raw, fuentes):
    filas = []
    for nombre, df in {"predios": raw, **fuentes}.items():
        d = para_spark(df) if isinstance(df, gpd.GeoDataFrame) else df.copy()
        # Huella del contenido bronze leído, incluidos los nulos; distinta de un hash del archivo físico.
        serializado = d.to_json(orient="split", index=False, date_format="iso", double_precision=15)
        filas.append({"fuente": nombre, "filas_bronce": len(df),
                      "sha256_contenido_bronce": hashlib.sha256(serializado.encode()).hexdigest(),
                      "archivo": "Datosprediales.json" if nombre == "predios" else ARCHIVOS_PLATA[nombre],
                      "corte_fuente": None, "corte_estado": "no_conservado_en_extracto",
                      "procesado_utc": datetime.now(timezone.utc).isoformat()})
    out = pd.DataFrame(filas)
    out["corte_fuente"] = pd.to_datetime(out.corte_fuente, utc=True)
    out["procesado_utc"] = pd.to_datetime(out.procesado_utc, utc=True)
    return out


def construir_plata(raw, fuentes):
    """Produce tablas tipadas y relaciones. Valida antes de permitir escritura local/Delta."""
    faltan = set(ARCHIVOS_PLATA) - set(fuentes)
    if faltan:
        raise ValueError(f"Fuentes bronze ausentes: {sorted(faltan)}")
    p, reporte = limpiar_predios_plata(raw)
    territorios = territorios_plata(fuentes)
    servicios = servicios_plata(fuentes)
    vias = vias_plata(fuentes["osm_vias_principales"])
    ex = exposicion_plata(fuentes["gem_exposicion"])
    grilla = puntos_plata(fuentes["gem_microzonas_grilla"], "gem_microzonas_grilla",
                          {"ampcode": "ampcode", "vs30": "vs30_modelo_m_s", "vs30measured": "vs30measured_original"}, {"vs30"})
    af = amplificacion_plata(fuentes["gem_amplificacion_suelo"])
    sitio = puntos_plata(fuentes["gem_sitio_licuacion_ladera"], "gem_sitio_licuacion_ladera",
                         {"unit": "unidad_geologica", "liq_susc_cat": "licuacion_cat", "gwd": "profundidad_agua_original",
                          "pendiente_grados": "pendiente_original"}, {"gwd", "pendiente_grados"})
    sitio["unidad_pendiente"] = "etiquetada_grados_por_extractor_pendiente_confirmar_origen"
    sm = puntos_plata(fuentes["usgs_shakemap_cali"], "usgs_shakemap_cali",
                      {c: c for c in ("mmi", "pga", "pgv", "psa03", "psa06", "psa10", "psa30", "svel")},
                      {"mmi", "pga", "pgv", "psa03", "psa06", "psa10", "psa30", "svel"})
    sm = sm.rename(columns={"pga": "pga_pct_g", "pgv": "pgv_cm_s", **{f"psa{n}": f"psa{n}_pct_g" for n in ("03", "06", "10", "30")}})
    sm["pga_g"] = sm.pga_pct_g / 100
    sm["psa10_g"] = sm.psa10_pct_g / 100
    sm["evento_id"] = "us6000tjl2"
    sm["version_producto"] = "v11_segun_registro_descarga"
    eventos, origen = eventos_plata({k: fuentes[k] for k in ("usgs_sismos_2026_08", "usgs_replicas")})
    observaciones = observaciones_plata(fuentes["usgs_estaciones_cali"])
    # Las tablas de referencia deben tener llaves válidas antes de usarlas en map/join.
    for nombre, df in {"territorios": territorios, "servicios": servicios, "vias": vias,
                       "exposicion_gem": ex, "sitio_grilla": grilla, "sitio": sitio, "shakemap": sm}.items():
        exigir_identidad(df, ["id"], nombre)
    exigir_identidad(af, ["ampcode", "nivel_roca_g", "imt", "periodo_s"], "amplificacion")
    relaciones = []
    for tipo, campo in (("comunas", "comuna"), ("barrios", "barrio")):
        z = territorios[territorios.tipo.eq(tipo)]
        j, r = cruzar_territorio(p, z)
        r["tipo"] = tipo
        relaciones.append(r)
        p[f"n_coincidencias_{campo}"] = j.n_coincidencias
        p[f"id_{campo}_osm"] = j.id_territorio
        if tipo == "comunas":
            codigo = pd.to_numeric(j.id_territorio.map(z.set_index("id").codigo), errors="coerce").astype("Int64")
            p["comuna_osm"] = codigo
            p["comuna_discrepante"] = (p.comuna.notna() & codigo.notna() & p.comuna.ne(codigo)).fillna(False)
            p["comuna_completada_osm"] = p.comuna.isna() & codigo.notna()
            p["comuna"] = p.comuna.fillna(codigo)
        else:
            p["barrio"] = j.id_territorio.map(z.set_index("id").nombre)
    p, gem = enriquecer_gem_plata(p, ex)
    p = suelo_plata(p, grilla, af)
    for nombre, objetivos in {
        "salud": servicios[servicios.fuente.eq("osm_salud")],
        "salud_urgencias": servicios[servicios.fuente.eq("osm_salud") & servicios.urgencias.eq("si")],
        "bomberos": servicios[servicios.tipo.eq("fire_station")], "via_principal": vias,
    }.items():
        j = vecino_plata(p, objetivos)
        p[f"dist_{nombre}_m"] = j.distancia_m
        p[f"id_{nombre}_cercano"] = j.id_objetivo
        p[f"n_vecinos_{nombre}"] = j.n_coincidencias
    p["metodo_distancia_servicios"] = "euclidiana_contorno_a_geometria_epsg9377"
    # Conservar el nombre consumido por gold, contando registros no marcados como lote; no es población.
    p = contar_en_radio(p, p[~p.sin_construccion_registrada], 100, "edif")
    p["puede_bloquear_via"] = (p.alta_escombros & p.dist_via_principal_m.le(p.pisos * METROS_POR_PISO)).astype("boolean")
    p.loc[p.pisos.isna() | p.dist_via_principal_m.isna(), "puede_bloquear_via"] = pd.NA
    for nombre, capa, cols in (("sitio", sitio, ["licuacion_cat", "pendiente_original"]),
                                ("shakemap", sm, ["mmi", "pga_g", "psa10_g"])):
        j = vecino_plata(p, capa, limitar_cobertura=True)
        p[f"dist_{nombre}_m"] = j.distancia_m
        p[f"id_{nombre}"] = j.id_objetivo
        p[f"n_vecinos_{nombre}"] = j.n_coincidencias
        p[f"dentro_cobertura_{nombre}"] = j.dentro_cobertura
        for col in cols:
            p[col] = j.id_objetivo.map(capa.set_index("id")[col])
    p["licuacion"] = p.licuacion_cat.map(SUSC_LICUACION)
    # Alias de compatibilidad: su unidad sigue pendiente, explícita en sitio y documentación.
    p["pendiente_grados"] = p.pendiente_original
    p["evento_shakemap_id"] = "us6000tjl2"
    p["fuente_principal"] = "predios"
    tablas = {"predios": p, "territorios": territorios, "servicios": servicios, "vias": vias,
              "sitio_grilla": grilla, "amplificacion": af, "exposicion_gem": ex,
              "sitio_licuacion_ladera": sitio, "shakemap": sm, "observaciones": observaciones,
              "eventos": eventos, "eventos_origen": origen, "cruces_gem": gem,
              "cruces_territoriales": pd.concat(relaciones, ignore_index=True), "fuentes": huellas_plata(raw, fuentes)}
    tablas["calidad"] = validar_plata(tablas, len(raw))
    reporte.update({"filas_silver": len(p), "pisos_nulos_a_imputar": int(p.pisos_imputado.sum()),
                    "comuna_completada_con_osm": int(p.comuna_completada_osm.sum()),
                    "predios_gem_ambiguo": int(p.gem_ambiguo.sum()), "predios_gem_reutilizado": int(p.gem_reutilizado.sum()),
                    "predios_sin_gem": int(p.n_registros_gem.eq(0).sum()),
                    "lotes_con_senal_danio": int(p.discrepancia_lote_satelite.sum()),
                    "eventos_unicos": len(eventos), "observaciones_instrumentales": int(observaciones.tipo_observacion.eq("instrumental").sum()),
                    "tablas": {k: len(v) for k, v in tablas.items()}})
    return tablas, reporte


def validar_plata(tablas, filas_bronce):
    controles = []

    def control(nombre, ok, detalle):
        controles.append({"control": nombre, "cumple": bool(ok), "detalle": str(detalle)})

    claves = {k: ["id"] for k in ("predios", "territorios", "servicios", "vias", "sitio_grilla", "exposicion_gem",
                                   "sitio_licuacion_ladera", "shakemap", "observaciones", "eventos")}
    claves.update({"amplificacion": ["ampcode", "nivel_roca_g", "imt", "periodo_s"],
                   "cruces_gem": ["id_predio", "id_gem"], "cruces_territoriales": ["id_predio", "id_territorio"],
                   "eventos_origen": ["id_evento", "fuente"], "fuentes": ["fuente"]})
    for nombre, campos in claves.items():
        d = tablas[nombre]
        control(f"{nombre}_llave", not d[campos].isna().any().any() and not d.duplicated(campos).any(), campos)
        control(f"{nombre}_columnas", all(re.fullmatch(r"[a-z][a-z0-9_]*", c) for c in d.columns), "snake_case")
        if isinstance(d, gpd.GeoDataFrame):
            control(f"{nombre}_geometria", d.geometry.notna().all() and not d.is_empty.any() and d.is_valid.all(), "no vacías y válidas")
    p = tablas["predios"]
    lotes = p.sin_construccion_registrada
    control("cardinalidad_predios", len(p) == filas_bronce, f"bronze={filas_bronce}, silver={len(p)}")
    control("lotes_sin_pisos_ni_periodo", p.loc[lotes, ["pisos", "pisos_estimados", "periodo_s"]].isna().all().all()
            and not p.loc[lotes, "pisos_imputado"].any(), int(lotes.sum()))
    control("pisos_observados_no_imputados", p.loc[p.pisos_imputado, "pisos_observados"].isna().all(), "estimados separados")
    control("pga_conversion", np.allclose(tablas["shakemap"].pga_g * 100, tablas["shakemap"].pga_pct_g, equal_nan=True), "%g / 100 = g")
    control("urgencias_dominio", tablas["servicios"].urgencias.isin(["si", "no", "sin_dato"]).all(), "tres estados")
    control("licuacion_dominio", tablas["sitio_licuacion_ladera"].licuacion_cat.isin(SUSC_LICUACION).all(), "vh/h/m/l/vl/n")
    for columna in [c for c in p if c.startswith("dist_") and c.endswith("_m")]:
        control(f"{columna}_no_negativa", p[columna].dropna().ge(0).all(), "metros EPSG:9377")
    for columna in ("p_ductilidad_baja", "p_mamposteria_no_reforzada"):
        control(f"{columna}_rango", tablas["exposicion_gem"][columna].dropna().between(0, 1).all(), "probabilidad de tipología")
    control("amplificacion_llaves_conocidas", set(tablas["sitio_grilla"].ampcode.dropna()) <= set(tablas["amplificacion"].ampcode), "códigos sin fallback a 1")
    control("cruces_gem_referencias", set(tablas["cruces_gem"].id_predio) <= set(p.id)
            and set(tablas["cruces_gem"].id_gem) <= set(tablas["exposicion_gem"].id), "integridad referencial")
    control("cruces_territoriales_referencias", set(tablas["cruces_territoriales"].id_predio) <= set(p.id)
            and set(tablas["cruces_territoriales"].id_territorio) <= set(tablas["territorios"].id), "integridad referencial")
    control("eventos_origen_referencias", set(tablas["eventos_origen"].id_evento) == set(tablas["eventos"].id), "catálogos conservados")
    control("gem_seleccion_unica", tablas["cruces_gem"].groupby("id_predio").seleccionado.sum().eq(1).all(), "uno por predio con candidato")
    for nombre in ("sitio_grilla", "exposicion_gem", "sitio_licuacion_ladera", "shakemap"):
        d = tablas[nombre]
        control(f"{nombre}_coordenadas", d.lon.between(-180, 180).all() and d.lat.between(-90, 90).all(), "WGS84")
    out = pd.DataFrame(controles)
    fallos = out[~out.cumple]
    if len(fallos):
        raise ValueError("Plata no publicable: " + ", ".join(fallos.control))
    return out


def escribir_plata_local(tablas, reporte, carpeta):
    """Solo llamar con carpeta privada. Revalida antes de sobrescribir salidas."""
    validar_plata(tablas, reporte["filas_bronze"])
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    for nombre, df in tablas.items():
        # Conservar dtypes nullable en Parquet: convertirlos a object perdería el tipo en columnas 100% nulas.
        d = (pd.DataFrame(df.drop(columns="geometry")).assign(geom_wkt=df.geometry.to_wkt(rounding_precision=-1))
             if isinstance(df, gpd.GeoDataFrame) else df)
        try:
            d.to_parquet(carpeta / f"silver_{EQUIPO}_{nombre}.parquet", index=False)
        except (ImportError, ValueError):
            # shortcut: sin motor Parquet usable (p. ej. DLL de pyarrow bloqueada por Windows) se guarda CSV y se pierden dtypes nullable; solo afecta la copia local
            d.to_csv(carpeta / f"silver_{EQUIPO}_{nombre}.csv", index=False)
    (carpeta / "reporte.json").write_text(json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8")


def guardar_plata_spark(spark, tablas):
    """Esquema explícito incluso para columnas/tablas completamente nulas/vacías."""
    from pyspark.sql.types import StructType, StructField, StringType, BooleanType, LongType, DoubleType, TimestampType

    validar_plata(tablas, int(tablas["fuentes"].set_index("fuente").loc["predios", "filas_bronce"]))
    for nombre, df in tablas.items():
        d = para_spark(df)
        tipos = []
        for c in d:
            s = df[c] if c in df else d[c]
            tipo = (BooleanType() if pd.api.types.is_bool_dtype(s.dtype) else
                    LongType() if pd.api.types.is_integer_dtype(s.dtype) else
                    DoubleType() if pd.api.types.is_numeric_dtype(s.dtype) else
                    TimestampType() if pd.api.types.is_datetime64_any_dtype(s.dtype) else StringType())
            tipos.append(StructField(c, tipo, True))
        esquema = StructType(tipos)
        filas = []
        for fila in d.itertuples(index=False, name=None):
            valores = []
            for v, campo in zip(fila, tipos):
                if pd.isna(v):
                    valores.append(None)
                elif isinstance(campo.dataType, TimestampType):
                    # Python/Spark puede interpretar datetimes naive en la zona local del driver.
                    instante = pd.Timestamp(v)
                    instante = instante.tz_convert("UTC") if instante.tzinfo else instante.tz_localize("UTC")
                    valores.append(instante.to_pydatetime())
                elif isinstance(campo.dataType, StringType):
                    valores.append(str(v))
                elif isinstance(campo.dataType, BooleanType):
                    valores.append(bool(v))
                elif isinstance(campo.dataType, LongType):
                    valores.append(int(v))
                else:
                    valores.append(float(v))
            filas.append(tuple(valores))
        destino = tabla("silver", nombre)
        spark.createDataFrame(filas, esquema).write.mode("overwrite").option("overwriteSchema", True).saveAsTable(destino)
        print(f"{destino}: {len(d)} filas")
