# -*- coding: utf-8 -*-
"""
CLI del Radar Normativo.

    venv\\Scripts\\python.exe gestorias\\run_radar.py --dias 7
    venv\\Scripts\\python.exe gestorias\\run_radar.py --dias 7 --boletin

--dias N        ingesta y clasifica los BOE de los últimos N días (def. 7)
--solo-ingesta  descarga sin clasificar (no gasta API)
--boletin       además, genera el boletín para clientes del rango
"""
import argparse
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gestorias.radar import boe, classifier, digest, store  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Radar Normativo BOE para gestorias")
    parser.add_argument("--dias", type=int, default=7)
    parser.add_argument("--solo-ingesta", action="store_true")
    parser.add_argument("--boletin", action="store_true")
    args = parser.parse_args()

    hoy = dt.date.today()
    desde = hoy - dt.timedelta(days=args.dias - 1)
    conn = store.get_conn()

    print(f"[1/3] Ingesta BOE {desde} -> {hoy}")
    items = boe.sumarios_rango(desde, hoy)
    nuevos = store.upsert_items(conn, [it.as_dict() for it in items])
    print(f"  {len(items)} items leidos, {nuevos} nuevos")

    if not args.solo_ingesta:
        print("[2/3] Clasificacion")
        stats = classifier.clasificar_pendientes(conn)
        print(f"  descartados por prefiltro: {stats['descartados_prefiltro']}")
        print(f"  clasificados con LLM:      {stats['clasificados_llm']}")
        print(f"  fallback keywords:         {stats['clasificados_keywords']}")
        print(f"  relevantes:                {stats['relevantes']}")

    if args.boletin:
        print("[3/3] Boletin para clientes")
        md = digest.generar_boletin(conn, desde.isoformat(), hoy.isoformat())
        if md:
            print(f"  generado ({len(md)} caracteres), guardado en BD")
        else:
            print("  sin items relevantes en el rango")

    conn.close()
    print("OK")


if __name__ == "__main__":
    main()
