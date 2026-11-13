# Databricks notebook source
"""Oro compartido: consumir plata, explicar prioridades y publicar indicadores auditables.

Cargar después de 00_utils_espacial, 00_pipeline y 00_silver. Sin descargas ni Spark
al transformar. Los ocupantes GEM son modelados; no representan personas afectadas.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

VERSION_ORO = "oro_v1"
TABLAS_PLATA_ORO = ("predios", "territorios", "servicios", "vias", "sitio_grilla", "amplificacion",
                    "exposicion_gem", "sitio_licuacion_ladera", "shakemap", "observaciones", "eventos",
                    "eventos_origen", "cruces_gem", "cruces_territoriales", "fuentes", "calidad")
GEO_PLATA_ORO = {"predios", "territorios", "servicios", "vias", "sitio_grilla", "exposicion_gem",
                 "sitio_licuacion_ladera", "shakemap", "observaciones", "eventos"}


TIPOS_COMUNAS_ORO = {'comuna': 'Int64', 'n_predios': 'int64', 'n_lotes': 'int64', 'n_con_pisos_observados': 'int64', 'n_pisos_desconocidos_originales': 'int64', 'n_sin_dato_satelital': 'int64', 'n_con_dato_satelital': 'int64', 'n_en_ranking': 'int64', 'n_alta_escombros': 'int64', 'n_con_senal_danio': 'int64', 'pct_alta_escombros': 'float64', 'pct_danio_entre_con_dato': 'float64', 'pct_sin_dato': 'float64', 'pisos_prom_observados': 'float64', 'indice_prom': 'float64', 'indice_p90': 'float64', 'n_prioridad_muy_alta': 'int64', 'n_prioridad_alta': 'int64', 'n_puede_bloquear_via': 'int64', 'n_bloqueo_desconocido': 'int64', 'dist_salud_prom_m': 'float64', 'amplif_suelo_prom': 'float64', 'mmi_prom': 'float64', 'n_gem_ambiguo': 'int64', 'n_gem_reutilizado': 'int64', 'ocupantes_asignados_gem': 'float64', 'ocupantes_asignados_gem_con_senal_danio': 'float64', 'pct_area_sin_dato': 'float64', 'n_salud': 'int64', 'n_bomberos': 'int64', 'ranking': 'Int64', 'n_edificios': 'int64', 'pisos_prom': 'float64', 'ocupantes_noche': 'float64', 'ocupantes_en_edif_con_danio': 'float64'}


def leer_plata_oro(carpeta):
    carpeta = Path(carpeta)
    tablas = {}
    for nombre in TABLAS_PLATA_ORO:
        ruta = carpeta / f"silver_{EQUIPO}_{nombre}.parquet"
        if not ruta.exists():
            raise FileNotFoundError(f"Se requiere plata Parquet tipada: {ruta}. Ejecutar correr_plata.py con pyarrow.")
        d = pd.read_parquet(ruta)
        tablas[nombre] = geometria_plata(d) if nombre in GEO_PLATA_ORO else d
    return tablas


def escenarios_oro():
    escenarios = {k: dict(v) for k, v in ESCENARIOS_SENSIBILIDAD.items() if k != "sin_fuentes_gem"}
    escenarios["sin_vulnerabilidad_ni_suelo"] = dict(ESCENARIOS_SENSIBILIDAD["sin_fuentes_gem"])
    escenarios["sin_fuentes_gem"] = {k: v for k, v in PESOS.items()
                                      if k not in ("c_vulnerabilidad", "c_suelo", "c_exposicion")}
    return escenarios


def predios_oro(plata):
    p = calcular_indice(plata.copy())
    componentes = list(PESOS)
    disponibles = p[componentes].notna()
    w = pd.Series(PESOS, dtype=float)
    denominador = disponibles.mul(w).sum(axis=1).replace(0, np.nan)
    p["n_componentes_disponibles"] = disponibles.sum(axis=1).astype("Int64")
    p["peso_base_disponible"] = denominador
    for c in componentes:
        p[f"peso_efectivo_{c}"] = disponibles[c].mul(w[c]).div(denominador)
        p[f"aporte_{c}"] = p[c].fillna(0).mul(p[f"peso_efectivo_{c}"])
    aportes = p[[f"aporte_{c}" for c in componentes]]
    etiquetas = {f"aporte_{c}": c.removeprefix("c_") for c in componentes}
    p["motivos_principales"] = aportes.apply(
        lambda s: ", ".join(etiquetas[k] for k in s.dropna().sort_values(ascending=False, kind="stable").head(3).index
                            if s[k] > 0), axis=1).astype("string")
    p["posicion"] = posiciones_oro(p, p.indice_riesgo)
    p["cola_trabajo"] = np.select(
        [p.sin_dato_satelital, p.sin_construccion_registrada],
        ["verificar_dato_satelital", "verificar_predio_sin_construccion"], "inspeccion_priorizada")
    p["interpretacion_indice"] = "priorizacion_relativa_no_probabilidad_de_colapso"
    p["ocupantes_asignados_gem"] = p.ocupantes_noche
    p["version_oro"] = VERSION_ORO
    return p


def posiciones_oro(p, puntaje):
    validos = p.en_ranking & puntaje.notna()
    orden = pd.DataFrame({"id": p.loc[validos, "id"].astype(str), "puntaje": puntaje[validos]})
    orden = orden.sort_values(["puntaje", "id"], ascending=[False, True], kind="stable")
    posiciones = pd.Series(range(1, len(orden) + 1), index=orden.index, dtype="Int64")
    return posiciones.reindex(p.index)


def sensibilidad_oro(p):
    filas, resumen = [], []
    base = p.posicion
    n_top = min(50, int(base.notna().sum()))
    top_base = set(p.loc[base.le(n_top).fillna(False), "id"])
    for nombre, pesos in escenarios_oro().items():
        puntaje = indice_riesgo(p, pesos)
        posicion = posiciones_oro(p, puntaje)
        mascara = p.en_ranking
        filas.append(pd.DataFrame({"id_predio": p.loc[mascara, "id"], "escenario": nombre,
                                   "indice": puntaje[mascara], "posicion": posicion[mascara],
                                   "cambio_posicion": (posicion - base)[mascara],
                                   "en_top": posicion[mascara].le(n_top).fillna(False)}))
        comparables = base.notna() & posicion.notna()
        correlacion = np.nan
        # La correlación de puntajes empatados usa rangos medios, no el desempate por ID.
        if comparables.sum() > 1:
            correlacion = p.loc[comparables, "indice_riesgo"].rank().corr(puntaje[comparables].rank())
        top = set(p.loc[posicion.le(n_top).fillna(False), "id"])
        resumen.append({"escenario": nombre, "n_comparables": int(comparables.sum()), "n_top": n_top,
                        "spearman_vs_base": correlacion,
                        "top50_coincide_%": 100 * len(top_base & top) / n_top if n_top else np.nan,
                        "n_top_coincide": len(top_base & top)})
    detalle = pd.concat(filas, ignore_index=True)
    # Nombre canónico snake_case; el alias anterior se crea solo para el CSV de compatibilidad.
    return detalle, pd.DataFrame(resumen).rename(columns={"top50_coincide_%": "pct_top_coincide"})


def afectaciones_oro(p):
    filas = []
    grupos = [("inventario", "todas", p)] + [("comuna", str(c) if pd.notna(c) else "sin_comuna", d)
                                                for c, d in p.groupby("comuna", dropna=False)]
    for ambito, zona, d in grupos:
        area_total = float(d.area_m2.sum())
        area_union = float(d.to_crs(CRS_METROS).geometry.union_all().area)
        for estado, s in d.groupby("estado", dropna=False):
            filas.append({"ambito": ambito, "zona": zona, "estado": str(estado) if pd.notna(estado) else "sin_categoria",
                          "n_predios": len(s), "n_lotes": int(s.sin_construccion_registrada.sum()),
                          "denominador_predios": len(d), "pct_predios": 100 * len(s) / len(d),
                          "area_contornos_sumada_m2": float(s.area_m2.sum()),
                          "denominador_area_sumada_m2": area_total,
                          "pct_area_sumada": 100 * float(s.area_m2.sum()) / area_total if area_total else np.nan,
                          "area_union_categoria_m2": float(s.to_crs(CRS_METROS).geometry.union_all().area),
                          "area_union_inventario_m2": area_union})
    return pd.DataFrame(filas)


def servicios_oro(p, servicios, territorios):
    s = servicios.copy()
    zonas = territorios[territorios.tipo.eq("comunas")]
    j, _ = cruzar_territorio(s, zonas)
    s["comuna"] = pd.to_numeric(j.id_territorio.map(zonas.set_index("id").codigo), errors="coerce").astype("Int64")
    s["n_coincidencias_comuna"] = j.n_coincidencias
    s["n_predios_mas_cercanos"] = 0
    s["n_predios_con_senal_danio_mas_cercanos"] = 0
    for fuente, col in (("osm_salud", "id_salud_cercano"), ("bomberos", "id_bomberos_cercano")):
        mascara = s.fuente.eq(fuente) if fuente == "osm_salud" else s.tipo.eq("fire_station")
        if col not in p:
            continue
        s.loc[mascara, "n_predios_mas_cercanos"] = s.loc[mascara, "id"].map(p.groupby(col).size()).fillna(0).astype(int)
        afectados = p[~p.sin_construccion_registrada & ~p.sin_dato_satelital & p.sev_estado.ge(.7)]
        s.loc[mascara, "n_predios_con_senal_danio_mas_cercanos"] = s.loc[mascara, "id"].map(afectados.groupby(col).size()).fillna(0).astype(int)
    s["interpretacion"] = "asignacion_por_proximidad_no_demanda_ni_capacidad_operativa"
    return s


def comunas_oro(p, territorios, servicios):
    filas = []
    zonas = territorios[territorios.tipo.eq("comunas")].copy()
    zonas["comuna"] = pd.to_numeric(zonas.codigo, errors="coerce").astype("Int64")
    for comuna, d in p.groupby("comuna"):
        sat = ~d.sin_dato_satelital
        edificios = ~d.sin_construccion_registrada
        ranking = d.en_ranking
        danio = sat & d.sev_estado.ge(.7)
        fila = {"comuna": comuna, "n_predios": len(d), "n_lotes": int((~edificios).sum()),
                "n_con_pisos_observados": int(d.pisos_observados.notna().sum()),
                "n_pisos_desconocidos_originales": int(d.estado_predial.eq("pisos_desconocidos").sum()),
                "n_sin_dato_satelital": int((~sat).sum()), "n_con_dato_satelital": int(sat.sum()),
                "n_en_ranking": int(ranking.sum()), "n_alta_escombros": int(d.alta_escombros.sum()),
                "n_con_senal_danio": int(danio.sum()),
                "pct_alta_escombros": 100 * d.alta_escombros.sum() / len(d),
                "pct_danio_entre_con_dato": 100 * danio.sum() / sat.sum() if sat.any() else np.nan,
                "pct_sin_dato": 100 * (~sat).sum() / len(d),
                "pisos_prom_observados": d.pisos_observados.mean(),
                "indice_prom": d.loc[ranking, "indice_riesgo"].mean(),
                "indice_p90": d.loc[ranking, "indice_riesgo"].quantile(.9),
                "n_prioridad_muy_alta": int(d.prioridad.eq("Muy alta").sum()),
                "n_prioridad_alta": int(d.prioridad.eq("Alta").sum()),
                "n_puede_bloquear_via": int(d.puede_bloquear_via.fillna(False).sum()),
                "n_bloqueo_desconocido": int(d.puede_bloquear_via.isna().sum()),
                "dist_salud_prom_m": d.dist_salud_m.mean(),
                "amplif_suelo_prom": d.amplif_suelo.mean(), "mmi_prom": d.mmi.mean(),
                "n_gem_ambiguo": int(d.gem_ambiguo.sum()), "n_gem_reutilizado": int(d.gem_reutilizado.sum()),
                "ocupantes_asignados_gem": d.ocupantes_noche.sum(min_count=1),
                "ocupantes_asignados_gem_con_senal_danio": d.loc[danio & edificios, "ocupantes_noche"].sum(min_count=1),
                "pct_area_sin_dato": 100 * d.loc[~sat, "area_m2"].sum() / d.area_m2.sum() if d.area_m2.sum() else np.nan}
        for campo, mascara in (("n_salud", servicios.fuente.eq("osm_salud")),
                                ("n_bomberos", servicios.tipo.eq("fire_station"))):
            fila[campo] = int((mascara & servicios.comuna.eq(comuna)).sum())
        filas.append(fila)
    if not filas:
        vacio = pd.DataFrame({c: pd.Series(dtype=t) for c, t in TIPOS_COMUNAS_ORO.items()})
        return gpd.GeoDataFrame(vacio, geometry=gpd.GeoSeries([], crs=CRS_GEO), crs=CRS_GEO)
    agg = pd.DataFrame(filas)
    agg["ranking"] = agg.indice_p90.rank(ascending=False, method="min").astype("Int64")
    # Alias conservados para lectores del mapa/CSV; su semántica se documenta.
    agg["n_edificios"] = agg.n_predios
    agg["pisos_prom"] = agg.pisos_prom_observados
    agg["ocupantes_noche"] = agg.ocupantes_asignados_gem
    agg["ocupantes_en_edif_con_danio"] = agg.ocupantes_asignados_gem_con_senal_danio
    return zonas[["comuna", "geometry"]].merge(agg, on="comuna", how="inner").sort_values(["ranking", "comuna"], na_position="last")


def exposicion_oro(p, cruces, ex, territorios):
    rel = cruces.merge(p[["id", "sin_construccion_registrada", "sin_dato_satelital", "sev_estado"]],
                       left_on="id_predio", right_on="id", validate="many_to_one")
    rel["con_senal_danio"] = ~rel.sin_dato_satelital & ~rel.sin_construccion_registrada & rel.sev_estado.ge(.7)
    conteos = rel.groupby("id_gem").agg(n_predios_vinculados=("id_predio", "nunique"),
                                        n_vinculos_con_senal_danio=("con_senal_danio", "sum"))
    out = ex[ex.id.isin(conteos.index)].copy()
    out = out.merge(conteos, left_on="id", right_index=True, validate="one_to_one")
    zonas = territorios[territorios.tipo.eq("comunas")]
    j, _ = cruzar_territorio(out, zonas)
    out["comuna_gem"] = pd.to_numeric(j.id_territorio.map(zonas.set_index("id").codigo), errors="coerce").astype("Int64")
    out["n_coincidencias_comuna"] = j.n_coincidencias
    out["interpretacion"] = "registro_gem_contado_una_vez_no_personas_afectadas_ni_identidad_predial"
    return out


def factores_oro(p):
    filas, grupos = [], []
    d = p[p.en_ranking].copy()
    d["danio"] = d.sev_estado.ge(.7)
    for campo in ("periodo_construccion", "estrato", "uso", "microzona", "licuacion_cat", "comuna"):
        validos = d[campo].notna()
        ct = pd.crosstab(d.loc[validos, campo], d.loc[validos, "danio"]).reindex(columns=[False, True], fill_value=0)
        n = int(ct.to_numpy().sum())
        pv = efecto = esperada_min = np.nan
        estado = "sin_variacion_o_sin_datos"
        if ct.shape[0] > 1 and ct.sum(axis=0).gt(0).all():
            estadistico, pv, _, esperadas = chi2_contingency(ct, correction=False)
            esperada_min = float(esperadas.min())
            efecto = float(np.sqrt(estadistico / n / min(ct.shape[0] - 1, 1)))
            estado = "evaluada" if (esperadas >= 5).all() else "exploratoria_frecuencias_bajas"
        filas.append({"factor": campo, "n_elegibles": len(d), "n_validos": n,
                      "n_faltantes": int((~validos).sum()), "n_categorias": len(ct),
                      "p_valor_chi2": pv, "v_cramer": efecto, "frecuencia_esperada_min": esperada_min,
                      "estado_prueba": estado})
        for categoria, fila in ct.iterrows():
            total = int(fila.sum())
            grupos.append({"factor": campo, "categoria": str(categoria), "n_validos": total,
                           "n_con_senal_danio": int(fila[True]),
                           "pct_con_senal_danio": 100 * fila[True] / total if total else np.nan})
    out = pd.DataFrame(filas)
    evaluables = out.estado_prueba.eq("evaluada") & out.p_valor_chi2.notna()
    # Holm para las pruebas con aproximación admisible; no inventar conclusiones en tablas escasas.
    ids = out.loc[evaluables].sort_values("p_valor_chi2").index
    ajuste = np.maximum.accumulate(out.loc[ids, "p_valor_chi2"].to_numpy() * np.arange(len(ids), 0, -1))
    out["p_ajustado_holm"] = np.nan
    out.loc[ids, "p_ajustado_holm"] = np.minimum(1., ajuste)
    out["interpretacion"] = "exploratoria_no_causal_independencia_espacial_no_acreditada"
    return out, pd.DataFrame(grupos, columns=["factor", "categoria", "n_validos", "n_con_senal_danio", "pct_con_senal_danio"])


def verificaciones_oro(p):
    banderas = pd.DataFrame({"sin_construccion_registrada": p.sin_construccion_registrada,
                            "sin_dato_satelital": p.sin_dato_satelital,
                            "discrepancia_lote_satelite": p.discrepancia_lote_satelite,
                            "pisos_desconocidos_originales": p.estado_predial.eq("pisos_desconocidos"),
                            "gem_ambiguo": p.gem_ambiguo, "gem_reutilizado": p.gem_reutilizado,
                            "comuna_sin_asignar": p.comuna.isna(),
                            "contorno_estado_contradictorio": p.contorno_estado_contradictorio})
    motivos = banderas.apply(lambda s: ", ".join(s.index[s.fillna(False)]), axis=1)
    out = p.loc[motivos.ne(""), ["id", "comuna", "cola_trabajo", "prioridad", "posicion"]].copy()
    out["motivos_verificacion"] = motivos[motivos.ne("")]
    out["n_motivos"] = banderas.loc[out.index].sum(axis=1).astype(int)
    return out.sort_values(["cola_trabajo", "posicion", "id"], na_position="last")


def parametros_oro():
    filas = [{"parametro": f"peso_{escenario}_{c}", "valor": str(v)}
             for escenario, pesos in escenarios_oro().items() for c, v in pesos.items()]
    valores = {"version": VERSION_ORO, "normalizacion": "minmax_cuantiles_0.01_0.99_inventario_valido_por_componente",
               "unidad_indice": "prioridad_relativa_no_probabilidad", "top_sensibilidad": "min(50,n_elegibles)",
               "distancias": "euclidianas_epsg9377_no_tiempos", "unidad_pendiente_gem": "pendiente_confirmar_no_usada",
               "comparacion_ciudades": "pendiente_datasets_comparables", "denominador_danio": "con_dato_satelital"}
    filas += [{"parametro": k, "valor": v} for k, v in valores.items()]
    return pd.DataFrame(filas)


def construir_oro(plata):
    validar_plata(plata, len(plata["predios"]))
    if plata["predios"].empty:
        raise ValueError("Oro requiere inventario predial no vacío")
    p = predios_oro(plata["predios"])
    servicios = servicios_oro(p, plata["servicios"], plata["territorios"])
    detalle, resumen = sensibilidad_oro(p)
    factores, grupos = factores_oro(p)
    fuentes = plata["fuentes"].copy()
    mapa = {"predios": "predios", "osm_comunas": "territorios", "osm_barrios": "territorios",
            "osm_salud": "servicios", "osm_emergencia": "servicios", "osm_educacion": "servicios",
            "osm_puntos_encuentro": "servicios", "osm_vias_principales": "vias",
            "gem_microzonas_grilla": "sitio_grilla", "gem_amplificacion_suelo": "amplificacion",
            "gem_exposicion": "exposicion_gem", "gem_sitio_licuacion_ladera": "sitio_licuacion_ladera",
            "usgs_shakemap_cali": "shakemap", "usgs_estaciones_cali": "observaciones",
            "usgs_sismos_2026_08": "eventos", "usgs_replicas": "eventos"}
    fuentes["tabla_plata"] = fuentes.fuente.map(mapa).map(lambda n: tabla("silver", n))
    fuentes["version_oro"] = VERSION_ORO
    tablas = {"predios": p, "comunas": comunas_oro(p, plata["territorios"], servicios),
              "afectaciones": afectaciones_oro(p), "servicios": servicios,
              "exposicion_gem": exposicion_oro(p, plata["cruces_gem"], plata["exposicion_gem"], plata["territorios"]),
              "sensibilidad": detalle, "resumen_sensibilidad": resumen, "factores": factores,
              "grupos_factores": grupos, "verificaciones": verificaciones_oro(p),
              "fuentes": fuentes, "parametros": parametros_oro()}
    tablas["calidad"] = validar_oro(tablas, plata)
    reporte = {"version": VERSION_ORO, "procesado_utc": datetime.now(timezone.utc).isoformat(),
               "n_predios": len(p), "n_en_ranking": int(p.en_ranking.sum()),
               "n_lotes": int(p.sin_construccion_registrada.sum()),
               "prioridades": {str(k): int(v) for k, v in p.prioridad.value_counts().items()},
               "tablas": {k: len(v) for k, v in tablas.items()},
               "publicado_databricks": False}
    return tablas, reporte


def validar_oro(tablas, plata):
    filas = []
    def control(nombre, cumple, detalle):
        filas.append({"control": nombre, "cumple": bool(cumple), "detalle": str(detalle)})
    p, original = tablas["predios"], plata["predios"]
    claves = {"predios": ["id"], "comunas": ["comuna"], "afectaciones": ["ambito", "zona", "estado"],
              "servicios": ["id"], "exposicion_gem": ["id"], "sensibilidad": ["id_predio", "escenario"],
              "resumen_sensibilidad": ["escenario"], "factores": ["factor"], "grupos_factores": ["factor", "categoria"],
              "verificaciones": ["id"], "fuentes": ["fuente"], "parametros": ["parametro"]}
    for nombre, campos in claves.items():
        d = tablas[nombre]
        control(f"{nombre}_llave", not d[campos].isna().any().any() and not d.duplicated(campos).any(), campos)
        control(f"{nombre}_columnas", all(re.fullmatch(r"[a-z][a-z0-9_]*", c) for c in d.columns), "snake_case")
    control("predios_conservados", len(p) == len(original) and set(p.id) == set(original.id), "sin pérdidas ni multiplicación")
    control("elegibilidad", p.en_ranking.eq(~p.sin_dato_satelital & ~p.sin_construccion_registrada).all(), "lotes y sin dato fuera")
    control("indice_rango", p.indice_riesgo.dropna().between(0, 1).all() and p.loc[p.en_ranking, "indice_riesgo"].notna().all(), "0..1")
    control("posiciones", p.loc[~p.en_ranking, "posicion"].isna().all() and
            sorted(p.posicion.dropna()) == list(range(1, int(p.en_ranking.sum()) + 1)), "orden total solo elegibles")
    suma = p[[f"aporte_{c}" for c in PESOS]].sum(axis=1, min_count=1)
    control("aportes_reconstruyen_indice", np.allclose(suma, p.indice_riesgo.astype(float), atol=.000051, equal_nan=True), "antes del redondeo a 4 decimales")
    control("lotes_sin_pisos", p.loc[p.sin_construccion_registrada, ["pisos", "pisos_estimados", "periodo_s"]].isna().all().all(), "sin imputación")
    control("afectaciones_total", tablas["afectaciones"].query("ambito == 'inventario'").n_predios.sum() == len(p), "denominador explícito")
    control("comunas_conservan_asignados", tablas["comunas"].n_predios.sum() == p.comuna.notna().sum(), "sin comuna se conserva en afectaciones")
    control("exposicion_ids_unicos", set(tablas["exposicion_gem"].id) == set(plata["cruces_gem"].id_gem), "un registro por candidato, sin población única")
    control("servicios_conservados", set(tablas["servicios"].id) == set(plata["servicios"].id), "sin capacidad inventada")
    control("sensibilidad_solo_elegibles", set(tablas["sensibilidad"].id_predio) == set(p.loc[p.en_ranking, "id"]), "no incluir lotes")
    control("pisos_observados_conservados", p.set_index("id").pisos_observados.equals(original.set_index("id").pisos_observados), "no sustituir por estimados")
    for comuna, d in p.groupby("comuna"):
        real = tablas["comunas"].set_index("comuna").loc[comuna, "indice_p90"]
        esperado = d.loc[d.en_ranking, "indice_riesgo"].quantile(.9)
        control(f"p90_comuna_{int(comuna)}", np.isclose(real, esperado, equal_nan=True), "solo elegibles")
    resultado = pd.DataFrame(filas)
    if not resultado.cumple.all():
        raise ValueError("Oro no publicable: " + ", ".join(resultado.loc[~resultado.cumple, "control"]))
    return resultado


def escribir_oro_local(tablas, reporte, carpeta, plata):
    validar_oro(tablas, plata)
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    for nombre, df in tablas.items():
        d = pd.DataFrame(df.drop(columns="geometry")).assign(geom_wkt=df.geometry.to_wkt(rounding_precision=-1)) if isinstance(df, gpd.GeoDataFrame) else df
        d.to_parquet(carpeta / f"gold_{EQUIPO}_{nombre}.parquet", index=False)
    (carpeta / "reporte.json").write_text(json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8")


def guardar_oro_spark(spark, tablas, plata):
    """Esquemas explícitos para nulos/vacíos. Validar todo antes de la primera escritura."""
    from pyspark.sql.types import StructType, StructField, StringType, BooleanType, LongType, DoubleType, TimestampType
    validar_oro(tablas, plata)
    for nombre, df in tablas.items():
        d = para_spark(df)
        campos = []
        for c in d:
            s = df[c] if c in df else d[c]
            tipo = (BooleanType() if pd.api.types.is_bool_dtype(s) else LongType() if pd.api.types.is_integer_dtype(s)
                    else DoubleType() if pd.api.types.is_numeric_dtype(s) else TimestampType() if pd.api.types.is_datetime64_any_dtype(s)
                    else StringType())
            campos.append(StructField(c, tipo, True))
        filas = []
        for fila in d.itertuples(index=False, name=None):
            valores = []
            for v, campo in zip(fila, campos):
                t = campo.dataType
                valores.append(None if pd.isna(v) else str(v) if isinstance(t, StringType) else
                               bool(v) if isinstance(t, BooleanType) else int(v) if isinstance(t, LongType) else
                               pd.Timestamp(v).to_pydatetime() if isinstance(t, TimestampType) else float(v))
            filas.append(tuple(valores))
        spark.createDataFrame(filas, StructType(campos)).write.mode("overwrite").option("overwriteSchema", True).saveAsTable(tabla("gold", nombre))
        print(f"{tabla('gold', nombre)}: {len(d)} filas")


# Comentarios de Unity Catalog: documentan el contrato en el Catalog y orientan a Genie.
COMENTARIOS_TABLAS_ORO = {
    "predios": "Una fila por predio del inventario satelital (5.146). Índice de riesgo ante réplicas 0..1, prioridad, posición y motivos. "
               "Priorización relativa: no certifica seguridad ni es probabilidad de colapso. Filtrar en_ranking para edificios priorizables.",
    "comunas": "Una fila por comuna. Ranking por indice_p90 (solo edificios en_ranking), volumen de inspección, cobertura satelital y ocupación GEM modelada.",
    "afectaciones": "Estado satelital por ámbito (inventario o comuna): conteos de predios y áreas con su denominador.",
    "servicios": "Servicios OSM (salud, bomberos, policía, educación, puntos de encuentro) y predios cuyo servicio más cercano es ese. No es demanda ni capacidad.",
    "exposicion_gem": "Una fila por registro GEM vinculado a algún predio. Sumar ocupantes_noche aquí evita contar dos veces un registro; sigue siendo ocupación modelada.",
    "sensibilidad": "Puntaje y posición de cada edificio en_ranking bajo cada escenario de pesos.",
    "resumen_sensibilidad": "Una fila por escenario: correlación de Spearman y coincidencia del top 50 frente al escenario base.",
    "factores": "Pruebas exploratorias chi-cuadrado de asociación con señal de daño, con V de Cramér y ajuste Holm. Un p alto no prueba ausencia de relación.",
    "grupos_factores": "Tasa de señal de daño por categoría de cada factor, con su denominador.",
    "verificaciones": "Predios con motivos para revisar datos o verificar en terreno (sin dato satelital, lotes con daño, cruces ambiguos).",
    "fuentes": "Manifiesto de fuentes heredado de plata, con huellas SHA-256 y tabla que materializa cada fuente.",
    "parametros": "Pesos por escenario, versión y parámetros de normalización del índice.",
    "calidad": "Controles de publicación de oro: todos deben cumplir antes de escribir.",
}

COMENTARIOS_COLUMNAS_ORO = {
    "predios": {
        "id": "Llave del predio (OBJECTID del archivo oficial)",
        "comuna": "Comuna del archivo oficial, completada con OSM solo si venía vacía",
        "estado": "Estado estructural satelital entregado por la organización",
        "sev_estado": "Severidad 0..1: escombros 1,0; techo desaparecido 0,7; sin cambio aparente 0,1; nulo sin dato",
        "alta_escombros": "Verdadero si el satélite marca alta probabilidad de escombros",
        "sin_dato_satelital": "Sin información satelital: no significa sano; va a verificación en terreno",
        "sin_construccion_registrada": "NPISOS=0: predio sin construcción registrada (lote); fuera del ranking",
        "en_ranking": "Edificio priorizable: con dato satelital y con construcción registrada",
        "indice_riesgo": "Índice de riesgo ante réplicas 0..1, suma ponderada de 7 componentes; relativo, no probabilidad de colapso",
        "prioridad": "Muy alta (top 5 %), Alta (siguiente 10 %), Media (25 %), Baja; sin dato y lotes con categoría propia",
        "posicion": "Puesto en el ranking de inspección (1 = primero); nulo fuera del ranking",
        "motivos_principales": "Los tres componentes que más aportan al índice de este predio",
        "cola_trabajo": "inspeccion_priorizada, verificar_dato_satelital o verificar_predio_sin_construccion",
        "pisos": "Pisos efectivos: observados o estimados; nulo en lotes",
        "pisos_observados": "Pisos oficiales válidos; nulo si no hay dato o es lote",
        "pisos_fuente": "Origen de los pisos: oficial, gem_estimado o sin_construccion_registrada",
        "periodo_construccion": "Época de construcción según GEM, cruzada por cercanía",
        "ocupantes_asignados_gem": "Ocupantes nocturnos GEM asignados por cercanía; un registro puede repetirse entre predios. No es población afectada",
        "dist_salud_m": "Distancia euclidiana en metros al centro de salud OSM más cercano; no es tiempo de viaje",
        "dist_salud_urgencias_m": "Distancia en metros al centro de salud OSM que declara urgencias",
        "puede_bloquear_via": "Daño visible y a menos de pisos x 3 m de una vía principal",
        "microzona": "Microzona sísmica INGEOMINAS-DAGMA 2005 (grilla GEM)",
        "amplif_suelo": "Factor de amplificación del suelo para el período propio del edificio",
        "mmi": "Intensidad Mercalli del ShakeMap USGS en el predio",
        "c_danio": "Componente de daño observado normalizado 0..1 (peso 25 %)",
        "c_vulnerabilidad": "Componente de vulnerabilidad de la tipología GEM 0..1 (peso 20 %)",
        "c_exposicion": "Componente de ocupación modelada 0..1 (peso 15 %)",
        "c_suelo": "Componente de suelo: amplificación y licuación 0..1 (peso 10 %)",
        "c_altura": "Componente de altura 0..1 (peso 10 %)",
        "c_acceso_salud": "Componente de lejanía a salud 0..1 (peso 10 %)",
        "c_bloqueo_via": "Componente de posible bloqueo de vía principal 0..1 (peso 10 %)",
    },
    "comunas": {
        "comuna": "Número de comuna de Cali",
        "ranking": "Puesto de la comuna por indice_p90 (1 = más urgente)",
        "indice_p90": "Percentil 90 del índice entre los edificios en_ranking de la comuna",
        "n_predios": "Predios del inventario en la comuna, incluidos lotes y sin dato",
        "n_en_ranking": "Edificios priorizables (con dato satelital y construcción registrada)",
        "n_prioridad_muy_alta": "Edificios con prioridad Muy alta",
        "n_prioridad_alta": "Edificios con prioridad Alta",
        "n_alta_escombros": "Predios con alta probabilidad de escombros",
        "n_con_senal_danio": "Predios con daño visible (severidad >= 0,7); puede incluir lotes",
        "pct_danio_entre_con_dato": "Porcentaje con daño visible sobre los predios con dato satelital",
        "pct_sin_dato": "Porcentaje de predios sin dato satelital sobre todo el inventario de la comuna",
        "ocupantes_asignados_gem_con_senal_danio": "Ocupación GEM modelada en edificios con daño, sumada por predio (puede repetir registros); no es población afectada",
        "n_salud": "Centros de salud OSM en la comuna",
    },
    "resumen_sensibilidad": {
        "escenario": "Juego de pesos comparado con el base",
        "spearman_vs_base": "Correlación de rangos con el índice base (1 = mismo orden)",
        "pct_top_coincide": "Porcentaje del top 50 base que sigue en el top 50 del escenario",
    },
    "factores": {
        "factor": "Variable probada contra la señal de daño",
        "p_valor_chi2": "p-valor chi-cuadrado sin ajustar; exploratorio",
        "p_ajustado_holm": "p-valor ajustado por Holm entre las pruebas admisibles; nulo si hay frecuencias bajas",
        "v_cramer": "Tamaño de efecto 0..1; menor a 0,1 es muy pequeño",
        "estado_prueba": "evaluada o exploratoria_frecuencias_bajas",
    },
    "exposicion_gem": {
        "ocupantes_noche": "Ocupantes nocturnos modelados por GEM (censo 2018) de este registro; contado una vez",
        "n_vinculos_con_senal_danio": "Predios con daño visible vinculados a este registro GEM; no prueba que sea el mismo edificio",
        "comuna_gem": "Comuna donde cae el punto GEM",
    },
    "verificaciones": {
        "motivos_verificacion": "Motivos coexistentes para revisar el predio",
        "cola_trabajo": "Cola a la que pertenece el predio",
    },
}


def comentar_oro_spark(spark):
    """Aplica comentarios de tabla y columna a las tablas oro ya publicadas."""
    def sql(texto):
        return texto.replace("'", "''")  # comilla simple escapada para el literal SQL
    for nombre, texto in COMENTARIOS_TABLAS_ORO.items():
        spark.sql(f"COMMENT ON TABLE {tabla('gold', nombre)} IS '{sql(texto + ' Contrato docs/ORO.md.')}'")
    for nombre, columnas in COMENTARIOS_COLUMNAS_ORO.items():
        for columna, texto in columnas.items():
            spark.sql(f"ALTER TABLE {tabla('gold', nombre)} ALTER COLUMN {columna} COMMENT '{sql(texto)}'")
    print(f"Comentarios: {len(COMENTARIOS_TABLAS_ORO)} tablas, {sum(map(len, COMENTARIOS_COLUMNAS_ORO.values()))} columnas")
