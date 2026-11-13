# Entrega: correo del viernes 13 antes de las 5:00 p. m.

**Para:** marcelasabogue@ieee.org
**Asunto:** `databridgehack: icesixuao`

Cifras: corrida con los datos oficiales del 13-nov-2026, 11:00. Cada una se rastrea a una tabla gold (indicada entre corchetes en las notas de cada sección; las notas no van en el correo). Antes de enviar, confirmar que las tablas gold de Databricks dan lo mismo.

Checklist del correo:

- [ ] 1. Captura del Catalog (`workspace.default`) con `bronze_icesixuao_*`, `silver_icesixuao_predios` y `gold_icesixuao_*`
- [ ] 2. Texto de decisiones (≤ 200 palabras)
- [ ] 3. Respuesta a las dos preguntas (≤ 500 palabras)
- [ ] 4. Lista de fuentes
- [ ] 5. Presentación de 3 diapositivas (PowerPoint o PDF), la última con el pantallazo del mapa

---

## 2. Decisiones en silver y gold (≤ 200 palabras)

**Bronze:** copia fiel del GeoJSON (5.146 edificios, 21 columnas) como texto, con los nulos y espacios tal como llegaron, más 15 capas externas sin modificar.

**Silver:** usamos `OBJECTID` como llave, porque `ID_PREDIO` tiene 1.509 nulos. Convertimos los vacíos y los espacios en nulos. `NPISOS` era 0 o nulo en 1.245 edificios: tomamos los pisos del modelo de exposición de GEM (1.221) y la mediana de la comuna en el resto, y dejamos una marca. Reparamos 17 polígonos inválidos y calculamos el área en m² (EPSG:9377), porque `Shape__Area` viene en grados. No borramos los 435 edificios sin datos satelitales: quedan marcados para verificar en terreno. Como el daño viene por categoría, lo convertimos en severidad: escombros 1,0; techo desaparecido 0,7; sin cambio aparente 0,1, porque no significa sin daño. Cruzamos cada edificio con GEM, el ShakeMap del USGS y OpenStreetMap.

**Gold:** un índice de 0 a 1 por edificio que suma daño (25 %), vulnerabilidad (20 %), ocupantes (15 %), suelo, altura, distancia a salud y bloqueo de vías (10 % cada uno), con prioridades por percentil. Por comuna usamos el percentil 90. Probamos siete combinaciones de pesos.

> Notas: [`silver_icesixuao_predios`: `pisos_fuente`, `geom_reparada`, `area_m2`, `sin_dato_satelital`], [`gold_icesixuao_sensibilidad`].

---

## 3. Respuesta a las dos preguntas (≤ 500 palabras)

**¿Qué afectaciones generó el sismo en Cali?**

El sismo de M7,4 a 116 km de profundidad sacudió los edificios analizados con intensidad Mercalli de 6,4 a 7,1 y aceleración de 0,19 a 0,23 g, según el ShakeMap del USGS. Ese valor coincide con el acelerógrafo del Servicio Geológico Colombiano en Cali (6,9) y con los reportes ciudadanos (6,86).

*Infraestructura.* De 5.146 edificios en 7 comunas, el análisis satelital marca 296 con alta probabilidad de escombros (5,8 %) y 1.058 con posible desaparición de techo (20,6 %). Hay 435 sin datos satelitales (8,5 %), que no deben leerse como sanos.

*Población.* Al cruzar cada edificio con el modelo de exposición de GEM (censo 2018), estimamos que 6.907 personas duermen en edificios con daño visible: 3.731 de ellas en la comuna 19. Otras 2.646 viven en edificios sin dato satelital.

*Servicios urbanos.* 86 edificios institucionales y 233 comerciales muestran daño. 626 edificios dañados están a menos de 200 m de un centro de salud.

**¿Qué factores reducen el impacto de las réplicas?**

Las réplicas siguen: el USGS registró 67, de hasta M5,4, y 47 ocurrieron en septiembre, un mes después del sismo principal. Un edificio ya debilitado es el que más puede colapsar con la siguiente sacudida.

Primero probamos qué explica el daño. Ni la edad de construcción, ni el estrato, ni el uso, ni la microzona sísmica, ni la susceptibilidad a licuación cambian la tasa de daño satelital (chi-cuadrado, todos con p > 0,05). Tampoco se agrupa en el espacio: los vecinos de un edificio dañado no están más dañados. La señal satelital es individual y puede tener ruido. Sirve para marcar edificios, pero no basta para priorizar.

Por eso los factores que reducen el impacto combinan lo observado con lo conocido:

1. **Inspeccionar primero donde coinciden daño, fragilidad y gente.** El índice deja 247 edificios en prioridad muy alta: el 98 % tiene daño visible, el 67 % se construyó antes del código sísmico de 1984 y allí duermen 3.154 personas. Si se quitan las fuentes externas, solo el 30 % de ese top se mantiene: sin ellas, la priorización sería otra.
2. **Empezar por la comuna 3:** el 67 % de sus edificios es anterior a 1985 y su vulnerabilidad media es la más alta. La comuna 19 concentra el mayor número de personas en edificios dañados.
3. **Verificar en terreno los 435 edificios sin dato**, en lugar de suponer que están bien.
4. **Proteger los servicios:** revisar primero los edificios dañados cercanos a centros de salud y los institucionales, y despejar las vías principales que sus escombros podrían bloquear.
5. **A mediano plazo, reforzar el parque anterior a 1985,** como hicieron Japón y Chile. Esa es la única medida que actúa sobre la vulnerabilidad, el factor que más cambia la prioridad.

**Límites:** los datos son inferencias satelitales, no inspecciones. La vulnerabilidad y los ocupantes vienen de un modelo (catastro 2021, censo 2018). El índice sirve para priorizar, no para declarar un edificio seguro o inseguro.

> Notas: [`gold_icesixuao_predios`], [`gold_icesixuao_comunas`: `ocupantes_en_edif_con_danio`, `pct_antes_1985`], [`gold_icesixuao_factores`], [`gold_icesixuao_sensibilidad`: `solo_datos_oficiales` 30 %].

---

## 4. Fuentes externas

1. **GEM Foundation, proyecto TREQ: modelo de exposición de Cali** (github.com/gem/treq-riesgo-urbano, CC BY-SA 4.0). Por edificio: año de construcción, estrato, uso, pisos, ocupantes y vulnerabilidad de la tipología. Se cruzó con el 98,9 % de los edificios. Aportó la población en edificios dañados, la vulnerabilidad del índice y los pisos faltantes.
2. **GEM TREQ: microzonificación sísmica INGEOMINAS-DAGMA 2005, funciones de amplificación y susceptibilidad a licuación** (mismo repositorio). Aportó el componente de suelo del índice.
3. **USGS ShakeMap v11 del sismo us6000tjl2** (earthquake.usgs.gov). Aportó la intensidad y la aceleración recibidas por cada edificio.
4. **Servicio Geológico Colombiano, acelerógrafo RAC2C, y USGS "Did You Feel It?"** (estaciones del ShakeMap). Validaron el ShakeMap en Cali.
5. **USGS, catálogo de sismos ComCat** (API FDSN). Aportó las 67 réplicas hasta el 3 de noviembre.
6. **OpenStreetMap** (Overpass API y extracto de Geofabrik, ODbL). Aportó salud, bomberos, vías principales, comunas y barrios; distancia a salud y posible bloqueo de vías.

---

## 5. Las 3 diapositivas

**Diapositiva 1: Arquitectura.** Un diagrama de tres columnas:

- **Bronze:** GeoJSON oficial + 15 capas externas, copia fiel en texto.
- **Silver:** limpieza (`OBJECTID`, pisos 0 → GEM, polígonos reparados, área en m², sin dato marcado) + cruces (GEM 98,9 %, ShakeMap, OSM).
- **Gold:** índice por edificio, ranking por comuna, prueba de factores y sensibilidad.

Abajo, una línea por decisión clave con su porqué.

**Diapositiva 2: Respuesta.** Dos columnas.

- **Izquierda, afectaciones:** tres cifras grandes.
  - 1.354 edificios con daño visible (26 %).
  - 6.907 personas viviendo en ellos.
  - 435 edificios sin dato.
- **Derecha, qué reduce el impacto:** el hallazgo "el daño satelital no sigue ningún patrón → no basta para priorizar" y las 5 acciones en una línea cada una.
- **Pie:** límites.

**Diapositiva 3: Mapa.** El pantallazo (ver abajo) y tres líneas:

- qué muestra: prioridad por edificio y comunas por índice;
- por qué: dónde inspeccionar primero;
- cómo se hizo: gold → GeoJSON → MapLibre + deck.gl.

### El pantallazo del mapa (debe entenderse en 30 segundos)

- Edificios coloreados por **prioridad**: rojo muy alta, naranja alta, gris el resto, morado sin dato.
- Comunas con borde y su puesto en el ranking (1 = comuna 3).
- Centros de salud como puntos verdes y vías principales en blanco.
- Título en la imagen: "Dónde inspeccionar primero ante la próxima réplica".
- Leyenda visible; fuente de datos en una esquina.
