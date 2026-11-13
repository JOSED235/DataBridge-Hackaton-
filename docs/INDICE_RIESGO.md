# Índice de riesgo ante réplicas

> Borrador. Los pesos y categorías se revisan el viernes con los datos reales; cada cambio va a la tabla de decisiones de `BITACORA.md`.
> Código: `calcular_indice()` en `notebooks/00_pipeline.py`.

## Qué mide

Para cada edificio, **qué tan urgente es inspeccionarlo antes de la próxima réplica**. No mide si el edificio es seguro: los datos son satelitales y solo sirven para priorizar.

## Explicación en 30 segundos (para el jurado)

> "Cada edificio recibe un puntaje de 0 a 1 que suma cinco factores: qué tanto daño se ve desde el satélite, qué tan alto es, cuánta gente hay alrededor, qué tan lejos está del hospital más cercano y si sus escombros podrían tapar una vía principal. El daño pesa más porque es lo único observado; los otros cuatro dicen cuánto empeora la situación si una réplica lo termina de tumbar. Probamos cinco combinaciones de pesos y el ranking se mantiene."

## Componentes

Todos normalizados a 0..1 (1 = más urgente). Para que un valor atípico no aplaste al resto, se recortan los percentiles 1 y 99 antes de normalizar.

| Componente | Peso | Cómo se calcula | Por qué |
|---|---|---|---|
| `c_danio` | 35 % | Promedio de probabilidad de escombros y severidad del `Estado_Estructural` | Es el único dato observado del daño. Va primero porque un edificio ya dañado es el que más puede colapsar con una réplica. |
| `c_altura` | 20 % | `NPISOS` normalizado | Más pisos = más masa que cae, más ocupantes y mayor alcance de los escombros. |
| `c_exposicion` | 15 % | Edificios a menos de 100 m (proxy de población) | Sin datos de población por manzana disponibles, la densidad construida aproxima cuántas personas quedan expuestas. |
| `c_acceso_salud` | 15 % | Distancia al hospital o clínica más cercano (OSM) | Si hay heridos, la lejanía a salud aumenta el impacto. |
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

`sensibilidad()` compara el ranking base con cuatro escenarios de pesos: pesos iguales, solo daño y altura, énfasis en servicios y énfasis en población. Reporta la correlación de Spearman y qué porcentaje del top 50 se mantiene.

Con los datos ficticios de prueba: Spearman entre 0,83 y 0,97; el top 50 se mantiene entre 48 % y 70 %. **TODO-VIERNES:** reemplazar por los valores reales y comentarlos (si un escenario cambia mucho el top, decir cuál factor manda).

## Limitaciones a decir en voz alta

- Datos satelitales: priorizan, no certifican seguridad.
- Sin microzonificación sísmica: la capa de la IDESC no estaba disponible (portal caído desde el 21-oct-2026). El tipo de suelo sería el factor siguiente a agregar.
- Población aproximada por densidad de edificios, no por censo.
- OSM etiqueta como "hospital" muchas IPS pequeñas: la distancia a salud es optimista.
- El umbral de bloqueo de vía (pisos × 3 m) es una regla práctica, no un modelo de caída de escombros.
