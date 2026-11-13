"""Lectura y perfiles de calidad para los notebooks exploratorios de bronce.

No limpia ni sobrescribe los archivos originales. Los resultados se guardan
localmente en analisis_bronce/resultados/, excluido de Git.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import HTML, display


def raiz_proyecto() -> Path:
    """Encuentra la raíz sin depender del directorio desde el que se abre Jupyter."""
    for p in (Path.cwd(), *Path.cwd().parents):
        if (p / "CLAUDE.md").exists() and (p / "data/externos").is_dir():
            return p
    raise FileNotFoundError("Abrir el notebook dentro de DataBridge-Hackaton-")


RAIZ = raiz_proyecto()
SALIDAS = RAIZ / "analisis_bronce/resultados"
SALIDAS.mkdir(parents=True, exist_ok=True)
CRS_METROS = 9377


def huella(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def ficha(path: Path) -> dict[str, Any]:
    return {
        "archivo": str(path.relative_to(RAIZ)),
        "bytes": path.stat().st_size,
        "sha256": huella(path),
        "consulta_utc": datetime.now(timezone.utc).isoformat(),
    }


def leer_geojson(path: Path) -> tuple[dict, pd.DataFrame, gpd.GeoDataFrame]:
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    features = raw.get("features", [])
    props = pd.DataFrame([f.get("properties") or {} for f in features])
    if features:
        geo = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
    else:
        geo = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    assert len(props) == len(geo) == len(features)
    return raw, props, geo


def perfil(df: pd.DataFrame) -> pd.DataFrame:
    """Distingue nulos originales, cadenas vacías y espacios; no los modifica."""
    rows = []
    for col in df:
        s = df[col]
        nulos = s.isna()
        vacios = s.map(lambda v: isinstance(v, str) and v == "")
        espacios = s.map(lambda v: isinstance(v, str) and v != "" and not v.strip())
        unicos = s.dropna().map(lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False)).nunique()
        rows.append({
            "columna": col, "tipo_lectura": str(s.dtype),
            "tipos_originales": dict(Counter(type(v).__name__ for v in s[~nulos])),
            "nulos": int(nulos.sum()), "vacios": int(vacios.sum()),
            "solo_espacios": int(espacios.sum()), "distintos_no_nulos": int(unicos),
            "faltantes_pct": round(100 * (nulos | vacios | espacios).mean(), 2) if len(s) else None,
        })
    return pd.DataFrame(rows)


def mostrar_perfil(df: pd.DataFrame) -> pd.DataFrame:
    p = perfil(df)
    if p.empty:
        display(HTML("<p>Archivo vacío: no permite inferir esquema a partir de filas.</p>"))
    else:
        display(HTML("<details open><summary>Calidad por columna</summary>"
                     "<div style='max-height:520px;overflow:auto'>" +
                     p.to_html(index=False, escape=True) + "</div></details>"))
    return p


def geometria(g: gpd.GeoDataFrame) -> dict[str, Any]:
    if g.empty:
        return {"filas": 0, "crs": str(g.crs), "tipos": {}, "nulas": 0, "vacias": 0,
                "invalidas": 0, "duplicadas_exactas": 0, "bbox": None}
    no_nulas = g.geometry.notna()
    no_vacias = no_nulas & ~g.geometry.is_empty
    validas = g.geometry.is_valid
    coords = g.total_bounds.tolist()
    duplicate_count = int(g.loc[no_vacias].geometry.to_wkb().duplicated().sum())
    out = {"filas": len(g), "crs": str(g.crs), "tipos": g.geom_type.value_counts().to_dict(),
           "nulas": int((~no_nulas).sum()), "vacias": int(g.geometry.is_empty.sum()),
           "invalidas": int((no_vacias & ~validas).sum()),
           "duplicadas_exactas": duplicate_count, "bbox": coords,
           "con_z": int(g.geometry.has_z.sum())}
    assert out["nulas"] + out["vacias"] <= len(g)
    return out


def conteos(s: pd.Series, nombre: str = "categoria") -> pd.DataFrame:
    return s.fillna("Sin dato").value_counts(dropna=False).rename_axis(nombre).reset_index(name="filas")


def faltantes(df: pd.DataFrame, campos: list[str]) -> pd.DataFrame:
    p = perfil(df).set_index("columna") if len(df.columns) else pd.DataFrame()
    return pd.DataFrame([{
        "campo": c,
        "presentes": len(df) - int(p.loc[c, ["nulos", "vacios", "solo_espacios"]].sum()) if c in p.index else 0,
        "total": len(df),
        "columna_existe": c in df,
    } for c in campos])


def json_seguro(v: Any) -> Any:
    if isinstance(v, dict):
        return {str(k): json_seguro(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [json_seguro(x) for x in v]
    if isinstance(v, (np.integer, np.floating, np.bool_)):
        return json_seguro(v.item())
    if isinstance(v, (datetime, pd.Timestamp)):
        return v.isoformat()
    if isinstance(v, float) and not np.isfinite(v):
        return None
    return v


def guardar_resumen(nombre: str, datos: dict) -> None:
    (SALIDAS / f"{nombre}.json").write_text(
        json.dumps(json_seguro(datos), ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )


def grafico_barras(tabla: pd.DataFrame, titulo: str, archivo: str) -> None:
    """Guarda y muestra el gráfico agregado, sin coordenadas de predios."""
    if tabla.empty:
        return
    fig, ax = plt.subplots(figsize=(10, max(3.5, len(tabla) * .33)))
    ax.barh(tabla.iloc[:, 0].astype(str), tabla.iloc[:, 1], color="#226e86")
    ax.invert_yaxis()
    ax.set(title=titulo, xlabel=tabla.columns[1])
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(SALIDAS / f"{archivo}.png", dpi=150, bbox_inches="tight")
    plt.show()
