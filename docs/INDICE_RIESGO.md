# Índice de riesgo ante réplicas

> Borrador. Los pesos y categorías se revisan el viernes con los datos reales; cada cambio va a la tabla de decisiones de `BITACORA.md`.
> Código: `calcular_indice()` en `notebooks/00_pipeline.py`.

## Qué mide

Para cada edificio, **qué tan urgente es inspeccionarlo antes de la próxima réplica**. No mide si el edificio es seguro: los datos son satelitales y solo sirven para priorizar.

## Explicación en 30 segundos (para el jurado)

> "Cada edificio recibe un puntaje de 0 a 1 que suma seis factores: qué tanto daño se ve desde el satélite, cuánto amplifica su suelo justo la vibración a la que ese edificio es sensible, qué tan alto es, cuánta gente hay alrededor, qué tan lejos está del hospital más cercano y si sus escombros podrían tapar una vía principal. El daño pesa más porque es lo único observado; los otros cinco dicen cuánto empeora la situación si una réplica lo termina de tumbar. Probamos seis combinaciones de pesos, incluida una sin suelo, y comparamos el ranking."

## Componentes

Todos normalizados a 0..1 (1 = más urgente). Para que un valor atípico no aplaste al resto, se recortan los percentiles 1 y 99 antes de normalizar.

| Componente | Peso | Cómo se calcula | Por qué |
|---|---|---|---|
| `c_danio` | 30 % | Severidad del `Estado_Estructural`: escombros 1,0, techo desaparecido 0,7, sin cambio aparente 0,1 (los datos no traen probabilidad; `Indice_Escombros` tiene daño en las dos colas) | Es el único dato observado del daño. Va primero porque un edificio ya dañado es el que más puede colapsar con una réplica. |
| `c_suelo` | 15 % | Factor de amplificación de su microzona (INGEOMINAS-DAGMA 2005, funciones de GEM TREQ) en el período propio del edificio, T ≈ pisos/10 s, leído para 0,23 g en roca | La misma sacudida daña distinto según el suelo. En Cali el suelo amplifica hasta ~2 veces los períodos largos, los de edificios de 15 a 25 pisos (resonancia). Ver `docs/INFORME_SISMO.md`, caps. 5 y 8. |
| `c_altura` | 15 % | `NPISOS` normalizado | Más pisos = más masa que cae, más ocupantes y mayor alcance de los escombros. |
| `c_exposicion` | 15 % | Edificios a menos de 100 m (proxy de población) | Sin datos de población por manzana disponibles, la densidad construida aproxima cuántas personas quedan expuestas. |
| `c_acceso_salud` | 10 % | Distancia al hospital o clínica más cercano (OSM) | Si hay heridos, la lejanía a salud aumenta el impacto. Pesa menos porque es la medida menos confiable (OSM etiqueta como hospital muchas IPS pequeñas). |
| `c_bloqueo_via` | 15 % | 1 si tiene alta prob. de escombros y está a menos de su altura (pisos × 3 m) de una vía principal | Responde a "servicios urbanos": escombros sobre una vía principal cortan el paso de ambulancias y bomberos. |

**Faltantes:** si a un edificio le falta un componente, su peso se reparte entre los que sí tiene (ni se castiga ni se premia el faltante). Los edificios **sin dato satelital** reciben la categoría propia *"Sin dato: verificar en terreno"*, porque no sabemos nada de su daño.

## Categorías de prioridad

| Prioridad | Regla |
|---|---|
| Muy alta | 5 % de índice más alto |
| Alta | siguiente 10 % |
| Media | siguiente 25 % |
| Baja | resto |
| Sin dato: verificar en terreno | sin información satelital |

Se usan percentiles (no cortes fijos) porque el objetivo es ordenar a quién inspeccionar primero con recursos limitados.

## Por comuna

`gold_comunas` ordena las comunas por el **percentil 90 del índice** (no por el promedio): una comuna con muchos edificios sanos y un grupo muy crítico no debe quedar escondida por el promedio. También reporta % de alta probabilidad de escombros, % sin dato, centros de salud y bomberos dentro de la comuna y edificios que podrían bloquear vías.

## Sensibilidad

`sensibilidad()` compara el ranking base con cinco escenarios de pesos: sin suelo (el borrador anterior), pesos iguales, solo daño y altura, énfasis en servicios y énfasis en población. Reporta la correlación de Spearman y qué porcentaje del top 50 se mantiene.

Con los datos ficticios de prueba: Spearman entre 0,78 y 0,97; el top 50 se mantiene entre 28 % y 66 % (sin suelo: 0,89 y 60 %). Los datos ficticios no tienen relación real con el suelo, así que esto solo prueba que el cálculo funciona. **TODO-VIERNES:** reemplazar por los valores reales y comentarlos (si un escenario cambia mucho el top, decir cuál factor manda).

## Limitaciones a decir en voz alta

- Datos satelitales: priorizan, no certifican seguridad.
- Suelo con resolución de ~750 m: la capa vectorial de la IDESC no está disponible (portal caído desde el 21-oct-2026), así que cada edificio toma la microzona del punto más cercano de la grilla de GEM TREQ. Cerca de los bordes entre microzonas puede quedar en la vecina.
- Las funciones de amplificación son modelos estadísticos, no mediciones de esta sacudida, y T ≈ pisos/10 es una regla práctica.
- Población aproximada por densidad de edificios, no por censo.
- OSM etiqueta como "hospital" muchas IPS pequeñas: la distancia a salud es optimista.
- El umbral de bloqueo de vía (pisos × 3 m) es una regla práctica, no un modelo de caída de escombros.
