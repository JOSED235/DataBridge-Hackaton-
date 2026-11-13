# DataBridge Hack: documento maestro del equipo

> Organizado por IEEE Computer Society, Colombia Chapter.
> Este documento reúne (1) lo que dice la guía oficial, (2) las recomendaciones técnicas y estratégicas que hemos discutido y (3) lo que falta por definir. Está pensado para ir actualizándose.
>
> **Convención:** las secciones marcadas como *Guía oficial* vienen del PDF de la organización. Las marcadas como *Propuesta* son recomendaciones nuestras, no reglas del evento.

---

## 1. Resumen ejecutivo

- **Qué es:** hackatón de datos de dos días con datos reales del sismo del **10 de agosto de 2026** (magnitud 7,4, epicentro en el Chocó) que afectó fuertemente a Cali.
- **Objetivo del equipo:** no solo participar, sino **ganar**. Queremos una solución robusta, detallada y bien argumentada, aunque el desarrollo sea en un solo día (viernes).
- **Enfoque propuesto:** pipeline en Databricks (bronze/silver/gold) + análisis espacial con fuentes externas + índice de riesgo propio y explicable + visor propio con **MapLibre GL JS + deck.gl** (con Kepler.gl como plan B) + presentación con narrativa clara y recomendaciones accionables.

---

## 2. Información del evento (Guía oficial)

| Dato | Detalle |
|---|---|
| Días | Viernes 13 y sábado 14 de noviembre de 2026 |
| Horario | Viernes 13: 8:00 a. m. a 4:00 p. m. (con receso al mediodía). Sábado 14: 8:00 a. m. a 11:00 a. m. |
| Lugar | Universidad Santiago de Cali, Sede Pampalinda (Calle 5 # 62-00, Cali) |
| Viernes | Apertura en el Auditorio T-USACA y reto en las salas 2413 y 2414, Bloque 2, piso 4 |
| Sábado | Auditorio T-USACA |
| Equipos | 2 a 3 personas |
| Premios | 1.er puesto $500.000, 2.º puesto $300.000, 3.er puesto $200.000 COP, más premios para los participantes |

### Dinámica de los dos días

| Día | Qué pasa |
|---|---|
| Viernes 13 de noviembre | **Desarrollo:** cargan los datos a Databricks, los analizan y construyen su mapa |
| Sábado 14 de noviembre (mañana) | **Presentación:** cada equipo muestra sus hallazgos y su recomendación ante el jurado |

---

## 3. La pregunta problema (Guía oficial)

> **¿Qué afectaciones generó el sismo del 10 de agosto en la ciudad de Cali y qué factores contribuyen a reducir el impacto de las réplicas sobre la población, la infraestructura y los servicios urbanos?**

### Cómo leerla (análisis nuestro)

La pregunta tiene **dos mitades**, y ganar depende de responder bien ambas:

1. **Afectaciones:** qué daño hubo y dónde (edificios, población, servicios).
2. **Factores que reducen el impacto de réplicas:** qué condiciones, acciones o recursos disminuyen el riesgo futuro. Casi todos los equipos se quedarán en la primera mitad, así que la segunda es donde podemos diferenciarnos.

Tres dimensiones de impacto que menciona la pregunta: **población**, **infraestructura** y **servicios urbanos**. Conviene que nuestro análisis toque las tres explícitamente.

### Reglas de la solución (Guía oficial)

- La solución es **abierta**: elegimos el enfoque, los datos adicionales y la herramienta de visualización.
- Lo único que se entrega paso a paso es **la carga de los datos a Databricks**.
- Se espera que organicemos el trabajo en **tres capas (bronze, silver y gold)** y lo enviemos en un **formulario de entrega**. Los organizadores compartirán los detalles durante el evento.

---

## 4. Qué se sabe de los datos

### Lo que dice la guía

- Los **datos de edificios se entregan el día del evento** (no antes).
- Pesan unos **5 MB**, así que cada integrante puede repetir la carga y trabajar en paralelo.
- Vienen de un **análisis de imágenes satelitales, no de inspecciones en terreno**. Sirven para **priorizar y plantear hipótesis**, no para declarar que una edificación es segura o insegura. **Nuestra presentación debe decirlo explícitamente.**
- **No se pueden redistribuir** fuera del evento.

### Campos y conceptos que se mencionan (por los ejemplos de Genie)

- `Estado_Estructural`
- `NPISOS` (número de pisos)
- Probabilidad de escombros (alta probabilidad vs. el resto)
- Comuna
- Edificios **sin datos satelitales** (hay faltantes)

### Pendiente de confirmar el viernes

- Formato exacto (¿CSV, GeoJSON, ambos?), sistema de coordenadas y si traen geometría (puntos o polígonos).
- Nombres reales de todas las columnas y su diccionario.
- Criterios de evaluación del jurado y detalles del formulario de entrega.

---

## 5. Requisitos y logística (Guía oficial)

- **Conocimientos:** Python básico-intermedio (idealmente pandas) y SQL básico (SELECT, WHERE, GROUP BY, JOIN). No se requiere experiencia previa en Databricks ni en SIG.
- **Equipo:** portátil con cargador y navegador actualizado. Idealmente, **cada integrante lleva el suyo**.
- **Cuenta:** cada integrante debe crear su propia cuenta de **Databricks Free Edition** (gratuita, sin tarjeta), al menos un día antes.

### Configuración de Databricks Free Edition

1. Entrar a `databricks.com/learn/free-edition` y elegir **Free Edition** (no la prueba de pago).
2. Registrarse con correo y verificar la cuenta.
3. Ir a **Workspace → Create → Notebook**.
4. No hay que crear ni encender clúster: el cómputo es *serverless* y se conecta solo. Verificar que arriba del notebook aparezca el cómputo conectado.
5. Ejecutar `print("hola")` y luego `spark.range(5).show()`.
6. Abrir **Catalog** y confirmar que se ve el catálogo `workspace`.

> **Cuota diaria:** la Free Edition tiene límites de cómputo por día. Si se agotan, el cómputo se pausa hasta el día siguiente. Evitar celdas pesadas innecesarias, y repartir bien quién ejecuta qué.

### Video introductorio (opcional pero recomendado)

"¿Qué es Databricks y por qué TODO el mundo en datos lo usa?" (unos 20 minutos). Si habla de iniciar un clúster, ignorarlo: en Free Edition no hace falta.

---

## 6. Uso de IA (Guía oficial)

- **Se puede y se recomienda** usar IA: Claude, ChatGPT, Gemini, Copilot o Databricks Genie.
- En la demo final **el jurado preguntará por qué tomamos cada decisión**. La IA puede escribir el código, pero nosotros decidimos si el resultado tiene sentido. Tenemos que poder justificar cada decisión.
- Si pedimos ideas de fuentes de datos a una IA, **verificar que la fuente exista y diga lo que la IA afirma**.

### Databricks Genie

Asistente de IA de Databricks, disponible en Free Edition. Convierte preguntas en lenguaje natural a SQL sobre nuestras tablas. Se encuentra en el menú izquierdo; se crea un espacio de Genie y se le indica qué tablas puede consultar.

Preguntas de ejemplo de la guía:

- «¿Cuántos edificios hay por Estado_Estructural?»
- «¿Qué comunas tienen más edificios con alta probabilidad de escombros?»
- «¿Cuál es el promedio de pisos (NPISOS) de los edificios con alta probabilidad de escombros frente al resto?»
- «¿Qué porcentaje de los edificios de cada comuna aparece sin datos satelitales?»

> **Genie puede equivocarse:** revisar siempre el SQL generado y que el resultado tenga sentido.

---

## 7. Equipo y habilidades

| Integrante | Habilidades |
|---|---|
| Yo | JavaScript |
| Compañero | Python, SQL, Java, lenguajes de front y back |
| (Tercer integrante, si hay) | Por definir |

**Lectura:** cubrimos todo el stack necesario. JavaScript permite ir por MapLibre + deck.gl con confianza, y Python/SQL cubren Databricks y el análisis espacial.

---

## 8. Herramientas de mapas (Guía oficial + análisis)

| Herramienta | Qué es | Sirve para | Dificultad |
|---|---|---|---|
| **QGIS** | SIG de escritorio, gratuito | Abrir GeoJSON, colorear por categoría, análisis espacial | Baja a media |
| **Kepler.gl** | Aplicación web, sin instalar | Explorar rápido con filtros, mapas de calor y 3D | Baja |
| **MapLibre GL JS + deck.gl** | Librerías WebGL en JavaScript | Visor web propio con edificios en 3D y tablero | Media a alta |
| **ArcGIS (Pro u Online)** | SIG comercial | Solo si hay licencia | Media |

### Decisión propuesta: stack en capas

| Capa | Herramienta | Para qué |
|---|---|---|
| Datos | Databricks (bronze/silver/gold) con PySpark + SQL | Es lo que piden entregar y evalúan |
| Análisis espacial | GeoPandas + Shapely (en el notebook) y/o QGIS | Cruces: edificios vs. suelo, hospitales, vías, réplicas |
| Visualización principal | **MapLibre GL JS + deck.gl** | Visor propio con 3D, capas y tablero |
| Plan B | **Kepler.gl** | Si el visor propio falla, la presentación no se cae |

**Por qué no solo Kepler.gl:** es la opción segura, pero casi todos los equipos novatos la elegirán y los mapas se parecerán. Es excelente para exploración rápida; para destacar, conviene un visor propio con narrativa.

**Por qué MapLibre + deck.gl sí es viable para nosotros:** sabemos JavaScript. El riesgo es el tiempo, por eso hay que **adelantar el esqueleto del visor antes del viernes**.

### Cómo usar cada herramienta en la práctica

**MapLibre GL JS + deck.gl**
- Mapa base con MapLibre (estilos vectoriales abiertos, por ejemplo basados en OpenStreetMap).
- Capas de deck.gl: `GeoJsonLayer` o `PolygonLayer` con extrusión por `NPISOS` (edificios 3D), coloreados por probabilidad de escombros o `Estado_Estructural`; `HeatmapLayer`/`HexagonLayer` para densidad de daño; `ScatterplotLayer` para hospitales, albergues y réplicas.
- Panel lateral/tablero: filtros por comuna y nivel de daño, indicadores clave (total de edificios, % con alta probabilidad de escombros, población expuesta), y el ranking de zonas prioritarias.
- Consumir los datos desde archivos GeoJSON/JSON exportados de la tabla *gold*.

**Kepler.gl (plan B y exploración)**
- Cargar CSV con lat/lon o GeoJSON, colorear, filtrar, extruir en 3D.
- Útil el viernes en la mañana para **explorar rápido** y descubrir patrones antes de construir el visor final.

**QGIS**
- Análisis espacial rápido: *buffers* (por ejemplo, edificios dañados a menos de 500 m de un hospital), intersecciones con zonas de suelo o amenaza, uniones espaciales por comuna.
- Exportar el resultado como GeoJSON para el visor.

**GeoPandas (en Databricks)**
- Hacer los mismos cruces de forma **reproducible y documentada** en el notebook (mejor que QGIS manual para el pipeline, porque el jurado valora el flujo).

---

## 9. Arquitectura de datos: capas bronze, silver y gold

| Capa | Contenido | Ejemplos |
|---|---|---|
| **Bronze** | Datos crudos, tal como llegan, sin modificar | Tabla de edificios original; réplicas, suelos, DANE, OSM tal como se descargaron |
| **Silver** | Datos limpios y enriquecidos | Tipos corregidos, geometrías válidas, manejo de faltantes, CRS unificado, cruces espaciales con fuentes externas |
| **Gold** | Tablas finales listas para análisis y visualización | Tabla por edificio con índice de riesgo; tabla por comuna con indicadores; lista priorizada de zonas |

Buenas prácticas para el jurado:
- Notebooks ordenados y numerados (`01_bronze`, `02_silver`, `03_gold`).
- Comentarios en tablas y columnas (diccionario de datos).
- Cada paso de limpieza justificado (por qué se eliminó, imputó o excluyó algo).
- Registrar qué porcentaje de edificios **no tiene datos satelitales** y cómo se trató.

**Flujo de datos hacia el visor:** tabla *gold* en Databricks → exportar a GeoJSON/CSV → servir al visor (MapLibre + deck.gl) o cargar en Kepler.gl.

---

## 10. Fuentes de datos externas

**Guía oficial:** no es obligatorio, pero es lo que más puede subir el análisis. Los datos base muestran **dónde** hay daño; las otras fuentes permiten explicar **por qué** y **qué hacer ante réplicas**.

Criterios para elegir una fuente (de la guía):
- ¿Qué necesito saber para responder la pregunta que los edificios no me dicen?
- ¿Quién publica el dato y es confiable?
- ¿Cubre Cali, es reciente y lo puedo poner en un mapa o cruzar con los edificios?
- **Anotar siempre la fuente** (enlace).

| Necesidad | Fuente sugerida | Uso en el análisis |
|---|---|---|
| Sismos y réplicas | USGS, Servicio Geológico Colombiano (SGC) | Mapa de réplicas, magnitud, profundidad, distancia a zonas dañadas |
| Suelo y ciudad | Alcaldía de Cali y datos abiertos | Microzonificación sísmica, tipo de suelo, amplificación |
| Población y territorio | DANE | Población por comuna/manzana, vulnerabilidad social, densidad |
| Servicios y vías | OpenStreetMap | Hospitales, bomberos, albergues, red vial, accesos de emergencia |
| Daños reportados | Informes oficiales y prensa confiable | Contraste con nuestros resultados |

> Las cifras oficiales son **preliminares y a veces no coinciden entre sí**. Documentar discrepancias y qué fuente se eligió.

### Tabla de seguimiento de fuentes

Movida a `docs/FUENTES.md`, con las fuentes ya descargadas y verificadas. **Ojo:** datos.cali.gov.co y la IDESC están fuera de línea desde el 21-oct-2026; comunas, barrios, servicios y vías se tomaron de OpenStreetMap. La microzonificación sísmica no está disponible como capa.

---

## 11. Estrategia para ganar (Propuesta)

### 11.1. Responder las dos mitades de la pregunta
- **(a) Afectaciones:** dónde y cuánto daño, en población, infraestructura y servicios.
- **(b) Factores que reducen el impacto de réplicas:** qué características (suelo, altura, densidad, cercanía a servicios, redundancia vial) se asocian con menos riesgo y qué intervenciones priorizar.

### 11.2. Explicar el porqué, no solo el dónde
Cruzar el daño con variables externas: tipo de suelo, altura/pisos, densidad de edificios, población y vulnerabilidad, cercanía a hospitales y vías, réplicas registradas.

### 11.3. Índice de riesgo propio, transparente y explicable
Un puntaje por edificio y por comuna que combine, por ejemplo:

- Probabilidad de escombros (dato base)
- Altura / número de pisos
- Tipo de suelo o amplificación sísmica
- Población expuesta
- Distancia a servicios de emergencia y a vías de acceso

Reglas: pesos justificados, fácil de explicar en 30 segundos, con **análisis de sensibilidad** (qué pasa si cambian los pesos). El jurado va a preguntar por qué cada decisión.

### 11.4. Conclusiones accionables
- Lista priorizada de zonas/edificios para **inspección en terreno** ante réplicas.
- Vías y accesos de emergencia que podrían quedar bloqueados por escombros.
- Comunas con alto daño y poca cobertura de servicios cercanos.
- Recomendaciones concretas (qué haría la Alcaldía con esto, en qué orden).

### 11.5. Rigor y honestidad
- Decir explícitamente que los datos vienen de **imágenes satelitales** y sirven para priorizar, no para declarar seguridad.
- Mostrar limitaciones: edificios sin datos, cifras oficiales discordantes, sesgos posibles.
- Fuentes citadas con enlace.

### 11.6. Visor propio con narrativa
- Edificios en 3D por pisos, coloreados por riesgo.
- Capas activables: réplicas, hospitales, vías, suelo, población.
- Tablero con filtros por comuna y ranking de zonas prioritarias.
- Un recorrido guiado ("storytelling") que lleve al jurado del problema a la recomendación.

### 11.7. Presentación de 5 a 7 minutos (estructura sugerida)
1. **Contexto y pregunta** (30 s)
2. **Qué pasó en Cali** (hallazgo principal con mapa)
3. **Por qué pasó** (factores explicativos con fuentes externas)
4. **Qué hacer ante réplicas** (índice de riesgo y priorización)
5. **Recomendaciones y limitaciones**
6. **Cierre:** una frase que se recuerde

Preparar respuestas a preguntas probables del jurado: por qué esos pesos, por qué esa fuente, qué pasa con los edificios sin datos, qué tan confiable es el dato satelital, cómo se validó.

---

## 12. Reparto de roles (Propuesta, ajustar)

| Rol | Responsabilidades | Perfil natural |
|---|---|---|
| **Datos** | Carga a Databricks, bronze/silver/gold, limpieza, integración de fuentes externas | Python/SQL |
| **Análisis espacial** | Cruces con GeoPandas/QGIS, índice de riesgo, validación y sensibilidad | Python |
| **Visualización y presentación** | Visor MapLibre + deck.gl, tablero, guion y demo | JavaScript |

Con dos personas, repartir así: uno lleva **datos + análisis**, el otro **visualización + presentación**, y ambos cruzan revisión del índice de riesgo y del guion.

---

## 13. Plan de trabajo

### 13.1. Antes del evento (esta semana)

- [ ] Confirmar equipo (2 a 3 personas).
- [ ] Ver el video introductorio de Databricks.
- [ ] Crear cuenta de Databricks Free Edition **cada integrante** y verificar `print("hola")` y `spark.range(5).show()`.
- [ ] Confirmar que se ve el catálogo `workspace` en Catalog.
- [ ] Ubicar **Genie** en el menú y leer qué es.
- [ ] Probar abrir un GeoJSON en QGIS y/o Kepler.gl.
- [x] Investigar y **descargar** fuentes externas (OSM y réplicas listas; suelo y DANE no disponibles). Ver `docs/FUENTES.md`.
- [x] Armar el **visor** (MapLibre + deck.gl) con datos de muestra: `visor/`.
- [x] Escribir funciones de cruce espacial en GeoPandas probadas con datos de ejemplo: `notebooks/00_utils_espacial.py`.
- [x] Definir un borrador del índice de riesgo: `docs/INDICE_RIESGO.md`.
- [x] Preparar los notebooks bronze/silver/gold: `notebooks/` (probados en local con datos ficticios).
- [x] Guion de presentación y respuestas al jurado: `docs/GUION_PRESENTACION.md`.
- [x] Plan paso a paso del viernes: `docs/PLAN_VIERNES.md`.
- [ ] Llevar portátil con cargador y saber cómo llegar a la Sede Pampalinda (Calle 5 # 62-00).

### 13.2. Viernes 13 (8:00 a. m. a 4:00 p. m., con receso al mediodía)

Cronograma **propuesto** (ajustar según lo que digan los organizadores):

| Franja | Actividad |
|---|---|
| Apertura | Escuchar detalles del formulario de entrega y criterios del jurado. Anotarlos. |
| Primera hora | Cargar datos a Databricks (cada integrante). Revisar columnas, tipos, geometría y CRS. Armar **bronze**. |
| Mañana | Exploración (SQL, Genie, Kepler.gl). Limpieza y **silver**. Integrar fuentes externas ya descargadas. |
| Mediodía | Receso. Decidir hallazgos principales y definir el índice de riesgo. |
| Primera parte de la tarde | **Gold**: tablas por edificio y por comuna, índice de riesgo. Exportar a GeoJSON y conectar el visor. |
| Final de la tarde | Pulir el visor, escribir el guion, enviar el **formulario de entrega**. Ensayar la presentación al menos una vez. |

> Dejar un margen: enviar el formulario con tiempo y no esperar a la última hora.

### 13.3. Sábado 14 (8:00 a. m. a 11:00 a. m.)

- Llegar temprano, probar proyección y conexión.
- Tener el visor **funcionando sin internet crítico** (o con captura/video de respaldo) y Kepler.gl como plan B.
- Presentar y responder preguntas del jurado.

---

## 14. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Se agota la cuota de cómputo de Databricks | Evitar celdas pesadas, repartir ejecuciones, trabajar con la tabla *gold* ya agregada |
| El visor propio no queda a tiempo | Esqueleto adelantado + Kepler.gl como plan B |
| Formato de datos inesperado | Revisar CRS/geometría en la primera hora; funciones de cruce probadas con ejemplos |
| Fuentes externas no cruzan bien con los edificios | Descargarlas antes y validar cobertura de Cali y CRS |
| Fuentes con cifras contradictorias | Documentar discrepancia y criterio de elección |
| Genie o la IA generan SQL/código erróneo | Revisar siempre el SQL y validar resultados con sentido común |
| El jurado pregunta "por qué" y no sabemos justificar | Registrar decisiones y su razón mientras trabajamos |
| Falla de internet o del equipo en la presentación | Capturas, video de respaldo y archivos locales |

---

## 15. Checklist oficial antes del evento (Guía oficial)

- [ ] Tengo un equipo confirmado de 2 a 3 personas.
- [ ] Vi el video introductorio de Databricks.
- [ ] Mi cuenta de Databricks Free Edition está activa.
- [ ] Ejecuté `print("hola")` en un notebook y funcionó.
- [ ] Exploré las herramientas de mapas y tengo claro cuáles me gustaría usar.
- [ ] Probé abrir un archivo GeoJSON en alguna de ellas.
- [ ] Ubiqué Genie en el menú de Databricks y leí qué es.
- [ ] Investigué al menos una fuente externa y anoté su enlace.
- [ ] Leí la pregunta problema y pensé qué datos adicionales podrían ayudar.
- [ ] Llevo el portátil con cargador.
- [ ] Confirmé mi inscripción y sé cómo llegar a la Sede Pampalinda (Calle 5 # 62-00).

---

## 16. Preguntas abiertas

- ¿Quién es el tercer integrante (si lo hay) y qué rol toma?
- ¿Qué enfoque principal elegimos: infraestructura, población o servicios urbanos (o una combinación)?
- ¿Cuál es el formato real de los datos de edificios y qué columnas traen?
- ¿Cuáles son los criterios del jurado y cómo es el formulario de entrega?
- ¿Qué fuentes externas son realmente descargables y cruzables con Cali?
- ¿Qué pesos y variables componen el índice de riesgo?

---

## 17. Bitácora de decisiones (completar durante el evento)

> El jurado preguntará por qué tomamos cada decisión. La bitácora de aportes y decisiones vive en `docs/BITACORA.md`.

---

## 18. Notas y enlaces

- Guía original: `DataBridge_GeoHack_Guia_Previa.pdf`
- Databricks Free Edition: `databricks.com/learn/free-edition`
- Video: "¿Qué es Databricks y por qué TODO el mundo en datos lo usa?" (20:08)
- Recordatorio: **no redistribuir los datos fuera del evento.**
