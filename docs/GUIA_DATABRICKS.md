# Guía de Databricks para principiantes

> Pensada para quien nunca ha usado Databricks. Sigue el orden. Lo que dice **(hoy)** conviene hacerlo antes del evento; el resto, el viernes.
> Los nombres de botones pueden variar un poco según la versión de la interfaz: si no aparece uno, buscar el más parecido o usar la barra de búsqueda de arriba.

## 0. Conceptos mínimos (2 minutos)

| Término | Qué es | Equivalente que ya conocen |
|---|---|---|
| **Workspace** | Las carpetas y notebooks de tu cuenta | El explorador de archivos |
| **Notebook** | Documento con celdas de código (Python, SQL) y texto | Un Jupyter / Google Colab |
| **Celda** | Bloque de código que se ejecuta por separado | Una celda de Colab |
| **Serverless** | El computador que ejecuta el código. En Free Edition se conecta solo, no hay que crear clúster | El "entorno de ejecución" de Colab |
| **Catalog** | Donde viven las tablas y archivos | Una base de datos con carpetas |
| `workspace.databridge.silver_edificios` | Nombre completo de una tabla: `catálogo.esquema.tabla` | `base_de_datos.tabla` |
| **Volumen** | Carpeta para archivos sueltos (GeoJSON, CSV) dentro del Catalog. Ruta: `/Volumes/workspace/databridge/externos/` | Una carpeta compartida |
| **Delta table** | El formato de tabla de Databricks. Se crea con `saveAsTable(...)` | Una tabla SQL |
| `spark` | Objeto que ya existe en todo notebook para leer y escribir tablas | La conexión a la base de datos |
| **Genie** | Chat que convierte preguntas en SQL sobre tus tablas | ChatGPT conectado a tus tablas |

Cada integrante tiene **su propio workspace**: lo que uno crea no lo ve el otro. Por eso el código vive en GitHub y cada uno lo trae a su cuenta. Las tablas finales para la entrega las genera **una sola persona** (la de datos).

## 1. Cuenta y prueba básica (hoy, 5 min)

1. Entrar a `databricks.com/learn/free-edition` → **Free Edition** (no la prueba de pago) → registrarse y verificar el correo.
2. En el menú izquierdo: **Workspace**.
3. Botón **Create → Notebook**.
4. Arriba a la derecha debe decir que está conectado a **Serverless**. Si dice "Connect", hacer clic y elegir *Serverless*.
5. En la primera celda escribir `print("hola")` y presionar **Shift + Enter** (ejecuta y pasa a la siguiente celda).
6. En la siguiente: `spark.range(5).show()`. Debe mostrar una tabla del 0 al 4.
7. Menú izquierdo → **Catalog**: debe aparecer el catálogo `workspace`.

Atajos útiles: **Shift + Enter** ejecuta la celda; **Esc + B** agrega celda abajo; **Run all** (arriba) ejecuta todo el notebook en orden.

## 2. Traer el código del repo (hoy, 10 min)

El repo es **privado**, así que hay dos caminos. El A es mejor porque luego se actualiza con un clic.

### Opción A: Git folder conectado a GitHub (recomendada)

1. En GitHub (cuenta con acceso al repo): **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**. Acceso solo al repo `DataBridge-Hackaton-`, permiso **Contents: Read and write**. Copiar el token.
   - El compañero necesita que José David lo agregue como colaborador del repo (GitHub → repo → Settings → Collaborators).
2. En Databricks: clic en tu ícono de usuario (arriba a la derecha) → **Settings → Linked accounts → Add Git credential** → proveedor **GitHub** → pegar el usuario y el token → **Save**.
3. Menú izquierdo **Workspace** → **Create → Git folder**.
4. URL: `https://github.com/JOSED235/DataBridge-Hackaton-.git` → **Create Git folder**.
5. Abrir la carpeta `notebooks/`: los `.py` aparecen como notebooks.
6. Para traer cambios nuevos del repo: abrir el Git folder → botón con el nombre de la rama (`main`) → **Pull**.

> **No subir los datos oficiales al repo desde Databricks.** Si se hace commit desde el Git folder, revisar que no aparezca nada de `data/oficial/`.

### Opción B: importar los archivos a mano

1. En GitHub: botón **Code → Download ZIP** y descomprimir.
2. En Databricks: **Workspace** → tu carpeta de usuario → crear una carpeta `databridge` (**Create → Folder**).
3. Dentro de la carpeta: menú **⋮** (o clic derecho) → **Import** → **File** → arrastrar los 5 archivos de `notebooks/` uno por uno (o un ZIP con los 5).
4. Deben quedar **los 5 en la misma carpeta**, porque `%run ./00_utils_espacial` busca el archivo al lado.

## 3. Probar que GeoPandas funciona (hoy, 5 min): el riesgo más grande

1. En la misma carpeta de los notebooks: **Create → Notebook**, nombre `prueba`.
2. Celda 1 (sola):
   ```
   %pip install geopandas --quiet
   ```
   Al terminar, Python se reinicia: es normal. Todo lo definido antes se pierde, por eso el `%pip` va siempre de primero.
3. Celda 2 (sola):
   ```
   %run ./00_utils_espacial
   ```
   Debe imprimir **`autoprueba OK`**.
4. Si sale `ModuleNotFoundError: geopandas`, volver a correr la celda 1. Si `%pip` falla del todo, avisar en la bitácora y usar el plan B de `PLAN_VIERNES.md` (cruces en local).

## 4. Viernes: crear el espacio de trabajo y subir capas externas

1. Abrir `01_bronze` y ejecutar **solo la primera celda de código** (la de `%sql CREATE SCHEMA...`). Crea:
   - el esquema `workspace.databridge`,
   - los volúmenes `externos` (entradas) y `salidas` (GeoJSON para el visor).
2. Menú **Catalog** → `workspace` → `databridge` → **Volumes** → `externos` → botón **Upload to this volume**.
   Si no lo ven, refrescar el Catalog (ícono de flecha circular).
3. Arrastrar los 7 archivos de `data/externos/` del repo (descargados de GitHub o del portátil): `osm_comunas`, `osm_barrios`, `osm_salud`, `osm_emergencia`, `osm_educacion`, `osm_vias_principales`, `usgs_sismos_2026-08` (todos `.geojson`).

## 5. Viernes: cargar los edificios (bronze)

**Seguir el paso a paso de los organizadores**: es lo único que entregan guiado. Normalmente es una de estas dos:

- **Ellos crean una tabla** (p. ej. con **+ New → Add or upload data → Create or modify table**, subiendo un CSV). Copiar su nombre completo desde el Catalog (ícono de copiar junto al nombre) y ponerlo en `TABLA_ORIGEN` de `01_bronze`.
- **Ellos dan un archivo**: subirlo al volumen `externos` (paso 4.2) y poner su ruta en `ARCHIVO_ORIGEN`, por ejemplo `/Volumes/workspace/databridge/externos/edificios.csv`. Clic derecho sobre el archivo en el Catalog → **Copy path** da la ruta exacta.

Luego **Run all** en `01_bronze`. Al final muestra:
- las primeras filas,
- el % de nulos por columna,
- los valores distintos de las columnas con pocas categorías.

**Copiar eso a `BITACORA.md`**: con eso se ajusta `00_pipeline`.

## 6. Viernes: ajustar la configuración

1. Abrir `00_pipeline` y editar el bloque `CONFIGURACIÓN`:
   - `COLS`: a la derecha, el nombre **real** de cada columna (respetar mayúsculas). Si una no existe, poner `None`.
   - `SEVERIDAD_ESTADO`: una línea por cada valor real de `Estado_Estructural`, en minúsculas y sin tildes, con su severidad de 0 a 1.
   - `ESCOMBROS_CATEGORIA`: igual, si la probabilidad de escombros viene como texto.
2. Guardar es automático. Los notebooks 02 y 03 leen esta configuración con `%run`.

## 7. Viernes: silver y gold

1. `02_silver` → **Run all**.
   - Revisar el `reporte`: `valores_estado_sin_mapear` debe salir `[]`. Si salen valores, agregarlos a `SEVERIDAD_ESTADO` y volver a correr.
   - Si sale `KeyError: Columnas no encontradas`, el mensaje lista las columnas reales: corregir `COLS`.
2. `03_gold` → **Run all**. Revisar la tabla de sensibilidad y las 3 consultas SQL (son hallazgos para el guion).
3. Ver las tablas creadas: **Catalog → workspace → databridge** → `bronze_*`, `silver_edificios`, `gold_edificios`, `gold_comunas`, `gold_sensibilidad`. La pestaña **Sample Data** muestra filas; **Details** muestra los comentarios.

## 8. Viernes: llevar los datos al visor

1. **Catalog → workspace → databridge → Volumes → salidas**.
2. Clic en `edificios.geojson` → menú **⋮** → **Download**. Igual con `comunas.geojson`.
3. Copiarlos a `visor/data/` en el portátil, reemplazando los de muestra, y **borrar `visor/data/MUESTRA.txt`**.
4. **No hacer commit de esos dos archivos con datos reales**: son derivados de datos no redistribuibles. Antes de cualquier commit del viernes, restaurar los de muestra o no incluirlos.

## 9. Viernes: Genie (preguntas en lenguaje natural)

1. Menú izquierdo → **Genie** → **New**.
2. Elegir tablas: `workspace.databridge.gold_edificios` y `workspace.databridge.gold_comunas`.
3. En las instrucciones del espacio pegar:
   > "Los datos vienen de imágenes satelitales. `indice_riesgo` va de 0 a 1 (más alto = inspeccionar primero). `prioridad` puede ser Muy alta, Alta, Media, Baja o 'Sin dato: verificar en terreno'. `puede_bloquear_via` indica edificios cuyos escombros podrían bloquear una vía principal."
4. Probar con las preguntas de la guía oficial. **Siempre abrir "Show code" y revisar el SQL** antes de creer el resultado.

## 10. Problemas comunes

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `NameError: name 'gpd' is not defined` | No se corrió el `%run` o se reinició Python | Correr de nuevo desde arriba (**Run all**) |
| `ModuleNotFoundError: geopandas` | El `%pip` no se ejecutó o se reinició la sesión | Correr la celda `%pip install geopandas` |
| `%run` dice que no encuentra el notebook | Los notebooks no están en la misma carpeta | Moverlos juntos (paso 2) |
| `TABLE_OR_VIEW_NOT_FOUND` | Nombre de tabla mal escrito o no se corrió el notebook anterior | Revisar en Catalog; correr 01 → 02 → 03 en orden |
| `PATH_NOT_FOUND` en `/Volumes/...` | No se subió el archivo o la ruta tiene otro nombre | Catalog → volumen → clic derecho → **Copy path** |
| El cómputo se pausa o dice cuota agotada | Límite diario de Free Edition | Avisar al equipo; el otro integrante corre desde su cuenta; no repetir celdas pesadas |
| Algo se cuelga más de 5 min | Celda pesada | Botón **Interrupt** (cuadrado) arriba y revisar |
| `sparkContext` o RDD no disponible | Serverless no los permite | No usarlos; usar `spark.table`, `spark.sql`, pandas |

## 11. Orden de ejecución (resumen para tener a mano)

```
Hoy:      cuenta → Git folder o import → notebook "prueba" → autoprueba OK
Viernes:  01_bronze (celda SQL) → subir data/externos al volumen → cargar edificios
          → 01_bronze completo → ajustar 00_pipeline → 02_silver → 03_gold
          → descargar salidas → visor → Genie
```
