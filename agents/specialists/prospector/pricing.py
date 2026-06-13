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
        kpi="+1,5 pp de conversión sobre las visitas actuales",
        uplift_conversion_pp=1.5,
    ),
    Servicio(
        clave="agente_whatsapp",
        nombre="Agente IA en WhatsApp 24/7",
        descripcion="Responde en segundos a cualquier hora, cualifica y agenda automáticamente.",
        setup=(600, 1600),
        mensual=(200, 450),
        kpi="Atiende el 100% de los leads (vs perder los de fuera de horario)",
        uplift_leads_pct=10.0,
        uplift_conversion_pp=1.0,
    ),
    Servicio(
        clave="reservas_online",
        nombre="Sistema de reservas online",
        descripcion="Reserva/cita en la web 24/7 con recordatorios automáticos anti no-show.",
        setup=(500, 1200),
        mensual=(90, 220),
        kpi="-40% de no-shows y citas captadas fuera de horario",
        uplift_conversion_pp=1.5,
        uplift_leads_pct=3.0,
    ),
    Servicio(
        clave="seguimiento_fidelizacion",
        nombre="Seguimiento y fidelización IA",
        descripcion="Follow-up post-visita, recordatorios, felicitaciones y reactivación de clientes.",
        setup=(400, 1000),
        mensual=(150, 320),
        kpi="+10% de recurrencia e ingresos del cliente existente",
        uplift_ingresos_pct=10.0,
    ),
    Servicio(
        clave="captacion_ads",
        nombre="Captación con Ads + IA",
        descripcion="Campañas optimizadas con IA que llevan tráfico cualificado a la web/agente.",
        setup=(1200, 2000),
        mensual=(600, 2500),
        kpi="+20-25% de leads nuevos al mes",
        uplift_leads_pct=22.0,
    ),
    Servicio(
        clave="seo_local",
        nombre="SEO local + contenido",
        descripcion="Posicionamiento en búsquedas locales y contenido que atrae pacientes/clientes nuevos.",
        setup=(600, 1500),
        mensual=(300, 600),
        kpi="Aparecer en las búsquedas locales del nicho",
        uplift_leads_pct=8.0,
    ),
]

CATALOGO_POR_CLAVE: Dict[str, Servicio] = {s.clave: s for s in CATALOGO}


# ── Paquetes (good / better / best) ───────────────────────────────────────────
# Anclaje de precio: presentar 3 niveles sube el ticket medio y hace que el del
# medio parezca la opción "sensata". El descuento crece con el tamaño del pack.
@dataclass
class Paquete:
    clave: str
    nombre: str
    tagline: str
    servicios: tuple          # claves del CATALOGO
    descuento_pct: float      # % de descuento sobre la suma de servicios
    ideal_para: str
    nivel: int                # 1=good, 2=better, 3=best


PAQUETES: List[Paquete] = [
    Paquete(
        clave="esencial",
        nombre="Esencial — Presencia que convierte",
        tagline="Lo mínimo para dejar de perder clientes online",
        servicios=("web_conversion", "agente_whatsapp"),
        descuento_pct=0.0,
        ideal_para="Negocios sin web o con web pobre que necesitan la base.",
        nivel=1,
    ),
    Paquete(
        clave="crecimiento",
        nombre="Crecimiento — Máquina de captación",
        tagline="Captar más, no perder ningún lead y fidelizar",
        servicios=("web_conversion", "agente_whatsapp", "reservas_online", "seguimiento_fidelizacion"),
        descuento_pct=10.0,
        ideal_para="El punto óptimo: la mayoría de negocios locales activos.",
        nivel=2,
    ),
    Paquete(
        clave="dominacion",
        nombre="Dominación Local — Líder del nicho",
        tagline="Ser el nº1 de su zona en Google y en captación",
        servicios=("web_conversion", "agente_whatsapp", "reservas_online",
                   "seguimiento_fidelizacion", "captacion_ads", "seo_local"),
        descuento_pct=15.0,
        ideal_para="Quien quiere liderar su nicho y aplastar a la competencia.",
        nivel=3,
    ),
]

PAQUETES_POR_CLAVE: Dict[str, Paquete] = {p.clave: p for p in PAQUETES}


@dataclass
class ServicioRecomendado:
    servicio: Servicio
    setup: float            # precio final calculado
    mensual: float          # precio final calculado
    motivo: str             # por qué se recomienda (evidencia del análisis)


@dataclass
class PerdidaDolor:
    """Dinero que el negocio pierde HOY por una carencia concreta (€/mes)."""
    concepto: str
    euros_mes: float
    explicacion: str
    servicio: str           # qué servicio lo resuelve

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class PaqueteCotizado:
    """Un paquete con precios calculados y su ROI proyectado para el cliente."""
    paquete: Paquete
    servicios: List[ServicioRecomendado]
    setup: float            # ya con descuento aplicado
    mensual: float          # ya con descuento aplicado
    setup_sin_descuento: float
    mensual_sin_descuento: float
    recomendado: bool
    roi: "ROI"

    def to_dict(self) -> dict:
        return {
            "clave": self.paquete.clave,
            "nombre": self.paquete.nombre,
            "tagline": self.paquete.tagline,
            "nivel": self.paquete.nivel,
            "ideal_para": self.paquete.ideal_para,
            "descuento_pct": self.paquete.descuento_pct,
            "servicios": [s.servicio.nombre for s in self.servicios],
            "setup": self.setup,
            "mensual": self.mensual,
            "setup_sin_descuento": self.setup_sin_descuento,
            "mensual_sin_descuento": self.mensual_sin_descuento,
            "recomendado": self.recomendado,
            "roi": self.roi.to_dict(),
        }


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
        factor_optimismo: float = 1.0,
    ) -> ROI:
        """
        Modela el impacto combinado de los servicios seleccionados sobre los
        ingresos del cliente. Conservador: aplica los upliftes una sola vez.

        factor_optimismo escala los upliftes para el simulador de escenarios:
        0.6 conservador / 1.0 realista / 1.4 optimista.
        """
        # Situación actual
        ventas_actual = leads_mes * conversion_actual / 100
        ingresos_actual = ventas_actual * ticket

        # Upliftes combinados con saturación (no se acumulan linealmente) y
        # escalados por el factor del simulador. Techos por categoría para que
        # los números sigan siendo creíbles aunque se sumen muchos servicios.
        f = factor_optimismo

        # Leads: OR probabilístico → 1 - Π(1 - u_i). Satura por debajo del 100%.
        prod = 1.0
        for s in servicios:
            prod *= (1 - min(s.servicio.uplift_leads_pct / 100, 0.9))
        up_leads = min((1 - prod) * f, 0.45)            # techo +45% leads

        # Conversión: suma aditiva en pp, con techo de +8 pp
        up_conv = min(sum(s.servicio.uplift_conversion_pp for s in servicios) * f, 8.0)

        # Ingresos por recurrencia/LTV: techo +20%
        up_ing = min(sum(s.servicio.uplift_ingresos_pct for s in servicios) / 100 * f, 0.20)

        leads_nuevo = leads_mes * (1 + up_leads)
        conversion_nueva = min(conversion_actual + up_conv, 60.0)  # techo realista
        ventas_nuevo = leads_nuevo * conversion_nueva / 100
        ingresos_nuevo = ventas_nuevo * ticket * (1 + up_ing)

        ingreso_extra_mes = max(ingresos_nuevo - ingresos_actual, 0)
        # Techo de credibilidad global: el incremento de ingresos no supera el
        # 55% de la facturación actual (un +55% ya es un resultado excelente).
        ingreso_extra_mes = min(ingreso_extra_mes, ingresos_actual * 0.55)
        # Reajustar ingresos_nuevo al extra capado para que la tabla cuadre
        ingresos_nuevo = ingresos_actual + ingreso_extra_mes

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

    # ── Dinero sobre la mesa: pérdidas actuales por cada carencia ──────────────
    def calcular_perdidas(
        self,
        result: ProspectorResult,
        ticket: float,
        leads_mes: float,
        conversion_actual: float,
    ) -> List[PerdidaDolor]:
        """
        Estima cuánto dinero pierde el negocio HOY por cada carencia detectada.
        Es el artefacto de venta más potente: no proyecta ganancias futuras,
        cuantifica la sangría actual ("pierdes X€/mes por no tener Y").

        Modelos conservadores, todos en €/mes:
          - Sin reserva 24/7 / sin chat → leads fuera de horario que se evaporan
          - Web lenta o no responsive → rebote (53% abandona si tarda >3s)
          - Sin captación (CTA/formulario) → conversión por debajo de potencial
          - Sin fidelización (email) → recurrencia perdida del cliente existente
          - Reputación baja (<4★) → clientes que eligen a la competencia
        """
        cl = result.web_checklist
        b = result.business
        conv = max(conversion_actual, 1.0) / 100
        ventas_base = leads_mes * conv  # ventas/mes actuales estimadas
        perdidas: List[PerdidaDolor] = []

        sin_web = not b.tiene_web

        # 1. Sin canal 24/7 (reservas online o chat/WhatsApp)
        if sin_web or (cl and not cl.tiene_reserva_online and not cl.tiene_chat_whatsapp):
            leads_fuera = leads_mes * 0.25  # ~25% del interés llega fuera de horario
            ventas_perdidas = leads_fuera * conv * 0.6  # captvariamos el 60%
            euros = ventas_perdidas * ticket
            if euros > 0:
                perdidas.append(PerdidaDolor(
                    concepto="Leads fuera de horario sin atender",
                    euros_mes=round(euros),
                    explicacion=f"~{round(leads_fuera)} contactos/mes llegan fuera de horario y no hay quién responda (sin reservas 24/7 ni chat).",
                    servicio="Agente IA WhatsApp 24/7 + reservas online",
                ))

        # 2. Web lenta o no responsive → rebote
        if cl and (not cl.carga_rapida or not cl.es_mobile_responsive):
            factor = 0.20 if not cl.carga_rapida else 0.12
            ventas_perdidas = leads_mes * factor * conv
            euros = ventas_perdidas * ticket
            if euros > 0:
                motivo = "Web lenta (>3s)" if not cl.carga_rapida else "Web no optimizada para móvil"
                perdidas.append(PerdidaDolor(
                    concepto="Abandono por mala experiencia web",
                    euros_mes=round(euros),
                    explicacion=f"{motivo}: el 53% abandona si tarda más de 3s. Pierdes ~{round(leads_mes*factor)} visitas cualificadas/mes.",
                    servicio="Web profesional de conversión",
                ))

        # 3. Sin captación clara (CTA + formulario)
        if sin_web or (cl and (not cl.tiene_cta_reserva or not cl.tiene_formulario)):
            # 2 pp de conversión por debajo de su potencial
            ventas_perdidas = leads_mes * 0.02
            euros = ventas_perdidas * ticket
            if euros > 0:
                perdidas.append(PerdidaDolor(
                    concepto="Conversión por debajo de potencial",
                    euros_mes=round(euros),
                    explicacion="Sin CTA clara ni formulario, la web no convierte visitas en clientes (≈2 pp de conversión perdidos).",
                    servicio="Web de conversión + captación de leads",
                ))

        # 4. Sin fidelización (sin email DB)
        if not sin_web and cl and not cl.tiene_captura_email:
            ingresos_actual = ventas_base * ticket
            euros = ingresos_actual * 0.15  # 15% de recurrencia perdida
            if euros > 0:
                perdidas.append(PerdidaDolor(
                    concepto="Recurrencia perdida (clientes que no vuelven)",
                    euros_mes=round(euros),
                    explicacion="Sin base de datos de clientes no hay seguimiento ni reactivación: se pierde ~15% de la recurrencia.",
                    servicio="Seguimiento y fidelización IA",
                ))

        # 5. Reputación baja (<4★) → fuga a la competencia
        if b.rating and b.rating < 4.0 and b.total_resenas:
            ventas_perdidas = leads_mes * 0.15 * conv
            euros = ventas_perdidas * ticket
            if euros > 0:
                perdidas.append(PerdidaDolor(
                    concepto="Clientes que eligen a la competencia",
                    euros_mes=round(euros),
                    explicacion=f"Rating {b.rating}★: el 92% lee reseñas antes de decidir y muchos descartan por debajo de 4★.",
                    servicio="Gestión de reputación + protocolo de reseñas",
                ))

        # Techo de credibilidad: las pérdidas se solapan, así que la suma no
        # debe superar el 45% de los ingresos actuales (si no, nadie se lo cree).
        ingresos_actual = ventas_base * ticket
        techo = ingresos_actual * 0.45
        total = sum(p.euros_mes for p in perdidas)
        if techo > 0 and total > techo:
            factor = techo / total
            for p in perdidas:
                p.euros_mes = round(p.euros_mes * factor)

        perdidas.sort(key=lambda p: p.euros_mes, reverse=True)
        return [p for p in perdidas if p.euros_mes > 0]

    @staticmethod
    def total_perdidas(perdidas: List[PerdidaDolor]) -> float:
        return round(sum(p.euros_mes for p in perdidas))

    # ── Paquetes good/better/best + simulador ──────────────────────────────────
    def recomendar_paquete(self, result: ProspectorResult, ticket: float) -> str:
        """
        Decide qué paquete marcar como 'recomendado' según el análisis.
        Cubre los servicios que de verdad necesita, sin pasarse (anclaje al medio).
        """
        necesarios = {r.servicio.clave for r in self.recomendar(result, ticket)}
        # El paquete más pequeño que cubra la mayoría de lo necesario
        for paq in PAQUETES:  # de menor a mayor
            cubiertos = necesarios & set(paq.servicios)
            if necesarios and len(cubiertos) >= max(1, int(len(necesarios) * 0.7)):
                return paq.clave
        return "crecimiento"  # por defecto, el del medio

    def cotizar_paquetes(
        self,
        result: ProspectorResult,
        ticket: float,
        leads_mes: float,
        conversion_actual: float,
        factor_optimismo: float = 1.0,
    ) -> List[PaqueteCotizado]:
        """
        Cotiza los 3 paquetes con sus precios (con descuento) y el ROI que
        obtendría el cliente con cada uno. Base del simulador de escenarios.
        """
        clave_reco = self.recomendar_paquete(result, ticket)
        cotizados: List[PaqueteCotizado] = []

        for paq in PAQUETES:
            servicios = []
            for clave in paq.servicios:
                s = CATALOGO_POR_CLAVE[clave]
                servicios.append(ServicioRecomendado(
                    servicio=s,
                    setup=self._precio(s.setup, ticket),
                    mensual=self._precio(s.mensual, ticket),
                    motivo="",
                ))
            setup_bruto = sum(s.setup for s in servicios)
            mensual_bruto = sum(s.mensual for s in servicios)
            desc = paq.descuento_pct / 100
            setup = round(setup_bruto * (1 - desc), -1)
            mensual = round(mensual_bruto * (1 - desc), -1)

            roi = self.proyectar_roi(
                leads_mes, conversion_actual, ticket, servicios, factor_optimismo
            )
            # Recalcular ROI con el precio del paquete (con descuento), no la suma bruta
            roi.inversion_setup = setup
            roi.inversion_mensual = mensual
            beneficio = roi.ingreso_extra_mes - mensual
            roi.payback_meses = round(setup / beneficio, 1) if beneficio > 0 else 999.0
            for meses, attr in [(3, "roi_3m"), (6, "roi_6m"), (12, "roi_12m")]:
                coste = setup + mensual * meses
                ganancia = roi.ingreso_extra_mes * meses
                setattr(roi, attr, round((ganancia - coste) / coste * 100, 1) if coste > 0 else 0.0)

            cotizados.append(PaqueteCotizado(
                paquete=paq,
                servicios=servicios,
                setup=setup,
                mensual=mensual,
                setup_sin_descuento=round(setup_bruto, -1),
                mensual_sin_descuento=round(mensual_bruto, -1),
                recomendado=(paq.clave == clave_reco),
                roi=roi,
            ))
        return cotizados
