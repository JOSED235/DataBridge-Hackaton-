# Bitácora del equipo

> Cada aporte se registra aquí en el momento en que se hace. El responsable es siempre un integrante del equipo. Formato y reglas en `CLAUDE.md`.

## Aportes

### 2026-11-12 23:35 · José David
**Qué:** Documento maestro del equipo con la guía oficial, la estrategia y el plan de trabajo.
**Por qué:** Tener en un solo lugar las reglas del evento, la pregunta problema y cómo pensamos ganar.
**Archivos:** `docs/DataBridge_Hack_Plan_Maestro.md`

### 2026-11-12 23:45 · José David
**Qué:** Descarga de fuentes externas: catálogo de sismos del USGS (76 eventos M ≥ 2,5) y capas de OpenStreetMap para Cali (22 comunas, 338 barrios, 439 sitios de salud, 63 estaciones de bomberos y policía, 287 sitios de educación, 4070 tramos de vías principales). Script reproducible con reintentos ante errores del servidor.
**Por qué:** Explicar el porqué del daño y medir el impacto en servicios urbanos. El portal de datos abiertos de Cali y la IDESC están fuera de línea desde el 21-oct-2026.
**Archivos:** `scripts/descargar_osm.py`, `data/externos/*.geojson`, `docs/FUENTES.md`

### 2026-11-12 23:55 · José David
**Qué:** Funciones espaciales (unión espacial, distancia al más cercano, conteo en radio, normalización, índice ponderado y análisis de sensibilidad) con autoprueba sobre datos sintéticos.
**Por qué:** Dejar probadas antes del evento las operaciones que más fallan bajo presión (CRS, uniones y distancias).
**Archivos:** `notebooks/00_utils_espacial.py`

### 2026-11-13 00:10 · José David
**Qué:** Pipeline bronze/silver/gold para Databricks. La lógica está en funciones de pandas/GeoPandas (`00_pipeline`) y los notebooks 01 a 03 solo leen y escriben tablas. Simulación de extremo a extremo con edificios ficticios que valida el flujo y genera datos de muestra para el visor.
**Por qué:** El viernes solo hay que ajustar los nombres de columnas; el resto ya está probado. Los datos de muestra permiten construir el visor sin esperar los oficiales.
**Archivos:** `notebooks/00_pipeline.py`, `notebooks/01_bronze.py`, `notebooks/02_silver.py`, `notebooks/03_gold.py`, `scripts/simular_pipeline.py`

### 2026-11-13 00:25 · José David
**Qué:** Visor web con MapLibre GL JS + deck.gl: edificios 3D por pisos, color por prioridad, índice o escombros; capas de comunas, calor, vías, salud, emergencia y sismos; KPIs, filtro por comuna, ranking y recorrido guiado de 4 pasos. Librerías copiadas en `visor/vendor/` para funcionar sin internet; si no hay internet usa un fondo plano.
**Por qué:** Diferenciarnos de los equipos que usen solo Kepler.gl y contar la historia del problema a la recomendación durante la demo.
**Archivos:** `visor/index.html`, `visor/app.js`, `visor/vendor/`, `visor/data/`

### 2026-11-13 00:35 · José David
**Qué:** Documentación: índice de riesgo, fuentes, guion con preguntas del jurado, plan paso a paso del viernes, reglas del repo y README.
**Por qué:** El jurado pregunta el porqué de cada decisión y el viernes no hay tiempo de escribir desde cero.
**Archivos:** `docs/INDICE_RIESGO.md`, `docs/FUENTES.md`, `docs/GUION_PRESENTACION.md`, `docs/PLAN_VIERNES.md`, `CLAUDE.md`, `AGENTS.md`, `README.md`

### 2026-11-13 00:45 · José David
**Qué:** Estrategia de solución (cómo se responde cada mitad de la pregunta en cada dimensión, qué nos diferencia, reglas para decidir rápido y reparto), lista de pendientes para hoy, el viernes y el sábado.
**Por qué:** Llegar al evento con el plan decidido y aprovechar el día solo en ejecutar con los datos reales.
**Archivos:** `docs/PLAN_VIERNES.md`, `README.md`

### 2026-11-13 01:00 · José David
**Qué:** Guía de Databricks paso a paso para principiantes: conceptos, cuenta, traer el código del repo (Git folder o importación), prueba de GeoPandas, carga de datos, ajuste de configuración, silver/gold, descarga al visor, Genie y problemas comunes.
**Por qué:** El equipo casi no tiene experiencia con Databricks y el viernes no hay tiempo para aprender la plataforma sobre la marcha.
**Archivos:** `docs/GUIA_DATABRICKS.md`, `docs/PLAN_VIERNES.md`, `README.md`

### 2026-11-13 09:36 · Mrsasayo
**Qué:** Informe de investigación previa (44 páginas): parámetros oficiales del sismo, comparación con el doblete de Venezuela de junio de 2026, catálogo de fuentes oficiales, efecto del suelo y de la profundidad, banco de 19 terremotos comparables, física de ondas, historia del código sismorresistente, corrupción constructiva y propuesta de flujo bronze/silver/gold.
**Por qué:** Sustentar el "por qué pasó" y los factores que reducen el impacto de las réplicas con evidencia citada.
**Archivos:** `docs/Informe_Sismo_10Agosto2026_DatosOficiales_Cali.pdf` (luego convertido a `docs/INFORME_SISMO.md`)

### 2026-11-13 09:45 · José David
**Qué:** Conversión del informe a Markdown (texto y 8 tablas completas; las 6 figuras quedan como leyenda) y retiro del PDF del repo, recuperable desde el commit `5cbd157`.
**Por qué:** El Markdown se lee y se busca más rápido durante el evento, se ve en GitHub y sus cambios se pueden revisar línea por línea.
**Archivos:** `docs/INFORME_SISMO.md`, `docs/Informe_Sismo_10Agosto2026_DatosOficiales_Cali.pdf` (eliminado), `README.md`

### 2026-11-13 09:50 · José David
**Qué:** Factor de suelo en el pipeline y en el índice. Se descargó de GEM TREQ la grilla de microzonas de Cali y las funciones de amplificación. Cada edificio toma la microzona del punto más cercano de la grilla y la amplificación de esa microzona en su período propio (T ≈ pisos/10 s). Nuevo componente `c_suelo` (15 %), escenario de sensibilidad `sin_suelo`, columnas de suelo en `gold_comunas` y el visor, y dos SQL en `03_gold`: daño por microzona dentro de cada rango de pisos (prueba del efecto de sitio) y edificios de 15 a 25 pisos sobre suelo que amplifica su período (resonancia). Simulación de extremo a extremo aprobada.
**Por qué:** El informe muestra que el suelo blando de Cali amplifica hasta unas 2 veces los períodos largos y que es el factor que explica el daño a 160 km del epicentro. El índice no lo tenía porque la capa oficial está caída.
**Archivos:** `notebooks/00_pipeline.py`, `notebooks/01_bronze.py`, `notebooks/02_silver.py`, `notebooks/03_gold.py`, `scripts/simular_pipeline.py`, `data/externos/gem_microzonas_grilla.csv`, `data/externos/gem_amplificacion_suelo.csv`, `docs/INDICE_RIESGO.md`, `docs/FUENTES.md`, `docs/GUION_PRESENTACION.md`, `docs/GUIA_DATABRICKS.md`, `docs/PLAN_VIERNES.md`, `README.md`

### 2026-11-13 10:30 · José David
**Qué:** Llegaron la guía oficial y los datos. Datos: `Datosprediales.json`, 5.146 polígonos en EPSG:4326 con 20 propiedades. Columnas clave: `OBJECTID` (único), `COMUNA`, `BARRIO`, `NPISOS`, `Indice_Escombros` y `Estado_Estructural`. Las 4 categorías de estado: sin cambio aparente / daño interno 3.357, posible desaparición de techo 1.058, sin datos satelitales 435, alta probabilidad de escombros 296. Hay 7 comunas, 2 filas con `COMUNA` vacía, 1.234 con `NPISOS` = 0 y 11 nulos, y 17 polígonos inválidos. `Indice_Escombros` tiene dos colas de daño: más de 4,3 es escombros y menos de -10,8 es techo desaparecido.
**Por qué:** Es la base para ajustar la configuración del pipeline y justificar cada limpieza.
**Archivos:** `DataBridge_Hack_Guia_Evento_2.md`, `data/oficiales/` (fuera de git)

### 2026-11-13 10:30 · José David
**Qué:** Pipeline adaptado a los datos y a la guía. Nombres `workspace.default.<capa>_icesixuao_<contenido>` y volumen del equipo. Bronze guarda todo como texto con nulos reales y comprueba 5.146 × 21. Severidad por categoría, `alta_escombros` desde la categoría, pisos 0 imputados y marcados, polígonos reparados con make_valid, área en m² y % de área sin dato por comuna. Las consultas de gold quedaron en Python para usar los nombres del equipo. Nuevo `scripts/correr_local.py`, que corre todo con los datos oficiales como plan B. El simulador quedó con el formato real y ya no pisa el mapa real. El visor muestra daño y suelo en vez de la probabilidad de escombros. `.gitignore` incluye `data/oficiales/` y los GeoJSON del mapa con datos reales.
**Por qué:** La guía fija nombres, esquema y verificación de bronze. Los datos no traen probabilidad sino una categoría y un puntaje con signo.
**Archivos:** `notebooks/00_pipeline.py`, `notebooks/01_bronze.py`, `notebooks/02_silver.py`, `notebooks/03_gold.py`, `scripts/correr_local.py`, `scripts/simular_pipeline.py`, `visor/app.js`, `visor/index.html`, `.gitignore`, `docs/GUIA_DATABRICKS.md`, `docs/PLAN_VIERNES.md`, `docs/INDICE_RIESGO.md`, `README.md`

### 2026-11-13 10:30 · José David
**Qué:** Primera corrida con los datos reales. Reporte de limpieza: 5.146 filas en silver, 1.245 pisos imputados, 17 geometrías reparadas, 2 comunas completadas con OSM y ningún estado sin mapear. Hallazgos: la comuna 19 concentra el 61 % de los edificios. El % de escombros no cambia con la altura (5,5 % a 7 %) ni con la microzona (5,4 % a 8,9 %, sin relación con la amplificación), así que la hipótesis del efecto de sitio **no** se confirma en esta muestra. Los edificios sin dato son el 9,5 % del área, no el ~45 % que menciona la guía. Ranking de comunas por p90: 3, 20, 18, 9, 10, 19, 17. Sensibilidad: Spearman de 0,77 a 0,96; el top 50 se mantiene entre 26 % y 64 %.
**Por qué:** Saber qué sostienen los datos antes de escribir las conclusiones: una conclusión que los datos no sostienen resta puntos.
**Archivos:** `data/oficiales/salidas/` (fuera de git)

### 2026-11-13 10:47 · Mrsasayo
**Qué:** Revisión de las 20 entradas del catálogo y las 38 referencias de `INFORME_SISMO.md`, con acceso, formato, cobertura, utilidad para contrastar ciudades y estado de verificación en `FUENTES.md`. Se consultaron API de USGS, metadatos y agregados de UNGRD, catálogo HDX, servicios DANE y recursos GEM. Se identificaron modelos de exposición de Cali, Quito y Santiago de los Caballeros, 13 escenarios de Cali, productos ShakeMap/DYFI/PAGER y un recurso HDX anunciado para 2016–2026 cuyo libro queda sin inspeccionar. Se corrigió el nombre institucional del CPNAA en la bibliografía y se señaló la revisión desde el README. Se consultó la guía oficial incorporada en paralelo y se actualizó el registro para distinguir su contrato de datos de una inspección del inventario, que no se hizo en este aporte.
**Por qué:** Distinguir conjuntos utilizables de referencias de contexto y no dar por verificadas coberturas, cifras o descargas que todavía están pendientes. Dejar rutas concretas para comparar sacudida, afectación y respuesta, separando datos observados de escenarios modelados. Es una propuesta de incorporación; no modifica los pesos del índice ni adopta nuevas fuentes en el pipeline. La descarga y extracción OSM ya terminadas se toman del resumen del dueño y no se repitieron.
**Archivos:** `docs/FUENTES.md`, `docs/INFORME_SISMO.md`, `README.md`, `docs/BITACORA.md`

### 2026-11-13 10:51 · Mrsasayo
**Qué:** Respaldo local de los archivos e índice antes de concluir el pull que estaba detenido. Se resolvió el único conflicto de `.gitignore` conservando las exclusiones del PBF, datos oficiales y mapas derivados. Fusión registrada en `2b383fe`; después, `git pull --no-rebase` respondió que no había cambios remotos adicionales. Los cambios pendientes de la revisión de fuentes se conservaron fuera del commit de fusión.
**Por qué:** Incorporar los ajustes remotos a los datos oficiales sin perder la extracción OSM local ni la documentación de esta sesión.
**Archivos:** `.gitignore`, `docs/BITACORA.md` (registro); los demás archivos de la fusión corresponden al aporte remoto ya documentado a las 10:30.
### 2026-11-13 10:55 · José David
**Qué:** Nuevas fuentes externas, cruzadas edificio por edificio. (1) Modelo de exposición de GEM TREQ: 348 mil edificios de Cali, recortado a las 7 comunas (95.010), con año, estrato, uso, pisos, ocupantes y vulnerabilidad derivada de la tipología; se cruzó el 98,9 % de los edificios oficiales. (2) Susceptibilidad a licuación y pendiente de GEM. (3) ShakeMap v11 del USGS (MMI 6,4 a 7,1 y PGA 0,19 a 0,23 g en los edificios). (4) Validación del ShakeMap con el acelerógrafo RAC2C del SGC (MMI 6,9 registrada frente a 6,8) y con 32 celdas DYFI (6,86 frente a 6,79). (5) Catálogo de réplicas actualizado: 67 réplicas, 47 en septiembre. Script reproducible y ficha completa de cada fuente: qué es, cómo se obtuvo, por qué, cómo se cruzó, qué aportó y sus límites.
**Por qué:** La guía da 25 puntos a los datos externos y exige que estén citados, bien cruzados y que aporten. Los datos base dicen dónde hubo daño, no quién vive ahí ni qué tan frágil es el edificio.
**Archivos:** `scripts/descargar_externos.py`, `data/externos/gem_exposicion.csv`, `data/externos/gem_sitio_licuacion_ladera.csv`, `data/externos/usgs_shakemap_cali.csv`, `data/externos/usgs_estaciones_cali.geojson`, `data/externos/usgs_replicas.geojson`, `notebooks/00_pipeline.py`, `notebooks/01_bronze.py`, `notebooks/02_silver.py`, `notebooks/03_gold.py`, `scripts/correr_local.py`, `scripts/simular_pipeline.py`, `docs/FUENTES.md`, `docs/INDICE_RIESGO.md`, `docs/GUIA_DATABRICKS.md`, `docs/PLAN_VIERNES.md`, `README.md`

### 2026-11-13 10:55 · José David
**Qué:** Prueba de qué factores externos se asocian con el daño satelital (chi-cuadrado sobre 4.711 edificios con dato) y de agrupamiento espacial (permutación, vecinos a 50 m). Ningún factor es significativo: período p = 0,14, estrato p = 0,94, uso p = 0,85, microzona p = 0,34, licuación p = 0,18, comuna p = 0,51. El daño tampoco se agrupa (p = 0,62). Población: 6.907 ocupantes en edificios con daño visible, 2.646 en edificios sin dato. 35,8 % de los edificios son anteriores a 1985.
**Por qué:** Saber qué sostienen los datos antes de concluir. Que nada explique el daño satelital es un hallazgo: indica una señal individual con posible ruido, y justifica que el índice combine el daño con lo que las fuentes externas saben de cada edificio.
**Archivos:** `notebooks/03_gold.py` (tabla `gold_icesixuao_factores`), `docs/FUENTES.md`

### 2026-11-13 11:13 · Mrsasayo
**Qué:** En curso: análisis exploratorio de bronce en carpeta independiente `analisis_bronce/`, con un notebook por cada uno de los 12 datasets/contenedores locales y salidas ejecutadas en IPYNB y HTML. Se protegió en `.gitignore` el archivo oficial entregado en `data/Datosprediales.json`, se conservó intacto y se verificó una copia en `data/oficiales/`. Se ejecutó `scripts/correr_local.py` con éxito y se guardó su salida en un registro privado. README actualizado con estructura, ejecución y ubicación de resultados. La selección final para plata y su evidencia se registran al cerrar el análisis.
**Por qué:** Evaluar cada fuente antes de cruzarla, conservar resultados visibles y distinguir calidad del dato, cobertura y decisiones de limpieza. La ejecución local del pipeline es una comprobación del estado actual; no significa que ya implemente las nuevas reglas que se decidan desde el EDA.
**Archivos:** `.gitignore`, `README.md`, `analisis_bronce/soporte.py`, `analisis_bronce/ejecutar.py`, `analisis_bronce/notebooks/`, `analisis_bronce/ejecutados/` y `analisis_bronce/resultados/` (salidas fuera de git), `data/oficiales/` (fuera de git), `docs/BITACORA.md`

### 2026-11-13 11:29 · Mrsasayo
**Qué:** Cierre del EDA de bronce: 17 notebooks independientes, uno por dataset/contenedor local, y una síntesis posterior con pruebas de cruces y selección para plata. Se incorporaron las cinco capas nuevas que llegaron durante la revisión. Salidas IPYNB/HTML, perfiles y figuras guardados en carpetas privadas; fuentes y README sin salidas oficiales para reproducción. Se verificó la aclaración del dueño: NPISOS=0 corresponde a lote sin edificación registrada (1.234), 1.228 de ellos con EDIFPRED nulo o en blanco; los 11 pisos NULL se tratan aparte. Se midieron cobertura territorial, ambigüedad de GEM, urgencias declaradas y solape entre los catálogos USGS. Selección y puertas de calidad en `docs/EDA_BRONCE.md` y notebook 99.
**Por qué:** Decidir qué enriquecer en plata desde calidad y cobertura reales. El cruce GEM a ≤15 m tiene 1.667 empates y no acredita identidad predial; salud no acredita capacidad operativa; ambos catálogos USGS comparten 68 eventos y no se suman. El EDA no convierte modelos en daño observado ni lotes en edificios. La lógica heredada de imputación de ceros queda señalada como cambio necesario antes de usar la siguiente plata; no se modificaron los pesos del índice.
**Archivos:** `analisis_bronce/notebooks/`, `analisis_bronce/soporte.py`, `analisis_bronce/ejecutar.py`, `analisis_bronce/verificar.py`, `analisis_bronce/test_analisis.py`, `analisis_bronce/README.md`, `analisis_bronce/ejecutados/` y `analisis_bronce/resultados/` (privados), `.gitignore`, `README.md`, `docs/EDA_BRONCE.md`, `docs/FUENTES.md`, `docs/BITACORA.md`. Verificación final: 18 notebooks, 97 celdas, 20 figuras y cero errores; 17 huellas de fuente conservadas; dos regresiones aprobadas. Evidencia en `docs/EDA_BRONCE.md`.

### 2026-11-13 11:29 · Mrsasayo
**Qué:** Corrección de fidelidad geométrica de la serialización WKT de bronce/silver/Spark. El original tiene 4 geometrías inválidas; el redondeo predeterminado introducía 13 más, elevando el reporte a 17. Se usa `rounding_precision=-1` y se comprueba igualdad exacta de las 5.146 geometrías. Una regresión sintética reproduce el defecto y comprueba el arreglo; el notebook 01 conserva la comparación con salidas visibles. También se corrigió el acceso a la columna `level` en el notebook de amplificación, que colisionaba con una propiedad interna de pandas.
**Por qué:** Bronce debe conservar la fuente. Reparar geometrías que se dañaron durante la carga escondía el origen del problema y explicaba la discrepancia de conteos entre sesiones.
**Archivos:** `notebooks/00_pipeline.py`, `analisis_bronce/notebooks/01_predios_oficiales.ipynb`, `analisis_bronce/notebooks/11_gem_amplificacion.ipynb`, `analisis_bronce/test_analisis.py`, `docs/EDA_BRONCE.md`, `docs/BITACORA.md`

## Decisiones

| Fecha/hora | Decisión | Razón | Alternativas descartadas | Responsable |
|---|---|---|---|---|
| 2026-11-12 23:45 | Comunas, barrios, servicios y vías desde OpenStreetMap | datos.cali.gov.co e IDESC fuera de línea; OSM cubre las 22 comunas (122 km², coincide con el casco urbano) | Datos abiertos de Cali (caído), IDESC WFS (404) | José David |
| 2026-11-12 23:45 | Profundidad del sismo: 116 km (USGS) | Es la del catálogo descargado y usado en el mapa | SGC 96 km, OPS 103 km (se citan como discrepancia) | José David |
| 2026-11-12 23:55 | Distancias en EPSG:9377 (MAGNA-SIRGAS Origen Nacional) | CRS oficial de Colombia en metros; evita errores de calcular distancias en grados | EPSG:3857 (deforma distancias), MAGNA Cali local (no lo usan las capas OSM) | José David |
| 2026-11-13 00:10 | Índice borrador: daño 35 %, altura 20 %, exposición 15 %, salud 15 %, bloqueo de vía 15 % | El daño es lo único observado; los demás miden cuánto empeora el impacto. Detalle en `INDICE_RIESGO.md` | Pesos iguales y otros 3 escenarios, que quedan como prueba de sensibilidad | José David |
| 2026-11-13 00:10 | Edificios sin dato satelital no se borran ni se imputan: categoría propia "verificar en terreno" | Borrarlos esconde zonas sin información; imputarlos como sanos es peligroso | Eliminar filas, imputar con la media | José David |
| 2026-11-13 00:10 | Pisos inválidos (fuera de 1 a 60) se anulan e imputan con la mediana de la comuna | No perder el edificio por un error de captura de un campo | Eliminar la fila | José David |
| 2026-11-13 00:10 | Ranking de comunas por percentil 90 del índice | El promedio esconde grupos críticos dentro de comunas mayormente sanas | Promedio, conteo absoluto | José David |
| 2026-11-13 00:10 | Población aproximada por densidad de edificios a 100 m | Sin datos de población por manzana disponibles a tiempo | Población DANE por manzana (por verificar) | José David |
| 2026-11-13 00:25 | Visor propio con MapLibre + deck.gl, Kepler.gl como plan B | Diferenciación y narrativa guiada; el plan B evita que la demo dependa del visor | Solo Kepler.gl, QGIS | José David |
| 2026-11-13 09:50 | Suelo desde la grilla de GEM TREQ (punto más cercano, ~750 m) | Es la microzonificación oficial de 2005 en formato abierto; la capa vectorial de la IDESC sigue caída | Vs30 global del USGS (más grueso y sin microzonas), mapa PDF de la Alcaldía (habría que digitalizarlo), dejar el suelo fuera | José David |
| 2026-11-13 09:50 | Amplificación en el período propio del edificio (T ≈ pisos/10 s), leída para 0,23 g en roca | Captura la resonancia: el mismo suelo castiga distinto a una casa y a un edificio de 20 pisos. 0,23 g es un nivel fuerte pero no extremo del modelo | Un solo factor por microzona (ignora la resonancia), Vs30 de la grilla (vale 800 dentro de las microzonas porque allí manda la función de amplificación), PGA (en suelo blando desamplifica) | José David |
| 2026-11-13 09:50 | Pesos: daño 30 %, suelo 15 %, altura 15 %, exposición 15 %, salud 10 %, vías 15 % (confirmar al mediodía) | El daño sigue mandando; el suelo entra al nivel de los demás factores de contexto; la salud baja porque OSM la mide de forma optimista | Mantener el borrador sin suelo (queda como escenario `sin_suelo`), suelo al 20 % | José David |
| 2026-11-13 10:30 | Severidad por categoría: escombros 1,0; techo desaparecido 0,7; sin cambio aparente 0,1 | `Indice_Escombros` tiene daño en las dos colas, así que no sirve como probabilidad. "Sin cambio aparente" no significa "sin daño" (la guía), por eso 0,1 y no 0 | Usar `Indice_Escombros` normalizado (trata el techo desaparecido como sano), severidad 0 para sin cambio | José David |
| 2026-11-13 10:30 | NPISOS = 0 (1.234) se imputa con la mediana de la comuna, se marca y se excluye del análisis por altura | El 0 aparece en proporción pareja en las 4 categorías: parece falta de captura, no un lote vacío. Borrarlos perdería el 24 % de los edificios | Borrar las filas; dejar 0 (anula su altura en el índice); imputar por área | José David |
| 2026-11-13 10:30 | Polígonos inválidos (17) se reparan con make_valid, no se borran | Son edificios reales con errores de digitalización | Eliminarlos | José David |
| 2026-11-13 10:30 | Llave: `OBJECTID` | Es único; `ID_PREDIO` es nulo en 1.509 filas (la guía) | `ID_PREDIO` | José David |
| 2026-11-13 10:30 | Bronze todo como texto con nulos reales y esquema explícito | Copia fiel: los vacíos y los espacios se conservan para decidir en silver. El esquema explícito evita el error de Spark con columnas 100 % nulas (`OBJECTID_1`) | `astype(str)` (convierte nulos en "nan"), inferir tipos | José David |
| 2026-11-13 10:30 | Área sin dato: se reporta el 9,5 % medido y no el ~45 % de la guía | Medido en m² (EPSG:9377) y con `Shape__Area` da lo mismo | Citar el 45 % de la guía | José David |
| 2026-11-13 10:55 | Modelo de exposición de GEM como fuente de vulnerabilidad y población, cruzado por edificio (dentro del polígono o a ≤ 15 m) | Única base pública por edificio con año, tipología y ocupantes. El 95 % de los edificios tiene un punto GEM a menos de 9 m, por eso 15 m es un tope seguro | Población DANE por manzana (sin tipología y no verificada a tiempo), WorldPop o Kontur (grillas que no distinguen edificios), densidad de edificios (proxy anterior) | José David |
| 2026-11-13 10:55 | Vulnerabilidad = probabilidad de ductilidad baja o nula (DUL + DNO) según los pesos de expertos de GEM (esquema MEAN) | Una sola cifra de 0 a 1, explicable, que resume material, sistema y cumplimiento del código | Solo mampostería no reforzada (deja fuera concreto no dúctil), período de construcción (no considera la tipología), uno de los otros esquemas de expertos | José David |
| 2026-11-13 10:55 | Pisos faltantes (`NPISOS` = 0 o nulo) se toman de GEM antes que de la mediana de la comuna (1.221 de 1.245) | Es un dato del catastro de ese edificio, no un promedio | Mantener la mediana (decisión anterior) | José David |
| 2026-11-13 10:55 | Pesos: daño 25, vulnerabilidad 20, ocupantes 15, suelo 10, altura 10, salud 10, vías 10 | El daño sigue siendo lo único observado, pero no sigue ningún patrón; la vulnerabilidad es el factor más sólido de la literatura; el suelo baja porque no explica el daño en esta muestra | Borrador de la mañana (escenario `sin_suelo`), solo datos oficiales (escenario de sensibilidad) | José David |
| 2026-11-13 10:55 | ShakeMap fuera del índice | Describe el sismo que ya pasó, varía poco en la zona (MMI 6,4 a 7,1) y no se asocia con el daño | Usarlo como componente de sacudida | José David |
| 2026-11-13 10:55 | Licuación local de GEM en vez del modelo de licuación del USGS | Es local y por unidad geológica; el del USGS es un ráster global de ~1 km y requiere una dependencia nueva (`rasterio`) | USGS *ground-failure* (Zhu 2017) | José David |
| 2026-11-13 11:29 | NPISOS=0 es lote sin edificación registrada; se conserva y se excluye de promedios de altura y del ranking de inspección de edificios. Los 11 NULL son desconocidos | Aclaración explícita del dueño; 1.228 de los 1.234 ceros tienen EDIFPRED nulo/blanco (99,51 %). Sustituye para la siguiente plata las decisiones anteriores que imputaban ceros | Tratar cero como error; imputar pisos de lote con GEM o mediana; borrar lote del inventario | Mrsasayo |
| 2026-11-13 11:29 | Conservar geometría WKT a precisión completa en bronce/silver/Spark | El redondeo creaba 13 geometrías inválidas adicionales; sin redondeo hay igualdad exacta en las 5.146 filas | Reparar como si los 17 defectos fueran de la fuente; redondear durante la carga | Mrsasayo |
| 2026-11-13 11:29 | Seleccionar predios oficiales, OSM de servicios/vías y ShakeMap/sitio GEM para la siguiente plata; exposición GEM por predio queda condicionada a resolver correspondencia | Son fuentes materializadas relevantes para afectación, acceso y sacudida. El extracto de exposición tiene coordenadas redondeadas y 1.667 empates entre vecinos más cercanos a ≤15 m | Aceptar automáticamente el primer vecino; imputar pisos a lotes; incorporar referencias sin datos disponibles | Mrsasayo |
| 2026-11-13 11:29 | Salud distingue urgencias sí/no/sin dato; bomberos y policía separados; educación no equivale a albergue | Solo 23 de 439 sitios declaran urgencias; capacidad y operatividad no están acreditadas; hay 11 bomberos y 52 policías | Tratar 439 puntos como hospitales operativos; sumar servicios distintos como brigadas; habilitar colegios como albergues sin evidencia | Mrsasayo |
| 2026-11-13 11:29 | Consolidar los catálogos USGS por ID y separar observaciones instrumentales de macroseísmicas | Los 68 eventos del extracto actualizado ya están en el de 76; stationlist tiene 1 instrumento y 32 observaciones macroseísmicas | Sumar archivos como eventos independientes; llamar réplicas a todo evento posterior; llamar validación independiente a reproducir insumos de ShakeMap | Mrsasayo |
