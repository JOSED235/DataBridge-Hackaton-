# Espacio de Genie sobre las tablas oro

Genie responde en lenguaje natural sobre las tablas `gold_icesixuao_*`. Sirve para la demo ante el jurado
("pregúntele a los datos") y para comprobar cifras rápido. Las respuestas esperadas de abajo salen de las tablas oro
publicadas el 13-nov-2026 (commit `41c9e0b`). Si Genie da otra cifra, revisar su SQL antes de usarla
(regla del repo: todo SQL generado se revisa).

## Configuración

- **Nombre:** `Réplicas Cali · icesixuao`
- **Descripción:** Priorización de inspección ante réplicas del sismo del 10-ago-2026 en Cali, desde imágenes satelitales y fuentes abiertas.
- **SQL warehouse:** el serverless del workspace.
- **Tablas** (catálogo `workspace`, esquema `default`):
  `gold_icesixuao_predios`, `gold_icesixuao_comunas`, `gold_icesixuao_resumen_sensibilidad`, `gold_icesixuao_factores`,
  `gold_icesixuao_grupos_factores`, `gold_icesixuao_exposicion_gem`, `gold_icesixuao_verificaciones`,
  `gold_icesixuao_afectaciones`, `gold_icesixuao_servicios`.
  No agregar `sensibilidad` (28.552 filas de detalle) ni las tablas silver: confunden y gastan cuota.
- Antes de crear el espacio, correr la celda `comentar_oro_spark(spark)` de `03_gold`: Genie lee los comentarios de
  tablas y columnas.

## Instrucciones generales (pegar tal cual)

```text
Responde en español.
Los datos de daño vienen de imágenes satelitales: sirven para priorizar inspecciones, nunca para declarar un edificio seguro o inseguro.
indice_riesgo es una priorización relativa de 0 a 1, no una probabilidad de colapso.
Para rankings de edificios usa gold_icesixuao_predios con en_ranking = true y ordena por posicion ascendente.
Para ordenar comunas usa la columna ranking de gold_icesixuao_comunas (1 = más urgente, por indice_p90).
Los predios con sin_dato_satelital = true o sin_construccion_registrada = true no están en el ranking: van a verificación en terreno. Sin dato no significa sano.
"Daño visible" significa sev_estado >= 0.7 y sin_dato_satelital = false.
La ocupación de GEM es modelada (censo 2018) y cruzada por cercanía. Llámala "ocupantes modelados", nunca "personas afectadas".
Para sumar ocupantes sin contar dos veces un registro GEM, usa gold_icesixuao_exposicion_gem; la suma por predio (ocupantes_asignados_gem) puede repetir registros.
Las distancias son euclidianas en metros, no tiempos de viaje.
Las pruebas de gold_icesixuao_factores son exploratorias: un p alto no prueba ausencia de relación; reporta p_ajustado_holm y v_cramer.
```

## Preguntas de ejemplo (agregar como SQL de ejemplo)

| Pregunta | Respuesta esperada |
|---|---|
| ¿Qué comunas hay que inspeccionar primero? | 3, 9, 10, 18, 20, 19, 17 (p90 0,544 a 0,438) |
| ¿Cuáles son los 10 edificios más urgentes? | Puesto 1 en la comuna 19 (0,752); puestos 2 y 3 en la comuna 3 |
| ¿Cuántos edificios hay por prioridad? | Muy alta 179, Alta 357, Media 892, Baja 2.141, Sin dato 435, Sin construcción registrada 1.142 |
| ¿Cuántos ocupantes modelados hay en edificios con daño visible, sin duplicar? | 5.494 (6.950 si se suma por predio) |
| ¿Qué tan estable es el ranking si cambian los pesos? | Spearman 0,764 a 0,972; con solo datos oficiales se mantiene el 40 % del top 50 |
| ¿Cuántos predios dañados quedan a más de 1 km de urgencias, por comuna? | 430: comuna 19 211, 10 118, 20 87, 17 14 |
| ¿Por qué la comuna 19 tiene más edificios de prioridad muy alta pero no es la primera? | Tiene 75 de 179, pero el ranking usa el p90: la 3 concentra puntajes más altos; la 19 tiene más volumen (2.269 edificios en ranking) |
| ¿Qué factores se asocian con el daño satelital? | Ninguno detectado con esta muestra: menor p ajustado por Holm 0,27, V de Cramér ≤ 0,06 |

```sql
-- Comunas a inspeccionar primero
SELECT comuna, ranking, round(indice_p90, 3) AS indice_p90, n_prioridad_muy_alta, n_prioridad_alta, n_en_ranking
FROM workspace.default.gold_icesixuao_comunas ORDER BY ranking;

-- 10 edificios más urgentes
SELECT id, comuna, posicion, prioridad, round(indice_riesgo, 3) AS indice_riesgo, motivos_principales
FROM workspace.default.gold_icesixuao_predios WHERE en_ranking ORDER BY posicion LIMIT 10;

-- Edificios por prioridad
SELECT prioridad, count(*) AS predios FROM workspace.default.gold_icesixuao_predios GROUP BY prioridad ORDER BY predios DESC;

-- Ocupantes modelados en edificios con daño visible, cada registro GEM una vez
SELECT round(sum(ocupantes_noche)) AS ocupantes_modelados
FROM workspace.default.gold_icesixuao_exposicion_gem WHERE n_vinculos_con_senal_danio > 0;

-- Estabilidad del ranking
SELECT escenario, round(spearman_vs_base, 3) AS spearman, pct_top_coincide
FROM workspace.default.gold_icesixuao_resumen_sensibilidad ORDER BY spearman;

-- Predios dañados a más de 1 km de urgencias
SELECT comuna, count(*) AS predios FROM workspace.default.gold_icesixuao_predios
WHERE NOT sin_dato_satelital AND sev_estado >= 0.7 AND dist_salud_urgencias_m > 1000
GROUP BY comuna ORDER BY predios DESC;

-- Factores asociados con el daño
SELECT factor, estado_prueba, round(p_ajustado_holm, 3) AS p_holm, round(v_cramer, 3) AS v_cramer
FROM workspace.default.gold_icesixuao_factores ORDER BY p_holm;
```

## Verificación del espacio (13-nov-2026)

Espacio creado en el workspace con las 9 tablas, las instrucciones y los 7 SQL de ejemplo. Se hicieron las 8 preguntas:
6 coinciden con la respuesta esperada. En "¿qué comunas inspeccionar primero?" el SQL devuelve las 7 comunas, pero el
texto de Genie solo nombra las 5 primeras. En "¿por qué la 19 no es la primera?" la respuesta es correcta, pero no
menciona el volumen de la 19 (2.269 edificios en ranking).

## Demo ante el jurado

Hacer dos preguntas en vivo: "¿qué comunas inspeccionar primero?" y "¿cuántos ocupantes modelados hay en edificios
con daño visible?". La segunda muestra que el espacio sabe distinguir ocupación modelada de población. En la primera,
mostrar la tabla de resultado (trae las 7 comunas) y no solo el texto. Tener abierta esta tabla para comparar.
