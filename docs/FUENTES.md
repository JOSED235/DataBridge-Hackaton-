# Fuentes externas

> EDA local del 13-nov-2026: `docs/EDA_BRONCE.md` y `analisis_bronce/notebooks/`
> perfilan los 17 datasets/contenedores ya materializados, incluidas las cinco
> nuevas capas externas. Las decisiones para plata y sus restricciones están en
> el notebook `99_seleccion_para_plata` y en la bitácora. Los estados históricos
> de disponibilidad de las revisiones anteriores se conservan con su alcance.

> **Regla:** antes de usar o citar una fuente, verificar que existe y dice lo que se afirma. Las cifras oficiales del sismo son preliminares; si dos fuentes no coinciden, se anota la discrepancia y cuál se eligió.
>
> **Criterio del jurado (guía oficial):** cada dato externo debe ser **verdadero** (fuente identificable y citada), **tener sentido** (cubre Cali, es reciente y se cruza con los edificios) y **aportar valor** (cambia o enriquece la respuesta). Un dato que solo decora no suma; uno falso o una conclusión sin sustento resta. Cada ficha de abajo responde esas tres pruebas.

> **Dos partes:** las fichas 1 a 8 son las fuentes **usadas** en el pipeline y la entrega. La sección [Revisión de las fuentes del informe](#revisión-de-las-fuentes-del-informe-13-nov-2026) revisa las 20 entradas del catálogo y las 38 referencias de `INFORME_SISMO.md`: datos inspeccionados, recursos localizados y verificaciones pendientes.

Todas las descargas son reproducibles con dos scripts: `scripts/descargar_osm.py` (OpenStreetMap) y `scripts/descargar_externos.py` (USGS y GEM). Los archivos quedan recortados a Cali en `data/externos/`. Los cruces con los edificios están en `cruzar_externos()`, `asignar_suelo()` y `enriquecer()` de `notebooks/00_pipeline.py`. Todas las cifras de este documento salen de `scripts/correr_local.py` sobre los 5.146 edificios oficiales.

## Resumen

| # | Fuente | Qué responde | Cómo se cruza con cada edificio | Cobertura del cruce | Dónde se usa |
|---|---|---|---|---|---|
| 1 | GEM TREQ: modelo de exposición de Cali | ¿Quién vive ahí y qué tan vulnerable es la construcción? | Edificio GEM dentro del polígono o a ≤ 15 m | 98,9 % | `c_vulnerabilidad`, `c_exposicion`, pisos faltantes, análisis de factores, población afectada |
| 2 | GEM TREQ: microzonificación y funciones de amplificación | ¿Cuánto amplifica el suelo la próxima sacudida? | Punto de grilla más cercano + período propio del edificio | 100 % | `c_suelo` |
| 3 | GEM TREQ: licuación y pendiente | ¿Puede fallar el terreno bajo el edificio? | Sitio más cercano | 100 % | `c_suelo`, análisis de factores |
| 4 | USGS ShakeMap v11 (evento us6000tjl2) | ¿Con qué intensidad se sacudió cada edificio? | Nodo más cercano (~1 km) | 100 % | Análisis de factores, contexto |
| 5 | SGC (acelerógrafo RAC2C) y USGS DYFI | ¿El ShakeMap es creíble en Cali? | Comparación estación/celda contra nodo | 1 estación, 32 celdas | Validación |
| 6 | USGS: catálogo de réplicas | ¿Siguen ocurriendo réplicas? | Contexto regional (no por edificio) | — | Contexto y mapa |
| 7 | OpenStreetMap | ¿Qué servicios urbanos quedan expuestos? | Distancia, unión espacial, conteo en radio | 100 % | `c_acceso_salud`, `c_bloqueo_via`, comuna y barrio |
| 8 | Informes oficiales y prensa | Cifras de impacto para el contexto | No se cruzan | — | Diapositiva de contexto |

---

## 1. GEM TREQ: modelo de exposición de Cali (edificio por edificio)

| | |
|---|---|
| **Qué es** | Inventario de los 348.483 edificios de Cali con su tipología constructiva, construido para la evaluación de riesgo sísmico de la ciudad. Por edificio: período de construcción, estrato, uso, pisos, ocupantes nocturnos, área, valor de reposición y clase de taxonomía GEM. |
| **Quién lo produce** | Fundación GEM (Global Earthquake Model), proyecto TREQ, con la Alcaldía de Cali. Base: geodatabase de la Alcaldía (Etapas I y II), catastro al 30-abr-2021, censo DANE 2018 y 25.641 encuestas a edificaciones. Metodología: Yepes-Estrada et al. (2022). |
| **Enlace** | [github.com/gem/treq-riesgo-urbano/tree/master/Cali/Exposicion](https://github.com/gem/treq-riesgo-urbano/tree/master/Cali/Exposicion): `Exposure_Cali_Colombia.csv` y `taxonomy_mapping_MEAN.csv` |
| **Licencia** | CC BY-SA 4.0: citar "GEM Foundation, proyecto TREQ". |
| **Cómo se obtuvo** | `scripts/descargar_externos.py`, 13-nov-2026. Se descargó el archivo completo (47,6 MB) y se recortó a las 7 comunas de los datos oficiales (3, 9, 10, 17, 18, 19, 20): 95.010 edificios, 8 MB, en `data/externos/gem_exposicion.csv`. |
| **Cómo se calculó la vulnerabilidad** | GEM no asigna una sola tipología a cada edificio: cada clase (uso / período / pisos / estrato) se reparte entre varias tipologías con pesos que suman 1, según el criterio de expertos (esquema `MEAN`). Se sumaron los pesos de las tipologías con **ductilidad baja o nula** (`DUL`, `DNO`) → `p_ductilidad_baja`. Igual con mampostería no reforzada y adobe (`MUR`) → `p_mamposteria_no_reforzada`. La ductilidad es la capacidad de deformarse sin colapsar; GEM la asocia con el cumplimiento del código y la formalidad de la construcción. |
| **Cómo se cruzó** | `sjoin_nearest` en EPSG:9377 con un máximo de 15 m: si el punto GEM cae dentro del polígono oficial la distancia es 0. Resultado: 98,9 % de los edificios cruzados; en 3.084 (60 %) el punto GEM está dentro del polígono; mediana 0 m; el 95 % a menos de 9 m. |
| **Por qué esta fuente** | Es la única base pública de Cali **por edificio** con año, ocupantes y tipología. Las alternativas eran más gruesas: población DANE por manzana (geoportal por verificar y sin tipología), densidad de edificios como proxy (lo que usábamos) o grillas globales de población (WorldPop, Kontur), que no distinguen un edificio de otro. |
| **Qué aportó** | (1) **Población afectada** (dimensión población): 30.234 ocupantes en los edificios analizados, **6.907 en edificios con daño visible** (escombros o techo), 1.404 en edificios con escombros y 2.646 en edificios sin dato satelital. (2) **Vulnerabilidad**: el 35,8 % se construyó antes de 1985, es decir, antes del primer código sísmico (Decreto-Ley 1400 de 1984); la probabilidad media de ductilidad baja es 0,82. (3) **Pisos faltantes**: de los 1.245 edificios con `NPISOS` = 0 o nulo, 1.221 se completaron con los pisos de GEM en lugar de la mediana de la comuna. (4) **Servicios**: 86 edificios institucionales con daño visible. |
| **Validación** | Donde ambos tienen pisos, `NPISOS` y GEM coinciden exactamente en el 54 % (correlación 0,55). GEM agrupa 6 a 10 pisos en una sola categoría y su catastro es de 2021. |
| **Limitaciones** | Es un modelo: la tipología es probabilística, no observada en cada edificio. Fecha de corte del catastro: abril de 2021. Los ocupantes son nocturnos (el sismo fue a las 7:34 a. m., cuando mucha gente seguía en casa). |
| **Tablas** | `silver_icesixuao_predios` (columnas `periodo_construccion`, `estrato`, `uso`, `ocupantes_noche`, `p_ductilidad_baja`, `pisos_fuente`, ...), `gold_icesixuao_predios`, `gold_icesixuao_comunas` (`ocupantes_en_edif_con_danio`, `pct_antes_1985`), `gold_icesixuao_factores`. |

## 2. GEM TREQ: microzonificación sísmica y funciones de amplificación

| | |
|---|---|
| **Qué es** | Microzonificación sísmica oficial de Cali (INGEOMINAS y DAGMA, 2005), con 10 zonas de respuesta, publicada por GEM como una grilla de 792 puntos (~750 m). Incluye la función de amplificación del suelo de cada microzona por período espectral (0,1 a 2,0 s) y nivel de sacudida en roca. |
| **Enlace** | [github.com/gem/treq-riesgo-urbano/tree/master/Cali/Condiciones_Sitio](https://github.com/gem/treq-riesgo-urbano/tree/master/Cali/Condiciones_Sitio): `site_model_uniform_grid_ampcodes.csv` y `soil_amplification_model_20210825_sigaf03.csv`, guardados como `gem_microzonas_grilla.csv` y `gem_amplificacion_suelo.csv`. |
| **Licencia** | CC BY-SA 4.0. |
| **Por qué esta fuente** | La capa oficial vivía en la IDESC, caída desde el 21-oct-2026 (ver "No disponibles"). GEM publica la misma microzonificación en formato abierto. Se descartó el Vs30 global del USGS (más grueso y sin microzonas) y el Vs30 de la propia grilla: dentro de las microzonas vale 800 m/s (roca de referencia), porque allí manda la función de amplificación. |
| **Cómo se cruzó** | Microzona del punto de grilla más cercano. Período propio del edificio T ≈ pisos/10 s, redondeado al período más cercano del modelo. Amplificación leída para 0,23 g en roca. Fuera de la microzonificación (`noaf`), el factor es 1. |
| **Qué aportó** | Un factor físico de la sacudida **futura** para cada edificio: los 5.146 caen en 7 microzonas (1, 2, 3, 4a, 4c, 4d, 5), con una amplificación de 1,0 a 1,9 veces. |
| **Resultado honesto** | El daño satelital **no** cambia con la microzona (escombros entre 5,4 % y 8,9 %, chi-cuadrado p = 0,21; escombros o techo, p = 0,34). El suelo no explica el daño observado en esta muestra; entra al índice como amplificador de la próxima réplica, con peso bajo (10 %). |
| **Limitaciones** | Resolución de ~750 m: en los bordes entre microzonas un edificio puede quedar en la vecina. Las funciones son modelos estadísticos, no mediciones de este sismo. |

## 3. GEM TREQ: susceptibilidad a licuación y pendiente

| | |
|---|---|
| **Qué es** | 4.169 sitios de Cali con la unidad geológica, la susceptibilidad a licuación (`vh` muy alta, `h`, `m`, `l`, `vl`, `n` nula), la profundidad del nivel freático y la pendiente del terreno. |
| **Enlace** | Misma carpeta de GEM: `sites_liquefaction.csv` y `sites_landslide.csv`, unidos en `gem_sitio_licuacion_ladera.csv` (se comprobó que los sitios coinciden fila a fila). |
| **Por qué** | El USGS emitió alerta roja de licuación para este evento (producto *ground-failure*). El modelo del USGS es un ráster global de ~1 km; el de GEM es local y por unidad geológica de Cali. |
| **Cómo se cruzó** | Sitio más cercano. Categoría convertida a 0..1 (`vh` 1,0 · `h` 0,8 · `m` 0,5 · `l` 0,25 · `vl` 0,1 · `n` 0). |
| **Qué aportó** | La comuna 10 tiene el 34,5 % de sus edificios en susceptibilidad alta o muy alta; las demás, entre 0 % y 4,7 %. Entra al índice dentro de `c_suelo`, promediado con la amplificación. |
| **Resultado honesto** | Sin relación con el daño satelital (chi-cuadrado p = 0,18). |

## 4. USGS ShakeMap del sismo principal

| | |
|---|---|
| **Qué es** | Mapa oficial del movimiento del suelo del evento us6000tjl2 (M7,4, 10-ago-2026), versión 11. Cada nodo (~1 km) trae la intensidad Mercalli (MMI), PGA, PGV y aceleración espectral a 0,3, 0,6, 1,0 y 3,0 s. Combina 66 estaciones sísmicas, 458 observaciones de intensidad y modelos de atenuación. |
| **Enlace** | [Página del evento](https://earthquake.usgs.gov/earthquakes/eventpage/us6000tjl2/shakemap): archivo `grid.xml` del producto ShakeMap. |
| **Licencia** | Dominio público (gobierno de EE. UU.). |
| **Cómo se obtuvo** | `scripts/descargar_externos.py` lee el `grid.xml` (28 MB, 674 × 671 nodos) y lo recorta al casco urbano: 306 nodos en `usgs_shakemap_cali.csv`. PGA y PSA vienen en %g y se pasan a g. |
| **Por qué** | Es la estimación oficial de cuánto se sacudió cada punto. Sin ella, "Cali está a 160 km del epicentro" no dice nada de la sacudida real. |
| **Qué aportó** | Los edificios analizados recibieron **MMI 6,4 a 7,1 (fuerte a muy fuerte) y PGA de 0,19 a 0,23 g**. Es la cifra de contexto de la mitad (a). |
| **Resultado honesto** | Dentro de la zona de los datos la sacudida varió poco y no se asocia con el daño satelital. Por eso no entra al índice: describe el sismo que ya pasó, no la próxima réplica. |

## 5. Validación: acelerógrafo del SGC y "Did You Feel It?" del USGS

| | |
|---|---|
| **Qué es** | Las observaciones que usa el ShakeMap dentro de Cali: la estación RAC2C de la Red Nacional de Acelerógrafos del SGC y 32 celdas de 1 km de reportes ciudadanos DYFI. |
| **Enlace** | `stationlist.json` del producto ShakeMap; [DYFI del evento](https://earthquake.usgs.gov/earthquakes/eventpage/us6000tjl2/dyfi). |
| **Cómo se usó** | Se comparó cada observación con el nodo del ShakeMap más cercano. Archivo: `usgs_estaciones_cali.geojson`. |
| **Qué aportó** | **El ShakeMap es consistente en Cali.** La estación RAC2C (SGC) registró PGA 0,116 g y MMI 6,9; el ShakeMap da MMI 6,8 en ese punto, aunque con PGA 0,154 g, un 33 % más alta. Las 32 celdas DYFI promedian una intensidad de 6,86 y el ShakeMap 6,79 en los mismos puntos. Esto le da credibilidad a la fuente 4 ante el jurado. |

## 6. USGS: catálogo de réplicas

| | |
|---|---|
| **Qué es** | Catálogo ComCat: sismos M ≥ 2,5 a menos de 150 km del epicentro, del 10-ago al 13-nov-2026. |
| **Enlace** | [API FDSN](https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2026-08-10&endtime=2026-11-14&latitude=4.8601&longitude=-76.2558&maxradiuskm=150&minmagnitude=2.5&orderby=time-asc), guardado como `usgs_replicas.geojson`. |
| **Qué aportó** | 67 réplicas después del sismo principal, la mayor de M5,4. **47 fueron en septiembre**, un mes después del sismo, y la última fue el 3-nov. La amenaza de réplicas sigue vigente, que es la premisa de la pregunta. |
| **Limitaciones** | Todas las registradas por el USGS en la zona son M ≥ 4: su red no detecta las pequeñas tan lejos. La prensa citó más de 130 réplicas (fuente 8). No se cruza por edificio porque todas están a más de 100 km de Cali. |

## 7. OpenStreetMap: servicios urbanos, vías y límites

| | |
|---|---|
| **Qué es** | Comunas (22), barrios (338), salud (439: 378 `hospital`, 61 `clinic`), bomberos y policía (63), educación (287) y vías principales (4.070 tramos motorway/trunk/primary/secondary). |
| **Enlace y licencia** | Overpass API (`scripts/descargar_osm.py`, 12-nov-2026) y extracto PBF de Geofabrik (`scripts/extraer_osm_pbf.py`, que agrega `osm_puntos_encuentro.geojson`). ODbL: citar "© colaboradores de OpenStreetMap". |
| **Por qué** | El portal de datos abiertos de Cali y la IDESC están fuera de línea desde el 21-oct-2026. OSM es la única fuente abierta con servicios y vías de toda la ciudad. |
| **Cómo se cruzó** | Distancia al hospital o clínica más cercano; distancia a la vía principal más cercana; comuna y barrio por unión espacial (se completaron las 2 comunas vacías). |
| **Qué aportó** | Servicios urbanos: 147 edificios con escombros a menos de 200 m de un centro de salud. 5 edificios con escombros podrían bloquear una vía principal (regla: distancia a la vía ≤ altura, pisos × 3 m); son pocos porque los edificios son bajos (mediana de 2 pisos). |
| **Limitaciones** | OSM etiqueta como "hospital" muchas IPS pequeñas, así que la distancia a salud es optimista. Barrios con nombres de OSM, no los códigos catastrales. |

## 8. Contexto del sismo (para la presentación, no para el modelo)

| Fuente | Enlace | Dato | Nota |
|---|---|---|---|
| OPS, Sitrep 1 | [PDF](https://www.paho.org/sites/default/files/2026/08/sitrep1-terremoto-colombia-agosto-20260.pdf) | 111 fallecidos y 87 heridos (corte 13:30 del 10-ago) | Preliminar. Profundidad 103 km según OPS |
| Cambio Colombia | [Nota](https://cambiocolombia.com/pais/articulo/2026/8/sismo-de-magnitud-74-con-epicentro-en-choco-se-sintio-en-gran-parte-de-colombia-que-se-sabe-hasta-ahora) | Profundidad 96 km según boletín del SGC | **Discrepancia de profundidad:** SGC 96 km (boletín), OPS 103 km, USGS 116 km. Usamos la del USGS porque es la del catálogo y el ShakeMap que usamos. |
| Infobae | [Nota](https://www.infobae.com/colombia/2026/08/12/nuevo-temblor-en-choco-se-sintio-con-fuerza-en-cali-y-genero-nuevas-afectaciones-en-la-infraestructura/) | Réplica del 12-ago con nuevas afectaciones en Cali | Argumento: "las réplicas siguen causando daño" |
| NTN24 | [Nota](https://www.ntn24.com/noticias-actualidad/nuevo-sismo-sacudio-la-region-de-choco-en-colombia-reportan-que-se-sintio-tambien-en-cali-651737) | Más de 130 réplicas | El USGS registra menos (ver fuente 6) |
| USGS, página del evento | [us6000tjl2](https://earthquake.usgs.gov/earthquakes/eventpage/us6000tjl2) | M7,4 Mww, 116 km, alerta roja PAGER, 1.253 reportes DYFI | Verificado el 13-nov-2026 por la API |
| Informe de investigación del equipo | `docs/INFORME_SISMO.md` | Comparación con Venezuela, banco de 19 casos, historia del código | Verificar cada cifra contra su fuente antes de ponerla en una diapositiva |

## Qué dicen las fuentes externas sobre el daño satelital

Se probó si alguna variable externa se asocia con el daño observado (escombros o techo desaparecido), con una prueba chi-cuadrado sobre los 4.711 edificios con dato satelital (tabla `gold_icesixuao_factores`):

| Factor (fuente) | % con daño, mínimo y máximo entre categorías | p-valor |
|---|---|---|
| Período de construcción (GEM) | 26,7 % a 34,0 % | 0,14 |
| Estrato (GEM) | 20,0 % a 29,0 % | 0,94 |
| Uso (GEM) | 28,3 % a 31,8 % | 0,85 |
| Microzona (GEM) | — | 0,34 |
| Licuación (GEM) | 20,8 % a 29,1 % | 0,18 |
| Comuna | — | 0,51 |

Además, el daño **no se agrupa en el espacio**: los vecinos a menos de 50 m de un edificio con escombros tienen escombros en la misma proporción que los vecinos de uno sin escombros (6,1 % frente a 6,3 %; prueba de permutación, p = 0,62).

**Lectura:** con estos datos, el daño satelital se comporta como una señal individual, no como un patrón explicable por el suelo, la edad o el uso. Hay dos explicaciones posibles: el daño fue parejo en esta zona, o la clasificación satelital tiene mucho ruido por edificio (la guía advierte que son inferencias, no inspecciones). Ninguna de las dos se puede descartar con estos datos. **Consecuencia práctica:** el dato satelital sirve para marcar edificios a inspeccionar, pero no basta para priorizar. Por eso el índice combina el daño observado con lo que las fuentes externas sí saben de cada edificio (vulnerabilidad, ocupantes, suelo y servicios).

## Lista para el correo de entrega

1. **GEM TREQ, modelo de exposición de Cali** (github.com/gem/treq-riesgo-urbano): por edificio, año, estrato, uso, ocupantes y vulnerabilidad de la tipología. Aportó la población en edificios dañados y la vulnerabilidad del índice.
2. **GEM TREQ, microzonificación INGEOMINAS-DAGMA 2005, amplificación y licuación** (misma fuente): componente de suelo del índice ante réplicas.
3. **USGS ShakeMap v11 del evento us6000tjl2** (earthquake.usgs.gov): intensidad MMI 6,4 a 7,1 y PGA 0,19 a 0,23 g en los edificios analizados.
4. **SGC, acelerógrafo RAC2C, y USGS DYFI**: validan el ShakeMap en Cali.
5. **USGS, catálogo de réplicas** (API FDSN): 67 réplicas M ≥ 4 hasta el 3-nov, 47 de ellas en septiembre.
6. **OpenStreetMap** (Overpass API): salud, bomberos, vías principales, comunas y barrios; distancia a salud y posible bloqueo de vías.

## No disponibles (y por qué)

| Fuente | Enlace | Problema | Alternativa |
|---|---|---|---|
| Datos abiertos Cali | [datos.cali.gov.co](https://datos.cali.gov.co/) | Fuera de línea desde el 21-oct-2026 por "medidas de seguridad" (comunicado de la Alcaldía) | Comunas y barrios desde OSM |
| IDESC (geovisor y WFS) | [idesc.cali.gov.co](https://idesc.cali.gov.co/) | Redirige al portal de la Alcaldía; el WFS responde 404 | Microzonificación desde GEM TREQ |
| Microzonificación (capa vectorial) | [Alcaldía](https://www.cali.gov.co/dagma/publicaciones/1099/microzonificacion-sismica-cali/) | Solo como mapa (PDF) | Grilla de GEM TREQ (fuente 2) |
| Población por manzana (DANE CNPV 2018) | geoportal del DANE | Sin tiempo para verificar la descarga | Ocupantes por edificio de GEM, que usa el mismo censo (fuente 1) |
| Modelo de licuación del USGS (*ground-failure*) | producto del evento | Ráster de ~1 km; requiere `rasterio` | Licuación local de GEM (fuente 3) |
| Copernicus EMS, activación EMSR916 | [mapping.emergency.copernicus.eu](https://mapping.emergency.copernicus.eu/activations/EMSR916) | El portal responde, pero no se alcanzó a revisar si cubre las comunas de los datos | Pendiente: sería la validación independiente del daño satelital |

Este hallazgo sirve en la presentación: la ciudad perdió su infraestructura de datos abiertos justo cuando más se necesita, y el pipeline se armó con fuentes abiertas alternativas.

## Revisión de las fuentes del informe (13-nov-2026)

Se revisaron el catálogo del capítulo 4 y las referencias del capítulo 15 de `INFORME_SISMO.md`, contrastándolos con páginas de los publicadores, metadatos de API y muestras de archivos públicos. Los 19 casos del capítulo 7 son casos históricos seleccionados, no 19 conjuntos de datos homogéneos. Las 38 referencias tampoco equivalen a 38 bases descargables: varias agrupan artículos, normas y noticias.

Alcance de los estados:

- **Inspeccionada:** se consultaron metadatos, campos o una muestra de datos. No implica validar todas las filas.
- **Localizada:** se encontró la ficha o el documento, pero su contenido completo o descarga sigue pendiente.
- **Parcial:** una referencia agrupa fuentes y solo algunas quedaron identificadas o comprobadas.
- **Acceso limitado:** la consulta recibió un bloqueo, tiempo agotado o redirección. No demuestra una caída general del servicio.
- **Interna:** depende de material del organizador; no se consultaron ni redistribuyeron los edificios del evento.

### Las 20 fuentes del catálogo, una por una

El número C corresponde al orden de la tabla del capítulo 4 del informe.

| ID | Fuente y acceso comprobado | Formato y unidad de análisis | Utilidad para contrastar con Cali | Resultado y pendiente |
|---|---|---|---|---|
| C01 | [USGS ComCat/FDSN](https://earthquake.usgs.gov/fdsnws/event/1/) | GeoJSON; un evento sísmico | Misma definición de magnitud, fecha, profundidad y coordenadas para diferentes sismos | **Inspeccionada.** Consultados por ID Colombia `us6000tjl2`, Venezuela `us6000t7zp`, Armenia `usp00091q3` y Bolivia `usp0006dzc`. No contiene por sí sola el daño municipal ni acredita causalidad. |
| C02 | [USGS ShakeMap, Colombia](https://earthquake.usgs.gov/earthquakes/eventpage/us6000tjl2/shakemap) y [Venezuela](https://earthquake.usgs.gov/earthquakes/eventpage/us6000t7zp/shakemap) | `download/grid.xml`; celda de sacudida por evento | Extraer MMI, PGA, PGV y aceleraciones espectrales sobre cada ciudad, incluida Cali frente a Pereira o Manizales en el mismo evento | **Inspeccionada.** Las API de ambos eventos incluyen el producto y sus grillas respondieron HTTP 200. Son estimaciones de sacudida, no inventarios de daños. PGA y PSA vienen en `%g`; PGV en `cm/s`. Guardar versión del producto. |
| C03 | [USGS DYFI, Colombia](https://earthquake.usgs.gov/earthquakes/eventpage/us6000tjl2/dyfi) y [Venezuela](https://earthquake.usgs.gov/earthquakes/eventpage/us6000t7zp/dyfi) | GeoJSON y texto; celdas de respuestas ciudadanas a 1 o 10 km | Contrastar percepción de la sacudida entre ciudades | **Inspeccionada.** Muestras de `dyfi_geo_10km.geojson` con `cdi`, `nresp`, `dist`, `stddev` y geometría. Conservar número de respuestas e incertidumbre: pocas respuestas no representan a toda la ciudad. |
| C04 | [USGS PAGER, Colombia](https://earthquake.usgs.gov/earthquakes/eventpage/us6000tjl2/pager) y [Venezuela](https://earthquake.usgs.gov/earthquakes/eventpage/us6000t7zp/pager) | JSON/XML; población expuesta por MMI, agregada y por país | Dar contexto de exposición con una metodología común | **Inspeccionada.** `json/exposures.json` disponible en ambos; contiene `mmi`, `aggregated_exposure` y `country_exposures`. Esta tabla no desagrega comunas. Sus estimaciones de pérdidas no son conteos observados de víctimas. |
| C05 | [USGS Vs30 Models and Data](https://earthquake.usgs.gov/data/vs30/) | Grilla global; Vs30 en m/s | Usar una referencia de sitio común para ciudades sin microzonificación local | **Localizada.** Página oficial especifica 30 segundos de arco y un ZIP global de 631 MB. No se descargó ese archivo. Es una aproximación basada en pendiente con modelos regionales incorporados; no es un estudio geotécnico de cada edificio. |
| C06 | [SGC, catálogo instrumental](https://bdrsnc.sgc.gov.co/paginas1/catalogo/Consulta_Experta/consultaexperta_2.php) y [Sismicidad Histórica](https://sish.sgc.gov.co/visor/) | Consultas instrumentales, intensidades y efectos históricos por sitio | Antecedentes colombianos, especialmente Popayán y Armenia; contraste con USGS | **Parcial.** El visor histórico respondió HTTP 200. El catálogo instrumental localizado declara junio de 1993 a febrero de 2018; no sirve como catálogo de 2026. Las rutas genéricas `/catalogo` y `/sismos` recibieron 403. Falta fijar exportación y ruta vigente para eventos recientes. |
| C07 | [Metadatos de `hbdu-4927`](https://www.datos.gov.co/api/views/hbdu-4927.json) | Entrada de catálogo externo del portal geocientífico | Descubrir capas específicas del SGC | **Inspeccionada.** El registro se llama «Portal de Datos Abiertos // SGC» y no presenta columnas tabulares. Hay que identificar una capa concreta con cobertura, escala, licencia y servicio de descarga. No incorporarlo como si fuera una tabla de sismos. |
| C08 | [Microzonificación de Cali, registro UNGRD](https://repositorio.gestiondelriesgo.gov.co/handle/20.500.11762/19833) | Estudio técnico; zonificación de 2005 | Caracterizar el sitio dentro de Cali | **Acceso limitado.** La consulta tuvo un bucle de redirección. El [README de condiciones de sitio de GEM](https://github.com/gem/treq-riesgo-urbano/tree/main/Cali/Condiciones_Sitio) identifica expresamente Ingeominas–Dagma 2005 como referencia. No se verificó aquí una descarga vectorial oficial. |
| C09 | [GEM TREQ](https://github.com/gem/treq-riesgo-urbano) | CSV/XML y capas; exposición, sitio y resultados de riesgo | Cali, Quito y Santiago de los Caballeros bajo una familia metodológica común | **Inspeccionada.** Árbol del repositorio, README de las tres ciudades y muestras CSV. Incluye mucho más que amplificación: inventarios modelados, vulnerabilidad y escenarios. Detalle en el apartado siguiente. Licencia del repositorio CC BY-SA 4.0; citar procedencia y versión. |
| C10 | [NSR-10, Título A, copia publicada por CAMACOL](https://camacol.co/sites/default/files/descargables/T%C3%ADtulo%20A%20NSR-10%20del%20Decreto%20926%20del%2019032010_0.pdf) | PDF normativo | Interpretar clases de suelo y requisitos de diseño | **Localizada.** Es una norma, no una base de daños o un inventario del cumplimiento por edificio. Para afirmar vigencia jurídica se necesita además revisar las modificaciones aplicables. |
| C11 | [DANE, herramientas CNPV 2018](https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/censo-nacional-de-poblacion-y-vivenda-2018/herramientas), [descargas](https://www.dane.gov.co/files/geoportal-provisional/) y [servicio Manzana](https://portalgis.dane.gov.co/mparcgis/rest/services/MARCO_INTEGRADO/Serv_DatosCNPV2018_Integrados_MGN2018/MapServer/215?f=pjson) | Shapefile, tablas y ArcGIS REST; municipio/manzana | Comparar población y vivienda con denominadores geográficos coherentes | **Parcial.** La capa 215 respondió HTTP 200 con códigos DANE y formatos JSON/GeoJSON/PBF; sus campos inspeccionados son cartográficos. Falta unir la tabla temática de población. La página oficial ofrece MGN integrado con CNPV a nivel de manzana. No se descargaron los paquetes nacionales ni se verificaron las proyecciones numéricas citadas en el informe. |
| C12 | UNGRD: [metadatos `wwkg-r6te`](https://www.datos.gov.co/api/views/wwkg-r6te.json) y [metadatos `2343-nuqp`](https://www.datos.gov.co/api/views/2343-nuqp.json) | API Socrata JSON/CSV; reporte de afectación y atención municipal | Comparar daño y ayudas realmente registradas en municipios colombianos | **Inspeccionada.** Coberturas reales consultadas: 2019–2022 y 2025, respectivamente. Hay 38 y 41 filas con `evento='SISMO'`; no son necesariamente eventos independientes. Incluyen afectaciones, ayudas e inversión. Campos y límites detallados abajo. |
| C13 | [Copernicus EMSR916](https://mapping.emergency.copernicus.eu/activations/EMSR916/) y [comunicado oficial](https://mapping.emergency.copernicus.eu/news/earthquake-in-colombia-emsr916/) | Productos de mapeo de emergencia por área de interés | Contraste de daño satelital entre áreas del mismo evento | **Localizada.** El comunicado confirma la activación por el sismo colombiano y menciona Cali, Pereira, Manizales y Quibdó. La página de activación necesita cargar contenido dinámico. Falta verificar qué áreas tienen productos, sus fechas y los archivos vectoriales/raster disponibles; una mención de ciudad no prueba cobertura de mapeo. |
| C14 | [NASA/JPL–Caltech ARIA](https://aria.caltech.edu/) y su [archivo de respuesta a desastres](https://aria-share.jpl.nasa.gov/) | Damage Proxy Maps y desplazamientos; raster por evento | Contrastar señal de cambio satelital en casos con cobertura | **Localizada.** La página oficial enlaza el archivo y describe los productos. No quedó verificado un archivo específico del doblete venezolano o de Cali. Un proxy de daño no equivale a inspección estructural. |
| C15 | [ReliefWeb](https://reliefweb.int/) y [recopilación de Naciones Unidas en Colombia](https://colombia.un.org/es/320793-informaci%C3%B3n-y-actualizaciones-sobre-el-terremoto-en-colombia) | Informes/PDF; institución y fecha de corte | Reconstruir balances, necesidades y respuesta por ciudad cuando el informe lo permita | **Parcial.** Búsqueda de actualizaciones en ReliefWeb respondió HTTP 200. La ONU enlaza actualizaciones humanitarias. Es un agregador: registrar la entidad autora de cada reporte. Se localizaron también [OPS, Sitrep 7](https://www.paho.org/sites/default/files/2026/09/sitrep7-colombia-sismo-04092026-es.pdf) y [PNUD, RAPIDA](https://www.undp.org/latin-america/press-releases/rapida-assessment-colombia-earthquake-estimates-usd-132-billion-cop-421-trillion-structural-damage-and-generated-169). No se transcribió una tabla municipal completa. |
| C16 | HDX: [UNGRD enero 2023–agosto 2024](https://data.humdata.org/dataset/emergencias-ungrd-desde-enero-2023-a-agosto-2024) y [Colombia: Desastres Naturales](https://data.humdata.org/dataset/colombia-desastres-naturales) | Recursos XLSX; inventarios históricos | Ampliar el historial municipal y buscar cobertura de 2026 | **Localizada mediante API CKAN**, aunque la ficha web tuvo 403. El primer recurso es `UNGRD_2023_A_2024_AGOSTO.xlsx`; el segundo anuncia `historico_ungrd_2016_2026_corte_20261005.xlsx`. No se descargaron ni inspeccionaron sus libros: el nombre no acredita completitud, columnas, ni presencia del sismo de agosto. Revisar organización publicadora y duplicidad con datos.gov.co. |
| C17 | [OSM/Geofabrik Colombia](https://download.geofabrik.de/south-america/colombia.html) | PBF; objetos geográficos con etiquetas | Vías y servicios de Cali y otras ciudades colombianas con el mismo corte | **Inspeccionada en el repo y localizada en el publicador.** El PBF local tiene 334.335.333 bytes. Según el resumen del dueño, terminó y el extractor se validó con educación (287/287); no se repitió esa extracción. El extractor actual limita la salida a Cali. Ausencia de `assembly_point` mapeados no demuestra ausencia de puntos de encuentro reales. Un colegio tampoco es automáticamente un albergue habilitado. |
| C18 | Alcaldía de Cali: [indicadores](https://indicadores.cali.gov.co/) y [datos abiertos](https://datos.cali.gov.co/) | Tablas/indicadores por comuna, según recurso | Complementar contexto local | **Acceso limitado:** ambas consultas recibieron 403 desde esta herramienta. Eso no confirma la afirmación histórica de caída global o su fecha inicial. Falta una URL de conjunto específico y su diccionario. |
| C19 | [FUNVISIS](https://funvisis.gob.ve/) | Catálogo e informes venezolanos, según producto | Validar parámetros y antecedentes de Venezuela con la agencia nacional | **Acceso limitado:** tiempo agotado. No se verificaron exportación ni informes de Cariaco/Caracas. USGS permite contrastar parámetros instrumentales; no reemplaza los balances oficiales de víctimas. |
| C20 | Datos de edificios del DataBridge Hack y `DataBridge_Hack_Guia_Evento_2.md` | GeoJSON; edificio con contorno y atributos | Daño por edificio y comuna en Cali | **Interna; guía inspeccionada.** Durante la revisión se incorporó en paralelo la guía oficial: describe 5.146 edificios y 20 propiedades más geometría. No se examinó el archivo de edificios ni se reprodujo la corrida reportada en el README actualizado. La versión recibida retira el aviso y las muestras ficticias iniciales. El README sitúa los datos oficiales en `data/oficiales/`, sin redistribución, incluidos los mapas derivados. |

### GEM TREQ: conjuntos adicionales dentro de una fuente ya citada

Se consultó el [árbol completo del repositorio](https://api.github.com/repos/gem/treq-riesgo-urbano/git/trees/main?recursive=1), los README y cabeceras de muestras. No se descargaron inventarios completos ni se ejecutó OpenQuake.

| Recurso | Qué quedó comprobado | Aplicación y condición |
|---|---|---|
| [Exposición de Cali](https://github.com/gem/treq-riesgo-urbano/tree/main/Cali/Exposicion) | `Exposure_Cali_Colombia.csv`: `id`, `lon`, `lat`, `taxonomy`, `number`, `structural`, `CONSTRUCTION_PERIOD`, `INCOME_LEVEL`, `FLOORS`, `OCC`, `night`, `AREA_CONST`, `OCCUPANCY`, `USO_DETALLE`, `COMUNA`, `ID_BARRIO`, `MICROZONE`. El README describe una base de aproximadamente 349 mil edificios con insumos catastrales de 2021 y población del censo 2018. | Contexto de exposición, ocupación y período constructivo para Cali. `night` es ocupación nocturna modelada; no es presencia observada durante el sismo de 2026. Verificar correspondencia espacial antes de cruzar con edificios del evento; los ID no son automáticamente comunes. |
| [Exposición de Quito](https://github.com/gem/treq-riesgo-urbano/tree/main/Quito/Exposicion) | `Exposure_Quito_br1.csv`: coordenadas, taxonomía, número, costo estructural, ocupación nocturna, uso, material, sistema resistente, código, altura y división territorial. El README declara varias ramas de exposición para incorporar incertidumbre. | Contrastar tipologías y composición de la exposición con Cali. No concatenar ramas como si fueran edificios diferentes. |
| [Exposición de Santiago de los Caballeros](https://github.com/gem/treq-riesgo-urbano/tree/main/Santiago/Exposicion) | `Exposure_Santiago_br1.csv`: coordenadas, taxonomía, ocupación, material, código, altura, año y unidades territoriales. Muestra descargada parcialmente y cabecera comprobada. | Tercera ciudad del proyecto TREQ. Se refiere a República Dominicana, no a Santiago de Chile. Homologar taxonomías y unidades antes de comparar. |
| [Condiciones de sitio de Cali](https://github.com/gem/treq-riesgo-urbano/tree/main/Cali/Condiciones_Sitio) | Grillas con Vs30 de SGC y USGS, roca, códigos de amplificación, funciones espectrales y parámetros para licuación/deslizamientos. | Ensayar sensibilidad de la caracterización del suelo. No asignar a cada edificio una medición geotécnica que la grilla no tiene. |
| [Riesgo de Cali](https://github.com/gem/treq-riesgo-urbano/tree/main/Cali/Riesgo) | El README enumera 13 escenarios. En `Scenarios/47080/aggrisk-COMUNA_47080.csv` se comprobaron estados de daño, colapsos, fallecidos, heridos, personas sin vivienda y pérdidas, con valores y razones. Hay también `barrios_data.csv`, `comunas_data.csv` y resultados probabilísticos. | Explorar necesidades bajo distintos escenarios. Son resultados modelados publicados en 2022; no daños observados en 2026. Conservar escenario y denominador; no sumar escenarios alternativos. |
| [Riesgo de Quito](https://github.com/gem/treq-riesgo-urbano/tree/main/Quito/Riesgo) y [Santiago](https://github.com/gem/treq-riesgo-urbano/tree/main/Santiago/Riesgo) | Carpetas de escenarios y cálculos probabilísticos presentes; README de ambos consultados. | Contraste entre modelos urbanos. Falta homologar campos, exposición, unidades monetarias, período y sacudida antes de comparar resultados. |
| [Vulnerabilidad y consecuencias](https://github.com/gem/treq-riesgo-urbano/tree/main/Vulnerabilidad_GEM) | Funciones de fragilidad/vulnerabilidad XML y CSV de consecuencias para colapsos, desplazamiento, fallecidos, heridos graves y pérdidas. | Sustentar escenarios mediante modelos explícitos. No convertir estas funciones directamente en pesos del índice actual ni validar un modelo contra resultados derivados de las mismas funciones. |

### UNGRD y HDX: cobertura y posibilidades reales

Las consultas Socrata usadas fueron `min(fecha)`, `max(fecha)`, `count(*)` y agrupación por `evento`. La unidad es una fila de reporte; varios municipios pueden corresponder al mismo sismo.

| Conjunto | Cobertura observada | Filas totales | Filas `SISMO` | Datos útiles y límites |
|---|---|---|---|---|
| [UNGRD `wwkg-r6te`](https://www.datos.gov.co/resource/wwkg-r6te.json?$select=min(fecha),max(fecha),count(*)) | 01-ene-2019 a 31-dic-2022 | 25.857 | 38 | `divipola`, fecha, municipio, fallecidos, heridos, personas, familias, viviendas destruidas/averiadas, salud, vías y educación. También asistencia, maquinaria, recursos ejecutados y cantidades de ayudas. Varios montos son texto y requieren limpieza y revisión de moneda/unidad. |
| [UNGRD V2 `2343-nuqp`](https://www.datos.gov.co/resource/2343-nuqp.json?$select=min(fecha),max(fecha),count(*)) | 01-ene-2025 a 31-dic-2025 | 6.506 | 41 | Cambia el esquema: `codificaci_n_segun_divipola`, `muertos`, `viv_destru`, `viv_aver`, `c_salud`, etc. Añade `codigo_emergencia`, coordenadas en texto, ayudas, horas de maquinaria y apoyo total. No asumir que tiene 2026 porque la descripción diga «posibles vigencias futuras». |
| [HDX 2023–2024](https://data.humdata.org/dataset/emergencias-ungrd-desde-enero-2023-a-agosto-2024) | El título anuncia ene-2023 a ago-2024 | Sin inspeccionar | Sin inspeccionar | Candidato para cubrir parte del vacío entre las dos API. Falta inspeccionar fechas, columnas y duplicados. |
| [HDX histórico](https://data.humdata.org/dataset/colombia-desastres-naturales) | El recurso anuncia 2016–2026, corte 05-oct-2026 | Sin inspeccionar | Sin inspeccionar | Es la primera comprobación pendiente para buscar afectaciones de 2026. La ficha y el enlace existen; el contenido del libro no se comprobó. |

La existencia de ayuda entregada permite estudiar la relación entre afectación y respuesta. No permite atribuir eficiencia o vidas salvadas sin información adicional sobre tiempos, capacidad disponible, necesidades no atendidas y criterios de asignación. Un faltante de registro tampoco significa cero daño o cero ayuda.

### Revisión de las 38 referencias bibliográficas

R01–R38 conservan la numeración del capítulo 15. «Localizada» se refiere al documento o portal, no a todas las cifras que el informe le atribuye. En referencias agrupadas se indica lo que sigue pendiente; no se declaran verificadas en bloque.

| ID | Fuente del informe | Comprobación, alcance y uso |
|---|---|---|
| R01 | USGS, evento de Colombia y FDSN | **Inspeccionada.** C01–C04. La respuesta del evento confirma M7,4, fecha 10-ago-2026, coordenadas y profundidad de 116,13 km en esta consulta. Guardar la revisión del catálogo al incorporarlo. |
| R02 | Wikipedia, Colombia 2026 | **Localizada.** [Artículo](https://es.wikipedia.org/wiki/Terremoto_de_Colombia_de_2026) accesible. Fuente secundaria para localizar referencias, no balance primario ni base municipal ya validada. |
| R03 | Wikipedia, Venezuela 2026 | **Localizada.** [Artículo](https://es.wikipedia.org/wiki/Terremotos_de_Venezuela_de_2026) accesible. Mismo límite que R02. |
| R04 | BBC Mundo, doblete venezolano | **Acceso limitado.** El [enlace citado](https://www.bbc.com/mundo/articles/crr8ezq9ez8o) no permitió lectura desde la herramienta. No se validaron sus cifras. Noticia de contexto. |
| R05 | GEM, reporte D.2.62 de Cali | **Localizada.** [PDF con ruta completa](https://cloud-storage.globalquakemodel.org/public/wix-new-website/pdf-collections-wix/publications/TREQ%20deliverables/reports/TREQ_D262_Riesgo_Sismico_Cali_v1.0.pdf) respondió HTTP 200 y cabecera PDF. El README de Cali enlaza una variante `v1.00.pdf`; la ruta `v1.0.pdf` es la comprobada. No se releyó íntegro el informe técnico. |
| R06 | GEM, funciones de amplificación | **Inspeccionada.** C09 y apartado GEM. La fuente permite ampliar a exposición y consecuencias, además del suelo ya descargado. |
| R07 | SGC, catálogo y visor | **Parcial.** C06. Diferenciar catálogo histórico, catálogo instrumental antiguo y eventos recientes. |
| R08 | UNGRD, microzonificación | **Acceso limitado.** C08. Se localizó su referencia metodológica en GEM; falta consultar el documento original. |
| R09 | CAMACOL/AIS, NSR-10 | **Localizada.** C10. Contexto técnico normativo; no aporta daño por ciudad ni observaciones de cumplimiento. |
| R10 | datos.gov.co, UNGRD y SGC | **Inspeccionada.** C07 y C12. Hay dos tablas de emergencias con períodos distintos y una ficha de portal externo; no tres tablas equivalentes. |
| R11 | Copernicus EMSR916 | **Localizada.** C13. Activación confirmada; faltan productos y áreas concretas descargadas. |
| R12 | USGS Vs30 | **Localizada.** C05. Misma variable global para contraste; no se descargó el raster completo. |
| R13 | ReliefWeb, Colombia agosto 2026 | **Parcial.** C15. El informe da solo el dominio y un título genérico; falta vincular cada cifra a un reporte y su entidad autora. |
| R14 | FUNVISIS, Cariaco | **Acceso limitado.** C19. Falta la ficha histórica exacta; no se verificaron las cifras del caso. |
| R15 | DANE, censo y proyecciones | **Parcial.** C11. Acceso cartográfico identificado; población temática y proyecciones específicas por ciudad pendientes. |
| R16 | IEEE, guía del evento | **Interna; copia local inspeccionada.** `DataBridge_Hack_Guia_Evento_2.md` llegó al árbol durante la revisión. Describe formato, campos, categorías y límites de interpretación del inventario. No se comprobó una publicación web original. Sirve para alcance y contrato de datos del evento; sus cifras contextuales requieren sus fuentes primarias. |
| R17 | Telemundo/Infobae, coberturas | **Referencia incompleta.** Esta entrada no identifica artículos por URL ni fecha de corte. Las notas citadas en la preparación inicial requieren comprobarse individualmente si se usan. Para cifras de impacto se localizaron alternativas primarias OPS/PNUD en C15. |
| R18 | USGS, Armenia, Bolivia y Venezuela | **Inspeccionada.** FDSN respondió HTTP 200 para los tres ID. Armenia `usp00091q3`: 17 km; Bolivia `usp0006dzc`: 631,3 km; Venezuela `us6000t7zp`: 10 km. Esos parámetros no verifican automáticamente los fallecidos citados. |
| R19 | SGC, Popayán 1983 y Armenia 1999 | **Parcial.** [Página del aniversario de Popayán](https://www2.sgc.gov.co/Noticias/Paginas/Aniversario-No-40-del-terremoto-de-Popayan-un-momento-para-pensar-en-la-importancia-de-construir-bien-en-Colombia.aspx) y [visor SISH](https://sish.sgc.gov.co/visor/) respondieron HTTP 200. Falta exportar las fichas y efectos por localidad para el banco comparativo. |
| R20 | EERI, Izmit, Bam y Avcılar | **Parcial.** El [inventario LFE de EERI](https://www.eeri.org/lfe/pdf/Report_LFE_Contributions.pdf) identifica la investigación de Bam y se encontró la referencia bibliográfica del reporte de Izmit. Faltan documentos originales precisos y localización del estudio de Avcılar. Aportan observaciones de mecanismos de daño; no se encontró aquí una tabla multiciudad lista para unir. |
| R21 | USGS, Loma Prieta | **Localizada.** [Ficha oficial](https://www.usgs.gov/programs/earthquake-hazards/science/m-69-october-17-1989-loma-prieta-earthquake) identifica 63 muertos y 3.757 heridos. Para comparar por ciudad se necesita desagregación; el total corresponde al evento. |
| R22 | Recopilaciones mundiales y NZ History | **Parcial.** Se localizaron [Vrancea 1977](https://en.wikipedia.org/wiki/1977_Vrancea_earthquake) y [NZ History sobre Christchurch](https://nzhistory.govt.nz/page/christchurch-earthquake-kills-185). NZ History y [Policía de Nueva Zelanda](https://www.police.govt.nz/news/major-events/previous-major-events/christchurch-earthquake) respaldan 185 víctimas para Christchurch. Bam, Haití, Turquía-Siria y Caracas requieren sus fuentes primarias y cortes propios. |
| R23 | Singh/UNAM e ITIC/UNESCO | **Parcial.** Se identificó bibliográficamente el artículo de Singh en Earthquake Spectra 4, 653–674 mediante referencias académicas. Falta recuperar su texto y la ficha exacta ITIC; no quedaron validados los cocientes de amplificación ni todo el balance chileno. |
| R24 | UNISDR/UNDRR, códigos | **Localizada.** [Comunicado de 2011](https://www.undrr.org/news/building-codes-saves-lives-main-message-anniversary-chile-earthquake-and-lesson-learned-nz). Sustento contextual para aplicación de normas; no estima el peso causal de un código en cada ciudad. |
| R25 | SGC, Pedernales 2016 | **Localizada.** [Informe oficial](https://www2.sgc.gov.co/Publicaciones/Sismos%20importantes/Informe%20Sismo%20Ecuador%2016%20de%20abril%20de%202016.pdf). Candidato para contrastar efectos de un sismo regional sentido en Colombia; falta extraer la información por sitio. |
| R26 | ANH, Cauca–Romeral | **Parcial.** [Documento Cauca–Patía](https://www.anh.gov.co/documents/4148/Cauca_Pat%C3%ADa_pdf-Ronda_Colombia_2010.pdf) identifica el sistema y segmentos. No se comprobó que sustente la distancia de 15–35 km a Cali ni una clasificación de «peor escenario». No es una estimación de recurrencia o probabilidad de sismo. |
| R27 | Wikipedia: Kantō, código japonés, Fukui, pagodas, amnistías, Sampoong y Nepal | **Parcial.** Se consultaron [Kantō](https://en.wikipedia.org/wiki/1923_Great_Kant%C5%8D_earthquake) y [amnistía constructiva](https://en.wikipedia.org/wiki/Construction_amnesty). La referencia mezcla siete temas; faltan enlaces primarios y comprobación individual de los demás. Sampoong es un colapso no sísmico: no incorporarlo como terremoto del banco. |
| R28 | Aoyama, NZSEE 1981 | **Localizada.** [Artículo original](https://bulletin.nzsee.org.nz/article/download/983/959): revisión del código japonés que entró en vigor en junio de 1981. Sirve para clasificar períodos normativos; no acredita la norma efectivamente aplicada a un edificio colombiano. |
| R29 | JSSI, MLIT y ley japonesa de refuerzo | **Parcial.** El dominio JSSI respondió y redirigió a `www.jssi.or.jp`; se localizó [documentación MLIT de daños por períodos constructivos](https://www.mlit.go.jp/common/001287789.pdf). No se verificaron el folleto exacto de 2024, los 5.286 edificios ni los porcentajes 28,2/2,2 y la ley citada. |
| R30 | GEM, BCN, EERI/Moroni y USGS sobre Chile | **Parcial.** Se localizaron [DS61 en BCN](https://www.bcn.cl/leychile/navegar?i=1034101) y [USGS OFR 2011-1053](https://pubs.usgs.gov/of/2011/1053/of2011-1053.pdf). Faltan DS60 exacto, trabajo de Moroni y páginas que respalden los porcentajes y «cinco edificios». `eerii.org` en la referencia parece una errata; EERI usa `eeri.org`. |
| R31 | Memoria Chilena, MINSAL e ITIC | **Parcial.** [Memoria Chilena](https://www.memoriachilena.gob.cl/602/w3-article-3576.html), [MINSAL, 1985](https://degreyd.minsal.cl/el-terremoto-del-3-de-marzo-de-1985-y-su-alto-impacto-en-la-infraestructura-de-salud/) y [CSN de la Universidad de Chile](https://www2.csn.uchile.cl/efemerides-sismicas-terremoto-de-algarrobo-1985/) localizados. CSN distingue 7,8 Ms de 8,0 Mw: no mezclar escalas. ITIC y el desglose de muertes por tsunami siguen pendientes. |
| R32 | SGC Tumaco y Javeriana Popayán | **Parcial.** Portal SISH disponible; falta fijar la ficha exacta de Tumaco y el documento de Javeriana. No quedó comprobado el rango de víctimas de Tumaco ni su metodología. |
| R33 | Normativa colombiana de 1984, 1998, 2010 y 2015 | **Parcial.** Se localizaron Título A y [antecedente judicial oficial que describe la secuencia normativa](https://consejodeestado.gov.co/documentos/boletines/223/05001-33-31-011-2011-00079-01.pdf), además de [documentación de Minvivienda](https://minvivienda.gov.co/node/850). Faltan textos originales completos y modificaciones para una revisión de vigencia. No es una base de cumplimiento por edificación. |
| R34 | Reuters, Guardian, Al Jazeera/CNN y Turkish Minute | **Parcial.** Se identificó una [republicación de Reuters de 2019](https://www.fijitimes.com.fj/turkish-cities-could-become-graveyards-with-building-amnesty-engineers-say/); el resto no tiene URL exacta en el informe y sus cifras no quedaron verificadas. Contexto institucional; no trasladar porcentajes de responsabilidad judicial a pesos de riesgo en Cali. |
| R35 | GEER-082 y supuesto artículo MDPI de 400 edificios | **Parcial, referencia por aclarar.** [GEER-082](https://www.geerassociation.org/?id=109&layout=default&view=geerreports) y DOI `10.18118/G6PM34` localizados. La búsqueda del estudio de 400 edificios encontró [Soil Dynamics and Earthquake Engineering, DOI 10.1016/j.soildyn.2024.109119](https://www.sciencedirect.com/science/article/pii/S0267726124006717), y [Natural Hazards, DOI 10.1007/s11069-025-07774-3](https://link.springer.com/article/10.1007/s11069-025-07774-3). No se identificó el artículo exacto de MDPI Sustainability descrito; falta autor/título/DOI. |
| R36 | CTV/Engineering NZ, Puebla y Rébsamen | **Parcial.** [Engineering NZ, CTV](https://www.engineeringnz.org/news-insights/ctv-building/) registra la queja acogida en septiembre de 2024. No se verificaron conjuntamente las acusaciones sobre otra persona ni las sentencias mexicanas. Son casos individuales de contexto, sin una variable municipal directamente utilizable. |
| R37 | Transparency International, CPNAA y DANE | **Parcial.** [CPI 2024](https://www.transparency.org/en/cpi/2024) mide percepción de corrupción pública a nivel nacional. [CPNAA](https://www.cpnaa.gov.co/) es el Consejo Profesional Nacional de Arquitectura y sus Profesiones Auxiliares; su [publicación sobre licencias](https://www.cpnaa.gov.co/tres-de-cada-cinco-viviendas-en-colombia-son-fabricadas-sin-licencia-de-construccion/) está identificada en su informe de gestión 2023. Falta fuente específica para el 36–40 % atribuido al DANE. Un índice nacional no identifica calidad constructiva de una comuna o edificio. |
| R38 | Brune, SEG, PNSN, PEER, NIST, GEM, USGS, Duke, UNDRR, RSNZ, UNESCO, Kelly, Washington Post y Skytree | **Parcial.** Se localizaron [notas de osciladores de Gavin/Duke](https://people.duke.edu/~hpgavin/StructuralDynamics/SimpleOscillators.pdf) y los recursos GEM ya descritos. La entrada agrupa teoría y cifras de edificios específicos sin identificar todos los títulos/DOI/páginas. Quedan pendientes las referencias individuales restantes. No incorporar sus ejemplos numéricos como observaciones de daño ni como multiplicadores universales del índice. |

### Discrepancias y condiciones para el contraste

1. **Profundidad de Armenia 1999:** FDSN devuelve 17 km para `usp00091q3`; el banco del informe redondea a unos 20 km y la tabla de escenarios GEM de Cali consigna 52 km para ese ID. Conservar cada valor con su fuente y distinguir escenario de catálogo; no resolverlo sustituyendo silenciosamente uno por otro.
2. **Población por manzana:** existe oferta oficial DANE y se comprobó un servicio cartográfico, pero todavía falta la tabla temática unida y su evaluación. «No disponible a tiempo» es una restricción operativa del borrador, no prueba de inexistencia del dato.
3. **Datos del SGC:** `hbdu-4927` es una ficha de portal. Hace falta seleccionar capas concretas.
4. **Disponibilidad web:** 403, redirecciones y tiempos agotados de esta consulta no prueban por sí solos que toda una institución esté fuera de línea. Conservar la evidencia de la otra sesión para el diagnóstico específico de Overpass.
5. **Registro OSM de puntos de encuentro:** la capa de Cali está vacía según la extracción validada en la sesión anterior. Representarla como «sin puntos mapeados en esta fuente»; verificar puntos habilitados con autoridad local. Educación, salud y puntos de encuentro son categorías distintas.
6. **Causas y pesos:** los 19 antecedentes fueron seleccionados deliberadamente. No constituyen una muestra representativa para concluir que profundidad, suelo o informalidad explican por sí solos una diferencia de mortalidad, ni para estimar automáticamente los pesos del índice.

### Orden propuesto de incorporación

Es una propuesta de investigación; no cambia las fuentes adoptadas, los pesos del índice ni el pipeline.

1. **Comparación del mismo evento entre ciudades:** ShakeMap y DYFI para Cali y otras ciudades afectadas, unidos a balances municipales con fuente y corte. Permite contrastar sacudida y afectación sin cambiar de terremoto. Primero verificar cobertura municipal de los reportes y de EMSR916.
2. **Antecedentes observados en Colombia:** inspeccionar el histórico anunciado por HDX y homologar UNGRD/SISH por fecha, municipio y código de evento cuando exista. Deduplicar publicaciones antes de contar casos. Los registros consultados de 2019–2022 y 2025 sirven como antecedentes, no como balance de 2026.
3. **Preparación por escenarios:** usar exposición y resultados GEM para comparar escenarios dentro de Cali y, después de homologar variables, con Quito y Santiago de los Caballeros. Etiquetar todos esos resultados como modelados.
4. **Necesidades y capacidad de respuesta:** cruzar población/exposición con servicios OSM y daño observado o modelado según la pregunta. Para asignar recursos hacen falta además inventario disponible, operatividad, tiempos de atención y restricciones de acceso; la presencia de un hospital en OSM no informa su capacidad disponible.

La tabla futura de contraste debe conservar, al menos, `evento_id`, `ciudad_codigo`, `fecha_evento`, `tipo_dato` (observado/modelado/reportado), `fuente`, `fecha_corte`, `version`, magnitud y tipo, profundidad, sacudida local, población expuesta, edificios analizados/afectados, afectación humana, ayudas entregadas y faltantes. Cada tasa debe indicar su numerador, denominador y unidad. Evitar comparar una cifra nacional con una municipal o usar población nacional para atribuir diferencias de riesgo a una ciudad.
