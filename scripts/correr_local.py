"""Pipeline local completo: materializa plata, consume sus tablas para oro y exporta mapa privado."""
from pathlib import Path
import json
from correr_plata import ejecutar_plata_local
from correr_oro import ejecutar_oro_local, cargar_api

RAIZ = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    _, reporte_plata, _ = ejecutar_plata_local()
    tablas, reporte, _ = ejecutar_oro_local()
    api = cargar_api()
    salida = RAIZ / "data/oficiales/salidas"
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "reporte_limpieza.json").write_text(json.dumps(reporte_plata, ensure_ascii=False, indent=2), encoding="utf-8")
    for carpeta in (salida, RAIZ / "visor/data"):
        api["exportar_visor"](tablas["predios"], tablas["comunas"], carpeta)
    for nombre, archivo in (("predios", "gold_edificios"), ("comunas", "gold_comunas"), ("resumen_sensibilidad", "gold_sensibilidad")):
        d = tablas[nombre].drop(columns="geometry", errors="ignore").copy()
        if nombre == "resumen_sensibilidad":
            d["top50_coincide_%"] = d.pct_top_coincide
        d.to_csv(salida / f"{archivo}.csv", index=False)
    print(json.dumps(reporte, ensure_ascii=False, indent=2))
    print(tablas["comunas"].drop(columns="geometry").to_string(index=False))
    print(tablas["resumen_sensibilidad"].to_string(index=False))
