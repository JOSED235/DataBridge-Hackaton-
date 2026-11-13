# Entrega: correo del viernes 13 antes de las 5:00 p. m.

**Para:** marcelasabogue@ieee.org
**Asunto:** `databridgehack: icesixuao`

Cifras: capa oro publicada en Databricks el 13-nov-2026 (commit `41c9e0b`, 43 controles aprobados) y verificada contra la corrida local: 5.146 predios, prioridades 179/357/892/2.141/435/1.142, ranking 3, 9, 10, 18, 20, 19, 17 y sensibilidad `solo_datos_oficiales` 0,764 / 40 %. Cada cifra se rastrea a una tabla gold (indicada entre corchetes en las notas de cada sección; las notas no van en el correo). La ocupación GEM es modelada y se cruza por cercanía: se dice "ocupantes modelados", nunca "personas afectadas".

Checklist del correo:

- [ ] 1. Captura del Catalog (`workspace.default`) con `bronze_icesixuao_*`, `silver_icesixuao_predios` y `gold_icesixuao_*`
- [ ] 2. Texto de decisiones (≤ 200 palabras)
- [ ] 3. Respuesta a las dos preguntas (≤ 500 palabras)
- [ ] 4. Lista de fuentes
- [ ] 5. Presentación de 3 diapositivas (PowerPoint o PDF), la última con el pantallazo del mapa

---

## 2. Decisiones en silver y gold (≤ 200 palabras)

**Bronze:** copia fiel del GeoJSON (5.146 predios, 21 columnas) como texto, con nulos y espacios intactos, más 15 capas externas.

**Silver:** llave `OBJECTID` (`ID_PREDIO` tiene 1.509 nulos); vacíos pasan a nulo. Los 1.234 predios con `NPISOS` = 0 no tienen construcción registrada: se conservan sin pisos, porque el satélite ve daño en 342. Los 11 `NPISOS` nulos se estiman con GEM y quedan marcados (`pisos_fuente`). Reparamos 4 polígonos inválidos sin redondear la geometría y calculamos el área en m² (EPSG:9377). Los 435 sin dato satelital no se borran. Severidad: escombros 1,0; techo desaparecido 0,7; sin cambio aparente 0,1 (no significa sin daño). Cruces con GEM (cercanía ≤ 15 m, no llave catastral), ShakeMap del USGS y OpenStreetMap.

**Gold:** índice de 0 a 1 por edificio: daño 25 %, vulnerabilidad 20 %, ocupantes 15 %; suelo, altura, salud y vías 10 % cada uno. Prioridades por percentil entre edificios con dato; sin dato y lotes tienen categoría propia. Comunas por percentil 90. Cada edificio muestra sus tres motivos principales. Siete escenarios alternativos de pesos y fuentes. La ocupación GEM no se suma como población única: un registro puede quedar cerca de varios predios.

> Notas: [`silver_icesixuao_predios`: `pisos_fuente`, `geom_reparada`, `area_m2`, `sin_dato_satelital`], [`gold_icesixuao_predios`: `motivos_principales`], [`gold_icesixuao_resumen_sensibilidad`].

---

## 3. Respuesta a las dos preguntas (≤ 500 palabras)

**¿Qué afectaciones generó el sismo en Cali?**

El sismo de M7,4 a 116 km de profundidad sacudió los edificios analizados con intensidad Mercalli de 6,4 a 7,1 y aceleración de 0,19 a 0,23 g, según el ShakeMap del USGS. Ese valor coincide con el acelerógrafo del Servicio Geológico Colombiano en Cali (6,9) y con los reportes ciudadanos (6,86).

*Infraestructura.* De 5.146 predios en 7 comunas, el satélite marca 296 con alta probabilidad de escombros (5,8 %) y 1.058 con posible desaparición de techo (20,6 %); 342 de esos 1.354 no tienen construcción registrada. Hay 435 sin dato satelital (8,5 %), que no deben leerse como sanos.

*Población.* El modelo de exposición de GEM (censo 2018), cruzado por cercanía, ubica unos 5.500 ocupantes nocturnos modelados en edificios dañados (5.494 contando una vez cada registro GEM; 6.950 sumando por predio), más de la mitad en la comuna 19, y 2.298 en edificios sin dato. Es un modelo, no un conteo de personas afectadas.

*Servicios urbanos.* Muestran daño 73 edificios institucionales y 177 comerciales. 626 predios dañados están a menos de 200 m de un centro de salud.

**¿Qué factores reducen el impacto de las réplicas?**

Las réplicas siguen: el USGS registró 67, de hasta M5,4, 47 de ellas en septiembre. Un edificio debilitado es el que más puede colapsar después.

Primero probamos qué se asocia con el daño satelital en los 3.569 edificios del ranking. No detectamos asociación con época, uso, microzona, licuación ni comuna (menor p ajustado por Holm: 0,27; V de Cramér ≤ 0,06); el estrato tiene grupos demasiado pequeños para probarlo. Eso no demuestra que no importen: la señal satelital sola no muestra un patrón claro, así que no basta para priorizar.

Por eso los factores que reducen el impacto combinan lo observado con lo conocido:

1. **Inspeccionar primero donde coinciden daño, fragilidad y gente.** 179 edificios quedan en prioridad muy alta: 99 % con daño visible, 69 % construidos hasta 1985 y 2.945 ocupantes modelados. Sin las fuentes externas, solo el 40 % del top 50 se mantendría.
2. **Empezar por la comuna 3:** dos de cada tres de sus edificios son de 1985 o antes y su vulnerabilidad media es la más alta.
3. **Verificar en terreno los 435 edificios sin dato y los 342 lotes con daño visible**, en lugar de suponer que están bien.
4. **Proteger los servicios:** revisar primero los edificios dañados cercanos a centros de salud y los institucionales, y despejar las vías principales que sus escombros podrían bloquear.
5. **A mediano plazo, reforzar el parque construido hasta 1985,** como hicieron Japón y Chile. Es la única medida que actúa sobre la vulnerabilidad, el factor que más cambia la prioridad.

**Límites:** daño inferido por satélite, no inspeccionado; vulnerabilidad y ocupantes modelados (catastro 2021, censo 2018); pruebas exploratorias, sin causalidad. El índice prioriza; no declara un edificio seguro o inseguro.

> Notas: [`gold_icesixuao_predios`: `prioridad`, `periodo_construccion`, `ocupantes_asignados_gem`], [`gold_icesixuao_comunas`: `ocupantes_asignados_gem_con_senal_danio` 6.950], [`gold_icesixuao_exposicion_gem`: `ocupantes_noche` de los 1.119 registros con `n_vinculos_con_senal_danio` > 0 = 5.494], [`gold_icesixuao_factores`: `p_ajustado_holm`, `v_cramer`], [`gold_icesixuao_resumen_sensibilidad`: `solo_datos_oficiales` 40 %].

---

## 4. Fuentes externas

1. **GEM Foundation, proyecto TREQ: modelo de exposición de Cali** (github.com/gem/treq-riesgo-urbano, CC BY-SA 4.0). Por edificio: año de construcción, estrato, uso, pisos, ocupantes y vulnerabilidad de la tipología. Se cruzó con el 98,9 % de los edificios. Aportó la población en edificios dañados, la vulnerabilidad del índice y los pisos de los 11 registros nulos.
2. **GEM TREQ: microzonificación sísmica INGEOMINAS-DAGMA 2005, funciones de amplificación y susceptibilidad a licuación** (mismo repositorio). Aportó el componente de suelo del índice.
3. **USGS ShakeMap v11 del sismo us6000tjl2** (earthquake.usgs.gov). Aportó la intensidad y la aceleración recibidas por cada edificio.
4. **Servicio Geológico Colombiano, acelerógrafo RAC2C, y USGS "Did You Feel It?"** (estaciones del ShakeMap). Validaron el ShakeMap en Cali.
5. **USGS, catálogo de sismos ComCat** (API FDSN). Aportó las 67 réplicas hasta el 3 de noviembre.
6. **OpenStreetMap** (Overpass API y extracto de Geofabrik, ODbL). Aportó salud, bomberos, vías principales, comunas y barrios; distancia a salud y posible bloqueo de vías.

---

## 5. Las 3 diapositivas

**Diapositiva 1: Arquitectura.** Un diagrama de tres columnas:

- **Bronze:** GeoJSON oficial + 15 capas externas, copia fiel en texto.
- **Silver:** limpieza (`OBJECTID`, `NPISOS` = 0 → sin construcción registrada, 4 polígonos reparados sin redondear el WKT, área en m², sin dato marcado) + cruces (GEM 98,9 %, ShakeMap, OSM).
- **Gold:** índice por edificio, ranking por comuna, prueba de factores y sensibilidad.

Abajo, una línea por decisión clave con su porqué.

**Diapositiva 2: Respuesta.** Dos columnas.

- **Izquierda, afectaciones:** tres cifras grandes.
  - 1.354 predios con daño visible (26 %).
  - Unos 5.500 ocupantes nocturnos modelados en edificios dañados (GEM; 6.950 si se suma por predio).
  - 435 edificios sin dato.
- **Derecha, qué reduce el impacto:** el hallazgo "con esta muestra el daño satelital no muestra un patrón claro → no basta para priorizar" y las 5 acciones en una línea cada una.
- **Pie:** límites.

**Diapositiva 3: Mapa.** El pantallazo (ver abajo) y tres líneas:

- qué muestra: prioridad por edificio y comunas por índice;
- por qué: dónde inspeccionar primero;
- cómo se hizo: gold → GeoJSON → MapLibre + deck.gl.

### El pantallazo del mapa (debe entenderse en 30 segundos)

- Edificios coloreados por **prioridad**: rojo muy alta, naranja alta, gris el resto, morado sin dato, azul sin construcción registrada.
- Comunas con borde y su puesto en el ranking: 3, 9, 10, 18, 20, 19, 17.
- Centros de salud como puntos verdes y vías principales en blanco.
- Título en la imagen: "Dónde inspeccionar primero ante la próxima réplica".
- Leyenda visible; fuente de datos en una esquina.
