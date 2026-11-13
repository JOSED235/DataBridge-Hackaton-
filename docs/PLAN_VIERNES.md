# Plan del viernes 13: estrategia, pendientes y paso a paso

> Este es el archivo a abrir mañana. Todo lo que se pudo adelantar ya está en el repo; el viernes se conectan los datos reales. Buscar `TODO-VIERNES` en el repo para ver cada punto que depende de ellos.

## 0. Actualización 13-nov 10:30: guía oficial y datos reales

Guía completa en `DataBridge_Hack_Guia_Evento_2.md` (raíz). Lo que cambia el plan:

**Entrega (lo único que cuenta).** Hay que enviar un correo a marcelasabogue@ieee.org **antes de las 5:00 p. m.** con el asunto `databridgehack: grupoX`. Debe traer:

1. Una captura del Catalog con las tablas bronze, silver y gold.
2. Un texto de decisiones en silver y gold (≤ 200 palabras).
3. La respuesta a las dos preguntas (≤ 500 palabras).
4. La lista de fuentes.
5. **3 diapositivas:** arquitectura, respuesta y pantallazo del mapa.

El sábado se sustentan **5 min solo con eso: no hay demo en vivo del visor.** El visor sirve para sacar el pantallazo. El recorrido guiado y el video ya no son prioridad.

**Puntaje:**

| Criterio | Puntos | Qué mira el jurado |
|---|---|---|
| Respuesta a la pregunta | 30 | Las dos mitades, conectadas y visibles en el mapa |
| Datos externos | 25 | Citados, cruzados con los edificios y que aporten valor. Un dato que solo decora no suma; uno falso o una conclusión sin sustento **resta** |
| Calidad del análisis | 20 | Cifras rastreables a las tablas gold y límites reconocidos |
| Presentación | 15 | Mapa claro en 30 s, 3 diapositivas |
| Arquitectura | 10 | Decisiones de cada capa justificadas |

**Nombres.** Todo va en `workspace.default`, con volumen y tablas `<capa>_icesixuao_<contenido>`. Ya está en `00_pipeline` (`EQUIPO`).

**Lo que dicen los datos reales** (corrida local con `scripts/correr_local.py`):

- **Cobertura:** 5.146 edificios, solo de 7 comunas (3, 9, 10, 17, 18, 19 y 20); la comuna 19 tiene el 61 %. No hay edificios del oriente blando (microzona 6), así que el argumento "oriente de Cali" del informe no aplica a esta muestra.
- **Daño:** 296 con alta probabilidad de escombros (5,8 %), 1.058 con posible desaparición de techo (20,6 %), 3.357 sin cambio aparente (65,2 %) y 435 sin dato (8,5 %).
- **Altura:** son edificios bajos (mediana de 2 pisos y máximo 13), así que no hay ninguno en la banda de resonancia de 15 a 25 pisos.
- **Suelo:** **la hipótesis del efecto de sitio no se cumple en esta muestra.** El % de escombros va de 5,4 % a 8,9 % entre microzonas, sin relación con la amplificación, y tampoco cambia con la altura. Se dice así en la entrega; afirmar lo contrario resta puntos. El suelo sigue en el índice porque mide la sacudida *futura* de una réplica, no explica el daño observado. Al mediodía hay que decidir si baja al 10 %.
- **Área sin dato:** la guía dice que los 435 edificios sin dato suman "cerca del 45 %" del área construida. Nosotros medimos **9,5 %**, tanto en m² (EPSG:9377) como con `Shape__Area`. Anotarlo como discrepancia y no usar el 45 %.
- **NPISOS:** vale 0 en 1.234 edificios, en proporción pareja entre las 4 categorías (21 % a 29 %). Se imputan con la mediana de la comuna, se marcan con `pisos_imputado` y se excluyen del análisis por altura.
- **Ranking de comunas por índice p90:** 3, 20, 18, 9, 10, 19 y 17.

## 1. Estrategia

### Idea central (la frase que debe quedar en el jurado)

**"No podemos evitar la próxima réplica, pero sí decidir dónde llegar primero."** Todo el trabajo responde a eso: un ranking explicable de edificios y comunas para inspeccionar, y las acciones que reducen el impacto.

### Cómo respondemos cada parte de la pregunta

La pregunta tiene dos mitades y tres dimensiones. Cada celda tiene un entregable concreto:

| | (a) Afectaciones: qué pasó | (b) Factores que reducen el impacto de réplicas |
|---|---|---|
| **Infraestructura** | Edificios con alta prob. de escombros y su estado, por comuna (`gold_comunas`, mapa de calor) | Suelo, altura y densidad como factores: daño por microzona dentro de cada rango de pisos y edificios de 15 a 25 pisos sobre suelo que amplifica su período (SQL en `03_gold`). Si los datos traen material, año o uso, se agregan a ese análisis |
| **Población** | Edificios dañados en zonas densas (`n_edif_100m`), % sin dato satelital por comuna | Inspeccionar primero los de prioridad muy alta en zonas densas; verificar en terreno los edificios sin dato |
| **Servicios urbanos** | Edificios que podrían bloquear vías principales; carga sobre salud (edificios dañados por centro de salud) | Despejar y vigilar esas vías; reforzar salud y albergues (colegios de OSM) donde hay más daño y menos cobertura |

La mitad (b) es donde la mayoría de equipos se va a quedar corta. Ahí está nuestra ventaja: el índice, el bloqueo de vías y la carga sobre salud son "factores que reducen el impacto" medibles, no solo opiniones.

### Qué cambió con el informe de investigación (13-nov, `docs/INFORME_SISMO.md`)

La estrategia se mantiene: el informe llega a la misma propuesta (bronze/silver/gold, índice por comuna, priorizar inspección). Cambian cuatro cosas:

1. **El suelo entra al índice como `c_suelo` (15 %).** La capa oficial sigue caída, pero GEM TREQ publica la microzonificación de 2005 como grilla con funciones de amplificación. Cada edificio toma la amplificación de su microzona en su propio período (T ≈ pisos/10 s), así que el índice captura la resonancia. Los nuevos pesos son daño 30 %, suelo 15 %, altura 15 %, exposición 15 %, salud 10 % y vías 15 %; se confirman al mediodía.
2. **Hay una hipótesis que probar con datos:** si el daño sube con la amplificación del suelo **dentro del mismo rango de pisos**, el efecto de sitio queda demostrado dentro de Cali. Es el hallazgo más fuerte posible para la mitad (b), y el SQL ya está en `03_gold`. Si no se cumple, se dice así: el peso recae en la tipología constructiva.
3. **La narrativa del "por qué pasó" se apoya en el contraste con Venezuela 2026:** con magnitud casi igual, Venezuela tuvo un sismo 11,6 veces más somero y 36,7 veces más mortalidad por habitante. Bucharest 1977 es el paralelo de Cali: un sismo intermedio y lejano que hizo daño por resonancia sobre sedimentos. Basta con una diapositiva; no hay que convertir la charla en una clase de sismología.
4. **Las recomendaciones ganan sustento:** los edificios dañados son la principal víctima de las réplicas (el doblete de 39 s), hay que proteger primero hospitales (el HUV tuvo colapso parcial) y el siguiente paso de política es reforzar lo existente, no hacer otra norma (Japón y Chile).

Lo que **no** cambia: no se buscan más fuentes hoy. Corrupción constructiva, año frente al código e Índice de Percepción de la Corrupción solo entran si los datos oficiales traen año o tipología.

### Qué nos diferencia

1. **Índice propio, explicable en 30 s y con prueba de sensibilidad** (`docs/INDICE_RIESGO.md`), que incluye la amplificación del suelo en el período de cada edificio.
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
3. **Catalog → workspace → databridge → externos → Upload to this volume:** subir los 9 archivos de `data/externos/` (7 `.geojson` y 2 `.csv` de suelo).
4. Cargar los edificios según el paso a paso oficial. Poner la tabla o archivo en `TABLA_ORIGEN` o `ARCHIVO_ORIGEN` de `01_bronze` y correrlo completo.
5. Con la "Primera revisión" de `01_bronze`, anotar en la bitácora: columnas reales, % de nulos, valores de `Estado_Estructural`, si hay coordenadas o polígonos y en qué CRS.
6. Guardar una copia local de los datos en `data/oficial/` (está en `.gitignore`: **nunca se sube**).

### Mañana: silver

1. En `00_pipeline` ajustar `COLS`, `SEVERIDAD_ESTADO`, `ESCOMBROS_CATEGORIA` y la regla de `sin_dato_satelital` a los datos reales.
2. Correr `02_silver`. Revisar el `reporte` de limpieza y `valores_estado_sin_mapear` (debe quedar vacío). Copiar el reporte a la bitácora.
3. Si las coordenadas vienen en otro CRS (no lon/lat), convertir a EPSG:4326 en `a_geo()` y anotarlo.
4. En paralelo, quien lleva el visor explora en Kepler.gl o con el visor de muestra.

### Mediodía: decidir

- Mirar los 5 SQL de `03_gold` (sobre todo el de daño por microzona dentro de cada rango de pisos) y la distribución del índice.
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
