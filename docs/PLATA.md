# Capa plata: contrato y ejecución

## Decisiones vigentes

Esta implementación continúa desde `9e14ab3` y conserva los cambios del equipo
posteriores a la publicación del EDA:

- `6203cab`: precisión WKT completa y top de sensibilidad con desempate por ID.
- `9e14ab3`: lotes fuera del ranking de inspección, categoría propia para verificar;
  exposición GEM mantenida como cruce por cercanía, sin llave catastral.
- Empates GEM: sumar ocupantes y valor; tomar los demás atributos del candidato
  con más ocupantes, con desempate por ID. La relación completa queda auditable.

La decisión posterior sobre GEM sustituye la propuesta del EDA de dejarlo fuera
del enriquecimiento predial hasta resolver correspondencia. Sus límites se
conservan: determinismo no demuestra identidad predial. Esta capa no modifica
los pesos de oro ni calibra causalidad entre suelo, altura y daño.

## Arquitectura

`notebooks/00_silver.py` contiene las transformaciones compartidas.
`02_silver.py` lee las tablas bronze de Databricks y publica las tablas siguientes
como `workspace.default.silver_icesixuao_<nombre>`. La lectura de amplificación acepta los nombres originales del CSV y los
normalizados por `01_bronze` para Delta (`SA(0.1)` / `SA_0.1`), incorporados
en el remoto `e4af152`. La configuración de equipo,
catálogo, unidades y constantes heredadas permanece en `00_pipeline.py` y
`00_utils_espacial.py`.

En local, `scripts/correr_plata.py` lee los archivos equivalentes, comprueba sus
SHA-256 antes/después y genera Parquet en `data/oficiales/plata/`. No modifica
bronze ni genera el mapa. `scripts/correr_local.py` usa esta misma transformación
antes de ejecutar oro y exportar el mapa. El simulador anterior conserva sus
funciones de compatibilidad; no es el ejecutor de este contrato nuevo.

## Tablas

| Nombre | Unidad y llave | Contenido |
|---|---|---|
| `predios` | Una fila oficial, `id` = OBJECTID normalizado | Originales, tipos, geometría reparada, pisos, estado satelital, cruces y calidad |
| `territorios` | Entidad OSM, `id` = tipo:osm_id | Comunas y barrios separados, código, nombre y geometría |
| `servicios` | Entidad por fuente OSM, `id` = fuente:osm_id | Salud, bomberos, policía y educación; urgencias y faltantes explícitos |
| `vias` | Tramo OSM, `id` | Jerarquía, longitud métrica, restricciones etiquetadas |
| `sitio_grilla` | Coordenada GEM, `id` | Microzona y Vs30 del modelo; no una medición por predio |
| `amplificacion` | `(ampcode, nivel_roca_g, imt, periodo_s)` | Funciones PGA/SA, factor, sigma y referencia Vs30 |
| `exposicion_gem` | Edificio modelado, `id` original GEM | Uso, época, ocupantes, valor y probabilidades de tipología; precisión del extracto |
| `sitio_licuacion_ladera` | Coordenada GEM, `id` | Categoría de susceptibilidad, unidad geológica y pendiente original |
| `shakemap` | Nodo, `id` | MMI, PGA/PSA en %g y conversiones en g, PGV en cm/s, evento |
| `observaciones` | Red:código, `id` | Tipo instrumental/macrosísmico, valores originales; insumos de ShakeMap |
| `eventos` | Evento USGS, `id` | Unión de catálogos, fecha UTC, escala, profundidad en km y procedencia |
| `eventos_origen` | `(id_evento, fuente)` | Participación de cada evento en cada catálogo y actualización |
| `cruces_gem` | `(id_predio, id_gem)` | Todos los vecinos a distancia mínima ≤15 m, ocupantes/valor, empate, selección y reutilización |
| `cruces_territoriales` | `(id_predio, id_territorio)` | Coincidencias de centroides con comunas/barrios, incluso múltiples |
| `fuentes` | `fuente` | Filas de entrada, archivo, huella del contenido bronze, corte y procesamiento |
| `calidad` | `control` | Resultado y descripción de las puertas de publicación |

Las geometrías locales/Delta se guardan como WKT de precisión completa,
EPSG:4326. Áreas y distancias se calculan en EPSG:9377. La profundidad Z de los
catálogos USGS se conserva como `profundidad_km`, sin interpretar sus kilómetros
como altitud en metros.

## Reglas de transformación

### Predios y pisos

Se mantienen `npisos_original`, `pisos_observados`, `pisos_estimados`,
`pisos_fuente`, `pisos_imputado` y `estado_predial`. `pisos` es el valor efectivo
para el modelo, que puede ser observado o estimado: para estadísticas de pisos
reales se usa `pisos_observados`.

- Cero: `sin_construccion_registrada=True`; no hay estimación, altura ni período.
- Positivo entero de 1 a 60: piso observado según el rango heredado del pipeline.
- NULL o inválido: estado desconocido. Su original y su piso observado siguen
  nulos; la estimación, si existe, se guarda aparte. Se mantiene la preferencia
  heredada por GEM y después mediana de comuna/muestra, calculada únicamente
  sobre pisos observados positivos.
- En GEM, `6-10` y `11+` se preservan como categorías y límites. Los valores 8 y
  12 son estimadores heredados explícitos, nunca pisos observados.

Se conservan categorías satelitales y registros sin dato. Se marcan discrepancias
lote/satélite y contornos repetidos con estados diferentes, sin borrar predios
ni inventar edificaciones. Se conserva WKT original y el WKT reparado.

### Uniones territoriales y proximidad

Las uniones territoriales usan centroides proyectados dentro de polígonos.
Se cuentan coincidencias; solo una coincidencia permite asignación automática.
La comuna original se conserva y solo se completa cuando falta; las discrepancias
se marcan. No se inventa barrio para una zona sin cobertura.

Las distancias de plata son del **contorno a la geometría objetivo**, no las
mediciones exploratorias de centroide del EDA. La diferencia de método queda
identificada; no deben compararse cifras como si midieran lo mismo. Se conservan
ID cercano y número de vecinos empatados. Empates en distancias de servicios se
desempatan por llave estable. Una capa objetivo vacía produce nulo, no distancia 0.

Salud conserva urgencias `si/no/sin_dato`. Ausencia de operatividad/capacidad no
significa cierre ni capacidad cero. Bomberos y policía siguen separados. La
educación es contexto, no inventario de albergues. La fuente vacía de puntos de
encuentro queda registrada con cero filas en `fuentes`.

`n_edif_100m` cuenta registros no marcados como lote alrededor del contorno
(incluye pisos desconocidos y el propio cuando aplica); no acredita población ni edificios
físicos únicos. `puede_bloquear_via` es una hipótesis heredada de altura y distancia;
queda nulo sin pisos o distancia suficiente para evaluarla.

### GEM, suelo y sacudida

Los ocupantes por predio se mantienen según la política aprobada de suma de
empates. **No son población única**: un candidato GEM puede reutilizarse entre
predios. `gem_ambiguo`, `gem_reutilizado`, `n_registros_gem` y `cruces_gem`
permiten detectarlo. Ni la proximidad ni la suma acreditan correspondencia física.

Las grillas se asignan por vecino más cercano al contorno, conservando distancia
y empates. Se limita la asignación a centroides dentro de la envolvente convexa
de cada grilla para evitar extrapolación indefinida. Esa envolvente expresa la
cobertura del extracto, no una frontera geológica ni exactitud predial.

Amplificación: nivel de referencia 0,2267 g, período aproximado pisos/10 discretizado
a los seis períodos GEM y sigma conservada. Lotes o pisos efectivos desconocidos
no reciben período. Un código o función faltante produce nulo, nunca factor 1
por defecto. `noaf` recibe los valores explícitos de su función, si existe.

ShakeMap se conserva como estimación de sacudida del evento, separado de la
amplificación del escenario GEM. PGA/PSA de %g se dividen por 100 para obtener g.
No se multiplica ShakeMap por el factor GEM. La pendiente preserva su valor y
advierte que la etiqueta de grados procede del extractor; falta confirmar el
metadato de unidad en la fuente original. Se conserva `pendiente_grados` como
alias de compatibilidad, con esa limitación documentada.

### Eventos y procedencia

Se conserva una fila por ID USGS, con la actualización más reciente; desempate
estable por fuente. No se suman archivos solapados. Principal y posteriores se
identifican temporalmente, sin declarar asociación de réplica no evaluada.
Las observaciones instrumentales se distinguen de las macrosísmicas: al alimentar
ShakeMap no constituyen una validación independiente del mismo mapa.

La huella `sha256_contenido_bronce` representa el contenido efectivamente leído;
no equivale al hash físico del archivo. En el ejecutor local se añade también
`sha256_archivo`. Databricks identifica `tabla_origen`. Cuando el extracto no
conserva corte de publicación, `corte_fuente` queda nulo y se explica en
`corte_estado`; la fecha de procesamiento no sustituye ese corte. Versión v11
identificada según el registro de descarga, no reconstruida desde el CSV.

## Calidad y ejecución

Se validan llaves, columnas snake_case, geometrías, conservación de cardinalidad,
regla de lotes, separación de estimados, unidades, dominios, probabilidades,
distancias no negativas e integridad de los cruces. Las identidades nulas o
repetidas y las geometrías no utilizables detienen la publicación; no hay borrado
silencioso ni deduplicación por nombre o contorno. Las relaciones uno-a-muchos
quedan fuera de la tabla principal.

La ejecución local produce Parquet privado y `reporte.json`. La validación visible
se guarda en `analisis_plata/ejecutados/01_validacion_plata.html` y su IPYNB.

```bash
/home/nicolas/venv_global/bin/python scripts/correr_plata.py
/home/nicolas/venv_global/bin/python analisis_plata/ejecutar.py
/home/nicolas/venv_global/bin/python analisis_plata/verificar.py
/home/nicolas/venv_global/bin/python -m pytest tests/test_silver.py analisis_bronce/test_analisis.py -q
```

Databricks: importar también `00_silver.py`, ejecutar `01_bronze`, después
`02_silver` y revisar `reporte` y `calidad`. Se usa esquema explícito, incluso
con columnas completamente nulas. Solo después ejecutar `03_gold`.
Cada tabla Delta se escribe por separado; no hay transacción global entre las
16 tablas. Esta sesión valida en local; no acredita publicación remota en Databricks.

La comparación entre ciudades sigue pendiente de materializar datos comparables;
esta plata no crea datos DANE, UNGRD u otras ciudades a partir de referencias.

Las cifras de entregas anteriores corresponden a su versión del pipeline. Deben
revalidarse en oro después de ejecutar esta plata; conservar los pesos no
garantiza cifras idénticas al corregir faltantes y precisión de los insumos.

## Evidencia de esta ejecución

Datos locales: 5.146 predios; 1.234 lotes sin imputación; 3.901 pisos observados
positivos y 11 originalmente desconocidos con estimación separada; 4 geometrías
reparadas, 2 comunas completadas y 342 discrepancias lote/señal de daño. GEM:
55 predios sin candidato, 1.667 con empate y 3.825 con algún candidato reutilizado.
Los dos catálogos aportan 144 registros de origen y 76 eventos únicos. Hay una
observación instrumental y 32 macrosísmicas. Las cifras son del inventario
analizado, no de todo Cali.

Comando desde la raíz:
`/home/nicolas/venv_global/bin/python -m pytest -q`.
Salida 0; 0 fallos, 0 errores. Salida literal:

```text
............                                                             [100%]
12 passed in 39.36s
```

Comando: `/home/nicolas/venv_global/bin/python analisis_plata/verificar.py`.
Salida 0; 0 fallos, 0 errores. Salida literal:

```text
autoprueba OK
16 tablas Parquet; 5146 predios; 65 controles válidos
16 archivos conservan SHA-256; tipos nulos conservados; resultados privados ignorados
1 notebook ejecutado; 7 celdas; 3 figuras; 0 errores
```

`/home/nicolas/venv_global/bin/python scripts/correr_local.py` terminó con código
0, incluyendo las aserciones de oro y exportación local. Salida completa privada:
`data/oficiales/plata/pipeline_completo.log`. Los pesos permanecen iguales.

`analisis_bronce/verificar.py` también terminó con código 0: conserva los
18 notebooks previos, 97 celdas, 20 figuras y las huellas de sus 17 fuentes.
Se reprodujeron en rojo y corrigieron dos fallos de integración: CRS 3D USGS
(EPSG:4979 frente a 4326) y condiciones nullable de NumPy al calcular prioridad.

La escritura Spark usa esquema explícito, pero **no se ejecutó contra Databricks**
en esta sesión: no hay sesión Spark conectada ni PySpark local. Se probó la
transformación común con entradas en formato de tablas bronze de texto y su
igualdad con archivos locales; la publicación Delta queda para `02_silver`.
