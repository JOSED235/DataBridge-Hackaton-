# Entrega: correo del viernes 13 antes de las 5:00 p. m.

**Para:** marcelasabogue@ieee.org
**Asunto:** `databridgehack: icesixuao`

Cifras: capa oro publicada en Databricks el 13-nov-2026 (commit `41c9e0b`, 43 controles aprobados) y verificada contra la corrida local: 5.146 predios, prioridades 179/357/892/2.141/435/1.142, ranking 3, 9, 10, 18, 20, 19, 17 y sensibilidad `solo_datos_oficiales` 0,764 / 40 %. Cada cifra se rastrea a una tabla gold (indicada entre corchetes en las notas de cada sección; las notas no van en el correo). La ocupación GEM es modelada y se cruza por cercanía: se dice "ocupantes modelados", nunca "personas afectadas".

Checklist del correo:

- [ ] 1. Captura del Catalog (`workspace.default`) con `bronze_icesixuao_*`, `silver_icesixuao_*` y `gold_icesixuao_*`: lista en `capturas/primeracatalog.png`, `segundacatalog.png` y `terceracatalog.png` (45 tablas)
- [ ] 2. Texto de decisiones (≤ 200 palabras)
- [ ] 3. Respuesta a las dos preguntas (≤ 500 palabras)
- [ ] 4. Lista de fuentes
- [ ] 5. Presentación de 3 diapositivas (PowerPoint o PDF), la última con el pantallazo del mapa
- [ ] 6. Enlace al mapa interactivo: https://josed235.github.io/DataBridge-Hackaton-/ y al dashboard de resultados: https://josed235.github.io/DataBridge-Hackaton-/dashboard.html (publicados con autorización de la organización hasta el cierre del evento)

---

## 2. Decisiones en silver y gold (≤ 200 palabras)

**Bronze:** copia fiel del GeoJSON (5.146 predios, 21 columnas) como texto, con nulos intactos, más 15 capas externas.

**Silver:** llave `OBJECTID` (`ID_PREDIO` tiene 1.509 nulos); vacíos pasan a nulo. Los 1.234 predios con `NPISOS` = 0 no tienen construcción registrada: se conservan sin pisos, porque el satélite ve daño en 342. Los 11 `NPISOS` nulos se estiman con GEM y quedan marcados (`pisos_fuente`). Reparamos 4 polígonos inválidos sin redondear la geometría y calculamos el área en m² (EPSG:9377). Los 435 sin dato satelital no se borran. Severidad: escombros 1,0; techo desaparecido 0,7; sin cambio aparente 0,1 (no significa sin daño). Cruces con GEM (cercanía ≤ 15 m), ShakeMap y OpenStreetMap.

**Gold:** índice de 0 a 1 por edificio: daño 25 %, vulnerabilidad 20 %, ocupantes 15 %; suelo, altura, salud y vías 10 % cada uno. Suma ponderada y no PCA: los siete componentes son casi independientes (el primer eje explica 26 %). Prioridades por percentil entre edificios con dato; sin dato y lotes tienen categoría propia. Comunas por percentil 90. Cada edificio muestra sus tres motivos. Siete escenarios de sensibilidad. La ocupación GEM no se suma como población única. Tablas comentadas en el Catalog, con Genie y dashboard.

> Notas: [`silver_icesixuao_predios`: `pisos_fuente`, `geom_reparada`, `area_m2`, `sin_dato_satelital`], [`gold_icesixuao_predios`: `motivos_principales`], [`gold_icesixuao_resumen_sensibilidad`].

---

## 3. Respuesta a las dos preguntas (≤ 500 palabras)

**¿Qué afectaciones generó el sismo en Cali?**

El sismo de M7,4 a 116 km de profundidad sacudió los edificios con intensidad Mercalli de 6,4 a 7,1 (ShakeMap del USGS), confirmada por el acelerógrafo del Servicio Geológico Colombiano en Cali (6,9) y los reportes ciudadanos (6,86).

*Infraestructura.* De 5.146 predios en 7 comunas, el satélite marca 296 con alta probabilidad de escombros (5,8 %) y 1.058 con posible desaparición de techo (20,6 %); 342 de esos 1.354 no tienen construcción registrada. Hay 435 sin dato satelital (8,5 %), que no deben leerse como sanos.

*Población.* El modelo de exposición de GEM (censo 2018), cruzado por cercanía, ubica unos 5.500 ocupantes nocturnos modelados en edificios dañados (5.494 contando una vez cada registro GEM; 6.950 sumando por predio), más de la mitad en la comuna 19, y 2.298 en edificios sin dato. Es un modelo, no un conteo de personas.

*Servicios urbanos.* Muestran daño 73 edificios institucionales y 177 comerciales. 626 predios dañados están a menos de 200 m de un centro de salud.

**¿Qué factores reducen el impacto de las réplicas?**

Las réplicas siguen: el USGS registró 67, de hasta M5,4, 47 de ellas en septiembre. Un edificio debilitado es el que más puede colapsar después.

Primero probamos qué se asocia con el daño satelital en los 3.569 edificios del ranking: no detectamos asociación con época, uso, microzona, licuación ni comuna (menor p ajustado por Holm: 0,27; V de Cramér ≤ 0,06). Eso no prueba que no importen. Un estudio de la Javeriana Cali lo explica: en Cali el daño fue interior, en edificios de 3 a 6 pisos anteriores a 1984, y el satélite casi no lo ve (Copernicus vio 21 edificaciones; hubo 1.538 reportes locales). Por eso el dato satelital sirve para marcar edificios, pero no basta para priorizar.

Los factores que reducen el impacto combinan lo observado con lo conocido:

1. **Inspeccionar primero donde coinciden daño, fragilidad y gente.** 179 edificios quedan en prioridad muy alta: 99 % con daño visible, 69 % construidos hasta 1985 y 2.945 ocupantes modelados; un tercio, edificios de 3 a 6 pisos de 1985 o antes. Sin las fuentes externas, solo el 40 % del top 50 se mantendría.
2. **Empezar por la comuna 3:** dos de cada tres de sus edificios son de 1985 o antes y su vulnerabilidad media es la más alta.
3. **Verificar en terreno los 435 edificios sin dato y los 342 lotes con daño visible**, en lugar de suponer que están bien; el visor entrega cada lista en Excel.
4. **Proteger los servicios:** revisar primero los dañados cerca de centros de salud y los institucionales, y despejar las vías que sus escombros podrían bloquear.
5. **A mediano plazo, reforzar el parque construido hasta 1985,** como hicieron Japón y Chile: es la única medida que reduce la vulnerabilidad.

**Límites:** daño inferido por satélite, no inspeccionado; vulnerabilidad y ocupantes modelados (catastro 2021, censo 2018); pruebas exploratorias, sin causalidad. El índice prioriza; no declara un edificio seguro o inseguro.

> Notas: [`gold_icesixuao_predios`: `prioridad`, `periodo_construccion`, `ocupantes_asignados_gem`], [`gold_icesixuao_comunas`: `ocupantes_asignados_gem_con_senal_danio` 6.950], [`gold_icesixuao_exposicion_gem`: `ocupantes_noche` de los 1.119 registros con `n_vinculos_con_senal_danio` > 0 = 5.494], [`gold_icesixuao_factores`: `p_ajustado_holm`, `v_cramer`], [`gold_icesixuao_resumen_sensibilidad`: `solo_datos_oficiales` 40 %], [cohorte de 3 a 6 pisos hasta 1985: 58 de 179 en muy alta, 303 de 3.569 en ranking; Javeriana en `docs/FUENTES.md`].

---

## 4. Fuentes externas

1. **GEM Foundation, proyecto TREQ: modelo de exposición de Cali** (https://github.com/gem/treq-riesgo-urbano/tree/main/Cali/Exposicion, CC BY-SA 4.0). Por edificio: año de construcción, estrato, uso, pisos, ocupantes y vulnerabilidad de la tipología. Se cruzó con el 98,9 % de los edificios. Aportó la población en edificios dañados, la vulnerabilidad del índice y los pisos de los 11 registros nulos.
2. **GEM TREQ: microzonificación sísmica INGEOMINAS-DAGMA 2005, funciones de amplificación y susceptibilidad a licuación** (https://github.com/gem/treq-riesgo-urbano/tree/main/Cali/Condiciones_Sitio). Aportó el componente de suelo del índice.
3. **USGS ShakeMap v11 del sismo us6000tjl2** (https://earthquake.usgs.gov/earthquakes/eventpage/us6000tjl2/shakemap). Aportó la intensidad y la aceleración recibidas por cada edificio.
4. **Servicio Geológico Colombiano, acelerógrafo RAC2C, y USGS "Did You Feel It?"** (https://earthquake.usgs.gov/earthquakes/eventpage/us6000tjl2/dyfi). Validaron el ShakeMap en Cali.
5. **USGS, catálogo de sismos ComCat** (https://earthquake.usgs.gov/fdsnws/event/1/). Aportó las 67 réplicas hasta el 3 de noviembre.
6. **OpenStreetMap** (https://www.openstreetmap.org, vía Overpass API y https://download.geofabrik.de/south-america/colombia.html, ODbL). Aportó salud, bomberos, vías principales, comunas y barrios; distancia a salud y posible bloqueo de vías.
7. **Pontificia Universidad Javeriana Cali, IEI: "Seis clústeres de afectación del sismo del 10 de agosto de 2026"** (https://www.javerianacali.edu.co/sites/default/files/2026-08/clu%CC%81steres%20de%20afectacio%CC%81n%20del%20sismo%20del%2010%20de%20agosto%20de%202026.pdf, agosto de 2026). Validación externa: ubica el daño de Cali en edificios de 3 a 6 pisos anteriores a 1984 y documenta que el satélite de Copernicus (EMSR916) vio 21 edificaciones frente a 1.538 reportes locales.

---

## 5. Las 3 diapositivas

**Diapositiva 1: Arquitectura.** Un diagrama de tres columnas:

- **Bronze:** GeoJSON oficial + 15 capas externas, copia fiel en texto.
- **Silver:** limpieza (`OBJECTID`, `NPISOS` = 0 → sin construcción registrada, 4 polígonos reparados sin redondear el WKT, área en m², sin dato marcado) + cruces (GEM 98,9 %, ShakeMap, OSM).
- **Gold:** índice por edificio, ranking por comuna, prueba de factores, sensibilidad y PCA (siete dimensiones casi independientes); 13 tablas comentadas, Genie y dashboard.

Abajo, una línea por decisión clave con su porqué.

**Diapositiva 2: Respuesta.** Dos columnas.

- **Izquierda, afectaciones:** tres cifras grandes.
  - 1.354 predios con daño visible (26 %).
  - Unos 5.500 ocupantes nocturnos modelados en edificios dañados (GEM; 6.950 si se suma por predio).
  - 435 edificios sin dato.
- **Derecha, qué reduce el impacto:** las acciones en una línea cada una.
- **Abajo:** el hallazgo "el daño satelital no muestra un patrón claro", la explicación externa (Javeriana: daño interior en edificios de 3 a 6 pisos anteriores a 1984, que el satélite ve poco) y el 40 % del top 50 que se mantiene sin fuentes externas.
- **Pie:** límites.

**Diapositiva 3: Mapa.** El pantallazo (ver abajo) y tres líneas:

- qué muestra: prioridad por edificio y comunas por índice;
- por qué: dónde inspeccionar primero;
- cómo se hizo: gold → GeoJSON → MapLibre + deck.gl; el visor filtra por cola de trabajo y descarga la lista en Excel para las brigadas.

### El pantallazo del mapa (debe entenderse en 30 segundos)

- Edificios coloreados por **prioridad**: rojo muy alta, naranja alta, gris el resto, morado sin dato, azul sin construcción registrada.
- Comunas con borde y su puesto en el ranking: 3, 9, 10, 18, 20, 19, 17.
- Centros de salud como puntos verdes, bomberos y policía en azul, vías principales en blanco y halos de concentración de riesgo.
- Título en la imagen: "Dónde inspeccionar primero ante la próxima réplica".
- Leyenda visible; fuente de datos en una esquina.
