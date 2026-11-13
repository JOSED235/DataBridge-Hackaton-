# Índice de riesgo ante réplicas

> Versión con los datos oficiales y las fuentes externas (13-nov-2026, 10:55). Si cambian los pesos, la decisión va a la tabla de `BITACORA.md`.
> Código: `calcular_indice()` en `notebooks/00_pipeline.py`. Fuentes: `docs/FUENTES.md`.

## Qué mide

Para cada edificio, **qué tan urgente es inspeccionarlo antes de la próxima réplica**. No mide si el edificio es seguro: los datos son satelitales y solo sirven para priorizar.

## Por qué combina daño observado y fuentes externas

El daño satelital no se asocia con ninguna característica conocida: ni la edad, el estrato, el uso, la microzona o la licuación, ni la cercanía a otros edificios dañados (`docs/FUENTES.md`, última sección). Por edificio se comporta como una señal individual con mucho ruido posible. Por eso el índice no depende solo de él: suma lo que las fuentes externas sí saben de cada edificio, que es qué tan frágil es, cuánta gente hay dentro, en qué suelo está y qué servicios afectaría.

## Explicación en 30 segundos (para el jurado)

> "Cada edificio recibe un puntaje de 0 a 1. El satélite dice si se ve dañado, y eso pesa más, pero no basta: el daño satelital no sigue ningún patrón, así que le sumamos lo que sí sabemos de cada edificio. Del modelo de exposición de GEM tomamos qué tan frágil es su tipo de construcción y cuánta gente duerme ahí; de la microzonificación, cuánto amplifica su suelo y si puede licuarse; y de OpenStreetMap, qué tan lejos está del hospital y si sus escombros tapan una vía. Con siete combinaciones de pesos distintas, el ranking se mantiene correlacionado entre 0,71 y 0,97."

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
| Muy alta | 5 % de índice más alto | 253 |
| Alta | siguiente 10 % | 467 |
| Media | siguiente 25 % | 1.124 |
| Baja | resto | 2.867 |
| Sin dato: verificar en terreno | sin información satelital | 435 |

Se usan percentiles (no cortes fijos) porque el objetivo es ordenar a quién inspeccionar primero con recursos limitados.

## Por comuna

`gold_icesixuao_comunas` ordena las comunas por el **percentil 90 del índice**, no por el promedio: una comuna con muchos edificios sanos y un grupo muy crítico no debe quedar escondida. Ranking: **3, 9, 18, 10, 20, 19, 17**. La comuna 3 queda primera por su vulnerabilidad: el 66,9 % de sus edificios se construyó antes de 1985. La comuna 19 tiene la mayor cantidad de gente en edificios con daño (4.014 con construcción registrada), pero no encabeza el p90 porque su construcción es más reciente.

## Sensibilidad (datos reales)

| Escenario | Spearman vs. base | Top 50 que se mantiene |
|---|---|---|
| Solo datos oficiales (daño 60 %, altura 40 %) | 0,714 | 8 % |
| Sin fuentes GEM (sin vulnerabilidad ni suelo) | 0,852 | 50 % |
| Sin suelo (borrador de la mañana) | 0,857 | 50 % |
| Pesos iguales | 0,922 | 62 % |
| Énfasis en servicios | 0,915 | 66 % |
| Énfasis en población | 0,970 | 48 % |

**Lectura:** el orden general es estable (Spearman ≥ 0,84 en todos los escenarios con fuentes externas). **Lo que más cambia el top 50 es quitar las fuentes externas:** con solo los datos oficiales, solo el 8 % del top se mantiene. Esa es la prueba de que las fuentes externas cambian la respuesta, no solo la decoran.

## Limitaciones a decir en voz alta

- Datos satelitales: priorizan, no certifican seguridad.
- La vulnerabilidad y los ocupantes vienen de un modelo (GEM, catastro 2021 y censo 2018), no de inspección. La tipología es probabilística.
- Suelo con resolución de ~750 m. Las funciones de amplificación son modelos y T ≈ pisos/10 es una regla práctica.
- OSM etiqueta como "hospital" muchas IPS pequeñas: la distancia a salud es optimista.
- El umbral de bloqueo de vía (pisos × 3 m) es una regla práctica, no un modelo de caída de escombros.
- Los pesos son una decisión del equipo, justificada arriba y probada con la sensibilidad.
