"""Ejecuta el notebook de validación y conserva IPYNB/HTML privados."""
from pathlib import Path
import hashlib
import json

import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter

RAIZ = Path(__file__).resolve().parents[1]
origen = RAIZ / "analisis_plata/notebooks/01_validacion_plata.ipynb"
salida = RAIZ / "analisis_plata/ejecutados"
salida.mkdir(parents=True, exist_ok=True)
nb = nbformat.read(origen, as_version=4)
NotebookClient(nb, timeout=600, kernel_name="venv_global", resources={"metadata": {"path": str(RAIZ)}}).execute()
errores = [o for c in nb.cells if c.cell_type == "code" for o in c.outputs if o.output_type == "error"]
assert not errores, errores
assert all(c.execution_count is not None for c in nb.cells if c.cell_type == "code")
nbformat.write(nb, salida / origen.name)
html, _ = HTMLExporter().from_notebook_node(nb)
(salida / "01_validacion_plata.html").write_text(html, encoding="utf-8")
recibo = {"notebooks": 1, "celdas_ejecutadas": sum(c.cell_type == "code" for c in nb.cells),
          "figuras": sum("image/png" in o.get("data", {}) for c in nb.cells if c.cell_type == "code" for o in c.outputs),
          "errores": len(errores), "sha256_notebook_fuente": hashlib.sha256(origen.read_bytes()).hexdigest()}
(salida / "ejecucion.json").write_text(json.dumps(recibo, indent=2), encoding="utf-8")
print(json.dumps(recibo, ensure_ascii=False))
print(salida / "01_validacion_plata.html")
