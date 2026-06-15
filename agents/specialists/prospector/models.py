from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Business:
    place_id: str
    nombre: str
    tipo: str
    ciudad: str
    direccion: str
    telefono: Optional[str] = None
    web: Optional[str] = None
    rating: Optional[float] = None
    total_resenas: Optional[int] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    tiene_web: bool = False
    nombre_propietario: Optional[str] = None
    gbp_raw: Optional[dict] = None       # campos crudos de Places API para auditoría GBP


@dataclass
class ChecklistWeb:
    tiene_formulario: bool = False
    tiene_chat_whatsapp: bool = False
    carga_rapida: bool = False
    es_mobile_responsive: bool = False
    tiene_https: bool = False
    tiene_cta_reserva: bool = False
    tiene_reserva_online: bool = False
    tiene_testimonios: bool = False
    tiene_video: bool = False
    tiene_galeria: bool = False
    tiene_blog: bool = False
    tiene_pixel_tracking: bool = False
    tiene_captura_email: bool = False
    tiene_gmb: bool = False
    tiene_resenas_visibles: bool = False

    def score(self) -> int:
        return sum([
            self.tiene_formulario, self.tiene_chat_whatsapp, self.carga_rapida,
            self.es_mobile_responsive, self.tiene_https, self.tiene_cta_reserva,
            self.tiene_reserva_online, self.tiene_testimonios, self.tiene_video,
            self.tiene_galeria, self.tiene_blog, self.tiene_pixel_tracking,
            self.tiene_captura_email, self.tiene_gmb, self.tiene_resenas_visibles,
        ])

    def oportunidad(self) -> str:
        s = self.score()
        if s <= 5:
            return "alta"
        if s <= 10:
            return "media"
        return "baja"

    def problemas(self) -> List[str]:
        p = []
        if not self.tiene_formulario:
            p.append("Sin formulario de contacto para capturar leads")
        if not self.tiene_chat_whatsapp:
            p.append("Sin chat ni botón de WhatsApp — los clientes no pueden contactar al instante")
        if not self.carga_rapida:
            p.append("Web lenta (>3 segundos) — el 53% de usuarios abandona si tarda más")
        if not self.es_mobile_responsive:
            p.append("No optimizada para móviles — el 70% del tráfico local viene de móvil")
        if not self.tiene_https:
            p.append("Sin HTTPS — Google penaliza el posicionamiento y los usuarios desconfían")
        if not self.tiene_cta_reserva:
            p.append("Sin botón claro de reserva — los clientes no saben qué hacer")
        if not self.tiene_reserva_online:
            p.append("Sin sistema de reserva online — dependen del teléfono y pierden citas fuera de horario")
        if not self.tiene_testimonios:
            p.append("Sin testimonios visibles — el 92% de consumidores lee reseñas antes de comprar")
        if not self.tiene_blog:
            p.append("Sin blog ni contenido SEO — invisible en búsquedas de Google")
        if not self.tiene_pixel_tracking:
            p.append("Sin píxel de seguimiento — imposible hacer remarketing a visitas")
        if not self.tiene_captura_email:
            p.append("No captura emails — sin base de datos propia de clientes")
        if not self.tiene_video:
            p.append("Sin vídeo de presentación — baja confianza y tiempo en página")
        return p

    def to_dict(self) -> dict:
        return {
            "tiene_formulario": self.tiene_formulario,
            "tiene_chat_whatsapp": self.tiene_chat_whatsapp,
            "carga_rapida": self.carga_rapida,
            "es_mobile_responsive": self.es_mobile_responsive,
            "tiene_https": self.tiene_https,
            "tiene_cta_reserva": self.tiene_cta_reserva,
            "tiene_reserva_online": self.tiene_reserva_online,
            "tiene_testimonios": self.tiene_testimonios,
            "tiene_video": self.tiene_video,
            "tiene_galeria": self.tiene_galeria,
            "tiene_blog": self.tiene_blog,
            "tiene_pixel_tracking": self.tiene_pixel_tracking,
            "tiene_captura_email": self.tiene_captura_email,
            "tiene_gmb": self.tiene_gmb,
            "tiene_resenas_visibles": self.tiene_resenas_visibles,
        }


@dataclass
class Resena:
    autor: str
    rating: int
    texto: str
    fecha: Optional[str] = None
    categoria_dolor: Optional[str] = None


@dataclass
class PainPoint:
    categoria: str
    descripcion: str
    servicio: str
    urgencia: int  # 1-10
    evidencia: str


@dataclass
class ProspectorResult:
    business: Business
    web_checklist: Optional[ChecklistWeb] = None
    tiempo_carga: Optional[float] = None
    resenas: List[Resena] = field(default_factory=list)
    pains: List[PainPoint] = field(default_factory=list)
    score_oportunidad: int = 0
    resumen_oportunidad: str = ""

    # Outreach generado
    email_asunto: Optional[str] = None
    email_cuerpo: Optional[str] = None
    whatsapp_mensaje: Optional[str] = None
    script_llamada: Optional[str] = None

    # Scorecard de madurez digital + benchmark + win probability (deterministas)
    scorecard: Optional[dict] = None          # Scorecard.to_dict()
    win_probability: Optional[dict] = None     # WinProbability.to_dict()

    # Datos duros (Bloque 2)
    tech_stack: Optional[dict] = None          # {categoria: [herramientas]}
    pagespeed: Optional[dict] = None           # PageSpeedResult.to_dict()
    competitive: Optional[dict] = None         # análisis competitivo + battle card
    automation: Optional[dict] = None          # PerfilAutomatizacion.to_dict() (sistemas autónomos / IA)
    gbp_audit: Optional[dict] = None           # PerfilGBP.to_dict() (auditoría Google Business Profile)

    # Pricing & ROI (motor de ventas)
    ticket_promedio: Optional[float] = None
    leads_mensuales: Optional[int] = None
    conversion_actual: Optional[float] = None
    servicios_recomendados: List[dict] = field(default_factory=list)
    roi_data: Optional[dict] = None
    perdidas: List[dict] = field(default_factory=list)   # PerdidaDolor.to_dict()
    perdida_total_mes: Optional[float] = None
    paquetes: List[dict] = field(default_factory=list)   # PaqueteCotizado.to_dict()

    # Assets de venta generados
    propuesta_texto: Optional[str] = None
    demo_prompt: Optional[str] = None
    landing_prompt: Optional[str] = None
    presentacion_prompt: Optional[str] = None
    secuencia_seguimiento: List[dict] = field(default_factory=list)  # toques de follow-up

    # CRM
    estado: str = "nuevo"
    notas: str = ""
    fecha_contacto: Optional[str] = None
