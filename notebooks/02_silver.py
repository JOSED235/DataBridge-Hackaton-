# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Silver: limpieza y cruces espaciales
# MAGIC
# MAGIC 1. Tipos y categorías normalizadas (espacios y vacíos a nulo), NPISOS = 0 o nulo imputado con la mediana de la comuna y marcado, polígonos inválidos reparados, área real en m². Todo queda contado en el reporte.
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

raw = spark.table(tabla("bronze", "predios")).toPandas()  # ~5 MB: cabe de sobra en memoria
silver, reporte = limpiar(raw)
reporte  # copiar a la bitácora: es la justificación de cada paso de limpieza

# COMMAND ----------

capas = {n: gpd.read_file(f"{VOL}/osm_{n}.geojson") for n in ("comunas", "barrios", "salud", "emergencia", "vias_principales")}
bomberos = capas["emergencia"][capas["emergencia"]["amenity"] == "fire_station"]
g = enriquecer(a_geo(silver), capas["comunas"], capas["barrios"], capas["salud"], bomberos, capas["vias_principales"])
g = asignar_suelo(g, *leer_suelo(VOL))  # microzona y amplificación del suelo (GEM TREQ)
reporte["geometrias_reparadas"] = int(g["geom_reparada"].sum())
reporte["comuna_completada_con_osm"] = int(silver["comuna"].isna().sum())
print(reporte, "| fuera de microzonas:", int((g["microzona"] == "noaf").sum()))
g.drop(columns="geometry").describe()

# COMMAND ----------

(spark.createDataFrame(para_spark(g)).write.mode("overwrite").option("overwriteSchema", True)
     .saveAsTable(tabla("silver", "predios")))

comentarios = {
    "sin_dato_satelital": "True si Estado_Estructural es Sin datos satelitales. No significa sin daño",
    "sev_estado": "Severidad 0..1: escombros 1, techo desaparecido 0,7, sin cambio aparente 0,1 (puede haber daño interno)",
    "indice_escombros": "Indice_Escombros original: puntaje con signo; > 4,3 escombros y < -10,8 techo desaparecido",
    "alta_escombros": "True si Estado_Estructural es Alta probabilidad de escombros",
    "pisos_imputado": "True si NPISOS era 0 o nulo y se imputó con la mediana de la comuna",
    "area_m2": "Área del contorno en m² (EPSG:9377); Shape__Area original está en grados",
    "geom_reparada": "True si el polígono era inválido y se reparó con make_valid",
    "barrio_cod": "Código de barrio original; solo identifica un barrio junto con la comuna",
    "dist_salud_m": "Metros al hospital o clínica más cercano (OSM)",
    "dist_via_principal_m": "Metros a la vía principal más cercana (OSM: motorway, trunk, primary, secondary)",
    "n_edif_100m": "Edificios a menos de 100 m (proxy de población expuesta)",
    "puede_bloquear_via": "Alta prob. de escombros y distancia a vía principal <= altura estimada (pisos x 3 m)",
    "microzona": "Microzona sísmica INGEOMINAS-DAGMA 2005 (grilla GEM TREQ); noaf = fuera de la microzonificación",
    "periodo_s": "Período propio estimado del edificio, T = pisos/10 s, redondeado a los períodos del modelo GEM",
    "amplif_suelo": "Factor de amplificación del suelo de su microzona en su período propio (GEM TREQ, roca 0,23 g)",
}
for col, txt in comentarios.items():
    spark.sql(f"ALTER TABLE {tabla('silver', 'predios')} ALTER COLUMN {col} COMMENT '{txt}'")
spark.sql(f"COMMENT ON TABLE {tabla('silver', 'predios')} IS 'Edificios limpios y enriquecidos con OSM. Base satelital: sirve para priorizar, no para declarar seguridad.'")
