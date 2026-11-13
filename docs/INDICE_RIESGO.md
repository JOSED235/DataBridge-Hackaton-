> Actualización de contrato de oro: ver `docs/ORO.md`. Los pesos siguientes se
> conservan. Las cifras de esta ficha coinciden con las tablas oro publicadas en
> Databricks el 13-nov-2026 (commit `41c9e0b`). GEM es un modelo cruzado por cercanía:
> no acredita atributos físicos de cada predio ni población única afectada.
> Las pruebas de asociación son exploratorias; un p-valor alto no demuestra
> ausencia de relación y no establece causalidad. El escenario antiguo sin
> vulnerabilidad/suelo se conserva con ese nombre; sin GEM excluye además exposición.

# Índice de riesgo ante réplicas

> Versión con los datos oficiales y las fuentes externas (13-nov-2026, 10:55). Si cambian los pesos, la decisión va a la tabla de `BITACORA.md`.
> Código: `calcular_indice()` en `notebooks/00_pipeline.py`. Fuentes: `docs/FUENTES.md`.

## Qué mide

Para cada edificio, **qué tan urgente es inspeccionarlo antes de la próxima réplica**. No mide si el edificio es seguro: los datos son satelitales y solo sirven para priorizar.

## Por qué combina daño observado y fuentes externas

La corrida exploratoria anterior no detectó asociaciones concluyentes con las características evaluadas: ni la edad, el estrato, el uso, la microzona o la licuación, ni la cercanía a otros edificios dañados (`docs/FUENTES.md`, última sección). Por edificio se comporta como una señal individual con mucho ruido posible. Por eso el índice no depende solo de él: suma lo que las fuentes externas sí saben de cada edificio, que es qué tan frágil es, cuánta gente hay dentro, en qué suelo está y qué servicios afectaría.

## Explicación en 30 segundos (para el jurado)

> "Cada edificio recibe un puntaje de 0 a 1. El satélite dice si se ve dañado, y eso pesa más, pero no basta: complementamos la señal satelital con contexto modelado y documentamos sus incertidumbres. Del modelo de exposición de GEM tomamos qué tan frágil es su tipo de construcción y cuánta gente duerme ahí; de la microzonificación, cuánto amplifica su suelo y si puede licuarse; y de OpenStreetMap, qué tan lejos está del hospital y si sus escombros tapan una vía. Con siete combinaciones de pesos distintas, el ranking se mantiene correlacionado entre 0,76 y 0,97."

## Componentes

Todos de 0 a 1 (1 = más urgente). Para que un valor atípico no aplaste al resto, se recortan los percentiles 1 y 99 antes de normalizar.

| Componente | Peso | Fuente | Cómo se calcula | Por qué |
|---|---|---|---|---|
| `c_danio` | 25 % | Datos oficiales | Severidad del `Estado_Estructural`: escombros 1,0, techo desaparecido 0,7, sin cambio aparente 0,1. Los datos no traen probabilidad, y `Indice_Escombros` tiene daño en las dos colas | Es lo único observado del sismo. Un edificio ya dañado es el que más puede colapsar con una réplica. |
| `c_vulnerabilidad` | 20 % | GEM exposición | Probabilidad de que su tipología tenga ductilidad baja o nula (`p_ductilidad_baja`) | Un edificio poco dúctil (informal o anterior al código de 1984) colapsa con menos sacudida. Es lo que más pesa en los modelos de riesgo, y en Kumamoto 2016 colapsó el 28 % de las casas anteriores al código frente al 2 % de las nuevas (`INFORME_SISMO.md`, cap. 9). |
| `c_exposicion` | 15 % | GEM exposición (censo 2018) | Ocupantes nocturnos del edificio | Responde a "población": cuántas personas quedan en riesgo. Reemplaza el proxy anterior (edificios a menos de 100 m). |
| `c_suelo` | 10 % | GEM microzonificación | Promedio de (a) la amplificación de su microzona en su período propio (T ≈ pisos/10 s) y (b) la susceptibilidad a licuación | Una réplica se amplifica o hace fallar el terreno según el suelo. Pesa poco porque en esta muestra no explica el daño observado. |
| `c_altura` | 10 % | Datos oficiales (GEM si `NPISOS` es nulo) | Pisos normalizados. En los 1.234 predios con `NPISOS` = 0 (sin construcción registrada) queda vacío y su peso se reparte | Más pisos = más masa que cae y mayor alcance de los escombros. |
| `c_acceso_salud` | 10 % | OpenStreetMap | Distancia al hospital o clínica más cercano | Si hay heridos, la lejanía a salud aumenta el impacto. |
| `c_bloqueo_via` | 10 % | OpenStreetMap | 1 si tiene escombros y está a menos de su altura (pisos × 3 m) de una vía principal | Responde a "servicios urbanos": escombros sobre la vía cortan el paso de ambulancias y bomberos. |

**Faltantes:** si a un edificio le falta un componente (por ejemplo, el 1,1 % sin edificio GEM a menos de 15 m), su peso se reparte entre los que sí tiene. Así no se castiga ni se premia el faltante. Los edificios **sin dato satelital** reciben la categoría propia *"Sin dato: verificar en terreno"*.

## Categorías de prioridad

| Prioridad | Regla | Edificios |
|---|---|---|
| Muy alta | 5 % de índice más alto | 179 |
| Alta | siguiente 10 % | 357 |
| Media | siguiente 25 % | 892 |
| Baja | resto | 2.141 |
| Sin dato: verificar en terreno | sin información satelital | 435 |
| Sin construcción registrada: verificar | `NPISOS` = 0 con dato satelital (342 con daño visible) | 1.142 |

Los percentiles se calculan solo entre los 3.569 edificios con construcción registrada y dato satelital (`en_ranking`). Los lotes quedan fuera del ranking de edificios, como pidió la organización, pero visibles en el mapa con su propia categoría.

Se usan percentiles (no cortes fijos) porque el objetivo es ordenar a quién inspeccionar primero con recursos limitados.

## Por comuna

`gold_icesixuao_comunas` ordena las comunas por el **percentil 90 del índice**, no por el promedio: una comuna con muchos edificios sanos y un grupo muy crítico no debe quedar escondida. Ranking: **3, 9, 10, 18, 20, 19, 17** (p90 calculado solo con los edificios del ranking). La comuna 3 queda primera por su vulnerabilidad: el 66,9 % de sus edificios se construyó antes de 1985. La comuna 19 tiene la mayor ocupación modelada en edificios con daño (4.008 sumando por predio; más de la mitad del total), pero no encabeza el p90 porque su construcción es más reciente.

## Sensibilidad (datos reales)

| Escenario | Spearman vs. base | Top 50 que se mantiene |
|---|---|---|
| Solo datos oficiales (daño 60 %, altura 40 %) | 0,764 | 40 % |
| Sin vulnerabilidad ni suelo | 0,876 | 64 % |
| Sin fuentes GEM (sin vulnerabilidad, suelo ni ocupantes) | 0,876 | 56 % |
| Sin suelo (borrador de la mañana) | 0,878 | 66 % |
| Pesos iguales | 0,918 | 64 % |
| Énfasis en servicios | 0,918 | 72 % |
| Énfasis en población | 0,972 | 66 % |

**Lectura:** el orden general es estable (Spearman ≥ 0,87 en todos los escenarios con fuentes externas; sensibilidad calculada sobre los edificios en ranking). **Lo que más cambia el top 50 es quitar las fuentes externas:** con solo los datos oficiales, solo el 40 % del top se mantiene. Esa es la prueba de que las fuentes externas cambian la respuesta, no solo la decoran.

## ¿Por qué no PCA, análisis factorial o un modelo?

Se probó si los siete componentes se podían resumir en menos dimensiones con un análisis de componentes principales (PCA) sobre los 3.569 edificios del ranking (`gold_icesixuao_predios`, columnas `c_*` estandarizadas; los 29 sin dato GEM se imputaron con la media solo para esta prueba; con los 3.540 completos las cifras cambian a lo sumo una décima).

| Componente principal | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| Varianza explicada | 26,2 % | 16,0 % | 15,5 % | 13,4 % | 12,9 % | 9,3 % | 6,7 % |
| Acumulada | 26,2 % | 42,2 % | 57,7 % | 71,1 % | 84,0 % | 93,3 % | 100 % |

No hay una dimensión dominante: hacen falta 4 o 5 componentes para llegar al 71-84 %. La razón está en las correlaciones entre componentes: la media de |r| fuera de la diagonal es 0,11.

| Par | r | Lectura |
|---|---|---|
| Suelo y altura | 0,43 | La más alta, y en parte por construcción: la amplificación del suelo se lee en el período del edificio (T ≈ pisos/10) |
| Vulnerabilidad y ocupantes | -0,32 | Los edificios de tipología más frágil tienen menos ocupantes modelados |
| Altura y ocupantes | 0,31 | Más pisos, más ocupantes modelados |
| Altura y vulnerabilidad | -0,26 | Los edificios con más pisos tienen tipologías menos frágiles según GEM |
| Daño observado con cualquier otro | ≤ 0,09 | El daño satelital va casi por su cuenta, coherente con la prueba de factores |

**Lectura:** las siete dimensiones son casi independientes (daño observado, fragilidad, gente, suelo, masa, acceso a salud y vía), por eso se combinan de forma aditiva con pesos explícitos y no con una síntesis automática. Comprimirlas con PCA no simplificaría nada (se necesitan 4 o 5 ejes) y destruiría la explicabilidad: hoy cada edificio dice sus motivos ("daño, vulnerabilidad, bloqueo de vía") y cada peso se puede discutir. Un modelo supervisado tampoco es viable: no hay una variable de resultado verificada en terreno por edificio para entrenarlo; usar el daño satelital como objetivo enseñaría al modelo a reproducir una señal que, con esta muestra, no se asocia con los demás factores.

## Limitaciones a decir en voz alta

- Datos satelitales: priorizan, no certifican seguridad.
- La vulnerabilidad y los ocupantes vienen de un modelo (GEM, catastro 2021 y censo 2018), no de inspección. La tipología es probabilística.
- Suelo con resolución de ~750 m. Las funciones de amplificación son modelos y T ≈ pisos/10 es una regla práctica.
- OSM etiqueta como "hospital" muchas IPS pequeñas: la distancia a salud es optimista.
- El umbral de bloqueo de vía (pisos × 3 m) es una regla práctica, no un modelo de caída de escombros.
- Los pesos son una decisión del equipo, justificada arriba y probada con la sensibilidad.
