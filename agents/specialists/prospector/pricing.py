"""
Motor de pricing + ROI para ProspectorIA.

Determinista (sin IA): instantáneo, consistente y sin coste de tokens.
A partir del análisis real del negocio (dolores detectados + checklist web)
recomienda QUÉ servicios venderle, a QUÉ precio, y proyecta el ROI que
obtendría el cliente — la tabla "Sin / Con automatización" que cierra ventas.

Diferencia vs MKT Hackers: ellos parten de campos rellenados a mano; nosotros
partimos del diagnóstico real (web score, reseñas, pains), así la recomendación
y el ROI ya vienen justificados con evidencia.
"""
import unicodedata
from dataclasses import dataclass, field
from typing import List, Optional, Dict

from .models import ProspectorResult


def _normalizar(texto: str) -> str:
    """Minúsculas sin acentos, para comparar nichos de forma robusta."""
    t = unicodedata.normalize("NFKD", (texto or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c)).strip()


# ── Ticket medio por defecto según nicho (€ por cliente/venta) ────────────────
# Sirve para pre-rellenar el slider con un valor realista del sector.
TICKET_DEFAULT: Dict[str, float] = {
    "clínica dental": 600,
    "clínica estética": 400,
    "fisioterapia": 50,
    "veterinaria": 120,
    "restaurante": 35,
    "bar": 25,
    "cafetería": 18,
    "gimnasio": 45,
    "peluquería": 40,
    "inmobiliaria": 3000,
    "taller mecánico": 250,
    "farmacia": 25,
    "óptica": 180,
    "academia de idiomas": 120,
}

# Leads/mes y conversión típicos de partida para negocio local pequeño.
LEADS_DEFAULT = 200
CONVERSION_DEFAULT = 25.0  # %


# ── Catálogo de servicios ─────────────────────────────────────────────────────
# setup y mensual son rangos (min, max). El precio final se escala según el
# tier de ticket del cliente (agresivo / estándar / premium).
@dataclass
class Servicio:
    clave: str
    nombre: str
    descripcion: str
    setup: tuple          # (min, max) €
    mensual: tuple        # (min, max) €/mes
    kpi: str              # impacto medible para el ROI / la propuesta
    # Impacto en el modelo de ROI:
    uplift_conversion_pp: float = 0.0   # puntos porcentuales de conversión extra
    uplift_leads_pct: float = 0.0       # % más leads
    uplift_ingresos_pct: float = 0.0    # % más ingresos por recurrencia/LTV


CATALOGO: List[Servicio] = [
    Servicio(
        clave="web_conversion",
        nombre="Web profesional de conversión",
        descripcion="Página rápida, mobile-first, con CTA claro y captación de leads integrada.",
        setup=(900, 2800),
        mensual=(0, 0),
        kpi="+2 pp de conversión sobre las visitas actuales",
        uplift_conversion_pp=2.0,
    ),
    Servicio(
        clave="agente_whatsapp",
        nombre="Agente IA en WhatsApp 24/7",
        descripcion="Responde en segundos a cualquier hora, cualifica y agenda automáticamente.",
        setup=(600, 1600),
        mensual=(200, 450),
        kpi="Atiende el 100% de los leads (vs perder los de fuera de horario)",
        uplift_leads_pct=20.0,
        uplift_conversion_pp=1.5,
    ),
    Servicio(
        clave="reservas_online",
        nombre="Sistema de reservas online",
        descripcion="Reserva/cita en la web 24/7 con recordatorios automáticos anti no-show.",
        setup=(500, 1200),
        mensual=(90, 220),
        kpi="-40% de no-shows y citas captadas fuera de horario",
        uplift_conversion_pp=2.0,
    ),
    Servicio(
        clave="seguimiento_fidelizacion",
        nombre="Seguimiento y fidelización IA",
        descripcion="Follow-up post-visita, recordatorios, felicitaciones y reactivación de clientes.",
        setup=(400, 1000),
        mensual=(150, 320),
        kpi="+20% de recurrencia e ingresos del cliente existente",
        uplift_ingresos_pct=20.0,
    ),
    Servicio(
        clave="captacion_ads",
        nombre="Captación con Ads + IA",
        descripcion="Campañas optimizadas con IA que llevan tráfico cualificado a la web/agente.",
        setup=(1200, 2000),
        mensual=(600, 2500),
        kpi="+35% de leads nuevos al mes",
        uplift_leads_pct=35.0,
    ),
    Servicio(
        clave="seo_local",
        nombre="SEO local + contenido",
        descripcion="Posicionamiento en búsquedas locales y contenido que atrae pacientes/clientes nuevos.",
        setup=(600, 1500),
        mensual=(300, 600),
        kpi="Aparecer en las búsquedas locales del nicho",
        uplift_leads_pct=15.0,
    ),
]

CATALOGO_POR_CLAVE: Dict[str, Servicio] = {s.clave: s for s in CATALOGO}


@dataclass
class ServicioRecomendado:
    servicio: Servicio
    setup: float            # precio final calculado
    mensual: float          # precio final calculado
    motivo: str             # por qué se recomienda (evidencia del análisis)


@dataclass
class ROI:
    # Entradas
    leads_mes: float
    conversion_actual: float   # %
    ticket: float
    # Situación actual
    ventas_actual: float
    ingresos_actual: float
    # Situación proyectada
    leads_nuevo: float
    conversion_nueva: float
    ventas_nuevo: float
    ingresos_nuevo: float
    # Resultado
    ingreso_extra_mes: float
    inversion_setup: float
    inversion_mensual: float
    payback_meses: float
    roi_3m: float
    roi_6m: float
    roi_12m: float

    def to_dict(self) -> dict:
        return self.__dict__.copy()


class PricingCalculator:
    """Recomienda servicios, calcula precios y proyecta ROI. 100% determinista."""

    # ── Ticket por defecto ─────────────────────────────────────────────────
    @staticmethod
    def ticket_sugerido(tipo: str) -> float:
        tipo_l = _normalizar(tipo)
        for clave, valor in TICKET_DEFAULT.items():
            clave_n = _normalizar(clave)
            if clave_n in tipo_l or tipo_l in clave_n:
                return valor
        return 150.0  # genérico

    # ── Tier de precio según ticket del cliente ────────────────────────────
    @staticmethod
    def _factor_tier(ticket: float) -> float:
        """
        Ticket bajo → precio en la parte baja del rango (agresivo, para entrar).
        Ticket alto → precio en la parte alta (premium, el cliente lo soporta).
        Devuelve un factor 0..1 para interpolar dentro del rango (min, max).
        """
        if ticket < 100:
            return 0.10
        if ticket < 500:
            return 0.40
        if ticket < 2000:
            return 0.70
        return 1.0

    @classmethod
    def _precio(cls, rango: tuple, ticket: float) -> float:
        lo, hi = rango
        f = cls._factor_tier(ticket)
        return round(lo + (hi - lo) * f, -1)  # redondeo a la decena

    # ── Recomendación de servicios según el análisis ───────────────────────
    def recomendar(self, result: ProspectorResult, ticket: float) -> List[ServicioRecomendado]:
        """
        Decide qué servicios ofrecer en base a los dolores detectados y al
        checklist web. Devuelve la lista ordenada por relevancia (los que
        atacan dolores de mayor urgencia primero).
        """
        b = result.business
        cl = result.web_checklist
        claves: Dict[str, str] = {}  # clave_servicio -> motivo

        def add(clave: str, motivo: str):
            if clave not in claves:
                claves[clave] = motivo

        # 1) Señales de la WEB
        if not b.tiene_web:
            add("web_conversion", "No tiene web propia: solo aparece en Google Maps.")
            add("agente_whatsapp", "Sin canal digital para responder a clientes al instante.")
        elif cl:
            if cl.score() <= 8:
                add("web_conversion", f"Web con baja madurez digital ({cl.score()}/15).")
            if not cl.tiene_chat_whatsapp:
                add("agente_whatsapp", "Sin chat ni WhatsApp: no responde fuera de horario.")
            if not cl.tiene_reserva_online:
                add("reservas_online", "Sin reserva/cita online: depende del teléfono.")
            if not cl.tiene_captura_email:
                add("seguimiento_fidelizacion", "No captura emails: sin base de datos para fidelizar.")
            if not cl.tiene_blog:
                add("seo_local", "Sin blog ni contenido: invisible en búsquedas locales.")
            if not cl.tiene_pixel_tracking:
                add("captacion_ads", "Sin píxel de seguimiento: no puede hacer remarketing.")

        # 2) Señales de los DOLORES detectados (mapeo por categoría)
        mapa_pain = {
            "tiempo_respuesta": ("agente_whatsapp", "Reseñas se quejan de respuesta lenta."),
            "reservas_citas": ("reservas_online", "Clientes reportan dificultad para reservar."),
            "atencion_cliente": ("agente_whatsapp", "Quejas sobre atención al cliente."),
            "esperas": ("reservas_online", "Quejas por esperas y gestión de citas."),
            "informacion_web": ("web_conversion", "Falta información clave accesible online."),
            "seguimiento": ("seguimiento_fidelizacion", "Falta de seguimiento post-visita."),
        }
        for pain in result.pains:
            par = mapa_pain.get(pain.categoria)
            if par:
                add(par[0], par[1])

        # 3) Si hay pocas reseñas/leads, sugerir captación
        if (b.total_resenas or 0) < 30:
            add("captacion_ads", "Pocas reseñas: poca visibilidad y captación insuficiente.")

        # Fallback: siempre al menos la web + un agente
        if not claves:
            add("web_conversion", "Mejora base de presencia y conversión digital.")
            add("agente_whatsapp", "Atención automática 24/7 para no perder leads.")

        # Construir recomendaciones con precios
        recomendados = []
        for clave, motivo in claves.items():
            s = CATALOGO_POR_CLAVE[clave]
            recomendados.append(ServicioRecomendado(
                servicio=s,
                setup=self._precio(s.setup, ticket),
                mensual=self._precio(s.mensual, ticket),
                motivo=motivo,
            ))

        # Ordenar: primero los que más mueven la aguja (mayor uplift combinado)
        recomendados.sort(
            key=lambda r: (
                r.servicio.uplift_leads_pct
                + r.servicio.uplift_conversion_pp * 10
                + r.servicio.uplift_ingresos_pct
            ),
            reverse=True,
        )
        return recomendados

    # ── Proyección de ROI ──────────────────────────────────────────────────
    def proyectar_roi(
        self,
        leads_mes: float,
        conversion_actual: float,
        ticket: float,
        servicios: List[ServicioRecomendado],
    ) -> ROI:
        """
        Modela el impacto combinado de los servicios seleccionados sobre los
        ingresos del cliente. Conservador: aplica los upliftes una sola vez.
        """
        # Situación actual
        ventas_actual = leads_mes * conversion_actual / 100
        ingresos_actual = ventas_actual * ticket

        # Upliftes combinados
        up_leads = sum(s.servicio.uplift_leads_pct for s in servicios) / 100
        up_conv = sum(s.servicio.uplift_conversion_pp for s in servicios)
        up_ing = sum(s.servicio.uplift_ingresos_pct for s in servicios) / 100

        leads_nuevo = leads_mes * (1 + up_leads)
        conversion_nueva = min(conversion_actual + up_conv, 95.0)  # techo realista
        ventas_nuevo = leads_nuevo * conversion_nueva / 100
        ingresos_nuevo = ventas_nuevo * ticket * (1 + up_ing)

        ingreso_extra_mes = max(ingresos_nuevo - ingresos_actual, 0)

        inversion_setup = sum(s.setup for s in servicios)
        inversion_mensual = sum(s.mensual for s in servicios)

        beneficio_neto_mes = ingreso_extra_mes - inversion_mensual
        if beneficio_neto_mes > 0:
            payback = inversion_setup / beneficio_neto_mes
        else:
            payback = 999.0  # no se recupera con estos supuestos

        def roi_a(meses: int) -> float:
            ganancia = ingreso_extra_mes * meses
            coste = inversion_setup + inversion_mensual * meses
            if coste <= 0:
                return 0.0
            return round((ganancia - coste) / coste * 100, 1)

        return ROI(
            leads_mes=leads_mes,
            conversion_actual=conversion_actual,
            ticket=ticket,
            ventas_actual=round(ventas_actual, 1),
            ingresos_actual=round(ingresos_actual),
            leads_nuevo=round(leads_nuevo),
            conversion_nueva=round(conversion_nueva, 1),
            ventas_nuevo=round(ventas_nuevo, 1),
            ingresos_nuevo=round(ingresos_nuevo),
            ingreso_extra_mes=round(ingreso_extra_mes),
            inversion_setup=round(inversion_setup),
            inversion_mensual=round(inversion_mensual),
            payback_meses=round(payback, 1),
            roi_3m=roi_a(3),
            roi_6m=roi_a(6),
            roi_12m=roi_a(12),
        )
