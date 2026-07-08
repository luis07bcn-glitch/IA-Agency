"""
Genera el PDF: MerakIA — Estrategia de Captación y Marketing 2026
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.utils import ImageReader
import datetime
import os

W, H = A4

# ── Colores ────────────────────────────────────────────────────────────────────
PURPLE       = colors.HexColor("#6B2D8B")
PURPLE_LIGHT = colors.HexColor("#9B59B6")
PURPLE_BG    = colors.HexColor("#F3E8FF")
DARK         = colors.HexColor("#1A1A2E")
GRAY         = colors.HexColor("#CCCCCC")
GRAY_BG      = colors.HexColor("#F8F8F8")
GREEN        = colors.HexColor("#27AE60")
GREEN_BG     = colors.HexColor("#E8F8F0")
ORANGE       = colors.HexColor("#E67E22")
ORANGE_BG    = colors.HexColor("#FEF5E7")
RED          = colors.HexColor("#E74C3C")
WHITE        = colors.white
TABLE_HEAD   = colors.HexColor("#4A1A6E")

styles = getSampleStyleSheet()

def s(name, **kw):
    return ParagraphStyle(name, parent=styles["Normal"], **kw)

ST = {
    "h1":      s("h1",   fontName="Helvetica-Bold", fontSize=26, textColor=PURPLE,
                          alignment=TA_CENTER, spaceAfter=6),
    "h2":      s("h2",   fontName="Helvetica-Bold", fontSize=15, textColor=PURPLE,
                          spaceBefore=14, spaceAfter=6),
    "h3":      s("h3",   fontName="Helvetica-Bold", fontSize=11, textColor=PURPLE,
                          spaceBefore=10, spaceAfter=4),
    "body":    s("body", fontName="Helvetica", fontSize=9.5, textColor=DARK,
                          leading=14, alignment=TA_JUSTIFY, spaceAfter=6),
    "bullet":  s("bul",  fontName="Helvetica", fontSize=9.5, textColor=DARK,
                          leading=13, leftIndent=14, firstLineIndent=-14, spaceAfter=3),
    "num":     s("num",  fontName="Helvetica-Bold", fontSize=9.5, textColor=DARK,
                          leading=13, leftIndent=14, firstLineIndent=-14, spaceAfter=3),
    "caption": s("cap",  fontName="Helvetica-Oblique", fontSize=9, textColor=PURPLE,
                          alignment=TA_CENTER, leading=13),
    "label":   s("lbl",  fontName="Helvetica-Bold", fontSize=8, textColor=PURPLE,
                          alignment=TA_CENTER),
    "sub":     s("sub",  fontName="Helvetica", fontSize=12, textColor=PURPLE_LIGHT,
                          alignment=TA_CENTER, spaceAfter=4),
    "footer":  s("ftr",  fontName="Helvetica", fontSize=8,
                          textColor=colors.HexColor("#888888"), alignment=TA_CENTER),
    "script":  s("scr",  fontName="Helvetica-Oblique", fontSize=9.5, textColor=DARK,
                          leading=14, leftIndent=8, rightIndent=8,
                          borderColor=PURPLE_LIGHT, borderWidth=0, spaceAfter=4),
    "tag":     s("tag",  fontName="Helvetica-Bold", fontSize=8, textColor=WHITE,
                          alignment=TA_CENTER),
}

def hr():
    return HRFlowable(width="100%", thickness=1.5, color=PURPLE, spaceAfter=8, spaceBefore=4)

def hr_thin():
    return HRFlowable(width="100%", thickness=0.5, color=GRAY, spaceAfter=6, spaceBefore=4)

def bullet(text, bold_prefix=None):
    if bold_prefix:
        return Paragraph(f"• <b>{bold_prefix}</b> {text}", ST["bullet"])
    return Paragraph(f"• {text}", ST["bullet"])

def numbered(n, text):
    return Paragraph(f"{n}. {text}", ST["num"])

def box(text, bg=PURPLE_BG, border=PURPLE_LIGHT, text_style="caption"):
    data = [[Paragraph(text, ST[text_style])]]
    t = Table(data, colWidths=[16*cm])
    t.setStyle(TableStyle([
        ("BOX",           (0,0), (-1,-1), 1, border),
        ("BACKGROUND",    (0,0), (-1,-1), bg),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING",   (0,0), (-1,-1), 14),
        ("RIGHTPADDING",  (0,0), (-1,-1), 14),
    ]))
    return t

def color_box(label, bg, border):
    data = [[Paragraph(label, ST["tag"])]]
    t = Table(data, colWidths=[3.5*cm], rowHeights=[0.55*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), bg),
        ("BOX",           (0,0), (-1,-1), 1, border),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    return t

def page_deco(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(colors.HexColor("#888888"))
    canvas_obj.drawString(2*cm, H - 1.3*cm, "MerakIA • Estrategia de Captación y Marketing 2026")
    canvas_obj.drawRightString(W - 2*cm, H - 1.3*cm, "CONFIDENCIAL")
    canvas_obj.setStrokeColor(GRAY)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(2*cm, H - 1.5*cm, W - 2*cm, H - 1.5*cm)
    canvas_obj.drawCentredString(W/2, 1*cm, f"— {canvas_obj.getPageNumber()} —")
    canvas_obj.restoreState()


def build():
    story = []

    # ══════════════════════════════════════════════════════════════════════════
    # PORTADA
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 1.2*cm))
    story.append(Paragraph("MERAKIA", ST["h1"]))
    story.append(Paragraph("Estrategia de Captación y Marketing 2026", ST["sub"]))
    story.append(Spacer(1, 0.4*cm))
    story.append(hr())
    story.append(Spacer(1, 0.6*cm))

    # Foto del fundador centrada
    foto_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "foto Luis IA.jpg")
    if os.path.exists(foto_path):
        # Calcular dimensiones para recorte circular-ish: foto cuadrada centrada
        foto_w = 6.5 * cm
        foto_h = 7.5 * cm
        img = Image(foto_path, width=foto_w, height=foto_h)
        img.hAlign = "CENTER"

        # Marco de tabla centrado con borde violeta
        foto_table = Table(
            [[img]],
            colWidths=[foto_w + 0.6*cm],
            rowHeights=[foto_h + 0.6*cm],
        )
        foto_table.setStyle(TableStyle([
            ("ALIGN",         (0,0), (-1,-1), "CENTER"),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("BOX",           (0,0), (-1,-1), 2.5, PURPLE),
            ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#0D0D1A")),
            ("TOPPADDING",    (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LEFTPADDING",   (0,0), (-1,-1), 4),
            ("RIGHTPADDING",  (0,0), (-1,-1), 4),
        ]))

        # Centrar la foto usando una tabla exterior de ancho de página
        outer = Table(
            [[foto_table]],
            colWidths=[16*cm],
        )
        outer.setStyle(TableStyle([
            ("ALIGN",  (0,0), (-1,-1), "CENTER"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(outer)
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(
            "Luis — Fundador &amp; Chief AI Officer · MerakIA",
            ST["caption"]
        ))
        story.append(Spacer(1, 0.5*cm))

    story.append(box(
        "Cómo conseguir los primeros clientes, construir autoridad local\n"
        "y escalar MerakIA a un negocio de 6 cifras.",
        bg=PURPLE_BG, border=PURPLE_LIGHT, text_style="caption"
    ))
    story.append(Spacer(1, 0.8*cm))

    # Índice visual
    indice = [
        ["01", "Posicionamiento y propuesta de valor única"],
        ["02", "Cliente ideal (ICP) — a quién venderle primero"],
        ["03", "Los primeros 90 días — plan de acción concreto"],
        ["04", "Canales de captación — dónde y cómo aparecer"],
        ["05", "Proceso de venta — de lead a cliente pagando"],
        ["06", "Scripts de venta — qué decir en cada situación"],
        ["07", "Paquetes de entrada — cómo fijar precios"],
        ["08", "Estrategia de contenido para MerakIA"],
        ["09", "KPIs y métricas de seguimiento"],
    ]
    idx_data = [[Paragraph(f"<font color='#9B59B6'><b>{r[0]}</b></font>", ST["body"]),
                 Paragraph(r[1], ST["body"])] for r in indice]
    idx_t = Table(idx_data, colWidths=[1.5*cm, 13.5*cm])
    idx_t.setStyle(TableStyle([
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LINEBELOW",     (0,0), (-1,-2), 0.4, GRAY),
    ]))
    story.append(idx_t)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 01 — POSICIONAMIENTO
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("01 — Posicionamiento y Propuesta de Valor Única", ST["h2"]))
    story.append(hr())
    story.append(Paragraph(
        "El mayor error que cometen las agencias de IA es posicionarse como \"hacemos IA para empresas\". "
        "Eso no significa nada. MerakIA tiene una ventaja enorme: está construida específicamente para "
        "pymes locales españolas. Eso es un nicho concreto, con dolores concretos y presupuestos reales.",
        ST["body"]
    ))

    story.append(Paragraph("La frase que te define", ST["h3"]))
    story.append(box(
        '"Somos la agencia de IA para negocios locales españoles que quieren atender más clientes, '
        'perder menos citas y aparecer primero en Google — sin necesitar un equipo de tecnología."',
        bg=PURPLE_BG, border=PURPLE, text_style="caption"
    ))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("Los 3 pilares de diferenciación", ST["h3"]))
    for bold, desc in [
        ("Especialización radical en pymes locales.",
         "No trabajamos con startups ni grandes empresas. Solo negocios locales con 1-20 empleados. "
         "Eso nos permite conocer sus problemas mejor que nadie."),
        ("Entregamos resultados, no software.",
         "El cliente no aprende a usar herramientas. Recibe el agente de voz configurado, "
         "el calendario editorial listo, las respuestas a reseñas escritas. Llave en mano."),
        ("IA con alma.",
         "El posicionamiento emocional: la IA de MerakIA suena humana, habla como el negocio "
         "y trata a los clientes como personas. No como un chatbot genérico."),
    ]:
        story.append(bullet(desc, bold_prefix=bold))

    story.append(Paragraph("Contra quién competimos (y cómo ganar)", ST["h3"]))
    comp_data = [
        ["Competidor", "Su debilidad", "Nuestro argumento"],
        ["Agencias de marketing tradicionales",
         "No saben de IA,\nofrecen posts manuales",
         "Mismo precio, 10x más rápido\ny con datos reales"],
        ["Freelancers de IA genéricos",
         "Sin especialización\nsectorial",
         "Sabemos lo que necesita\nuna clínica dental vs un restaurante"],
        ["Tools SaaS (ManyChat, etc.)",
         "El cliente tiene que\naprenderlas solo",
         "Nosotros lo montamos y\nlo gestionamos por ellos"],
        ["No hacer nada (status quo)",
         "Pierden clientes ante\ncompetidores más ágiles",
         "Cada llamada perdida son\n50-200€ que van a la competencia"],
    ]
    comp_t = Table(comp_data, colWidths=[4.5*cm, 5*cm, 6*cm])
    comp_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), TABLE_HEAD),
        ("TEXTCOLOR",     (0,0), (-1,0), WHITE),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8.5),
        ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, GRAY_BG]),
        ("GRID",          (0,0), (-1,-1), 0.4, GRAY),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 7),
    ]))
    story.append(comp_t)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 02 — ICP
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("02 — Cliente Ideal (ICP) — A Quién Venderle Primero", ST["h2"]))
    story.append(hr())
    story.append(Paragraph(
        "No todos los negocios locales son iguales. Para maximizar la tasa de cierre en los primeros "
        "meses, hay que concentrar el esfuerzo en el perfil que más rápido convierte y con quien "
        "más fácil es demostrar ROI.",
        ST["body"]
    ))

    story.append(Paragraph("Perfil de cliente ideal — Tier 1 (atacar primero)", ST["h3"]))
    story.append(box(
        "Clínica dental, de estética o fisioterapia · 1-5 dentistas/terapeutas · "
        "Facturación 200.000-800.000€/año · Con ficha de Google con reseñas · "
        "Reciben llamadas que no siempre pueden atender · Ya gastan en marketing pero no miden resultados",
        bg=GREEN_BG, border=GREEN, text_style="body"
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>¿Por qué este perfil?</b>", ST["body"]))
    for t in [
        "Ticket de servicio alto (40-300€/cita) → el ROI del agente de voz se ve en días, no meses.",
        "Sufren no-shows (10-25% de las citas) → Recordatorios & Fidelización es una venta fácil.",
        "El dueño suele ser el que atiende el teléfono → motivación altísima para automatizar.",
        "Comparan precios en Google → reseñas y posicionamiento son críticos para ellos.",
        "Presupuesto disponible: 300-800€/mes en herramientas de gestión sin problema.",
    ]:
        story.append(bullet(t))

    story.append(Paragraph("Perfil Tier 2 (segundo foco)", ST["h3"]))
    tier2_data = [
        ["Sector", "Servicio de entrada más fácil", "Ticket medio mensual"],
        ["Restaurante con reservas", "Agente de Voz + Content Engine", "297-497€/mes"],
        ["Peluquería / salón estética", "Recordatorios + Chatbot", "197-397€/mes"],
        ["Gimnasio / centro deportivo", "Content Engine + Fidelización", "297-497€/mes"],
        ["Farmacia", "Chatbot + Automatización interna", "397-597€/mes"],
        ["Psicólogo / nutricionista", "Agente de Voz + Recordatorios", "197-297€/mes"],
    ]
    t2 = Table(tier2_data, colWidths=[4.5*cm, 6*cm, 4*cm])
    t2.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), TABLE_HEAD),
        ("TEXTCOLOR",     (0,0), (-1,0), WHITE),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8.5),
        ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, GRAY_BG]),
        ("GRID",          (0,0), (-1,-1), 0.4, GRAY),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 7),
    ]))
    story.append(t2)

    story.append(Paragraph("El decisor — quién firma", ST["h3"]))
    story.append(Paragraph(
        "En pymes de 1-10 empleados el decisor es siempre el dueño o gerente. No hay comités ni "
        "departamentos de compras. La venta es emocional y racional a la vez: "
        "<b>le tienes que gustar como persona y demostrarle el ROI en números concretos.</b> "
        "Nunca hables con el recepcionista o el empleado — pide directamente hablar con el dueño.",
        ST["body"]
    ))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 03 — PRIMEROS 90 DÍAS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("03 — Los Primeros 90 Días — Plan de Acción Concreto", ST["h2"]))
    story.append(hr())
    story.append(box(
        "Regla de oro: los primeros 90 días no son de escalar, son de validar. "
        "Un cliente real pagando 300€/mes vale más que 100 leads en una hoja de cálculo.",
        bg=ORANGE_BG, border=ORANGE, text_style="body"
    ))
    story.append(Spacer(1, 0.4*cm))

    for mes, titulo, acciones in [
        ("MES 1 — Semanas 1-4", "Validar y conseguir el primer cliente",
         [
             "SEMANA 1: Prepara tu kit de venta. Configura la web, el perfil de LinkedIn, "
             "el Google Business Profile de MerakIA (sí, tú también necesitas uno). "
             "Ten lista una demo en vivo del Agente de Voz y del Chatbot.",
             "SEMANA 2: Lista de 20 negocios locales de tu zona (clínicas dentales primero). "
             "Búscalos con ProspectorIA — ya tienes la herramienta. Identifica los que tienen "
             "rating <4.2★ o pocas reseñas respondidas. Son los más receptivos.",
             "SEMANA 3: Contacto directo con los 20. Primero WhatsApp o DM de Instagram "
             "(no email en frío). Objetivo: conseguir 5 reuniones, no vender nada todavía.",
             "SEMANA 4: 5 reuniones → Soul Audit gratis como ganchoentrada → "
             "al menos 1 cliente de pago. Si no cierras: analiza el feedback y ajusta.",
         ]),
        ("MES 2 — Semanas 5-8", "Entregar, pedir referidos y escalar el outreach",
         [
             "Entrega impecable al primer cliente. El primer cliente es tu caso de éxito — "
             "documenta resultados (llamadas atendidas, no-shows reducidos, reseñas ganadas).",
             "Pide 2-3 referidos activamente. Las pymes confían más en el boca a boca que "
             "en cualquier anuncio. Un referido cierra al 60-70% vs 10-15% en frío.",
             "Amplía el outreach a 50 negocios. Empieza a publicar contenido en LinkedIn "
             "y en el Instagram de MerakIA (usa tu propio Content Engine para esto).",
             "Objetivo del mes: 2-3 clientes pagando. Ingresos recurrentes: 600-1.500€/mes.",
         ]),
        ("MES 3 — Semanas 9-12", "Sistematizar y crear el primer activo de autoridad",
         [
             "Crea el primer caso de éxito en PDF. Una página, datos reales, antes/después. "
             "Es tu argumento de venta más potente para el resto del año.",
             "Activa Google Ads local con 150-300€/mes. Keywords: 'agencia IA Barcelona', "
             "'chatbot para clínica dental', 'agente de voz para negocio'. ROI rápido.",
             "Pide a los clientes actuales una reseña en tu Google Business. "
             "Las primeras 5 reseñas multiplican la credibilidad x3.",
             "Objetivo del mes: 4-6 clientes. Ingresos recurrentes: 1.500-3.000€/mes. "
             "Sistema de onboarding documentado para poder escalar sin depender de ti solo.",
         ]),
    ]:
        story.append(KeepTogether([
            Paragraph(mes, ST["h3"]),
            Paragraph(f"<i>{titulo}</i>", ST["body"]),
        ]))
        for i, a in enumerate(acciones, 1):
            story.append(numbered(i, a))
        story.append(Spacer(1, 0.3*cm))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 04 — CANALES DE CAPTACIÓN
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("04 — Canales de Captación — Dónde y Cómo Aparecer", ST["h2"]))
    story.append(hr())

    canales = [
        ("🔥 OUTREACH DIRECTO — Prioridad 1",
         ORANGE_BG, ORANGE,
         "El canal más efectivo para los primeros 10 clientes. Contacto personal, "
         "sin intermediarios, conversión alta.",
         [
             "WhatsApp directo al dueño del negocio (no al número general). "
             "Mensaje de 3 líneas: contexto → valor concreto → CTA para una llamada de 15 min.",
             "DM de Instagram a negocios con pocos seguidores pero activos. "
             "Comenta su contenido 2-3 veces antes de enviar el DM.",
             "Visita presencial en frío (especialmente efectivo con clínicas y restaurantes). "
             "Lleva el Soul Audit de su negocio ya hecho — muestra que has hecho los deberes.",
             "Networking en grupos de empresarios locales (BNI, Cámara de Comercio, "
             "grupos de WhatsApp de autónomos de tu ciudad).",
         ]),
        ("📱 LINKEDIN — Prioridad 2",
         PURPLE_BG, PURPLE,
         "Para construir autoridad y recibir leads entrantes. No es inmediato pero "
         "es el canal de mayor calidad a medio plazo.",
         [
             "Publica 3x/semana: casos prácticos, tips de IA para negocios locales, "
             "resultados de clientes (con permiso). Nada de contenido genérico.",
             "Conecta con dueños de clínicas, restaurantes y gimnasios de tu ciudad. "
             "Mensaje de conexión personalizado (menciona algo específico de su negocio).",
             "Comparte el proceso de trabajar en MerakIA: qué construiste esta semana, "
             "qué problema resolviste, qué aprendiste. Genera confianza y curiosidad.",
             "Artículos de 800-1.200 palabras cada 2 semanas: 'Cómo la IA redujo los "
             "no-shows un 65% en una clínica dental de Barcelona' — con datos reales.",
         ]),
        ("🔍 GOOGLE ADS LOCAL — Prioridad 3",
         GREEN_BG, GREEN,
         "Actívalo en el mes 3 cuando tengas 1-2 casos de éxito. "
         "Con 150-300€/mes puedes generar 5-10 leads cualificados al mes.",
         [
             "Keywords de intención alta: 'agente de voz para clínica', 'chatbot whatsapp "
             "para restaurante', 'automatización para dentista'.",
             "Landing page específica por sector (usa tu Web Developer de la plataforma). "
             "Una landing para clínicas, otra para restaurantes.",
             "Lead magnet: 'Descarga gratis el informe de IA para clínicas dentales 2026'. "
             "Captura email y nurturing por WhatsApp.",
             "Retargeting a visitantes de la web que no convirtieron: anuncio con "
             "el caso de éxito del cliente + CTA para diagnóstico gratuito.",
         ]),
        ("📧 EMAIL & WHATSAPP NURTURING — Prioridad 4",
         GRAY_BG, GRAY,
         "Para leads que no convierten en la primera reunión. "
         "El 80% de las ventas B2B se cierran entre el contacto 5 y el 12.",
         [
             "Secuencia de 5 emails de bienvenida tras el Soul Audit gratuito: "
             "D+1 caso de éxito → D+3 tip accionable → D+7 oferta → D+14 seguimiento.",
             "Grupo de WhatsApp 'Propietarios de [Ciudad] + IA': newsletter semanal "
             "con 1 tip práctico. Máximo 50 personas. Crea comunidad antes de vender.",
             "Newsletter mensual con 3 casos reales + 1 herramienta práctica gratis. "
             "Construye lista desde el día 1 — incluso sin clientes todavía.",
         ]),
    ]

    for titulo, bg, border, intro, bullets in canales:
        story.append(KeepTogether([
            Paragraph(titulo, ST["h3"]),
            Paragraph(intro, ST["body"]),
        ]))
        for b in bullets:
            story.append(bullet(b))
        story.append(Spacer(1, 0.3*cm))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 05 — PROCESO DE VENTA
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("05 — Proceso de Venta — De Lead a Cliente Pagando", ST["h2"]))
    story.append(hr())
    story.append(Paragraph(
        "Las pymes locales no compran software. Compran confianza, resultados y comodidad. "
        "El proceso de venta de MerakIA está diseñado para eliminar la fricción y "
        "demostrar valor antes de pedir dinero.",
        ST["body"]
    ))

    pasos_venta = [
        ("PASO 1 — Primer contacto (Día 0)",
         "Objetivo: conseguir una reunión de 20-30 min, nada más.",
         [
             "Mensaje de WhatsApp (ejemplo en sección 06): 3 líneas, personalizado, CTA claro.",
             "Si no responde en 48h: 1 seguimiento. Si no responde: pasa al siguiente.",
             "No vendas nada en el primer mensaje. Solo despierta curiosidad.",
         ]),
        ("PASO 2 — Reunión de diagnóstico (Día 3-7)",
         "Objetivo: entender el negocio y el dolor. No presentar servicios todavía.",
         [
             "Primeros 10 min: preguntas abiertas. '¿Cuántas llamadas perdéis fuera de horario?' "
             "'¿Cuántos no-shows tenéis al mes?' '¿Alguien lleva vuestras redes?'",
             "Muestra que conoces su sector: menciona datos específicos de su tipo de negocio.",
             "Al final: '¿Te parece bien si preparo un análisis rápido de tu situación "
             "y te lo presento la semana que viene? Sin coste, sin compromiso.'",
         ]),
        ("PASO 3 — Soul Audit (Día 7-10)",
         "Objetivo: impresionar con el análisis y anclar el problema con datos reales.",
         [
             "Usa ProspectorIA para generar el informe completo de su negocio.",
             "Personaliza con 2-3 observaciones muy específicas que demuestren que "
             "has estudiado su negocio a fondo (menciona una reseña negativa concreta, "
             "un competidor que le está ganando terreno, una oportunidad que está perdiendo).",
             "Entrega en reunión presencial o videollamada, nunca por email solo.",
         ]),
        ("PASO 4 — Propuesta (Día 10-12)",
         "Objetivo: proponer la solución mínima que resuelve el dolor más urgente.",
         [
             "No propongas los 9 servicios de golpe. Propón 1-2 servicios que "
             "resuelvan el dolor más agudo identificado en el diagnóstico.",
             "Presenta siempre el ROI en euros: 'Si el agente de voz recupera "
             "8 citas al mes a 80€ de media, son 640€/mes extra. El servicio son 297€/mes.'",
             "Ofrece 3 opciones de precio (ver sección 07). La del medio siempre gana.",
             "Incluye garantía de satisfacción: 'Si en 30 días no ves resultados, "
             "te devuelvo el dinero.' Reduce el riesgo percibido al mínimo.",
         ]),
        ("PASO 5 — Cierre (Día 12-15)",
         "Objetivo: cobrar el primer mes y empezar la implementación.",
         [
             "Si no cierra en la reunión: seguimiento a las 48h con un 'Por cierto, "
             "he visto que tu competidor [nombre] acaba de activar un chatbot en su web.'",
             "Cobra el setup + primer mes por adelantado. Acepta Bizum, transferencia o Stripe.",
             "Envía contrato sencillo de 1 página (alcance, precio, duración, cláusula de salida).",
             "Onboarding inmediato: agenda la sesión de configuración para la semana siguiente.",
         ]),
    ]

    for paso, objetivo, bullets in pasos_venta:
        story.append(KeepTogether([
            Paragraph(paso, ST["h3"]),
            Paragraph(f"<i>{objetivo}</i>", ST["body"]),
        ]))
        for b in bullets:
            story.append(bullet(b))
        story.append(Spacer(1, 0.2*cm))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 06 — SCRIPTS DE VENTA
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("06 — Scripts de Venta — Qué Decir en Cada Situación", ST["h2"]))
    story.append(hr())

    scripts = [
        ("WhatsApp de primer contacto — Clínica dental",
         "Hola [Nombre], soy [tu nombre] de MerakIA.\n\n"
         "He analizado vuestra clínica en Google y vi que tenéis 47 reseñas con un 4.1★ — "
         "hay margen claro de mejora, especialmente en tiempo de respuesta fuera de horario.\n\n"
         "Trabajo con clínicas como la vuestra para que no pierdan pacientes cuando el teléfono "
         "no está atendido. ¿Te parece si hablamos 20 minutos esta semana?"),
        ("WhatsApp de primer contacto — Restaurante",
         "Hola [Nombre], soy [tu nombre] de MerakIA.\n\n"
         "Vi que [Restaurante] tiene muy buenas reseñas pero no tenéis nadie respondiendo "
         "a las últimas 6 — eso se nota en Google Maps.\n\n"
         "Ayudo a restaurantes a automatizar la gestión de reseñas y reservas con IA. "
         "¿5 minutos esta semana para contarte cómo?"),
        ("Respuesta a '¿cuánto cuesta?' en la primera llamada",
         "Antes de darte un número, déjame hacerte 2 preguntas rápidas para asegurarme "
         "de que lo que te propongo tiene sentido para tu negocio.\n\n"
         "¿Cuántas llamadas creéis que perdéis a la semana fuera de horario?\n"
         "¿Tenéis problemas de no-shows — gente que no aparece a la cita?\n\n"
         "[Tras las respuestas]: Entonces la inversión que tiene más sentido para vosotros "
         "está entre X y Y euros al mes. Y el ROI suele verse en las primeras 2-4 semanas."),
        ("Respuesta a 'ya tenemos una agencia de marketing'",
         "Perfecto, eso me indica que ya entendéis el valor del marketing. "
         "Lo que hacemos en MerakIA es diferente: no creamos contenido manualmente "
         "ni gestionamos anuncios.\n\n"
         "Automatizamos la atención al cliente, las citas y los recordatorios con IA — "
         "cosas que una agencia de marketing no toca. De hecho, muchos de nuestros clientes "
         "trabajan con su agencia de siempre y nos contratan a nosotros para lo operativo.\n\n"
         "¿Te cuento en 10 minutos la diferencia con un caso concreto?"),
        ("Respuesta a 'no tenemos presupuesto ahora'",
         "Lo entiendo perfectamente. Déjame hacerte una pregunta:\n\n"
         "Si el agente de voz atiende las llamadas que ahora se pierden y recupera "
         "5 citas al mes a [precio medio de su servicio]€ cada una — ¿eso cubre con creces "
         "la inversión mensual?\n\n"
         "La mayoría de nuestros clientes no lo ven como un gasto sino como una palanca "
         "de ingresos. ¿Te hago un cálculo rápido con tus números?"),
    ]

    for titulo, texto in scripts:
        story.append(Paragraph(titulo, ST["h3"]))
        script_data = [[Paragraph(texto, ST["body"])]]
        t = Table(script_data, colWidths=[16*cm])
        t.setStyle(TableStyle([
            ("BOX",           (0,0), (-1,-1), 1, PURPLE_LIGHT),
            ("BACKGROUND",    (0,0), (-1,-1), PURPLE_BG),
            ("TOPPADDING",    (0,0), (-1,-1), 10),
            ("BOTTOMPADDING", (0,0), (-1,-1), 10),
            ("LEFTPADDING",   (0,0), (-1,-1), 12),
            ("RIGHTPADDING",  (0,0), (-1,-1), 12),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.4*cm))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 07 — PAQUETES Y PRECIOS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("07 — Paquetes de Entrada — Cómo Fijar Precios", ST["h2"]))
    story.append(hr())
    story.append(Paragraph(
        "La regla de los 3 precios: siempre presenta 3 opciones. El 70% elige el del medio, "
        "el 20% elige el alto y solo el 10% elige el bajo. Nunca presentes solo un precio.",
        ST["body"]
    ))
    story.append(Spacer(1, 0.3*cm))

    paquetes = [
        ["", "STARTER\n(entrada)", "PROFESSIONAL\n(más vendido ★)", "PREMIUM\n(máximo impacto)"],
        ["Precio setup", "297€", "497€", "797€"],
        ["Precio mensual", "197€/mes", "397€/mes", "697€/mes"],
        ["Soul Audit inicial", "✓", "✓", "✓"],
        ["Chatbot IA (1 canal)", "✓", "✓", "✓"],
        ["Agente de Voz", "—", "✓", "✓"],
        ["Recordatorios anti-no-show", "—", "✓", "✓"],
        ["Gestor de Reseñas", "—", "✓", "✓"],
        ["Content Engine (mensual)", "—", "—", "✓"],
        ["Informes mensuales", "Básico", "Completo", "Ejecutivo"],
        ["Soporte", "Email", "WhatsApp", "WhatsApp prioritario"],
        ["Garantía", "14 días", "30 días", "30 días"],
        ["Ideal para", "Primer mes /\npresupuesto ajustado",
         "Clínica o peluquería\ncon agenda activa",
         "Negocio que quiere\ncrecer en serio"],
    ]

    col_w = [4.5*cm, 3.5*cm, 4.5*cm, 4.5*cm]
    pkg_t = Table(paquetes, colWidths=col_w)
    pkg_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  TABLE_HEAD),
        ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("BACKGROUND",    (2,0), (2,-1),  colors.HexColor("#3D0F6E")),
        ("TEXTCOLOR",     (2,1), (2,-1),  colors.HexColor("#E8D5FF")),
        ("FONTNAME",      (2,1), (2,-1),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8.5),
        ("FONTNAME",      (0,1), (0,-1),  "Helvetica-Bold"),
        ("FONTNAME",      (1,1), (1,-1),  "Helvetica"),
        ("FONTNAME",      (3,1), (3,-1),  "Helvetica"),
        ("ROWBACKGROUNDS",(0,1), (0,-1),  [WHITE, GRAY_BG]),
        ("GRID",          (0,0), (-1,-1), 0.4, GRAY),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",         (1,0), (-1,-1), "CENTER"),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
    ]))
    story.append(pkg_t)
    story.append(Spacer(1, 0.5*cm))
    story.append(box(
        "Regla de oro: el paquete Professional es el que debes vender siempre de entrada. "
        "Si el cliente dice que es mucho, baja a Starter pero mantén la promesa "
        "de subir a Professional cuando vea los resultados (suele pasar en 60-90 días).",
        bg=ORANGE_BG, border=ORANGE, text_style="body"
    ))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 08 — CONTENIDO PARA MERAKIA
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("08 — Estrategia de Contenido para MerakIA", ST["h2"]))
    story.append(hr())
    story.append(Paragraph(
        "MerakIA necesita su propio Content Engine. El contenido que publiques en LinkedIn "
        "e Instagram no es solo marketing — es demostración de producto. "
        "Si generas buen contenido sobre IA para negocios locales, tus clientes potenciales "
        "llegan ya convencidos.",
        ST["body"]
    ))

    story.append(Paragraph("Los 4 pilares de contenido de MerakIA", ST["h3"]))
    pilares = [
        ("CASOS REALES (40%)",
         "El contenido que más convierte. '¿Cómo una clínica dental de Valencia redujo "
         "sus no-shows un 65% en 30 días?' Con datos, con antes/después, con nombres "
         "(si el cliente lo permite) o anonimizado. Formato: carrusel en Instagram + "
         "artículo en LinkedIn."),
        ("EDUCACIÓN PRÁCTICA (30%)",
         "'5 preguntas que debes hacerte antes de contratar un chatbot para tu negocio'. "
         "'Qué es un Place ID de Google y por qué importa para tu restaurante'. "
         "Contenido que el cliente potencial puede aplicar hoy. Genera confianza y autoridad."),
        ("BEHIND THE SCENES (20%)",
         "Muestra el proceso: qué estás construyendo, qué problema resolviste esta semana, "
         "cómo funciona la plataforma por dentro. La gente compra a personas, no a empresas. "
         "Este contenido humaniza MerakIA y diferencia de las grandes consultoras."),
        ("PROVOCACIÓN Y OPINIÓN (10%)",
         "'La IA no va a quitar el trabajo a los recepcionistas — va a hacer que los dueños "
         "dejen de hacer de recepcionistas.' Contenido que genera debate, comentarios y "
         "visibilidad. Toma posición. Las opiniones blandas no reciben engagement."),
    ]
    for titulo, desc in pilares:
        story.append(bullet(desc, bold_prefix=titulo))

    story.append(Paragraph("Calendario de publicación recomendado", ST["h3"]))
    cal_data = [
        ["Día", "Canal", "Tipo de contenido", "Formato"],
        ["Lunes",     "LinkedIn",  "Caso real o resultado de cliente",          "Texto largo + datos"],
        ["Martes",    "Instagram", "Tip educativo para negocios locales",        "Carrusel 5-7 slides"],
        ["Miércoles", "LinkedIn",  "Behind the scenes / proceso de trabajo",     "Texto medio + foto"],
        ["Jueves",    "Instagram", "Antes / después de un cliente",              "Imagen comparativa"],
        ["Viernes",   "LinkedIn",  "Opinión / provocación del sector IA",        "Texto corto + debate"],
        ["Sábado",    "Instagram", "Contenido ligero / motivacional del sector", "Reel corto 15-30s"],
    ]
    cal_t = Table(cal_data, colWidths=[2.5*cm, 2.5*cm, 7*cm, 4.5*cm])
    cal_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), TABLE_HEAD),
        ("TEXTCOLOR",     (0,0), (-1,0), WHITE),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8.5),
        ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, GRAY_BG]),
        ("GRID",          (0,0), (-1,-1), 0.4, GRAY),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
    ]))
    story.append(cal_t)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 09 — KPIs
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("09 — KPIs y Métricas de Seguimiento", ST["h2"]))
    story.append(hr())
    story.append(Paragraph(
        "Lo que no se mide no mejora. Estos son los números que debes revisar "
        "cada semana para saber si la estrategia de captación está funcionando.",
        ST["body"]
    ))

    kpi_data = [
        ["KPI", "Objetivo mes 1", "Objetivo mes 3", "Objetivo mes 6", "Cómo medirlo"],
        ["Negocios contactados / semana", "20", "40", "60", "Hoja de seguimiento"],
        ["Reuniones conseguidas", "5", "12", "20", "Calendario"],
        ["Tasa conversión reunión→cliente", ">20%", ">30%", ">40%", "CRM simple"],
        ["Clientes activos", "1", "4-6", "10-15", "Facturación"],
        ["MRR (ingresos recurrentes)", "300€", "1.500€", "4.000€", "Contabilidad"],
        ["Churn rate (% baja mensual)", "<10%", "<5%", "<3%", "CRM"],
        ["NPS / satisfacción cliente", "—", ">8/10", ">9/10", "Encuesta mensual"],
        ["Seguidores LinkedIn", "500", "1.000", "2.500", "LinkedIn Analytics"],
        ["Leads inbound (mes)", "0", "3-5", "10-15", "Formulario web"],
    ]
    kpi_t = Table(kpi_data, colWidths=[4.5*cm, 2.3*cm, 2.3*cm, 2.3*cm, 4.6*cm])
    kpi_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), TABLE_HEAD),
        ("TEXTCOLOR",     (0,0), (-1,0), WHITE),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
        ("FONTNAME",      (0,1), (0,-1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, GRAY_BG]),
        ("GRID",          (0,0), (-1,-1), 0.4, GRAY),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",         (1,0), (-1,-1), "CENTER"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
    ]))
    story.append(kpi_t)
    story.append(Spacer(1, 0.6*cm))

    story.append(Paragraph("La única métrica que importa en los primeros 90 días", ST["h3"]))
    story.append(box(
        "Reuniones realizadas por semana.\n\n"
        "Todo lo demás (followers, visitas web, leads en pipeline) es vanidad "
        "si no se convierte en reuniones reales con decisores reales. "
        "Si tienes 5+ reuniones/semana con el perfil correcto, los clientes llegan.",
        bg=GREEN_BG, border=GREEN, text_style="body"
    ))

    story.append(Spacer(1, 1.2*cm))
    story.append(hr_thin())
    story.append(Spacer(1, 0.4*cm))
    story.append(box(
        "La oportunidad existe ahora. El 95% de las pymes locales españolas no tiene "
        "ningún agente de IA. El 5% que lo tiene, tiene resultados que los demás no pueden ignorar. "
        "Quien se mueva primero en su zona, gana el mercado.",
        bg=PURPLE_BG, border=PURPLE, text_style="caption"
    ))
    story.append(Spacer(1, 0.8*cm))
    story.append(Paragraph(f"Documento generado el {datetime.date.today().strftime('%d de %B de %Y')}.", ST["footer"]))
    story.append(Paragraph("© 2026 MerakIA — Inteligencia Artificial con Alma para tu Negocio.", ST["footer"]))
    story.append(Paragraph("Documento confidencial — uso interno.", ST["footer"]))

    return story


def generar_pdf(destino) -> None:
    """Construye la estrategia en `destino` (ruta str o buffer BytesIO)."""
    doc = SimpleDocTemplate(
        destino,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.2*cm, bottomMargin=2*cm,
        title="MerakIA — Estrategia de Captación y Marketing 2026",
        author="MerakIA",
    )
    doc.build(build(), onFirstPage=page_deco, onLaterPages=page_deco)


def generar_pdf_bytes() -> bytes:
    """Devuelve la estrategia como bytes (para descarga directa en Streamlit)."""
    import io
    buf = io.BytesIO()
    generar_pdf(buf)
    return buf.getvalue()


if __name__ == "__main__":
    import os
    os.makedirs("outputs", exist_ok=True)
    output = "outputs/MerakIA_Estrategia_Captacion_2026.pdf"
    generar_pdf(output)
    print(f"PDF generado: {output}")
