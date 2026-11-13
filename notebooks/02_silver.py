# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Silver: limpieza y cruces espaciales
# MAGIC
# MAGIC 1. Tipos y categorías normalizadas (espacios y vacíos a nulo), NPISOS = 0 o nulo imputado con la mediana de la comuna y marcado, polígonos inválidos reparados, área real en m². Todo queda contado en el reporte.
# MAGIC 2. Marca `sin_dato_satelital`: esos edificios **no se borran**; se marcan para verificación en terreno.
# MAGIC 3. Cruces con OSM: comuna faltante, barrio, distancia a salud, bomberos y vía principal, densidad de edificios a 100 m y si sus escombros podrían bloquear una vía.
# MAGIC 4. Cruce con la microzonificación sísmica (GEM TREQ): microzona y amplificación del suelo en el período propio del edificio.
# MAGIC 5. Cruce con el modelo de exposición de GEM (edificio por edificio: año, estrato, uso, pisos, ocupantes, vulnerabilidad), la susceptibilidad a licuación y pendiente (GEM) y el ShakeMap del USGS. NPISOS = 0 se completa con los pisos de GEM.

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
g = enriquecer(cruzar_externos(a_geo(silver), VOL), capas["comunas"], capas["barrios"], capas["salud"], bomberos, capas["vias_principales"])
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
    "pisos_imputado": "True si NPISOS era nulo y se imputó (GEM o mediana de la comuna)",
    "sin_construccion_registrada": "True si NPISOS = 0: predio sin edificación registrada en catastro (organizadores); pisos queda nulo",
    "ocupantes_noche": "Ocupantes nocturnos de GEM (censo 2018); si varios registros GEM empatan, se suman",
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
    "dist_gem_m": "Metros al edificio del modelo de exposición GEM usado (0 = dentro del polígono; nulo si > 15 m)",
    "periodo_construccion": "Período de construcción según GEM (catastro 2021); hitos del código: 1984, 1998, 2010",
    "estrato": "Estrato socioeconómico según GEM",
    "p_ductilidad_baja": "Probabilidad de ductilidad baja o nula de su tipología (GEM, esquema de expertos MEAN)",
    "p_mamposteria_no_reforzada": "Probabilidad de mampostería no reforzada o adobe de su tipología (GEM)",
    "pisos_fuente": "oficial = NPISOS; gem = NPISOS era 0 o nulo y se tomó de GEM; mediana_comuna = sin dato en ambos",
    "licuacion_cat": "Susceptibilidad a licuación del sitio más cercano (GEM): vh, h, m, l, vl, n",
    "pendiente_grados": "Pendiente del terreno en el sitio más cercano (GEM)",
    "mmi": "Intensidad Mercalli del sismo principal en su nodo del ShakeMap v11 del USGS (~1 km)",
    "pga_g": "Aceleración pico del suelo (g) en su nodo del ShakeMap del USGS",
}
for col, txt in comentarios.items():
    spark.sql(f"ALTER TABLE {tabla('silver', 'predios')} ALTER COLUMN {col} COMMENT '{txt}'")
spark.sql(f"COMMENT ON TABLE {tabla('silver', 'predios')} IS 'Edificios limpios y enriquecidos con OSM. Base satelital: sirve para priorizar, no para declarar seguridad.'")
