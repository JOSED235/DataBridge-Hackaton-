# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Bronze: datos crudos tal como llegan
# MAGIC
# MAGIC - **Edificios**: `Datosprediales.json` de la organización (5.146 edificios, 20 propiedades + geometría; análisis satelital, no redistribuible).
# MAGIC - **Capas externas** (`data/externos/` del repo): comunas, barrios, salud, bomberos/policía, vías (OpenStreetMap); réplicas, ShakeMap y estaciones (USGS/SGC); microzonas, amplificación, licuación, pendiente y modelo de exposición edificio por edificio (GEM TREQ).
# MAGIC
# MAGIC Bronze no corrige nada: guarda una copia fiel, **todo como texto y con los nulos tal como vienen**, para poder rehacer silver/gold si algo sale mal. Los tipos se corrigen en silver.
# MAGIC
# MAGIC **Antes de correr:** correr la celda que crea el volumen y subir a él `Datosprediales.json` y los `.geojson` y `.csv` de `data/externos/` (Catalog → workspace → default → Volumes → icesixuao → *Upload to this volume*).

# COMMAND ----------

# MAGIC %pip install geopandas --quiet

# COMMAND ----------

# MAGIC %run ./00_utils_espacial

# COMMAND ----------

# MAGIC %run ./00_pipeline

# COMMAND ----------

spark.sql(f"CREATE VOLUME IF NOT EXISTS {ESQUEMA}.{EQUIPO} COMMENT 'DataBridge Hack: edificios de la organización y capas externas'")
print("Subir los archivos a:", VOL)

# COMMAND ----------

import os
import geopandas as gpd
from pyspark.sql.types import StringType, StructField, StructType


def guardar_texto(pdf, nombre, comentario):
    """pandas (todo texto) -> tabla Delta con esquema explícito de strings (sirve aunque una columna sea 100 % nula)."""
    esquema = StructType([StructField(c, StringType()) for c in pdf.columns])
    spark.createDataFrame(pdf, esquema).write.mode("overwrite").option("overwriteSchema", True).saveAsTable(nombre)
    spark.sql(f"COMMENT ON TABLE {nombre} IS '{comentario}'")
    print(f"{nombre}: {len(pdf)} filas, {len(pdf.columns)} columnas")


ARCHIVO_ORIGEN = f"{VOL}/Datosprediales.json"
bronze = bronze_desde_geojson(gpd.read_file(ARCHIVO_ORIGEN))
assert bronze.shape == (5146, 21), bronze.shape  # la guía: 5.146 filas y 21 columnas (20 propiedades + geometría)
guardar_texto(bronze, tabla("bronze", "predios"),
              "Edificios tal como los entregó la organización (análisis satelital, no inspección en terreno). No redistribuir.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Primera revisión (anotar en la bitácora)

# COMMAND ----------

from pyspark.sql import functions as F
t = spark.table(tabla("bronze", "predios"))
display(t.limit(20))
display(t.select([F.round(100 * F.avg(F.col(c).isNull().cast("int")), 2).alias(c) for c in t.columns]))  # % nulos
display(t.select([F.sum((F.trim(F.col(c)) == "").cast("int")).alias(c) for c in t.columns]))  # vacíos o solo espacios
display(t.groupBy("Estado_Estructural").count().orderBy(F.desc("count")))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Capas externas a bronze

# COMMAND ----------

for archivo in sorted(os.listdir(VOL)):
    nombre = archivo.rsplit(".", 1)[0].replace("-", "_").replace(".", "_")
    if archivo.endswith(".geojson"):
        guardar_texto(bronze_desde_geojson(gpd.read_file(f"{VOL}/{archivo}")), tabla("bronze", nombre), f"Capa externa {archivo} sin modificar")
    elif archivo.startswith(("gem_", "usgs_")) and archivo.endswith(".csv"):
        pdf = pd.read_csv(f"{VOL}/{archivo}", dtype=str, comment="#", keep_default_na=False).replace("", None)
        guardar_texto(pdf, tabla("bronze", nombre), f"Fuente externa {archivo} (ver docs/FUENTES.md)")
