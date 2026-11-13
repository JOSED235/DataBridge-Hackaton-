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
| `workspace.default.silver_icesixuao_predios` | Nombre completo de una tabla: `catálogo.esquema.tabla` | `base_de_datos.tabla` |
| **Volumen** | Carpeta para archivos sueltos (GeoJSON, CSV) dentro del Catalog. Ruta: `/Volumes/workspace/default/icesixuao/` | Una carpeta compartida |
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
2. En Databricks: **Workspace** → tu carpeta de usuario → crear una carpeta `databridge` (**Create → Folder**) y hacer clic derecho **sobre esa carpeta** → Import (si se importa desde la raíz sale el error `undefined/... is not absolute`).
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

## 4. Viernes: volumen del equipo y archivos

La guía oficial exige trabajar en `workspace.default`, con un volumen y tablas con el nombre del equipo. El nombre está en `EQUIPO` de `00_pipeline` (hoy `icesixuao`); si cambia, se cambia solo ahí.

1. Abrir `01_bronze` y correr las celdas hasta la que dice `CREATE VOLUME` (incluida). Crea el volumen `workspace.default.icesixuao`.
2. Menú **Catalog** → `workspace` → `default` → **Volumes** → `icesixuao` → **Upload to this volume**. Si no aparece, refrescar el Catalog.
3. Subir **todo junto al mismo volumen**: `Datosprediales.json` (datos oficiales, de `data/oficiales/`) y los 15 archivos de `data/externos/` (`.geojson` y `.csv`).

## 5. Viernes: bronze

`01_bronze` → **Run all**. Crea `bronze_icesixuao_predios` (5.146 filas y 21 columnas, todo como texto y con los nulos tal como vienen) y una tabla `bronze_icesixuao_<capa>` por cada archivo externo. El `assert` falla si la tabla no tiene 5.146 × 21, que es lo que pide verificar la guía.

La configuración de `00_pipeline` (`COLS`, `SEVERIDAD_ESTADO`) ya está ajustada a los datos reales.

## 6. Viernes: silver y gold

1. `02_silver` → **Run all**. Revisar el `reporte`: `valores_estado_sin_mapear` debe salir `[]`, 1.245 pisos imputados (1.234 con 0 y 11 nulos), 17 geometrías reparadas y 2 comunas completadas con OSM.
2. `03_gold` → **Run all**. Revisar la sensibilidad y las 5 consultas: son las cifras del correo y de las diapositivas.
3. Para la captura del correo: **Catalog → workspace → default** con las tablas `bronze_icesixuao_*`, `silver_icesixuao_predios` y `gold_icesixuao_*` a la vista.

Plan B si Databricks falla: `python scripts/correr_local.py` da las mismas tablas gold en `data/oficiales/salidas/` y el mapa en `visor/data/`.

## 7. Viernes: llevar los datos al mapa

1. **Catalog → workspace → default → Volumes → icesixuao → salidas**.
2. Clic en `edificios.geojson` → menú **⋮** → **Download**. Igual con `comunas.geojson`.
3. Copiarlos a `visor/data/` y **borrar `visor/data/MUESTRA.txt`** si existe. Ya están en `.gitignore`: no se suben.

## 8. Viernes: Genie (preguntas en lenguaje natural)

1. Menú izquierdo → **Genie** → **New**.
2. Elegir tablas: `workspace.default.gold_icesixuao_predios` y `workspace.default.gold_icesixuao_comunas`.
3. En las instrucciones del espacio pegar:
   > "Los datos vienen de imágenes satelitales. `indice_riesgo` va de 0 a 1 (más alto = inspeccionar primero). `prioridad` puede ser Muy alta, Alta, Media, Baja o 'Sin dato: verificar en terreno'. `puede_bloquear_via` indica edificios cuyos escombros podrían bloquear una vía principal."
4. Probar con las preguntas de la guía oficial. **Siempre abrir "Show code" y revisar el SQL** antes de creer el resultado.

## 9. Problemas comunes

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

## 10. Orden de ejecución (resumen para tener a mano)

```
Hoy:      cuenta → Git folder o import → notebook "prueba" → autoprueba OK
Viernes:  01_bronze hasta CREATE VOLUME → subir Datosprediales.json + los 15 de data/externos al volumen
          → 01_bronze completo → 02_silver → 03_gold → captura del Catalog
          → descargar salidas → mapa → Genie → correo antes de las 5:00 p. m.
```
