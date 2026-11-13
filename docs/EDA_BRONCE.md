# Exploración de bronce y selección para plata

Fecha: 13-nov-2026. Responsable: Mrsasayo.

## Alcance y evidencia

Se ejecutaron análisis independientes de los **17 datasets/contenedores locales**
y después una síntesis de selección con pruebas de cruce. Las cinco capas
materializadas durante la revisión se incorporaron como notebooks 13–17.
Las fuentes que solo tienen enlaces o referencias bibliográficas siguen
pendientes de adquisición y no reciben estadísticas inventadas.

Los notebooks fuente están en `analisis_bronce/notebooks/`. Los `.ipynb` con
salidas y sus HTML están en `analisis_bronce/ejecutados/`; abrir `index.html`.
Los perfiles JSON, figuras y versiones del entorno están en
`analisis_bronce/resultados/`. Ambas carpetas de resultados son privadas y no se
versionan. Se conservan huellas SHA-256 de cada archivo analizado.

Este es EDA sobre archivos locales de bronce; no una consulta ejecutada contra
tablas Delta en Databricks. Cada notebook muestra tipos, nulos, vacíos, espacios,
llaves, distribuciones y calidad espacial cuando aplica. Las copias en memoria
permiten ensayar limpieza sin sobrescribir los crudos.

## Hallazgos por dataset

| Notebook | Filas/unidad | Hallazgo y consecuencia para plata |
|---|---|---|
| 01 Predios oficiales | 5.146 registros prediales | OBJECTID es único; ID_PREDIO tiene 1.509 nulos. Hay 1.234 lotes NPISOS=0, 3.901 registros con pisos positivos y 11 NULL. No imputar lotes. Hay 9 contornos exactamente repetidos adicionales, con 18 filas en esos grupos; 5 grupos tienen categorías satelitales diferentes. Revisar identidad/unidad antes de deduplicar. |
| 02 OSM comunas | 22 polígonos | Llaves y nombres completos/únicos; geometrías válidas y sin solape significativo. Los 5.146 centroides del inventario tienen una coincidencia única; no hay discrepancias con las comunas originales conocidas. Sirve como auxiliar territorial. |
| 03 OSM barrios | 338 polígonos | Geometrías válidas y 3 nombres repetidos. Quedan 312 predios sin barrio OSM. Hay 1,94 km² de comunas no cubiertos por barrios y 11,97 km² de barrios fuera de esas comunas. El campo `comuna` solo está diligenciado en 16 de 338 filas. No tomarlo como llave territorial suficiente. |
| 04 OSM salud | 439 puntos | 378 hospital y 61 clinic; 23 declaran urgencias, 11 las niegan y 405 no informan. Solo uno informa estado operativo. Tres pares de nombre normalizado coinciden a ≤30 m, como candidatos a revisión. Sirve para proximidad, no para capacidad sanitaria verificada. |
| 05 OSM emergencia | 63 puntos | 11 bomberos y 52 policías. Mantener funciones separadas; no sumarlos como brigadas equivalentes. |
| 06 OSM educación | 287 puntos | 234 escuelas, 27 universidades y 26 college. No acredita albergues autorizados o su capacidad. Conservar como contexto educativo. |
| 07 Puntos de encuentro | 0 registros | GeoJSON vacío interpretable. Representa ausencia de puntos mapeados en esta fuente, no inexistencia de puntos reales. No usar para asignar albergues ni recursos. |
| 08 Vías principales | 4.070 tramos | 533,21 km de geometría; sin tramos de longitud cero ni duplicación geométrica exacta. Sirve para proximidad a vías principales. No incluye toda la red local ni permite inferir tiempos de viaje. |
| 09 USGS inicial | 76 eventos | Magnitud mínima realmente observada 4,0, aunque la consulta pide ≥2,5; 66 mb, 6 mww y 4 mwr. Solo 2 eventos tienen MMI. No acredita completitud de réplicas pequeñas ni intensidad por comuna. |
| 10 GEM microzonas | 792 puntos | 11 códigos, incluido `noaf` en 475 puntos; espaciamiento mediano al vecino de 741,69 m. Los códigos tienen funciones asociadas. Vs30=800 en microzonas es referencia del esquema de amplificación, no prueba de roca medida en cada predio. |
| 11 GEM amplificación | 220 filas | Matriz completa de 11 códigos × 20 niveles, sin duplicados de clave; seis períodos SA además de PGA. Conservar factores, sigmas y metadato `vs30_ref=800`; no tratarlos como observación del evento. |
| 12 PBF Colombia | 334.335.333 bytes | Cabecera con corte `2026-11-12T21:23:05Z`. Respaldo de OSM para extracción reproducible, no evidencia independiente adicional. No se contaron todos los objetos del país. |
| 13 GEM exposición | 95.010 puntos | ID único, pero todas las coordenadas están discretizadas a cuatro decimales y hay 21.843 puntos coincidentes adicionales. Las probabilidades de vulnerabilidad son derivaciones expertas del modelo, no daño observado. Usar para contexto agregado; condicionar el cruce predial a recuperar precisión y resolver ambigüedades. |
| 14 GEM licuación/ladera | 4.166 sitios | Sin coordenadas duplicadas; categorías `vh/h/m/l/vl/n` reconocidas. Pendiente y susceptibilidad son contexto modelado; preservar metadatos de unidad y distancia de asignación. No declaran licuación o deslizamiento observados. |
| 15 ShakeMap Cali | 306 nodos | MMI 6,1–7,1; PGA 13,49–23,71 %g, equivalente a 0,1349–0,2371 g. Espaciado mediano ≈996 m. Seleccionar para sacudida local con versión, unidades y distancia al nodo. |
| 16 stationlist Cali | 33 observaciones | Una instrumental y 32 macroseísmicas. Que un campo PGA esté poblado no significa que las 33 filas sean acelerógrafos. Al ser entradas de ShakeMap, comparar contra el mapa no acredita validación independiente. |
| 17 USGS actualizado | 68 eventos | Incluye principal y 67 posteriores. Los 68 ID están también en el archivo de 76 eventos: su unión tiene 76, no 144. Cambian radio y ventana, y el nombre `replicas` no prueba asociación sismológica de todos los eventos. |

## Decisión sobre NPISOS, según aclaración del dueño

`NPISOS=0` significa **predio sin edificación registrada (lote)**. Se conserva el
cero y se crea una bandera de estado predial. Se excluyen esos lotes de los
promedios de pisos y del ranking de inspección de edificios; no se borran del
inventario y no se les inventan pisos con una mediana o con un punto GEM cercano.

La comprobación local encuentra EDIFPRED nulo o en blanco en 1.228 de los 1.234
lotes (99,51 %). Otros tres tienen `00` y tres `01`; se preservan esos códigos,
sin equipararlos automáticamente con un faltante. Los 11 NPISOS NULL siguen
siendo desconocidos. El promedio sobre los 3.901 pisos positivos es 2,097 y la
mediana es 2.

Hay 85 lotes con categoría satelital de alta probabilidad de escombros y 257 con
posible desaparición de techo. Es una discrepancia entre semántica catastral y
señal satelital que requiere revisar unidad, fecha y correspondencia espacial.
No se resuelve declarando esos predios construidos ni borrando la señal satelital.

## Defecto de fidelidad geométrica detectado y corregido

El archivo original tiene 4 geometrías inválidas. Serializarlo con el WKT
predeterminado elevaba el total a 17: 13 originalmente válidas se volvían
inválidas por el redondeo. Con `rounding_precision=-1` se preservan exactamente
las 5.146 geometrías y siguen existiendo solo las 4 inválidas de origen.

Se corrigieron las conversiones WKT de bronce, preparación geográfica y salida
para Spark en `notebooks/00_pipeline.py`. Una prueba sintética con un hueco
cercano al contorno reproduce el fallo antes del cambio y verifica precisión y
validez después. Esto explica la discrepancia con los 17 reportados antes;
no debe atribuirse a cambios de la fuente sin esta evidencia.

## Selección decidida para la siguiente plata

1. **Base:** inventario oficial de predios, distinguiendo lote, construcción
   registrada y pisos desconocidos; categorías satelitales preservadas.
2. **Servicios y acceso:** OSM salud, bomberos y vías principales, con comunas
   como soporte territorial y barrios como auxiliar condicionado a cobertura.
   No convertir proximidad en capacidad ni tiempos de respuesta.
3. **Sacudida y sitio:** ShakeMap para intensidad/aceleración local; grilla y
   funciones GEM para contexto de respuesta de sitio. Conservar por separado
   estimación de sacudida y amplificación para evitar doble conteo del suelo.
   Licuación/ladera queda como contexto condicionado a metadatos y distancia.
4. **Exposición GEM:** seleccionada para contexto agregado; el cruce por predio
   queda condicionado a precisión, unicidad y correspondencia. A ≤15 m aparecen
   55 predios sin candidato, 3.424 con un candidato más cercano único y 1.667 con
   empate. Tomar el primero reutiliza 1.348 ID GEM en varios predios. Además,
   1.211 lotes oficiales tienen candidato GEM: eso no autoriza imputarles pisos.
5. **Catálogos USGS y stationlist:** contexto y consistencia de la sacudida,
   conservando ID, ventana, escala, tipo de observación y procedencia; no
   multiplicar conteos por versiones o archivos.
6. **Fuera del núcleo operativo:** educación como contexto; puntos de encuentro
   como cobertura vacía; PBF como respaldo de extracción. No se seleccionan
   colegios como albergues ni una capa vacía como inventario real de puntos.

El criterio sigue la guía: cruces que respondan la pregunta y puedan explicarse,
con calidad y cobertura medidas. El notebook 99 incluye el contrato de tablas
plata y sus puertas de calidad. Las fuentes DANE, UNGRD/HDX, escenarios y otras
ciudades quedan como adquisiciones posteriores; no se han perfilado archivos
inexistentes ni construido un banco comparable mundial con estos datos locales.

## Límites de implementación

El EDA elige fuentes y reglas; no migra todas esas reglas a plata ni valida los
pesos del índice. El pipeline local se ejecutó como comprobación del estado
heredado y sus salidas se conservaron privadas. En la versión inicial del EDA se
imputaban los ceros. Al publicar se integró la actualización remota `8418820`,
que incorpora `sin_construccion_registrada` y evita imputar esos predios. También
hace determinista la resolución de empates GEM. Esto no acredita por sí solo
la correspondencia física de los registros; la restricción de calidad del EDA
sigue vigente. La corrección implementada en esta revisión es la fidelidad WKT;
el resto del contrato conserva el alcance descrito para la siguiente fase.

Los 435 predios sin dato satelital son 8,45 % de filas y 9,51 % del área sumada
de sus polígonos. Esa área no equivale a área construida por pisos ni a población.
La muestra solo cubre siete comunas, con 61,04 % de registros en la comuna 19.
No extrapolar sus proporciones a toda Cali.

## Verificación de la entrega

Comando: `/home/nicolas/venv_global/bin/python analisis_bronce/verificar.py`.
Código de salida: 0. Salida:

```text
18 notebooks ejecutados; 97 celdas; 20 figuras; 0 errores
17 fuentes conservan su SHA-256; notebooks fuente sin salidas; resultados privados ignorados
Archivo oficial de análisis: SHA-256 idéntico al del perfil; entrega inicial opcional
```

Regresiones: `/home/nicolas/venv_global/bin/python -m pytest analisis_bronce/test_analisis.py -q`.
Código de salida: 0; última ejecución: `2 passed in 8.52s`.
La prueba de fidelidad WKT se reprodujo antes del cambio con `1 failed, 1 passed`.
`git diff --check` terminó sin salida y con código 0. El registro por notebook
queda en `analisis_bronce/resultados/verificacion.json`.
