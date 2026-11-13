# Capa oro: contrato, decisiones y reproducción

## Propósito y alcance

Oro transforma exclusivamente las 16 tablas plata en productos para priorizar
inspección, describir afectaciones y detectar información por verificar. El alcance
es el inventario entregado de Cali, no toda la ciudad. El puntaje no es probabilidad
de colapso y las categorías satelitales no certifican seguridad estructural.

Se continúa desde `80a4772`: el p90 de comuna incluye solo registros `en_ranking`.
Se conservan los siete pesos vigentes: daño 0,25; vulnerabilidad 0,20; exposición
0,15; suelo, altura, salud y vías 0,10 cada uno. Las correcciones de agregación,
tipos y nombres no constituyen calibración del modelo.

## Arquitectura

- `notebooks/00_gold.py`: transformaciones comunes y controles de oro.
- `notebooks/03_gold.py`: lee únicamente `workspace.default.silver_icesixuao_*`,
  transforma, valida y escribe `workspace.default.gold_icesixuao_*`.
- `scripts/correr_oro.py`: lee los 16 Parquet de `data/oficiales/plata/`, comprueba
  sus hashes antes/después y guarda tablas/reporte privados en `data/oficiales/oro/`.
- `scripts/correr_local.py`: materializa plata, ejecuta oro desde sus tablas y
  genera los CSV/GeoJSON de compatibilidad para el visor.
- `analisis_gold/`: notebook fuente, ejecutor y verificador de resultados guardados.

Se requiere Parquet tipado y pyarrow para el contrato local de oro. El respaldo CSV
que permite plata en otros entornos no conserva los tipos y no sustituye esta
entrada. Si solo existe CSV, el ejecutor explica cómo regenerar Parquet.

## Tablas finales

Todos los nombres llevan el prefijo `gold_icesixuao_`.

| Sufijo | Unidad y llave | Uso |
|---|---|---|
| `predios` | Registro oficial, `id` | Puntaje, prioridad, posición, aportes, pesos efectivos, motivos y banderas |
| `comunas` | Comuna, `comuna` | P90 de elegibles, volumen de inspección, cobertura y denominadores |
| `afectaciones` | `(ambito, zona, estado)` | Estado satelital en inventario/comuna, conteos, área sumada y unión |
| `servicios` | Servicio OSM, `id` | Etiquetas originales y asignaciones de predios por vecino cercano |
| `exposicion_gem` | Candidato GEM vinculado, `id` | Una fila por ID GEM, vínculos y comuna del punto GEM |
| `sensibilidad` | `(id_predio, escenario)` | Puntajes, posiciones y cambios por escenario, solo elegibles |
| `resumen_sensibilidad` | `escenario` | Spearman, coincidencia del top y cantidad realmente comparada |
| `factores` | `factor` | Prueba exploratoria, faltantes, tamaño de efecto, frecuencias y ajuste Holm |
| `grupos_factores` | `(factor, categoria)` | Tasas de señal de daño con denominador de cada grupo |
| `verificaciones` | Registro oficial, `id` | Motivos coexistentes para revisar datos, sin duplicar predios |
| `fuentes` | `fuente` | Manifiesto heredado de plata y tabla que materializa cada fuente |
| `parametros` | `parametro` | Pesos por escenario, versión, normalización y límites |
| `calidad` | `control` | Puertas de publicación y evidencia |

Cambio de contrato: la tabla `sensibilidad` anterior contenía el resumen.
Ahora el resumen está en `resumen_sensibilidad` y el detalle en `sensibilidad`.
El CSV `gold_sensibilidad.csv` conserva el resumen y el alias
`top50_coincide_%` para lectores existentes.

## Decisiones de cálculo

### Elegibilidad y explicación

`en_ranking = ~sin_dato_satelital & ~sin_construccion_registrada`.
Se mantienen los percentiles estrictos >0,95, >0,85 y >0,60 y sus categorías.
Las posiciones se ordenan por índice descendente e ID ascendente; los empates
no dependen del orden de llegada. El índice se redondea a cuatro decimales.

Por cada componente se publica `peso_efectivo_c_*` y `aporte_c_*`.
El peso efectivo es el peso base disponible dividido por la suma de pesos
base disponibles. Su producto por el componente es el aporte; la suma de aportes
reconstruye el índice antes de redondear. Se conserva `peso_base_disponible` y
`n_componentes_disponibles`, sin inventar una probabilidad de confianza.

La normalización conserva el criterio heredado: cuantiles 0,01/0,99 sobre los
valores disponibles del inventario para cada componente, luego min-max.
Los cuantiles se calculan en flotante para admitir entradas Int64 nullable;
se preservan faltantes y no se modifica la entrada.

### Predios, pisos y denominadores

Se distingue `n_predios`, `n_lotes`, `n_con_pisos_observados`,
`n_pisos_desconocidos_originales`, `n_en_ranking` y cobertura satelital.
`pisos_prom_observados` usa únicamente pisos observados. Las estimaciones siguen
visibles por predio, pero no se presentan como mediciones.

`pct_danio_entre_con_dato` usa el número con dato satelital; `pct_sin_dato` usa
todo el inventario del ámbito. El conteo de señal de daño puede incluir lotes
con discrepancia, que siguen identificados por separado. No sumar banderas
coexistentes como poblaciones disjuntas.

Se publican tanto `area_contornos_sumada_m2` como `area_union_categoria_m2` y
`area_union_inventario_m2`, calculadas en EPSG:9377. Las uniones por categoría
no son aditivas si hay solapamiento; ninguna de estas áreas equivale a área
construida por pisos o población. Los predios sin comuna permanecen en el total
y en afectaciones `sin_comuna`, sin inventar un polígono territorial.

El p90 expresa concentración de puntajes elevados; los conteos de prioridad
expresan volumen de trabajo. No se convierte el ranking en números de brigadas,
ambulancias o presupuesto sin datos de disponibilidad, capacidades y tiempos.

### Exposición GEM y servicios

Se conserva el enriquecimiento aprobado por cercanía para el índice. Su suma
por predio se llama `ocupantes_asignados_gem` y puede repetir candidatos.
La tabla `exposicion_gem` contiene una sola fila por ID candidato vinculado;
la comuna se obtiene del punto GEM, no repartiendo sus ocupantes arbitrariamente
entre predios. Si el punto coincide con varios territorios, no se asigna uno.

`n_vinculos_con_senal_danio` cuenta vínculos con predios no lote y con señal
satelital; no demuestra que el edificio GEM sea ese predio ni que sus ocupantes
estén afectados. Tampoco la suma de candidatos únicos acredita personas únicas.

Servicios conserva urgencias `si/no/sin_dato`, operatividad y capacidad originales.
Los conteos de predios cuyo servicio más cercano es ese sitio no son demanda,
capacidad ni radio de atención. Policía, bomberos y educación no se equiparan.
Las distancias siguen siendo euclidianas; no tiempos de desplazamiento.

### Sensibilidad y asociaciones

Se conservan los escenarios previos y sus parámetros. El escenario antiguo
`sin_fuentes_gem` se conserva bajo `sin_vulnerabilidad_ni_suelo`, porque seguía
usando exposición. El nuevo `sin_fuentes_gem` elimina también `c_exposicion`.
Esto evalúa los componentes GEM del índice, sin rehacer imputaciones de plata;
no equivale a reconstruir toda la cadena sin GEM.

El top usa `min(50, n_elegibles)`, y se registra el número real para no dividir
muestras pequeñas por 50. La correlación usa rangos medios de puntajes;
los desempates por ID solo definen posiciones. Con cero comparables o falta de
variación no se inventa correlación ni porcentaje.

Factores se evalúan solo entre elegibles, con faltantes contados aparte.
Se guarda chi-cuadrado sin corrección de continuidad y V de Cramér. Una tabla
sin variación no recibe p-valor; si alguna frecuencia esperada es <5 se marca
`exploratoria_frecuencias_bajas`. Holm se calcula únicamente entre las pruebas
con todas las frecuencias esperadas >=5. Se publican tasas por grupo y tamaños.

Las conclusiones no están precargadas: un p-valor alto no demuestra ausencia
de relación. La independencia espacial y entre registros no está acreditada;
las pruebas son exploratorias y no justifican causalidad ni eficacia de intervenciones.

### Compatibilidad y privacidad

Se conservan aliases de comuna: `n_edificios = n_predios`,
`pisos_prom = pisos_prom_observados`, `ocupantes_noche = ocupantes_asignados_gem` y
`ocupantes_en_edif_con_danio = ocupantes_asignados_gem_con_senal_danio`.
Los consumidores nuevos deben usar los nombres explícitos. El visor etiqueta
predios y ocupación modelada y muestra fuente de pisos y motivos de prioridad;
NULL no se transforma en piso cero, y los lotes no reciben altura ficticia.

Los derivados permanecen ignorados en Git. No se regeneran automáticamente
presentaciones o correos antiguos con cifras que aún no se han revisado.
Los pesos no cambian, pero los agregados pueden diferir al corregir denominadores.

## Ejecución y validación

Desde la raíz del repositorio:

```bash
/home/nicolas/venv_global/bin/python scripts/correr_plata.py  # si no existe plata vigente
/home/nicolas/venv_global/bin/python scripts/correr_oro.py
/home/nicolas/venv_global/bin/python analisis_gold/ejecutar.py
/home/nicolas/venv_global/bin/python -B analisis_gold/verificar.py
/home/nicolas/venv_global/bin/python -m pytest -q
```

Abrir `analisis_gold/ejecutados/01_validacion_gold.html` o el IPYNB ejecutado.
El reporte local conserva hashes físicos de los 16 Parquet de entrada y de los
cuatro módulos de transformación. Si existe el mapa local, el verificador contrasta
IDs, prioridades, posiciones, pisos e índices con las tablas oro; un mapa viejo
requiere volver a ejecutar el pipeline completo. Las huellas de archivos originales se heredan
de plata, distintas de la huella del contenido bronze.

Los controles validan identidades, conservación, elegibilidad, posiciones,
aportes, pisos, denominadores, relaciones y p90 antes de escribir. Si fallan,
no se autoriza publicación. Las tablas Delta se escriben individualmente;
no hay transacción global. Databricks debe importar también `00_gold.py` y ejecutar
la plata nueva antes de `03_gold.py`.

Esta implementación se valida en local. No acredita ejecución remota de las
nuevas tablas en Databricks. La comparación entre ciudades requiere materializar
datasets compatibles; no se genera una comparación ficticia desde referencias.
La unidad original de pendiente GEM sigue pendiente y no se usa para puntuar.

## Evidencia local

`python -m pytest -q`: 24 pruebas aprobadas, 0 fallos y 0 errores
(`24 passed in 46.58s`). Se reprodujeron en rojo y corrigieron la normalización
de enteros nullable con cuantiles decimales y el agregado de un inventario
sin comuna. También se comprueba exportación de pisos NULL sin convertirlos en cero.

El notebook guarda 7 celdas ejecutadas y 4 figuras sin errores. El verificador
independiente comprueba 13 tablas, 5.146 predios, 43 controles y las 16 huellas
de plata. El pipeline completo se ejecuta desde `scripts/correr_local.py`;
su registro privado es `data/oficiales/oro/pipeline_completo.log`.
