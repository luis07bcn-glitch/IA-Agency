# -*- coding: utf-8 -*-
"""
Plan de Accion 30 dias — MerakIA · Nicho: Clinicas dentales/estetica
(Vilanova i la Geltru, comarca del Garraf)
Genera plan_accion_merakia_dental_30dias.pdf

Documento de EJECUCION: nicho, dolor cuantificado, oferta, 40 prospectos reales,
sistema de prospeccion, guiones, demo, entrega, calendario dia a dia, metricas y
economia. Carga los prospectos reales de outputs/prospector/prospectos_dental_vng.json
"""
import json
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle,
    Spacer, HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas

ROOT = Path(__file__).parent
PROSPECTOS = ROOT / "outputs" / "prospector" / "prospectos_dental_vng.json"
OUTPUT = ROOT / "plan_accion_merakia_dental_30dias.pdf"

# ── Paleta (consistente con el premortem) ───────────────────────────────────
FONDO   = colors.HexColor("#0a0e1a")
PANEL   = colors.HexColor("#121829")
PANEL2  = colors.HexColor("#0f1422")
LINEA   = colors.HexColor("#26304a")
TEXTO   = colors.HexColor("#cdd6e8")
TENUE   = colors.HexColor("#8a96b0")
BLANCO  = colors.white
ROJO    = colors.HexColor("#ef4444")
AMBAR   = colors.HexColor("#f5a623")
VERDE   = colors.HexColor("#34d399")
CYAN    = colors.HexColor("#2de2e6")
VIOLETA = colors.HexColor("#8b5cf6")
GOLD    = colors.HexColor("#e4b85c")
W = 17 * cm


def _draw_bg(cnv, doc):
    pw, ph = A4
    cnv.saveState()
    cnv.setFillColor(FONDO)
    cnv.rect(0, 0, pw, ph, fill=1, stroke=0)
    cnv.restoreState()


class Cnv(canvas.Canvas):
    def __init__(self, fn, **kw):
        super().__init__(fn, **kw)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._saved)
        for st in self._saved:
            self.__dict__.update(st)
            self._foot(n)
            super().showPage()
        super().save()

    def _foot(self, n):
        pw, ph = A4
        if self._pageNumber <= 1:
            return
        self.saveState()
        self.setFillColor(TENUE)
        self.setFont("Helvetica", 6.5)
        self.drawString(2 * cm, 0.9 * cm,
                        "MerakIA — Plan de Accion 30 dias · Clinicas dentales Vilanova i la Geltru")
        self.drawRightString(pw - 2 * cm, 0.9 * cm, f"{self._pageNumber} / {n}")
        self.setStrokeColor(LINEA)
        self.setLineWidth(0.5)
        self.line(2 * cm, 1.15 * cm, pw - 2 * cm, 1.15 * cm)
        self.restoreState()


def build():
    prospectos = json.loads(PROSPECTOS.read_text(encoding="utf-8"))

    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4,
        topMargin=1.6 * cm, bottomMargin=1.6 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title="MerakIA — Plan de Accion 30 dias (Clinicas dentales Vilanova i la Geltru)",
        author="MerakIA Agency",
    )
    base = getSampleStyleSheet()

    def stl(n, **kw):
        return ParagraphStyle(n, parent=base["Normal"], **kw)

    S = {
        "ptit": stl("ptit", fontSize=28, textColor=BLANCO, fontName="Helvetica-Bold",
                    alignment=TA_CENTER, leading=32),
        "psub": stl("psub", fontSize=12.5, textColor=CYAN, fontName="Helvetica-Bold",
                    alignment=TA_CENTER, spaceAfter=4),
        "pdesc": stl("pdesc", fontSize=9.5, textColor=TENUE, alignment=TA_CENTER, leading=14),
        "h1n": stl("h1n", fontSize=9, textColor=CYAN, fontName="Helvetica-Bold", spaceAfter=2),
        "h1": stl("h1", fontSize=18, textColor=BLANCO, fontName="Helvetica-Bold",
                  spaceAfter=4, leading=22),
        "h2": stl("h2", fontSize=12.5, textColor=BLANCO, fontName="Helvetica-Bold",
                  spaceBefore=9, spaceAfter=4, leading=16),
        "h3": stl("h3", fontSize=10.5, textColor=GOLD, fontName="Helvetica-Bold",
                  spaceBefore=6, spaceAfter=3, leading=14),
        "body": stl("body", fontSize=9, leading=13.5, textColor=TEXTO, alignment=TA_JUSTIFY),
        "bodyl": stl("bodyl", fontSize=9, leading=13.8, textColor=TEXTO),
        "lead": stl("lead", fontSize=10, leading=15, textColor=TEXTO, alignment=TA_JUSTIFY),
        "tc": stl("tc", fontSize=8, leading=11.5, textColor=TEXTO),
        "tcb": stl("tcb", fontSize=8, leading=11.5, textColor=BLANCO, fontName="Helvetica-Bold"),
        "tch": stl("tch", fontSize=8, leading=11, textColor=BLANCO, fontName="Helvetica-Bold"),
        "tcs": stl("tcs", fontSize=6.8, leading=8.5, textColor=TEXTO),
        "tcsb": stl("tcsb", fontSize=6.8, leading=8.5, textColor=BLANCO, fontName="Helvetica-Bold"),
        "tcsh": stl("tcsh", fontSize=6.8, leading=8.5, textColor=BLANCO, fontName="Helvetica-Bold",
                    alignment=TA_CENTER),
        "tcsc": stl("tcsc", fontSize=6.8, leading=8.5, textColor=TEXTO, alignment=TA_CENTER),
        "kpi": stl("kpi", fontSize=18, textColor=CYAN, fontName="Helvetica-Bold",
                   alignment=TA_CENTER),
        "kpil": stl("kpil", fontSize=7, textColor=TENUE, alignment=TA_CENTER, leading=9),
        "quote": stl("quote", fontSize=12, leading=16, textColor=BLANCO,
                     fontName="Helvetica-Bold", alignment=TA_CENTER),
        "mini": stl("mini", fontSize=7.5, textColor=TENUE, leading=10, alignment=TA_CENTER),
        "mono": stl("mono", fontSize=8.5, leading=13, textColor=colors.HexColor("#a9f0f2"),
                    fontName="Courier"),
    }

    def sp(h=0.3):
        return Spacer(1, h * cm)

    def hr(c=LINEA, t=1):
        return HRFlowable(width="100%", thickness=t, color=c, spaceAfter=4)

    def seccion(num, tit):
        return [PageBreak(), Paragraph(f"// {num}", S["h1n"]),
                Paragraph(tit, S["h1"]), hr(CYAN, 2), sp(0.2)]

    def tabla(data, widths, header_bg=PANEL, head_color=CYAN, fs="tc"):
        wrapped = []
        for ri, row in enumerate(data):
            nr = []
            for cell in row:
                if isinstance(cell, (Table, Paragraph)):
                    nr.append(cell)
                elif ri == 0:
                    nr.append(Paragraph(str(cell), S["tch"]))
                else:
                    nr.append(Paragraph(str(cell), S[fs]))
            wrapped.append(nr)
        t = Table(wrapped, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), header_bg),
            ("TEXTCOLOR", (0, 0), (-1, 0), head_color),
            ("GRID", (0, 0), (-1, -1), 0.4, LINEA),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PANEL2, PANEL]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        return t

    def caja(txt, border=CYAN, bg=PANEL, s="body"):
        t = Table([[Paragraph(txt, S[s])]], colWidths=[W])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("BOX", (0, 0), (-1, -1), 1.2, border),
            ("LEFTPADDING", (0, 0), (-1, -1), 11),
            ("RIGHTPADDING", (0, 0), (-1, -1), 11),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ]))
        return t

    def kpi_row(kpis, border=CYAN):
        w = W / len(kpis)
        data = [[Paragraph(v, S["kpi"]) for v, _ in kpis],
                [Paragraph(l.replace("\n", "<br/>"), S["kpil"]) for _, l in kpis]]
        t = Table(data, colWidths=[w] * len(kpis))
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PANEL),
            ("BOX", (0, 0), (-1, -1), 1, border),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, LINEA),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return t

    story = []

    # ════════ PORTADA ════════
    story.append(sp(2.0))
    story.append(Paragraph("PLAN DE ACCIÓN · 30 DÍAS", S["psub"]))
    story.append(sp(0.15))
    story.append(Paragraph("De proyecto a", S["ptit"]))
    story.append(Paragraph("primer cliente que paga", S["ptit"]))
    story.append(sp(0.35))
    story.append(hr(CYAN, 2.5))
    story.append(sp(0.25))
    story.append(Paragraph(
        "MerakIA · Agencia de IA para pymes. Un nicho, un servicio, un objetivo: "
        "cerrar el primer cliente de una clínica dental en Vilanova i la Geltrú en 30 días.",
        S["pdesc"]))
    story.append(sp(0.9))
    port = [
        ["Proyecto elegido", "MerakIA — Agencia de IA para pymes"],
        ["Nicho de ataque", "Clínicas dentales y estética · Vilanova i la Geltrú (Garraf)"],
        ["Servicio estrella", "Agente IA anti no-show + recepción 24/7 por WhatsApp"],
        ["Activos que ya tienes", "ProspectorIA (diagnóstico) + agente-whatsapp-citas (entrega)"],
        ["Prospectos en este plan", f"{len(prospectos)} clínicas reales con teléfono y web"],
        ["Objetivo a 30 días", "1 cliente ancla cerrado + 2-3 reuniones avanzadas"],
    ]
    tp = Table([[Paragraph(r[0], S["tcb"]), Paragraph(r[1], S["tc"])] for r in port],
               colWidths=[4.6 * cm, 12.4 * cm])
    tp.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), PANEL),
        ("BACKGROUND", (1, 0), (1, -1), PANEL2),
        ("TEXTCOLOR", (0, 0), (0, -1), CYAN),
        ("GRID", (0, 0), (-1, -1), 0.5, LINEA),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(tp)
    story.append(sp(0.9))
    story.append(caja(
        "<b>La regla de oro de estos 30 días:</b> el 80% de tu tiempo va a hablar con "
        "clínicas (llamar, visitar, reunir, proponer). El 20% a producto. Si una semana "
        "no tuviste conversaciones de venta, fue una semana perdida — por muy productiva "
        "que se sintiera.", border=GOLD, bg=PANEL, s="lead"))

    # ════════ 01 TESIS ════════
    story += seccion("01", "La tesis de ataque")
    story.append(Paragraph(
        "Tienes el motor de prospección (ProspectorIA) y el producto de entrega "
        "(agente-whatsapp-citas) ya construidos. Lo único que falta es lo más importante "
        "y lo que has estado evitando: <b>la acción comercial</b>. Este plan elimina toda "
        "la ambigüedad para que en 30 días pases de cero a tu primer cliente que paga.", S["lead"]))
    story.append(sp(0.3))
    story.append(Paragraph("Las 4 decisiones que ya están tomadas", S["h2"]))
    story.append(tabla([
        ["Decisión", "Elección", "Por qué"],
        ["UN nicho", "Clínicas dentales/estética en Vilanova i la Geltrú",
         "Ticket alto (1.500-3.500€/mes), dolor cuantificable, ROI visible el mes 1. Mercado local que puedes visitar en persona."],
        ["UN servicio", "Agente IA anti no-show + recepción 24/7",
         "El de ROI más fácil de demostrar: las ausencias son dinero perdido medible HOY."],
        ["UN objetivo", "1 cliente ancla en 30 días",
         "No 10 clientes. Uno, bien entregado, que te dé el caso de éxito que rompe el círculo."],
        ["UNA métrica", "Nº de conversaciones de venta / semana",
         "Lo único que mueve la aguja. Todo lo demás (features, web) es secundario este mes."],
    ], [2.6 * cm, 5.4 * cm, 9.0 * cm]))
    story.append(sp(0.3))
    story.append(Paragraph("Por qué el cliente ancla lo cambia todo", S["h3"]))
    story.append(Paragraph(
        "El premortem identificó que el fallo más probable de la agencia es \"construir sin vender\" "
        "y la falta de prueba social. El cliente ancla ataca ambos: te obliga a vender de verdad y "
        "te da el primer caso de éxito real (con métricas y testimonio). Con un caso, la segunda "
        "venta cuesta la mitad; con tres, empieza el boca a boca. Sin el primero, no hay nada. "
        "Por eso el objetivo de 30 días no es facturar mucho — es <b>romper el cero</b>.", S["body"]))

    # ════════ 02 NICHO Y DOLOR ════════
    story += seccion("02", "El nicho: radiografía del dolor")
    story.append(Paragraph(
        "Una clínica dental es un negocio de agenda: si una silla está vacía una hora que "
        "debería estar ocupada, ese dinero no se recupera nunca. Ahí vive tu oferta. Estos son "
        "los cinco dolores, traducidos a euros — el lenguaje del dueño de la clínica.", S["body"]))
    story.append(sp(0.25))
    story.append(tabla([
        ["Dolor", "Dato del sector", "Traducción a dinero"],
        ["Ausencias (no-shows)", "20-30% de la capacidad productiva se pierde por citas no confirmadas",
         "Una agenda de 30 citas/día con 20% de no-show = ~130 huecos/mes. A 80€/cita = >10.000€/mes en sillas vacías."],
        ["Teléfono desbordado", "40% de las llamadas entran cuando no hay nadie para cogerlas",
         "Cada llamada perdida puede ser un paciente nuevo (LTV de cientos a miles de €) que llama a la siguiente clínica."],
        ["Lead lento", "El lead medio tarda +14h en ser contactado",
         "La probabilidad de cerrar un lead cae drásticamente pasados los primeros minutos. Pagan publicidad y la desperdician."],
        ["Recordatorios manuales", "2-3h diarias del personal en confirmar citas a mano",
         "Salario administrativo quemado en una tarea 100% automatizable. Y aún así se escapan no-shows."],
        ["Reseñas sin gestionar", "No piden valoraciones de forma sistemática",
         "Un 4.4 frente a un 4.8 en Google = menos pacientes nuevos cada mes. Reputación = captación."],
    ], [3.0 * cm, 6.0 * cm, 8.0 * cm], head_color=ROJO))
    story.append(sp(0.3))
    story.append(caja(
        "<b>El gancho de una frase:</b> «¿Sabes cuánto dinero perdiste el mes pasado en sillas "
        "vacías por pacientes que no avisaron? Te lo calculo gratis, y te enseño cómo recuperar "
        "la mitad con un sistema que confirma y reactiva citas solo.»", border=CYAN, bg=PANEL, s="lead"))

    # ════════ 03 OFERTA ════════
    story += seccion("03", "La oferta: empaquetado y precio")
    story.append(Paragraph(
        "Nada de \"hacemos de todo\". Una oferta única, clara, con precio cerrado y resultado "
        "prometido. Productizada para que puedas venderla y entregarla sin reinventar nada cada vez.", S["body"]))
    story.append(sp(0.2))
    story.append(Paragraph("Producto: «Agenda Llena» — el guardián de tu agenda", S["h2"]))
    story.append(tabla([
        ["Incluye", "Qué hace"],
        ["Agente WhatsApp anti no-show",
         "Confirma cada cita automáticamente, reconfirma 24h antes y reactiva al paciente si cancela. "
         "(Lo entregas con tu agente-whatsapp-citas, ya construido.)"],
        ["Recepción IA 24/7",
         "Responde dudas frecuentes, horarios y disponibilidad por WhatsApp fuera de horario; "
         "capta al paciente que llama cuando la clínica está cerrada."],
        ["Recordatorios + reactivación",
         "Secuencias automáticas de recordatorio y recuperación de pacientes inactivos."],
        ["Informe mensual de resultados",
         "Reporte claro: no-shows evitados, citas reactivadas, € recuperados. La prueba del ROI cada mes."],
    ], [4.5 * cm, 12.5 * cm], head_color=VERDE))
    story.append(sp(0.3))
    story.append(Paragraph("Precio (ancla al ROI, no al coste)", S["h2"]))
    story.append(kpi_row([
        ("590€", "implantación\n(pago único)"),
        ("390€/mes", "cuota mensual\nsin permanencia"),
        (">10x", "ROI típico\nvs. no-shows"),
        ("14 días", "garantía\no no pagas"),
    ]))
    story.append(sp(0.25))
    story.append(Paragraph(
        "<b>Cómo defender el precio:</b> si la clínica pierde más de 5.000€/mes en sillas vacías y tu "
        "sistema recupera solo el 40%, son 2.000€/mes recuperados por una cuota de 390€. El precio no "
        "se discute cuando lo anclas a lo que ya está perdiendo. <b>Reducción de riesgo:</b> sin "
        "permanencia los primeros meses y garantía de 14 días — \"si no ves resultados, no sigues "
        "pagando\". Esto desarma la objeción principal.", S["body"]))
    story.append(sp(0.2))
    story.append(caja(
        "<b>Oferta especial para el CLIENTE ANCLA (los 1-2 primeros):</b> implantación gratis y "
        "1 mes sin coste, a cambio de (1) un testimonio en vídeo y (2) permiso para usar sus "
        "resultados como caso de éxito. No regalas tu trabajo: compras tu primer caso de éxito, "
        "que vale más que esos 980€.", border=GOLD, bg=colors.HexColor("#1a1500"), s="lead"))

    # ════════ 04 LISTA 40 PROSPECTOS ════════
    story += seccion("04", "Tus 40 prospectos reales")
    sin_web = sum(1 for p in prospectos if not p["web"])
    bajo = sum(1 for p in prospectos if p["rating"] and p["rating"] < 4.5)
    story.append(Paragraph(
        f"Extraídos en vivo de Google Places para clínicas dentales y de estética en Vilanova i la "
        f"Geltrú, ordenados por <b>score de oportunidad</b> (mayor = más señales de dolor digital = mejor "
        f"punto de entrada). De los {len(prospectos)}: <b>{sin_web} sin web propia</b> y "
        f"<b>{bajo} con rating mejorable (&lt;4.5)</b>. La lista completa con direcciones, enlaces de "
        "Maps y señales detalladas está en <b>outputs/prospector/prospectos_dental_vng.csv</b>.", S["body"]))
    story.append(sp(0.2))
    story.append(caja(
        "<b>Cómo trabajar la lista:</b> empieza por los 10 primeros (mayor score). Antes de llamar a "
        "cada uno, pásalo por ProspectorIA para tener su scorecard, pérdida en €/mes y propuesta "
        "personalizada — llegas a la conversación con un diagnóstico, no con un pitch genérico.",
        border=CYAN, bg=PANEL, s="bodyl"))
    story.append(sp(0.25))

    # tabla de prospectos
    head = ["#", "Clínica", "Teléfono", "Val.", "Web", "Opt", "Señal de entrada"]
    rows = [[Paragraph(h, S["tcsh"]) for h in head]]
    for i, p in enumerate(prospectos, 1):
        rating = p["rating"]
        val = f"{rating}·{p['resenas']}" if rating is not None else f"-·{p['resenas']}"
        if not p["web"]:
            web_html = '<font color="#ef4444">NO</font>'
        else:
            web_html = '<font color="#34d399">Sí</font>'
        rows.append([
            Paragraph(str(i), S["tcsc"]),
            Paragraph(p["nombre"], S["tcsb"]),
            Paragraph(p["telefono"] or "-", S["tcs"]),
            Paragraph(val, S["tcsc"]),
            Paragraph(web_html, S["tcsc"]),
            Paragraph(str(p["score_oportunidad"]), S["tcsc"]),
            Paragraph(p["motivos"], S["tcs"]),
        ])
    tw = [0.7 * cm, 4.7 * cm, 2.3 * cm, 1.5 * cm, 0.9 * cm, 0.9 * cm, 6.0 * cm]
    t = Table(rows, colWidths=tw, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), PANEL),
        ("GRID", (0, 0), (-1, -1), 0.3, LINEA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PANEL2, PANEL]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]
    # resaltar top-10
    for r in range(1, min(11, len(rows))):
        style.append(("BACKGROUND", (0, r), (0, r), CYAN))
        style.append(("TEXTCOLOR", (0, r), (0, r), FONDO))
    t.setStyle(TableStyle(style))
    story.append(t)
    story.append(sp(0.15))
    story.append(Paragraph(
        "Val. = rating · nº reseñas · Opt = score de oportunidad (0-100). "
        "Los 10 primeros (índice en cian) son tu lista de ataque de la Semana 1-2.", S["mini"]))

    # ════════ 05 SISTEMA DE PROSPECCIÓN ════════
    story += seccion("05", "El sistema de prospección y contacto")
    story.append(Paragraph(
        "No improvises cada contacto. Una cadencia de varios toques en 14 días multiplica la "
        "respuesta frente a un único intento. Combina canales: llamada, WhatsApp y email.", S["body"]))
    story.append(sp(0.2))
    story.append(Paragraph("Cadencia de 5 toques en 14 días", S["h2"]))
    story.append(tabla([
        ["Día", "Canal", "Acción"],
        ["1", "Llamada", "Llamada en frío corta: gancho del dinero perdido + pedir reunión de 15 min (no vender por teléfono)."],
        ["1", "WhatsApp", "Si no contesta: mensaje con el gancho + propuesta de diagnóstico gratis. Personalizado con su nombre."],
        ["4", "Email", "Email con el cálculo de pérdida estimada por no-shows + caso/ejemplo. Asunto corto y directo."],
        ["8", "Llamada", "Segunda llamada referenciando el mensaje anterior. Insistir en el diagnóstico gratuito, sin compromiso."],
        ["14", "WhatsApp", "Cierre de cadencia: \"última vez que te escribo por esto\" + valor. La urgencia/escasez reactiva respuestas."],
    ], [1.2 * cm, 2.3 * cm, 13.5 * cm]))
    story.append(sp(0.25))
    story.append(Paragraph("Guion de llamada en frío (30-45 segundos)", S["h3"]))
    story.append(caja(
        "«Hola, ¿hablo con la responsable de [Clínica]? Soy [Nombre], de MerakIA. Trabajo con "
        "clínicas dentales de Vilanova i la Geltrú ayudándolas a recuperar el dinero que pierden en citas "
        "que no se presentan. No te quiero vender nada por teléfono: te ofrezco calcularte gratis "
        "cuánto estás perdiendo al mes en sillas vacías y enseñarte cómo recuperar la mitad. "
        "Son 15 minutos. ¿Te va bien el [día] por la mañana o prefieres por la tarde?»",
        border=VERDE, bg=PANEL, s="bodyl"))
    story.append(sp(0.15))
    story.append(Paragraph("Primer WhatsApp / email", S["h3"]))
    story.append(caja(
        "«Hola [Nombre], soy [tu nombre] de MerakIA. Ayudo a clínicas dentales de Vilanova i la Geltrú a "
        "reducir las ausencias y a no perder pacientes que llaman fuera de horario. He hecho un "
        "pequeño análisis de [Clínica] y veo margen claro de mejora. ¿Te mando un diagnóstico "
        "gratuito de cuánto podrías estar recuperando cada mes? Sin compromiso.»",
        border=VERDE, bg=PANEL, s="bodyl"))
    story.append(sp(0.2))
    story.append(Paragraph(
        "<b>Atajo:</b> ProspectorIA ya genera estos textos personalizados (email, WhatsApp, script y "
        "una secuencia de 5 toques) con los datos reales de cada clínica. Úsalo para no escribir "
        "desde cero cada vez.", S["body"]))

    # ════════ 06 LA DEMO QUE CIERRA ════════
    story += seccion("06", "La reunión que cierra")
    story.append(Paragraph(
        "La reunión es un <b>diagnóstico</b>, no un pitch. Llegas con datos de su clínica y dejas que "
        "los números vendan. Estructura de 15-20 minutos:", S["body"]))
    story.append(sp(0.2))
    story.append(tabla([
        ["Min", "Bloque", "Qué haces"],
        ["0-3", "El espejo",
         "Le enseñas su scorecard de ProspectorIA: su rating, su presencia, cómo está vs. la media de "
         "clínicas de la zona. Reconoce su realidad antes de proponer nada."],
        ["3-8", "El dinero perdido",
         "Le muestras la estimación de € que pierde al mes en no-shows y llamadas no atendidas. "
         "Este es el momento que cambia la conversación: ya no hablas de IA, hablas de SU dinero."],
        ["8-13", "La solución en vivo",
         "Demo del agente WhatsApp: una cita real se confirma sola, un paciente pregunta a las 23h y "
         "recibe respuesta. \"Esto pasa en tu clínica desde el primer día.\""],
        ["13-18", "La oferta + cierre",
         "Precio anclado a lo que pierde, garantía de 14 días, sin permanencia. \"¿Lo probamos un mes "
         "y lo ves con tus propios números?\" Para el ancla: oferta de implantación gratis."],
    ], [1.5 * cm, 3.0 * cm, 12.5 * cm]))
    story.append(sp(0.25))
    story.append(Paragraph("Objeciones y respuestas", S["h3"]))
    story.append(tabla([
        ["Objeción", "Respuesta"],
        ["\"Ya tenemos recepcionista\"",
         "Perfecto, esto no la sustituye: la libera. Tu recepcionista no puede contestar a las 23h ni "
         "confirmar 80 citas a mano sin que se escape ninguna. El agente hace lo repetitivo; ella, lo humano."],
        ["\"Es caro\"",
         "¿Cuánto perdiste el mes pasado en citas que no vinieron? Si recuperamos solo el 40%, esto se "
         "paga solo varias veces. Y si no funciona, el mes siguiente no lo pagas."],
        ["\"No somos de tecnología\"",
         "No tienes que tocar nada. Lo configuro yo, funciona sobre el WhatsApp que ya usáis. Tú solo "
         "ves el informe de resultados a fin de mes."],
        ["\"Me lo tengo que pensar\"",
         "Claro. Para que decidas con datos y no con dudas: déjame activarlo 14 días. Si no ves menos "
         "ausencias, lo paramos sin coste. ¿Qué riesgo hay?"],
    ], [4.5 * cm, 12.5 * cm], head_color=AMBAR))

    # ════════ 07 ENTREGA ════════
    story += seccion("07", "Entrega: implementar sin morir")
    story.append(Paragraph(
        "El premortem avisó: la entrega artesanal te satura a los 2-3 clientes. Por eso entregas con "
        "un proceso repetible y con tu producto ya construido, no reinventando cada vez.", S["body"]))
    story.append(sp(0.2))
    story.append(Paragraph("Tu stack de entrega (ya lo tienes)", S["h3"]))
    story.append(tabla([
        ["Pieza", "Para qué"],
        ["agente-whatsapp-citas",
         "El producto núcleo: CRM + agente IA de WhatsApp para citas + recordatorios anti-ausencias. "
         "Es exactamente lo que vende «Agenda Llena». Falta: API key de OpenRouter + YCloud y desplegar por cliente."],
        ["ProspectorIA",
         "Diagnóstico y propuesta personalizada por clínica. Es tu herramienta de venta, no solo de prospección."],
        ["merakia-web",
         "La web pública. Necesita datos de contacto reales (no placeholder) antes de enviar tráfico (ver checklist)."],
    ], [4.3 * cm, 12.7 * cm], head_color=VIOLETA))
    story.append(sp(0.25))
    story.append(Paragraph("Checklist de onboarding repetible (por cliente)", S["h3"]))
    story.append(caja(
        "☐ Alta del cliente y conexión de su número de WhatsApp (YCloud).<br/>"
        "☐ Carga de horarios, tipos de cita y FAQs de la clínica.<br/>"
        "☐ Configuración de las secuencias: confirmación, recordatorio 24h, reactivación.<br/>"
        "☐ Prueba con 5 citas reales antes de activar al 100%.<br/>"
        "☐ Activar monitorización + alerta de caída (si el agente deja de responder, te enteras tú primero).<br/>"
        "☐ Agendar la revisión de resultados a 30 días (renovación + testimonio).",
        border=VIOLETA, bg=PANEL, s="bodyl"))
    story.append(sp(0.2))
    story.append(caja(
        "<b>Regla anti-desastre (del premortem):</b> nunca pongas un agente en producción en una "
        "clínica sin monitorización, alerta de caída y un fallback humano. Un agente que falla un "
        "sábado y pierde citas es el fallo más peligroso de la agencia: destruye el boca a boca del "
        "que dependes.", border=ROJO, bg=colors.HexColor("#1a0f12"), s="bodyl"))

    # ════════ 08 CALENDARIO ════════
    story += seccion("08", "Calendario día a día — 30 días")
    semanas = [
        ("SEMANA 1", "Preparar el terreno y empezar a contactar", CYAN, [
            ("Día 1-2", "Arregla la web: datos de contacto REALES (teléfono, email, formulario que funcione). "
                        "Quita métricas inventadas. Sin esto no envíes a nadie a la web."),
            ("Día 2", "Consigue API key de OpenRouter + YCloud y deja agente-whatsapp-citas listo para desplegar una demo."),
            ("Día 3", "Pasa los 10 primeros prospectos por ProspectorIA: scorecard, pérdida €/mes y textos personalizados."),
            ("Día 4-5", "Primera tanda de contacto (cadencia toque 1): llama + WhatsApp a los 10 primeros. Meta: 3 reuniones agendadas."),
        ]),
        ("SEMANA 2", "Prospección intensiva + primeras reuniones", VERDE, [
            ("Día 8-9", "Toque 2 de la cadencia a los no-contactados + contacta los prospectos 11-25."),
            ("Día 8-12", "Celebra las primeras reuniones-diagnóstico. Usa la estructura de 15-20 min. Lleva su scorecard impreso."),
            ("Día 10", "Prepara una demo en vivo pulida del agente WhatsApp (un número de prueba que confirme y responda)."),
            ("Día 12", "Revisa qué objeciones aparecen y afina el guion. Meta acumulada: 5-6 reuniones, 1-2 propuestas enviadas."),
        ]),
        ("SEMANA 3", "Cerrar el cliente ancla", GOLD, [
            ("Día 15-17", "Seguimiento de propuestas. Ofrece a los 2 más interesados la oferta ANCLA (implantación gratis + 1 mes)."),
            ("Día 17-19", "Cierra el cliente ancla. Firma simple (1 página) y agenda el onboarding."),
            ("Día 19-21", "Arranca la implantación con el checklist. Configura y prueba con citas reales."),
        ]),
        ("SEMANA 4", "Entregar, demostrar y multiplicar", VIOLETA, [
            ("Día 22-25", "Agente en producción en el cliente ancla. Vigila a diario la primera semana."),
            ("Día 25-27", "Primeros resultados: documenta no-shows evitados y citas reactivadas. Pide el testimonio en vídeo."),
            ("Día 28-30", "Convierte el caso en material de venta. Reabre la cadencia con prospectos 26-40 usando el caso real. "
                         "Meta: 2-3 reuniones nuevas calientes para el mes 2."),
        ]),
    ]
    for tit, sub, col, items in semanas:
        head = Table([[Paragraph(f"<b>{tit}</b>", S["tcb"]), Paragraph(sub, S["tcb"])]],
                     colWidths=[3.0 * cm, 14.0 * cm])
        head.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), col),
            ("BACKGROUND", (1, 0), (1, -1), PANEL),
            ("TEXTCOLOR", (0, 0), (0, -1), FONDO),
            ("TEXTCOLOR", (1, 0), (1, -1), BLANCO),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        body_rows = [[Paragraph(d, S["tcb"]), Paragraph(a, S["tc"])] for d, a in items]
        bt = Table(body_rows, colWidths=[2.4 * cm, 14.6 * cm])
        bt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PANEL2),
            ("GRID", (0, 0), (-1, -1), 0.3, LINEA),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("TEXTCOLOR", (0, 0), (0, -1), col),
        ]))
        story.append(KeepTogether([head, bt, sp(0.3)]))

    # ════════ 09 MÉTRICAS ════════
    story += seccion("09", "Métricas y metas")
    story.append(Paragraph(
        "Mide actividad (lo que controlas) y resultado (lo que persigues). Si la actividad está alta y "
        "el resultado no llega, el problema está en el guion o la oferta — no en el esfuerzo.", S["body"]))
    story.append(sp(0.2))
    story.append(tabla([
        ["Métrica", "Tipo", "Meta 30 días"],
        ["Clínicas contactadas (cadencia completa)", "Actividad", "40 (toda la lista)"],
        ["Reuniones-diagnóstico realizadas", "Actividad", "6-8"],
        ["Propuestas enviadas", "Actividad", "4-5"],
        ["Clientes cerrados (incl. ancla)", "Resultado", "1 (mínimo viable)"],
        ["Caso de éxito documentado", "Resultado", "1 (con métricas + vídeo)"],
        ["Conversaciones de venta / semana", "North Star", "≥ 10"],
    ], [7.5 * cm, 3.0 * cm, 6.5 * cm], head_color=CYAN))
    story.append(sp(0.25))
    story.append(caja(
        "<b>Tablero simple:</b> una hoja de cálculo con una fila por clínica y columnas para cada toque "
        "de la cadencia (fecha + resultado), estado (contactado / reunión / propuesta / cerrado / "
        "descartado) y notas. El CRM de ProspectorIA ya hace esto — úsalo y exporta a CSV cada viernes "
        "para ver tu progreso real.", border=CYAN, bg=PANEL, s="bodyl"))

    # ════════ 10 ECONOMÍA ════════
    story += seccion("10", "Economía: precios, proyección y caja")
    story.append(Paragraph("Proyección conservadora (si rompes el cero este mes)", S["h2"]))
    story.append(tabla([
        ["Hito", "Clientes", "MRR", "Setup puntual", "Comentario"],
        ["Mes 1", "1 (ancla, gratis)", "0€", "0€", "El caso de éxito vale más que el dinero ahora."],
        ["Mes 2", "2-3 de pago", "780-1.170€", "1.180-1.770€", "Ya vendes con el caso del ancla en la mano."],
        ["Mes 3", "4-6 de pago", "1.560-2.340€", "1.180-2.360€", "Boca a boca empieza; afinas la entrega."],
        ["Mes 6", "10-15 de pago", "3.900-5.850€", "—", "Punto de plantearte delegar la entrega."],
    ], [2.0 * cm, 3.2 * cm, 3.2 * cm, 3.2 * cm, 5.4 * cm], head_color=VERDE))
    story.append(sp(0.25))
    story.append(Paragraph("Lo que necesitas para arrancar (coste real bajo)", S["h3"]))
    story.append(tabla([
        ["Partida", "Coste", "Nota"],
        ["Google Places API", "0€", "Dentro del crédito gratuito de 200$/mes (ya configurado)."],
        ["Claude API", "~20-50€/mes", "Prospección + agentes. Escala con uso."],
        ["WhatsApp (YCloud) + OpenRouter", "Variable bajo", "Necesario para el agente. Pendiente de dar de alta."],
        ["Hosting agente por cliente", "Bajo", "Railway/Render o similar. Se repercute en el setup."],
        ["Tu tiempo", "El recurso real", "El 80% en venta. Es lo único verdaderamente escaso."],
    ], [5.0 * cm, 3.2 * cm, 8.8 * cm], head_color=AMBAR))
    story.append(sp(0.2))
    story.append(Paragraph(
        "<b>Unit economics a vigilar (del premortem):</b> a 390€/mes con clientes que se quedan, la "
        "economía es sanísima frente a un coste de adquisición casi nulo (prospección propia, sin ads). "
        "El riesgo no es el CAC aquí — es tu tiempo de entrega. Por eso el proceso repetible importa "
        "desde el cliente uno.", S["body"]))

    # ════════ 11 CHECKLIST ════════
    story += seccion("11", "Checklist pre-acción (antes del Día 1)")
    story.append(caja(
        "☐ Web con contacto real y funcional (sin placeholders, sin métricas inventadas).<br/>"
        "☐ agente-whatsapp-citas desplegable como demo (API keys de OpenRouter + YCloud resueltas).<br/>"
        "☐ Los 10 primeros prospectos pasados por ProspectorIA (scorecard + pérdida €/mes + textos).<br/>"
        "☐ Guion de llamada y plantillas de WhatsApp/email impresos o a mano.<br/>"
        "☐ Demo en vivo del agente probada (un número que confirma cita y responde fuera de horario).<br/>"
        "☐ Oferta y precio memorizados, con la versión ANCLA lista para los 2 primeros.<br/>"
        "☐ Tablero de seguimiento abierto (CRM de ProspectorIA o una hoja de cálculo).<br/>"
        "☐ Bloqueado en tu calendario: 80% del tiempo de esta semana para contactar y reunir.",
        border=CYAN, bg=PANEL, s="bodyl"))
    story.append(sp(0.3))
    story.append(Paragraph("Los 6 proyectos congelados", S["h3"]))
    story.append(Paragraph(
        "Recuerda el acuerdo contigo mismo: ChefMenu, VideoStudio, Financial Analyzer, Alertas/Trading, "
        "y los demás quedan congelados estos 30 días. No los abandonas: los aparcas para volver con "
        "foco cuando MerakIA genere su primer cliente. Cada hora que les dediques este mes es una hora "
        "que no estás vendiendo.", S["body"]))

    # ── CIERRE ──
    story.append(PageBreak())
    story.append(sp(3))
    story.append(Paragraph("El plan ya no es el problema.", S["quote"]))
    story.append(sp(0.3))
    story.append(Paragraph("La única variable que queda eres tú llamando a la primera clínica.", S["quote"]))
    story.append(sp(0.5))
    story.append(hr(CYAN, 2))
    story.append(sp(0.4))
    story.append(Paragraph(
        "Tienes el nicho, el dolor cuantificado, la oferta, 40 prospectos reales con su teléfono, "
        "los guiones, la demo, el proceso de entrega y el calendario. Todo lo que falta cabe en una "
        "acción: marcar el primer número. Empieza por el #1 de la lista.", S["pdesc"]))
    story.append(sp(0.8))
    story.append(Paragraph(
        "MerakIA · Plan de Acción 30 días · Clínicas dentales Vilanova i la Geltrú · "
        "Generado el 27 de junio de 2026", S["mini"]))

    doc.build(story, onFirstPage=_draw_bg, onLaterPages=_draw_bg, canvasmaker=Cnv)
    print(f"OK -> {OUTPUT}")


if __name__ == "__main__":
    build()
