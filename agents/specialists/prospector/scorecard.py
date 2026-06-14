"""
Scorecard de Madurez Digital + Benchmark de nicho + Win Probability.

100% determinista (sin IA): instantáneo, consistente y sin coste de tokens.
Convierte el checklist web + señales de Google en un cuadro de mando tipo
auditoría (McKinsey/Deloitte adaptado a pymes locales), lo compara contra
el promedio del nicho en esa ciudad (algo que solo nosotros podemos hacer
porque escaneamos el nicho entero) y calcula la probabilidad de cierre.

Diseñado para enriquecerse con datos duros (PageSpeed real, tech stack) sin
romper la interfaz: cada dimensión se construye de señales ponderadas que se
pueden ampliar.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .models import Business, ChecklistWeb, Resena, PainPoint, ProspectorResult


# ── Una señal ponderada dentro de una dimensión ───────────────────────────────
@dataclass
class Senal:
    peso: float
    presente: bool
    ok: str       # etiqueta si la tiene
    falta: str    # etiqueta de oportunidad si no la tiene


def _nivel(score: float) -> str:
    if score >= 75:
        return "fuerte"
    if score >= 50:
        return "aceptable"
    if score >= 25:
        return "débil"
    return "crítico"


@dataclass
class Dimension:
    clave: str
    nombre: str
    icono: str
    peso: float                       # peso en el score global
    score: float = 0.0                # 0-100
    nivel: str = "crítico"
    senales_ok: List[str] = field(default_factory=list)
    senales_falta: List[str] = field(default_factory=list)

    @classmethod
    def desde_senales(cls, clave, nombre, icono, peso, senales: List[Senal]) -> "Dimension":
        total = sum(s.peso for s in senales) or 1
        logrado = sum(s.peso for s in senales if s.presente)
        score = round(logrado / total * 100, 1)
        return cls(
            clave=clave, nombre=nombre, icono=icono, peso=peso,
            score=score, nivel=_nivel(score),
            senales_ok=[s.ok for s in senales if s.presente],
            senales_falta=[s.falta for s in senales if not s.presente],
        )

    def to_dict(self) -> dict:
        return {
            "clave": self.clave, "nombre": self.nombre, "icono": self.icono,
            "peso": self.peso, "score": self.score, "nivel": self.nivel,
            "senales_ok": self.senales_ok, "senales_falta": self.senales_falta,
        }


@dataclass
class Scorecard:
    dimensiones: List[Dimension]
    score_global: float
    nivel_global: str
    # Benchmark de nicho (se rellena después con aplicar_benchmark)
    percentil_nicho: Optional[float] = None        # % de competidores por DEBAJO
    score_medio_nicho: Optional[float] = None
    tamano_muestra_nicho: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "dimensiones": [d.to_dict() for d in self.dimensiones],
            "score_global": self.score_global,
            "nivel_global": self.nivel_global,
            "percentil_nicho": self.percentil_nicho,
            "score_medio_nicho": self.score_medio_nicho,
            "tamano_muestra_nicho": self.tamano_muestra_nicho,
        }

    def dimension(self, clave: str) -> Optional[Dimension]:
        return next((d for d in self.dimensiones if d.clave == clave), None)


def _score_reputacion(business: Business, resenas: List[Resena]) -> Dimension:
    """Dimensión continua: rating + volumen + sentiment de reseñas minadas."""
    rating = business.rating or 0.0
    total = business.total_resenas or 0
    # Sub-score rating (3.5★ = 0, 5★ = 100)
    s_rating = max(0.0, min(100.0, (rating - 3.5) / 1.5 * 100)) if rating else 0.0
    # Sub-score volumen (0 reseñas = 0, 100+ = 100)
    s_volumen = max(0.0, min(100.0, total / 100 * 100))
    # Sub-score respuesta del negocio (proxy: reseñas con texto negativo sin gestionar)
    negativas = [r for r in resenas if r.rating <= 3 and r.texto]
    s_gestion = 100.0 if not negativas else max(0.0, 100 - len(negativas) * 20)

    score = round(s_rating * 0.45 + s_volumen * 0.30 + s_gestion * 0.25, 1)
    ok, falta = [], []
    (ok if rating >= 4.3 else falta).append(
        f"Rating {rating}★" if rating else "Sin rating en Google"
    )
    (ok if total >= 50 else falta).append(
        f"{total} reseñas" if total >= 50 else f"Pocas reseñas ({total})"
    )
    (ok if not negativas else falta).append(
        "Reputación limpia" if not negativas else f"{len(negativas)} reseñas negativas sin gestionar"
    )
    return Dimension(
        clave="reputacion", nombre="Reputación & Reseñas", icono="⭐", peso=1.2,
        score=score, nivel=_nivel(score), senales_ok=ok, senales_falta=falta,
    )


def construir_scorecard(
    business: Business,
    checklist: Optional[ChecklistWeb],
    resenas: List[Resena],
    tiempo_carga: Optional[float] = None,
    automation: Optional[dict] = None,
) -> Scorecard:
    """Construye el cuadro de mando de madurez digital (8 dimensiones)."""
    cl = checklist or ChecklistWeb()
    tiene_web = business.tiene_web
    carga_ok = (tiempo_carga is not None and tiempo_carga < 3.0) or cl.carga_rapida
    au = automation or {}

    dims: List[Dimension] = []

    # 1. Presencia & Rendimiento Web
    dims.append(Dimension.desde_senales(
        "presencia_web", "Presencia & Rendimiento Web", "🌐", 1.4, [
            Senal(3.0, tiene_web, "Tiene web propia", "Sin web propia (solo Google Maps)"),
            Senal(1.0, cl.tiene_https, "HTTPS seguro", "Sin HTTPS — Google penaliza"),
            Senal(1.5, carga_ok, "Carga rápida (<3s)", "Web lenta (>3s) — 53% abandona"),
            Senal(1.5, cl.es_mobile_responsive, "Optimizada para móvil", "No responsive — 70% del tráfico es móvil"),
        ],
    ))

    # 2. Conversión & Captación
    dims.append(Dimension.desde_senales(
        "conversion", "Conversión & Captación", "🎯", 1.3, [
            Senal(1.5, cl.tiene_cta_reserva, "CTA clara de reserva/contacto", "Sin llamada a la acción clara"),
            Senal(1.5, cl.tiene_formulario, "Formulario de captación", "Sin formulario — no captura leads"),
            Senal(1.0, cl.tiene_captura_email, "Captura de email", "No captura emails"),
        ],
    ))

    # 3. Automatización & IA 24/7 (el sello de MerakIA — peso alto)
    dims.append(Dimension.desde_senales(
        "automatizacion", "Automatización & IA 24/7", "🤖", 1.7, [
            Senal(2.5, au.get("tiene_chatbot_ia", False),
                  "Chatbot/agente IA en la web",
                  "Sin chatbot ni agente IA — nadie atiende la web fuera de horario"),
            Senal(2.0, au.get("tiene_whatsapp_automatizado", False),
                  "WhatsApp automatizado (IA)",
                  "WhatsApp sin automatizar — depende de una persona"),
            Senal(1.5, cl.tiene_reserva_online,
                  "Reserva/cita online 24/7",
                  "Sin reservas automáticas — depende del teléfono"),
        ],
    ))

    # 4. SEO & Visibilidad Local
    dims.append(Dimension.desde_senales(
        "seo_local", "SEO & Visibilidad Local", "🔍", 1.1, [
            Senal(1.5, cl.tiene_blog, "Blog/contenido SEO", "Sin contenido — invisible en búsquedas"),
            Senal(1.0, cl.tiene_gmb, "Enlace a Google Business", "Sin integración con Google Business"),
            Senal(0.8, cl.tiene_resenas_visibles, "Reseñas visibles en la web", "No muestra reseñas en la web"),
        ],
    ))

    # 5. Contenido & Autoridad
    dims.append(Dimension.desde_senales(
        "contenido", "Contenido & Autoridad", "📝", 0.9, [
            Senal(1.0, cl.tiene_testimonios, "Testimonios", "Sin testimonios — 92% lee reseñas antes de comprar"),
            Senal(1.0, cl.tiene_video, "Vídeo de presentación", "Sin vídeo — menos confianza y tiempo en página"),
            Senal(0.8, cl.tiene_galeria, "Galería de imágenes", "Sin galería visual"),
        ],
    ))

    # 6. Reputación & Reseñas (continua)
    dims.append(_score_reputacion(business, resenas))

    # 7. Datos & Analítica
    dims.append(Dimension.desde_senales(
        "datos", "Datos & Analítica", "📊", 0.8, [
            Senal(1.0, cl.tiene_pixel_tracking, "Píxel/analítica instalado", "Sin píxel — imposible remarketing ni medir"),
        ],
    ))

    # 8. Fidelización & Retención
    dims.append(Dimension.desde_senales(
        "fidelizacion", "Fidelización & Retención", "💌", 1.0, [
            Senal(1.0, cl.tiene_captura_email, "Base de datos de clientes (email)", "Sin base de datos para fidelizar"),
            Senal(1.0, cl.tiene_chat_whatsapp, "Canal directo de re-engagement", "Sin canal para reactivar clientes"),
        ],
    ))

    # Score global ponderado
    total_peso = sum(d.peso for d in dims) or 1
    score_global = round(sum(d.score * d.peso for d in dims) / total_peso, 1)

    return Scorecard(
        dimensiones=dims,
        score_global=score_global,
        nivel_global=_nivel(score_global),
    )


def aplicar_benchmark(results: List[ProspectorResult]) -> None:
    """
    Calcula el percentil de cada negocio frente al promedio del nicho.
    Modifica result.scorecard['percentil_nicho'] in-place.
    percentil = % de competidores con MENOR madurez digital (más bajo = más rezagado).
    """
    scores = [
        r.scorecard["score_global"]
        for r in results
        if r.scorecard and "score_global" in r.scorecard
    ]
    if len(scores) < 2:
        return
    media = round(sum(scores) / len(scores), 1)
    n = len(scores)
    for r in results:
        if not r.scorecard:
            continue
        propio = r.scorecard["score_global"]
        por_debajo = sum(1 for s in scores if s < propio)
        percentil = round(por_debajo / n * 100)
        r.scorecard["percentil_nicho"] = percentil
        r.scorecard["score_medio_nicho"] = media
        r.scorecard["tamano_muestra_nicho"] = n


# ── Win Probability ───────────────────────────────────────────────────────────
@dataclass
class WinProbability:
    score: int                       # 0-100
    nivel: str                       # muy alta / alta / media / baja
    componentes: List[dict]          # [{factor, valor, peso, aporta}]
    explicacion: str

    def to_dict(self) -> dict:
        return {
            "score": self.score, "nivel": self.nivel,
            "componentes": self.componentes, "explicacion": self.explicacion,
        }


def _nivel_win(s: int) -> str:
    if s >= 75:
        return "muy alta"
    if s >= 60:
        return "alta"
    if s >= 40:
        return "media"
    return "baja"


def calcular_win_probability(
    result: ProspectorResult,
    scorecard: Scorecard,
) -> WinProbability:
    """
    Probabilidad de cierre 0-100. Cuanto peor está el negocio (más margen de
    mejora) y más por detrás de su nicho, más fácil es venderle.
    """
    sg = scorecard.score_global
    pains = result.pains or []
    b = result.business

    # 1. Margen de mejora digital (a peor madurez, más para vender)
    margen = 100 - sg

    # 2. Posición vs nicho (cuánto por debajo de la media → urgencia competitiva)
    media = scorecard.score_medio_nicho
    if media is not None:
        vs_nicho = max(0.0, min(100.0, (media - sg) * 2 + 50))
    else:
        vs_nicho = 50.0  # neutro si no hay benchmark

    # 3. Urgencia máxima de los dolores detectados
    urgencia = max((p.urgencia for p in pains), default=5) * 10

    # 4. Accesibilidad de contacto (¿podemos llegar a ellos?)
    canales = sum([bool(b.telefono), bool(b.web), (b.total_resenas or 0) > 0])
    accesibilidad = min(100, canales / 3 * 100)

    # 5. Tracción/actividad (negocio vivo, ni muerto ni saturado)
    total = b.total_resenas or 0
    if total == 0:
        traccion = 25.0      # quizá inactivo
    elif total < 10:
        traccion = 60.0
    elif total <= 300:
        traccion = 100.0     # activo y manejable
    else:
        traccion = 80.0      # grande, puede ser más difícil de cerrar

    componentes = [
        ("Margen de mejora digital", round(margen), 0.35),
        ("Por detrás de su nicho", round(vs_nicho), 0.20),
        ("Urgencia del dolor", round(urgencia), 0.20),
        ("Accesibilidad de contacto", round(accesibilidad), 0.10),
        ("Tracción del negocio", round(traccion), 0.15),
    ]
    score = round(sum(v * p for _, v, p in componentes))
    score = max(0, min(100, score))
    nivel = _nivel_win(score)

    # Explicación: el factor que más aporta
    factor_top = max(componentes, key=lambda c: c[1] * c[2])
    if nivel in ("muy alta", "alta"):
        explicacion = (
            f"Prospecto caliente: {factor_top[0].lower()} es el motor "
            f"({factor_top[1]}/100). Hay mucho margen para venderle y cerrar rápido."
        )
    elif nivel == "media":
        explicacion = (
            "Prospecto con potencial pero requiere más trabajo de venta: "
            f"apóyate en {factor_top[0].lower()}."
        )
    else:
        explicacion = (
            "Difícil de cerrar: el negocio ya está bastante maduro digitalmente. "
            "Prioriza otros prospectos antes que este."
        )

    return WinProbability(
        score=score,
        nivel=nivel,
        componentes=[
            {"factor": f, "valor": v, "peso": p, "aporta": round(v * p, 1)}
            for f, v, p in componentes
        ],
        explicacion=explicacion,
    )
