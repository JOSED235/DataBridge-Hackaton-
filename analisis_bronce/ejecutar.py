"""Ejecuta cada notebook de bronce y conserva sus salidas y su versión HTML.

Uso desde la raíz: /home/nicolas/venv_global/bin/python analisis_bronce/ejecutar.py
Opcional: --solo 01_predios_oficiales para ejecutar un único dataset.
Los archivos crudos y notebooks fuente no se sobrescriben.
"""

import argparse
import html
import json
import sys
import platform
from importlib.metadata import version
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solo", help="Nombre del notebook sin extensión")
    parser.add_argument("--kernel", default="venv_global")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    folder = root / "analisis_bronce"
    output = folder / "ejecutados"
    output.mkdir(parents=True, exist_ok=True)
    sources = sorted((folder / "notebooks").glob("*.ipynb"))
    if args.solo:
        sources = [p for p in sources if p.stem == args.solo]
        if not sources:
            parser.error("No existe ese notebook")
    exporter = HTMLExporter(template_name="lab")
    index = []
    receipt = output / "ejecucion.json"
    if args.solo:
        # Reconstruir desde los archivos, incluso después de una corrida interrumpida.
        for previous in sorted(output.glob("*.ipynb")):
            source = folder / "notebooks" / previous.name
            if not source.exists():
                continue
            done = nbformat.read(previous, as_version=4)
            original = nbformat.read(source, as_version=4)
            same = [c.source for c in done.cells] == [c.source for c in original.cells]
            cells = [c for c in done.cells if c.cell_type == "code" and c.source.strip()]
            errors = [o for c in cells for o in c.outputs if o.output_type == "error"]
            if same and cells and not errors and all(c.execution_count is not None for c in cells):
                index.append({"notebook": previous.name, "celdas_ejecutadas": len(cells), "errores": 0})
    (folder / "resultados").mkdir(exist_ok=True)
    (folder / "resultados" / "entorno.json").write_text(json.dumps({
        "python": platform.python_version(), "ejecutable": sys.executable,
        "paquetes": {name: version(name) for name in [
            "pandas", "geopandas", "shapely", "pyproj", "numpy", "scipy",
            "matplotlib", "nbformat", "nbclient", "nbconvert", "osmium"]},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    for path in sources:
        print(f"Ejecutando {path.name}...", flush=True)
        nb = nbformat.read(path, as_version=4)
        client = NotebookClient(nb, timeout=240, kernel_name=args.kernel,
                                resources={"metadata": {"path": str(root)}})
        try:
            client.execute()
        except Exception:
            nbformat.write(nb, output / path.name)
            print(f"Falló {path.name}; se conserva la ejecución parcial.", file=sys.stderr)
            raise
        nbformat.write(nb, output / path.name)
        body, _ = exporter.from_notebook_node(nb)
        (output / f"{path.stem}.html").write_text(body, encoding="utf-8")
        code = [c for c in nb.cells if c.cell_type == "code" and c.source.strip()]
        errors = [o for c in code for o in c.outputs if o.output_type == "error"]
        assert not errors and all(c.execution_count is not None for c in code)
        index = [row for row in index if row["notebook"] != path.name]
        index.append({"notebook": path.name, "celdas_ejecutadas": len(code), "errores": len(errors)})
        receipt.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Guardado: {path.stem}.ipynb y .html; {len(code)} celdas, 0 errores", flush=True)
    # El índice incluye también ejecuciones anteriores cuando se usa --solo.
    links = []
    for path in sorted(output.glob("*.html")):
        if path.name != "index.html":
            links.append(f'<li><a href="{html.escape(path.name)}">{html.escape(path.stem)}</a></li>')
    (output / "index.html").write_text(
        '<!doctype html><html lang="es"><meta charset="utf-8"><title>Análisis de bronce</title>'
        '<style>body{font:17px system-ui;max-width:1000px;margin:50px auto;padding:0 24px;line-height:1.7}'
        'a{color:#165b78}li{margin:10px 0}</style><h1>Análisis exploratorio de bronce</h1>'
        '<p>Un notebook por dataset. Salidas locales con datos oficiales: no redistribuir.</p>'
        '<p>Consultar 99_seleccion_para_plata después de los análisis individuales.</p><ol>'
        + ''.join(links) + '</ol></html>', encoding="utf-8")
    (output / "ejecucion.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Índice: {output / 'index.html'}")


if __name__ == "__main__":
    main()
