"""
Combina señales de web + reseñas + ausencia de web para detectar
los dolores más críticos del negocio, priorizados por urgencia e impacto en ventas.
"""
import json
from typing import List, Tuple
import anthropic

from .models import Business, ChecklistWeb, Resena, PainPoint


class PainDetector:
    def __init__(self, client: anthropic.Anthropic):
        self.client = client

    def detectar(
        self,
        business: Business,
        checklist: ChecklistWeb | None,
        resenas: List[Resena],
    ) -> Tuple[List[PainPoint], int, str]:
        """
        Devuelve (pains_priorizados, score_oportunidad_0_100, resumen).
        score alto = lead muy caliente (muchos problemas, activo, sin presencia digital).
        """
        contexto = self._construir_contexto(business, checklist, resenas)

        prompt = f"""Eres un consultor de marketing digital especializado en encontrar oportunidades de negocio en empresas locales.

Analiza estos datos y determina cuáles son los 3-5 dolores más críticos de este negocio,
ordenados de MAYOR a MENOR impacto en sus ventas e ingresos.

DATOS DEL NEGOCIO:
{contexto}

INSTRUCCIONES:
- Prioriza dolores que directamente cuestan dinero al negocio HOY
- Si tienen reseñas que mencionen un problema específico, ese dolor es más urgente (tienen evidencia real)
- "Sin web" es siempre urgencia máxima
- Rating bajo (<4.0) con reseñas negativas sobre atención = dolor muy urgente
- No incluyas dolores menores o secundarios
- El score_oportunidad refleja qué tan caliente es este prospecto:
  100 = perfecto (muchos problemas críticos, sin presencia digital, activos en Google)
  0 = no vale la pena (todo optimizado, pocos problemas)

Responde ÚNICAMENTE con JSON válido, sin texto adicional:
{{
  "pains": [
    {{
      "categoria": "nombre_corto_sin_espacios",
      "descripcion": "descripción del problema en términos de pérdida económica para ellos",
      "servicio": "el servicio concreto que podríamos ofrecerles",
      "urgencia": 8,
      "evidencia": "la prueba específica encontrada (cita de reseña exacta o dato del análisis web)"
    }}
  ],
  "score_oportunidad": 75,
  "resumen": "en 1-2 frases por qué es un buen/mal prospecto y cuál es el argumento de venta más fuerte"
}}"""

        try:
            msg = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1200,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = msg.content[0].text.strip()
            # Limpiar posible markdown
            if raw.startswith("```"):
                raw = "\n".join(
                    l for l in raw.splitlines()
                    if not l.strip().startswith("```")
                )
            data = json.loads(raw)
        except Exception:
            return self._fallback(business, checklist, resenas)

        pains = []
        for p in data.get("pains", []):
            pains.append(PainPoint(
                categoria=p.get("categoria", "desconocido"),
                descripcion=p.get("descripcion", ""),
                servicio=p.get("servicio", ""),
                urgencia=min(10, max(1, int(p.get("urgencia", 5)))),
                evidencia=p.get("evidencia", ""),
            ))

        score = min(100, max(0, int(data.get("score_oportunidad", 50))))
        resumen = data.get("resumen", "")
        return pains, score, resumen

    def _construir_contexto(
        self,
        business: Business,
        checklist: ChecklistWeb | None,
        resenas: List[Resena],
    ) -> str:
        lines = [
            f"Nombre: {business.nombre}",
            f"Tipo de negocio: {business.tipo}",
            f"Ciudad: {business.ciudad}",
            f"Rating Google: {business.rating}/5 ({business.total_resenas} reseñas en total)",
        ]

        if not business.tiene_web:
            lines.append("⚠️ SIN SITIO WEB — Solo aparece en Google Maps, sin presencia web propia")
        else:
            lines.append(f"Web: {business.web}")
            if checklist:
                score = checklist.score()
                lines.append(f"Análisis web: {score}/15 puntos ({checklist.oportunidad()} oportunidad)")
                problemas = checklist.problemas()
                if problemas:
                    lines.append("Problemas detectados en la web:")
                    for prob in problemas:
                        lines.append(f"  - {prob}")

        negativas = [r for r in resenas if r.rating <= 3 and r.texto]
        if negativas:
            lines.append(f"\nReseñas negativas ({len(negativas)} de {len(resenas)} totales analizadas):")
            for r in negativas[:5]:
                lines.append(f"  [{r.rating}★] {r.autor}: \"{r.texto[:200]}\"")
        elif resenas:
            positivas = [r for r in resenas if r.rating >= 4]
            lines.append(f"\nReseñas: {len(positivas)} positivas, 0 negativas con texto relevante")

        return "\n".join(lines)

    def _fallback(
        self,
        business: Business,
        checklist: ChecklistWeb | None,
        resenas: List[Resena],
    ) -> Tuple[List[PainPoint], int, str]:
        """Pains básicos si Claude falla."""
        pains = []

        if not business.tiene_web:
            pains.append(PainPoint(
                categoria="sin_web",
                descripcion="Sin presencia web propia — pierden clientes que buscan online cada día",
                servicio="Landing page profesional + SEO local + Google My Business optimizado",
                urgencia=10,
                evidencia="No tiene sitio web registrado en Google Maps",
            ))

        if checklist:
            problemas = checklist.problemas()
            for i, prob in enumerate(problemas[:3]):
                pains.append(PainPoint(
                    categoria=f"web_gap_{i}",
                    descripcion=prob,
                    servicio="Optimización web integral",
                    urgencia=max(5, 8 - i),
                    evidencia="Detectado en análisis automático de su web",
                ))

        negativas = [r for r in resenas if r.rating <= 3]
        if negativas:
            pains.append(PainPoint(
                categoria="reputacion",
                descripcion=f"Reputación online deteriorada ({len(negativas)} reseñas negativas recientes)",
                servicio="Gestión de reputación online + protocolo de respuesta",
                urgencia=8,
                evidencia=negativas[0].texto[:150] if negativas[0].texto else "Múltiples reseñas negativas",
            ))

        score = 80 if not business.tiene_web else (
            60 if (checklist and checklist.score() < 6) else 40
        )
        return pains, score, "Prospecto detectado con oportunidades de mejora digital."
