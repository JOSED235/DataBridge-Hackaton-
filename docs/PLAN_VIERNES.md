# Plan del viernes 13: estrategia, pendientes y paso a paso

> Este es el archivo a abrir mañana. Todo lo que se pudo adelantar ya está en el repo; el viernes se conectan los datos reales. Buscar `TODO-VIERNES` en el repo para ver cada punto que depende de ellos.

## 1. Estrategia

### Idea central (la frase que debe quedar en el jurado)

**"No podemos evitar la próxima réplica, pero sí decidir dónde llegar primero."** Todo el trabajo responde a eso: un ranking explicable de edificios y comunas para inspeccionar, y las acciones que reducen el impacto.

### Cómo respondemos cada parte de la pregunta

La pregunta tiene dos mitades y tres dimensiones. Cada celda tiene un entregable concreto:

| | (a) Afectaciones: qué pasó | (b) Factores que reducen el impacto de réplicas |
|---|---|---|
| **Infraestructura** | Edificios con alta prob. de escombros y su estado, por comuna (`gold_comunas`, mapa de calor) | Altura y densidad como factores: tasa de alta prob. de escombros por rango de pisos (SQL en `03_gold`). Si los datos traen material, año o uso, se agregan a ese análisis |
| **Población** | Edificios dañados en zonas densas (`n_edif_100m`), % sin dato satelital por comuna | Inspeccionar primero los de prioridad muy alta en zonas densas; verificar en terreno los edificios sin dato |
| **Servicios urbanos** | Edificios que podrían bloquear vías principales; carga sobre salud (edificios dañados por centro de salud) | Despejar y vigilar esas vías; reforzar salud y albergues (colegios de OSM) donde hay más daño y menos cobertura |

La mitad (b) es donde la mayoría de equipos se va a quedar corta. Ahí está nuestra ventaja: el índice, el bloqueo de vías y la carga sobre salud son "factores que reducen el impacto" medibles, no solo opiniones.

### Qué nos diferencia

1. **Índice propio, explicable en 30 s y con prueba de sensibilidad** (`docs/INDICE_RIESGO.md`).
2. **Servicios urbanos medidos de verdad:** bloqueo de vías y acceso a salud con OSM.
3. **Honestidad visible:** aviso de datos satelitales, edificios sin dato tratados aparte, discrepancias de fuentes documentadas.
4. **Visor propio con recorrido guiado**, no un mapa suelto.
5. **Hallazgo de contexto:** el portal de datos abiertos de Cali y la IDESC están caídos desde el 21-oct-2026; la solución se armó con fuentes abiertas alternativas.
6. **Bitácora de decisiones:** cada "¿por qué?" del jurado tiene respuesta escrita.

### Reglas para decidir rápido durante el día

- **Primero completo, después bonito.** A las 2:00 p. m. el pipeline debe estar de punta a punta con datos reales, aunque el índice sea el borrador.
- Si los datos traen algo inesperado (otras columnas, polígonos, otro CRS), adaptar `00_pipeline` y anotar la decisión; no rehacer la arquitectura.
- Si un dato nuevo es valioso (material, año de construcción, uso, estrato), agregarlo como factor en el análisis de la mitad (b) antes que tocar el índice.
- No perseguir fuentes nuevas el viernes: las externas ya están descargadas.

### Reparto (dos personas)

| Persona | Mañana | Tarde |
|---|---|---|
| Datos (Python/SQL) | Bronze y silver con datos reales, ajustar `COLS`, reporte de limpieza | Gold, sensibilidad, SQL de hallazgos, Genie, formulario de entrega |
| Visor y presentación (JS) | Explorar datos en el visor de muestra o Kepler.gl, preparar diapositiva de contexto | Conectar GeoJSON reales, textos del recorrido, guion con cifras, video de respaldo |

Ambos: revisar juntos el índice al mediodía y ensayar al final. Cada uno anota sus aportes en `BITACORA.md`.

## 2. Pendientes

### Hoy, antes del evento (si alcanza el tiempo)

- [ ] **Probar en Databricks Free Edition** importar `notebooks/` y correr `%pip install geopandas` + `%run ./00_utils_espacial` (debe imprimir `autoprueba OK`). Es el riesgo técnico más grande que no se pudo probar en local. Seguir `docs/GUIA_DATABRICKS.md` pasos 1 a 3.
- [ ] Hacer commit y push del repo para que el compañero lo clone.
- [ ] Cada integrante: cuenta de Databricks activa, portátil y cargador.
- [ ] Abrir el visor local una vez en cada portátil.

### Cuando lleguen los datos

- [ ] Anotar columnas reales, formato, CRS y valores de `Estado_Estructural` en la bitácora.
- [ ] Ajustar `COLS`, `SEVERIDAD_ESTADO`, `ESCOMBROS_CATEGORIA` y la regla de `sin_dato_satelital` en `00_pipeline`.
- [ ] Correr 01, 02 y 03; revisar reporte de limpieza y sensibilidad.
- [ ] Confirmar o ajustar pesos del índice (decisión en la bitácora).
- [ ] Exportar GeoJSON al visor y borrar `visor/data/MUESTRA.txt`.
- [ ] Llenar cifras en `PASOS` de `visor/app.js`, en `GUION_PRESENTACION.md` y en la sección de sensibilidad de `INDICE_RIESGO.md`.
- [ ] Validación: contrastar el top de comunas y edificios con lo reportado en prensa y OPS (`FUENTES.md`).
- [ ] Espacio de Genie sobre las tablas gold.
- [ ] Formulario de entrega enviado con margen.
- [ ] Video y capturas de respaldo; ensayo con cronómetro.

### Sábado

- [ ] Llegar temprano, probar proyección, visor sin internet y plan B (Kepler.gl).

## 3. Paso a paso

### Antes de salir (o al llegar)

1. Clonar el repo en cada portátil.
2. Tener a mano la cuenta de Databricks Free Edition abierta.
3. Abrir el visor local una vez para confirmar que carga (ver `README.md`).

### Apertura

- Anotar en `BITACORA.md`: criterios del jurado, detalles del formulario de entrega y del paso a paso de carga.

### Primera hora: bronze

1. En Databricks: **Workspace → Import** y subir los 5 archivos de `notebooks/` (se importan como notebooks).
2. Correr la primera celda de `01_bronze` (crea esquema `workspace.databridge` y los volúmenes).
3. **Catalog → workspace → databridge → externos → Upload to this volume:** subir los 7 `.geojson` de `data/externos/`.
4. Cargar los edificios según el paso a paso oficial. Poner la tabla o archivo en `TABLA_ORIGEN` o `ARCHIVO_ORIGEN` de `01_bronze` y correrlo completo.
5. Con la "Primera revisión" de `01_bronze`, anotar en la bitácora: columnas reales, % de nulos, valores de `Estado_Estructural`, si hay coordenadas o polígonos y en qué CRS.
6. Guardar una copia local de los datos en `data/oficial/` (está en `.gitignore`: **nunca se sube**).

### Mañana: silver

1. En `00_pipeline` ajustar `COLS`, `SEVERIDAD_ESTADO`, `ESCOMBROS_CATEGORIA` y la regla de `sin_dato_satelital` a los datos reales.
2. Correr `02_silver`. Revisar el `reporte` de limpieza y `valores_estado_sin_mapear` (debe quedar vacío). Copiar el reporte a la bitácora.
3. Si las coordenadas vienen en otro CRS (no lon/lat), convertir a EPSG:4326 en `a_geo()` y anotarlo.
4. En paralelo, quien lleva el visor explora en Kepler.gl o con el visor de muestra.

### Mediodía: decidir

- Mirar los 3 SQL de `03_gold` y la distribución del índice.
- Decidir pesos finales (o confirmar los del borrador) y anotarlos con su razón en la tabla de decisiones.
- Elegir los 3 hallazgos principales para el guion.

### Tarde: gold y visor

1. Correr `03_gold`. Revisar `gold_sensibilidad` y anotar el resultado.
2. Descargar de **Catalog → databridge → salidas** `edificios.geojson` y `comunas.geojson`, copiarlos a `visor/data/` y **borrar `visor/data/MUESTRA.txt`**.
3. Probar el visor y el recorrido guiado; actualizar los textos de `PASOS` en `visor/app.js` con las cifras reales.
4. Crear un espacio de Genie sobre `gold_edificios` y `gold_comunas` para responder preguntas en vivo.

### Final de la tarde

1. Llenar los `[corchetes]` de `GUION_PRESENTACION.md`.
2. Enviar el **formulario de entrega** con margen, sin esperar a la última hora.
3. Grabar un video corto del recorrido guiado y sacar capturas: respaldo si falla la proyección o internet.
4. Ensayar la presentación al menos una vez con cronómetro.

## 4. Plan B

- Visor propio falla: abrir `visor/data/edificios.geojson` en [Kepler.gl](https://kepler.gl/demo) (arrastrar el archivo).
- Se agota la cuota de Databricks: correr `scripts/simular_pipeline.py` en local con los datos reales de `data/oficial/` (cambiar la generación ficticia por la lectura del archivo).
- `%pip install geopandas` falla en Databricks: hacer los cruces espaciales en local con el mismo código y subir el resultado como tabla.
