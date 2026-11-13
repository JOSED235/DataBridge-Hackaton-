# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Bronze: datos crudos tal como llegan
# MAGIC
# MAGIC - **Edificios** (datos oficiales del evento, satelitales, no redistribuibles).
# MAGIC - **Capas externas** (`data/externos/` del repo): comunas, barrios, salud, bomberos/policía, vías (OpenStreetMap) y sismos (USGS).
# MAGIC
# MAGIC Bronze no corrige nada: guarda una copia fiel para poder rehacer silver/gold si algo sale mal.
# MAGIC
# MAGIC **Antes de correr:** subir los `.geojson` de `data/externos/` al volumen `/Volumes/workspace/databridge/externos/` (Catalog → workspace → databridge → externos → *Upload to this volume*).

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE SCHEMA IF NOT EXISTS workspace.databridge COMMENT 'DataBridge Hack: sismo 10-ago-2026, Cali';
# MAGIC CREATE VOLUME IF NOT EXISTS workspace.databridge.externos COMMENT 'Capas externas (OSM, USGS) en GeoJSON';
# MAGIC CREATE VOLUME IF NOT EXISTS workspace.databridge.salidas COMMENT 'GeoJSON exportados para el visor';

# COMMAND ----------

# TODO-VIERNES: completar según el paso a paso de carga de los organizadores.
# Opción A: ya crearon una tabla -> poner su nombre completo en TABLA_ORIGEN.
# Opción B: subimos un archivo a un volumen -> poner su ruta en ARCHIVO_ORIGEN (csv o geojson).
TABLA_ORIGEN = ""        # ej. "workspace.default.edificios"
ARCHIVO_ORIGEN = ""      # ej. "/Volumes/workspace/databridge/externos/edificios.csv"
ESQUEMA = "workspace.databridge"
VOL_EXT = "/Volumes/workspace/databridge/externos"

# COMMAND ----------

if TABLA_ORIGEN:
    df = spark.table(TABLA_ORIGEN)
elif ARCHIVO_ORIGEN.lower().endswith(".csv"):
    df = spark.read.option("header", True).option("inferSchema", False).csv(ARCHIVO_ORIGEN)  # todo como texto: los tipos se corrigen en silver
elif ARCHIVO_ORIGEN.lower().endswith((".geojson", ".json")):
    import geopandas as gpd  # si falla: correr %pip install geopandas en una celda aparte
    g = gpd.read_file(ARCHIVO_ORIGEN)
    g["geom_wkt"] = g.geometry.to_wkt()
    df = spark.createDataFrame(g.drop(columns="geometry").astype(str))
else:
    raise ValueError("Definir TABLA_ORIGEN o ARCHIVO_ORIGEN")

df.write.mode("overwrite").option("overwriteSchema", True).saveAsTable(f"{ESQUEMA}.bronze_edificios")
spark.sql(f"COMMENT ON TABLE {ESQUEMA}.bronze_edificios IS 'Edificios tal como los entregó la organización (análisis satelital, no inspección en terreno). No redistribuir.'")
print(df.count(), "filas"); df.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Primera revisión (anotar en la bitácora)
# MAGIC Columnas reales, tipos, nulos por columna, valores distintos de `Estado_Estructural`, si hay coordenadas o geometría y en qué CRS.
# MAGIC Con esto se ajusta `COLS` y `SEVERIDAD_ESTADO` en `00_pipeline`.

# COMMAND ----------

from pyspark.sql import functions as F
t = spark.table(f"{ESQUEMA}.bronze_edificios")
display(t.limit(20))
display(t.select([F.round(100 * F.avg(F.col(c).isNull().cast("int")), 2).alias(c) for c in t.columns]))  # % nulos
for c in t.columns:
    if t.select(c).distinct().count() <= 30:
        display(t.groupBy(c).count().orderBy(F.desc("count")))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Capas externas a bronze

# COMMAND ----------

import os
import geopandas as gpd

for archivo in sorted(os.listdir(VOL_EXT)):
    if not archivo.endswith(".geojson") or archivo.startswith("edificios"):
        continue
    g = gpd.read_file(f"{VOL_EXT}/{archivo}")
    g["geom_wkt"] = g.geometry.to_wkt()
    tabla = f"{ESQUEMA}.bronze_{archivo.removesuffix('.geojson').replace('-', '_').replace('.', '_')}"
    spark.createDataFrame(g.drop(columns="geometry").astype(str)).write.mode("overwrite").option("overwriteSchema", True).saveAsTable(tabla)
    print(f"{tabla}: {len(g)} filas")
