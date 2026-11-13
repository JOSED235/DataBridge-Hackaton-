"""Descarga de la lista del visor: el XLSX abre con columnas tipadas y el CSV se separa en Excel en español."""
import csv
import io
import json
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
PREDIOS = [
    {"posicion": 1, "id": 3221, "comuna": 3, "barrio": "San Juan Bosco", "prioridad": "Muy alta", "indice_riesgo": 0.7376,
     "cola_trabajo": "inspeccion_priorizada", "motivos_principales": "danio, vulnerabilidad, bloqueo_via",
     "estado": "Alta probabilidad de escombros", "pisos": 4.0, "pisos_fuente": "oficial", "dist_salud_m": 152.4,
     "puede_bloquear_via": True, "lon": -76.531234, "lat": 3.451234},
    {"posicion": None, "id": "lote; \"raro\"", "comuna": None, "barrio": None, "prioridad": "Sin dato: verificar en terreno",
     "indice_riesgo": None, "cola_trabajo": "verificar_dato_satelital", "motivos_principales": None, "estado": None,
     "pisos": None, "pisos_fuente": None, "dist_salud_m": None, "puede_bloquear_via": False, "lon": None, "lat": None},
]


@pytest.fixture(scope="module")
def salidas(tmp_path_factory):
    if not shutil.which("node"):
        pytest.skip("Node no está instalado")
    carpeta = tmp_path_factory.mktemp("lista")
    script = (
        "const L = require(process.argv[1]); const fs = require('fs');"
        "const p = JSON.parse(process.argv[2]);"
        "fs.writeFileSync(process.argv[3], L.csv(p));"
        "fs.writeFileSync(process.argv[4], L.xlsx(p, [['Comuna', 'Todas'], ['Predios en la lista', p.length]]));"
    )
    subprocess.run(["node", "-e", script, str(RAIZ / "visor/lista.js"), json.dumps(PREDIOS),
                    str(carpeta / "l.csv"), str(carpeta / "l.xlsx")], check=True)
    return carpeta


def test_xlsx_abre_con_encabezado_fijo_filtro_y_tipos(salidas):
    openpyxl = pytest.importorskip("openpyxl")
    libro = openpyxl.load_workbook(salidas / "l.xlsx")
    assert libro.sheetnames == ["Lista", "Notas"]
    hoja = libro["Lista"]
    assert hoja["A1"].value == "Posición" and hoja["F1"].value == "Índice de riesgo"
    assert hoja.freeze_panes == "A2" and hoja.auto_filter.ref == "A1:O3"
    assert hoja["A2"].value == 1 and hoja["F2"].value == pytest.approx(0.7376) and hoja["F2"].number_format == "0.000"
    assert hoja["H2"].value == "daño, vulnerabilidad, bloqueo de vía" and hoja["M2"].value == "Sí"
    assert hoja["B3"].value == 'lote; "raro"' and hoja["A3"].value is None and hoja["I3"].value == "Sin dato"
    assert libro["Notas"]["B3"].value == 2


def test_csv_separado_por_punto_y_coma_con_coma_decimal(salidas):
    texto = (salidas / "l.csv").read_text(encoding="utf-8-sig")
    filas = list(csv.reader(io.StringIO(texto), delimiter=";"))
    assert filas[0][0] == "Posición" and len(filas[0]) == 15
    assert filas[1][5] == "0,738" and filas[1][13] == "-76,531234"
    assert filas[2][1] == 'lote; "raro"' and all(len(f) == 15 for f in filas)
