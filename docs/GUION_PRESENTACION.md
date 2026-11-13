# Guion de la presentación (5 a 7 minutos)

> Borrador. Los `[corchetes]` se llenan el viernes con cifras reales. La demo sigue el **Recorrido guiado** del visor (botón en el panel izquierdo), que ya tiene estos 4 pasos.

## 0 · Apertura (20 s)

"El 10 de agosto un sismo de 7,4 con epicentro en el Chocó golpeó a Cali. Desde entonces ha habido [más de 70] réplicas registradas. La pregunta no es solo qué se dañó, sino **dónde la próxima réplica puede hacer más daño y qué hacer primero**."

## 1 · El sismo (40 s) · paso 1 del recorrido

- Mapa regional: epicentro a 165 km de Cali, 116 km de profundidad (USGS).
- Réplicas: siguen ocurriendo; la del 12 de agosto causó nuevas afectaciones en Cali.
- Frase: "Cali está lejos del epicentro, pero un sismo profundo y grande sacude ciudades enteras sobre suelos blandos."

## 2 · Qué pasó en Cali (1 min) · paso 2

- [N] edificios analizados, [X %] con alta probabilidad de escombros, [Y %] sin dato satelital.
- Las comunas más afectadas: [lista]. Patrón: [ej. concentración en ladera / centro antiguo].
- **Aviso explícito:** "Esto viene de imágenes satelitales. Sirve para priorizar, no para decir que un edificio es seguro."

## 3 · Por qué (1 min 30 s) · paso 3

- Factor altura: edificios de [11+] pisos tienen [Z %] de alta prob. de escombros vs. [W %] los de 1-2 pisos (consulta SQL en `03_gold`).
- Servicios: [N] edificios con alta prob. de escombros junto a vías principales; sus escombros podrían cortar el acceso de ambulancias.
- Salud: comuna [C] tiene [k] edificios con alta prob. de escombros por cada centro de salud.

## 4 · Qué hacer ante réplicas (1 min 30 s) · paso 4

- Índice en 30 segundos (ver `INDICE_RIESGO.md`).
- Ranking: comunas [1, 2, 3] primero. Top [N] edificios para inspección inmediata.
- **Factores que reducen el impacto** (la segunda mitad de la pregunta):
  1. Inspeccionar primero los edificios altos y dañados en zonas densas.
  2. Despejar y vigilar las vías principales con edificios que podrían bloquearlas: mantienen abiertos los accesos de emergencia.
  3. Ubicar recursos de salud y albergues (colegios) donde hay más daño y menos cobertura.
  4. Mandar equipos de verificación a los [Y %] edificios sin dato satelital.
  5. Recuperar la infraestructura de datos abiertos de la ciudad (IDESC y datos.cali.gov.co estaban fuera de línea).

## 5 · Limitaciones (30 s)

Datos satelitales, sin microzonificación (portal caído), población aproximada, cifras oficiales preliminares y discordantes.

## 6 · Cierre (15 s)

"No podemos evitar la próxima réplica, pero sí decidir **dónde llegar primero**."

---

## Preguntas probables del jurado

| Pregunta | Respuesta |
|---|---|
| ¿Por qué esos pesos? | El daño observado pesa más porque es lo único medido; los demás factores dicen cuánto empeora el impacto. Probamos 5 escenarios de pesos y el top se mantiene en [X %] (tabla `gold_sensibilidad`). |
| ¿Qué hicieron con los edificios sin dato? | No se borran ni se imputan como sanos: van a una categoría propia, "verificar en terreno", y se reportan por comuna. |
| ¿Qué tan confiable es el dato satelital? | Ve techos y escombros, no columnas ni fallas internas. Por eso lo usamos para priorizar inspecciones, no para certificar. |
| ¿Cómo validaron? | Contraste con lo reportado en prensa y por OPS para [comunas/sitios], revisión de casos extremos y prueba de sensibilidad. [Completar.] |
| ¿Por qué OSM y no datos oficiales? | El portal de datos abiertos de Cali y la IDESC están fuera de línea desde el 21-oct-2026. OSM es abierto, verificable y cubre las 22 comunas. |
| ¿Por qué el percentil 90 por comuna y no el promedio? | El promedio esconde grupos críticos dentro de comunas con muchos edificios sanos. |
| ¿Por qué pisos × 3 m para el bloqueo de vías? | Regla práctica: los escombros caen hasta una distancia del orden de la altura. Es conservadora y explicable; un modelo de caída sería el siguiente paso. |
| ¿Qué falta para usarlo de verdad? | Microzonificación sísmica (tipo de suelo), población por manzana del DANE y validación en terreno de una muestra. |
| ¿Por qué Databricks bronze/silver/gold? | Bronze guarda lo crudo para poder rehacer todo; silver limpia y cruza; gold queda listo para decidir y para el visor. Cada paso está documentado en la tabla y en la bitácora. |
