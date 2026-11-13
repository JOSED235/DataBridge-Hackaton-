# Guion de la presentación (5 a 7 minutos)

> Cifras de las tablas gold publicadas en Databricks el 13-nov-2026 (commit `41c9e0b`, 43 controles aprobados), iguales a la corrida local. Decir "ocupantes modelados", no "personas": la ocupación GEM es un modelo cruzado por cercanía. La demo sigue el **Recorrido guiado** del visor (botón en el panel izquierdo), que ya tiene estos 4 pasos.

## 0 · Apertura (20 s)

"El 10 de agosto un sismo de 7,4 con epicentro en el Chocó golpeó a Cali. Desde entonces el USGS ha registrado 67 réplicas, de hasta M 5,4. La pregunta no es solo qué se dañó, sino **dónde la próxima réplica puede hacer más daño y qué hacer primero**."

## 1 · El sismo (40 s) · paso 1 del recorrido

- Mapa regional: epicentro a 165 km de Cali, 116 km de profundidad (USGS).
- Réplicas: siguen ocurriendo; la del 12 de agosto causó nuevas afectaciones en Cali.
- Frase: "Cali está lejos del epicentro, pero un sismo profundo y grande sacude ciudades enteras sobre suelos blandos."

## 2 · Qué pasó en Cali (1 min) · paso 2

- 5.146 edificios analizados, 5,8 % con alta probabilidad de escombros, 8,5 % sin dato satelital.
- Las comunas más afectadas por índice (p90 de los edificios del ranking): 3, 9, 10, 18, 20, 19, 17. Patrón: con esta muestra no detectamos que el daño satelital se asocie con suelo, época, uso ni comuna (pruebas exploratorias con ajuste Holm). Lo que sí se concentra es la fragilidad (comuna 3: 2 de cada 3 edificios de 1985 o antes) y la ocupación (comuna 19: más de la mitad de los ocupantes modelados en edificios dañados).
- **Aviso explícito:** "Esto viene de imágenes satelitales. Sirve para priorizar, no para decir que un edificio es seguro."

## 3 · Por qué (1 min 30 s) · paso 3

- Altura: solo hay 8 edificios de 11+ pisos en el inventario; la muestra no da para afirmar que la altura marque la tasa de daño (12,5 % de escombros en 11+ frente a 5,8 % en 1-2 pisos, sin significancia comprobable). Su efecto entra por otra vía: la regla pisos × 3 m identifica 5 edificios dañados que podrían bloquear una vía principal.
- Servicios: 430 predios con daño visible (289 con construcción registrada) están a más de 1 km de urgencias; solo 23 de los 439 centros de salud de OSM declaran tenerlas.
- Salud: la comuna 20 tiene 4 edificios con alta probabilidad de escombros por cada uno de sus 5 centros de salud; la comuna 10, 2 por centro.

## 4 · Qué hacer ante réplicas (1 min 30 s) · paso 4

- Índice en 30 segundos (ver `INDICE_RIESGO.md`).
- Ranking: comunas 3, 9 y 10 primero. Top: 179 edificios de prioridad muy alta y 357 de alta para inspección inmediata.
- **Factores que reducen el impacto** (la segunda mitad de la pregunta):
  1. Inspeccionar primero donde coinciden daño visible, construcción frágil (de 1985 o antes) y ocupación: los 179 de prioridad muy alta.
  2. Despejar y vigilar las vías principales con edificios que podrían bloquearlas: mantienen abiertos los accesos de emergencia.
  3. Ubicar recursos de salud y albergues (colegios) donde hay más daño y menos cobertura.
  4. Mandar equipos de verificación a los 435 edificios sin dato satelital (8,5 %).
  5. Recuperar la infraestructura de datos abiertos de la ciudad (IDESC y datos.cali.gov.co estaban fuera de línea).

## 5 · Limitaciones (30 s)

Datos satelitales, microzonificación con resolución de ~750 m (la capa oficial está caída; usamos la grilla de GEM), ocupación modelada y cruzada por cercanía (no es población afectada), pruebas de asociación exploratorias, cifras oficiales preliminares y discordantes.

## 6 · Cierre (15 s)

"No podemos evitar la próxima réplica, pero sí decidir **dónde llegar primero**."

---

## Preguntas probables del jurado

| Pregunta | Respuesta |
|---|---|
| ¿Por qué esos pesos? | El daño observado pesa más porque es lo único medido; los demás factores dicen cuánto empeora el impacto. Probamos 7 escenarios alternativos frente al base: cambiando los pesos, el 64-72 % del top 50 se mantiene; quitando los componentes de GEM, el 56-64 %; con solo los datos oficiales, el 40 % (tabla `gold_icesixuao_resumen_sensibilidad`). |
| ¿Por qué dicen "ocupantes modelados" y no "personas"? | GEM estima ocupantes por edificio desde el censo 2018 y lo cruzamos por cercanía (≤ 15 m), no por llave catastral. Un mismo registro GEM puede quedar cerca de varios predios: sumando por predio da 6.950 en edificios dañados; contando cada registro una vez, 5.494. Ninguna de las dos es un conteo de personas afectadas. |
| ¿Entonces la época de construcción no influye en el daño? | No lo afirmamos. Con esta muestra no detectamos asociación (menor p ajustado por Holm 0,27, V de Cramér ≤ 0,06), pero un p alto no prueba ausencia de relación y las pruebas son exploratorias. Por eso la vulnerabilidad entra al índice por conocimiento sísmico (códigos de 1984 y 1998), no por esta prueba. |
| ¿Qué hicieron con los edificios sin dato? | No se borran ni se imputan como sanos: van a una categoría propia, "verificar en terreno", y se reportan por comuna. |
| ¿Qué tan confiable es el dato satelital? | Ve techos y escombros, no columnas ni fallas internas. Por eso lo usamos para priorizar inspecciones, no para certificar. |
| ¿Cómo validaron? | Contraste del ShakeMap con el acelerógrafo del SGC en Cali (RAC2C: 6,9) y con los reportes ciudadanos DYFI (6,86); 65 controles automáticos en silver y 43 en gold antes de publicar; sensibilidad con 7 escenarios alternativos de pesos y fuentes; publicación en Databricks con las mismas cifras que la corrida local; notebook de validación ejecutado sin errores. |
| ¿Por qué OSM y no datos oficiales? | El portal de datos abiertos de Cali y la IDESC están fuera de línea desde el 21-oct-2026. OSM es abierto, verificable y cubre las 22 comunas. |
| ¿Por qué el percentil 90 por comuna y no el promedio? | El promedio esconde grupos críticos dentro de comunas con muchos edificios sanos. |
| ¿Por qué pisos × 3 m para el bloqueo de vías? | Regla práctica: los escombros caen hasta una distancia del orden de la altura. Es conservadora y explicable; un modelo de caída sería el siguiente paso. |
| ¿Qué falta para usarlo de verdad? | La capa vectorial oficial de microzonificación (hoy usamos una grilla de ~750 m), población por manzana del DANE, año de construcción frente al código (1984, 1998, 2010) y validación en terreno de una muestra. |
| ¿Por qué Databricks bronze/silver/gold? | Bronze guarda lo crudo para poder rehacer todo; silver limpia y cruza; gold queda listo para decidir y para el visor. Cada paso está documentado en la tabla y en la bitácora. |
