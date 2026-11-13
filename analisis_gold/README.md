# Validación ejecutada de oro

`notebooks/01_validacion_gold.ipynb` consume plata local y ejecuta el contrato
común de oro. Muestra inventario, prioridades, afectaciones con denominadores,
contribuciones al puntaje, exposición GEM, servicios, sensibilidad, factores y
controles. Genera cuatro figuras y tablas visibles.

```bash
/home/nicolas/venv_global/bin/python analisis_gold/ejecutar.py
/home/nicolas/venv_global/bin/python -B analisis_gold/verificar.py
```

Abrir `ejecutados/01_validacion_gold.html` o su IPYNB. El kernel es `venv_global`.
Requiere las 16 tablas Parquet de `data/oficiales/plata/`, pandas, GeoPandas,
NumPy, SciPy, Shapely, pyarrow, Matplotlib, nbformat, nbclient y nbconvert.

El notebook fuente se versiona limpio; IPYNB/HTML ejecutados, figuras y recibo
son privados e ignorados. Las tablas están en `data/oficiales/oro/`.
El verificador comprueba controles y hashes sin transformar ni escribir.

Contrato: `docs/ORO.md`. La ejecución local no publica Delta remoto y la
ocupación GEM no acredita personas afectadas ni identidad catastral.
