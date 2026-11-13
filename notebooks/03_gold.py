# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · Gold: prioridades explicables, afectación y calidad
# MAGIC Consume exclusivamente las 16 tablas silver. Siete componentes; pesos vigentes conservados.
# MAGIC Lotes y sin dato quedan fuera del ranking. Ocupación GEM modelada no es población afectada.
# MAGIC Contrato: docs/ORO.md. No certifica seguridad ni predice colapso.

# COMMAND ----------

# MAGIC %pip install geopandas scipy pyarrow --quiet

# COMMAND ----------

# MAGIC %run ./00_utils_espacial

# COMMAND ----------

# MAGIC %run ./00_pipeline

# COMMAND ----------

# MAGIC %run ./00_silver

# COMMAND ----------

# MAGIC %run ./00_gold

# COMMAND ----------

plata = {}
for nombre in TABLAS_PLATA_ORO:
    d = spark.table(tabla("silver", nombre)).toPandas()
    plata[nombre] = geometria_plata(d) if nombre in GEO_PLATA_ORO else d
tablas_oro, reporte = construir_oro(plata)
print(reporte)
display(tablas_oro["calidad"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Publicación
# MAGIC Todas las validaciones terminan antes de escribir. Las escrituras Delta son individuales;
# MAGIC no hay transacción global entre tablas. Una ejecución incompleta no autoriza exportar el mapa.

# COMMAND ----------

guardar_oro_spark(spark, tablas_oro, plata)

# COMMAND ----------

# Comentarios de tabla y columna para el Catalog y Genie. Se puede correr solo, tras los %run, sobre tablas ya publicadas.
comentar_oro_spark(spark)

# COMMAND ----------

display(tablas_oro["comunas"].drop(columns="geometry"))
display(tablas_oro["predios"].query("en_ranking").sort_values("posicion")[["id", "comuna", "posicion", "prioridad", "indice_riesgo", "motivos_principales", "peso_base_disponible"]].head(20))
display(tablas_oro["resumen_sensibilidad"])
display(tablas_oro["factores"])
display(tablas_oro["afectaciones"])
display(tablas_oro["verificaciones"].head(20))

# COMMAND ----------

exportar_visor(tablas_oro["predios"], tablas_oro["comunas"], VOL_OUT)
dbutils.fs.ls(VOL_OUT)
