# Fuentes de datos

> Regla: antes de usar o citar una fuente, verificar que existe y dice lo que se afirma. Las cifras oficiales del sismo son preliminares; si dos fuentes no coinciden, anotar la discrepancia y cuál se eligió.

## Descargadas y verificadas (12-nov-2026)

| Fuente | Enlace | Archivo | Formato | Contenido | Estado |
|---|---|---|---|---|---|
| USGS, catálogo de sismos | [API FDSN](https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2026-08-01&endtime=2026-11-12&latitude=4.9&longitude=-76.3&maxradiuskm=300&minmagnitude=2.5) | `data/externos/usgs_sismos_2026-08.geojson` | GeoJSON | 76 sismos M ≥ 2,5 a 300 km del epicentro, 1-ago a 12-nov-2026. Principal: M7,4, 10-ago-2026 12:34 UTC (7:34 a. m. hora local), 116 km de profundidad, 4 km SSW de San José del Palmar | Descargada |
| OpenStreetMap: comunas | Overpass API (`scripts/descargar_osm.py`) | `osm_comunas.geojson` | GeoJSON | 22 comunas (admin_level 8), 122 km² en total | Descargada |
| OpenStreetMap: barrios | ídem | `osm_barrios.geojson` | GeoJSON | 338 barrios/sectores (admin_level 9) | Descargada |
| OpenStreetMap: salud | ídem | `osm_salud.geojson` | GeoJSON | 439 puntos (378 `hospital`, 61 `clinic`) | Descargada |
| OpenStreetMap: emergencia | ídem | `osm_emergencia.geojson` | GeoJSON | 11 estaciones de bomberos, 52 de policía | Descargada |
| OpenStreetMap: educación | ídem | `osm_educacion.geojson` | GeoJSON | 287 colegios y universidades (posibles albergues) | Descargada |
| OpenStreetMap: vías | ídem | `osm_vias_principales.geojson` | GeoJSON | 4070 tramos motorway/trunk/primary/secondary | Descargada |

Licencia OSM: ODbL, citar "© colaboradores de OpenStreetMap".

## Contexto del sismo (para la presentación, no para el modelo)

| Fuente | Enlace | Dato | Nota |
|---|---|---|---|
| OPS, Sitrep 1 | [PDF](https://www.paho.org/sites/default/files/2026/08/sitrep1-terremoto-colombia-agosto-20260.pdf) | 111 fallecidos y 87 heridos (corte 13:30 del 10-ago) | Preliminar. Profundidad 103 km según OPS |
| Cambio Colombia | [Nota](https://cambiocolombia.com/pais/articulo/2026/8/sismo-de-magnitud-74-con-epicentro-en-choco-se-sintio-en-gran-parte-de-colombia-que-se-sabe-hasta-ahora) | Profundidad 96 km según boletín del SGC | **Discrepancia de profundidad:** SGC 96 km, OPS 103 km, USGS 116 km. Usamos la de USGS porque es la del catálogo que descargamos. |
| Infobae | [Nota](https://www.infobae.com/colombia/2026/08/12/nuevo-temblor-en-choco-se-sintio-con-fuerza-en-cali-y-genero-nuevas-afectaciones-en-la-infraestructura/) | Réplica del 12-ago con nuevas afectaciones en Cali | Útil para el argumento "las réplicas siguen causando daño" |
| NTN24 | [Nota](https://www.ntn24.com/noticias-actualidad/nuevo-sismo-sacudio-la-region-de-choco-en-colombia-reportan-que-se-sintio-tambien-en-cali-651737) | Secuencia de más de 130 réplicas | El USGS registra menos porque su umbral es M ≥ 2,5 |

### Suelo (agregado el 13-nov-2026)

| Fuente | Enlace | Dato | Nota |
|---|---|---|---|
| GEM, proyecto TREQ (riesgo urbano de Cali) | [github.com/gem/treq-riesgo-urbano](https://github.com/gem/treq-riesgo-urbano/tree/master/Cali/Condiciones_Sitio) | Grilla de 792 puntos con la microzona sísmica (INGEOMINAS-DAGMA 2005) y funciones de amplificación del suelo por microzona, período y nivel de sacudida | Licencia CC BY-SA 4.0 (citar a GEM). Originales `site_model_uniform_grid_ampcodes.csv` y `soil_amplification_model_20210825_sigaf03.csv`, guardados como `data/externos/gem_microzonas_grilla.csv` y `gem_amplificacion_suelo.csv`. Verificado el 13-nov-2026. Dentro de las microzonas la columna `vs30` vale 800 (roca de referencia), por eso se usa el factor de amplificación y no el Vs30. |
| Informe de investigación previa del equipo | `docs/INFORME_SISMO.md` | Parámetros oficiales, comparación con Venezuela, banco de 19 casos, suelo, ondas, código y corrupción constructiva | Cada cifra cita fuente y fecha de corte; verificarla contra su fuente antes de ponerla en una diapositiva. **Discrepancia:** el informe da SGC ≈ 103 km de profundidad; arriba se anotó 96 km del boletín del SGC. Seguimos con USGS 116 km. |

**TODO-VIERNES:** si hay tiempo, buscar el balance oficial más reciente de UNGRD y SGC para la diapositiva de contexto.

## No disponibles (y por qué)

| Fuente | Enlace | Problema | Alternativa |
|---|---|---|---|
| Datos abiertos Cali | [datos.cali.gov.co](https://datos.cali.gov.co/) | Fuera de línea desde el 21-oct-2026 por "medidas de seguridad" (comunicado de la Alcaldía) | Comunas y barrios desde OSM |
| IDESC (geovisor y WFS) | [idesc.cali.gov.co](https://idesc.cali.gov.co/) | Redirige al portal de la Alcaldía; el WFS responde 404 | Microzonificación desde GEM TREQ (ver Suelo) |
| Microzonificación sísmica de Cali (capa vectorial) | [Alcaldía](https://www.cali.gov.co/dagma/publicaciones/1099/microzonificacion-sismica-cali/) | Solo como mapa (PDF); la capa vectorial vivía en la IDESC | Grilla de GEM TREQ con la microzona por punto (~750 m), usada como `c_suelo` |
| Población por manzana (DANE CNPV 2018) | geoportal del DANE | Por verificar | Densidad de edificios como proxy |

Este hallazgo sirve en la presentación: la ciudad perdió su infraestructura de datos abiertos justo cuando más se necesita, y el pipeline se armó con fuentes abiertas alternativas.

## Tabla de seguimiento (completar el viernes)

| Fuente | Enlace | Formato | Cubre Cali | Fecha | Estado | Responsable |
|---|---|---|---|---|---|---|
| Edificios (organización) | entregado en el evento | por confirmar | sí | 13-nov-2026 | pendiente | |
| | | | | | | |
