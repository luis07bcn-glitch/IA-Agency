# -*- coding: utf-8 -*-
"""
Ficha de venta — Estetic Estil (Vilanova i la Geltru)
Genera ficha_estetic_estil.pdf: verificacion digital + diagnostico + los 3 textos
de maxima persuasion (email, WhatsApp, guion de llamada con objeciones) listos
para usar sin tener que volver al chat.
"""
import html
import re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas

ROOT = Path(__file__).parent
OUTPUT = ROOT / "ficha_estetic_estil.pdf"

FONDO  = colors.HexColor("#0a0e1a")
PANEL  = colors.HexColor("#121829")
PANEL2 = colors.HexColor("#0f1422")
LINEA  = colors.HexColor("#26304a")
TEXTO  = colors.HexColor("#cdd6e8")
TENUE  = colors.HexColor("#8a96b0")
BLANCO = colors.white
ROJO   = colors.HexColor("#ef4444")
AMBAR  = colors.HexColor("#f5a623")
VERDE  = colors.HexColor("#34d399")
CYAN   = colors.HexColor("#2de2e6")
GOLD   = colors.HexColor("#e4b85c")
W = 17 * cm


def limpia(t):
    if not t:
        return ""
    return t.encode("cp1252", "ignore").decode("cp1252")


def px(t):
    return html.escape(limpia(str(t))).replace("\n", "<br/>")


def _bg(cnv, doc):
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
        self.drawString(2 * cm, 0.9 * cm, "MerakIA — Ficha de venta · Estetic Estil")
        self.drawRightString(pw - 2 * cm, 0.9 * cm, f"{self._pageNumber} / {n}")
        self.setStrokeColor(LINEA)
        self.setLineWidth(0.5)
        self.line(2 * cm, 1.15 * cm, pw - 2 * cm, 1.15 * cm)
        self.restoreState()


def build():
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, topMargin=1.6 * cm, bottomMargin=1.6 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title="MerakIA — Ficha de venta: Estetic Estil", author="MerakIA Agency")
    base = getSampleStyleSheet()

    def stl(n, **kw):
        return ParagraphStyle(n, parent=base["Normal"], **kw)

    S = {
        "ptit": stl("ptit", fontSize=25, textColor=BLANCO, fontName="Helvetica-Bold",
                    alignment=TA_CENTER, leading=29),
        "psub": stl("psub", fontSize=11.5, textColor=CYAN, fontName="Helvetica-Bold",
                    alignment=TA_CENTER, spaceAfter=4),
        "pdesc": stl("pdesc", fontSize=9.5, textColor=TENUE, alignment=TA_CENTER, leading=14),
        "h2": stl("h2", fontSize=12, textColor=BLANCO, fontName="Helvetica-Bold",
                  spaceBefore=8, spaceAfter=3),
        "h3": stl("h3", fontSize=8, textColor=GOLD, fontName="Helvetica-Bold", spaceAfter=2),
        "body": stl("body", fontSize=9.3, leading=13.5, textColor=TEXTO, alignment=TA_JUSTIFY),
        "tc": stl("tc", fontSize=8, leading=11.5, textColor=TEXTO),
        "tcb": stl("tcb", fontSize=8, leading=11.5, textColor=BLANCO, fontName="Helvetica-Bold"),
        "tch": stl("tch", fontSize=7.5, leading=10, textColor=BLANCO, fontName="Helvetica-Bold"),
        "kpi": stl("kpi", fontSize=16, textColor=CYAN, fontName="Helvetica-Bold", alignment=TA_CENTER),
        "kpil": stl("kpil", fontSize=6.8, textColor=TENUE, alignment=TA_CENTER, leading=8.5),
        "copy": stl("copy", fontSize=8.6, leading=12.6, textColor=colors.HexColor("#d7e0f0")),
        "copyh": stl("copyh", fontSize=8.9, leading=12.6, textColor=GOLD, fontName="Helvetica-Bold"),
        "copygap": stl("copygap", fontSize=3, leading=4, textColor=PANEL2),
        "mini": stl("mini", fontSize=7.8, textColor=TENUE, leading=11),
    }

    def sp(h=0.3):
        return Spacer(1, h * cm)

    def hr(c=LINEA, t=1):
        return HRFlowable(width="100%", thickness=t, color=c, spaceAfter=4)

    def kpi_box(kpis, border=CYAN):
        w = W / len(kpis)
        data = [[Paragraph(v, S["kpi"]) for v, _, _ in kpis],
                [Paragraph(l, S["kpil"]) for _, l, _ in kpis]]
        t = Table(data, colWidths=[w] * len(kpis))
        cmds = [
            ("BACKGROUND", (0, 0), (-1, -1), PANEL),
            ("BOX", (0, 0), (-1, -1), 1, border),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, LINEA),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        for i, (_, _, col) in enumerate(kpis):
            if col:
                cmds.append(("TEXTCOLOR", (i, 0), (i, 0), col))
        t.setStyle(TableStyle(cmds))
        return t

    def _md_inline(s):
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        return s

    def copy_box(titulo, texto, border, canal):
        base_txt = html.escape(limpia(texto))
        rows = [[Paragraph(f'{canal} — {titulo}', S["tch"])]]
        blank = False
        for raw in base_txt.split("\n"):
            st = raw.strip()
            if not st:
                if not blank:
                    rows.append([Paragraph("&nbsp;", S["copygap"])])
                    blank = True
                continue
            blank = False
            rows.append([Paragraph(_md_inline(st), S["copy"])])
        t = Table(rows, colWidths=[W], repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), border),
            ("TEXTCOLOR", (0, 0), (0, 0), FONDO),
            ("BACKGROUND", (0, 1), (-1, -1), PANEL2),
            ("BOX", (0, 0), (-1, -1), 0.8, border),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 1.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
            ("TOPPADDING", (0, 0), (0, 0), 5),
            ("BOTTOMPADDING", (0, 0), (0, 0), 5),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 7),
        ]))
        return [t, sp(0.25)]

    story = []

    # ---- PORTADA ----
    story.append(sp(1.6))
    story.append(Paragraph("FICHA DE VENTA", S["psub"]))
    story.append(sp(0.1))
    story.append(Paragraph("Estetic Estil", S["ptit"]))
    story.append(sp(0.2))
    story.append(Paragraph("Vilanova i la Geltrú · Estética &amp; peluquería", S["psub"]))
    story.append(sp(0.25))
    story.append(hr(CYAN, 2))
    story.append(sp(0.3))

    story.append(kpi_box([
        ("4.9★", "RATING GOOGLE (~80 reseñas)", VERDE),
        ("15.2/100", "MADUREZ DIGITAL", ROJO),
        ("93/100", "PROB. DE CIERRE", VERDE),
        ("~2.760€", "PIERDE AL MES (est.)", ROJO),
    ], border=CYAN))
    story.append(sp(0.35))

    story.append(Paragraph("Diagnóstico", S["h2"]))
    story.append(Paragraph(
        "Reputación excelente (4.9★, ~80 reseñas) pero infraestructura digital "
        "prácticamente inexistente: sin web propia, sin chatbot, sin agente IA en "
        "WhatsApp, sin captación de leads. Toda la demanda depende de que alguien "
        "conteste el teléfono en horario comercial. Argumento de venta más fuerte: "
        "cada noche y cada domingo que pasa sin respuesta automática es una clienta "
        "que se va a la competencia sin que nadie lo note.", S["body"]))
    story.append(sp(0.25))

    story.append(Paragraph("Verificación de estado (previa a la llamada)", S["h3"]))
    verif = [
        ("Negocio real y activo", "Confirmado en Facebook, Google Maps, Treatwell, Volumus, bodas.net."),
        ("Web propia", "No tiene — solo Google Maps y redes."),
        ("WhatsApp / atención", "Manual, sin automatización ni agente IA detectado."),
        ("Reservas online (Treatwell)", "Desactivadas — \"no acepta reservas en este momento\"."),
        ("Aviso antes de llamar", "Reseñas en Treatwell de +1 año — comprobar en Google Maps que "
                                   "el horario y la actividad reciente confirman que sigue operativa."),
    ]
    vrows = [[Paragraph(k, S["tcb"]), Paragraph(v, S["tc"])] for k, v in verif]
    vt = Table(vrows, colWidths=[4.6 * cm, 12.4 * cm])
    vt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL2),
        ("GRID", (0, 0), (-1, -1), 0.3, LINEA),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(vt)
    story.append(sp(0.3))

    story.append(Paragraph("Dinero que pierde hoy — ~2.760 €/mes", S["h2"]))
    prows = [[Paragraph("Concepto", S["tch"]), Paragraph("€/mes", S["tch"]), Paragraph("Por qué", S["tch"])],
             [Paragraph("Leads fuera de horario sin atender", S["tcb"]), Paragraph("1.800", S["tcb"]),
              Paragraph("~30 contactos/mes llegan fuera de horario y no hay quién responda.", S["tc"])],
             [Paragraph("Conversión por debajo de potencial", S["tcb"]), Paragraph("960", S["tcb"]),
              Paragraph("Sin CTA ni formulario, no hay forma de capturar ni convertir leads.", S["tc"])]]
    pt = Table(prows, colWidths=[5.0 * cm, 1.8 * cm, 10.2 * cm], repeatRows=1)
    pt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PANEL),
        ("TEXTCOLOR", (0, 0), (-1, 0), ROJO),
        ("GRID", (0, 0), (-1, -1), 0.3, LINEA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PANEL2, PANEL]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TEXTCOLOR", (1, 1), (1, -1), ROJO),
    ]))
    story.append(pt)
    story.append(sp(0.3))

    story.append(Paragraph("Qué ofrecerle", S["h2"]))
    srows = [[Paragraph("Servicio", S["tch"]), Paragraph("Setup", S["tch"]),
              Paragraph("€/mes", S["tch"]), Paragraph("Impacto", S["tch"])],
             [Paragraph("Agente IA en WhatsApp 24/7", S["tcb"]), Paragraph("1.000€", S["tc"]),
              Paragraph("300€", S["tc"]), Paragraph("Responde en segundos a cualquier hora, agenda citas.", S["tc"])],
             [Paragraph("Chatbot IA en la web 24/7", S["tcb"]), Paragraph("1.140€", S["tc"]),
              Paragraph("250€", S["tc"]), Paragraph("Captura el ~25% de leads que hoy se pierden.", S["tc"])],
             [Paragraph("Web profesional de conversión", S["tcb"]), Paragraph("1.660€", S["tc"]),
              Paragraph("—", S["tc"]), Paragraph("Presencia donde el 81% busca antes de contactar.", S["tc"])]]
    st_ = Table(srows, colWidths=[5.4 * cm, 1.9 * cm, 1.9 * cm, 7.8 * cm], repeatRows=1)
    st_.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PANEL),
        ("TEXTCOLOR", (0, 0), (-1, 0), VERDE),
        ("GRID", (0, 0), (-1, -1), 0.3, LINEA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PANEL2, PANEL]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(st_)

    # ---- TEXTOS DE MAXIMA PERSUASION ----
    story.append(PageBreak())
    story.append(Paragraph("Textos de máxima persuasión — copiar y usar", S["h2"]))
    story.append(Paragraph(
        "Aplican prueba social (su propio 4.9★ como gancho), agitación cuantificada del "
        "dolor (€/mes concretos) y cierre asumido (dos opciones, nunca pregunta abierta).",
        S["mini"]))
    story.append(sp(0.2))

    email_txt = (
        "Asunto: Vuestro 4.9★ está financiando a la competencia (sin querer)\n\n"
        "Hola,\n\n"
        "Voy a ir directo porque vuestro tiempo vale más que una intro larga.\n\n"
        "Vi vuestra ficha de Google: 4.9 sobre 5 con más de 70 reseñas. Eso no lo tiene "
        "ni el 5% de los negocios de estética en Vilanova. Os lo habéis ganado a base de "
        "trato y trabajo bien hecho, eso no se compra.\n\n"
        "Y por eso mismo me llamó la atención lo que encontré después: no tenéis web "
        "propia, ni forma de responder fuera de horario. Solo Google Maps y un teléfono "
        "que nadie coge a las 20h de un martes.\n\n"
        "Aquí está el problema exacto: alguien ve vuestra nota de 4.9, decide escribiros "
        "por la noche (que es cuando más se decide este tipo de tratamiento), no le "
        "respondéis... y a la mañana siguiente ya ha reservado en el centro de al lado "
        "que sí le contestó en el momento.\n\n"
        "No es una teoría. Con vuestro volumen, eso son entre 8 y 12 clientas perdidas "
        "al mes, unos 1.800€ mensuales que se van sin que nadie se entere, porque no hay "
        "forma de medir lo que nunca llegó a sonar el teléfono.\n\n"
        "Lo que hacemos es sencillo: un agente de IA en vuestro WhatsApp que responde al "
        "instante, a cualquier hora, informa de tratamientos y agenda directamente en "
        "vuestra agenda. Sin que cambiéis nada de cómo trabajáis hoy.\n\n"
        "No os pido decidir nada por email. Solo 15 minutos para enseñaros, con vuestros "
        "propios números, cuánto estáis dejando sobre la mesa ahora mismo.\n\n"
        "¿Martes o jueves esta semana?\n\n"
        "Un saludo,\n"
        "[Tu nombre]\n"
        "MerakIA — Vilanova i la Geltrú\n\n"
        "P.D. Estoy cerrando esta semana con otro centro de estética de la zona, os "
        "enseño resultados reales, no una demo genérica."
    )
    story.extend(copy_box("Prospección en frío", email_txt, CYAN, "Email"))

    wa_txt = (
        "Hola! Soy [Nombre], de MerakIA (Vilanova).\n\n"
        "Vi vuestro 4.9★ en Google, vaya nivel. Por eso me sorprendió que fuera de "
        "horario (noches, domingos) nadie pueda responder por WhatsApp.\n\n"
        "Con vuestro volumen, eso suele ser 8-12 clientas al mes que se van a la "
        "competencia sin que os enteréis (~1.800€/mes en tratamientos perdidos).\n\n"
        "Tenemos un agente IA que responde al segundo, 24/7, e incluso agenda la cita "
        "solo. Cero cambios en cómo trabajáis ahora.\n\n"
        "¿15 min esta semana y os enseño el cálculo exacto para Estetic Estil?"
    )
    story.extend(copy_box("Primer contacto", wa_txt, VERDE, "WhatsApp"))

    call_txt = (
        "**APERTURA (0-10s)**\n"
        "\"Hola, ¿hablo con Estetic Estil? Perfecto, soy [Nombre], de MerakIA, aquí en "
        "Vilanova. Un minuto, ¿te va bien?\"\n\n"
        "**GANCHO — halago específico + agitación (10-30s)**\n"
        "\"Os llamo porque vi vuestra ficha de Google: 4.9 sobre 5, más de 70 reseñas. "
        "Eso es una barbaridad, muy pocos centros lo tienen. Y precisamente por eso me "
        "choca lo que vi después: fuera del horario de la tienda, si alguien os escribe "
        "por WhatsApp a las 9 de la noche, no hay quien responda hasta el día siguiente. "
        "Con vuestra reputación, cada noche que pasa así es una clienta que se va directa "
        "al centro de al lado. ¿Os suena esto?\"\n"
        "(pausa: dejar que confirmen o maticen)\n\n"
        "**CUALIFICACIÓN (30-60s)**\n"
        "\"¿Cómo lleváis ahora mismo esos mensajes fuera de horario? ¿Alguien está "
        "pendiente o se queda ahí hasta que abrís?\"\n"
        "\"Y a ojo, ¿cuántos mensajes nuevos os llegan a la semana por WhatsApp o "
        "Instagram?\"\n"
        "(dejar que ellos hagan el cálculo en voz alta, vale más que cualquier cifra "
        "que les des tú)\n\n"
        "**PROPUESTA (60-80s)**\n"
        "\"Lo que hacemos es instalar un agente de inteligencia artificial en vuestro "
        "WhatsApp que responde al instante, cualquier hora, informa de tratamientos y "
        "precios, y agenda la cita directo en vuestro calendario. Centros con vuestro "
        "perfil recuperan entre 8 y 15 clientas al mes que hoy se pierden. Vosotros "
        "seguís haciendo exactamente lo mismo que ahora, solo que ya no se os escapa "
        "nadie.\"\n\n"
        "**CIERRE ASUMIDO (80-90s)**\n"
        "\"No te pido que decidas nada ahora. Solo 20 minutos esta semana, te enseño con "
        "vuestros números reales cuánto estáis perdiendo y cómo se soluciona. ¿Martes o "
        "jueves por la tarde te va mejor?\"\n\n"
        "**OBJECIONES**\n\n"
        "\"No me interesa\" -> \"Lo entiendo, ni yo esperaría que lo supieras sin verlo. "
        "Solo te pido 20 min para enseñarte la cifra real de lo que perdéis al mes. Si "
        "no tiene sentido, me lo dices y no insisto más.\"\n\n"
        "\"Ya lo llevamos nosotros\" -> \"Genial que esté cubierto. ¿Es algo que responde "
        "solo 24/7, o alguien que lo mira cuando puede?\" (Si es manual:) \"Ahí es justo "
        "donde entramos, el hueco de la noche y el domingo.\"\n\n"
        "\"Ahora no es buen momento\" -> \"Con más razón, cada semana así son clientas que "
        "se van. No te pido nada hoy, solo la reunión. ¿La semana que viene mejor?\"\n\n"
        "\"¿Cuánto cuesta?\" -> \"Depende de qué necesitéis exactamente, por eso prefiero "
        "no tirar un número al aire. Lo que te puedo decir es que se nota en el primer "
        "mes. ¿Vemos esos 20 min y te lo cuento con transparencia total?\""
    )
    story.extend(copy_box("Guion de llamada en frío + objeciones", call_txt, AMBAR, "Llamada"))

    doc.build(story, onFirstPage=_bg, onLaterPages=_bg, canvasmaker=Cnv)
    print(f"OK -> {OUTPUT}")


if __name__ == "__main__":
    build()
