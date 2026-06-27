"""
Generador del Catálogo de Servicios MerakIA 2026 — versión actualizada.
Añade servicios 11 (Agente de Voz) y 12 (Recordatorios & Fidelización).
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame
import datetime

# ── Colores marca ──────────────────────────────────────────────────────────────
PURPLE      = colors.HexColor("#6B2D8B")
PURPLE_LIGHT= colors.HexColor("#9B59B6")
PURPLE_BG   = colors.HexColor("#F3E8FF")
DARK_TEXT   = colors.HexColor("#1A1A2E")
GRAY_LINE   = colors.HexColor("#CCCCCC")
WHITE       = colors.white
TABLE_HEADER= colors.HexColor("#4A1A6E")

W, H = A4

# ── Estilos ────────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

def s(name, **kw):
    base = styles["Normal"]
    return ParagraphStyle(name, parent=base, **kw)

ST = {
    "header":    s("header",    fontName="Helvetica-Bold", fontSize=22,
                   textColor=PURPLE, alignment=TA_CENTER, spaceAfter=4),
    "subheader": s("subheader", fontName="Helvetica-Bold", fontSize=14,
                   textColor=PURPLE, alignment=TA_CENTER, spaceAfter=6),
    "body":      s("body",      fontName="Helvetica", fontSize=9.5,
                   textColor=DARK_TEXT, leading=14, alignment=TA_JUSTIFY,
                   spaceAfter=6),
    "section":   s("section",   fontName="Helvetica-Bold", fontSize=11,
                   textColor=PURPLE, spaceBefore=10, spaceAfter=4),
    "service":   s("service",   fontName="Helvetica-Bold", fontSize=13,
                   textColor=PURPLE, spaceBefore=2, spaceAfter=6),
    "bullet":    s("bullet",    fontName="Helvetica", fontSize=9.5,
                   textColor=DARK_TEXT, leading=13, leftIndent=12,
                   firstLineIndent=-12, spaceAfter=2),
    "italic_box":s("italic_box",fontName="Helvetica-Oblique", fontSize=10,
                   textColor=PURPLE, alignment=TA_CENTER, leading=15),
    "footer":    s("footer",    fontName="Helvetica", fontSize=8,
                   textColor=colors.HexColor("#888888"), alignment=TA_CENTER),
    "index":     s("index",     fontName="Helvetica", fontSize=10,
                   textColor=DARK_TEXT, leading=16, spaceAfter=2),
    "conf":      s("conf",      fontName="Helvetica", fontSize=8,
                   textColor=colors.HexColor("#888888")),
}

# ── Helpers ────────────────────────────────────────────────────────────────────
def hr():
    return HRFlowable(width="100%", thickness=1.5, color=PURPLE,
                      spaceAfter=8, spaceBefore=4)

def hr_thin():
    return HRFlowable(width="100%", thickness=0.5, color=GRAY_LINE,
                      spaceAfter=6, spaceBefore=2)

def bullet(text):
    return Paragraph(f"• {text}", ST["bullet"])

def box(text):
    data = [[Paragraph(text, ST["italic_box"])]]
    t = Table(data, colWidths=[15*cm])
    t.setStyle(TableStyle([
        ("BOX",        (0,0), (-1,-1), 1, PURPLE_LIGHT),
        ("BACKGROUND", (0,0), (-1,-1), PURPLE_BG),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING",   (0,0), (-1,-1), 14),
        ("RIGHTPADDING",  (0,0), (-1,-1), 14),
    ]))
    return t

def page_header_footer(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(colors.HexColor("#888888"))
    canvas_obj.drawString(2*cm, H - 1.3*cm, "MerakIA • Catálogo de Servicios 2026")
    canvas_obj.drawRightString(W - 2*cm, H - 1.3*cm, "CONFIDENCIAL")
    canvas_obj.setStrokeColor(GRAY_LINE)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(2*cm, H - 1.5*cm, W - 2*cm, H - 1.5*cm)
    page_num = canvas_obj.getPageNumber()
    canvas_obj.drawCentredString(W/2, 1*cm, f"— {page_num} —")
    canvas_obj.restoreState()

# ── Servicio helper ────────────────────────────────────────────────────────────
def servicio(num, titulo, descripcion, proposito, dolores,
             proceso, herramientas, dif_cliente, dif_merakia,
             roi, entregables, verticales, cierre=None):
    items = []
    items.append(PageBreak())
    items.append(Paragraph(f"▶ {num}. {titulo}", ST["service"]))
    items.append(hr())

    for sec, content in [
        ("Descripción del Servicio", descripcion),
        ("Propósito y Beneficios para el Cliente", proposito),
    ]:
        items.append(Paragraph(sec, ST["section"]))
        items.append(Paragraph(content, ST["body"]))

    items.append(Paragraph("Dolor que Resuelve", ST["section"]))
    for d in dolores:
        items.append(bullet(d))

    items.append(Paragraph("Proceso de Implementación (Paso a Paso)", ST["section"]))
    for i, p in enumerate(proceso, 1):
        items.append(Paragraph(f"{i}. {p}", ST["bullet"]))

    items.append(Paragraph("Herramientas y Tecnología", ST["section"]))
    items.append(Paragraph(herramientas, ST["body"]))

    items.append(Paragraph("Nivel de Dificultad", ST["section"]))
    items.append(bullet(f"Para el cliente: {dif_cliente}"))
    items.append(bullet(f"Para MerakIA: {dif_merakia}"))

    items.append(Paragraph("Nivel de Beneficio / ROI Esperado", ST["section"]))
    items.append(Paragraph(roi, ST["body"]))

    if entregables:
        items.append(Paragraph("Entregables", ST["section"]))
        for e in entregables:
            items.append(bullet(e))

    if verticales:
        items.append(Paragraph("Verticales con Mayor Impacto", ST["section"]))
        items.append(Paragraph(verticales, ST["body"]))

    if cierre:
        items.append(Spacer(1, 8))
        items.append(box(cierre))

    return items

# ── Contenido ──────────────────────────────────────────────────────────────────
def build_story():
    story = []

    # ── PORTADA ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 4*cm))
    story.append(Paragraph("MERAKIA", ST["header"]))
    story.append(Paragraph("Catálogo Completo de Servicios 2026", ST["subheader"]))
    story.append(Spacer(1, 0.5*cm))
    story.append(hr())
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        "Inteligencia Artificial con Alma para<br/>"
        "Pymes • Restaurantes • Clínicas Dentales • Gimnasios • Farmacias",
        ST["subheader"]
    ))
    story.append(Spacer(1, 2*cm))
    story.append(box(
        "12 servicios de IA listos para implementar en tu negocio local.\n"
        "Desde el diagnóstico hasta la fidelización automática."
    ))
    story.append(PageBreak())

    # ── INTRO ──────────────────────────────────────────────────────────────────
    story.append(Paragraph("MERAKIA", ST["header"]))
    story.append(Paragraph("Catálogo Completo de Servicios 2026", ST["subheader"]))
    story.append(hr())
    story.append(Paragraph(
        "MerakIA es la agencia de inteligencia artificial con alma diseñada específicamente para pymes "
        "españolas. Nuestra misión es democratizar el acceso a capacidades de IA de nivel agencia, "
        "permitiendo que restaurantes, clínicas dentales, gimnasios, farmacias y otros negocios locales "
        "compitan con herramientas que antes solo estaban al alcance de grandes empresas con "
        "presupuestos elevados.",
        ST["body"]
    ))
    story.append(Paragraph(
        "Este documento detalla de forma exhaustiva y transparente todos los servicios que ofrecemos. "
        "Para cada servicio encontrarás:",
        ST["body"]
    ))
    for item in [
        "Descripción clara y concreta de lo que entregamos",
        "Propósito y beneficios reales para el cliente",
        "Dolores específicos que resolvemos",
        "Proceso de implementación paso a paso",
        "Herramientas y tecnología que utilizamos",
        "Nivel de dificultad (para el cliente y para MerakIA)",
        "Nivel de beneficio / ROI esperado",
        "Entregables concretos",
        "Recomendaciones de verticales donde más impacto genera",
    ]:
        story.append(bullet(item))
    story.append(Spacer(1, 0.5*cm))
    story.append(box(
        "Todos nuestros servicios combinan la potencia de agentes IA especializados con "
        "supervisión humana experta cuando es necesario. El resultado es tecnología de "
        "alto rendimiento con el toque humano y la atención al detalle que las pymes merecen."
    ))
    story.append(PageBreak())

    # ── ÍNDICE ─────────────────────────────────────────────────────────────────
    story.append(Paragraph("ÍNDICE DE SERVICIOS", ST["service"]))
    story.append(hr())
    indice = [
        "Meraki Soul Audit – Diagnóstico y Roadmap Personalizado",
        "Content Engine & Estrategia de Contenidos",
        "Desarrollo de Webs y Landing Pages con IA",
        "Chatbots Personalizados e Integrados",
        "Project Manager IA – Orquestación de Proyectos",
        "MerakChat – Asistente Conversacional con Memoria",
        "Automatización de Procesos Internos (Autónomo)",
        "Meraki Vertical Packs – Implementación por Sector",
        "Meraki Academy – Formación y Capacitación",
        "Meraki Hybrid Team – Retainer con Soporte Humano",
        "Agente de Voz IA – Recepción Telefónica 24/7 ★ NUEVO",
        "Recordatorios & Fidelización – Anti-No-Show Automatizado ★ NUEVO",
    ]
    for i, item in enumerate(indice, 1):
        color = PURPLE if i >= 11 else DARK_TEXT
        story.append(Paragraph(
            f"<font color='#{color.hexval()[2:]}'>{i}. {item}</font>",
            ST["index"]
        ))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        "Al final del documento encontrarás una tabla comparativa de todos los servicios y "
        "recomendaciones de paquetes según tamaño y sector del cliente.",
        ST["body"]
    ))

    # ── SERVICIOS 1-10 ─────────────────────────────────────────────────────────
    story += servicio(
        1, "Meraki Soul Audit – Diagnóstico y Roadmap Personalizado",
        "Análisis integral y profundo del negocio del cliente utilizando inteligencia artificial avanzada. "
        "Evaluamos su presencia digital actual (web, Google Business Profile, reseñas, redes sociales), "
        "analizamos competidores locales, identificamos oportunidades de mejora y generamos un informe "
        "detallado con un \"Meraki Score\" (0-100) y un roadmap accionable de 90 días priorizado por "
        "impacto y esfuerzo.",
        "El cliente recibe una radiografía objetiva y profesional de su situación digital actual, junto con "
        "un plan claro y priorizado que le permite dejar de \"hacer cosas\" de forma aleatoria y empezar a "
        "ejecutar acciones con alto retorno. Elimina la parálisis por análisis y la sensación de estar "
        "invirtiendo tiempo y dinero sin saber si va por el buen camino.",
        [
            "Incertidumbre sobre qué está funcionando y qué no en su marketing digital.",
            "Pérdida de tiempo y dinero en acciones que no generan resultados medibles.",
            "Sensación de estar \"dejando dinero sobre la mesa\" sin saber exactamente dónde.",
            "Falta de visión estratégica clara y priorizada.",
        ],
        [
            "Recopilación de accesos y datos (web, Google Business, redes, software interno).",
            "Análisis automatizado con agentes IA especializados en cada área.",
            "Revisión humana experta para contextualizar y enriquecer el análisis.",
            "Generación del informe Meraki Score + Roadmap de 90 días.",
            "Sesión de presentación y explicación de 60-90 minutos con el cliente.",
            "Entrega del documento editable + plan de acción priorizado.",
        ],
        "Agentes IA de análisis de web y competidores, herramientas de scraping ético y análisis de "
        "reseñas, modelos de lenguaje avanzados para síntesis estratégica, dashboards visuales generados "
        "automáticamente.",
        "Bajo (solo tiene que proporcionar accesos y asistir a una reunión).",
        "Medio-Alto (requiere análisis profundo + supervisión humana de calidad).",
        "Alto. La mayoría de clientes identifican entre 3 y 7 acciones de alto impacto que estaban "
        "ignorando o haciendo mal. Muchos recuperan la inversión del audit en las primeras 4-6 semanas.",
        [
            "Informe PDF profesional de 15-25 páginas con Meraki Score visual.",
            "Roadmap de 90 días con acciones priorizadas (Impacto vs Esfuerzo).",
            "Grabación de la sesión de presentación.",
            "Acceso a versión editable del roadmap para seguimiento.",
        ],
        "Clínicas dentales y de estética, restaurantes independientes, gimnasios medianos y farmacias con "
        "varios puntos de venta.",
        "El Soul Audit es el servicio ideal de entrada. Permite al cliente ver el valor de MerakIA de "
        "forma tangible antes de contratar servicios continuos.",
    )

    story += servicio(
        2, "Content Engine & Estrategia de Contenidos",
        "Sistema completo de generación, planificación y optimización de contenido para redes sociales, "
        "Google Business Profile, email marketing y web. Incluye calendario editorial mensual o semanal, "
        "creación de posts, copy, carruseles, ideas de Reels, emails y contenido para web, todo adaptado "
        "al tono de voz del negocio y a los objetivos específicos de cada vertical.",
        "El cliente deja de sufrir por \"¿qué publico hoy?\" y pasa a tener un flujo constante de "
        "contenido profesional, coherente y alineado con sus objetivos de negocio (más reservas, más "
        "pacientes, más socios, más ventas). Aumenta la visibilidad, mejora el engagement y genera leads "
        "de forma más consistente.",
        [
            "Bloqueo creativo y estrés por generar contenido constantemente.",
            "Inconsistencia en la publicación (semanas sin publicar seguidas de rachas).",
            "Contenido genérico que no convierte ni refleja la personalidad del negocio.",
            "Pérdida de oportunidades de engagement y posicionamiento local.",
        ],
        [
            "Sesión de onboarding (45-60 min) para definir tono de voz, objetivos y buyer persona.",
            "Configuración del Content Engine con las cuentas del cliente.",
            "Generación del primer calendario editorial (30 días).",
            "Revisión y ajuste conjunto del primer mes.",
            "Entrega continua de contenido (semanal o quincenal según plan).",
            "Informe mensual de rendimiento + recomendaciones de mejora.",
        ],
        "Agentes especializados en copywriting y estrategia de contenidos, modelos de lenguaje fine-tuned "
        "por vertical, herramientas de programación de posts, análisis de rendimiento de contenido previo "
        "del cliente.",
        "Bajo-Medio (revisa y aprueba, pero no tiene que crear desde cero).",
        "Medio (requiere buen entendimiento del negocio y ajustes continuos).",
        "Muy Alto. Los clientes suelen ver incremento en alcance orgánico del 40-120% en los primeros "
        "3 meses, además de ahorro significativo de tiempo del propietario o equipo.",
        [
            "Calendario editorial mensual en Google Sheets o Notion.",
            "Pack de contenido listo para publicar (textos + sugerencias visuales).",
            "Informe mensual de rendimiento con insights accionables.",
        ],
        "Todos los verticales. Especialmente potente en clínicas dentales (contenido educativo + "
        "antes/después), restaurantes (menús, promociones, behind the scenes) y gimnasios "
        "(motivación + resultados de socios).",
    )

    story += servicio(
        3, "Desarrollo de Webs y Landing Pages con IA",
        "Creación y optimización de páginas web y landing pages profesionales, rápidas y optimizadas "
        "para conversión, generadas y ajustadas con inteligencia artificial. Incluye diseño responsive, "
        "SEO on-page básico, integración de formularios, chatbots y analítica. Ideal para captar leads, "
        "presentar servicios o promocionar ofertas específicas.",
        "El cliente obtiene una presencia web profesional y moderna sin los costes y tiempos "
        "tradicionales de desarrollo. Las landing pages están diseñadas específicamente para convertir "
        "(más reservas, más citas, más contactos). Además, son fáciles de mantener y actualizar.",
        [
            "Webs anticuadas, lentas o que no generan confianza.",
            "Coste elevado y plazos largos de agencias tradicionales de diseño web.",
            "Dificultad para crear páginas específicas para campañas o promociones concretas.",
            "Falta de optimización para móviles y conversión.",
        ],
        [
            "Brief de objetivos, público objetivo y mensajes clave.",
            "Generación de estructura y diseño con IA.",
            "Revisión y ajustes de copy y diseño con el cliente.",
            "Desarrollo técnico y optimización (velocidad, SEO, responsive).",
            "Integración de formularios, chatbot y herramientas de tracking.",
            "Puesta en marcha + formación básica de gestión al cliente.",
        ],
        "Agente Web Developer especializado, frameworks modernos (HTML5, Tailwind, React ligero cuando "
        "es necesario), herramientas de optimización de velocidad, integraciones con WhatsApp Business, "
        "Google Analytics y CRM del cliente.",
        "Bajo (revisa y aprueba; la gestión posterior es sencilla).",
        "Medio-Alto (requiere calidad técnica y atención al detalle de conversión).",
        "Alto. Una buena landing page bien optimizada puede multiplicar por 2-5x la conversión de "
        "campañas de pago o tráfico orgánico.",
        [
            "Web o landing page fully responsive y optimizada.",
            "Código limpio y documentado (si el cliente lo desea).",
            "Integraciones configuradas (formularios, chatbot, analítica).",
            "Manual de uso sencillo para actualizaciones básicas.",
        ],
        None,
    )

    story += servicio(
        4, "Chatbots Personalizados e Integrados",
        "Diseño, desarrollo e implementación de chatbots inteligentes personalizados para web, WhatsApp "
        "Business e Instagram. Los chatbots están entrenados con la información específica del negocio "
        "(servicios, precios, horarios, FAQ, políticas de cancelación, etc.) y pueden calificar leads, "
        "reservar citas, responder dudas frecuentes y derivar a humanos cuando es necesario. Incluye "
        "integración con el CRM o sistema de gestión del cliente.",
        "El cliente puede atender y cualificar leads 24/7 sin aumentar su equipo. Reduce el tiempo de "
        "respuesta, mejora la experiencia del cliente potencial y libera al equipo humano para tareas de "
        "mayor valor. En muchos casos, el chatbot cierra o agenda directamente una parte significativa "
        "de las consultas.",
        [
            "Pérdida de leads por no responder rápido (especialmente fuera de horario).",
            "Sobrecarga del equipo con consultas repetitivas y de bajo valor.",
            "Inconsistencia en la información que se da a los clientes potenciales.",
            "Dificultad para escalar la atención sin aumentar costes de personal.",
        ],
        [
            "Recopilación de toda la información del negocio (servicios, precios, FAQ, políticas).",
            "Diseño del flujo conversacional y árboles de decisión.",
            "Entrenamiento y configuración del chatbot con datos del cliente.",
            "Integración en web / WhatsApp / Instagram según necesidades.",
            "Pruebas exhaustivas y ajustes.",
            "Puesta en marcha + monitorización inicial y optimización continua.",
        ],
        "Agente Chatbot Specialist, plataformas de chatbot avanzadas con NLP, integraciones con "
        "WhatsApp Business API, CRMs populares (Cliniko, Holded, Odoo, etc.), sistemas de reserva online.",
        "Bajo-Medio (proporciona información; el mantenimiento es mínimo).",
        "Medio-Alto (requiere buen diseño de flujos y entrenamiento preciso).",
        "Muy Alto. Un buen chatbot puede atender entre el 60-80% de las consultas iniciales de forma "
        "autónoma, mejorando drásticamente la tasa de respuesta y liberando decenas de horas al mes.",
        [
            "Chatbot fully functional en los canales elegidos.",
            "Documentación de flujos y base de conocimiento.",
            "Dashboard de monitorización y estadísticas de uso.",
            "Plan de optimización continua (recomendado retainer).",
        ],
        None,
    )

    story += servicio(
        5, "Project Manager IA – Orquestación de Proyectos",
        "Servicio de orquestación completa de proyectos de marketing y comunicación para el cliente. "
        "Un Project Manager IA (con supervisión humana cuando es necesario) coordina todos los agentes "
        "involucrados (contenido, web, chatbot, nurturing, etc.), establece plazos, hace seguimiento, "
        "resuelve bloqueos y entrega el proyecto completo al cliente de forma ordenada y profesional.",
        "El cliente recibe proyectos completos (lanzamiento de servicio, campaña de temporada, "
        "rebranding digital, etc.) sin tener que coordinar a múltiples personas o agencias. Todo está "
        "gestionado de forma centralizada, con comunicación clara y entregas en plazo.",
        [
            "Caos y falta de coordinación cuando se contratan varios proveedores.",
            "Proyectos que se alargan o se quedan a medias por falta de seguimiento.",
            "Sobrecarga del propio cliente teniendo que hacer de \"director de orquesta\".",
            "Pérdida de tiempo en reuniones de seguimiento y correos.",
        ],
        [
            "Definición clara del alcance, objetivos y entregables del proyecto.",
            "Desglose en tareas y asignación a los agentes correspondientes.",
            "Planificación temporal realista con hitos intermedios.",
            "Ejecución coordinada con seguimiento diario/semanal.",
            "Revisión de calidad humana en puntos clave.",
            "Entrega final ordenada + documentación y formación si procede.",
        ],
        "Agente Project Manager, herramientas de gestión de proyectos (Notion, Linear, etc.), "
        "integración con los demás agentes de MerakIA, sistemas de comunicación con el cliente.",
        "Bajo (participa en definición y revisiones clave).",
        "Medio-Alto (requiere buena coordinación y gestión de expectativas).",
        "Alto. El cliente ahorra decenas de horas de coordinación y reduce significativamente el riesgo "
        "de que los proyectos se desvíen o se retrasen.",
        None, None,
    )

    story += servicio(
        6, "MerakChat – Asistente Conversacional con Memoria",
        "Asistente conversacional inteligente con memoria de sesión y contexto del negocio. Puede "
        "funcionar como soporte al cliente final (en web o WhatsApp), como asistente interno para el "
        "equipo del cliente (consultas sobre políticas, procedimientos, información de servicios) o como "
        "herramienta de ventas interna. Mantiene contexto a lo largo de la conversación y aprende de "
        "interacciones previas cuando está configurado para ello.",
        "Ofrece atención inmediata y de calidad 24/7, reduce la carga del equipo humano en consultas "
        "repetitivas y mejora la experiencia tanto de clientes como de empleados. Es especialmente útil "
        "en negocios con alto volumen de consultas similares o con equipos pequeños.",
        [
            "Tiempo del equipo perdido en responder las mismas preguntas una y otra vez.",
            "Clientes que se van por no recibir respuesta rápida.",
            "Inconsistencia en la información que recibe el cliente según quién le atienda.",
            "Dificultad para escalar la atención sin aumentar personal.",
        ],
        [
            "Definición del rol y alcance del asistente (soporte cliente / interno / ventas).",
            "Carga de información base del negocio (documentos, FAQ, políticas).",
            "Configuración de memoria y contexto.",
            "Integración en los canales deseados.",
            "Pruebas y refinamiento.",
            "Monitorización y ajustes continuos (especialmente en las primeras semanas).",
        ],
        "Agente Chat con memoria avanzada, modelos de lenguaje con capacidad de retención de contexto, "
        "integraciones con WhatsApp, web y herramientas internas del cliente.",
        "Bajo (uso diario es muy intuitivo).",
        "Medio (el entrenamiento inicial y los ajustes son clave).",
        "Alto. Reduce significativamente el tiempo dedicado a consultas repetitivas y mejora la "
        "satisfacción del cliente al recibir respuestas instantáneas y precisas en cualquier momento.",
        None, None,
    )

    story += servicio(
        7, "Automatización de Procesos Internos (Autónomo)",
        "Implementación de automatizaciones inteligentes para tareas repetitivas y procesos internos del "
        "negocio. El agente Autónomo puede manejar cálculos, gestión de archivos, actualizaciones de "
        "datos, recordatorios, integraciones entre herramientas, preparación de informes periódicos y "
        "otras tareas que consumen tiempo del equipo pero no requieren creatividad humana.",
        "Libera al equipo de tareas mecánicas y de bajo valor para que puedan centrarse en lo que "
        "realmente importa: atención al cliente, creatividad, estrategia y crecimiento del negocio. "
        "Reduce errores humanos y aumenta la consistencia y velocidad de los procesos internos.",
        [
            "Tiempo excesivo dedicado a tareas repetitivas y administrativas.",
            "Errores humanos en procesos manuales (cálculos, copias de datos, envíos).",
            "Dependencia de una sola persona que \"sabe cómo se hacen las cosas\".",
            "Dificultad para escalar operaciones sin aumentar proporcionalmente el equipo.",
        ],
        [
            "Identificación de procesos repetitivos y de alto volumen de tiempo.",
            "Análisis y documentación del proceso actual.",
            "Diseño de la automatización con el agente Autónomo.",
            "Desarrollo y pruebas.",
            "Puesta en marcha gradual con supervisión inicial.",
            "Documentación y formación al equipo del cliente.",
        ],
        "Agente Autónomo con capacidad de usar herramientas (calculadora, manejo de archivos, APIs, "
        "integraciones con Google Workspace, Excel, CRM, etc.).",
        "Bajo-Medio (depende de la complejidad del proceso).",
        "Medio-Alto (requiere buen análisis de procesos).",
        "Muy Alto en procesos de alto volumen. Muchos clientes recuperan la inversión en pocas semanas "
        "al liberar decenas de horas al mes del equipo.",
        None, None,
    )

    story += servicio(
        8, "Meraki Vertical Packs – Implementación por Sector",
        "Paquetes pre-configurados y optimizados específicamente para cada vertical (Restaurantes, "
        "Clínicas Dentales, Gimnasios, Farmacias, Clínicas de Estética, etc.). Incluyen prompts, flujos, "
        "integraciones y dashboards adaptados a las necesidades y lenguaje específico de cada sector, "
        "acelerando la puesta en marcha y maximizando el impacto desde el primer día.",
        "El cliente no empieza desde cero. Recibe una solución ya afinada para su tipo de negocio, con "
        "casos de uso probados, lenguaje adecuado y las integraciones más habituales en su sector. "
        "Reduce drásticamente el tiempo hasta obtener resultados y aumenta la relevancia de todo lo que "
        "se genera.",
        [
            "Soluciones genéricas que no entienden las particularidades del sector.",
            "Tiempo perdido en configurar y adaptar herramientas generales.",
            "Resultados mediocres por falta de conocimiento sectorial en la IA.",
            "Sensación de que \"esto no está hecho para mi tipo de negocio\".",
        ],
        [
            "Elección del Vertical Pack adecuado.",
            "Onboarding acelerado con configuración predefinida.",
            "Personalización ligera con datos específicos del cliente.",
            "Formación rápida sobre el pack y sus casos de uso.",
            "Puesta en marcha con soporte prioritario las primeras semanas.",
        ],
        "Packs pre-configurados de prompts, flujos y agentes, integraciones específicas por sector "
        "(TPV de restaurantes, software de gestión de clínicas, sistemas de reserva de gimnasios, etc.).",
        "Bajo (la configuración base ya está hecha).",
        "Bajo-Medio (el trabajo pesado de adaptación sectorial ya está realizado).",
        "Muy Alto. Los clientes con Vertical Pack suelen ver resultados significativos en las primeras "
        "2-4 semanas, mucho antes que con soluciones genéricas.",
        None, None,
    )

    story += servicio(
        9, "Meraki Academy – Formación y Capacitación",
        "Programa de formación práctica y personalizada para que el equipo del cliente aprenda a "
        "utilizar eficazmente las herramientas de IA de MerakIA y desarrolle competencias internas en "
        "IA aplicada a su negocio. Incluye talleres presenciales u online, materiales de apoyo, "
        "ejercicios prácticos y seguimiento posterior.",
        "El cliente deja de depender completamente de MerakIA para tareas sencillas y desarrolla "
        "capacidad interna. Su equipo gana autonomía, confianza y habilidades que pueden aplicar más "
        "allá de los servicios contratados. Aumenta el aprovechamiento de la tecnología y reduce la "
        "curva de aprendizaje.",
        [
            "Sensación de que la IA es \"cosa de otros\" y no la aprovechan al máximo.",
            "Dependencia total de proveedores externos para cualquier tarea de IA.",
            "Miedo o resistencia del equipo a adoptar nuevas tecnologías.",
            "Subutilización de las herramientas contratadas por falta de conocimiento.",
        ],
        [
            "Diagnóstico de nivel actual del equipo y necesidades formativas.",
            "Diseño del programa de formación adaptado al cliente.",
            "Ejecución de talleres (individuales o grupales, online o presenciales).",
            "Entrega de materiales y guías de referencia.",
            "Ejercicios prácticos con feedback.",
            "Sesión de seguimiento a las 4-6 semanas para resolver dudas y avanzar.",
        ],
        "Materiales propios de MerakIA, casos reales del sector del cliente, ejercicios prácticos con "
        "los agentes de MerakIA, grabaciones de sesiones.",
        "Medio (requiere tiempo y actitud de aprendizaje del equipo).",
        "Medio (requiere buena capacidad didáctica y adaptación).",
        "Alto a medio-largo plazo. Los clientes que invierten en formación suelen aprovechar mucho más "
        "todos los servicios de MerakIA y desarrollan mayor autonomía.",
        None, None,
    )

    story += servicio(
        10, "Meraki Hybrid Team – Retainer con Soporte Humano",
        "Modelo de retainer mensual que combina acceso ilimitado o de alto volumen a todos los agentes "
        "IA de MerakIA con un número de horas de soporte humano experto (estratega de marketing + IA). "
        "El cliente tiene un \"CMO fraccionario\" que revisa resultados, propone mejoras, ajusta "
        "estrategia y actúa como punto de contacto principal, mientras los agentes ejecutan el trabajo "
        "operativo.",
        "El cliente obtiene lo mejor de ambos mundos: la velocidad, escalabilidad y coste de la IA, "
        "combinado con la inteligencia estratégica, el juicio humano y la relación de confianza de un "
        "profesional experimentado. Ideal para negocios que quieren crecer de forma sostenida sin tener "
        "que contratar un equipo interno completo de marketing.",
        [
            "Sensación de \"navegar a ciegas\" aunque se tengan herramientas potentes.",
            "Falta de visión estratégica y alguien que \"piense\" por el negocio.",
            "Necesidad de alguien de confianza que revise y valide lo que genera la IA.",
            "Deseo de tener un \"socio\" de marketing sin el coste de un equipo o agencia tradicional.",
        ],
        [
            "Definición de objetivos anuales y mensuales del negocio.",
            "Configuración del acceso a agentes y asignación de horas de soporte humano.",
            "Reunión de kick-off y alineación estratégica.",
            "Ritmo de trabajo mensual: planificación, ejecución con IA, revisión humana, reporting.",
            "Revisiones trimestrales de estrategia y ajuste de rumbo.",
        ],
        "Acceso prioritario a todos los agentes de MerakIA, dashboard de seguimiento compartido, "
        "reuniones periódicas con el estratega humano asignado, informes ejecutivos mensuales.",
        "Bajo (participa en revisiones estratégicas).",
        "Medio-Alto (requiere estrategas senior y gestión de expectativas).",
        "Muy Alto para clientes que facturan lo suficiente como para justificar el retainer. Ofrece "
        "crecimiento más ordenado, menor riesgo y mayor tranquilidad.",
        None, None,
    )

    # ── SERVICIO 11 — NUEVO ────────────────────────────────────────────────────
    story += servicio(
        11, "Agente de Voz IA – Recepción Telefónica 24/7",
        "Diseño y configuración completa de un agente de voz telefónico con IA que atiende las llamadas "
        "del negocio de forma autónoma: responde con voz natural, recoge información del cliente, "
        "agenda citas en tiempo real consultando el calendario, gestiona preguntas sobre servicios y "
        "precios, y escala a humano cuando detecta una situación compleja. Funciona 24/7, incluidos "
        "fines de semana y festivos. Preparado para conectarse a la línea telefónica existente mediante "
        "desvío de llamadas o centralita.",
        "El negocio nunca pierde una llamada: ni fuera de horario, ni cuando el equipo está ocupado con "
        "pacientes o clientes. El agente suena como una recepcionista real entrenada por el propio "
        "negocio — conoce los servicios, los precios y los horarios. Agenda citas directamente en el "
        "Google Calendar del negocio, eliminando el riesgo de dobles reservas.",
        [
            "Llamadas perdidas fuera de horario que se convierten en clientes de la competencia.",
            "Recepcionista ocupada que no puede atender el teléfono durante tratamientos.",
            "Coste elevado de ampliar el horario de atención telefónica con personal humano.",
            "Dobles reservas y errores de agenda cuando hay múltiples canales de citas.",
            "Información inconsistente sobre precios y disponibilidad según quién atienda.",
        ],
        [
            "Recopilación de información del negocio: servicios, precios, horarios, FAQ, política de cancelación.",
            "Carga opcional de documentos (carta, tratamientos, tarifas) como base de conocimiento.",
            "Diseño del system prompt optimizado para voz: flujo de llamada, tono, frases clave.",
            "Configuración en Vapi.ai: voz ElevenLabs en español, transcripción Deepgram, modelo Claude.",
            "Integración con Google Calendar vía n8n: check de disponibilidad + creación de cita en tiempo real.",
            "Configuración del desvío de llamadas desde la línea del negocio (móvil o centralita).",
            "Pruebas de llamadas reales y ajuste fino del agente.",
            "Entrega con guía de uso y monitorización inicial.",
        ],
        "Vapi.ai (plataforma de agentes de voz), ElevenLabs (síntesis de voz natural en español), "
        "Deepgram nova-2 (transcripción en español), Claude (modelo de lenguaje), n8n (automatización "
        "de agenda), Google Calendar API, desvío de llamadas USSD (móvil) o reglas de centralita "
        "(Ringover, Vonage, etc.).",
        "Bajo (proporciona información del negocio; la gestión posterior es mínima).",
        "Medio-Alto (requiere diseño cuidadoso del flujo de voz y pruebas reales).",
        "Muy Alto. Una clínica dental que recibe 20 llamadas fuera de horario al mes y convierte solo "
        "el 30% porque nadie atiende, con el agente puede recuperar 14+ citas adicionales al mes. "
        "El ROI suele cubrirse en la primera semana de uso.",
        [
            "Agente de voz configurado y activo en Vapi.ai, listo para recibir llamadas.",
            "System prompt + flujos de conversación + ejemplos documentados.",
            "Workflow n8n de agenda en tiempo real conectado a Google Calendar.",
            "Guía de desvío de llamadas personalizada según el tipo de línea del negocio.",
            "JSON exportable de configuración Vapi para backup y portabilidad.",
            "Sesión de pruebas + entrega con formación básica de seguimiento.",
        ],
        "Clínicas dentales y de estética (altísimo volumen de llamadas de citas), fisioterapeutas, "
        "psicólogos, veterinarias, peluquerías y salones de belleza, restaurantes con reservas "
        "telefónicas, cualquier negocio con recepción telefónica activa.",
        "El Agente de Voz es el servicio de mayor impacto inmediato para negocios con alta demanda "
        "telefónica. Cada llamada perdida es dinero que va a la competencia — el agente lo recupera "
        "sin aumentar el equipo.",
    )

    # ── SERVICIO 12 — NUEVO ────────────────────────────────────────────────────
    story += servicio(
        12, "Recordatorios & Fidelización – Anti-No-Show Automatizado",
        "Sistema completo de comunicación automatizada con clientes antes, durante y después de su "
        "visita. Incluye: recordatorios de cita (24h y 2h antes), confirmación anti-no-show con "
        "respuesta de un clic, recuperación de ausencias sin culpabilizar, reactivación de clientes "
        "dormidos (win-back), mensaje post-visita con petición de reseña en Google y sugerencia de "
        "próxima cita, y felicitación de cumpleaños con oferta personalizada. Todo automatizado vía "
        "WhatsApp Business o email, usando Google Calendar como fuente única de verdad.",
        "El negocio reduce drásticamente los no-shows (ausencias sin avisar), que en muchos sectores "
        "suponen entre el 10-25% de los huecos agenda. Cada cita recuperada es facturación directa. "
        "Además, el sistema reactiva clientes que no han vuelto y genera reseñas positivas en Google "
        "de forma consistente, mejorando el posicionamiento local sin esfuerzo manual.",
        [
            "No-shows que dejan huecos en la agenda sin posibilidad de rellenarlos.",
            "Pérdida de clientes que no vuelven porque nadie les recuerda que existen.",
            "Falta de reseñas en Google pese a tener clientes satisfechos (nadie las deja si no se les pide).",
            "Gestión manual de recordatorios que consume tiempo del equipo.",
            "Dificultad para reactivar clientes inactivos sin parecer invasivo.",
        ],
        [
            "Recopilación de información del negocio: servicios, ciclos de visita, tono de comunicación.",
            "Generación del pack completo de mensajes con IA, personalizado al sector y al negocio.",
            "Configuración del workflow n8n: Schedule Trigger horario → Google Calendar → WhatsApp/Email.",
            "Personalización de variables automáticas: {nombre}, {fecha}, {hora}, {servicio}, {negocio}.",
            "Configuración del canal de envío: WhatsApp Business vía Twilio o Gmail.",
            "Pruebas con datos reales y ajuste de cadencia (cuándo enviar cada mensaje).",
            "Activación y monitorización inicial.",
        ],
        "n8n (automatización de workflows), Google Calendar API (fuente de eventos), Twilio "
        "(WhatsApp Business para recordatorios), Gmail (canal email alternativo), Claude IA "
        "(generación del pack de mensajes personalizado), Google Reviews API (enlace de reseña directo).",
        "Bajo (proporciona información del negocio y acceso al calendario; funciona solo).",
        "Medio (requiere configurar correctamente el workflow y los canales de envío).",
        "Muy Alto. Reducir los no-shows del 20% al 5% en una agenda de 100 citas al mes supone "
        "15 citas recuperadas — a 50€ de media son 750€/mes adicionales. El sistema también genera "
        "reseñas y reactiva clientes, amplificando el impacto más allá de la reducción de ausencias.",
        [
            "Pack completo de 6 secuencias de mensajes personalizadas al negocio y sector.",
            "Workflow n8n exportable y listo para importar (recordatorios automáticos por hora).",
            "Configuración de cadencia recomendada según sector (cuándo enviar cada tipo de mensaje).",
            "Guía de activación paso a paso (Calendar → n8n → WhatsApp/Gmail).",
            "Variables predefinidas para personalización automática por cliente.",
        ],
        "Clínicas dentales, de estética y fisioterapia (reducción de no-shows es crítica), "
        "peluquerías y salones de belleza, consultas de psicología y nutrición, veterinarias, "
        "gimnasios (reactivación de socios inactivos), cualquier negocio con citas programadas.",
        "Recordatorios & Fidelización es el servicio de mayor ROI silencioso: no capta nuevos "
        "clientes, pero multiplica el valor de los que ya tienes. Combinado con el Agente de Voz, "
        "forma el sistema de atención y fidelización más completo del mercado para pymes.",
    )

    # ── TABLA COMPARATIVA ──────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Tabla Comparativa de Servicios", ST["service"]))
    story.append(hr())

    tabla_data = [
        ["Servicio", "Ideal para", "Beneficio Principal", "Dificultad Cliente"],
        ["Soul Audit", "Todos (punto de entrada)", "Visión clara + plan priorizado", "Bajo"],
        ["Content Engine", "Todos los verticales", "Contenido constante y profesional", "Bajo-Medio"],
        ["Web / Landing Pages", "Lanzamientos y campañas", "Presencia profesional que convierte", "Bajo"],
        ["Chatbots", "Alto volumen consultas", "Atención 24/7 + cualificación leads", "Bajo-Medio"],
        ["Project Manager IA", "Proyectos complejos", "Ejecución ordenada sin esfuerzo", "Bajo"],
        ["MerakChat", "Soporte o atención interna", "Respuestas inmediatas y consistentes", "Bajo"],
        ["Automatización", "Procesos repetitivos", "Ahorro de tiempo y reducción errores", "Bajo-Medio"],
        ["Vertical Packs", "Todos (especialmente nuevos)", "Puesta en marcha rápida y relevante", "Bajo"],
        ["Academy", "Equipos que quieren autonomía", "Capacidad interna en IA", "Medio"],
        ["Hybrid Team", "Crecimiento sostenido", "Estrategia + ejecución sin equipo interno", "Bajo"],
        ["★ Agente de Voz IA", "Negocios con alta demanda telefónica", "Cero llamadas perdidas + agenda automática", "Bajo"],
        ["★ Recordatorios & Fidelización", "Negocios con citas programadas", "Reducción no-shows + reseñas + win-back", "Bajo"],
    ]

    col_widths = [4.2*cm, 4.5*cm, 5.5*cm, 3.0*cm]
    t = Table(tabla_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),  (-1,0),  TABLE_HEADER),
        ("TEXTCOLOR",    (0,0),  (-1,0),  WHITE),
        ("FONTNAME",     (0,0),  (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0,0),  (-1,0),  9),
        ("FONTNAME",     (0,1),  (-1,-1), "Helvetica"),
        ("FONTSIZE",     (0,1),  (-1,-1), 8.5),
        ("BACKGROUND",   (0,11), (-1,12), PURPLE_BG),
        ("TEXTCOLOR",    (0,11), (-1,12), PURPLE),
        ("FONTNAME",     (0,11), (-1,12), "Helvetica-Bold"),
        ("ROWBACKGROUNDS",(0,1), (-1,10), [WHITE, colors.HexColor("#F9F5FF")]),
        ("GRID",         (0,0),  (-1,-1), 0.5, GRAY_LINE),
        ("VALIGN",       (0,0),  (-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0),  (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),  (-1,-1), 5),
        ("LEFTPADDING",  (0,0),  (-1,-1), 6),
        ("RIGHTPADDING", (0,0),  (-1,-1), 6),
    ]))
    story.append(t)

    story.append(Spacer(1, 1*cm))
    story.append(box(
        "MerakIA no vende herramientas. Vendemos resultados. Cada servicio está diseñado para "
        "resolver un dolor real de las pymes y entregar un beneficio tangible, medible y sostenible "
        "en el tiempo. La combinación de varios servicios genera un efecto sinérgico mucho mayor "
        "que la suma de las partes."
    ))

    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        f"Documento generado el {datetime.date.today().strftime('%d de %B de %Y')}.",
        ST["footer"]
    ))
    story.append(Paragraph(
        "© 2026 MerakIA — Inteligencia Artificial con Alma para tu Negocio.",
        ST["footer"]
    ))
    story.append(Paragraph(
        "Este documento es confidencial y forma parte del manual operativo de MerakIA.",
        ST["footer"]
    ))

    return story


# ── API reutilizable ────────────────────────────────────────────────────────────
def generar_pdf(destino) -> None:
    """Construye el catálogo en `destino` (ruta str o buffer BytesIO)."""
    doc = SimpleDocTemplate(
        destino,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm,  bottomMargin=2*cm,
        title="MerakIA — Catálogo de Servicios 2026",
        author="MerakIA",
    )
    doc.build(build_story(), onFirstPage=page_header_footer,
              onLaterPages=page_header_footer)


def generar_pdf_bytes() -> bytes:
    """Devuelve el catálogo como bytes (para descarga directa en Streamlit)."""
    import io
    buf = io.BytesIO()
    generar_pdf(buf)
    return buf.getvalue()


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os; os.makedirs("outputs", exist_ok=True)
    output = "outputs/MerakIA_Catalogo_Servicios_2026_v2.pdf"
    generar_pdf(output)
    print(f"PDF generado: {output}")
