"""Oro: invariantes de decisión con predios sintéticos, nunca datos privados."""
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def contexto():
    api = {"__name__": "prueba_oro"}
    for nombre in ("00_utils_espacial.py", "00_pipeline.py", "00_silver.py", "00_gold.py"):
        exec(compile((RAIZ / "notebooks" / nombre).read_text(encoding="utf-8"), nombre, "exec"), api)
    fuentes = api["leer_fuentes_plata"](RAIZ / "data/externos")
    g = gpd.GeoDataFrame({"OBJECTID": ["lote", "sin_dato", "observado", "estimado", "otro"],
                         "NPISOS": ["0", "3", "2", None, "4"], "COMUNA": ["19"] * 5,
                         "Estado_Estructural": ["Alta probabilidad de escombros", "Sin datos satelitales",
                                                "Posible desaparicion de techo", "Alta probabilidad de escombros",
                                                "Sin cambio aparente / dano interno"]},
                        geometry=[box(-76.545 + i * .0002, 3.42, -76.5449 + i * .0002, 3.4201)
                                  for i in range(5)], crs=4326)
    plata, _ = api["construir_plata"](api["bronze_desde_geojson"](g), fuentes)
    oro, _ = api["construir_oro"](plata)
    return api, plata, oro


def test_conserva_predios_y_excluye_lotes_y_sin_dato(contexto):
    _, plata, oro = contexto
    p = oro["predios"].set_index("id")
    assert set(p.index) == set(plata["predios"].id)
    assert not p.loc["lote", "en_ranking"] and not p.loc["sin_dato", "en_ranking"]
    assert pd.isna(p.loc["lote", "posicion"]) and pd.isna(p.loc["lote", "pisos"])
    assert p.loc["estimado", "pisos_imputado"] and pd.isna(p.loc["estimado", "pisos_observados"])


def test_aportes_y_pesos_reconstruyen_puntaje_con_faltantes(contexto):
    api, plata, _ = contexto
    datos = plata["predios"].copy()
    datos.loc[:, "p_ductilidad_baja"] = np.nan
    p = api["predios_oro"](datos)
    assert p.peso_efectivo_c_vulnerabilidad.eq(0).all()
    np.testing.assert_allclose(p[[f"peso_efectivo_{c}" for c in api["PESOS"]]].sum(axis=1), 1.)
    np.testing.assert_allclose(p[[f"aporte_{c}" for c in api["PESOS"]]].sum(axis=1), p.indice_riesgo, atol=.000051)


def test_p90_solo_elegibles_y_media_solo_pisos_observados(contexto):
    _, _, oro = contexto
    p = oro["predios"]
    c = oro["comunas"].set_index("comuna").loc[19]
    assert c.n_predios == 5 and c.n_lotes == 1 and c.n_en_ranking == 3
    assert c.indice_p90 == pytest.approx(p.loc[p.en_ranking, "indice_riesgo"].quantile(.9))
    assert c.pisos_prom_observados == pytest.approx((3 + 2 + 4) / 3)
    assert c.n_con_dato_satelital == 4


def test_sensibilidad_empates_estable_y_top_pequeno(contexto):
    api, plata, _ = contexto
    p = api["predios_oro"](plata["predios"])
    p["indice_riesgo"] = .5
    a = api["posiciones_oro"](p, p.indice_riesgo)
    b = api["posiciones_oro"](p.iloc[::-1], p.iloc[::-1].indice_riesgo)
    pd.testing.assert_series_equal(a.sort_index(), b.sort_index())
    detalle, resumen = api["sensibilidad_oro"](api["predios_oro"](plata["predios"]))
    base = resumen.set_index("escenario").loc["base"]
    assert base.n_top == 3 and base.pct_top_coincide == 100
    assert len(detalle) == 3 * len(api["escenarios_oro"]())
    assert "c_exposicion" not in api["escenarios_oro"]()["sin_fuentes_gem"]
    assert "c_exposicion" in api["escenarios_oro"]()["sin_vulnerabilidad_ni_suelo"]


def test_exposicion_no_duplica_ids_gem(contexto):
    _, plata, oro = contexto
    ex = oro["exposicion_gem"]
    assert ex.id.is_unique
    assert set(ex.id) == set(plata["cruces_gem"].id_gem)
    assert ex.n_predios_vinculados.sum() == len(plata["cruces_gem"])
    assert "personas_afectadas" not in ex


def test_calidad_rechaza_p90_contaminado_y_perdida(contexto):
    api, plata, oro = contexto
    cambiado = {k: d.copy() for k, d in oro.items()}
    cambiado["comunas"]["indice_p90"] = 99.
    with pytest.raises(ValueError, match="p90_comuna"):
        api["validar_oro"](cambiado, plata)
    cambiado = {k: d.copy() for k, d in oro.items()}
    cambiado["predios"] = cambiado["predios"].iloc[1:]
    with pytest.raises(ValueError, match="predios_conservados"):
        api["validar_oro"](cambiado, plata)


def test_sin_elegibles_conserva_inventario_y_no_inventa_top(contexto):
    api, plata, _ = contexto
    datos = plata["predios"].copy()
    datos["sin_dato_satelital"] = True
    p = api["predios_oro"](datos)
    detalle, resumen = api["sensibilidad_oro"](p)
    assert not p.en_ranking.any() and p.posicion.isna().all()
    assert detalle.empty and resumen.n_top.eq(0).all() and resumen.pct_top_coincide.isna().all()
    factores, _ = api["factores_oro"](p)
    assert factores.p_valor_chi2.isna().all()


def test_factores_escasos_no_inventan_significancia(contexto):
    _, _, oro = contexto
    f = oro["factores"]
    assert f.p_ajustado_holm.isna().all()
    assert f.n_validos.add(f.n_faltantes).eq(f.n_elegibles).all()
    assert f.interpretacion.str.contains("no_causal").all()


def test_afectacion_usa_denominadores_y_no_cambia_plata(contexto):
    api, plata, oro = contexto
    copia = plata["predios"].copy(deep=True)
    api["predios_oro"](plata["predios"])
    pd.testing.assert_frame_equal(plata["predios"], copia)
    a = oro["afectaciones"].query("ambito == 'inventario'")
    assert a.n_predios.sum() == 5 and a.denominador_predios.eq(5).all()
    assert a.pct_predios.sum() == pytest.approx(100)


def test_normalizacion_entera_nullable_no_trunca_percentiles():
    api = {}
    exec((RAIZ / 'notebooks/00_utils_espacial.py').read_text(encoding="utf-8"), api)
    s = pd.Series([None, 3, 2, 1, 4], dtype='Int64')
    antes = s.copy()
    resultado = api['normalizar'](s)
    assert pd.isna(resultado.iloc[0])
    assert resultado.iloc[3] == 0 and resultado.iloc[4] == 1
    assert resultado.iloc[1] == pytest.approx((3 - 1.03) / (3.97 - 1.03))
    pd.testing.assert_series_equal(s, antes)


def test_todos_sin_comuna_conservan_totales_y_esquema(contexto):
    api, plata, oro = contexto
    datos = {k: d.copy() for k, d in plata.items()}
    datos['predios']['comuna'] = pd.Series(pd.NA, index=datos['predios'].index, dtype='Int64')
    resultado, _ = api['construir_oro'](datos)
    assert resultado['comunas'].empty
    assert set(resultado['comunas'].columns) == set(oro['comunas'].columns)
    assert resultado['afectaciones'].query("ambito == 'comuna' and zona == 'sin_comuna'").n_predios.sum() == 5


def test_exportacion_no_convierte_desconocido_en_cero(contexto, tmp_path):
    api, _, oro = contexto
    import json
    api['exportar_visor'](oro['predios'], oro['comunas'], tmp_path)
    archivo = json.loads((tmp_path / 'edificios.geojson').read_text(encoding="utf-8"))
    p = {f['properties']['id']: f['properties'] for f in archivo['features']}
    assert p['lote']['pisos'] is None and p['lote']['sin_construccion_registrada']
    assert p['observado']['pisos'] == 2
    assert p['estimado']['pisos_observados'] is None
    assert 'motivos_principales' in p['observado']


def test_comentarios_apuntan_a_tablas_y_columnas_publicadas(contexto):
    api, _, oro = contexto
    assert set(api['COMENTARIOS_TABLAS_ORO']) == set(oro)
    for nombre, columnas in api['COMENTARIOS_COLUMNAS_ORO'].items():
        faltan = set(columnas) - set(oro[nombre].columns)
        assert not faltan, f"{nombre}: {faltan}"
