# -*- coding: utf-8 -*-
"""
Clasificador de correos del despacho.

Claude Haiku en lotes (asunto + remitente + adjuntos + extracto); si no hay
API key o falla, degrada a reglas por keywords para que la bandeja siempre
quede ordenada.
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import settings  # noqa: E402

from .fuentes import Correo

MODEL = os.getenv("CORREO_CLASSIFY_MODEL", "claude-haiku-4-5-20251001")
LOTE = 20

CATEGORIAS = ("factura", "requerimiento", "documentacion", "consulta", "comercial", "otro")


@dataclass
class Clasificacion:
    uid: str
    categoria: str          # una de CATEGORIAS
    prioridad: str          # alta | media | baja
    resumen: str
    accion: str
    clasificado_por: str    # llm | keywords


_PROMPT = """Eres el responsable de la bandeja de entrada de una gestoría/asesoría española. Clasifica estos correos.

Categorías (elige UNA por correo):
- factura: el remitente envía facturas o tickets para contabilizar (típico: "facturas del trimestre"). Si los adjuntos parecen facturas, es esta categoría aunque el texto sea escueto.
- requerimiento: notificaciones o requerimientos de la administración (AEAT, Seguridad Social, DGT, ayuntamientos, juzgados). SIEMPRE prioridad alta.
- documentacion: el cliente envía documentos que no son facturas (DNI, contratos, escrituras, nóminas, certificados).
- consulta: un cliente pregunta algo o pide una gestión.
- comercial: publicidad, newsletters, proveedores de software, spam.
- otro: nada de lo anterior.

Prioridad: alta (requiere acción esta semana / administración / plazos), media (trabajo normal), baja (sin urgencia o comercial).

CORREOS:
{correos}

Responde SOLO con un array JSON, un objeto por correo: {{"uid","categoria","prioridad","resumen","accion"}}.
- resumen: 1 frase de qué va el correo.
- accion: siguiente paso concreto para el despacho ("contabilizar 3 facturas adjuntas", "acceder a la notificación electrónica antes del plazo", "responder al cliente", "archivar").
Sin markdown ni texto adicional."""

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic | None:
    global _client
    if _client is None and settings.anthropic_api_key:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


# --- Fallback por keywords ---------------------------------------------------

_REGLAS = [
    ("requerimiento", r"aeat|agencia tributaria|seguridad social|notificaci[oó]n electr[oó]nica|"
                      r"requerimiento|embargo|diligencia|sanci[oó]n|juzgado"),
    ("factura", r"factura|fra\.?\s|invoice|tickets?\b|gastos del trimestre|recibos"),
    ("documentacion", r"dni|nie\b|contrato|escritura|n[oó]mina|certificado|modelo \d{3}"),
    ("comercial", r"oferta|descuento|dto\.?|promo|newsletter|webinar|unsubscribe|baja aqu"),
]


def _clasificar_keywords(c: Correo) -> Clasificacion:
    texto = f"{c.asunto} {c.cuerpo} {' '.join(c.nombres_adjuntos)}".lower()
    for cat, patron in _REGLAS:
        if re.search(patron, texto, re.I):
            prioridad = "alta" if cat == "requerimiento" else ("media" if cat in ("factura", "documentacion") else "baja")
            return Clasificacion(c.uid, cat, prioridad, "", "", "keywords")
    # Adjuntos procesables sin más pistas → probablemente facturas
    if any(a.procesable for a in c.adjuntos):
        return Clasificacion(c.uid, "factura", "media", "", "", "keywords")
    return Clasificacion(c.uid, "consulta", "media", "", "", "keywords")


# --- LLM ----------------------------------------------------------------------

def _parse_json(texto: str) -> list[dict]:
    texto = texto.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```(json)?\s*|\s*```$", "", texto)
    inicio, fin = texto.find("["), texto.rfind("]")
    if inicio == -1 or fin == -1:
        raise ValueError(f"Respuesta sin JSON: {texto[:200]}")
    return json.loads(texto[inicio:fin + 1])


def _clasificar_lote_llm(correos: list[Correo]) -> dict[str, dict]:
    client = _get_client()
    listado = "\n\n".join(
        f"- uid: {c.uid}\n  De: {c.de}\n  Asunto: {c.asunto}\n"
        f"  Adjuntos: {', '.join(c.nombres_adjuntos) or 'ninguno'}\n"
        f"  Extracto: {c.cuerpo[:300] or '(vacío)'}"
        for c in correos
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=6000,
        messages=[{"role": "user", "content": _PROMPT.format(correos=listado)}],
    )
    texto = next(b.text for b in resp.content if b.type == "text")
    return {r["uid"]: r for r in _parse_json(texto)}


def clasificar(correos: list[Correo], log=print) -> list[Clasificacion]:
    """Clasifica todos los correos. LLM en lotes con fallback a keywords."""
    resultados: list[Clasificacion] = []
    usar_llm = _get_client() is not None

    for i in range(0, len(correos), LOTE):
        lote = correos[i:i + LOTE]
        por_uid: dict[str, dict] = {}
        if usar_llm:
            try:
                por_uid = _clasificar_lote_llm(lote)
            except Exception as e:
                log(f"  [aviso] LLM fallo en lote de correos: {e} -> fallback keywords")
        for c in lote:
            r = por_uid.get(c.uid)
            if r and r.get("categoria") in CATEGORIAS:
                resultados.append(Clasificacion(
                    uid=c.uid,
                    categoria=r["categoria"],
                    prioridad=r.get("prioridad", "media"),
                    resumen=r.get("resumen", ""),
                    accion=r.get("accion", ""),
                    clasificado_por="llm",
                ))
            else:
                resultados.append(_clasificar_keywords(c))
    return resultados
