# Sustentación: sábado 14 de noviembre de 2026

Equipo icesixuao: Nicolas Zapata (Universidad Autónoma de Occidente) y José David Rodríguez Pinilla (Universidad Icesi).

Guía para prepararnos los dos. Cifras: tablas gold publicadas en Databricks el 13-nov-2026, iguales a las del correo enviado.

## 1. Logística

| Qué | Detalle |
|---|---|
| Hora y lugar | 8:00 a 11:00 a. m., Auditorio T-USACA, Universidad Santiago de Cali, sede Pampalinda (Calle 5 # 62-00) |
| Llegar | 7:30 a. m., para probar proyector, internet y audio |
| Formato | Cada equipo muestra hallazgos y recomendación ante el jurado; preparamos 5 a 7 minutos más preguntas |
| Presentación | `data/oficiales/salidas/presentacion_icesixuao.pptx` y `.pdf` (cada uno con copia en USB y en el correo enviado) |
| Mapa | https://josed235.github.io/DataBridge-Hackaton-/ |
| Dashboard | https://josed235.github.io/DataBridge-Hackaton-/dashboard.html |
| Databricks | Catalog `workspace.default`, espacio de Genie y dashboard `Réplicas Cali · icesixuao` (requieren sesión de José David) |

### Pestañas abiertas antes de empezar (en este orden)

1. Presentación en modo presentación.
2. Mapa, con zoom del navegador al 90 % y la ventana maximizada.
3. Dashboard publicado.
4. Genie en Databricks, con la sesión iniciada (solo si sobra tiempo).

Cerrar notificaciones, correo y chats. Celular en silencio.

## 2. Reparto (propuesta, ajustar en el ensayo)

| Parte | Tiempo | Quién | Por qué |
|---|---|---|---|
| Apertura | 0:20 | José David | Plantea la pregunta |
| Diapositiva 1, arquitectura | 1:15 | Nicolas | Construyó silver y gold, los controles y las pruebas |
| Diapositiva 2, respuesta | 2:15 | José David | Cifras y recomendaciones |
| Diapositiva 3 y demo del mapa | 1:30 | José David maneja el mapa, Nicolas narra | Uno habla y otro hace clic: no se pierde el hilo |
| Cierre | 0:15 | Nicolas | Frase final |
| Preguntas | resto | Técnicas (datos, Databricks, estadística, PCA): Nicolas. Recomendaciones, mapa, fuentes externas: José David | Responde quien domina el tema; el otro complementa solo si falta algo |

Total hablado: unos 5 minutos y medio, con margen para no pasar de 7.

## 3. Guion por diapositiva

### Apertura (20 s)

"El 10 de agosto un sismo de 7,4 con epicentro en el Chocó golpeó a Cali, y desde entonces el USGS ha registrado 67 réplicas de magnitud 4 o más. La pregunta no es solo qué se dañó, sino dónde la próxima réplica puede hacer más daño y qué hacer primero."

### Diapositiva 1: arquitectura (1 min 15 s)

- Bronze: el archivo oficial tal como llegó, 5.146 predios y 21 columnas como texto, más 15 capas externas. Detalle que muestra rigor: redondear la geometría al guardarla creaba 13 polígonos inválidos que no estaban en la fuente; la guardamos con precisión completa.
- Silver: llave `OBJECTID` porque `ID_PREDIO` tiene 1.509 nulos. Los 1.234 predios con `NPISOS` = 0 son lotes sin construcción registrada (lo aclaró la organización): no les inventamos pisos, pero no los borramos porque el satélite ve daño en 342. Reparamos los 4 polígonos inválidos de la fuente y cruzamos cada edificio con GEM, suelo, ShakeMap y OpenStreetMap.
- Fuentes (fila de abajo): GEM dice quién vive en cada edificio y qué tan frágil es; la microzonificación, cómo responde el suelo; el ShakeMap, cuánto se sacudió, validado con el acelerógrafo del SGC en Cali; el catálogo de réplicas, que la amenaza sigue; OpenStreetMap, los servicios.
- Gold: índice por edificio, ranking de comunas, prueba de factores y de sensibilidad. Probamos un PCA: el primer eje solo explica el 26 %, así que sumamos con pesos explícitos y cada edificio conserva sus motivos. Todo publicado en Databricks: 45 tablas con comentarios, Genie y dashboard, con 65 controles en silver y 43 en gold.

### Diapositiva 2: respuesta (2 min 15 s)

- Infraestructura: el satélite ve daño en 1.354 de los 5.146 predios (26 %): 296 con escombros y 1.058 sin techo; 342 son lotes. 435 no tienen dato, y eso no significa que estén bien.
- Población: unos 5.500 ocupantes nocturnos modelados viven en edificios con daño visible, más de la mitad en la comuna 19. Es un modelo, no un conteo de personas.
- Servicios: 626 predios dañados están a menos de 200 m de un centro de salud; 430, a más de 1 km de urgencias.
- Hallazgo: con esta muestra no detectamos que el daño satelital se asocie con época, suelo ni comuna. La Javeriana Cali explica por qué: en Cali el daño fue interior, en edificios de 3 a 6 pisos anteriores a 1984, y el satélite casi no lo ve (Copernicus vio 21 edificaciones frente a 1.538 reportes locales). Nuestro índice recupera ese grupo: es el 8,5 % del ranking y el 32 % de la prioridad muy alta.
- Qué reduce el impacto: inspeccionar primero los 179 de prioridad muy alta (99 % con daño, 69 % de 1985 o antes); empezar por la comuna 3; verificar en terreno los 435 sin dato y los 342 lotes con daño; proteger el acceso a salud y vías; a mediano plazo, reforzar lo construido hasta 1985.
- Prueba de que las fuentes externas aportan: sin ellas, solo el 40 % de los 50 más urgentes sigue en la lista.

### Diapositiva 3 y demo del mapa (1 min 30 s)

En la diapositiva (15 s): la leyenda explica cada color, punto, línea y capa; los rótulos dan comuna y puesto: C3 · #1.

Demo en el mapa (1 min 15 s), quien maneja hace exactamente esto:

1. Clic en **Recorrido guiado** y avanzar los 4 pasos sin detenerse: sismo y réplicas, daño, por qué importa, qué hacer.
2. Al terminar, en el ranking de la izquierda, clic en **Comuna 3**.
3. Pasar el cursor sobre un edificio rojo: la ficha muestra prioridad, pisos y su fuente, y los motivos.
4. En **Cola de trabajo**, elegir "Verificar en terreno: sin dato satelital" y clic en **Excel (.xlsx)**: "esta es la lista que se lleva una brigada".

Si el mapa no carga en 10 segundos, seguir con la diapositiva 3 y decir que el enlace está en el correo.

### Cierre (15 s)

"No podemos evitar la próxima réplica, pero sí decidir dónde llegar primero."

## 4. Cifras que hay que saber de memoria

| Dato | Cifra |
|---|---|
| Predios analizados | 5.146 en 7 comunas |
| Daño visible | 1.354 (26 %): 296 escombros, 1.058 sin techo; 342 son lotes |
| Sin dato satelital | 435 (8,5 %) |
| Lotes (`NPISOS` = 0) | 1.234 |
| Prioridad muy alta / alta | 179 / 357 |
| Ranking de comunas | 3, 9, 10, 18, 20, 19, 17 |
| Ocupantes modelados en edificios dañados | 5.494 sin duplicar (6.950 sumando por predio) |
| Sin fuentes externas | 40 % del top 50 se mantiene |
| Pesos | daño 25, vulnerabilidad 20, ocupantes 15, suelo, altura, salud y vías 10 cada uno |
| Factores | menor p ajustado por Holm 0,27; V de Cramér ≤ 0,06 |
| PCA | primer eje 26 %; 4 o 5 ejes para el 71-84 % |
| Validación externa | cohorte de 3 a 6 pisos hasta 1985: 8,5 % del ranking, 32 % de la muy alta |
| Sismo | M7,4, 116 km de profundidad, 165 km de Cali; MMI 6,4-7,1; RAC2C 6,9 |
| Réplicas | 67 de M ≥ 4 hasta el 3-nov; 47 en septiembre |
| Servicios | 626 dañados a 200 m o menos de salud; 430 a más de 1 km de urgencias; 23 de 439 centros declaran urgencias |
| Calidad | 65 controles en silver, 43 en gold; 45 tablas en el Catalog |

## 5. Frases a evitar

| No decir | Decir |
|---|---|
| "personas afectadas", "6.950 personas" | "ocupantes nocturnos modelados" |
| "este edificio es seguro / inseguro" | "prioridad de inspección" |
| "la época (o el suelo) no influye" | "con esta muestra no detectamos asociación" |
| "probabilidad de colapso" | "índice relativo de priorización" |
| "1.354 edificios dañados" | "1.354 predios con daño visible, 342 son lotes" |
| "sin dato = sano" | "sin dato va a verificación en terreno" |
| "la IA hizo…" | "decidimos…", "probamos…" |

## 6. Preguntas probables

Las 13 preguntas preparadas para el correo están en `docs/GUION_PRESENTACION.md` (pesos, ocupantes modelados, época, sin dato, confiabilidad satelital, validación, PCA, validación externa, OSM, p90, pisos × 3 m, qué falta, por qué Databricks). Estas son las adicionales:

| Pregunta | Respuesta corta |
|---|---|
| ¿Qué es el índice, en una frase? | Un puntaje de 0 a 1 por edificio que suma daño observado, fragilidad, ocupantes, suelo, altura, lejanía a salud y posible bloqueo de vía, con pesos explícitos; ordena a quién inspeccionar primero. |
| ¿Por qué 15 m para cruzar con GEM? | El 95 % de los edificios tiene un punto GEM a menos de 9 m; 15 m es un tope seguro. Los empates se suman de forma determinista y se publican como reutilización. |
| ¿Por qué techo desaparecido vale 0,7 y sin cambio 0,1? | Escombros es el daño más grave; perder el techo es daño estructural visible; "sin cambio aparente" no significa sin daño (la guía lo advierte), por eso no es 0. |
| ¿Por qué no usar `Indice_Escombros` directamente? | Tiene daño en las dos colas (escombros positivo, techo negativo); normalizarlo trataría el techo desaparecido como sano. |
| ¿Por qué la comuna 19 no es primera si tiene más edificios de prioridad muy alta? | Tiene 75 de 179, pero el ranking usa el p90: la 3 concentra puntajes más altos; la 19 tiene más volumen (2.269 edificios en ranking). P90 mide concentración; los conteos, carga de trabajo. |
| ¿Cómo lo usaría una brigada mañana? | Abre el mapa, elige su comuna y la cola de trabajo, descarga el Excel ordenado por prioridad con coordenadas y motivos, y sale a inspeccionar. |
| ¿Cómo usaron Databricks más allá de notebooks? | 45 tablas Delta en tres capas con prefijo de equipo, comentarios por tabla y columna, 108 controles de calidad antes de publicar, espacio de Genie con preguntas verificadas y dashboard. |
| ¿Es reproducible? | Todo está en el repositorio; la corrida local y la de Databricks dan las mismas cifras; las fuentes llevan huella SHA-256 y hay 25 pruebas automáticas. |
| ¿Por qué la microzona 4C no sube si la Javeriana la señala? | Nuestro suelo pesa 10 % y la prueba de factores no lo detectó en esta muestra. No ajustamos pesos a última hora a una sola fuente: lo dejamos documentado como siguiente paso. |
| ¿Qué harían con una semana más? | Capa vectorial oficial de microzonificación, población DANE por manzana, inspección en terreno de una muestra para calibrar los pesos, y extender a todo el inventario de Cali. |
| ¿El mapa público expone datos? | Lo publicamos con autorización de la organización solo hasta el cierre del evento; después se retira y el repositorio pasa a privado. |
| ¿Cuál es la principal limitación? | El dato satelital ve techos y escombros, no daño interior; la vulnerabilidad y los ocupantes son modelados. Por eso priorizamos, no certificamos. |

## 7. Plan B

| Si falla | Hacer |
|---|---|
| Internet | Presentación en PDF desde USB. Mapa local: `cd visor` y `python -m http.server 8000`, abrir `http://localhost:8000` (sin mapa base, las comunas dibujan la ciudad). Dashboard local: `data/oficiales/salidas/dashboard_icesixuao.html` |
| Proyector o computador | El otro integrante tiene los mismos archivos y el repo actualizado |
| Se acaba el tiempo | Saltar la demo del mapa: la diapositiva 3 ya tiene el pantallazo con leyenda |
| Genie no responde | No usarlo; mostrar el dashboard publicado |

## 8. Lista de verificación

Esta noche:

- [ ] Los dos: `git pull` del repo; tener presentación (pptx y pdf), dashboard HTML y visor local en el computador y en USB.
- [ ] Probar el visor local sin internet una vez en cada computador.
- [ ] Ensayar dos veces con cronómetro; meta: menos de 6 minutos.
- [ ] Cada uno practica en voz alta sus respuestas de la sección 6.
- [ ] Revisar que la sesión de Databricks siga iniciada.
- [ ] Cargar computadores y celulares.

Mañana:

- [ ] Llegar 7:30 a. m.; probar proyector y conexión.
- [ ] Abrir las pestañas de la sección 1 y dejar la presentación lista en la diapositiva 1.

Después del evento (lo hace José David):

- [ ] `git push origin --delete gh-pages`
- [ ] `gh api -X DELETE repos/JOSED235/DataBridge-Hackaton-/pages`
- [ ] Repositorio a privado en Settings.
