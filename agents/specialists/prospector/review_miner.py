"""
Clasifica reseñas negativas de Google en categorías de dolor
y extrae las citas más impactantes para usar en el outreach.
Usa Claude Haiku (barato y rápido) para la clasificación.
"""
from typing import List
import anthropic

from .models import Resena

# Mapa de categorías → qué dolor revelan → qué servicio vender
PAIN_MAP = {
    "tiempo_respuesta": {
        "label": "Respuesta lenta / no contestan",
        "servicio": "Chatbot 24/7 + WhatsApp Business automatizado",
        "urgencia_base": 9,
    },
    "reservas_citas": {
        "label": "Difícil reservar / sin sistema online",
        "servicio": "Sistema de reservas online integrado",
        "urgencia_base": 9,
    },
    "atencion_cliente": {
        "label": "Mala atención al cliente",
        "servicio": "CRM + seguimiento automatizado + formación del equipo",
        "urgencia_base": 8,
    },
    "esperas": {
        "label": "Largas esperas",
        "servicio": "Gestión inteligente de citas + recordatorios automáticos",
        "urgencia_base": 7,
    },
    "informacion_web": {
        "label": "Web con poca información / difícil de encontrar",
        "servicio": "Rediseño web + SEO local + ficha de Google optimizada",
        "urgencia_base": 7,
    },
    "seguimiento": {
        "label": "No hacen seguimiento post-visita",
        "servicio": "Email marketing + CRM automatizado",
        "urgencia_base": 6,
    },
    "precio_valor": {
        "label": "Precio sin justificación / sin transparencia",
        "servicio": "Landing page con propuesta de valor clara",
        "urgencia_base": 6,
    },
    "otro": {
        "label": "Otros problemas",
        "servicio": "Consultoría digital personalizada",
        "urgencia_base": 4,
    },
}

VALID_CATEGORIES = list(PAIN_MAP.keys())


class ReviewMiner:
    def __init__(self, client: anthropic.Anthropic):
        self.client = client

    def procesar(self, resenas_raw: List[dict]) -> List[Resena]:
        """
        Recibe reseñas crudas de Google Places API y devuelve
        Resena[] con categoría de dolor asignada en las negativas.
        """
        resenas = []
        for r in resenas_raw:
            resena = Resena(
                autor=r.get("author_name", "Anónimo"),
                rating=r.get("rating", 3),
                texto=r.get("text", ""),
                fecha=r.get("relative_time_description"),
            )
            # Solo clasificar negativas con texto suficiente
            if resena.rating <= 3 and len(resena.texto) > 15:
                resena.categoria_dolor = self._clasificar(resena.texto)
            resenas.append(resena)
        return resenas

    def _clasificar(self, texto: str) -> str:
        """Clasifica una reseña negativa en una categoría de dolor usando Claude Haiku."""
        cats = ", ".join(VALID_CATEGORIES)
        try:
            msg = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=30,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Clasifica esta reseña negativa en UNA categoría de esta lista:\n"
                        f"{cats}\n\n"
                        f"Reseña: \"{texto[:300]}\"\n\n"
                        f"Responde SOLO con el nombre exacto de la categoría."
                    ),
                }],
            )
            result = msg.content[0].text.strip().lower().replace(" ", "_")
            for cat in VALID_CATEGORIES:
                if cat in result:
                    return cat
        except Exception:
            pass
        return "otro"

    def citas_impactantes(self, resenas: List[Resena], max_citas: int = 3) -> List[dict]:
        """
        Selecciona las citas más potentes para usar en el email de prospección.
        Prioriza: rating bajo + texto descriptivo + categorías de mayor urgencia.
        """
        alta_urgencia = {"tiempo_respuesta", "reservas_citas", "atencion_cliente"}
        negativas = [
            r for r in resenas
            if r.rating <= 3 and len(r.texto) > 20
        ]
        # Ordenar: primero alta urgencia, luego por rating ascendente
        negativas.sort(key=lambda r: (
            0 if r.categoria_dolor in alta_urgencia else 1,
            r.rating,
        ))

        citas = []
        for r in negativas[:max_citas]:
            texto = r.texto[:160] + "..." if len(r.texto) > 160 else r.texto
            citas.append({
                "texto": texto,
                "rating": r.rating,
                "autor": r.autor,
                "fecha": r.fecha or "",
                "categoria": r.categoria_dolor or "otro",
                "servicio": PAIN_MAP.get(r.categoria_dolor or "otro", {}).get("servicio", ""),
            })
        return citas

    def resumen_dolor_reviews(self, resenas: List[Resena]) -> str:
        """Genera un resumen en texto de los dolores detectados en las reseñas."""
        negativas = [r for r in resenas if r.rating <= 3 and r.texto]
        if not negativas:
            return ""

        conteo: dict[str, int] = {}
        for r in negativas:
            cat = r.categoria_dolor or "otro"
            conteo[cat] = conteo.get(cat, 0) + 1

        partes = []
        for cat, n in sorted(conteo.items(), key=lambda x: -x[1]):
            label = PAIN_MAP.get(cat, {}).get("label", cat)
            partes.append(f"{n} reseña(s) sobre '{label}'")

        return "; ".join(partes)
