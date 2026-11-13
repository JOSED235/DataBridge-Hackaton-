# Validación ejecutada de plata

El notebook `notebooks/01_validacion_plata.ipynb` materializa las tablas,
comprueba calidad, muestra cruces y verifica la exclusión de lotes del ranking
existente. Está separado del EDA de bronce, que conserva un notebook por dataset.

Desde la raíz:

```bash
/home/nicolas/venv_global/bin/python scripts/correr_plata.py
/home/nicolas/venv_global/bin/python analisis_plata/ejecutar.py
/home/nicolas/venv_global/bin/python analisis_plata/verificar.py
/home/nicolas/venv_global/bin/python -m pytest tests/test_silver.py analisis_bronce/test_analisis.py -q
```

Abrir `ejecutados/01_validacion_plata.html` o el IPYNB ejecutado de esa carpeta.
Se guardan tablas, gráficas y comprobaciones; no se necesita volver a ejecutar
para leerlas. El kernel es `venv_global`; dependencias: GeoPandas, pandas,
NumPy, Shapely, pyarrow, Matplotlib, nbformat, nbclient, nbconvert e ipykernel.

Las tablas Parquet y el reporte están en `data/oficiales/plata/`, excluidos de
Git. Las salidas de este notebook también son privadas y están ignoradas.
Los notebooks fuente no contienen datos ni salidas del inventario oficial.

Contrato, reglas y límites: `docs/PLATA.md`. Databricks utiliza las mismas
funciones desde `notebooks/02_silver.py`, leyendo tablas bronze. La ejecución
local no publica tablas Delta en el workspace remoto.
