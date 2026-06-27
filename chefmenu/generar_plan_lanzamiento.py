"""
Plan de Lanzamiento Completo — ChefMenu AI
Genera plan_lanzamiento_chefmenu.pdf en la misma carpeta
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle,
    Spacer, HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
from pathlib import Path

VERDE    = colors.HexColor("#2e7d32")
VERDE_M  = colors.HexColor("#43a047")
DORADO   = colors.HexColor("#f9a825")
GRIS_OSC = colors.HexColor("#263238")
GRIS_D   = colors.HexColor("#1e2c30")
BLANCO   = colors.white
ROJO     = colors.HexColor("#c62828")
AZUL     = colors.HexColor("#1565c0")

OUTPUT = Path(__file__).parent / "plan_lanzamiento_chefmenu.pdf"
W = 17 * cm


class PortadaCanvas(canvas.Canvas):
    def __init__(self, filename, **kw):
        super().__init__(filename, **kw)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._saved)
        for st in self._saved:
            self.__dict__.update(st)
            self._footer(n)
            super().showPage()
        super().save()

    def _footer(self, n):
        if self._pageNumber == 1:
            return
        pw, ph = A4
        self.saveState()
        self.setFillColor(GRIS_OSC)
        self.rect(0, 0, pw, 1.1 * cm, fill=1, stroke=0)
        self.setFillColor(DORADO)
        self.setFont("Helvetica-Bold", 6.5)
        self.drawString(2 * cm, 0.38 * cm, "ChefMenu AI -- Plan de Lanzamiento Comercial 2025")
        self.setFillColor(colors.HexColor("#90a4ae"))
        self.drawRightString(pw - 2 * cm, 0.38 * cm, f"Pag. {self._pageNumber} / {n}")
        self.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title="ChefMenu AI -- Plan de Lanzamiento",
        author="MerakIA Agency",
    )

    base = getSampleStyleSheet()

    def st(name, **kw):
        return ParagraphStyle(name, parent=base["Normal"], **kw)

    S = {
        "ptit":   st("ptit", fontSize=32, textColor=BLANCO, fontName="Helvetica-Bold",
                     alignment=TA_CENTER, leading=36),
        "psub":   st("psub", fontSize=13, textColor=DORADO, fontName="Helvetica-Bold",
                     alignment=TA_CENTER, spaceAfter=4),
        "pdesc":  st("pdesc", fontSize=9.5, textColor=colors.HexColor("#b0bec5"),
                     alignment=TA_CENTER, leading=14),
        "h1":     st("h1", fontSize=16, textColor=DORADO, fontName="Helvetica-Bold",
                     spaceBefore=4, spaceAfter=5, leading=20),
        "h2":     st("h2", fontSize=12, textColor=VERDE_M, fontName="Helvetica-Bold",
                     spaceBefore=8, spaceAfter=3),
        "body":   st("body", fontSize=8.8, leading=13.5,
                     textColor=colors.HexColor("#cfd8dc")),
        "tc":     st("tc",  fontSize=7.8, leading=11,
                     textColor=colors.HexColor("#cfd8dc")),
        "tc_b":   st("tcb", fontSize=7.8, leading=11, textColor=BLANCO,
                     fontName="Helvetica-Bold"),
        "tc_h":   st("tch", fontSize=7.8, leading=11, textColor=BLANCO,
                     fontName="Helvetica-Bold", alignment=TA_CENTER),
        "tc_c":   st("tcc", fontSize=7.8, leading=11,
                     textColor=colors.HexColor("#cfd8dc"), alignment=TA_CENTER),
        "kpi":    st("kpi", fontSize=20, textColor=DORADO, fontName="Helvetica-Bold",
                     alignment=TA_CENTER),
        "kpi_l":  st("kpil", fontSize=7.5, textColor=colors.HexColor("#90a4ae"),
                     alignment=TA_CENTER, leading=10),
        "alerta": st("alert", fontSize=8.8, textColor=DORADO, fontName="Helvetica-Bold",
                     leading=13),
        "caja_b": st("cajab", fontSize=8.8, textColor=BLANCO,
                     fontName="Helvetica-Bold", leading=13),
    }

    def hr(color=VERDE, t=1.5):
        return HRFlowable(width="100%", thickness=t, color=color, spaceAfter=5)

    def sp(h=0.3):
        return Spacer(1, h * cm)

    def _p(v, sty="tc"):
        if not v and v != 0:
            return Paragraph("", S["tc"])
        if isinstance(v, Paragraph):
            return v
        return Paragraph(str(v), S[sty])

    def _ph(v):
        return _p(v, "tc_h")

    def _pb(v):
        return _p(v, "tc_b")

    def tabla(data, col_widths, header_bg=VERDE, row_colors=None):
        wrapped = []
        for ri, row in enumerate(data):
            new_row = []
            for cell in row:
                if ri == 0:
                    new_row.append(_ph(cell) if not isinstance(cell, Paragraph) else cell)
                else:
                    new_row.append(_p(cell) if not isinstance(cell, Paragraph) else cell)
            wrapped.append(new_row)
        t = Table(wrapped, colWidths=col_widths, repeatRows=1)
        cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), header_bg),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#37474f")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [GRIS_OSC, GRIS_D]),
        ]
        if row_colors:
            for r, c in row_colors:
                cmds.append(("BACKGROUND", (0, r), (-1, r), c))
        t.setStyle(TableStyle(cmds))
        return t

    def caja(texto, bg=GRIS_OSC, border=VERDE, bold=False):
        sty = S["alerta"] if not bold else S["caja_b"]
        data = [[Paragraph(texto, sty)]]
        t = Table(data, colWidths=[W])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("BOX", (0, 0), (-1, -1), 1.5, border),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        return t

    def kpi_row(kpis):
        w = W / len(kpis)
        data = [
            [Paragraph(v, S["kpi"]) for v, _ in kpis],
            [Paragraph(l.replace("\n", "<br/>"), S["kpi_l"]) for _, l in kpis],
        ]
        t = Table(data, colWidths=[w] * len(kpis))
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), GRIS_OSC),
            ("BOX", (0, 0), (-1, -1), 1, VERDE),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#37474f")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return t

    def seccion(num, titulo):
        return [PageBreak(), Paragraph(f"{num}  {titulo}", S["h1"]),
                hr(DORADO, 2), sp(0.25)]

    story = []

    # ═══ PORTADA ════════════════════════════════════════════════════════════
    story.append(sp(3))
    story.append(Paragraph("ChefMenu AI", S["ptit"]))
    story.append(sp(0.4))
    story.append(hr(DORADO, 3))
    story.append(sp(0.2))
    story.append(Paragraph("PLAN DE LANZAMIENTO COMERCIAL COMPLETO", S["psub"]))
    story.append(sp(0.3))
    story.append(Paragraph(
        "Software de gestion de menus para restaurantes potenciado por Inteligencia Artificial",
        S["pdesc"]))
    story.append(sp(1.6))

    port = [
        ["Mercado objetivo", "50.000+ restaurantes con menu del dia en Espana"],
        ["Tecnologia", "Claude AI + Python + SaaS Web"],
        ["Estado actual", "MVP funcional con 12 modulos operativos"],
        ["Objetivo 12 meses", "500 restaurantes de pago -- 25.000 EUR/mes MRR"],
        ["Version documento", "1.0 -- Junio 2025"],
    ]
    tp = Table([[_pb(r[0]), _p(r[1])] for r in port],
               colWidths=[4.5 * cm, 12.5 * cm])
    tp.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), GRIS_OSC),
        ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#1a2535")),
        ("TEXTCOLOR", (0, 0), (0, -1), DORADO),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#37474f")),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(tp)
    story.append(sp(1.6))
    story.append(Paragraph("Elaborado por MerakIA Agency -- Confidencial", S["pdesc"]))

    # ═══ 01 RESUMEN EJECUTIVO ════════════════════════════════════════════════
    story += seccion("01", "RESUMEN EJECUTIVO")

    story.append(Paragraph("La Oportunidad", S["h2"]))
    story.append(Paragraph(
        "Espana cuenta con <b>279.000 restaurantes activos</b>, de los cuales mas de 50.000 ofrecen "
        "menu del dia. El sector mueve <b>43.500 millones de euros anuales</b> (FEHR 2024) y se enfrenta "
        "a un problema estructural: la gestion del menu semanal se hace de forma manual, con un coste "
        "de tiempo estimado de <b>3-5 horas semanales por cocinero</b> y un desperdicio alimentario "
        "medio del <b>12-15% de la compra</b>.", S["body"]))
    story.append(sp(0.25))
    story.append(kpi_row([
        ("279.000", "restaurantes\nen Espana"),
        ("50.000+", "con menu\ndel dia"),
        ("43.500M EUR", "facturacion\nsector"),
        ("<5%", "usan software\ncon IA"),
    ]))
    story.append(sp(0.35))

    story.append(Paragraph("El Problema Real del Chef", S["h2"]))
    story.append(tabla(
        [
            ["Dolor", "Impacto", "Consecuencia"],
            ["Tiempo perdido", "3-5h/semana",
             "Planificar menu, calcular cantidades y gestionar desperdicio de forma completamente manual"],
            ["Food cost sin control", "Error +-8%",
             "Sin escandallo digital el coste real se desconoce hasta el cierre mensual"],
            ["Rotacion improvisada", "Repeticion",
             "Sin historial el chef repite proteinas y preparaciones sin darse cuenta"],
            ["Riesgo alergenos", "Multa hasta 60.000 EUR",
             "Reglamento UE 1169/2011: obligacion de declarar los 14 alergenos principales"],
            ["Desperdicio alimentario", "12-15%",
             "Ingredientes caducados por falta de gestion equivalen a perdida directa de margen"],
        ],
        [3 * cm, 2.8 * cm, 11.2 * cm], header_bg=ROJO))
    story.append(sp(0.35))

    story.append(Paragraph("Propuesta de Valor ChefMenu AI", S["h2"]))
    story.append(Paragraph(
        "ChefMenu AI es el <b>primer asistente de cocina potenciado por IA</b> que resuelve los cinco "
        "dolores simultaneamente: genera el menu optimo en 30 segundos, controla el food cost en tiempo "
        "real, gestiona la rotacion automatica, garantiza el cumplimiento de alergenos y convierte las "
        "sobras en platos creativos.", S["body"]))
    story.append(sp(0.2))
    story.append(caja(
        "Ventaja competitiva clave: ningun software actual de hosteleria usa IA conversacional para "
        "generar menus. Los competidores son gestores de recetas estaticos. ChefMenu AI es un chef "
        "virtual que piensa, propone y optimiza.",
        bg=colors.HexColor("#1a3a1a"), border=VERDE_M))
    story.append(sp(0.35))

    story.append(Paragraph("Proyeccion de Ingresos", S["h2"]))
    story.append(tabla(
        [
            ["Escenario", "Mes 6", "Mes 12", "Mes 18", "Mes 24", "MRR Mes 24"],
            ["Conservador", "20 clientes", "150 clientes", "300 clientes", "500 clientes", "20.000 EUR/mes"],
            ["Realista",    "40 clientes", "300 clientes", "600 clientes", "1.000 clientes", "42.000 EUR/mes"],
            ["Optimista",   "80 clientes", "500 clientes", "1.200 clientes", "2.500 clientes", "110.000 EUR/mes"],
        ],
        [3.4 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 3.6 * cm],
        row_colors=[(2, colors.HexColor("#1b3a1b"))]))

    # ═══ 02 PLATAFORMA ═══════════════════════════════════════════════════════
    story += seccion("02", "DECISION DE PLATAFORMA")

    story.append(Paragraph("Comparativa de Opciones", S["h2"]))
    story.append(tabla(
        [
            ["Plataforma", "TTM", "Coste dev.", "UX movil", "Distribucion", "Fase"],
            ["Web App SaaS (actual)", "0 meses", "Bajo", "Media", "URL directa", "FASE 1"],
            ["PWA", "2 meses", "Bajo-Medio", "Alta", "URL + instalar", "FASE 2"],
            ["App Nativa iOS+Android", "6-9 meses", "Alto", "Maxima", "App Stores", "FASE 3"],
            ["App hibrida React Native", "4-6 meses", "Medio", "Alta", "App Stores", "FASE 3"],
        ],
        [4.5 * cm, 2.2 * cm, 2.2 * cm, 2 * cm, 2.7 * cm, 3.4 * cm],
        row_colors=[(1, colors.HexColor("#1b3a1b")), (2, colors.HexColor("#1a2a1a"))]))
    story.append(sp(0.25))
    story.append(caja(
        "RECOMENDACION: Comenzar como Web SaaS (ya construido) y convertir a PWA en Fase 2 "
        "(unas 2 semanas de trabajo). La PWA permite instalar el icono en el movil del chef, "
        "funcionar offline y acceder a la camara, sin los costes ni tiempos de las app stores. "
        "App nativa solo si se supera los 1.000 restaurantes activos."))
    story.append(sp(0.35))

    story.append(Paragraph("Roadmap Tecnico: de MVP a Produccion", S["h2"]))
    story.append(tabla(
        [
            ["Fase", "Plazo", "Stack", "Accion clave"],
            ["0 - MVP actual",   "Ya listo",    "Streamlit + SQLite + Claude API",
             "Demos con 5 restaurantes piloto"],
            ["1 - SaaS basico",  "2 meses",     "FastAPI + PostgreSQL + React/Next.js",
             "Multi-tenant, login, billing Stripe"],
            ["2 - PWA",          "3 meses",     "Next.js PWA + Service Workers",
             "Instalar en movil, camara nativa, modo offline"],
            ["3 - Escala",       "6 meses",     "AWS/GCP + Redis + CDN + API publica",
             "Integraciones TPV, proveedores, franquicias"],
            ["4 - App nativa",   "9-12 meses",  "React Native o Flutter",
             "App Store / Google Play si MRR > 30.000 EUR"],
        ],
        [2.4 * cm, 2.2 * cm, 5.2 * cm, 7.2 * cm],
        row_colors=[(1, colors.HexColor("#1b3a1b"))]))
    story.append(sp(0.35))

    story.append(Paragraph("Arquitectura Objetivo (Fase 2)", S["h2"]))
    story.append(Paragraph(
        "<b>Frontend:</b> Next.js 14 + Tailwind CSS + PWA manifest. Desplegado en Vercel.<br/>"
        "<b>Backend:</b> FastAPI (Python) en Railway o Render. PostgreSQL con Supabase.<br/>"
        "<b>IA:</b> Claude Sonnet 4.6 via Anthropic API con cache de prompts para reducir costes.<br/>"
        "<b>Auth:</b> Clerk o Supabase Auth con soporte multi-restaurante.<br/>"
        "<b>Billing:</b> Stripe Subscriptions con webhooks para gestion de tiers.<br/>"
        "<b>Storage:</b> Cloudflare R2 para fotos de platos y despensa.<br/>"
        "<b>Coste de infraestructura estimado a 500 clientes:</b> ~350 EUR/mes (incluye Claude API ~200 EUR).",
        S["body"]))

    # ═══ 03 MODELO DE NEGOCIO ════════════════════════════════════════════════
    story += seccion("03", "MODELO DE NEGOCIO Y PRICING")

    story.append(Paragraph("Tiers de Precio", S["h2"]))
    story.append(tabla(
        [
            ["",                       "BASICO",    "PRO",        "CHAIN",       "GOURMET"],
            ["Precio/mes",             "29 EUR",    "59 EUR",     "199 EUR",     "249 EUR"],
            ["Precio/ano (20% dto.)",  "278 EUR",   "566 EUR",    "1.910 EUR",   "2.390 EUR"],
            ["Restaurantes",           "1",         "1",          "Hasta 5",     "1 alta cocina"],
            ["Generaciones IA/mes",    "30",        "Ilimitado",  "Ilimitado",   "Ilimitado"],
            ["Escandallo con merma",   "No",        "No",         "No",          "Si"],
            ["Menu degustacion",       "No",        "No",         "No",          "Si"],
            ["Foto despensa (IA)",     "No",        "Si",         "Si",          "Si"],
            ["Fichas tecnicas PDF",    "5/mes",     "Ilimitado",  "Ilimitado",   "Si Premium"],
            ["Soporte",                "Email",     "Email+Chat", "Account Mgr", "Asesor dedicado"],
        ],
        [4 * cm, 3 * cm, 3 * cm, 3 * cm, 4 * cm]))
    story.append(sp(0.25))
    story.append(caja(
        "Estrategia de entrada: Trial gratuito 14 dias (sin tarjeta) -> onboarding guiado en "
        "10 minutos -> el chef ve el valor en la primera generacion de menu. "
        "Conversion objetivo: 25% de trials a Pro."))
    story.append(sp(0.35))

    story.append(Paragraph("Revenue Model -- Escenario Realista", S["h2"]))
    story.append(tabla(
        [
            ["Mes", "Basico (29 EUR)", "Pro (59 EUR)", "Chain (199 EUR)", "MRR Total", "ARR anual"],
            ["Mes 3",  "20 x 29 = 580 EUR",   "10 x 59 = 590 EUR",
             "2 x 199 = 398 EUR",   "1.568 EUR",  "18.816 EUR"],
            ["Mes 6",  "50 x 29 = 1.450 EUR", "30 x 59 = 1.770 EUR",
             "5 x 199 = 995 EUR",   "4.215 EUR",  "50.580 EUR"],
            ["Mes 12", "120 x 29 = 3.480 EUR","100 x 59 = 5.900 EUR",
             "15 x 199 = 2.985 EUR","12.365 EUR", "148.380 EUR"],
            ["Mes 18", "200 x 29 = 5.800 EUR","200 x 59 = 11.800 EUR",
             "30 x 199 = 5.970 EUR","23.570 EUR", "282.840 EUR"],
            ["Mes 24", "300 x 29 = 8.700 EUR","300 x 59 = 17.700 EUR",
             "50 x 199 = 9.950 EUR","36.350 EUR", "436.200 EUR"],
        ],
        [1.8 * cm, 3.8 * cm, 3.8 * cm, 3.8 * cm, 2.2 * cm, 2.6 * cm],
        row_colors=[(4, colors.HexColor("#1b3a1b"))]))

    # ═══ 04 FASES ════════════════════════════════════════════════════════════
    story += seccion("04", "FASES DE LANZAMIENTO")

    fases = [
        ("FASE 0 -- MVP (Actual)", GRIS_OSC, VERDE,
         "Estado: Completado. 12 modulos funcionales sobre Streamlit + SQLite + Claude API.",
         [
             ("Que ya funciona",
              "Generador menu IA, escandallo, despensa por foto, fichas PDF, briefing, escandalo mode, "
              "rotacion inteligente, importar PDF/TXT, menu degustacion y escandallo con merma"),
             ("Que falta para Beta privada",
              "Login basico, hosting en Render/Railway, dominio propio, formulario de alta piloto"),
             ("Tiempo estimado", "3-4 semanas de trabajo tecnico"),
             ("Coste estimado", "0-200 EUR (hosting basico)"),
         ]),
        ("FASE 1 -- Beta Privada (Mes 0-3)", colors.HexColor("#1a2a1a"), VERDE_M,
         "Objetivo: 15-20 restaurantes piloto sin coste. Validar el producto y generar casos de exito.",
         [
             ("Captacion pilotos",
              "Contacto directo en bares y restaurantes del entorno, grupos de WhatsApp hosteleria, "
              "asociaciones locales y LinkedIn de chefs"),
             ("Que ofrecer",
              "Acceso gratuito 3 meses a cambio de feedback semanal y permiso para usar como caso de exito"),
             ("Metricas de validacion",
              "NPS > 40, retencion semana 4 > 60%, al menos 3 testimonios en video"),
             ("Entregables de fase",
              "Landing page, onboarding por email, formulario de feedback, dashboard interno de uso"),
         ]),
        ("FASE 2 -- Lanzamiento Publico (Mes 3-6)", colors.HexColor("#1a2a35"), AZUL,
         "Objetivo: 150 restaurantes de pago. Lanzamiento apoyado en prueba social y primeros ingresos.",
         [
             ("Canal principal",
              "Redes sociales (TikTok + Instagram) con demos en video del producto en cocinas reales"),
             ("Paid Ads",
              "Meta Ads: 500 EUR/mes segmentado a propietarios y cocineros de restaurantes en Espana"),
             ("PR",
              "Nota de prensa a medios del sector: Hosteltur, Restauracion News, El Confidencial Gastro"),
             ("Precio lanzamiento",
              "Oferta early adopter: Pro por 39 EUR/mes los 3 primeros meses para los 100 primeros clientes"),
         ]),
        ("FASE 3 -- Escala (Mes 6-12)", colors.HexColor("#1a1a2a"), DORADO,
         "Objetivo: 500+ restaurantes. Expansion de canales, partnerships y primeras integraciones.",
         [
             ("Partnerships clave",
              "Escuelas de hosteleria (CETT, Le Cordon Bleu), distribuidores alimentarios, proveedores TPV"),
             ("Integraciones",
              "API con TPVs principales (Agora, ICG, Cover Manager), exportacion avanzada a Excel/PDF"),
             ("Expansion geografica",
              "Portugal (mercado similar, mismo stack tecnico) y Latam (Argentina, Mexico) en Fase 4"),
             ("Equipo necesario",
              "1 developer frontend, 1 customer success, 1 comercial (comision pura los primeros 6 meses)"),
         ]),
    ]

    for titulo, bg, border, desc, items in fases:
        rows = [[_pb(k), _p(v)] for k, v in items]
        t = Table(rows, colWidths=[4 * cm, 13 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("BOX", (0, 0), (-1, -1), 1.5, border),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#37474f")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (0, -1), 9),
            ("LEFTPADDING", (1, 0), (1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.append(KeepTogether([
            Paragraph(titulo, S["h2"]),
            Paragraph(desc, S["body"]),
            sp(0.15), t, sp(0.35),
        ]))

    # ═══ 05 VENTAS B2B ═══════════════════════════════════════════════════════
    story += seccion("05", "ESTRATEGIA DE VENTAS B2B")

    story.append(Paragraph("Quien Toma la Decision de Compra", S["h2"]))
    story.append(tabla(
        [
            ["Perfil", "Rol", "Motivacion principal", "Canal de llegada"],
            ["Chef / Jefe de cocina", "Usuario + Influencer",
             "Ahorro de tiempo, reconocimiento profesional", "TikTok, Instagram, boca a boca"],
            ["Propietario del restaurante", "Decision maker",
             "Reducir costes, control del negocio", "LinkedIn, Google, referidos"],
            ["Gerente / Director F&B", "Comprador en cadenas",
             "ROI medible, integracion de sistemas", "LinkedIn, ferias, consultoria"],
            ["Asesor gastronomico", "Canal de distribucion",
             "Herramienta para sus propios clientes", "LinkedIn, webinars, partnership"],
        ],
        [3.5 * cm, 3 * cm, 5.5 * cm, 5 * cm]))
    story.append(sp(0.35))

    story.append(Paragraph("Demo de 10 Minutos que Cierra", S["h2"]))
    story.append(tabla(
        [
            ["Minuto", "Bloque", "Guion"],
            ["00:00-01:00", "El gancho",
             "Pregunta: 'Cuanto tiempo tardas en planificar el menu de la semana?' "
             "Deja que responda. Luego: 'Te lo hago en 30 segundos.'"],
            ["01:00-03:00", "Generacion en vivo",
             "Configura menu a 12 EUR, 3 primeros y 3 segundos. Pulsa generar. El chef ve "
             "aparecer el menu con food cost, opcion sin gluten y vegana incluidas."],
            ["03:00-05:00", "Foto de la nevera",
             "Saca el movil, haz foto a la nevera o despensa. Claude identifica ingredientes. "
             "'Esto lo hace solo en tu cocina.'"],
            ["05:00-07:00", "Briefing del dia",
             "Muestra el briefing con mise en place calculado para 50 cubiertos. "
             "'Esto es lo que le das a tu equipo cada manana.'"],
            ["07:00-09:00", "Ficha tecnica PDF",
             "Genera la ficha de un plato: ingredientes, pasos, alergenos, PVP recomendado, QR. "
             "Imprimible para la cocina."],
            ["09:00-10:00", "El cierre",
             "'Cuanto vale para ti ahorrar 4 horas a la semana y tener el food cost bajo control? "
             "Son 59 EUR/mes. Empezamos con 14 dias gratis.'"],
        ],
        [2.2 * cm, 2.6 * cm, 12.2 * cm], header_bg=AZUL))
    story.append(sp(0.35))

    story.append(Paragraph("Objeciones y Respuestas", S["h2"]))
    story.append(tabla(
        [
            ["Objecion", "Respuesta"],
            ["Ya uso Excel",
             "Excel no te avisa que el lomo esta por encima del food cost objetivo ni te genera "
             "el mise en place para 60 cubiertos. Pruebalo 14 dias y compara."],
            ["Es caro",
             "Cuanto vale una hora de tu tiempo? Si te ahorra 4 horas a la semana, a 15 EUR/hora "
             "son 240 EUR/mes que te ahorras. Pagas 59, ganas 180."],
            ["No soy tecnologico",
             "En 10 minutos te configuro yo el primer menu. Si en 14 dias no lo usas solo, "
             "te devuelvo el dinero sin preguntas."],
            ["Ya tenemos un sistema",
             "Tu sistema actual genera menus con IA, detecta alergenos automaticamente y convierte "
             "las sobras de ayer en platos de hoy? Esto es diferente."],
            ["Lo decido con mi jefe",
             "Perfecto. Cuando os veo a los dos? Tengo una demo de 10 minutos preparada. "
             "Esta semana o la siguiente?"],
        ],
        [4 * cm, 13 * cm], header_bg=ROJO))

    # ═══ 06 MARKETING DIGITAL ════════════════════════════════════════════════
    story += seccion("06", "ESTRATEGIA DE MARKETING DIGITAL")

    story.append(Paragraph("Canales Prioritarios", S["h2"]))
    story.append(tabla(
        [
            ["Canal", "Audiencia objetivo", "Tipo de contenido", "Frecuencia", "Objetivo"],
            ["TikTok / Reels", "Chefs jovenes 25-40",
             "Demo en cocina real, before/after, humor hosteleria",
             "1/dia", "Viralidad + brand awareness"],
            ["Instagram", "Chefs y propietarios 30-50",
             "Casos de exito, infografias food cost, stories Q&A",
             "1/dia + 3 stories", "Comunidad + leads"],
            ["YouTube", "Formacion hosteleria",
             "Tutoriales completos (10-15 min), testimonios reales",
             "1/semana", "SEO + autoridad"],
            ["LinkedIn", "Propietarios, directores F&B",
             "Datos de mercado, casos de negocio, articulos del sector",
             "3/semana", "B2B decision makers"],
            ["Google (SEO+SEM)", "Busqueda activa",
             "Blog hosteleria, landing pages especificas",
             "Continuo", "Captacion organica"],
        ],
        [2.5 * cm, 3 * cm, 5 * cm, 2.5 * cm, 4 * cm]))
    story.append(sp(0.35))

    story.append(Paragraph("Paid Ads -- Plan Detallado", S["h2"]))
    story.append(tabla(
        [
            ["Plataforma", "Presupuesto/mes", "Formato", "Segmentacion", "KPI objetivo"],
            ["Meta Ads Fase 1", "300 EUR/mes",
             "Video 15-30s + Lead Ads",
             "Espana, 28-55 anos. Intereses: hosteleria, cocina profesional, gestion restaurante",
             "CPL < 15 EUR, 20+ leads/mes"],
            ["Meta Ads Fase 2", "800 EUR/mes",
             "Video + Carrusel + Retargeting",
             "Lookalike de usuarios activos + retargeting web",
             "CPL < 10 EUR, ROAS > 3"],
            ["Google Ads", "400 EUR/mes",
             "Search + Display",
             "Keywords: 'software menu restaurante', 'escandallo restaurante', 'control food cost'",
             "CPC < 2 EUR, CTR > 4%"],
            ["TikTok Ads", "200 EUR/mes",
             "Spark Ads (amplificar posts organicos)",
             "Chefs, hosteleria, 22-45 anos",
             "CPV < 0,05 EUR, reach maximo"],
        ],
        [2.8 * cm, 2.4 * cm, 2.8 * cm, 5 * cm, 4 * cm]))
    story.append(sp(0.35))

    story.append(Paragraph("SEO -- Palabras Clave Objetivo", S["h2"]))
    story.append(tabla(
        [
            ["Keyword", "Vol. busqueda est.", "Dificultad", "Tipo de contenido"],
            ["software menu restaurante", "1.200/mes", "Media",
             "Landing page + articulo comparativa"],
            ["planificar menu semanal restaurante", "800/mes", "Baja",
             "Articulo blog + guia descargable"],
            ["escandallo cocina", "600/mes", "Baja",
             "Tutorial + herramienta gratuita"],
            ["control food cost restaurante", "900/mes", "Media",
             "Articulo blog + calculadora gratuita"],
            ["gestion cocina profesional", "700/mes", "Media",
             "Landing + casos de exito"],
            ["alergenos carta restaurante", "1.100/mes", "Media-Alta",
             "Guia legal + herramienta de gestion"],
        ],
        [5.5 * cm, 2.8 * cm, 2.4 * cm, 6.3 * cm]))

    # ═══ 07 PLAN 90 DIAS ═════════════════════════════════════════════════════
    story += seccion("07", "PLAN DE ACCION -- PRIMEROS 90 DIAS")

    semanas = [
        ("Semana 1-2", "PREPARACION TECNICA",
         "Migrar de Streamlit a hosting publico (Render/Railway). Anadir login basico con Google. "
         "Dominio propio. Formulario de registro beta."),
        ("Semana 3-4", "CAPTACION PILOTOS",
         "Contactar 30-40 restaurantes locales (visita presencial + WhatsApp). "
         "Ofrecer acceso gratuito 3 meses a cambio de feedback. Objetivo: 15 restaurantes activos."),
        ("Semana 5-6", "PRIMER CONTENIDO",
         "Crear cuentas TikTok, Instagram y LinkedIn. "
         "Grabar 10 videos demo en cocinas de pilotos (con permiso). Publicar 3 por semana."),
        ("Semana 7-8", "FEEDBACK Y MEJORA",
         "Entrevistar a los 15 pilotos (30 min cada uno). Priorizar las 3 funciones mas pedidas. "
         "Implementar quick wins. Recoger primer NPS y testimonios en video."),
        ("Semana 9-10", "LANDING + BILLING",
         "Landing page profesional con casos de exito reales. Integrar Stripe (mensual/anual). "
         "Sistema de trial 14 dias automatico. Email de onboarding en 5 pasos."),
        ("Semana 11-12", "LANZAMIENTO PUBLICO SOFT",
         "Publicar nota de prensa en Hosteltur y Restauracion News. "
         "Activar Meta Ads 300 EUR/mes. Oferta early adopter: Pro 39 EUR/mes. "
         "Objetivo: 20-30 restaurantes de pago al final de los 90 dias."),
    ]

    rows = [[_pb(s), _pb(t), _p(d)] for s, t, d in semanas]
    t = Table(rows, colWidths=[2.4 * cm, 3.4 * cm, 11.2 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), GRIS_OSC),
        ("BACKGROUND", (1, 0), (-1, -1), colors.HexColor("#1a2535")),
        ("BOX", (0, 0), (-1, -1), 0.5, VERDE),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#37474f")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(sp(0.3))
    story.append(Paragraph("Hitos Clave de los 90 Dias", S["h2"]))
    story.append(kpi_row([
        ("15", "pilotos activos\n(Semana 4)"),
        ("30", "videos publicados\n(Semana 8)"),
        ("NPS>40", "de pilotos\n(Semana 8)"),
        ("20+", "clientes de pago\n(Semana 12)"),
    ]))

    # ═══ 08 KPIs ═════════════════════════════════════════════════════════════
    story += seccion("08", "METRICAS Y KPIs")

    story.append(Paragraph("North Star Metric", S["h2"]))
    story.append(caja(
        "NORTH STAR: Numero de menus generados con IA por semana. "
        "Esto mide uso real, valor entregado y predice retencion. "
        "Si un restaurante genera su menu con ChefMenu AI cada semana, no se va a dar de baja.",
        bg=colors.HexColor("#1a1500"), border=DORADO))
    story.append(sp(0.35))

    story.append(Paragraph("KPIs por Fase (Framework AARRR)", S["h2"]))
    story.append(tabla(
        [
            ["Fase", "KPI", "Objetivo Mes 3", "Objetivo Mes 6", "Objetivo Mes 12"],
            ["Adquisicion", "Trials iniciados/mes", "30", "100", "300"],
            ["Activacion", "% trials con 1 menu generado", ">70%", ">75%", ">80%"],
            ["Retencion", "Churn mensual", "<8%", "<5%", "<3%"],
            ["Retencion", "DAU/MAU ratio", ">30%", ">40%", ">50%"],
            ["Revenue", "MRR", "1.500 EUR", "4.200 EUR", "12.000 EUR"],
            ["Revenue", "ARPU medio por usuario", "38 EUR/mes", "42 EUR/mes", "45 EUR/mes"],
            ["Referral", "% clientes que refieren", ">10%", ">15%", ">20%"],
        ],
        [3 * cm, 5 * cm, 2.7 * cm, 2.7 * cm, 3.6 * cm],
        row_colors=[(5, colors.HexColor("#1b3a1b"))]))
    story.append(sp(0.35))

    story.append(Paragraph("Estrategias de Retencion", S["h2"]))
    story.append(tabla(
        [
            ["Palanca", "Accion concreta", "Impacto esperado"],
            ["Email onboarding",
             "5 emails en 14 dias mostrando una funcion nueva cada dia",
             "Activacion +20%"],
            ["Notificacion semanal",
             "Es lunes, ya tienes el menu de esta semana? -- push/email cada lunes",
             "Uso habitual +35%"],
            ["Score de uso",
             "Dashboard interno: alertar si un usuario no entra en 7 dias -> llamada proactiva",
             "Churn -40%"],
            ["Comunidad",
             "Grupo WhatsApp/Telegram Chefs ChefMenu AI -- recetas, trucos, networking",
             "LTV +60%"],
            ["Caso de exito mensual",
             "Destacar un restaurante cliente con sus resultados reales cada mes",
             "Referral +25%"],
        ],
        [3 * cm, 9 * cm, 5 * cm]))

    # ═══ 09 INVERSION Y ROI ══════════════════════════════════════════════════
    story += seccion("09", "INVERSION NECESARIA Y ROI")

    story.append(Paragraph("Presupuesto por Fase", S["h2"]))
    story.append(tabla(
        [
            ["Partida", "Fase 0-1\n(0-3 meses)", "Fase 2\n(3-6 meses)", "Fase 3\n(6-12 meses)", "Total 12 m."],
            ["Desarrollo tecnico",          "2.000 EUR", "5.000 EUR", "8.000 EUR",  "15.000 EUR"],
            ["Hosting e infraestructura",   "100 EUR",   "300 EUR",   "600 EUR",    "1.000 EUR"],
            ["Claude API (IA)",             "50 EUR",    "200 EUR",   "500 EUR",    "750 EUR"],
            ["Diseno (landing, marca)",     "500 EUR",   "1.000 EUR", "0 EUR",      "1.500 EUR"],
            ["Marketing (ads + contenido)", "0 EUR",     "1.500 EUR", "3.000 EUR",  "4.500 EUR"],
            ["Herramientas (CRM, email, analytics)", "100 EUR", "300 EUR", "500 EUR", "900 EUR"],
            ["Miscelanea + imprevistos",    "200 EUR",   "500 EUR",   "1.000 EUR",  "1.700 EUR"],
            ["TOTAL",                       "2.950 EUR", "8.800 EUR", "13.600 EUR", "25.350 EUR"],
        ],
        [5.5 * cm, 2.8 * cm, 2.8 * cm, 2.8 * cm, 3.1 * cm],
        row_colors=[(8, VERDE)]))
    story.append(sp(0.35))

    story.append(Paragraph("Break-Even y ROI", S["h2"]))
    story.append(Paragraph(
        "Con el escenario realista, ChefMenu AI alcanza el break-even operativo en el <b>mes 8-9</b>, "
        "cuando el MRR supera los costes fijos mensuales (~2.800 EUR/mes). "
        "El ROI sobre la inversion total de 25.350 EUR se recupera en el <b>mes 14</b> aproximadamente, "
        "con un ARR proyectado de <b>148.000 EUR al final del ano 1</b>.", S["body"]))
    story.append(sp(0.25))
    story.append(kpi_row([
        ("25.350 EUR", "Inversion total\n12 meses"),
        ("Mes 9", "Break-even\noperativo"),
        ("148k EUR", "ARR proyectado\nano 1"),
        ("485%", "ROI estimado\nano 2"),
    ]))
    story.append(sp(0.35))

    story.append(Paragraph("Opciones de Financiacion", S["h2"]))
    story.append(tabla(
        [
            ["Via", "Importe", "Condiciones", "Recomendacion"],
            ["Bootstrapping propio", "0-5.000 EUR",
             "Sin dilucion, control total",
             "Fase 0-1 (ya cubre el MVP)"],
            ["Kit Digital (subvencion)", "hasta 12.000 EUR",
             "Para restaurantes clientes, no para el producto en si",
             "Vender como solucion Kit Digital a restaurantes"],
            ["ENISA / ICO digitalizacion", "25.000-75.000 EUR",
             "Prestamo participativo, sin avales",
             "Solicitar en Fase 2 con traccion demostrada"],
            ["Business Angel", "50.000-150.000 EUR",
             "5-15% equity",
             "Solo si se quiere acelerar muy rapido"],
            ["Aceleradoras (Lanzadera, Wayra)", "Variable",
             "Mentoring + red de contactos + posible inversion",
             "Aplicar en Fase 2 con MRR > 2.000 EUR"],
        ],
        [3.5 * cm, 2.8 * cm, 5.2 * cm, 5.5 * cm]))
    story.append(sp(0.25))
    story.append(caja(
        "OPORTUNIDAD KIT DIGITAL: El programa Kit Digital del Gobierno espanol subvenciona hasta "
        "12.000 EUR a restaurantes para adoptar soluciones de digitalizacion. ChefMenu AI puede "
        "certificarse como solucion homologada (categoria: Gestion de Procesos) y convertirse en "
        "agente digitalizador, accediendo a miles de restaurantes con compra subvencionada al 100%.",
        bg=colors.HexColor("#1a1500"), border=DORADO))

    # ── CIERRE ────────────────────────────────
    story.append(PageBreak())
    story.append(sp(3))
    story.append(Paragraph("ChefMenu AI", S["ptit"]))
    story.append(sp(0.4))
    story.append(hr(DORADO, 2))
    story.append(sp(0.4))
    story.append(Paragraph("El futuro de la cocina profesional es inteligente.", S["psub"]))
    story.append(sp(0.4))
    story.append(Paragraph(
        "Documento confidencial elaborado para uso interno de MerakIA Agency. "
        "Version 1.0 -- Junio 2025", S["pdesc"]))

    doc.multiBuild(story, canvasmaker=PortadaCanvas)
    print(f"PDF generado: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()
