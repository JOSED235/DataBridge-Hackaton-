# Análisis exploratorio de bronce

Carpeta independiente del pipeline. Hay **17 notebooks individuales**, uno por
dataset/contenedor disponible en el corte de esta revisión, y un notebook final
de selección para plata. No se analizan como si existieran archivos que solo
están mencionados en la investigación.

## Ver resultados guardados

Abrir `ejecutados/index.html`. Cada enlace muestra tablas, gráficas, controles y
decisiones del dataset sin volver a ejecutar código. Cada HTML tiene al lado su
`.ipynb` ejecutado, con salidas y contadores de ejecución conservados.

`ejecutados/` y `resultados/` están excluidos de Git porque contienen análisis de
datos oficiales del evento. Los notebooks fuente en `notebooks/` no contienen
salidas ni registros oficiales.

## Orden de lectura

| Notebook | Dataset |
|---|---|
| `01_predios_oficiales` | Inventario predial del evento |
| `02_osm_comunas` | Límites de comunas OSM |
| `03_osm_barrios` | Límites de barrios OSM |
| `04_osm_salud` | Hospitales y clínicas OSM |
| `05_osm_emergencia` | Bomberos y policía OSM |
| `06_osm_educacion` | Sitios educativos OSM |
| `07_osm_puntos_encuentro` | Capa vacía de puntos mapeados OSM |
| `08_osm_vias_principales` | Tramos de vías principales OSM |
| `09_usgs_sismos` | Extracto regional USGS inicial |
| `10_gem_microzonas` | Grilla de sitio GEM |
| `11_gem_amplificacion` | Funciones de amplificación GEM |
| `12_pbf_colombia` | Cabecera, corte y extracción del PBF nacional |
| `13_gem_exposicion` | Exposición GEM recortada y derivada |
| `14_gem_licuacion_ladera` | Sitio GEM combinado para licuación y pendiente |
| `15_usgs_shakemap_cali` | Grilla ShakeMap local |
| `16_usgs_estaciones_cali` | Instrumento y observaciones macroseísmicas de stationlist |
| `17_usgs_eventos_actualizados` | Segundo extracto USGS, con radio y ventana distintos |
| `99_seleccion_para_plata` | Síntesis posterior, pruebas de cruce y selección razonada |

## Reproducir

Desde la raíz del proyecto:

```bash
/home/nicolas/venv_global/bin/python analisis_bronce/ejecutar.py
/home/nicolas/venv_global/bin/python analisis_bronce/ejecutar.py --solo 04_osm_salud
/home/nicolas/venv_global/bin/python -m pytest analisis_bronce/test_analisis.py -q
/home/nicolas/venv_global/bin/python analisis_bronce/verificar.py
```

El kernel predeterminado es `venv_global`; se puede sustituir con `--kernel`.
Se requieren pandas, GeoPandas, Shapely, pyproj, SciPy, NumPy, Matplotlib, osmium,
nbformat, nbclient, nbconvert e ipykernel. No hay descargas dentro de los EDA.
Los crudos se leen desde `data/externos/`, `data/cache/` y
`data/oficiales/Datosprediales.json`. Se calcula SHA-256 y se comprueba que no
cambió durante el perfilado. Los notebooks trabajan en copias en memoria.

El PBF recibe análisis de cabecera y trazabilidad, no un conteo completo de
todos los objetos nacionales. Las capas derivadas sí reciben perfiles de filas,
columnas, geometría y variables. El segundo catálogo USGS se solapa con el
primero: no se suman sus filas para contar sismos.

## Decisiones y límites

- `NPISOS=0` es lote sin edificación registrada, según aclaración del dueño.
  Se conserva, se excluye de promedios de altura y no se imputa desde GEM ni
  desde una mediana. Los 11 valores NULL son una categoría distinta.
- El notebook 01 documenta que el redondeo WKT creaba 13 geometrías inválidas
  adicionales. Se corrigió la serialización del pipeline con precisión completa.
- El notebook 99 decide fuentes y reglas de la siguiente plata. No constituye
  una migración de todas esas reglas al pipeline ni valida los pesos del índice.
  En la versión analizada inicialmente se imputaban los ceros. La actualización
  remota `8418820`, integrada al publicar este EDA, incorpora la bandera
  `sin_construccion_registrada` y evita imputar esos predios. El resto de las
  restricciones de calidad del EDA conserva su alcance.
- Los datos satelitales permiten priorizar e investigar discrepancias, no
  certificar seguridad de edificaciones. Las coordenadas redondeadas de GEM y
  sus empates impiden asumir correspondencia predial solo por cercanía.

Resumen de hallazgos: `docs/EDA_BRONCE.md`. Selecciones y razones registradas
también en `docs/BITACORA.md`.
