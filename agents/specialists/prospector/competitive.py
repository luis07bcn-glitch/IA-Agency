"""
Análisis competitivo + Battle Cards.

Nuestra ventaja única: escaneamos el nicho entero, así que para un negocio
concreto podemos compararlo contra sus competidores REALES de la misma zona
sin pedir ningún dato extra. Genera:
  - Posición del negocio en el ranking de madurez del nicho
  - Gap analysis por dimensión (qué hace mejor/peor que la media)
  - Battle card: qué tiene el líder que el target no, listo para la reunión

100% determinista (a partir de los scorecards ya calculados).
"""
from typing import List, Optional, Dict

from .models import ProspectorResult


def analisis_competitivo(
    target: ProspectorResult,
    todos: List[ProspectorResult],
) -> Optional[dict]:
    """
    Compara `target` contra el resto de negocios del lote (su nicho local).
    Devuelve None si no hay suficientes competidores (<2 con scorecard).
    """
    con_sc = [r for r in todos if r.scorecard and "score_global" in r.scorecard]
    if len(con_sc) < 2 or not target.scorecard:
        return None

    # Ranking por madurez digital
    ranking = sorted(con_sc, key=lambda r: r.scorecard["score_global"], reverse=True)
    nombres = [r.business.nombre for r in ranking]
    try:
        posicion = nombres.index(target.business.nombre) + 1
    except ValueError:
        posicion = None
    total = len(ranking)

    lider = ranking[0]
    es_lider = lider.business.nombre == target.business.nombre
    media_global = round(
        sum(r.scorecard["score_global"] for r in con_sc) / len(con_sc), 1
    )

    # Gap por dimensión: media del nicho vs target
    dims_target = {d["clave"]: d for d in target.scorecard.get("dimensiones", [])}
    gap_dimensiones = []
    for clave, dt in dims_target.items():
        valores = [
            next((d["score"] for d in r.scorecard.get("dimensiones", []) if d["clave"] == clave), None)
            for r in con_sc
        ]
        valores = [v for v in valores if v is not None]
        if not valores:
            continue
        media_dim = round(sum(valores) / len(valores), 1)
        gap_dimensiones.append({
            "nombre": dt["nombre"],
            "icono": dt.get("icono", ""),
            "target": dt["score"],
            "media_nicho": media_dim,
            "brecha": round(dt["score"] - media_dim, 1),
        })
    gap_dimensiones.sort(key=lambda g: g["brecha"])  # peores brechas primero

    # Battle card: qué tienen los competidores que el target no
    # (carencias del target en las dimensiones donde va por detrás de la media)
    battle_card: List[str] = []
    if not es_lider:
        dims_lider = {d["clave"]: d for d in lider.scorecard.get("dimensiones", [])}
        for g in gap_dimensiones:
            if g["brecha"] >= 0:
                continue  # solo donde va por detrás
            clave = next((c for c, d in dims_target.items() if d["nombre"] == g["nombre"]), None)
            faltas = dims_target.get(clave, {}).get("senales_falta", []) if clave else []
            if faltas:
                tiene_lider = dims_lider.get(clave, {}).get("senales_ok", []) if clave else []
                pista = f" (el líder {lider.business.nombre} sí lo tiene)" if tiene_lider else ""
                battle_card.append(f"{g['icono']} {g['nombre']}: le falta {faltas[0].lower()}{pista}.")
        battle_card = battle_card[:5]

    # Ventajas a defender (dimensiones donde supera a la media)
    ventajas = [
        f"{g['icono']} {g['nombre']} (+{g['brecha']:.0f} sobre la media)"
        for g in gap_dimensiones if g["brecha"] > 5
    ][:3]

    return {
        "posicion": posicion,
        "total": total,
        "es_lider": es_lider,
        "lider_nombre": lider.business.nombre,
        "lider_score": lider.scorecard["score_global"],
        "media_nicho": media_global,
        "gap_dimensiones": gap_dimensiones,
        "battle_card": battle_card,
        "ventajas": ventajas,
    }


def aplicar_competitivo(results: List[ProspectorResult]) -> None:
    """Calcula y guarda el análisis competitivo de cada negocio del lote."""
    for r in results:
        try:
            r.competitive = analisis_competitivo(r, results)
        except Exception:
            r.competitive = None
