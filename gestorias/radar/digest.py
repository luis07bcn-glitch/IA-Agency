# -*- coding: utf-8 -*-
"""
Generador del boletín para clientes del despacho.

Toma los items relevantes de un rango de fechas y redacta con Claude un
boletín en markdown que la gestoría puede reenviar tal cual (email, WhatsApp,
PDF) con su propia marca. Este es el entregable que diferencia: el despacho
queda como el que "siempre está al día" sin dedicarle horas.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import settings  # noqa: E402

from . import store

# El boletín es texto de cara al cliente final: aquí sí compensa un modelo top.
MODEL = os.getenv("RADAR_DIGEST_MODEL", "claude-sonnet-5")

_PROMPT = """Eres el responsable técnico de una gestoría española. Redacta el boletín normativo para los CLIENTES del despacho (pymes, autónomos, particulares) con las novedades de abajo.

Reglas:
- Lenguaje llano, cero jerga jurídica. El lector es un panadero o el gerente de una pyme, no un abogado.
- Estructura en markdown: título con el periodo, 2-3 frases de apertura, secciones por tema (solo las que tengan contenido): **Fiscal**, **Laboral y Seguridad Social**, **Ayudas y subvenciones**, **Otros**.
- Cada novedad: un titular corto en negrita, 1-3 frases sobre qué cambia y a quién afecta, y si procede una línea "→ Qué hacer: ...".
- Prioriza por impacto: lo de impacto alto primero y con más detalle; lo de impacto bajo puede ir agrupado en una línea.
- Si hay convenios colectivos, agrúpalos en una sola entrada listando sectores afectados.
- Cierra con: "Si alguna de estas novedades te afecta, escríbenos y lo revisamos contigo." y una línea de descargo: "Este boletín es un resumen divulgativo y no sustituye al asesoramiento profesional."
- NO inventes nada que no esté en los datos. No cites números de BOE ni artículos: eso va en el enlace.
- Incluye al final de cada novedad el enlace en formato [BOE](url).

PERIODO: del {desde} al {hasta}

NOVEDADES (JSON):
{items}

Responde SOLO con el markdown del boletín."""


def generar_boletin(conn, desde: str, hasta: str) -> str:
    """Genera el boletín del rango, lo guarda en BD y lo devuelve (markdown)."""
    items = store.items_relevantes(conn, desde, hasta)
    if not items:
        return ""
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY no configurada: no se puede redactar el boletín")

    compactos = [
        {
            "titulo": it["titulo"][:300],
            "resumen": it["resumen"],
            "afecta": it["afecta"],
            "accion": it["accion"],
            "impacto": it["impacto"],
            "areas": it["areas"],
            "url": it["url_html"],
        }
        for it in items
    ]
    import json
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    resp = client.messages.create(
        model=MODEL,
        max_tokens=6000,
        messages=[{
            "role": "user",
            "content": _PROMPT.format(
                desde=desde, hasta=hasta,
                items=json.dumps(compactos, ensure_ascii=False),
            ),
        }],
    )
    # El modelo puede emitir bloques de razonamiento antes del texto
    boletin = next(b.text for b in resp.content if b.type == "text").strip()
    store.guardar_boletin(conn, desde, hasta, boletin)
    return boletin
