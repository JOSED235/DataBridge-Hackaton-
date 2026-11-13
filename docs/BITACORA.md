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
