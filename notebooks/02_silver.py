# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Silver: limpieza y cruces espaciales
# MAGIC
# MAGIC 1. Tipos y categorías normalizadas, pisos inválidos anulados e imputados (mediana de la comuna), duplicados y filas sin coordenadas fuera. Todo queda contado en el reporte.
# MAGIC 2. Marca `sin_dato_satelital`: esos edificios **no se borran**; se marcan para verificación en terreno.
# MAGIC 3. Cruces con OSM: comuna faltante, barrio, distancia a salud, bomberos y vía principal, densidad de edificios a 100 m y si sus escombros podrían bloquear una vía.
# MAGIC 4. Cruce con la microzonificación sísmica (GEM TREQ): microzona y amplificación del suelo en el período propio del edificio.

# COMMAND ----------

# MAGIC %pip install geopandas --quiet

# COMMAND ----------

# MAGIC %run ./00_utils_espacial

# COMMAND ----------

# MAGIC %run ./00_pipeline

# COMMAND ----------

ESQUEMA = "workspace.databridge"
VOL_EXT = "/Volumes/workspace/databridge/externos"
# TODO-VIERNES: si los nombres reales difieren, ajustar aquí (o en 00_pipeline) antes de seguir.
# COLS.update({"escombros": "Probabilidad_Escombros"})

# COMMAND ----------

raw = spark.table(f"{ESQUEMA}.bronze_edificios").toPandas()  # ~5 MB: cabe de sobra en memoria
silver, reporte = limpiar(raw)
reporte  # copiar a la bitácora: es la justificación de cada paso de limpieza

# COMMAND ----------

capas = {n: gpd.read_file(f"{VOL_EXT}/osm_{n}.geojson") for n in ("comunas", "barrios", "salud", "emergencia", "vias_principales")}
bomberos = capas["emergencia"][capas["emergencia"]["amenity"] == "fire_station"]
g = enriquecer(a_geo(silver), capas["comunas"], capas["barrios"], capas["salud"], bomberos, capas["vias_principales"])
g = asignar_suelo(g, *leer_suelo(VOL_EXT))  # microzona y amplificación del suelo (GEM TREQ)
print("comuna sin asignar:", int(g["comuna"].isna().sum()), "| fuera de microzonas:", int((g["microzona"] == "noaf").sum()))
g.drop(columns="geometry").describe()

# COMMAND ----------

(spark.createDataFrame(para_spark(g)).write.mode("overwrite").option("overwriteSchema", True)
     .saveAsTable(f"{ESQUEMA}.silver_edificios"))

comentarios = {
    "sin_dato_satelital": "True si el análisis satelital no da estado ni probabilidad de escombros",
    "prob_escombros": "Probabilidad de escombros normalizada a 0..1",
    "sev_estado": "Severidad 0..1 derivada de Estado_Estructural (ver SEVERIDAD_ESTADO)",
    "pisos_imputado": "True si NPISOS faltaba o era inválido y se imputó con la mediana de la comuna",
    "dist_salud_m": "Metros al hospital o clínica más cercano (OSM)",
    "dist_via_principal_m": "Metros a la vía principal más cercana (OSM: motorway, trunk, primary, secondary)",
    "n_edif_100m": "Edificios a menos de 100 m (proxy de población expuesta)",
    "puede_bloquear_via": "Alta prob. de escombros y distancia a vía principal <= altura estimada (pisos x 3 m)",
    "microzona": "Microzona sísmica INGEOMINAS-DAGMA 2005 (grilla GEM TREQ); noaf = fuera de la microzonificación",
    "periodo_s": "Período propio estimado del edificio, T = pisos/10 s, redondeado a los períodos del modelo GEM",
    "amplif_suelo": "Factor de amplificación del suelo de su microzona en su período propio (GEM TREQ, roca 0,23 g)",
}
for col, txt in comentarios.items():
    spark.sql(f"ALTER TABLE {ESQUEMA}.silver_edificios ALTER COLUMN {col} COMMENT '{txt}'")
spark.sql(f"COMMENT ON TABLE {ESQUEMA}.silver_edificios IS 'Edificios limpios y enriquecidos con OSM. Base satelital: sirve para priorizar, no para declarar seguridad.'")
