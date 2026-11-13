# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · Gold: índice de riesgo ante réplicas, ranking por comuna y exportación al visor
# MAGIC
# MAGIC Índice = suma ponderada de 5 componentes normalizados a 0..1 (justificación en `docs/INDICE_RIESGO.md`):
# MAGIC daño observado 35 %, altura 20 %, exposición 15 %, lejanía a salud 15 %, posible bloqueo de vía 15 %.
# MAGIC
# MAGIC Salidas: `gold_edificios`, `gold_comunas`, `gold_sensibilidad` y los GeoJSON para el visor en `/Volumes/workspace/databridge/salidas/`.

# COMMAND ----------

# MAGIC %pip install geopandas --quiet

# COMMAND ----------

# MAGIC %run ./00_utils_espacial

# COMMAND ----------

# MAGIC %run ./00_pipeline

# COMMAND ----------

ESQUEMA = "workspace.databridge"
VOL_EXT = "/Volumes/workspace/databridge/externos"
VOL_OUT = "/Volumes/workspace/databridge/salidas"

s = spark.table(f"{ESQUEMA}.silver_edificios").toPandas()
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
spark.createDataFrame(sens).write.mode("overwrite").option("overwriteSchema", True).saveAsTable(f"{ESQUEMA}.gold_sensibilidad")
sens

# COMMAND ----------

capas = {n: gpd.read_file(f"{VOL_EXT}/osm_{n}.geojson") for n in ("comunas", "salud", "emergencia")}
bomberos = capas["emergencia"][capas["emergencia"]["amenity"] == "fire_station"]
gc = gold_comunas(g, capas["comunas"], capas["salud"], bomberos)

def guardar(gdf, tabla, comentario):
    spark.createDataFrame(para_spark(gdf)).write.mode("overwrite").option("overwriteSchema", True).saveAsTable(f"{ESQUEMA}.{tabla}")
    spark.sql(f"COMMENT ON TABLE {ESQUEMA}.{tabla} IS '{comentario}'")

guardar(g, "gold_edificios", "Edificio con índice de riesgo ante réplicas (0..1) y prioridad de inspección")
guardar(gc, "gold_comunas", "Indicadores por comuna y ranking por índice p90")
display(gc.drop(columns="geometry"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Preguntas clave (también sirven para Genie sobre las tablas gold)

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Top 20 edificios a inspeccionar primero
# MAGIC SELECT id, comuna, barrio, pisos, round(prob_escombros, 2) AS prob_escombros, puede_bloquear_via, indice_riesgo
# MAGIC FROM workspace.databridge.gold_edificios
# MAGIC WHERE NOT sin_dato_satelital
# MAGIC ORDER BY indice_riesgo DESC LIMIT 20;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Vías principales con más edificios cuyos escombros podrían bloquearlas
# MAGIC SELECT barrio, comuna, count(*) AS edificios_que_pueden_bloquear
# MAGIC FROM workspace.databridge.gold_edificios
# MAGIC WHERE puede_bloquear_via
# MAGIC GROUP BY barrio, comuna ORDER BY edificios_que_pueden_bloquear DESC LIMIT 15;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ¿Los edificios altos tienen más probabilidad de escombros? (factor explicativo)
# MAGIC SELECT CASE WHEN pisos <= 2 THEN '1-2' WHEN pisos <= 5 THEN '3-5' WHEN pisos <= 10 THEN '6-10' ELSE '11+' END AS rango_pisos,
# MAGIC        count(*) AS n, round(avg(prob_escombros), 3) AS prob_media, round(100 * avg(cast(alta_escombros AS int)), 1) AS pct_alta
# MAGIC FROM workspace.databridge.gold_edificios WHERE NOT sin_dato_satelital
# MAGIC GROUP BY 1 ORDER BY min(pisos);

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exportar al visor
# MAGIC Descargar desde Catalog → databridge → salidas los archivos y copiarlos a `visor/data/` (reemplazan los de muestra).

# COMMAND ----------

exportar_visor(g, gc, VOL_OUT)
dbutils.fs.ls(VOL_OUT)
