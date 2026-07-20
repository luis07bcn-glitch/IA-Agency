# -*- coding: utf-8 -*-
"""
Clasificador de items del BOE para gestorías.

Dos etapas para controlar el coste de API:
1. Prefiltro por palabras clave y departamento — descarta el ~80% del BOE
   (nombramientos, defensa, condecoraciones...) sin gastar tokens.
2. Los candidatos pasan en lotes por Claude, que decide relevancia real,
   impacto, áreas y redacta el resumen/acción en llano.

Si no hay ANTHROPIC_API_KEY, la etapa 2 degrada a clasificación por keywords
(sin resumen redactado) para que el radar siga siendo utilizable.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import settings  # noqa: E402

# Barato y suficiente: clasifica títulos, no textos completos.
MODEL = os.getenv("RADAR_CLASSIFY_MODEL", "claude-haiku-4-5-20251001")
LOTE = 25  # items por llamada

# --- Etapa 1: prefiltro ------------------------------------------------------

DEPARTAMENTOS_CLAVE = re.compile(
    r"HACIENDA|TRABAJO|SEGURIDAD SOCIAL|INCLUSI|ECONOM|BANCO DE ESPA", re.I)

KEYWORDS = {
    "fiscal": r"impuest|tribut|irpf|iva\b|sociedades|aeat|agencia tributaria|"
              r"m[oó]dulos|catastr|aduaner|censal|recaudaci|verifactu|factur|"
              r"renta\b|patrimonio|declaraci[oó]n|liquidaci[oó]n|fiscal",
    "laboral": r"laboral|convenio colectivo|salario|n[oó]mina|empleo|"
               r"jornada|despido|erte\b|prevenci[oó]n de riesgos|contrataci[oó]n laboral",
    "seguridad_social": r"cotizaci[oó]n|seguridad social|aut[oó]nom|pensi[oó]n|"
                        r"prestaci[oó]n|incapacidad|jubilaci[oó]n",
    "mercantil": r"mercantil|sociedades de capital|concurs|blanqueo|auditor[ií]a de cuentas",
    "subvenciones": r"subvenci[oó]n|ayuda|bases reguladoras|bono|incentiv",
    "contable": r"contab|plan general de contabilidad|cuentas anuales",
    "otros": r"protecci[oó]n de datos|d[ií]as inh[aá]biles|inter[eé]s de demora|"
             r"salario m[ií]nimo|iprem",
}
_KEYWORDS_RE = {area: re.compile(patron, re.I) for area, patron in KEYWORDS.items()}


def prefiltro(item: dict) -> list[str]:
    """Devuelve las áreas que matchean por keywords ([] = descartable)."""
    texto = f"{item.get('titulo','')} {item.get('epigrafe','')}"
    areas = [area for area, rx in _KEYWORDS_RE.items() if rx.search(texto)]
    # Un convenio colectivo cualquiera matchea 'laboral'; un nombramiento en
    # Hacienda no matchea nada: el departamento solo rescata si hay duda.
    if not areas and DEPARTAMENTOS_CLAVE.search(item.get("departamento", "")):
        if re.search(r"resoluci[oó]n|orden|real decreto|circular", item.get("titulo", ""), re.I):
            areas = ["otros"]
    return areas


# --- Etapa 2: Claude ---------------------------------------------------------

_PROMPT = """Eres el socio director de una gestoría/asesoría española (clientes: pymes, autónomos y particulares). Evalúa estas publicaciones del BOE.

Para CADA item decide:
- relevante: true solo si un gestor debería enterarse (afecta a obligaciones fiscales, laborales, de Seguridad Social, mercantiles, contables o a ayudas que pueda tramitar para clientes). Convenios colectivos sectoriales SÍ son relevantes. Nombramientos, condecoraciones, oposiciones, asuntos militares o judiciales concretos NO.
- impacto: "alto" (obligación nueva o cambio que afecta a muchos clientes), "medio" (afecta a un sector o colectivo concreto), "bajo" (informativo).
- areas: subconjunto de ["fiscal","laboral","seguridad_social","mercantil","subvenciones","contable","otros"].
- resumen: 1-2 frases EN LENGUAJE LLANO explicando qué cambia. Sin jerga jurídica.
- afecta: a quién afecta ("todos los autónomos", "empresas del metal de Barcelona", "empleadores con trabajadores a tiempo parcial"...).
- accion: qué debería hacer el gestor ("revisar nóminas del sector X", "informar a clientes que...", "solo informativo").

ITEMS:
{items}

Responde SOLO con un array JSON válido, un objeto por item, con las claves: id, relevante, impacto, areas, resumen, afecta, accion. Sin markdown ni texto adicional."""

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic | None:
    global _client
    if _client is None and settings.anthropic_api_key:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def _parse_json(texto: str) -> list[dict]:
    texto = texto.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```(json)?\s*|\s*```$", "", texto)
    inicio, fin = texto.find("["), texto.rfind("]")
    if inicio == -1 or fin == -1:
        raise ValueError(f"Respuesta sin JSON: {texto[:200]}")
    return json.loads(texto[inicio:fin + 1])


def clasificar_lote_llm(items: list[dict]) -> list[dict]:
    """Clasifica un lote de items con Claude. items: dicts con identificador/titulo/..."""
    client = _get_client()
    if client is None:
        raise RuntimeError("Sin ANTHROPIC_API_KEY")

    listado = "\n".join(
        f'- id: {it["identificador"]} | sección {it["seccion"]} | {it["departamento"]}'
        f'{" | " + it["epigrafe"] if it.get("epigrafe") else ""}\n  "{it["titulo"][:400]}"'
        for it in items
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        messages=[{"role": "user", "content": _PROMPT.format(items=listado)}],
    )
    texto = next(b.text for b in resp.content if b.type == "text")
    return _parse_json(texto)


def clasificar_pendientes(conn, log=print) -> dict:
    """Clasifica todos los items pendientes de la BD. Devuelve contadores."""
    from . import store

    pendientes = [dict(r) for r in store.pendientes_de_clasificar(conn)]
    stats = {"descartados_prefiltro": 0, "clasificados_llm": 0,
             "clasificados_keywords": 0, "relevantes": 0}

    candidatos = []
    for it in pendientes:
        areas = prefiltro(it)
        if not areas:
            store.guardar_clasificacion(conn, it["identificador"], relevante=False,
                                        clasificado_por="prefiltro")
            stats["descartados_prefiltro"] += 1
        else:
            it["_areas_kw"] = areas
            candidatos.append(it)
    conn.commit()

    usar_llm = _get_client() is not None
    for i in range(0, len(candidatos), LOTE):
        lote = candidatos[i:i + LOTE]
        resultados = {}
        if usar_llm:
            try:
                resultados = {r["id"]: r for r in clasificar_lote_llm(lote)}
            except Exception as e:  # API caída/parse: degradar, no abortar la ingesta
                log(f"  [aviso] LLM fallo en lote {i // LOTE + 1}: {e} -> fallback keywords")
        for it in lote:
            r = resultados.get(it["identificador"])
            if r:
                store.guardar_clasificacion(
                    conn, it["identificador"],
                    relevante=bool(r.get("relevante")),
                    impacto=r.get("impacto", "bajo"),
                    areas=r.get("areas") or it["_areas_kw"],
                    resumen=r.get("resumen", ""),
                    afecta=r.get("afecta", ""),
                    accion=r.get("accion", ""),
                    clasificado_por="llm",
                )
                stats["clasificados_llm"] += 1
                stats["relevantes"] += int(bool(r.get("relevante")))
            else:
                # Fallback: lo marcamos relevante por keywords, sin resumen
                store.guardar_clasificacion(
                    conn, it["identificador"], relevante=True, impacto="medio",
                    areas=it["_areas_kw"], clasificado_por="keywords",
                )
                stats["clasificados_keywords"] += 1
                stats["relevantes"] += 1
        conn.commit()
        log(f"  clasificados {min(i + LOTE, len(candidatos))}/{len(candidatos)} candidatos")
    return stats
