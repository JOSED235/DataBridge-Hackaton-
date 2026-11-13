"""Audita outputs guardados y huellas sin volver a transformar ni escribir archivos."""
from pathlib import Path
import hashlib
import json
import runpy
import subprocess
import geopandas as gpd
import nbformat
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
carpeta = RAIZ / 'analisis_gold'
fuente = carpeta / 'notebooks/01_validacion_gold.ipynb'
nb = nbformat.read(fuente, as_version=4)
ejecutado = nbformat.read(carpeta / 'ejecutados' / fuente.name, as_version=4)
nbformat.validate(nb); nbformat.validate(ejecutado)
assert [c.source for c in nb.cells] == [c.source for c in ejecutado.cells]
assert all(c.execution_count is None and not c.outputs for c in nb.cells if c.cell_type == 'code')
celdas = [c for c in ejecutado.cells if c.cell_type == 'code']
assert all(c.execution_count is not None for c in celdas)
assert not [o for c in celdas for o in c.outputs if o.output_type == 'error']
recibo = json.loads((carpeta / 'ejecutados/ejecucion.json').read_text())
assert recibo['sha256_notebook_fuente'] == hashlib.sha256(fuente.read_bytes()).hexdigest()
figuras = sum('image/png' in o.get('data', {}) for c in celdas for o in c.outputs)
assert figuras == recibo['figuras'] and figuras >= 4
assert (carpeta / 'ejecutados/01_validacion_gold.html').stat().st_size > 1000
api = runpy.run_path(str(RAIZ / 'scripts/correr_oro.py'))['cargar_api']()
plata = api['leer_plata_oro'](RAIZ / 'data/oficiales/plata')
salida = RAIZ / 'data/oficiales/oro'
reporte = json.loads((salida / 'reporte.json').read_text())
tablas = {}
for nombre, n in reporte['tablas'].items():
    d = pd.read_parquet(salida / f"gold_{api['EQUIPO']}_{nombre}.parquet")
    assert len(d) == n, nombre
    if 'geom_wkt' in d:
        d = gpd.GeoDataFrame(d, geometry=gpd.GeoSeries.from_wkt(d.geom_wkt), crs=4326).drop(columns='geom_wkt')
    tablas[nombre] = d
controles = api['validar_oro'](tablas, plata)
assert tablas['calidad'].cumple.all() and controles.control.tolist() == tablas['calidad'].control.tolist()
for nombre, esperado in reporte['sha256_entradas_plata'].items():
    with (RAIZ / 'data/oficiales/plata' / nombre).open('rb') as f:
        assert hashlib.file_digest(f, 'sha256').hexdigest() == esperado, nombre
for nombre, esperado in reporte['sha256_codigo'].items():
    assert hashlib.sha256((RAIZ / 'notebooks' / nombre).read_bytes()).hexdigest() == esperado, nombre
privados = ['data/oficiales/oro', 'analisis_gold/ejecutados', 'visor/data/edificios.geojson', 'visor/data/comunas.geojson']
for ruta in privados:
    subprocess.run(['git', 'check-ignore', '-q', ruta], cwd=RAIZ, check=True)
assert not subprocess.check_output(['git', 'ls-files', '--', *privados], cwd=RAIZ)
# El pipeline completo exporta el mapa. Si está presente, contrastar sus cifras;
# correr_oro por sí solo no actualiza el mapa, por lo que una exportación vieja falla aquí.
mapa = RAIZ / 'visor/data/edificios.geojson'
if mapa.exists():
    features = json.loads(mapa.read_text())['features']
    props = pd.DataFrame([f['properties'] for f in features]).set_index('id').sort_index()
    predios = tablas['predios'].set_index('id').sort_index()
    assert props.index.equals(predios.index)
    assert props.prioridad.tolist() == predios.prioridad.tolist()
    assert props.posicion.fillna(-1).astype(int).tolist() == predios.posicion.fillna(-1).astype(int).tolist()
    assert props.pisos.fillna(-1).tolist() == predios.pisos.fillna(-1).tolist()
    assert props.indice_riesgo.tolist() == predios.indice_riesgo.tolist()
    comunas = json.loads((RAIZ / 'visor/data/comunas.geojson').read_text())['features']
    reales = tablas['comunas'].set_index('comuna')
    assert len(comunas) == len(reales)
    for f in comunas:
        v = f['properties']; fila = reales.loc[v['comuna']]
        assert v['ranking'] == fila.ranking and v['n_predios'] == fila.n_predios
        assert abs(v['indice_p90'] - fila.indice_p90) < 1e-10
    print('Mapa local consistente con predios y comunas oro')
print(f"{len(tablas)} tablas oro; {len(tablas['predios'])} predios; {len(controles)} controles válidos")
print(f"{len(reporte['sha256_entradas_plata'])} huellas plata intactas; código de ejecución coincidente; resultados privados ignorados")
print(f"1 notebook ejecutado; {len(celdas)} celdas; {figuras} figuras; 0 errores")
