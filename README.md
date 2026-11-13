# DataBridge Hack · Réplicas en Cali

Solución del equipo para la **DataBridge Hack** (IEEE Computer Society, Colombia Chapter), 13 y 14 de noviembre de 2026.

> **Pregunta:** ¿Qué afectaciones generó el sismo del 10 de agosto en Cali y qué factores contribuyen a reducir el impacto de las réplicas sobre la población, la infraestructura y los servicios urbanos?

**Enfoque:** pipeline bronze/silver/gold en Databricks, cruces espaciales con OpenStreetMap, USGS y la microzonificación sísmica (GEM TREQ), un índice de riesgo ante réplicas explicable y con prueba de sensibilidad, y un visor web propio con recorrido guiado.

## Estado

| Parte | Estado |
|---|---|
| Contraste entre ciudades y sismos | Fuentes candidatas revisadas en `docs/FUENTES.md`: 20 entradas de catálogo y 38 referencias, con alcance y pendientes de verificación; integración pendiente |
| Análisis exploratorio de bronce | 17 notebooks individuales y una síntesis en `analisis_bronce/`; resultados locales guardados en `.ipynb` y HTML |
| Fuentes externas (GEM TREQ: exposición, suelo, licuación; USGS: ShakeMap, estaciones, réplicas; OSM) | Descargadas y recortadas en `data/externos/`, con una ficha por fuente en `docs/FUENTES.md` |
| Capa plata | 16 tablas por entidad y relaciones, control de calidad y validación local; contrato en `docs/PLATA.md` |
| Funciones espaciales | Listas, con autoprueba |
| Notebooks bronze/silver/gold | Ajustados a los datos oficiales y a los nombres de la guía (`workspace.default.<capa>_icesixuao_<contenido>`) |
| Simulación con datos ficticios | Pasa de extremo a extremo |
| Corrida local con datos oficiales | Pasa (`scripts/correr_local.py`) |
| Visor | Lee los GeoJSON generados con datos reales (no se suben al repo) |
| Guion y preguntas del jurado | Borrador con cifras por llenar |

## Estructura

```
CLAUDE.md / AGENTS.md     Reglas para asistentes de IA (bitácora, commits, README)
DataBridge_Hack_Guia_Evento_2.md   Guía oficial del evento (datos, entrega, criterios del jurado)
docs/
  DataBridge_Hack_Plan_Maestro.md   Guía oficial, estrategia y plan general
  PLAN_VIERNES.md                   EMPEZAR AQUÍ: estrategia, pendientes y paso a paso del viernes
  GUIA_DATABRICKS.md                Paso a paso de Databricks para principiantes
  BITACORA.md                       Aportes y decisiones del equipo (con su razón)
  PLATA.md                          Contrato de tablas, reglas de cruces, calidad y reproducción
  INDICE_RIESGO.md                  Componentes, pesos y justificación del índice
  FUENTES.md                        Fuentes, revisión de las 20 entradas y 38 referencias, cobertura y pendientes
  GUION_PRESENTACION.md             Guion de 5 a 7 min y respuestas al jurado
  ENTREGA.md                        Borrador del correo: textos de 200 y 500 palabras, fuentes y 3 diapositivas
  INFORME_SISMO.md                  Informe de investigación previa (suelo, profundidad, Venezuela, casos)
notebooks/                Para importar en Databricks (Workspace → Import)
  00_utils_espacial.py    Funciones espaciales + autoprueba
  00_pipeline.py          Configuración y funciones compatibles de silver/gold (COLS, pesos)
  00_silver.py            Contrato de plata, tablas por entidad, cruces auditables y calidad
  01_bronze.py            Carga cruda de edificios y capas externas
  02_silver.py            Tablas bronze → 16 tablas plata tipadas y validadas
  03_gold.py              Índice, ranking, sensibilidad, SQL clave y exportación al visor
scripts/
  descargar_osm.py        Descarga las capas de OSM a data/externos/
  descargar_externos.py   Descarga y recorta GEM (exposición, licuación) y USGS (ShakeMap, estaciones, réplicas)
  simular_pipeline.py     Corre el pipeline en local con edificios ficticios (no pisa el mapa real)
  correr_plata.py         Materializa y valida solo plata en data/oficiales/plata/ (Parquet privado)
  correr_local.py         Plata nueva → gold en data/oficiales/salidas/ y mapa en visor/data/
analisis_bronce/          EDA independiente del pipeline: notebooks por dataset, ejecutor y soporte
  notebooks/             Notebooks fuente, sin salidas ni registros oficiales
  ejecutados/            Notebooks con salidas y HTML para visualizar (fuera de git)
  resultados/            Perfiles JSON, figuras y registro local de ejecución (fuera de git)
analisis_plata/           Notebook de validación de plata y ejecutor; HTML/IPYNB guardados privados
tests/test_silver.py      Pruebas del contrato con datos sintéticos y fuentes públicas
data/
  externos/               Fuentes externas públicas recortadas a Cali: OSM, USGS y GEM (detalle en docs/FUENTES.md)
  oficiales/              Datos del evento (Datosprediales.json): NO se suben (están en .gitignore)
visor/                    MapLibre GL JS + deck.gl, sin build
  data/                   GeoJSON que lee el visor; edificios y comunas con datos reales no se suben
  vendor/                 Librerías locales para funcionar sin internet
```

## Cómo correr

**Visor** (necesita servidor local, no abre con doble clic):

```bash
cd visor
python -m http.server 8000
# abrir http://localhost:8000
```

Sin internet funciona igual, con fondo plano en lugar del mapa base.

**Pipeline en local** (requiere `pip install geopandas`):

```bash
python notebooks/00_utils_espacial.py   # autoprueba de funciones espaciales
python scripts/simular_pipeline.py      # pipeline completo con datos ficticios
python scripts/correr_plata.py          # solo plata: tablas y reporte en data/oficiales/plata/
python scripts/correr_local.py          # plata + gold con datos oficiales de data/oficiales/
python scripts/descargar_osm.py         # volver a bajar capas de OSM (borra antes el archivo a actualizar)
python scripts/descargar_externos.py    # volver a bajar GEM y USGS (~80 MB)
```

**Databricks:** ver `docs/GUIA_DATABRICKS.md` (paso a paso desde cero) y `docs/PLAN_VIERNES.md`.

**Análisis exploratorio de bronce:**

```bash
/home/nicolas/venv_global/bin/python analisis_bronce/ejecutar.py
# Un dataset: agregar --solo 04_osm_salud
# Abrir analisis_bronce/ejecutados/index.html para ver las salidas guardadas.
```

Usa el kernel Jupyter `venv_global` (puede cambiarse con `--kernel`). Requiere
GeoPandas, pandas, SciPy, Matplotlib, osmium, nbformat, nbclient y nbconvert.
El EDA lee `data/oficiales/Datosprediales.json`, cuya huella se conserva en el perfil.
Si la entrega llega a `data/Datosprediales.json`, se copia a esa ruta privada sin
transformarla. Ambas rutas están excluidas de Git.

**Capa plata:** contrato en `docs/PLATA.md`. Conserva lotes sin imputación y GEM
como cruce por cercanía según la decisión del equipo, con empates y reutilización
visibles. Ocupantes asignados no equivalen a población única. Pisos observados
y estimados se guardan por separado. La ejecución local no publica Delta remoto.

```bash
/home/nicolas/venv_global/bin/python analisis_plata/ejecutar.py
# Abrir analisis_plata/ejecutados/01_validacion_plata.html
/home/nicolas/venv_global/bin/python -m pytest tests/test_silver.py analisis_bronce/test_analisis.py -q
```

## Reglas importantes

- Los datos de edificios vienen de **imágenes satelitales**: sirven para priorizar, no para declarar una edificación segura o insegura.
- Los datos oficiales del evento **no se redistribuyen**: van en `data/oficiales/` y nunca se suben al repo, igual que el mapa generado con ellos.
- Cada aporte y decisión se documenta en `docs/BITACORA.md`.
