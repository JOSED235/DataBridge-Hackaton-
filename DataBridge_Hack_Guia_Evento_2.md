![Imagen](media/image1.png)

**DataBridge Hack**

Guía del evento · 13 y 14 de noviembre

Cargar datos · Analizar · Construir el mapa · Presentar

<table>
<colgroup>
<col style="width: 33%" />
<col style="width: 33%" />
<col style="width: 33%" />
</colgroup>
<thead>
<tr class="header">
<th><p><strong>Viernes 13</strong></p>
<p>Desarrollo: 8:00 a. m. a 4:00 p. m.</p></th>
<th><p><strong>Sábado 14</strong></p>
<p>Presentación y premiación: 9:00 a. m. a 11:00 a. m.</p></th>
<th><p><strong>Entrega</strong></p>
<p>Un correo hasta las 5:00 p. m. del viernes, descrito al final de esta
guía</p></th>
</tr>
</thead>
</table>

## El reto

> **Pregunta problema: ¿Qué afectaciones generó el sismo del 10 de
> agosto en la ciudad de Cali y qué factores contribuyen a reducir el
> impacto de las réplicas sobre la población, la infraestructura y los
> servicios urbanos?**
>
> La solución es abierta: ustedes eligen el enfoque, los datos
> adicionales y la herramienta de visualización.

Se espera que el proyecto aborde integralmente la pregunta, explicando
qué afectaciones generó el sismo y qué medidas o condiciones contribuyen
a reducir los efectos de las réplicas. Estos elementos deberán estar
articulados y representados de manera coherente en el mapa.

**Contexto.** El sismo fue de magnitud 7,4, con epicentro en el Chocó, y
afectó fuertemente a Cali, con colapsos de edificios y daños en
hospitales y colegios. Las cifras oficiales son preliminares.

## Agenda

Universidad Santiago de Cali, Sede Pampalinda (Calle 5 \# 62-00).

| **Viernes 13 de noviembre** |                                                                                                                         |
|-----------------------------|-------------------------------------------------------------------------------------------------------------------------|
| 8:00 a. m.                  | Llegada y apertura en el Auditorio T-USACA: bienvenida y presentación del reto. Lo ideal es ir llegando desde esta hora |
| 9:00 a. m.                  | Inicio en las salas 2413 y 2414 (Bloque 2, piso 4): carga de los datos a Databricks                                     |
| 10:00 a. m.                 | Exploración de los datos y definición del enfoque                                                                       |
| 11:00 a. m.                 | Desarrollo: análisis, datos externos y mapa                                                                             |
| 2:00 p. m.                  | Cierre del desarrollo: lo que debe quedar listo                                                                         |
| 4:00 p. m.                  | Fin de la jornada                                                                                                       |

| **Sábado 14 de noviembre** |                                                                                                 |
|----------------------------|-------------------------------------------------------------------------------------------------|
| 9:00 a. m.                 | Recibimiento en el Auditorio T-USACA                                                            |
| Después                    | Sustentaciones ante el jurado, de 5 minutos por equipo (el orden se anuncia en el recibimiento) |
| 11:00 a. m.                | Premiación y clausura                                                                           |

## Los datos

Un archivo GeoJSON con 5.146 edificios de Cali. Cada edificio trae su
contorno, datos catastrales y el resultado de un análisis satelital de
daños. GeoJSON es un archivo de texto que guarda formas geográficas con
sus atributos; casi cualquier herramienta de mapas lo abre.

| **Estado_Estructural**             | **Edificios** |
|------------------------------------|---------------|
| Sin cambio aparente / Daño interno | 3.357         |
| Posible desaparición de techo      | 1.058         |
| Sin datos satelitales              | 435           |
| Alta probabilidad de escombros     | 296           |

| **Campo**                        | **Qué es**                                                 |
|----------------------------------|------------------------------------------------------------|
| OBJECTID                         | Identificador de la fila                                   |
| COMUNA, BARRIO                   | Códigos de comuna y barrio (no hay nombres)                |
| MANZANA, TERRENO, PREDIO y otros | Códigos catastrales                                        |
| NPISOS                           | Número de pisos                                            |
| Indice_Escombros                 | Puntaje del análisis satelital; de él salen las categorías |
| Estado_Estructural               | Una de las cuatro categorías                               |
| Shape\_\_Area, Shape\_\_Length   | Área y perímetro, en grados y no en metros                 |
| geometry                         | Contorno del edificio en longitud y latitud                |

**Lectura responsable:** son inferencias hechas desde el espacio, no
inspecciones. «Sin cambio aparente» no significa «sin daño», y «sin
datos» tampoco significa «sin daño».

## Cargar los datos a Databricks

Esta es la única parte guiada. Son cinco pasos cortos y, si algo falla,
se puede repetir sin romper nada. No hay código para copiar: pídanle
ayuda a Genie, al asistente de Databricks o a cualquier IA, y revisen
que el resultado tenga sentido.

> **Dos palabras que van a oír.** Un **notebook** es un documento donde
> se escribe código en bloques llamados **celdas**. Para ejecutar una
> celda, hagan clic en ella y presionen **Shift + Enter**.

1.  **Abran un notebook.** Workspace → Create → Notebook, con el nombre
    de su equipo.
2.  **Creen el volumen de su equipo.** En Catalog, dentro de `workspace`
    y del esquema `default`, creen un volumen con el nombre de su equipo
    (el lugar donde se suben archivos).
3.  **Suban el archivo GeoJSON** al volumen con **Upload to this
    volume**, y copien su ruta con **Copy path**.
4.  **Conviertan el archivo en la tabla bronze.** Pídanle a una IA el
    código, por ejemplo: *«Tengo un GeoJSON de edificios en esta ruta:
    \[su ruta\]. Necesito leerlo en Python y guardarlo como tabla Delta
    en workspace.default, con una fila por edificio, una columna por
    propiedad y una columna más con la geometría como texto.»* El
    archivo tiene 5.146 edificios y 20 propiedades más la geometría.
5.  **Verifiquen.** La tabla debe tener 5.146 filas y 21 columnas.

## Las tres capas

Cada equipo construye las tres capas y cuenta brevemente qué hizo en
silver y en gold.

| **Capa** | **Para qué sirve**                  | **Qué se espera**                                                                                   |
|----------|-------------------------------------|-----------------------------------------------------------------------------------------------------|
| Bronze   | Guardar los datos tal como llegaron | Copia fiel del archivo, sin limpiar. Es su red de seguridad                                         |
| Silver   | Limpiar y enriquecer                | Decisiones sobre nulos, espacios en blanco, edificios sin datos, polígonos dudosos y datos externos |
| Gold     | Responder la pregunta               | Tablas claras, derivadas de silver, de las que salen los números y el mapa                          |

Nombren las tablas con la capa, el nombre de su equipo y su contenido,
por ejemplo `bronze_equipo1_predios` o
`silver_equipo1_datos_adicionales`. Pueden tener varias por capa.

## Pistas sobre los datos

> **Usen Genie.** Es el asistente de Databricks que responde preguntas
> sobre sus tablas en lenguaje natural. Pídanle, por ejemplo, cuántos
> edificios hay por Estado_Estructural o qué comunas tienen más
> edificios con alta probabilidad de escombros, y verifiquen el SQL que
> genera.

No son la solución; son cosas que el equipo organizador encontró al
revisar el archivo.

| **Pista**                                                                         | **Por qué importa**                                                               |
|-----------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| `Shape__Area` está en grados, no en metros                                        | Para áreas reales hay que reproyectar a un sistema métrico, por ejemplo EPSG:9377 |
| El mismo código de barrio aparece en más de una comuna                            | BARRIO solo no identifica un barrio; hay que combinarlo con COMUNA                |
| ID_PREDIO es nulo en 1.509 filas                                                  | Para una llave única sirve OBJECTID                                               |
| Hay valores vacíos y valores con solo espacios                                    | Un nulo y un espacio no se filtran igual                                          |
| NPISOS es 0 en 1.234 edificios                                                    | No se puede tratar 0 pisos como un dato válido sin revisarlo                      |
| Los 435 edificios sin datos suman cerca del 45 % del área construida (aproximado) | Un porcentaje de daño que los ignore puede engañar                                |

## Fuentes externas

Los datos base dicen dónde hubo daño, no por qué ni cómo reducir el
riesgo ante réplicas. Sumar fuentes externas y analizarlas bien es lo
que más puede subir su resultado. Investiguen qué les sirve según su
enfoque, citen de dónde sacaron cada dato y revisen que cubra Cali, sea
reciente y se pueda cruzar con los edificios. Algunas ideas por dónde
empezar: USGS y Servicio Geológico Colombiano (sismos y réplicas),
Alcaldía de Cali (suelo y ciudad), DANE (población), OpenStreetMap
(servicios y vías) e informes de entidades oficiales.

Elijan uno o dos datos y háganlos bien: es mejor un cruce sólido que
cinco superficiales.

## Del dato al mapa

Databricks es donde se hace el trabajo de datos; el mapa se construye a
partir de la tabla gold. En un proyecto real el mapa se conectaría a
gold por una API. Hoy, para simplificar, **exportan gold como GeoJSON,
lo descargan** (pídanle el código a una IA y luego descárguenlo desde
Catalog) y lo abren en la herramienta que elijan.

| **Herramienta**    | **Cómo cargar el archivo**                                            |
|--------------------|-----------------------------------------------------------------------|
| QGIS               | Capa → Añadir capa → Añadir capa vectorial                            |
| Kepler.gl          | Arrastrar el archivo al navegador                                     |
| MapLibre + deck.gl | Servir el archivo con un servidor local y leerlo con una capa GeoJSON |
| ArcGIS             | Agregar el archivo como capa                                          |

- Exporten una tabla gold con solo las columnas que necesita el mapa, y
  con una columna lista para colorear.
- Si reproyectaron, vuelvan a longitud y latitud (EPSG:4326) antes de
  exportar.
- Si el mapa sale vacío o en otro continente, revisen el orden
  \[longitud, latitud\].
- Un dashboard en Databricks con sus tablas gold es un extra opcional.

## Trabajar en equipo

Cada integrante puede crear su propia cuenta de Free Edition: los datos
pesan unos 5 MB y repetir la carga toma pocos minutos. Para combinar el
trabajo pueden agregar a sus compañeros al espacio de trabajo y
compartir el notebook (botón **Share**), o exportar el notebook (File →
Export) e importarlo en otra cuenta (Workspace → Import). Elijan **una**
cuenta donde estén las tres capas.

## Qué debe quedar listo el viernes

> ☐ Las tres capas en Databricks, con el nombre del equipo en sus
> tablas.
>
> ☐ Un mapa que abra en la herramienta elegida, con sus correspondientes
> capas.
>
> ☐ Los dos textos (200 y 500 palabras), la lista de fuentes y las tres
> diapositivas con el pantallazo del mapa.
>
> ☐ El correo de entrega enviado antes de las 5:00 p. m. (ver el final
> de esta guía).

## Presentación del sábado

Cada equipo tiene **5 minutos** para sustentar ante el jurado. Presentan
**únicamente lo que enviaron el viernes**: sus tres diapositivas, la
última con el mapa. No se permitirá mostrar nada diferente a lo
entregado.

## Cómo se elige al ganador

El jurado puntúa sobre 100. Lo que más pesa es qué tan bien responden la
pregunta problema y qué datos adicionales traen para enriquecer el
análisis.

| **Criterio**                     | **Puntos** | **Qué mira el jurado**                                                                                                                                                                       |
|----------------------------------|------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Respuesta a la pregunta problema | 30         | Responde **ambas** preguntas: qué afectaciones generó el sismo y qué factores reducen el impacto de las réplicas en población, infraestructura y servicios. Conectadas y visibles en el mapa |
| Datos externos                   | 25         | Fuentes citadas, pertinentes para Cali y bien cruzadas con los edificios. Aportan algo que los datos base no dicen                                                                           |
| Calidad del análisis             | 20         | Hallazgos concretos, cifras que se rastrean hasta sus tablas gold y límites de los datos reconocidos                                                                                         |
| Presentación de resultados       | 15         | Mapa claro en 30 segundos, tres diapositivas ordenadas y una sustentación clara dentro de los 5 minutos                                                                                      |
| Arquitectura de las capas        | 10         | Decisiones justificadas en bronze, silver y gold                                                                                                                                             |

**Los datos externos son la clave.** Los datos base muestran dónde hubo
daño; las fuentes externas ayudan a explicar por qué y qué hacer ante
las réplicas. Para que sumen, tienen que pasar tres pruebas:

- **Ser verdaderos:** vienen de una fuente identificable y la citan.
- **Tener sentido:** cubren Cali, son recientes y realmente se pueden
  cruzar con los edificios.
- **Aportar valor:** cambian o enriquecen la respuesta a la pregunta. Un
  dato que solo decora el mapa no suma.

Un dato falso, inventado o sin sentido para el análisis **resta
puntos**, igual que una conclusión que los datos no sostienen. Un solo
cruce bien hecho vale más que varios superficiales.

| **Puesto**  | **Premio**    |
|-------------|---------------|
| 1.er puesto | \$500.000 COP |
| 2.º puesto  | \$300.000 COP |
| 3.er puesto | \$200.000 COP |

Además, habrá premios para los participantes.

## Entregable

Cada equipo envía **un correo** a **marcelasabogue@ieee.org**, **a más
tardar a las 5:00 p. m. del viernes 13**. Mañana sustentarán, en 5
minutos, únicamente con lo que entreguen.

**Asunto:** `databridgehack: grupoX` (cambien X por el nombre o número
de su equipo)

**El correo trae cinco cosas:**

1.  **Captura de sus tablas.** Una captura de Catalog donde se vean las
    tablas bronze, silver y gold con el nombre de su equipo, como en
    este ejemplo.

![Imagen](media/rId32.png)

2.  **Decisiones en silver y en gold.** Qué realizaron en cada capa y
    por qué, en máximo 200 palabras.

3.  **Respuesta a las dos preguntas.** Qué afectaciones generó el sismo
    y qué factores reducen el impacto de las réplicas, en máximo 500
    palabras.

4.  **Sus fuentes externas.** Una lista corta con el nombre, el enlace y
    qué aportó cada una. No cuenta dentro de las palabras de los textos.

5.  **Una presentación de 3 diapositivas**, en PowerPoint o PDF:

    - **Diapositiva 1, la arquitectura:** las decisiones que tomaron en
      bronze, silver y gold, y por qué.
    - **Diapositiva 2, la respuesta a las preguntas:** qué afectaciones
      encontraron y qué factores reducen el impacto de las réplicas, con
      datos.
    - **Diapositiva 3, el mapa:** el pantallazo del mapa y cómo lo
      hicieron: qué eligieron mostrar, por qué y cómo ayuda a responder
      las preguntas.

**Importante:** el sábado solo se presenta lo que enviaron. No se
permitirá mostrar nada diferente a lo entregado.
