"""
Plantillas de briefing web por sector.

Cada sector define las secciones, funcionalidades, estética e integraciones
recomendadas para su tipo de negocio. El Web Developer las usa como base para
generar una web a medida — no es lo mismo un restaurante que una clínica estética.
"""

# Estilos visuales disponibles (transversales a todos los sectores)
ESTILOS_VISUALES = {
    "Elegante y minimalista": "Diseño limpio, mucho espacio en blanco, tipografía serif refinada, paleta sobria. Sensación premium y sofisticada.",
    "Moderno y futurista (dark/neón)": "Fondo oscuro, acentos neón (violeta/cian), microanimaciones, gradientes. Tecnológico y vanguardista — estilo MerakIA.",
    "Cálido y acogedor": "Tonos tierra, fotografía cercana, tipografía amable, formas redondeadas. Transmite confianza y proximidad.",
    "Fresco y vibrante": "Colores saturados, dinamismo, ilustraciones, energía. Ideal para públicos jóvenes y activos.",
    "Clásico y profesional": "Estructura tradicional, azules corporativos, serif sobria, sensación de solidez y experiencia.",
    "Lujo y exclusividad": "Negro y dorado, tipografía display, fotografía editorial, lujo discreto. Para servicios premium.",
}

# Plantillas por sector
SECTORES = {
    "🍽️ Restaurante / Bar": {
        "estilo_sugerido": "Cálido y acogedor",
        "paleta": "Tonos tierra cálidos, terracota, verde oliva, crema",
        "secciones": [
            "Hero con fotografía apetitosa del plato estrella",
            "Carta / Menú digital con categorías y precios",
            "Galería de platos y ambiente",
            "Sistema de reservas online (fecha, hora, comensales)",
            "Horarios y ubicación con mapa",
            "Sobre nosotros / historia del restaurante",
            "Opiniones de clientes (Google Reviews)",
            "Eventos privados y celebraciones",
        ],
        "funcionalidades": [
            "Calendario de reservas en tiempo real",
            "Carta filtrable (alérgenos, vegano, sin gluten)",
            "Botón de pedido a domicilio / WhatsApp",
            "Integración con Google Maps",
            "Galería con lightbox",
        ],
        "integraciones": "WhatsApp Business para reservas, Google Maps, TheFork/Cover Manager, Instagram feed",
        "tono": "Apetitoso, cercano, que despierte el deseo de visitar el local",
    },
    "💆 Estética / Belleza": {
        "estilo_sugerido": "Elegante y minimalista",
        "paleta": "Rosas empolvados, nude, dorado suave, blanco roto",
        "secciones": [
            "Hero elegante con sensación de bienestar",
            "Tratamientos y servicios con descripción y precios",
            "Sistema de reserva de citas online",
            "Galería antes/después (con consentimiento)",
            "Bonos y packs de tratamientos",
            "Equipo de profesionales",
            "Testimonios de clientas",
            "Blog de consejos de belleza",
        ],
        "funcionalidades": [
            "Calendario de reservas con selección de tratamiento y profesional",
            "Catálogo de tratamientos con filtros por zona/objetivo",
            "Dashboard de bonos del cliente",
            "Galería antes/después con slider comparativo",
            "Formulario de primera consulta gratuita",
        ],
        "integraciones": "Sistema de citas (Booksy/Treatwell), WhatsApp Business, Instagram, pasarela de pago para bonos",
        "tono": "Sofisticado, aspiracional, transmitir cuidado personal y resultados",
    },
    "💪 Gimnasio / Fitness": {
        "estilo_sugerido": "Fresco y vibrante",
        "paleta": "Negro, energético (lima/naranja/eléctrico), grises técnicos",
        "secciones": [
            "Hero potente con vídeo o imagen de acción",
            "Horario de clases dirigidas (timetable)",
            "Tarifas y planes de suscripción",
            "Sistema de reserva de clases y aforo",
            "Entrenadores y especialidades",
            "Instalaciones y galería",
            "Transformaciones / resultados de socios",
            "Prueba gratuita / primer día gratis",
        ],
        "funcionalidades": [
            "Calendario de clases con reserva de plaza y aforo en tiempo real",
            "Comparador de planes de suscripción",
            "Dashboard del socio (clases reservadas, progreso)",
            "Formulario de prueba gratuita",
            "Contador de transformaciones / motivacional",
        ],
        "integraciones": "Software de gestión (Trainingym/Mindbody), pasarela de pago de cuotas, WhatsApp, app de reservas",
        "tono": "Motivador, enérgico, orientado a objetivos y comunidad",
    },
    "🦷 Clínica Dental": {
        "estilo_sugerido": "Clásico y profesional",
        "paleta": "Azules y verdes clínicos, blanco, acentos turquesa",
        "secciones": [
            "Hero que transmita confianza y profesionalidad",
            "Tratamientos (implantes, ortodoncia, estética dental...)",
            "Sistema de cita previa online",
            "Financiación y facilidades de pago",
            "Equipo médico con credenciales",
            "Tecnología y casos de éxito",
            "Primera visita gratuita / revisión",
            "Opiniones de pacientes verificadas",
        ],
        "funcionalidades": [
            "Calendario de cita previa con selección de tratamiento",
            "Calculadora de financiación de tratamientos",
            "Galería de casos antes/después",
            "Chat / WhatsApp para urgencias",
            "Formulario de primera consulta gratuita",
        ],
        "integraciones": "Software de gestión clínica (Gesden/Cliniko), WhatsApp Business, Google Reviews, agente de voz para citas",
        "tono": "Profesional, tranquilizador, que reduzca el miedo al dentista y genere confianza",
    },
    "✂️ Peluquería / Barbería": {
        "estilo_sugerido": "Moderno y futurista (dark/neón)",
        "paleta": "Negro, dorado o cobre, blanco, acentos vibrantes",
        "secciones": [
            "Hero con estilo y personalidad de marca",
            "Servicios y tarifas (corte, color, tratamientos)",
            "Reserva de cita online con profesional",
            "Galería de trabajos / looks",
            "Equipo de estilistas",
            "Productos a la venta",
            "Opiniones de clientes",
        ],
        "funcionalidades": [
            "Calendario de reservas con elección de estilista y servicio",
            "Galería tipo Instagram de trabajos",
            "Catálogo de servicios con duración y precio",
            "Recordatorios de cita automáticos",
        ],
        "integraciones": "Booksy/Treatwell, Instagram feed, WhatsApp, recordatorios automáticos",
        "tono": "Con estilo, moderno, que refleje la personalidad del salón",
    },
    "🩺 Fisioterapia / Salud": {
        "estilo_sugerido": "Cálido y acogedor",
        "paleta": "Verdes y azules suaves, blanco, tonos naturales",
        "secciones": [
            "Hero que transmita bienestar y recuperación",
            "Tratamientos y especialidades",
            "Sistema de cita previa online",
            "Equipo de fisioterapeutas",
            "Patologías que tratamos",
            "Primera valoración",
            "Testimonios de pacientes",
        ],
        "funcionalidades": [
            "Calendario de cita previa por especialidad",
            "Formulario de valoración inicial",
            "Buscador de tratamiento por dolencia",
            "WhatsApp para consultas rápidas",
        ],
        "integraciones": "Software de gestión, WhatsApp Business, Google Reviews, agente de voz",
        "tono": "Cercano, profesional, empático con el dolor del paciente",
    },
    "🏨 Hotel / Turismo": {
        "estilo_sugerido": "Lujo y exclusividad",
        "paleta": "Tonos elegantes según ubicación, dorado, neutros premium",
        "secciones": [
            "Hero inmersivo con vídeo del establecimiento",
            "Habitaciones y suites con galería",
            "Motor de reservas (check-in/out, huéspedes)",
            "Experiencias y servicios (spa, restaurante)",
            "Galería del entorno",
            "Ofertas y paquetes",
            "Ubicación y cómo llegar",
        ],
        "funcionalidades": [
            "Motor de reservas con disponibilidad y precios",
            "Galería inmersiva de habitaciones",
            "Comparador de tipos de habitación",
            "Mapa de experiencias del entorno",
        ],
        "integraciones": "Motor de reservas (Booking/Channel Manager), pasarela de pago, Google Maps",
        "tono": "Evocador, aspiracional, vender la experiencia más que el alojamiento",
    },
    "🛍️ Tienda / Comercio local": {
        "estilo_sugerido": "Fresco y vibrante",
        "paleta": "Según identidad de marca, colores de catálogo",
        "secciones": [
            "Hero con producto destacado o novedades",
            "Catálogo de productos por categorías",
            "Producto destacado / más vendido",
            "Sobre la tienda / historia",
            "Ubicación física y horarios",
            "Contacto y redes sociales",
        ],
        "funcionalidades": [
            "Catálogo de productos con filtros",
            "Ficha de producto con galería",
            "Botón de compra/reserva por WhatsApp",
            "Integración con Instagram Shopping",
        ],
        "integraciones": "WhatsApp Business, Instagram Shopping, Google Maps, pasarela de pago si hay e-commerce",
        "tono": "Acorde a la marca, cercano al cliente local",
    },
    "⚖️ Despacho / Consultoría": {
        "estilo_sugerido": "Clásico y profesional",
        "paleta": "Azul marino, gris, blanco, acento dorado o burdeos",
        "secciones": [
            "Hero que transmita autoridad y confianza",
            "Áreas de práctica / servicios",
            "Equipo de profesionales con credenciales",
            "Casos de éxito / resultados",
            "Solicitud de consulta",
            "Artículos / blog de autoridad",
            "Testimonios de clientes",
        ],
        "funcionalidades": [
            "Formulario de solicitud de consulta",
            "Calendario para agendar reunión",
            "Buscador de servicios por área",
            "Chat / WhatsApp profesional",
        ],
        "integraciones": "Calendario de citas (Calendly), WhatsApp Business, CRM, formularios avanzados",
        "tono": "Autoritativo, riguroso, transmitir experiencia y resultados",
    },
    "✨ Otro / Personalizado": {
        "estilo_sugerido": "Moderno y futurista (dark/neón)",
        "paleta": "A definir según la marca",
        "secciones": [
            "Hero con propuesta de valor clara",
            "Servicios / productos principales",
            "Sobre nosotros",
            "Llamada a la acción principal",
            "Contacto",
        ],
        "funcionalidades": [
            "Formulario de contacto",
            "Integración con WhatsApp",
        ],
        "integraciones": "WhatsApp Business, Google Maps, redes sociales",
        "tono": "A definir según el negocio",
    },
}


def construir_brief(
    sector_key: str,
    nombre_negocio: str,
    ciudad: str,
    estilo: str,
    secciones_elegidas: list,
    funcionalidades_elegidas: list,
    detalles_extra: str,
    paleta_custom: str = "",
) -> str:
    """Construye el prompt completo para el Web Developer a partir de las elecciones del usuario."""
    sector = SECTORES.get(sector_key, SECTORES["✨ Otro / Personalizado"])
    estilo_desc = ESTILOS_VISUALES.get(estilo, "")
    paleta = paleta_custom.strip() or sector["paleta"]

    secciones_txt = "\n".join(f"   - {s}" for s in secciones_elegidas) if secciones_elegidas else "   - (a criterio del desarrollador)"
    func_txt = "\n".join(f"   - {f}" for f in funcionalidades_elegidas) if funcionalidades_elegidas else "   - (a criterio del desarrollador)"

    return f"""Crea una página web completa, profesional y orientada a conversión para el siguiente negocio:

**NEGOCIO:** {nombre_negocio or '(nombre genérico del sector)'}
**SECTOR:** {sector_key}
**UBICACIÓN:** {ciudad or 'España'}

**ESTILO VISUAL:** {estilo}
{estilo_desc}

**PALETA DE COLORES:** {paleta}

**TONO DE LA WEB:** {sector['tono']}

**SECCIONES QUE DEBE INCLUIR:**
{secciones_txt}

**FUNCIONALIDADES CLAVE:**
{func_txt}

**INTEGRACIONES SUGERIDAS:** {sector['integraciones']}

**DETALLES ADICIONALES DEL CLIENTE:**
{detalles_extra.strip() or '(ninguno)'}

REQUISITOS TÉCNICOS:
- Entrega un único archivo HTML completo y autocontenido (HTML + CSS + JS inline), listo para abrir en el navegador.
- Diseño totalmente responsive (mobile-first).
- Usa datos de ejemplo realistas y coherentes con el sector (servicios, precios, textos).
- Animaciones sutiles y microinteracciones que aporten sensación premium.
- Las funcionalidades interactivas (calendario de reservas, catálogo filtrable, dashboard) deben ser funcionales con JS, aunque usen datos de demostración.
- Optimizado para conversión: CTAs claros y visibles, formularios accesibles.
- SEO básico (meta tags, estructura semántica, alt en imágenes).
- Usa placeholders de imágenes (https://placehold.co) con descripciones apropiadas."""
