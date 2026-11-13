"""Verifica ejecución, salidas, integridad de fuentes y exclusión de datos privados."""

import hashlib
import json
import subprocess
from pathlib import Path

import nbformat


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    folder = root / "analisis_bronce"
    sources = sorted((folder / "notebooks").glob("*.ipynb"))
    assert len(sources) == 18, len(sources)
    receipt = []
    for path in sources:
        source = nbformat.read(path, as_version=4)
        done = nbformat.read(folder / "ejecutados" / path.name, as_version=4)
        nbformat.validate(source)
        nbformat.validate(done)
        assert [c.source for c in source.cells] == [c.source for c in done.cells], path.name
        clean = [c for c in source.cells if c.cell_type == "code"]
        assert all(c.execution_count is None and not c.outputs for c in clean), path.name
        cells = [c for c in done.cells if c.cell_type == "code" and c.source.strip()]
        assert all(c.execution_count is not None for c in cells), path.name
        errors = [o for c in cells for o in c.outputs if o.output_type == "error"]
        assert not errors, path.name
        images = sum("image/png" in o.get("data", {}) for c in cells for o in c.outputs)
        html = folder / "ejecutados" / f"{path.stem}.html"
        assert html.stat().st_size > 1000
        if path.stem != "99_seleccion_para_plata":
            profile = json.loads((folder / "resultados" / f"{path.stem}.json").read_text())
            raw = root / profile["archivo"]
            with raw.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            assert digest == profile["sha256"], path.name
        receipt.append({"notebook": path.name, "celdas": len(cells), "figuras": images, "errores": 0})
    private = ["data/Datosprediales.json", "data/oficiales/Datosprediales.json",
               "analisis_bronce/ejecutados/index.html", "analisis_bronce/resultados/01_predios_oficiales.json"]
    for path in private:
        subprocess.run(["git", "check-ignore", "-q", path], cwd=root, check=True)
    # No se debe versionar el contenido privado, aunque la regla de ignore exista.
    tracked = subprocess.check_output(["git", "ls-files", "--", *private,
                                       "analisis_bronce/ejecutados", "analisis_bronce/resultados"], cwd=root)
    assert not tracked, "Hay datos privados versionados"
    source_copy = root / "data/oficiales/Datosprediales.json"
    delivery = root / "data/Datosprediales.json"
    if delivery.exists():
        assert delivery.read_bytes() == source_copy.read_bytes()
    execution_index = json.loads((folder / "ejecutados/ejecucion.json").read_text())
    assert {row["notebook"] for row in execution_index} == {p.name for p in sources}
    (folder / "resultados" / "verificacion.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(receipt)} notebooks ejecutados; {sum(r['celdas'] for r in receipt)} celdas; "
          f"{sum(r['figuras'] for r in receipt)} figuras; 0 errores")
    print("17 fuentes conservan su SHA-256; notebooks fuente sin salidas; resultados privados ignorados")
    print("Archivo oficial de análisis: SHA-256 idéntico al del perfil; entrega inicial opcional")


if __name__ == "__main__":
    main()
