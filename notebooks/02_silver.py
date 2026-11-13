# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Silver: entidades tipadas, cruces y calidad
# MAGIC
# MAGIC Lee las tablas bronze, valida todas las salidas antes de escribir y conserva los predios.
# MAGIC NPISOS=0 identifica lotes: no se imputa. Pisos observados, estimados y método van separados.
# MAGIC GEM se mantiene como cruce por cercanía a ≤15 m según la decisión del equipo:
# MAGIC ocupantes/valor se suman entre empates; atributos del mayor número de ocupantes y luego ID.
# MAGIC Las relaciones explicitan empates y reutilización; no acreditan identidad catastral ni población única.
# MAGIC ShakeMap y amplificación se conservan separados. Proximidad no equivale a capacidad o tiempo de viaje.
# MAGIC Contrato y límites: docs/PLATA.md. Los pesos y el ranking se calculan en 03_gold.

# COMMAND ----------

# MAGIC %pip install geopandas pyarrow --quiet

# COMMAND ----------

# MAGIC %run ./00_utils_espacial

# COMMAND ----------

# MAGIC %run ./00_pipeline

# COMMAND ----------

# MAGIC %run ./00_silver

# COMMAND ----------

raw = spark.table(tabla("bronze", "predios")).toPandas()
fuentes = {nombre: spark.table(tabla("bronze", nombre)).toPandas() for nombre in ARCHIVOS_PLATA}
tablas_plata, reporte = construir_plata(raw, fuentes)
tablas_plata["fuentes"]["modo_lectura"] = "tabla_bronze_databricks"
tablas_plata["fuentes"]["tabla_origen"] = tablas_plata["fuentes"].fuente.map(lambda n: tabla("bronze", n))
print(reporte)
display(tablas_plata["calidad"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Publicación
# MAGIC Si falla una puerta de calidad, la transformación lanza un error antes de escribir tablas.
# MAGIC Las tablas se escriben individualmente en Delta; el conjunto no es una transacción entre tablas.
# MAGIC No ejecutar gold hasta que termine esta celda. Las columnas nulas tienen esquema explícito.

# COMMAND ----------

guardar_plata_spark(spark, tablas_plata)
spark.sql(f"COMMENT ON TABLE {tabla('silver', 'predios')} IS 'Inventario predial satelital con cruces por cercanía y calidad. No certifica seguridad. GEM no acredita identidad catastral ni población única.'")

comentarios = {
    "npisos_original": "Valor NPISOS entregado por la organización, incluido cero y NULL",
    "pisos_observados": "Pisos oficiales positivos válidos; lotes y desconocidos quedan nulos",
    "pisos_estimados": "Solo para pisos desconocidos; estimación GEM o mediana identificada en pisos_fuente",
    "pisos": "Pisos efectivos para modelar: observados o estimados; lotes siempre nulos",
    "sin_construccion_registrada": "NPISOS=0: predio sin edificación registrada; se conserva y no se imputa",
    "ocupantes_noche": "Estimación GEM por cercanía, suma entre empates; puede repetirse entre predios. No sumar como población única",
    "gem_ambiguo": "Varios registros GEM empatan en distancia mínima al contorno",
    "gem_reutilizado": "Algún candidato GEM está asociado también a otros predios; ver cruces_gem",
    "dist_salud_m": "Distancia euclidiana entre contorno y sitio OSM, EPSG:9377; no tiempo ni capacidad",
    "dist_salud_urgencias_m": "Distancia a OSM con urgencias=yes; desconocido no equivale a no",
    "periodo_s": "Estimación pisos/10 discretizada a períodos GEM; sin período en lotes o pisos no disponibles",
    "amplif_suelo": "Factor del escenario GEM a 0.2267g en roca; separado de ShakeMap; sin fallback a 1",
    "n_edif_100m": "Registros no marcados como lote a 100m del contorno, incluye el propio; no población",
    "pga_g": "PGA del nodo ShakeMap cercano, convertida desde porcentaje de g dividiendo por 100",
    "pendiente_grados": "Alias heredado de pendiente_original; unidad etiquetada por extractor, pendiente de confirmar en origen",
}
for columna, comentario in comentarios.items():
    spark.sql(f"ALTER TABLE {tabla('silver', 'predios')} ALTER COLUMN {columna} COMMENT '{comentario}'")

# COMMAND ----------

display(tablas_plata["predios"].drop(columns="geometry").describe(include="number"))
display(tablas_plata["predios"].groupby("estado_predial").size().rename("predios").reset_index())
display(tablas_plata["observaciones"].groupby("tipo_observacion").size().rename("observaciones").reset_index())
