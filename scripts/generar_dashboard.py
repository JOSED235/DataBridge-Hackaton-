"""Dashboard HTML autónomo de conclusiones desde las tablas gold (y el reporte de silver).

Un solo archivo sin JavaScript ni dependencias externas: funciona sin internet y se puede
adjuntar o proyectar. Lee data/oficiales/oro/ y data/oficiales/plata/reporte.json.
La salida contiene derivados de datos oficiales: va a data/oficiales/salidas/, fuera de git.

Uso:  python scripts/generar_dashboard.py
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
ORO = RAIZ / "data" / "oficiales" / "oro"
PLATA = RAIZ / "data" / "oficiales" / "plata"
SALIDA = RAIZ / "data" / "oficiales" / "salidas" / "dashboard_icesixuao.html"

ACENTO, NARANJA, VERDE, AZUL, MORADO, GRIS = "#ff5a36", "#ff9500", "#3ecf8e", "#5aaadc", "#a06cd5", "#8b919b"
COLOR_PRIORIDAD = {"Muy alta": ACENTO, "Alta": NARANJA, "Media": "#e8d44d", "Baja": "#565d68",
                   "Sin dato: verificar en terreno": MORADO, "Sin construcción registrada: verificar": AZUL}


def num(v, dec=0):
    """Formato es-CO: miles con punto y decimales con coma."""
    s = f"{v:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(v, dec=1):
    return f"{num(v, dec)} %"


def barra(valor, maximo, color, etiqueta, texto_derecha):
    w = max(2.0, 100.0 * valor / maximo) if maximo else 0
    return (f'<div class="fila-barra"><span class="etq">{etiqueta}</span>'
            f'<div class="pista"><div class="lleno" style="width:{w:.1f}%;background:{color}"></div></div>'
            f'<span class="val">{texto_derecha}</span></div>')


def main():
    reporte_oro = json.loads((ORO / "reporte.json").read_text(encoding="utf-8"))
    reporte_plata = json.loads((PLATA / "reporte.json").read_text(encoding="utf-8"))
    comunas = pd.read_parquet(ORO / "gold_icesixuao_comunas.parquet")
    factores = pd.read_parquet(ORO / "gold_icesixuao_factores.parquet")
    sens = pd.read_parquet(ORO / "gold_icesixuao_resumen_sensibilidad.parquet")
    fuentes = pd.read_parquet(ORO / "gold_icesixuao_fuentes.parquet")
    pesos = pd.read_parquet(ORO / "gold_icesixuao_parametros.parquet")
    componentes = ["c_danio", "c_vulnerabilidad", "c_exposicion", "c_suelo", "c_altura", "c_acceso_salud", "c_bloqueo_via"]
    predios = pd.read_parquet(ORO / "gold_icesixuao_predios.parquet",
                              columns=["prioridad", "ocupantes_asignados_gem", "periodo_construccion", "en_ranking",
                                       "sin_construccion_registrada", "sin_dato_satelital", "sev_estado", "pisos", "comuna",
                                       "dist_salud_m", "dist_salud_urgencias_m", "puede_bloquear_via", "cola_trabajo", *componentes])
    exposicion = pd.read_parquet(ORO / "gold_icesixuao_exposicion_gem.parquet", columns=["ocupantes_noche", "n_vinculos_con_senal_danio"])

    n_ctrl_oro = int(len(pd.read_parquet(ORO / "gold_icesixuao_calidad.parquet")))
    n_ctrl_plata = int(reporte_plata["tablas"]["calidad"])
    procesado = datetime.fromisoformat(reporte_oro["procesado_utc"]).astimezone()
    remoto = "mismas cifras que las tablas gold publicadas en Databricks el 13-nov-2026"

    # --- Agregados que no vienen en las tablas de resumen ------------------------------------------
    mh = predios["prioridad"].eq("Muy alta")
    ocup_mh = int(predios.loc[mh, "ocupantes_asignados_gem"].sum())
    pre85 = predios["periodo_construccion"].isin(["<= 1960", "1961 - 1985"])
    pre85_mh = pct(100 * (pre85 & mh).sum() / mh.sum())
    n_altos = int((predios["pisos"] >= 11).sum())
    pre85_c3 = predios["comuna"].eq(3) & ~predios["sin_construccion_registrada"].fillna(False)
    c3_pre85 = pct(100 * (pre85 & pre85_c3).sum() / pre85_c3.sum())
    # Cohorte que señala la Javeriana Cali: 3 a 6 pisos, construida hasta 1985 (docs/FUENTES.md).
    cohorte = pre85 & predios["pisos"].between(3, 6) & predios["en_ranking"].fillna(False)
    cohorte_rank = pct(100 * cohorte.sum() / predios["en_ranking"].fillna(False).sum())
    cohorte_mh = pct(100 * (cohorte & mh).sum() / mh.sum())
    danio = ~predios["sin_dato_satelital"].fillna(False) & predios["sev_estado"].ge(0.7)
    lote = predios["sin_construccion_registrada"].fillna(False)
    ocup_unicos = int(exposicion.loc[exposicion["n_vinculos_con_senal_danio"] > 0, "ocupantes_noche"].sum())
    ocup_por_predio = int(predios.loc[danio & ~lote, "ocupantes_asignados_gem"].sum())
    n_danio, n_lotes_danio = int(danio.sum()), int((danio & lote).sum())

    # Servicios urbanos por comuna: proximidad euclidiana, no tiempos de viaje.
    servicios = predios[danio].groupby("comuna").agg(
        con_danio=("sev_estado", "size"),
        cerca_salud=("dist_salud_m", lambda s: int((s <= 200).sum())),
        lejos_urgencias=("dist_salud_urgencias_m", lambda s: int((s > 1000).sum())),
        bloqueo=("puede_bloquear_via", lambda s: int(s.fillna(False).sum())))
    filas_servicios = "".join(
        f'<tr><td>C{int(c)}</td><td>{num(r.con_danio)}</td><td>{num(r.cerca_salud)}</td>'
        f'<td>{num(r.lejos_urgencias)}</td><td>{num(r.bloqueo)}</td></tr>' for c, r in servicios.iterrows())
    tot = servicios.sum()
    filas_servicios += (f'<tr><td>Total</td><td>{num(tot.con_danio)}</td><td>{num(tot.cerca_salud)}</td>'
                        f'<td>{num(tot.lejos_urgencias)}</td><td>{num(tot.bloqueo)}</td></tr>')

    # Tabla completa por comuna (gold_icesixuao_comunas).
    filas_tabla_comunas = "".join(
        f'<tr><td>{int(c.ranking)}</td><td>Comuna {int(c.comuna)}</td><td>{num(c.indice_p90, 3)}</td>'
        f'<td>{num(c.n_predios)}</td><td>{num(c.n_en_ranking)}</td><td>{num(c.n_prioridad_muy_alta)}</td>'
        f'<td>{num(c.n_prioridad_alta)}</td><td>{pct(c.pct_danio_entre_con_dato)}</td><td>{pct(c.pct_sin_dato)}</td>'
        f'<td>{num(c.ocupantes_asignados_gem_con_senal_danio)}</td><td>{num(c.n_salud)}</td></tr>'
        for c in comunas.sort_values("ranking").itertuples())

    # Colas de trabajo para brigadas.
    colas = predios["cola_trabajo"].value_counts()
    nombres_cola = {"inspeccion_priorizada": "Inspección (ranking)",
                    "verificar_dato_satelital": "Sin dato satelital",
                    "verificar_predio_sin_construccion": "Lotes sin construcción"}
    color_cola = {"inspeccion_priorizada": ACENTO, "verificar_dato_satelital": MORADO}
    filas_colas = "".join(barra(v, int(colas.max()), color_cola.get(k, AZUL), nombres_cola.get(k, k), num(v))
                          for k, v in colas.items())

    # PCA de los siete componentes entre los edificios del ranking (faltantes imputados con la media solo aquí).
    x = predios.loc[predios["en_ranking"].fillna(False), componentes].astype(float)
    x = x.fillna(x.mean())
    var = np.linalg.eigvalsh(np.corrcoef(((x - x.mean()) / x.std(ddof=0)).T.values))[::-1]
    var = 100 * var / var.sum()
    corr = x.corr().values
    media_r = float(np.abs(corr[~np.eye(len(componentes), dtype=bool)]).mean())
    filas_pca = "".join(barra(v, var[0], AZUL, f"Componente {i + 1}", f"{pct(v)} · acumulado {pct(var[:i + 1].sum())}")
                        for i, v in enumerate(var))

    # --- Secciones ----------------------------------------------------------------------------------
    max_p90 = comunas["indice_p90"].max()
    filas_comunas = []
    for _, c in comunas.sort_values("ranking").iterrows():
        carga = int(c["n_prioridad_muy_alta"] + c["n_prioridad_alta"])
        filas_comunas.append(barra(
            c["indice_p90"], max_p90, ACENTO,
            f'C{int(c["comuna"])} · #{int(c["ranking"])}',
            f'p90 {num(c["indice_p90"], 3)} · {num(c["n_predios"])} predios · {carga} de prioridad alta o muy alta · '
            f'{num(int(c["ocupantes_en_edif_con_danio"]))} ocupantes con daño'))
    orden = "".join(filas_comunas)

    total_prior = int(sum(reporte_oro["prioridades"].values()))
    filas_prior = "".join(barra(
        v, total_prior, COLOR_PRIORIDAD.get(k, GRIS), k, f'{num(v)} · {pct(100 * v / total_prior)}')
        for k, v in sorted(reporte_oro["prioridades"].items(), key=lambda kv: -kv[1]))

    cat_danio = [("Alta probabilidad de escombros", 296, ACENTO), ("Posible desaparición de techo", 1058, NARANJA),
                 ("Sin cambio aparente / daño interno", 3357, GRIS), ("Sin datos satelitales", 435, MORADO)]
    barras_danio = "".join(barra(v, 5146, c, k, f'{num(v)} · {pct(100 * v / 5146)}') for k, v, c in cat_danio)

    filas_fact = "".join(
        f'<tr><td>{r.factor}</td><td>{num(r.n_validos)}</td><td>{num(r.p_valor_chi2, 3)}</td>'
        f'<td>{"–" if pd.isna(r.p_ajustado_holm) else num(r.p_ajustado_holm, 3)}</td>'
        f'<td>{num(r.v_cramer, 3)}</td><td>{num(r.frecuencia_esperada_min, 1)}</td>'
        f'<td>{"frecuencias bajas" if r.estado_prueba != "evaluada" else "válida"}</td></tr>'
        for r in factores.itertuples())

    max_top = sens["pct_top_coincide"].max()
    filas_sens = "".join(
        barra(r.pct_top_coincide, max_top, VERDE if r.escenario == "base" else (NARANJA if r.escenario == "solo_datos_oficiales" else AZUL),
              r.escenario, f'{num(r.pct_top_coincide)} % del top 50 · ρ {num(r.spearman_vs_base, 3)}')
        for r in sens.sort_values("pct_top_coincide").itertuples())

    filas_fuentes = "".join(
        f'<tr><td>{r.fuente}</td><td>{num(r.filas_bronce)}</td>'
        f'<td>{str(r.tabla_plata).split("silver_icesixuao_")[-1]}</td></tr>'
        for r in fuentes.sort_values("fuente").itertuples())

    peso_base = {p.parametro.replace("peso_base_", ""): float(p.valor)
                 for p in pesos.itertuples() if p.parametro.startswith("peso_base_")}
    nombres_peso = {"c_danio": "Daño satelital", "c_vulnerabilidad": "Vulnerabilidad (tipología GEM)",
                    "c_exposicion": "Exposición (ocupantes)", "c_suelo": "Suelo (amplificación)",
                    "c_altura": "Altura (pisos)", "c_acceso_salud": "Acceso a salud", "c_bloqueo_via": "Bloqueo de vía"}
    filas_pesos = "".join(barra(v * 100, 25, AZUL, nombres_peso[k], pct(v * 100, 0)) for k, v in peso_base.items())

    descartadas = [
        ("datos.cali.gov.co e IDESC (capas oficiales de Cali)", "fuera de línea desde el 21-oct-2026", "sustituidas por OSM (22 comunas, 338 barrios)"),
        ("Vs30 global del USGS", "grilla gruesa y sin microzonas oficiales", "grilla GEM TREQ de la microzonificación INGEOMINAS-DAGMA 2005"),
        ("Licuación global del USGS (Zhu 2017)", "ráster de ~1 km, no local", "susceptibilidad local de GEM (4.166 puntos)"),
        ("Shape__Area de la fuente", "viene en grados", "área recalculada en m² (EPSG:9377)"),
        ("Indice_Escombros como probabilidad", "daño en las dos colas; no es probabilidad", "severidad por categoría: escombros 1,0 · techo 0,7 · sin cambio 0,1"),
        ("ShakeMap dentro del índice", "describe el sismo que ya pasó y varía poco (MMI 6,4–7,1)", "se conserva como evidencia, validado con RAC2C (6,9) y DYFI (6,86)"),
        ("Ocupantes GEM como censo único", "el cruce es por cercanía: los ocupantes pueden repetirse entre predios", "se publica como ocupación modelada, con reutilización visible"),
        ("Educación OSM como albergues", "287 sitios mapeados no acreditan autorización ni capacidad", "no se usan como albergues"),
        ("NPISOS = 0 como error de carga", "99,5 % tienen EDIFPRED vacío: son lotes sin construcción registrada", "se conservan 1.234 lotes, fuera del ranking"),
        ("Deduplicar contornos repetidos", "9 grupos con categorías distintas: deduplicar inventaría o pierde", "se marcan y se documentan, sin borrar"),
        ("Amplificación faltante → factor 1", "inventaría respuesta del suelo", "queda NULL: una capa vacía produce distancia nula, nunca cero"),
        ("Pendiente GEM cuantitativa", "unidad del metadato sin confirmar", "solo se conserva como atributo, sin inferencias"),
    ]
    filas_descartadas = "".join(f'<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>' for a, b, c in descartadas)
    pendientes = [
        "Población por manzana del DANE y cifras UNGRD materializadas (hoy citadas solo como contexto)",
        "Capa vectorial oficial de microzonificación (hoy grilla GEM TREQ de ~750 m)",
        "Datasets comparables de otras ciudades: el catálogo existe, la comparación no está implementada",
        "Validación en terreno de una muestra: el satélite prioriza hipótesis, no certifica edificios",
    ]
    filas_pendientes = "".join(f"<li>{p}</li>" for p in pendientes)

    n_plata = len(reporte_plata["tablas"])
    n_oro = len(reporte_oro["tablas"])
    html = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dashboard de oro · icesixuao</title>
<style>
  :root {{ --bg:#0e1013; --panel:#15181d; --line:#262b33; --text:#e8e6e1; --muted:#8b919b;
          --acento:{ACENTO}; --verde:{VERDE}; --azul:{AZUL}; --mono:ui-monospace,Consolas,monospace; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text); font:14px/1.5 system-ui,sans-serif; }}
  .wrap {{ max-width:1180px; margin:0 auto; padding:28px 24px 60px; }}
  h1 {{ font-size:24px; margin:0 0 4px; letter-spacing:-.02em; }}
  h1 span {{ color:var(--acento); }}
  .sub {{ color:var(--muted); margin:0 0 18px; }}
  h2 {{ font:600 12px/1 var(--mono); text-transform:uppercase; letter-spacing:.12em;
       color:var(--muted); margin:34px 0 12px; border-top:1px solid var(--line); padding-top:18px; }}
  .aviso {{ border-left:3px solid var(--acento); background:#1d1714; color:#d9c9c2;
           padding:10px 12px; font-size:12.5px; margin-bottom:20px; }}
  .kpis {{ display:grid; grid-template-columns:repeat(6,1fr); gap:1px; background:var(--line);
          border:1px solid var(--line); }}
  .kpi {{ background:var(--panel); padding:12px; }}
  .kpi b {{ display:block; font:600 24px/1.1 var(--mono); }}
  .kpi small {{ color:var(--muted); font-size:11.5px; display:block; margin-top:3px; }}
  .kpi.hot b {{ color:var(--acento); }}
  .cols {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
  .panel {{ background:var(--panel); border:1px solid var(--line); padding:14px 16px; }}
  .fila-barra {{ display:grid; grid-template-columns:210px 1fr 320px; gap:10px; align-items:center;
                padding:5px 0; font-size:12.5px; }}
  .etq {{ color:var(--text); white-space:nowrap; }}
  .pista {{ background:#0b0d10; border:1px solid var(--line); height:16px; }}
  .lleno {{ height:100%; }}
  .val {{ color:var(--muted); font-size:11.5px; }}
  table {{ border-collapse:collapse; width:100%; font-size:12.5px; }}
  th {{ text-align:left; color:var(--muted); font:600 11px var(--mono); text-transform:uppercase;
       letter-spacing:.08em; border-bottom:1px solid var(--line); padding:6px 8px; }}
  td {{ border-bottom:1px solid var(--line); padding:6px 8px; vertical-align:top; }}
  td:first-child {{ color:var(--text); }}
  td {{ color:#c9cdd3; }}
  .conclusion li {{ margin:6px 0; }}
  .pie {{ color:var(--muted); font-size:11.5px; margin-top:34px; border-top:1px solid var(--line);
         padding-top:14px; }}
  .tag {{ display:inline-block; background:#1d1714; border:1px solid #5a2a22; color:var(--acento);
         font:600 11px var(--mono); padding:3px 8px; margin-left:8px; vertical-align:middle; }}
  @media (max-width:900px) {{ .kpis {{ grid-template-columns:repeat(3,1fr); }}
    .cols {{ grid-template-columns:1fr; }} .fila-barra {{ grid-template-columns:130px 1fr; }}
    .fila-barra .val {{ grid-column:1 / -1; }} }}
</style></head><body><div class="wrap">

<h1>Réplicas en Cali: <span>dónde inspeccionar primero</span></h1>
<p class="sub">DataBridge Hack 2026 · equipo icesixuao: Nicolas Zapato (Universidad Autónoma de Occidente) y
José David Rodríguez Pinilla (Universidad Icesi) · corrida {procesado:%d-%m-%Y %H:%M} · {remoto}</p>
<p class="sub">Mapa interactivo: <a href="./" style="color:var(--azul)">visor del equipo</a> ·
código: <a href="https://github.com/JOSED235/DataBridge-Hackaton-" style="color:var(--azul)">repositorio</a>
<span class="tag">publicación autorizada por la organización hasta el cierre del evento</span></p>
<p class="aviso">Los datos de edificios vienen de imágenes satelitales: sirven para priorizar, no para declarar
una edificación segura o insegura. La vulnerabilidad y la ocupación vienen de modelos (GEM); el cruce es por
cercanía, no por llave catastral. Las pruebas de asociación son exploratorias y no establecen causalidad. El índice
es un puntaje relativo de priorización, no una probabilidad de colapso.</p>

<h2>Conclusiones</h2>
<div class="panel conclusion"><ul>
<li><b>Dónde ir primero:</b> {num(int(mh.sum()))} edificios de prioridad muy alta ({pre85_mh} construidos hasta
1985; {num(ocup_mh)} ocupantes modelados). Empezar por la comuna 3, la de mayor índice: {c3_pre85} de sus
edificios son de 1985 o antes. La comuna 19 concentra la mayor ocupación modelada en edificios dañados.</li>
<li><b>El daño satelital no muestra un patrón claro:</b> con esta muestra no se detecta asociación con época,
uso, suelo, licuación ni comuna (ver p ajustado por Holm y V de Cramér en Factores). Un p alto no prueba que no
influyan. Por eso el índice combina lo observado con lo conocido de cada edificio.</li>
<li><b>Las fuentes externas cambian la lista:</b> sin ellas, solo el 40 % del top 50 se mantiene. La decisión de
prioridad depende de las fuentes tanto como del daño: por eso cada cifra se rastrea a su tabla.</li>
<li><b>Validación externa:</b> un estudio de la Javeriana Cali ubica el daño de Cali en edificios de 3 a 6 pisos
anteriores a 1984, con daño interior que el satélite casi no ve (Copernicus vio 21 edificaciones; hubo 1.538 reportes
locales). Ese grupo es el {cohorte_rank} del ranking y el {cohorte_mh} de la prioridad muy alta. No coincide en la
microzona 4C, que el índice no resalta (el suelo pesa 10 %).</li>
<li><b>Por qué suma ponderada y no PCA:</b> el primer componente principal explica solo el 26 % de la varianza; las
siete dimensiones son casi independientes, así que comprimirlas no simplifica y borraría los motivos por edificio.</li>
<li><b>Verificación en terreno aparte:</b> {num(int(reporte_oro["prioridades"].get("Sin dato: verificar en terreno", 0)))}
edificios sin dato satelital y {num(int(reporte_oro["prioridades"].get("Sin construcción registrada: verificar", 0)))}
predios sin construcción registrada no participan en el ranking: van a censo y verificación, no se suponen sanos.</li>
</ul></div>

<h2>Indicadores maestros</h2>
<div class="kpis">
  <div class="kpi"><b>{num(reporte_oro["n_predios"])}</b><small>edificios y lotes analizados</small></div>
  <div class="kpi hot"><b>{num(n_danio)}</b><small>con daño visible ({pct(100 * n_danio / len(predios))}; {num(n_lotes_danio)} son lotes)</small></div>
  <div class="kpi hot"><b>{num(ocup_unicos)}</b><small>ocupantes modelados en edificios dañados (GEM, sin duplicar; {num(ocup_por_predio)} por predio)</small></div>
  <div class="kpi hot"><b>179</b><small>prioridad muy alta</small></div>
  <div class="kpi"><b>435</b><small>sin dato satelital (8,5 %)</small></div>
  <div class="kpi"><b>1.234</b><small>lotes sin construcción registrada</small></div>
</div>

<h2>Ranking de comunas (p90 del índice entre edificios del ranking)</h2>
<div class="panel">{orden}</div>

<h2>Tabla por comuna (gold_icesixuao_comunas)</h2>
<div class="panel" style="overflow-x:auto"><table>
<tr><th>#</th><th>Comuna</th><th>p90</th><th>Predios</th><th>En ranking</th><th>Muy alta</th><th>Alta</th>
<th>Daño entre con dato</th><th>Sin dato</th><th>Ocupantes modelados con daño</th><th>Centros de salud</th></tr>
{filas_tabla_comunas}
</table>
<p style="color:var(--muted);font-size:12px;margin:10px 0 0">El p90 mide concentración de puntajes altos; los conteos de
prioridad miden volumen de trabajo. La comuna 19 tiene más edificios de prioridad muy alta, pero la 3 concentra puntajes
más altos. Ocupación sumada por predio: puede repetir registros GEM.</p></div>

<div class="cols">
<div><h2>Servicios urbanos cerca del daño</h2>
<div class="panel"><table>
<tr><th>Comuna</th><th>Predios con daño</th><th>A 200 m o menos de salud</th><th>A más de 1 km de urgencias</th><th>Pueden bloquear vía</th></tr>
{filas_servicios}
</table>
<p style="color:var(--muted);font-size:12px;margin:10px 0 0">Distancias euclidianas a sitios de OpenStreetMap; solo 23 de
439 centros de salud declaran urgencias. Proximidad no es capacidad ni tiempo de viaje.</p></div></div>

<div><h2>Colas de trabajo para brigadas</h2>
<div class="panel">{filas_colas}
<p style="color:var(--muted);font-size:12px;margin:10px 0 0">De los predios sin construcción registrada, {num(n_lotes_danio)}
muestran daño visible. El visor filtra por cola y comuna y descarga la lista en Excel, ordenada por prioridad.</p></div></div>
</div>

<h2>Prioridades de inspección ({num(total_prior)} registros)</h2>
<div class="panel">{filas_prior}</div>

<h2>Daño satelital por categoría (inventario completo)</h2>
<div class="panel">{barras_danio}</div>

<div class="cols">
<div><h2>¿Qué explica el daño? (exploratorio, no causal)</h2>
<div class="panel"><table>
<tr><th>Factor</th><th>n válidos</th><th>p χ²</th><th>p Holm</th><th>V Cramér</th><th>freq. esp. mín.</th><th>prueba</th></tr>
{filas_fact}
</table>
<p style="color:var(--muted);font-size:12px;margin:10px 0 0">Ninguna asociación significativa después de Holm;
la de comuna es la más cercana (p = {num(float(factores.loc[factores.factor == 'comuna', 'p_valor_chi2'].iloc[0]), 3)}).
Frecuencias esperadas bajas en estrato: sin prueba admisible. Independencia espacial no acreditada.</p></div></div>

<div><h2>¿Cuánto depende del índice de los supuestos?</h2>
<div class="panel">{filas_sens}
<p style="color:var(--muted);font-size:12px;margin:10px 0 0">Coincidencia del top 50 frente al escenario base
(ρ = Spearman sobre los {num(int(reporte_oro["n_en_ranking"]))} edificios del ranking). Pesos alternativos mueven
el orden; quitar las fuentes externas lo cambia: 40 %.</p></div></div>
</div>

<h2>¿Se puede resumir el índice? PCA de los siete componentes</h2>
<div class="panel">{filas_pca}
<p style="color:var(--muted);font-size:12px;margin:10px 0 0">Media de |r| entre componentes: {num(media_r, 2)}. No hay una
dimensión dominante: se combinan de forma aditiva con pesos explícitos para conservar los motivos de cada edificio.</p></div>

<div class="cols">
<div><h2>Pesos vigentes del índice</h2>
<div class="panel">{filas_pesos}
<p style="color:var(--muted);font-size:12px;margin:10px 0 0">Si un componente falta en un edificio, su peso se
reparte entre los disponibles; el faltante no castiga ni premia. Solo {n_altos} edificios tienen 11+ pisos:
la altura no marca tasa de daño medible en esta muestra.</p></div></div>

<div><h2>Calidad y trazabilidad</h2>
<div class="panel"><table>
<tr><th>Capa</th><th>Tablas</th><th>Controles</th><th>Verificación</th></tr>
<tr><td>Silver</td><td>{n_plata}</td><td>{n_ctrl_plata}</td><td>16 huellas SHA-256 de fuentes intactas</td></tr>
<tr><td>Gold</td><td>{n_oro}</td><td>{n_ctrl_oro}</td><td>huellas de plata revalidadas al consumir; mapa consistente</td></tr>
</table>
<p style="color:var(--muted);font-size:12px;margin:10px 0 0">Identidad una fila por OBJECTID; la publicación se detiene
si una llave se repite. Escrituras Delta individuales: la corrida incompleta no autoriza exportar el mapa.</p></div></div>
</div>

<h2>El abanico de datos: tomadas, descartadas y pendientes</h2>
<div class="panel">
<p style="margin:4px 0 8px"><b>Tomadas</b> — 16 fuentes materializadas en bronze (todo como texto y con huella
SHA-256), tipadas y cruzadas en silver:</p>
<table>
<tr><th>Fuente</th><th>Filas bronze</th><th>Tabla silver de destino</th></tr>
{filas_fuentes}
</table>
<p style="margin:14px 0 8px"><b>Vistas y descartadas o acotadas</b> — cada exclusión con su razón registrada en la
bitácora de decisiones:</p>
<table>
<tr><th>Se evaluó</th><th>Por qué no entró como estaba</th><th>Qué se hizo en su lugar</th></tr>
{filas_descartadas}
</table>
<p style="margin:14px 0 8px"><b>Pendientes (no inventadas):</b></p><ul style="margin:0 0 4px 18px;padding:0">{filas_pendientes}</ul>
</div>

<p class="pie">Cifras rastreables: gold_icesixuao_{{predios, comunas, afectaciones, factores, resumen_sensibilidad,
fuentes, parametros, calidad}} · silver_icesixuao_* (16 tablas) · reporte.json de cada capa. Generado por
scripts/generar_dashboard.py desde la corrida local de {procesado:%Y-%m-%d %H:%M}, con las mismas cifras que las tablas
gold publicadas en Databricks (13 tablas, 43 controles aprobados). Priorizar no es declarar seguro.</p>

</div></body></html>
"""
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(html, encoding="utf-8")
    print(f"Dashboard: {SALIDA}")


if __name__ == "__main__":
    main()
