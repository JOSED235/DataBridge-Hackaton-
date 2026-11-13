"""Contrato de plata: identidad, faltantes y correspondencia espacial, sin datos privados."""
from pathlib import Path
import re

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Point, box

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def api():
    scope = {"__name__": "prueba_plata"}
    for nombre in ("00_utils_espacial.py", "00_pipeline.py", "00_silver.py"):
        exec(compile((RAIZ / "notebooks" / nombre).read_text(), nombre, "exec"), scope)
    return scope


def test_lotes_y_desconocidos_se_conservan(api):
    g = gpd.GeoDataFrame({"OBJECTID": ["a", "b", "c"], "NPISOS": ["0", None, "3"],
                         "COMUNA": ["19"] * 3, "EDIFPRED": [" ", None, "00"],
                         "Estado_Estructural": ["Alta probabilidad de escombros"] * 3},
                        geometry=[box(-76.54 + i * .001, 3.4, -76.5395 + i * .001, 3.4005)
                                  for i in range(3)], crs=4326)
    raw = api["bronze_desde_geojson"](g)
    p, _ = api["limpiar_predios_plata"](raw)
    assert len(p) == 3
    assert p.estado_predial.tolist() == ["sin_construccion_registrada", "pisos_desconocidos", "con_pisos_registrados"]
    assert pd.isna(p.loc[0, "pisos"]) and not p.loc[0, "pisos_imputado"]
    assert pd.isna(p.loc[1, "pisos_observados"])
    assert p.loc[2, "edifpred"] == "00"
    with pytest.raises(ValueError, match="identidad"):
        api["limpiar_predios_plata"](pd.concat([raw, raw.iloc[:1]], ignore_index=True))


def test_empates_gem_y_reutilizacion_son_visibles_y_deterministas(api):
    p = gpd.GeoDataFrame({"id": ["p1", "p2"]},
                         geometry=[box(0, 0, 10, 10), box(0, 0, 10, 10)], crs=9377)
    ex = gpd.GeoDataFrame({"id": ["g2", "g1"], "ocupantes_noche": [2., 5.],
                          "valor_reemplazo_usd": [20., 50.]},
                         geometry=[Point(3, 3), Point(4, 4)], crs=9377)
    a = api["candidatos_gem"](p, ex)
    b = api["candidatos_gem"](p, ex.iloc[::-1])
    pd.testing.assert_frame_equal(a, b)
    assert len(a) == 4 and a.gem_reutilizado.all()
    assert a.n_candidatos.eq(2).all()
    assert a[a.seleccionado].id_gem.tolist() == ["g1", "g1"]
    # La política aprobada suma los empates por predio; no equivale a población única.
    assert a.groupby("id_predio").ocupantes_noche.sum().eq(7).all()


def test_zonas_multiples_no_se_eligen_arbitrariamente(api):
    p = gpd.GeoDataFrame({"id": ["a"]}, geometry=[Point(5, 5)], crs=9377)
    z = gpd.GeoDataFrame({"id": ["z1", "z2"], "nombre": ["Uno", "Dos"]},
                         geometry=[box(0, 0, 10, 10), box(0, 0, 10, 10)], crs=9377)
    valores, relaciones = api["cruzar_territorio"](p, z)
    assert valores.n_coincidencias.iloc[0] == 2
    assert pd.isna(valores.id_territorio.iloc[0])
    assert len(relaciones) == 2


def test_amplificacion_no_inventa_uno_y_lote_no_tiene_periodo(api):
    p = gpd.GeoDataFrame({"id": ["p1", "p2", "p3"], "pisos": [2., np.nan, 2.],
                          "sin_construccion_registrada": [False, True, False]},
                         geometry=[Point(5, 5), Point(6, 6), Point(50, 50)], crs=9377)
    sitio = gpd.GeoDataFrame({"id": ["s1", "s2", "s3", "s4"],
                              "ampcode": ["x"] * 4},
                             geometry=[Point(0, 0), Point(10, 0), Point(0, 10), Point(10, 10)], crs=9377)
    af = pd.DataFrame({"ampcode": ["otro"], "nivel_roca_g": [.2267], "imt": ["SA"],
                       "periodo_s": [.2], "factor": [1.5], "sigma": [.3]})
    out = api["suelo_plata"](p, sitio, af)
    assert out.amplif_suelo.isna().all()
    assert pd.isna(out.loc[1, "periodo_s"])
    assert not out.loc[2, "dentro_cobertura_microzona"]


def test_eventos_se_unifican_por_id_y_actualizacion(api):
    a = gpd.GeoDataFrame({"id": ["e1", "e2"], "time": [1000, 2000],
                          "updated": [2000, 2000], "mag": [4., 5.], "magType": ["mb", "mww"]},
                         geometry=[Point(-76, 4, 10), Point(-76, 4, 20)], crs=4326)
    b = a.iloc[:1].copy()
    b["updated"] = 3000
    b["mag"] = 4.2
    eventos, origen = api["eventos_plata"]({"inicial": a, "actualizado": b})
    assert len(eventos) == 2 and len(origen) == 3
    assert eventos.set_index("id").loc["e1", "magnitud"] == 4.2
    assert eventos.set_index("id").loc["e1", "profundidad_km"] == 10
    assert str(eventos.fecha_utc.dt.tz) == "UTC"


def test_catalogo_geografico_3d_conserva_profundidad(api):
    g = gpd.GeoDataFrame({"id": ["e"], "time": [1000], "updated": [2000]},
                         geometry=[Point(-76, 4, 116.13)], crs=4979)
    eventos, _ = api["eventos_plata"]({"catalogo": g})
    assert eventos.crs.to_epsg() == 4326
    assert eventos.profundidad_km.iloc[0] == 116.13


def test_servicios_sin_operatividad_no_se_asumen_cerrados(api):
    g = gpd.GeoDataFrame({"osm_id": ["node/1", "node/2", "node/3"],
                          "amenity": ["hospital"] * 3, "emergency": ["yes", "no", None]},
                         geometry=[Point(-76.5, 3.4)] * 3, crs=4326)
    s = api["servicios_plata"]({"osm_salud": g})
    assert s.urgencias.tolist() == ["si", "no", "sin_dato"]
    assert s.operatividad.isna().all() and s.capacidad.isna().all()


def test_vecino_sin_objetivos_es_faltante_y_no_cero(api):
    p = gpd.GeoDataFrame({"id": ["a"]}, geometry=[Point(-76.5, 3.4)], crs=4326)
    vacio = gpd.GeoDataFrame({"id": pd.Series(dtype="string")}, geometry=[], crs=4326)
    j = api["vecino_plata"](p, vacio)
    assert j.distancia_m.isna().all() and j.n_coincidencias.eq(0).all()


def test_lectura_bronze_texto_equivale_a_archivos_y_no_modifica_fuentes(api):
    fuentes = api["leer_fuentes_plata"](RAIZ / "data/externos")
    raw_g = gpd.GeoDataFrame({"OBJECTID": ["a", "b", "c"], "NPISOS": ["0", None, "3"],
                              "COMUNA": ["19"] * 3, "Estado_Estructural": ["Alta probabilidad de escombros"] * 3},
                             geometry=[box(-76.545 + i * .001, 3.42, -76.5445 + i * .001, 3.4205)
                                       for i in range(3)], crs=4326)
    raw = api["bronze_desde_geojson"](raw_g)
    antes = {k: d.copy(deep=True) for k, d in fuentes.items()}
    a, _ = api["construir_plata"](raw, fuentes)
    bronze = {k: api["bronze_desde_geojson"](d) if isinstance(d, gpd.GeoDataFrame) else d
              for k, d in fuentes.items()}
    # 01_bronze normaliza los caracteres que Delta rechaza (e4af152).
    bronze = {k: d.rename(columns=lambda c: re.sub(r"[ ,;{}()\n\t=]", "_", c).strip("_"))
              for k, d in bronze.items()}
    b, _ = api["construir_plata"](raw, bronze)
    pd.testing.assert_frame_equal(a["predios"], b["predios"])
    pd.testing.assert_frame_equal(a["eventos"], b["eventos"])
    for nombre in fuentes:
        pd.testing.assert_frame_equal(fuentes[nombre], antes[nombre])


def test_gold_acepta_tipos_nullable_sin_incluir_lotes_en_ranking(api):
    df = pd.DataFrame({"id": ["lote", "edificio", "sin_dato"],
                       "pisos": pd.Series([None, 2, 3], dtype="Float64"),
                       "sin_construccion_registrada": [True, False, False],
                       "sin_dato_satelital": [False, False, True],
                       "sev_estado": [1., .7, np.nan], "prob_escombros": [np.nan] * 3,
                       "n_edif_100m": [1, 2, 3], "dist_salud_m": [100., 200., 300.],
                       "puede_bloquear_via": pd.Series([None, False, True], dtype="boolean")})
    g = api["calcular_indice"](df)
    assert g.en_ranking.tolist() == [False, True, False]
    assert g.loc[0, "prioridad"] == "Sin construcción registrada: verificar"
    assert g.loc[2, "prioridad"] == "Sin dato: verificar en terreno"
