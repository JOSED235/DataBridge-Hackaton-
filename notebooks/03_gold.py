# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · Gold: índice de riesgo ante réplicas, ranking por comuna y exportación al mapa
# MAGIC
# MAGIC Índice = suma ponderada de 6 componentes normalizados a 0..1 (justificación en `docs/INDICE_RIESGO.md`):
# MAGIC daño observado 25 %, vulnerabilidad de la tipología 20 %, ocupantes 15 %, suelo 10 %, altura 10 %, lejanía a salud 10 %, posible bloqueo de vía 10 %.
# MAGIC
# MAGIC Salidas: `gold_icesixuao_predios`, `gold_icesixuao_comunas`, `gold_icesixuao_sensibilidad` y los GeoJSON del mapa en `/Volumes/workspace/default/icesixuao/salidas/`.

# COMMAND ----------

# MAGIC %pip install geopandas --quiet

# COMMAND ----------

# MAGIC %run ./00_utils_espacial

# COMMAND ----------

# MAGIC %run ./00_pipeline

# COMMAND ----------

s = spark.table(tabla("silver", "predios")).toPandas()
g = gpd.GeoDataFrame(s, geometry=gpd.GeoSeries.from_wkt(s.pop("geom_wkt")), crs=CRS_GEO)
g["comuna"] = g["comuna"].astype("Int64")
g = calcular_indice(g)  # para cambiar pesos: calcular_indice(g, {**PESOS, "c_altura": 0.3})
g["prioridad"].value_counts()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Sensibilidad: ¿el ranking cambia si cambian los pesos?
# MAGIC Si el top 50 se mantiene en buena parte con pesos distintos, la priorización no depende de una elección arbitraria.

# COMMAND ----------

sens = sensibilidad(g, ESCENARIOS_SENSIBILIDAD)
spark.createDataFrame(sens).write.mode("overwrite").option("overwriteSchema", True).saveAsTable(tabla("gold", "sensibilidad"))
sens

# COMMAND ----------

capas = {n: gpd.read_file(f"{VOL}/osm_{n}.geojson") for n in ("comunas", "salud", "emergencia")}
bomberos = capas["emergencia"][capas["emergencia"]["amenity"] == "fire_station"]
gc = gold_comunas(g, capas["comunas"], capas["salud"], bomberos)


def guardar(gdf, nombre, comentario):
    spark.createDataFrame(para_spark(gdf)).write.mode("overwrite").option("overwriteSchema", True).saveAsTable(nombre)
    spark.sql(f"COMMENT ON TABLE {nombre} IS '{comentario}'")


guardar(g, tabla("gold", "predios"), "Edificio con índice de riesgo ante réplicas (0..1) y prioridad de inspección")
guardar(gc, tabla("gold", "comunas"), "Indicadores por comuna y ranking por índice p90")
display(gc.drop(columns="geometry"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Preguntas clave (también sirven para Genie sobre las tablas gold)

# COMMAND ----------

GP = tabla("gold", "predios")
# Afectaciones: cuántos edificios y cuánta área por categoría (la guía: los sin dato pesan distinto en área)
display(spark.sql(f"""
SELECT estado, count(*) AS n, round(100 * count(*) / sum(count(*)) OVER (), 1) AS pct_edificios,
       round(100 * sum(area_m2) / sum(sum(area_m2)) OVER (), 1) AS pct_area
FROM {GP} GROUP BY estado ORDER BY n DESC"""))

# COMMAND ----------

# Top 20 edificios a inspeccionar primero
display(spark.sql(f"""
SELECT id, comuna, barrio, estado, pisos, pisos_imputado, microzona, amplif_suelo, puede_bloquear_via, indice_riesgo
FROM {GP} WHERE NOT sin_dato_satelital ORDER BY indice_riesgo DESC LIMIT 20"""))

# COMMAND ----------

# ¿Los edificios más altos tienen más daño? (solo pisos reales, sin imputados)
display(spark.sql(f"""
SELECT CASE WHEN pisos <= 1 THEN '1' WHEN pisos <= 2 THEN '2' WHEN pisos <= 3 THEN '3' ELSE '4+' END AS rango_pisos,
       count(*) AS n, round(100 * avg(cast(alta_escombros AS int)), 1) AS pct_escombros,
       round(100 * avg(cast(sev_estado >= 0.7 AS int)), 1) AS pct_escombros_o_techo
FROM {GP} WHERE NOT sin_dato_satelital AND NOT pisos_imputado AND pisos IS NOT NULL
GROUP BY 1 ORDER BY 1"""))

# COMMAND ----------

# ¿Qué factor externo se asocia con el daño satelital? Tasa de daño por categoría y prueba chi-cuadrado.
# Resultado con los datos del evento: ninguno es significativo (p > 0,05), ni el daño se agrupa en el espacio.
from scipy.stats import chi2_contingency
v = g[~g["sin_dato_satelital"]].assign(danio=lambda d: d["sev_estado"] >= 0.7)
filas = []
for col in ["periodo_construccion", "estrato", "uso", "microzona", "licuacion_cat", "comuna"]:
    ct = pd.crosstab(v[col], v["danio"])
    filas.append({"factor": col, "categorias": len(ct), "p_valor_chi2": round(chi2_contingency(ct)[1], 3),
                  "pct_danio_min": round(100 * (ct[True] / ct.sum(axis=1)).min(), 1),
                  "pct_danio_max": round(100 * (ct[True] / ct.sum(axis=1)).max(), 1)})
factores = pd.DataFrame(filas)
spark.createDataFrame(factores).write.mode("overwrite").option("overwriteSchema", True).saveAsTable(tabla("gold", "factores"))
display(factores)

# COMMAND ----------

# Población: ocupantes (GEM, censo 2018) en edificios con daño visible y en edificios sin dato satelital
display(spark.sql(f"""
SELECT comuna, round(sum(ocupantes_noche)) AS ocupantes,
       round(sum(CASE WHEN sev_estado >= 0.7 THEN ocupantes_noche END)) AS en_edif_con_danio,
       round(sum(CASE WHEN sin_dato_satelital THEN ocupantes_noche END)) AS en_edif_sin_dato
FROM {GP} GROUP BY comuna ORDER BY en_edif_con_danio DESC"""))

# COMMAND ----------

# Servicios: edificios con escombros cerca de salud y vías principales
display(spark.sql(f"""
SELECT comuna, count(*) AS n_escombros,
       sum(cast(dist_salud_m <= 200 AS int)) AS a_200m_de_salud,
       sum(cast(puede_bloquear_via AS int)) AS pueden_bloquear_via
FROM {GP} WHERE alta_escombros GROUP BY comuna ORDER BY n_escombros DESC"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exportar al mapa
# MAGIC Descargar desde Catalog → workspace → default → Volumes → icesixuao → salidas y copiarlos a `visor/data/` (o abrirlos en Kepler.gl).

# COMMAND ----------

exportar_visor(g, gc, VOL_OUT)
dbutils.fs.ls(VOL_OUT)
