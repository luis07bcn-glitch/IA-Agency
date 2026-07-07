# -*- coding: utf-8 -*-
"""
ANALISIS PARA EL CLIENTE — Estetic Estil (documento que SE ENVIA a la clienta)
PDF llamativo y personalizado para adjuntar al email/Instagram de primer contacto:
reconocimiento de su trabajo (4.9), el contraste con su puerta digital, la prueba
del cliente misterioso, cuanto les cuesta, la solucion en accion (mockup WhatsApp)
y la oferta Cliente Fundador con CTA.

Genera: analisis_estetic_estil_merakia.pdf
"""
import html
import re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, HRFlowable, PageBreak,
    KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas

ROOT = Path(__file__).parent
OUTPUT = ROOT / "analisis_estetic_estil_merakia.pdf"

FONDO  = colors.HexColor("#0a0e1a")
PANEL  = colors.HexColor("#121829")
PANEL2 = colors.HexColor("#0f1422")
LINEA  = colors.HexColor("#26304a")
TEXTO  = colors.HexColor("#cdd6e8")
TENUE  = colors.HexColor("#8a96b0")
BLANCO = colors.white
ROJO   = colors.HexColor("#ef4444")
ROSAL  = colors.HexColor("#fca5a5")
AMBAR  = colors.HexColor("#f5a623")
VERDE  = colors.HexColor("#34d399")
CYAN   = colors.HexColor("#2de2e6")
VIOLETA= colors.HexColor("#8b5cf6")
GOLD   = colors.HexColor("#e4b85c")
WABG   = colors.HexColor("#0b141a")   # fondo chat whatsapp dark
WAIN   = colors.HexColor("#202c33")   # burbuja entrante
WAOUT  = colors.HexColor("#005c4b")   # burbuja saliente
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
        self.drawString(2 * cm, 0.9 * cm,
                        "Análisis preparado en exclusiva para Estetic Estil · MerakIA")
        self.drawRightString(pw - 2 * cm, 0.9 * cm, f"{self._pageNumber} / {n}")
        self.setStrokeColor(LINEA)
        self.setLineWidth(0.5)
        self.line(2 * cm, 1.15 * cm, pw - 2 * cm, 1.15 * cm)
        self.restoreState()


def build():
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, topMargin=1.6 * cm, bottomMargin=1.6 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title="Análisis digital de Estetic Estil — MerakIA",
        author="MerakIA")
    base = getSampleStyleSheet()

    def stl(n, **kw):
        return ParagraphStyle(n, parent=base["Normal"], **kw)

    S = {
        "ptit": stl("ptit", fontSize=26, textColor=BLANCO, fontName="Helvetica-Bold",
                    alignment=TA_CENTER, leading=30),
        "psub": stl("psub", fontSize=11.5, textColor=CYAN, fontName="Helvetica-Bold",
                    alignment=TA_CENTER, spaceAfter=4),
        "pfrase": stl("pfrase", fontSize=11.5, textColor=TEXTO, alignment=TA_CENTER,
                      leading=17, fontName="Helvetica-Oblique"),
        "sec": stl("sec", fontSize=15, textColor=BLANCO, fontName="Helvetica-Bold",
                   leading=18, spaceBefore=4, spaceAfter=2),
        "h3": stl("h3", fontSize=8.5, textColor=GOLD, fontName="Helvetica-Bold", spaceAfter=2),
        "body": stl("body", fontSize=9.6, leading=14.5, textColor=TEXTO, alignment=TA_JUSTIFY),
        "bodyl": stl("bodyl", fontSize=9.6, leading=14.5, textColor=TEXTO, alignment=TA_LEFT),
        "big": stl("big", fontSize=12, leading=17, textColor=BLANCO, alignment=TA_CENTER,
                   fontName="Helvetica-Bold"),
        "tc": stl("tc", fontSize=8.3, leading=12, textColor=TEXTO),
        "tcb": stl("tcb", fontSize=8.3, leading=12, textColor=BLANCO, fontName="Helvetica-Bold"),
        "tch": stl("tch", fontSize=7.6, leading=10, textColor=BLANCO, fontName="Helvetica-Bold"),
        "kpi": stl("kpi", fontSize=19, textColor=CYAN, fontName="Helvetica-Bold", alignment=TA_CENTER),
        "kpil": stl("kpil", fontSize=6.9, textColor=TENUE, alignment=TA_CENTER, leading=9),
        "mini": stl("mini", fontSize=7.9, textColor=TENUE, leading=11.5),
        "minic": stl("minic", fontSize=7.9, textColor=TENUE, leading=11.5, alignment=TA_CENTER),
        "chat": stl("chat", fontSize=9, leading=13, textColor=colors.HexColor("#e9edef")),
        "chattime": stl("chattime", fontSize=6.5, textColor=colors.HexColor("#8696a0"),
                        alignment=TA_RIGHT),
        "chathdr": stl("chathdr", fontSize=9, textColor=colors.HexColor("#e9edef"),
                       fontName="Helvetica-Bold"),
        "chatsub": stl("chatsub", fontSize=6.8, textColor=colors.HexColor("#8696a0")),
        "barlab": stl("barlab", fontSize=8.5, textColor=TEXTO, fontName="Helvetica-Bold"),
        "barval": stl("barval", fontSize=8.5, textColor=BLANCO, fontName="Helvetica-Bold",
                      alignment=TA_CENTER),
        "ofbig": stl("ofbig", fontSize=28, textColor=VERDE, fontName="Helvetica-Bold",
                     alignment=TA_CENTER, leading=30),
        "ofanc": stl("ofanc", fontSize=11, textColor=TENUE, alignment=TA_CENTER),
        "oflab": stl("oflab", fontSize=8.8, textColor=TEXTO, alignment=TA_CENTER, leading=12.5),
        "quote": stl("quote", fontSize=10.5, leading=15.5, textColor=colors.HexColor("#e8dcc0"),
                     fontName="Helvetica-Oblique", alignment=TA_CENTER),
        "cta": stl("cta", fontSize=13, textColor=FONDO, fontName="Helvetica-Bold",
                   alignment=TA_CENTER, leading=17),
        "ctasub": stl("ctasub", fontSize=8.6, textColor=FONDO, alignment=TA_CENTER, leading=12),
    }

    def sp(h=0.3):
        return Spacer(1, h * cm)

    def hr(c=LINEA, t=1):
        return HRFlowable(width="100%", thickness=t, color=c, spaceAfter=4)

    def section(titulo, color=CYAN):
        bar = Table([[Paragraph(titulo, S["sec"])]], colWidths=[W])
        bar.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PANEL),
            ("LINEBEFORE", (0, 0), (0, -1), 3, color),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        return bar

    def kpi_box(kpis, border=CYAN):
        w = W / len(kpis)
        data = [[Paragraph(v, S["kpi"]) for v, _, _ in kpis],
                [Paragraph(l, S["kpil"]) for _, l, _ in kpis]]
        t = Table(data, colWidths=[w] * len(kpis))
        cmds = [
            ("BACKGROUND", (0, 0), (-1, -1), PANEL),
            ("BOX", (0, 0), (-1, -1), 1, border),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, LINEA),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        for i, (_, _, col) in enumerate(kpis):
            if col:
                cmds.append(("TEXTCOLOR", (i, 0), (i, 0), col))
        t.setStyle(TableStyle(cmds))
        return t

    def barra(label, pct, color, texto_dcha):
        """Barra horizontal de progreso hecha con tabla."""
        total = 11.5 * cm
        fill = max(0.8, total * pct / 100.0)
        rest = max(0.1, total - fill)
        bar = Table([[Paragraph(f"{pct}", S["barval"]), ""]],
                    colWidths=[fill, rest], rowHeights=[0.62 * cm])
        bar.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), color),
            ("BACKGROUND", (1, 0), (1, 0), PANEL2),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 0.5, LINEA),
        ]))
        row = Table([[Paragraph(label, S["barlab"]), bar,
                      Paragraph(texto_dcha, S["mini"])]],
                    colWidths=[3.4 * cm, 11.5 * cm, 2.1 * cm])
        row.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (0, 0), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        return row

    def burbuja(texto, hora, quien):
        """Burbuja de chat estilo WhatsApp. quien: 'in' (clienta) | 'out' (agente)."""
        bg = WAIN if quien == "in" else WAOUT
        bw = 9.2 * cm
        inner = Table([[Paragraph(texto, S["chat"])], [Paragraph(hora, S["chattime"])]],
                      colWidths=[bw])
        inner.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (0, 0), 6),
            ("BOTTOMPADDING", (0, 0), (0, 0), 1),
            ("TOPPADDING", (0, 1), (0, 1), 0),
            ("BOTTOMPADDING", (0, 1), (0, 1), 4),
        ]))
        gap = W - 0.8 * cm - bw
        if quien == "in":
            row = Table([[inner, ""]], colWidths=[bw, gap])
        else:
            row = Table([["", inner]], colWidths=[gap, bw])
        row.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        return row

    story = []

    # ═══════════ PORTADA ═══════════
    story.append(sp(1.5))
    story.append(Paragraph("ANÁLISIS DIGITAL · PREPARADO EN EXCLUSIVA PARA", S["psub"]))
    story.append(sp(0.15))
    story.append(Paragraph("Estetic Estil", S["ptit"]))
    story.append(sp(0.12))
    story.append(Paragraph("Carrer d'Olèrdola 43 · Vilanova i la Geltrú", S["psub"]))
    story.append(sp(0.35))
    story.append(hr(CYAN, 2.5))
    story.append(sp(0.35))
    story.append(Paragraph(
        "Hemos analizado a fondo vuestra presencia online.<br/>"
        "Lo primero que encontramos no fue un problema: fue un negocio excelente.",
        S["pfrase"]))
    story.append(sp(0.45))
    story.append(kpi_box([
        ("4.9★", "VALORACIÓN EN GOOGLE", VERDE),
        ("81", "RESEÑAS DE CLIENTAS", VERDE),
        ("Top", "ENTRE LOS MEJOR VALORADOS DE VILANOVA", GOLD),
    ], border=VERDE))
    story.append(sp(0.4))
    story.append(Paragraph(
        "Un 4.9 con 81 reseñas no se compra ni se improvisa: se gana clienta a clienta, "
        "año tras año. Vuestro trabajo habla por sí solo — profesionalidad, trato cercano "
        "y resultados. Esa reputación es un activo que muy pocos centros tienen.", S["body"]))
    story.append(sp(0.25))
    story.append(Paragraph(
        "Pero durante el análisis también encontramos algo que creemos que debéis saber: "
        "<b>una parte de las clientas que esa reputación os trae cada semana no consigue "
        "llegar hasta vosotras.</b> En las próximas páginas os enseñamos exactamente dónde "
        "se pierden, cuánto puede estar costando y cómo se soluciona — sin que cambiéis "
        "nada de vuestra forma de trabajar.", S["body"]))
    story.append(sp(0.5))
    story.append(Paragraph("MerakIA · Agencia de IA para negocios locales · Vilanova i la Geltrú", S["minic"]))

    # ═══════════ EL CONTRASTE ═══════════
    story.append(PageBreak())
    story.append(section("1 · Vuestra reputación vs. vuestra puerta de entrada", CYAN))
    story.append(sp(0.3))
    story.append(Paragraph(
        "Medimos dos cosas de todo negocio local: la <b>reputación</b> (lo que la gente "
        "opina) y la <b>puerta de entrada digital</b> (lo fácil que es pasar de \"me "
        "interesa\" a \"tengo cita\"). Este es vuestro resultado:", S["body"]))
    story.append(sp(0.35))
    story.append(barra("Reputación", 91, VERDE, "excelente"))
    story.append(barra("Puerta digital", 15, ROJO, "casi cerrada"))
    story.append(sp(0.25))
    story.append(Paragraph(
        "Ese hueco entre las dos barras es la historia de este documento. La reputación "
        "genera demanda todos los días; la puerta de entrada decide cuánta de esa demanda "
        "se convierte en citas. Hoy, para reservar con vosotras solo existe un camino: "
        "<b>llamar al fijo, en horario de tienda, justo cuando tenéis las manos ocupadas "
        "con otra clienta.</b>", S["body"]))
    story.append(sp(0.3))

    story.append(Paragraph("El recorrido real de una clienta nueva", S["h3"]))
    rec = [
        ("1. Os descubre", "Ve vuestro 4.9 en Google o un trabajo en Instagram. Le encanta.", "OK"),
        ("2. Quiere saber más", "Busca vuestra web para ver tratamientos y precios. No hay web.", "SE PIERDE AQUÍ"),
        ("3. Intenta escribiros", "Busca un WhatsApp para preguntar sin llamar. No hay WhatsApp.", "SE PIERDE AQUÍ"),
        ("4. Intenta reservar", "Son las 21:30. El fijo está cerrado hasta mañana.", "SE PIERDE AQUÍ"),
        ("5. Al día siguiente", "El impulso pasó… o ya reservó donde sí le respondieron anoche.", "CLIENTA PERDIDA"),
    ]
    rrows = [[Paragraph("Paso", S["tch"]), Paragraph("Qué pasa", S["tch"]), Paragraph("Resultado", S["tch"])]]
    for k, v, r in rec:
        col = VERDE if r == "OK" else (AMBAR if "PIERDE" in r else ROJO)
        rrows.append([Paragraph(k, S["tcb"]), Paragraph(v, S["tc"]),
                      Paragraph(f'<font color="{col.hexval().replace("0x","#")}"><b>{r}</b></font>', S["tc"])])
    rt = Table(rrows, colWidths=[3.6 * cm, 9.4 * cm, 4.0 * cm], repeatRows=1)
    rt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PANEL),
        ("TEXTCOLOR", (0, 0), (-1, 0), CYAN),
        ("GRID", (0, 0), (-1, -1), 0.3, LINEA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PANEL2, PANEL]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(rt)
    story.append(sp(0.25))
    story.append(Paragraph(
        "Lo hemos comprobado nosotros mismos: intentamos pedir cita un martes por la noche, "
        "como lo haría cualquier clienta después del trabajo. No encontramos ninguna forma "
        "de hacerlo. <b>Nada de esto es culpa vuestra — es simplemente una pieza que falta.</b> "
        "Y lo más importante: no lo veis porque la clienta que no consigue contactar no deja "
        "rastro. No se queja. Simplemente no llega.", S["body"]))

    # ═══════════ CUÁNTO CUESTA ═══════════
    story.append(PageBreak())
    story.append(section("2 · Cuánto puede estar costando", ROJO))
    story.append(sp(0.3))
    story.append(Paragraph(
        "Con supuestos prudentes (volumen de consultas habitual en centros de vuestro "
        "tamaño y un ticket medio de tratamiento de ~60–400€ según servicio), esta es "
        "nuestra estimación de lo que ese muro invisible os cuesta cada mes:", S["body"]))
    story.append(sp(0.3))
    prows = [
        [Paragraph("Fuga", S["tch"]), Paragraph("Estimación/mes", S["tch"]), Paragraph("Por qué ocurre", S["tch"])],
        [Paragraph("Consultas fuera de horario sin respuesta", S["tcb"]),
         Paragraph("~1.800€", S["tcb"]),
         Paragraph("Unas 25–30 personas al mes intentan contactar por la tarde-noche o el domingo. Sin canal que responda, la mayoría no vuelve a intentarlo.", S["tc"])],
        [Paragraph("Clientas nuevas que no os encuentran", S["tcb"]),
         Paragraph("~960€", S["tcb"]),
         Paragraph("Quien busca en Google \"depilación láser Vilanova\" o \"tratamiento facial Vilanova\" hoy no os ve: sin web, no hay dónde aterrizar ni forma de reservar.", S["tc"])],
        [Paragraph("TOTAL estimado", S["tcb"]),
         Paragraph("~2.760€/mes", S["tcb"]),
         Paragraph("Más de 33.000€ al año. No por hacer nada mal — por no tener por dónde entrar.", S["tc"])],
    ]
    pt = Table(prows, colWidths=[5.4 * cm, 2.6 * cm, 9.0 * cm], repeatRows=1)
    pt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PANEL),
        ("TEXTCOLOR", (0, 0), (-1, 0), ROJO),
        ("GRID", (0, 0), (-1, -1), 0.3, LINEA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PANEL2, PANEL]),
        ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#2a1420")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("TEXTCOLOR", (1, 1), (1, -1), ROJO),
    ]))
    story.append(pt)
    story.append(sp(0.25))
    story.append(Paragraph(
        "Es una estimación honesta, no una cifra para asustar: en 15 minutos con vuestros "
        "números reales (cuántas llamadas perdéis, cuántos mensajes os llegan a Instagram "
        "fuera de hora) la ajustamos juntas al euro.", S["mini"]))
    story.append(sp(0.4))
    story.append(hr(GOLD, 1.5))
    story.append(sp(0.25))
    story.append(Paragraph(
        "\"El problema no es que os falten clientas.<br/>Es que las que ya vienen de camino "
        "se encuentran la puerta cerrada.\"", S["quote"]))

    # ═══════════ LA SOLUCIÓN EN ACCIÓN ═══════════
    story.append(PageBreak())
    story.append(section("3 · La solución, en acción", VERDE))
    story.append(sp(0.3))
    story.append(Paragraph(
        "Proponemos una sola cosa, sencilla y probada: <b>un agente de inteligencia "
        "artificial en un WhatsApp de Estetic Estil</b>, configurado con vuestros "
        "tratamientos, precios y tono de trato. Responde al momento, a cualquier hora, "
        "todos los días. Así se vería una conversación real:", S["body"]))
    story.append(sp(0.3))

    # mockup whatsapp
    chat_head = Table([[Paragraph("Estetic Estil", S["chathdr"])],
                       [Paragraph("en línea · responde al instante", S["chatsub"])]],
                      colWidths=[W - 0.8 * cm])
    chat_head.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1f2c34")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (0, 0), 6),
        ("BOTTOMPADDING", (0, 1), (0, 1), 6),
    ]))
    burb = [
        burbuja("Hola! Vi vuestro centro en Google, tenéis unas reseñas buenísimas. "
                "¿Hacéis depilación láser? ¿Qué precio tiene piernas enteras?", "23:47", "in"),
        burbuja("¡Hola! Gracias por escribirnos. Sí, hacemos depilación láser de diodo. "
                "Piernas enteras son 89€/sesión, y tenemos bono de 6 sesiones con "
                "descuento. Si quieres, te reservo una valoración gratuita de 15 min "
                "para verlo en persona, sin compromiso.", "23:47", "out"),
        burbuja("Uy genial. ¿Podría ser el jueves a última hora de la tarde?", "23:49", "in"),
        burbuja("Claro. El jueves tengo 17:30 o 18:15 disponibles con Sara. "
                "¿Cuál te va mejor?", "23:49", "out"),
        burbuja("18:15 perfecto", "23:50", "in"),
        burbuja("¡Hecho! Cita reservada: jueves 18:15, valoración de depilación láser "
                "con Sara, en Carrer d'Olèrdola 43. Te enviaré un recordatorio el "
                "miércoles. ¡Hasta el jueves!", "23:50", "out"),
    ]
    chat_body_rows = [[b] for b in burb]
    chat_body = Table(chat_body_rows, colWidths=[W - 0.8 * cm])
    chat_body.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WABG),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    chat = Table([[chat_head], [chat_body]], colWidths=[W - 0.8 * cm])
    chat.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1f2c34")),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    chat_wrap = Table([[chat]], colWidths=[W])
    chat_wrap.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0.4 * cm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0.4 * cm),
    ]))
    story.append(chat_wrap)
    story.append(sp(0.2))
    story.append(Paragraph(
        "Son las 23:47 de un martes. Nadie de vuestro equipo ha tocado el móvil. "
        "La cita ya está en la agenda.", S["big"]))
    story.append(sp(0.15))
    story.append(Paragraph(
        "(Conversación de ejemplo: precios, servicios y disponibilidad se configuran con "
        "vuestros datos reales, y el tono se adapta al vuestro.)", S["minic"]))

    # ═══════════ QUÉ HACE / QUÉ NO ═══════════
    story.append(PageBreak())
    story.append(section("4 · Qué hace por vosotras (y qué no)", VIOLETA))
    story.append(sp(0.3))
    qh = [
        [Paragraph("LO QUE HACE", S["tch"]), Paragraph("LO QUE NO HACE", S["tch"])],
        [Paragraph("Responde al instante 24/7: precios, tratamientos, dudas frecuentes, cómo llegar.", S["tc"]),
         Paragraph("No sustituye vuestro trato. En cuanto una conversación necesita a una persona, os avisa y se aparta.", S["tc"])],
        [Paragraph("Agenda citas directamente y envía confirmación y recordatorio (menos olvidos y ausencias).", S["tc"]),
         Paragraph("No cambia vuestra forma de trabajar: vosotras seguís con vuestra agenda; él solo la llena.", S["tc"])],
        [Paragraph("Atiende a varias personas a la vez, también cuando estáis en cabina con las manos ocupadas.", S["tc"]),
         Paragraph("No suena a robot: se configura con vuestro tono cercano, en catalán o castellano.", S["tc"])],
        [Paragraph("Recoge el nombre y el interés de cada clienta: nada se pierde, todo queda registrado.", S["tc"]),
         Paragraph("No requiere que aprendáis nada técnico: lo montamos, lo probamos y os lo damos funcionando.", S["tc"])],
    ]
    qht = Table(qh, colWidths=[8.5 * cm, 8.5 * cm], repeatRows=1)
    qht.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), PANEL), ("BACKGROUND", (1, 0), (1, 0), PANEL),
        ("TEXTCOLOR", (0, 0), (0, 0), VERDE), ("TEXTCOLOR", (1, 0), (1, 0), CYAN),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PANEL2, PANEL]),
        ("GRID", (0, 0), (-1, -1), 0.3, LINEA),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(qht)
    story.append(sp(0.3))
    story.append(Paragraph(
        "En un centro de estética, el trato humano lo es todo. Por eso el agente no está "
        "pensado para reemplazarlo, sino para <b>proteger el momento en el que ocurre</b>: "
        "mientras vosotras estáis al 100% con la clienta de la cabina, él se ocupa de que "
        "la siguiente no se quede fuera.", S["body"]))

    # ═══════════ OFERTA ═══════════
    story.append(sp(0.4))
    story.append(section("5 · Nuestra propuesta para Estetic Estil", GOLD))
    story.append(sp(0.3))
    story.append(Paragraph(
        "Somos MerakIA, una agencia de IA de aquí, de Vilanova. Estamos seleccionando "
        "<b>un único centro de estética de la ciudad</b> como caso fundador: queremos "
        "demostrar lo que esta tecnología hace por un negocio local excelente, y para eso "
        "necesitamos al mejor. Por eso este análisis os llegó a vosotras y no a otro centro. "
        "A cambio de que, si funciona, nos deis vuestro testimonio, la propuesta es esta:",
        S["body"]))
    story.append(sp(0.3))
    of_price = Table([
        [Paragraph("PLAN CLIENTE FUNDADOR · Agente IA en WhatsApp 24/7", S["oflab"])],
        [Paragraph('Tarifa normal: <strike>900€ de montaje</strike> + <strike>300€/mes</strike>', S["ofanc"])],
        [Paragraph("0€ de montaje", S["ofbig"])],
        [Paragraph("Primer mes GRATIS para probarlo con clientas reales · después 150€/mes "
                    "<b>congelados para siempre</b>", S["oflab"])],
        [Paragraph("Sin permanencia · si en 30 días no os convence, lo retiramos y no nos debéis nada",
                    S["oflab"])],
    ], colWidths=[W])
    of_price.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("BOX", (0, 0), (-1, -1), 2, GOLD),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, LINEA),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 2), (-1, 2), 2),
        ("BOTTOMPADDING", (0, 2), (-1, 2), 2),
    ]))
    story.append(of_price)
    story.append(sp(0.25))
    story.append(Paragraph(
        "Para que os hagáis una idea: 150€/mes es menos de lo que factura una sola sesión "
        "de muchos de vuestros tratamientos. Si el agente recupera <b>una única clienta al "
        "mes</b>, ya está pagado varias veces. Y la estimación de la página 3 habla de "
        "bastantes más de una.", S["body"]))

    # ═══════════ CTA ═══════════
    story.append(sp(0.4))
    cta = Table([
        [Paragraph("¿Os lo enseñamos funcionando?", S["cta"])],
        [Paragraph("15 minutos, en vuestro centro y sin compromiso: llevamos el agente ya "
                    "configurado con vuestros tratamientos para que lo probéis vosotras mismas.",
                    S["ctasub"])],
        [Paragraph("<b>[TU NOMBRE] · MerakIA · [TU TELÉFONO / WHATSAPP] · [TU EMAIL]</b>",
                    S["ctasub"])],
    ], colWidths=[W])
    cta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CYAN),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ]))
    story.append(cta)
    story.append(sp(0.25))
    story.append(Paragraph(
        "Responded a este correo, escribidnos por Instagram o llamadnos — como os sea más "
        "cómodo. Si prefirís que no os contactemos más, también nos lo podéis decir y "
        "quedará aquí. Gracias por leer hasta el final: sea con nosotros o no, el hueco de "
        "la puerta digital merece que lo cerréis pronto. Vuestro 4.9 se lo ha ganado.",
        S["mini"]))

    doc.build(story, onFirstPage=_bg, onLaterPages=_bg, canvasmaker=Cnv)
    print(f"OK -> {OUTPUT}")


if __name__ == "__main__":
    build()
