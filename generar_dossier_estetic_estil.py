# -*- coding: utf-8 -*-
"""
DOSSIER DE PROSPECCION COMPLETO — Estetic Estil (Vilanova i la Geltru)
Primer cliente ancla de MerakIA. Prospeccion + dolores + escalera de servicios
+ oferta "Cliente Fundador" (precio accesible) + estrategia de venta/marketing
+ textos listos (visita, Instagram, llamada) + objeciones + palancas de persuasion.

Genera dossier_estetic_estil.pdf
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
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfgen import canvas

ROOT = Path(__file__).parent
OUTPUT = ROOT / "dossier_estetic_estil.pdf"

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
ROSA   = colors.HexColor("#ec4899")
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
        self.drawString(2 * cm, 0.9 * cm, "MerakIA — Dossier de venta · Estetic Estil (cliente fundador)")
        self.drawRightString(pw - 2 * cm, 0.9 * cm, f"{self._pageNumber} / {n}")
        self.setStrokeColor(LINEA)
        self.setLineWidth(0.5)
        self.line(2 * cm, 1.15 * cm, pw - 2 * cm, 1.15 * cm)
        self.restoreState()


def build():
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, topMargin=1.6 * cm, bottomMargin=1.6 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title="MerakIA — Dossier de venta: Estetic Estil", author="MerakIA Agency")
    base = getSampleStyleSheet()

    def stl(n, **kw):
        return ParagraphStyle(n, parent=base["Normal"], **kw)

    S = {
        "ptit": stl("ptit", fontSize=27, textColor=BLANCO, fontName="Helvetica-Bold",
                    alignment=TA_CENTER, leading=31),
        "psub": stl("psub", fontSize=11.5, textColor=CYAN, fontName="Helvetica-Bold",
                    alignment=TA_CENTER, spaceAfter=4),
        "pfrase": stl("pfrase", fontSize=11, textColor=TEXTO, alignment=TA_CENTER,
                      leading=16, fontName="Helvetica-Oblique"),
        "sec": stl("sec", fontSize=15, textColor=BLANCO, fontName="Helvetica-Bold",
                   leading=18, spaceBefore=4, spaceAfter=2),
        "h2": stl("h2", fontSize=12, textColor=BLANCO, fontName="Helvetica-Bold",
                  spaceBefore=8, spaceAfter=3),
        "h3": stl("h3", fontSize=8, textColor=GOLD, fontName="Helvetica-Bold", spaceAfter=2),
        "body": stl("body", fontSize=9.4, leading=14, textColor=TEXTO, alignment=TA_JUSTIFY),
        "bodyl": stl("bodyl", fontSize=9.4, leading=14, textColor=TEXTO, alignment=TA_LEFT),
        "tc": stl("tc", fontSize=8, leading=11.5, textColor=TEXTO),
        "tcb": stl("tcb", fontSize=8, leading=11.5, textColor=BLANCO, fontName="Helvetica-Bold"),
        "tch": stl("tch", fontSize=7.5, leading=10, textColor=BLANCO, fontName="Helvetica-Bold"),
        "kpi": stl("kpi", fontSize=17, textColor=CYAN, fontName="Helvetica-Bold", alignment=TA_CENTER),
        "kpil": stl("kpil", fontSize=6.8, textColor=TENUE, alignment=TA_CENTER, leading=8.5),
        "copy": stl("copy", fontSize=8.7, leading=12.8, textColor=colors.HexColor("#d7e0f0")),
        "copyh": stl("copyh", fontSize=9, leading=12.8, textColor=GOLD, fontName="Helvetica-Bold"),
        "copygap": stl("copygap", fontSize=3, leading=4, textColor=PANEL2),
        "mini": stl("mini", fontSize=7.8, textColor=TENUE, leading=11),
        "alerta": stl("alerta", fontSize=8.6, leading=12.5, textColor=ROSAL),
        "painnum": stl("painnum", fontSize=17, textColor=BLANCO, fontName="Helvetica-Bold",
                       alignment=TA_CENTER),
        "paint": stl("paint", fontSize=10.5, textColor=BLANCO, fontName="Helvetica-Bold", leading=13),
        "painb": stl("painb", fontSize=9, leading=13, textColor=TEXTO),
        "eur": stl("eur", fontSize=11, textColor=ROJO, fontName="Helvetica-Bold", alignment=TA_CENTER),
        "eurl": stl("eurl", fontSize=6, textColor=TENUE, alignment=TA_CENTER),
        "ofbig": stl("ofbig", fontSize=30, textColor=VERDE, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=32),
        "ofanc": stl("ofanc", fontSize=11, textColor=TENUE, alignment=TA_CENTER),
        "oflab": stl("oflab", fontSize=8.5, textColor=TEXTO, alignment=TA_CENTER, leading=12),
        "why": stl("why", fontSize=9.2, leading=13.5, textColor=colors.HexColor("#e8dcc0"), alignment=TA_LEFT),
        "quote": stl("quote", fontSize=9.4, leading=14, textColor=colors.HexColor("#d7e0f0"),
                     fontName="Helvetica-Oblique", alignment=TA_LEFT),
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
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        for i, (_, _, col) in enumerate(kpis):
            if col:
                cmds.append(("TEXTCOLOR", (i, 0), (i, 0), col))
        t.setStyle(TableStyle(cmds))
        return t

    def pain_card(num, titulo, euros, texto, color):
        numc = Table([[Paragraph(str(num), S["painnum"])]], colWidths=[1.0 * cm])
        numc.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), color),
                                  ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        eur = Table([[Paragraph(euros, S["eur"])], [Paragraph("AL MES", S["eurl"])]],
                    colWidths=[2.6 * cm])
        eur.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PANEL2),
                                 ("BOX", (0, 0), (-1, -1), 0.5, ROJO),
                                 ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                 ("TOPPADDING", (0, 0), (-1, -1), 3),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        top = Table([[Paragraph(titulo, S["paint"]), eur]],
                    colWidths=[W - 1.0 * cm - 2.6 * cm - 0.4 * cm, 2.6 * cm])
        top.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                 ("LEFTPADDING", (0, 0), (0, 0), 0)]))
        content = Table([[top], [Paragraph(texto, S["painb"])]], colWidths=[W - 1.0 * cm])
        content.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PANEL),
                                     ("LEFTPADDING", (0, 0), (-1, -1), 10),
                                     ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                                     ("TOPPADDING", (0, 0), (0, 0), 7),
                                     ("TOPPADDING", (1, 0), (1, 0), 2),
                                     ("BOTTOMPADDING", (0, -1), (-1, -1), 8)]))
        card = Table([[numc, content]], colWidths=[1.0 * cm, W - 1.0 * cm])
        card.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                  ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                  ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                  ("TOPPADDING", (0, 0), (-1, -1), 0),
                                  ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
        return KeepTogether([card, sp(0.2)])

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
            if set(st) <= set("-=*_~ #"):
                continue
            m = re.match(r"^#{1,6}\s*(.*)$", st)
            if m:
                rows.append([Paragraph(f"<b>{_md_inline(m.group(1))}</b>", S["copyh"])])
                continue
            if st.startswith("&gt;"):
                st = st[4:].strip()
            if st[:2] in ("- ", "* "):
                st = "&bull;&nbsp; " + st[2:]
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

    # ═══════════ PORTADA ═══════════
    story.append(sp(1.2))
    story.append(Paragraph("DOSSIER DE VENTA · CLIENTE FUNDADOR", S["psub"]))
    story.append(sp(0.15))
    story.append(Paragraph("Estetic Estil", S["ptit"]))
    story.append(sp(0.1))
    story.append(Paragraph("Centro de estética y peluquería · Vilanova i la Geltrú", S["psub"]))
    story.append(sp(0.3))
    story.append(hr(CYAN, 2.5))
    story.append(sp(0.3))
    story.append(Paragraph(
        "\"Uno de los centros de estética mejor valorados de Vilanova (4.9★)… "
        "al que solo puedes llegar llamando a un teléfono fijo en horario de tienda.\"",
        S["pfrase"]))
    story.append(sp(0.4))
    story.append(kpi_box([
        ("4.9★", "VALORACIÓN GOOGLE", VERDE),
        ("~81", "RESEÑAS REALES", VERDE),
        ("15/100", "MADUREZ DIGITAL", ROJO),
        ("93%", "PROB. DE CIERRE", VERDE),
        ("~2.760€", "PIERDE AL MES", ROJO),
    ], border=CYAN))
    story.append(sp(0.4))
    story.append(Paragraph(
        "Este documento es todo lo que necesitas para convertir Estetic Estil en el "
        "<b>primer cliente de MerakIA</b>: qué les duele, cuánto les cuesta, qué ofrecerles "
        "(ordenado por dolor y por facilidad de venta), a qué precio (oferta fundador "
        "irresistible), cómo abordarlos y qué decir exactamente en cada canal.", S["mini"]))
    story.append(sp(0.35))

    # por qué este, en una tabla-resumen
    story.append(section("Por qué este es EL primer cliente", GOLD))
    story.append(sp(0.2))
    razones = [
        ("Reputación de oro", "4.9★ con ~81 reseñas: la demanda ya existe y es real. No hay que crear mercado, solo dejar de perderlo."),
        ("Hueco digital enorme", "Sin web, sin WhatsApp, sin reservas online. Solo teléfono fijo + Instagram. El contraste con su reputación es la venta."),
        ("Dolor cuantificable", "~2.760€/mes que se escapan hoy. El retorno de arreglarlo es evidente y medible en semanas."),
        ("Decisor accesible", "Negocio local, dueña identificable (dirección de estética). Puedes entrar en persona. Sin comité de compras."),
        ("Sector prescriptor", "La estética funciona por boca-oreja. Un caso de éxito aquí abre la puerta al resto de Vilanova."),
    ]
    rrows = [[Paragraph(k, S["tcb"]), Paragraph(v, S["tc"])] for k, v in razones]
    rt = Table(rrows, colWidths=[4.2 * cm, 12.8 * cm])
    rt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL2),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [PANEL2, PANEL]),
        ("GRID", (0, 0), (-1, -1), 0.3, LINEA),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("TEXTCOLOR", (0, 0), (0, -1), GOLD),
    ]))
    story.append(rt)

    # ═══════════ RADIOGRAFÍA ═══════════
    story.append(PageBreak())
    story.append(section("1. Radiografía del negocio", CYAN))
    story.append(sp(0.25))
    story.append(Paragraph(
        "Estetic Estil es un centro de estética y peluquería en Carrer d'Olèrdola 43 "
        "(Vilanova i la Geltrú). Ofrece un abanico amplio de servicios —tratamientos "
        "faciales y corporales, depilación láser, manicura y pedicura, peluquería, "
        "preparación de novias— con un equipo veterano (más de 25 años de oficio). Abren "
        "de martes a viernes (9:30–19:00) y sábados por la mañana. Su reputación online es "
        "excelente: <b>4.9★ con unas 81 reseñas</b>, algo que muy pocos negocios de la zona "
        "tienen.", S["body"]))
    story.append(sp(0.2))
    story.append(Paragraph(
        "<b>El problema no es la calidad. Es la puerta de entrada.</b> Todo su prestigio "
        "vive en Google e Instagram, pero cuando alguien quiere dar el paso —reservar, "
        "preguntar un precio, consultar un tratamiento— se encuentra un muro: no hay web, "
        "no hay WhatsApp, no hay reserva online. Solo un teléfono fijo que suena en horario "
        "de tienda, cuando el equipo tiene las manos ocupadas con clientas. Ese muro, "
        "invisible para ellas, es una fuga de dinero constante.", S["body"]))
    story.append(sp(0.25))

    story.append(Paragraph("Fortalezas vs. huecos", S["h3"]))
    fvh = [
        [Paragraph("LO QUE YA HACEN BIEN (su palanca)", S["tch"]), Paragraph("LO QUE LES FALTA (tu oportunidad)", S["tch"])],
        [Paragraph("4.9★ y ~81 reseñas — prueba social de primera", S["tc"]),
         Paragraph("Sin web propia — invisibles en Google para quien no les conoce", S["tc"])],
        [Paragraph("Equipo experto y trato humano reconocido", S["tc"]),
         Paragraph("Sin WhatsApp — imposible escribirles; solo llamar", S["tc"])],
        [Paragraph("Cartera de servicios amplia (ticket ~400€)", S["tc"]),
         Paragraph("Sin reserva online — todo depende del teléfono", S["tc"])],
        [Paragraph("Instagram y Facebook activos", S["tc"]),
         Paragraph("Sin atención fuera de horario — cero respuesta noches/domingos", S["tc"])],
    ]
    fvht = Table(fvh, colWidths=[8.5 * cm, 8.5 * cm])
    fvht.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), PANEL), ("BACKGROUND", (1, 0), (1, 0), PANEL),
        ("TEXTCOLOR", (0, 0), (0, 0), VERDE), ("TEXTCOLOR", (1, 0), (1, 0), ROJO),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PANEL2, PANEL]),
        ("GRID", (0, 0), (-1, -1), 0.3, LINEA),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(fvht)
    story.append(sp(0.25))
    story.append(Paragraph("Verificado antes de contactar", S["h3"]))
    story.append(Paragraph(
        "Negocio real y activo (Google, Instagram, Facebook, Treatwell, bodas.net). "
        "Sin web propia y sin WhatsApp: confirmado. Atención 100% manual por teléfono "
        "fijo. <b>Único aviso:</b> algunas reseñas externas son de hace +1 año — comprueba "
        "en Google Maps la actividad reciente y que figure \"Abierto\" antes de ir. Todo "
        "lo demás apunta a un centro consolidado con una asignatura pendiente: lo digital.",
        S["mini"]))

    # ═══════════ DOLORES ═══════════
    story.append(PageBreak())
    story.append(section("2. Dónde pierden dinero (sus dolores)", ROJO))
    story.append(sp(0.15))
    story.append(Paragraph(
        "Ordenados de mayor a menor sangría. Cifras conservadoras sobre su volumen y un "
        "ticket medio de ~400€. No son para asustar: son para que, en la reunión, ellos "
        "mismos vean el agujero con sus propios números.", S["mini"]))
    story.append(sp(0.25))

    story.append(pain_card(
        1, "El agujero nocturno: la clienta que quería reservar y no pudo", "~1.800€",
        "Son las 22:30. Alguien ve vuestro Instagram, se enamora de un tratamiento y quiere "
        "reservar YA, en caliente. Busca vuestro WhatsApp: no hay. Busca vuestra web: no hay. "
        "Solo un teléfono cerrado hasta mañana. Y mañana… o ya se le ha pasado el impulso, o "
        "ya ha reservado en el centro de al lado que sí le respondió. Esto pasa decenas de "
        "veces al mes y nunca lo veis, porque <b>lo que no llega no hace ruido</b>. Es la "
        "fuga más grande y la más silenciosa.", ROJO))

    story.append(pain_card(
        2, "Invisibles para quien todavía no os conoce", "~960€",
        "Quien ya os conoce, os encuentra. Pero la persona nueva que busca en Google "
        "\"depilación láser Vilanova\" o \"tratamiento facial Vilanova\"… no os ve. Sin web, "
        "cedéis a ese cliente nuevo a la competencia que sí aparece —aunque vosotras seáis "
        "mejores y lo demuestren vuestras 81 reseñas. Estáis dejando que otros recojan la "
        "demanda que vuestra reputación genera.", AMBAR))

    story.append(pain_card(
        3, "Vuestro 4.9 trabaja a medio gas", "oculto",
        "81 reseñas de 4.9★ son oro puro: la mejor herramienta de venta que existe. Pero está "
        "encerrada dentro de Google. No está en una web que convenza a las 3 de la madrugada, "
        "no responde preguntas, no agenda citas. Tenéis el mejor argumento del mercado local "
        "guardado en un cajón. Un activo enorme, infrautilizado.", VIOLETA))

    story.append(pain_card(
        4, "Todo depende de manos que ya están ocupadas", "coste oculto",
        "Cada llamada la coge alguien que estaba atendiendo a una clienta en cabina. Cada "
        "consulta interrumpe un tratamiento o se pierde. El negocio no puede crecer más allá "
        "del número de horas que tenéis las manos libres para el teléfono. Automatizar la "
        "puerta de entrada no es quitar el trato humano: es liberarlo para donde de verdad "
        "importa —la clienta que tenéis delante.", CYAN))

    story.append(sp(0.1))
    story.append(Paragraph(
        "<b>Suma silenciosa: ~2.760€/mes.</b> Más de 33.000€ al año que no se pierden por "
        "hacerlo mal, sino por no tener por dónde entrar. La buena noticia: se arregla con "
        "un montaje, no con un milagro.", S["body"]))

    # ═══════════ ESCALERA DE SERVICIOS ═══════════
    story.append(PageBreak())
    story.append(section("3. Qué implementar (de mayor dolor a más fácil de vender)", VERDE))
    story.append(sp(0.2))
    story.append(Paragraph(
        "No se lo vendas todo a la vez. Esta es la <b>escalera</b>: entras por el escalón 1 "
        "(el que más duele y más fácil entra), demuestras resultados, y subes. Cada servicio "
        "está puntuado por dos ejes: <b>dolor que resuelve</b> y <b>facilidad de venta</b> "
        "(cuánto cuesta que digan que sí).", S["body"]))
    story.append(sp(0.25))

    head = ["#", "Servicio", "Dolor que resuelve", "Dolor", "Facilidad", "Tarifa normal"]
    esc = [
        ("1", "Agente IA en WhatsApp 24/7", "El agujero nocturno: responde, informa y agenda a cualquier hora",
         "MÁXIMO", "MÁXIMA", "900€ + 300€/mes"),
        ("2", "Ficha Google + motor de reseñas", "Refuerza y capitaliza el 4.9★; más visibilidad local ya",
         "Medio", "Muy alta", "300€ + 90€/mes"),
        ("3", "Web one-page de conversión", "Invisibilidad en Google; convierte la visita en cita",
         "Alto", "Media", "900€ (único)"),
        ("4", "Reservas online + recordatorios", "Fricción de reserva y no-shows; agenda que se llena sola",
         "Alto", "Media", "400€ + 120€/mes"),
        ("5", "Chatbot IA en la web 24/7", "Captura las visitas de la web fuera de horario",
         "Medio", "Media", "600€ + 150€/mes"),
        ("6", "CRM + fidelización/reactivación", "Retención: hacer volver a la clienta dormida",
         "Medio", "Baja", "500€ + 180€/mes"),
    ]
    erows = [[Paragraph(h, S["tch"]) for h in head]]
    for row in esc:
        n, serv, dolor, dnv, fnv, tar = row
        dcol = ROJO if dnv == "MÁXIMO" else (AMBAR if dnv == "Alto" else TENUE)
        fcol = VERDE if "MÁXIMA" in fnv or "Muy" in fnv else (AMBAR if fnv == "Media" else ROJO)
        erows.append([
            Paragraph(n, S["tcb"]),
            Paragraph(serv, S["tcb"]),
            Paragraph(dolor, S["tc"]),
            Paragraph(f'<font color="{dcol.hexval().replace("0x","#")}">{dnv}</font>', S["tc"]),
            Paragraph(f'<font color="{fcol.hexval().replace("0x","#")}">{fnv}</font>', S["tc"]),
            Paragraph(tar, S["tc"]),
        ])
    et = Table(erows, colWidths=[0.7 * cm, 3.6 * cm, 6.0 * cm, 1.7 * cm, 1.7 * cm, 3.3 * cm], repeatRows=1)
    et.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PANEL),
        ("TEXTCOLOR", (0, 0), (-1, 0), VERDE),
        ("GRID", (0, 0), (-1, -1), 0.3, LINEA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PANEL2, PANEL]),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#14243a")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("BOX", (0, 1), (-1, 1), 1, VERDE),
    ]))
    story.append(et)
    story.append(sp(0.2))
    story.append(Paragraph(
        "El <b>escalón 1 resaltado</b> es la punta de lanza y lo único que ofreces en la "
        "primera reunión. Es donde más dinero pierden y donde el \"sí\" es más fácil (no "
        "tienen NADA parecido, el gap es evidente y el resultado se ve en días). Los escalones "
        "2–6 son tu plan de crecimiento con este cliente durante los próximos meses: no los "
        "menciones como catálogo, aparecerán solos cuando el primero funcione.", S["mini"]))

    # ═══════════ LA OFERTA ═══════════
    story.append(PageBreak())
    story.append(section("4. La oferta irresistible: Plan Cliente Fundador", GOLD))
    story.append(sp(0.2))
    story.append(Paragraph(
        "Tu primera misión no es ganar dinero con este cliente: es <b>conseguir el cliente</b>. "
        "Un caso de éxito real y local vale mucho más que un margen. Así que la oferta está "
        "diseñada para que decir \"no\" sea más difícil que decir \"sí\".", S["body"]))
    story.append(sp(0.3))

    # caja de oferta
    of_price = Table([
        [Paragraph("PLAN CLIENTE FUNDADOR · Agente IA en WhatsApp 24/7", S["oflab"])],
        [Paragraph('Montaje: <strike>900€</strike> &nbsp; + &nbsp; Mes 1: <strike>300€</strike>', S["ofanc"])],
        [Paragraph("0€ de entrada", S["ofbig"])],
        [Paragraph("Primer mes GRATIS · después 150€/mes · <b>precio fundador congelado de por vida</b>", S["oflab"])],
        [Paragraph("sin permanencia &nbsp;·&nbsp; garantía total 30 días &nbsp;·&nbsp; lo monto yo entero", S["oflab"])],
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
    story.append(sp(0.3))

    story.append(Paragraph("Qué incluye, en cristiano", S["h3"]))
    incl = [
        "Agente de IA en un WhatsApp Business para el centro (lo creamos si no lo tienen).",
        "Responde al instante 24/7: informa de tratamientos y precios, resuelve dudas y agenda citas.",
        "Configurado con SU tono y SUS servicios — no un bot genérico y frío.",
        "Aviso al equipo solo cuando hace falta una persona de verdad. El resto, resuelto solo.",
        "Montaje, formación y ajustes: todo de mi lado. Ellas no tocan nada técnico.",
    ]
    for it in incl:
        story.append(Paragraph(f"&bull;&nbsp; {it}", S["bodyl"]))
    story.append(sp(0.25))

    story.append(Paragraph("La contrapartida (que la hace honesta, no un regalo sospechoso)", S["h3"]))
    story.append(Paragraph(
        "A cambio de este precio de fundador, cuando el sistema les funcione (que les "
        "funcionará) les pido tres cosas: <b>(1)</b> un testimonio en vídeo de 1 minuto, "
        "<b>(2)</b> permiso para enseñar su resultado a otras clínicas, y <b>(3)</b> que me "
        "presenten a 2 negocios de la zona que crean que también lo necesitan. No es un favor: "
        "es un trato. Ellas ganan el sistema casi gratis; yo gano mi primer caso de éxito.",
        S["body"]))
    story.append(sp(0.3))

    story.append(Paragraph("El martillo del retorno (memorízalo)", S["h3"]))
    story.append(Paragraph(
        "\"150€ al mes es menos de lo que cobráis por UN tratamiento. Si el agente os "
        "recupera UNA sola clienta al mes, ya se ha pagado dos o tres veces. Y ahora mismo "
        "se os están escapando entre 8 y 12. El mes que viene ya iríais en positivo.\"",
        S["quote"]))

    # ═══════════ PSICOLOGÍA DE LA OFERTA ═══════════
    story.append(PageBreak())
    story.append(section("5. Por qué esta oferta funciona (palancas de persuasión)", VIOLETA))
    story.append(sp(0.2))
    story.append(Paragraph(
        "No es \"barato porque sí\". Cada elemento activa una palanca psicológica. Entiéndelas "
        "y podrás improvisar sin perder el hilo:", S["body"]))
    story.append(sp(0.2))
    palancas = [
        ("Prueba social", "Arrancas SIEMPRE por su 4.9★. Reconoces lo que ya han ganado; bajan la guardia y se sienten vistos, no atacados."),
        ("Aversión a la pérdida", "Hablas de dinero que se ESCAPA, no de dinero que ganarían. Duele 2–3x más perder algo que dejar de ganarlo. Por eso todo va en clave de fuga."),
        ("Reciprocidad", "Les regalas el análisis (este dossier) y el montaje. Cuando das primero, la otra persona siente el impulso de corresponder."),
        ("Escasez / exclusividad", "\"Busco UNA clínica fundadora en Vilanova.\" Una sola plaza. Lo exclusivo se desea; lo ilimitado se pospone."),
        ("Reason-why (el porqué honesto)", "Explicas POR QUÉ es tan barato: acabas de arrancar y necesitas el caso, no el margen. La honestidad desarma la sospecha de \"¿dónde está la trampa?\"."),
        ("Anclaje de precio", "Enseñas 900€+300€ tachado ANTES del 0€. El cerebro juzga el precio contra el ancla: 150€ parece una ganga al lado de 300€."),
        ("Reversión del riesgo", "Mes gratis + garantía + sin permanencia. Quitas todo el miedo: el riesgo lo asumes tú, no ellas. Sin riesgo, no hay excusa para el \"no\"."),
        ("Autoridad y preparación", "Llegas con datos concretos y habiendo probado tú mismo el fallo (ver estrategia). Demuestras que has hecho los deberes: eres el experto, no un comercial más."),
        ("Coherencia (pequeños sí)", "El guion busca micro-acuerdos (\"¿os pasa esto?\", \"¿verdad?\"). Cada pequeño sí hace más natural el sí grande del final."),
    ]
    prows = [[Paragraph("Palanca", S["tch"]), Paragraph("Cómo la usas en esta venta", S["tch"])]]
    for k, v in palancas:
        prows.append([Paragraph(k, S["tcb"]), Paragraph(v, S["tc"])])
    pt = Table(prows, colWidths=[4.3 * cm, 12.7 * cm], repeatRows=1)
    pt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PANEL),
        ("TEXTCOLOR", (0, 0), (-1, 0), VIOLETA),
        ("GRID", (0, 0), (-1, -1), 0.3, LINEA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PANEL2, PANEL]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("TEXTCOLOR", (0, 1), (0, -1), GOLD),
    ]))
    story.append(pt)

    # ═══════════ ESTRATEGIA DE CONTACTO ═══════════
    story.append(PageBreak())
    story.append(section("6. Estrategia de abordaje (adaptada a que NO tienen WhatsApp)", CYAN))
    story.append(sp(0.2))
    story.append(Paragraph(
        "Aquí hay una ironía perfecta a tu favor: <b>vendes un canal de contacto moderno a un "
        "negocio al que casi no se puede contactar.</b> Úsalo. El propio problema es tu mejor "
        "argumento de entrada.", S["body"]))
    story.append(sp(0.25))

    story.append(Paragraph("El truco del cliente misterioso (hazlo ANTES de contactar)", S["h3"]))
    story.append(Paragraph(
        "Intenta reservar como lo haría una clienta real: busca su WhatsApp (no hay), su web "
        "(no hay), intenta reservar online de noche (imposible). Ese fracaso es tu apertura "
        "más potente: <i>\"El otro día quise pedir cita en vuestro centro por la noche y me di "
        "cuenta de que no había forma salvo llamar hoy. Con las reseñas que tenéis, ¿cuántas "
        "hacen lo mismo y ya no vuelven a llamar?\"</i> Imposible de rebatir, porque lo has "
        "vivido.", S["body"]))
    story.append(sp(0.25))

    story.append(Paragraph("Orden de canales (de más a menos potente para este caso)", S["h3"]))
    canales = [
        ("1. Visita en persona", "PRINCIPAL",
         "Es un salón local, ambiente cercano, entras sin gatekeeper corporativo. Llevas el dossier impreso, "
         "preguntas por la responsable (Sara / la dueña), sueltas el gancho del cliente misterioso y dejas la "
         "ficha. Objetivo: no vender ahí, sino conseguir 15–20 min con quien decide. La cara genera la confianza "
         "que un negocio sin clientes todavía necesita transmitir."),
        ("2. Instagram DM", "APOYO",
         "Están activos ahí. Un DM bien escrito llega directo a quien lleva las redes (a menudo la propia dueña). "
         "Sirve para calentar antes de la visita o para conseguir el nombre y el mejor momento. Además demuestra "
         "el punto: te han tenido que contestar por DM porque no hay otro canal."),
        ("3. Llamada al fijo", "RESERVA",
         "938 16 02 07. Contestará alguien entre clienta y clienta. No vendas por teléfono: identifica a la "
         "decisora y agenda. Llama en horas valle (media mañana entre semana), nunca a primera hora ni sábado."),
    ]
    crows = [[Paragraph("Canal", S["tch"]), Paragraph("Rol", S["tch"]), Paragraph("Cómo usarlo", S["tch"])]]
    for k, rol, v in canales:
        rc = VERDE if rol == "PRINCIPAL" else (CYAN if rol == "APOYO" else TENUE)
        crows.append([Paragraph(k, S["tcb"]),
                      Paragraph(f'<font color="{rc.hexval().replace("0x","#")}">{rol}</font>', S["tc"]),
                      Paragraph(v, S["tc"])])
    ct = Table(crows, colWidths=[3.0 * cm, 2.0 * cm, 12.0 * cm], repeatRows=1)
    ct.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PANEL),
        ("TEXTCOLOR", (0, 0), (-1, 0), CYAN),
        ("GRID", (0, 0), (-1, -1), 0.3, LINEA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PANEL2, PANEL]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(ct)
    story.append(sp(0.25))

    story.append(Paragraph("Estructura de la reunión de 15–20 min", S["h3"]))
    reunion = [
        "1. Rapport (2 min): elogia el centro y su 4.9★. Genuino. Que se sientan reconocidas.",
        "2. Diagnóstico compartido (5 min): enséñales el agujero con SUS números. Deja que ellas calculen en voz alta.",
        "3. La solución (5 min): UNA cosa —el agente de WhatsApp 24/7. Enseña cómo se vería para ellas.",
        "4. La oferta fundador (3 min): ancla el precio normal, revela el 0€ + mes gratis, explica el porqué.",
        "5. Cierre (2 min): \"¿Lo montamos esta semana o la que viene?\" Dos opciones, ninguna es \"no\".",
    ]
    for it in reunion:
        story.append(Paragraph(f"&bull;&nbsp; {it}", S["bodyl"]))

    # ═══════════ TEXTOS ═══════════
    story.append(PageBreak())
    story.append(section("7. Textos listos para usar (copiar y adaptar)", VERDE))
    story.append(sp(0.2))

    ig = (
        "Hola! Os escribo por aquí porque… he intentado encontrar vuestra web o WhatsApp "
        "para preguntaros por un tratamiento y no ha habido manera 😅 Solo el fijo, y estaba "
        "cerrado.\n\n"
        "Y justo de eso os quería hablar: soy [Nombre], de MerakIA, aquí en Vilanova. Ayudo a "
        "centros como el vuestro —con una reputación buenísima (¡ese 4.9 es de premio!) pero "
        "difíciles de contactar fuera de hora— a no perder esas clientas que escriben de "
        "noche y no encuentran cómo reservar.\n\n"
        "¿Quién lleva las decisiones del centro? Me encantaría enseñaros en 15 min una forma "
        "de arreglarlo casi sin coste. Sin compromiso, y si no lo veis, tan amigos 💙"
    )
    story.extend(copy_box("Primer contacto (calienta o consigue a la decisora)", ig, VIOLETA, "Instagram DM"))

    visita = (
        "**AL ENTRAR**\n"
        "\"Hola, buenas. ¿Está Sara o la responsable del centro? Soy [Nombre], soy de aquí de "
        "Vilanova. No vengo a venderos nada ahora mismo, tranquilas —traigo una cosa preparada "
        "para vosotras y prefiero dárosla en mano. ¿Tenéis 2 minutos o vuelvo en mejor rato?\"\n\n"
        "**EL GANCHO (cliente misterioso)**\n"
        "\"Os cuento en 20 segundos por qué me he pasado en persona: el otro día quise mirar "
        "cómo reservar en vuestro centro por la noche y me di cuenta de que no hay forma —ni "
        "web, ni WhatsApp— salvo llamar en horario. Y con las 81 reseñas de 4.9 que tenéis… "
        "imaginad cuánta gente hace eso y ya no vuelve a llamar al día siguiente.\"\n\n"
        "**LA TRANSICIÓN**\n"
        "\"He preparado un pequeño análisis de cuánto puede estar costándoos eso al mes, y una "
        "forma de arreglarlo casi sin coste porque busco mi primer caso aquí en Vilanova. ¿Os "
        "lo enseño con calma 15 minutos esta semana? ¿Os va mejor jueves o viernes por la "
        "mañana?\"\n\n"
        "**AL SALIR (siempre)**\n"
        "Deja el dossier impreso. Apunta el nombre de la decisora y el mejor momento para "
        "volver. Si no está: \"¿Cuándo suele estar Sara? Vuelvo encantado, sin prisa.\""
    )
    story.extend(copy_box("Guion de visita en persona (canal principal)", visita, VERDE, "Visita"))

    llamada = (
        "**APERTURA**\n"
        "\"Hola, buenas, ¿con quién tengo el gusto? [nombre]. Encantado [nombre]. Oye, "
        "seguramente esto no lo decides tú y no pasa nada —¿me puedes decir quién lleva la "
        "gestión del centro y cuándo la puedo encontrar un momento?\"\n\n"
        "**SI TE PASAN / SI ES ELLA**\n"
        "\"Te robo 40 segundos. He estado mirando vuestro centro: 4.9 en Google con 81 "
        "reseñas, un nivel altísimo. Y precisamente por eso me llamó la atención una cosa: "
        "fuera de vuestro horario, quien quiere reservar no tiene ni web ni WhatsApp, solo "
        "este fijo cerrado. Con vuestra reputación, cada noche eso son clientas que se van a "
        "la competencia. ¿Os habíais fijado en ese hueco?\"\n\n"
        "**CIERRE (siempre a reunión, nunca a venta por teléfono)**\n"
        "\"No te vendo nada por teléfono. Lo suyo es que os enseñe 15 minutos, con vuestros "
        "números, cuánto se está escapando y cómo se arregla —y os lo pongo muy fácil porque "
        "busco mi primer caso en Vilanova. ¿Os paso mejor jueves o viernes por la mañana?\"\n\n"
        "**Cuándo llamar:** martes a viernes, media mañana (10:30–12:00). Nunca a primera hora "
        "ni sábado."
    )
    story.extend(copy_box("Guion de llamada al fijo (reserva)", llamada, CYAN, "Llamada"))

    # ═══════════ OBJECIONES + CIERRE ═══════════
    story.append(PageBreak())
    story.append(section("8. Objeciones frecuentes y cómo desactivarlas", AMBAR))
    story.append(sp(0.2))
    obj = [
        ("\"No tenemos tiempo para más cosas\"",
         "\"Lo entiendo, por eso mismo os llamo. El agente es justo para que tengáis MENOS trabajo, "
         "no más: coge él las consultas mientras vosotras estáis en cabina. Y el montaje lo hago yo "
         "entero, vosotras no tocáis nada.\""),
        ("\"No entiendo de tecnología / no es lo mío\"",
         "\"Ni falta que hace. Ese es mi trabajo. Vosotras solo veréis las citas entrando. Lo dejo "
         "montado, funcionando y explicado en cristiano.\""),
        ("\"Ya nos va bien así\"",
         "\"Y se nota, por eso tenéis ese 4.9. Precisamente por eso: imaginad yendo bien pero sin "
         "perder a nadie por el camino. Lo que ya no llega no se ve, y ahí es donde entro yo.\""),
        ("\"¿La IA no será fría o impersonal?\"",
         "\"Buena pregunta —en estética el trato lo es todo. Por eso lo configuro con VUESTRO tono, y "
         "en cuanto hace falta una persona os avisa. La IA cubre el hueco de las noches; el trato "
         "humano lo dais vosotras donde importa, en la cabina.\""),
        ("\"¿Cuánto cuesta?\" (¡buena señal!)",
         "\"Te lo digo claro y te va a gustar: normalmente son 900€ de montaje y 300 al mes. Pero "
         "busco mi primera clínica fundadora en Vilanova, así que a la primera que diga sí: montaje "
         "gratis, primer mes gratis, y 150€/mes congelados de por vida. Sin permanencia. Si no os "
         "trae clientas, lo quito y no me debéis nada.\""),
        ("\"Me lo tengo que pensar\"",
         "\"Claro, faltaría más. Y justo para que no tengáis que pensarlo a ciegas, el primer mes es "
         "gratis: lo probáis con clientas reales y decidís con resultados delante, no con mi palabra. "
         "¿Lo dejamos montado y lo veis funcionando esta semana?\""),
    ]
    orows = [[Paragraph("Si te dicen…", S["tch"]), Paragraph("Respondes…", S["tch"])]]
    for k, v in obj:
        orows.append([Paragraph(k, S["tcb"]), Paragraph(v, S["tc"])])
    ot = Table(orows, colWidths=[4.6 * cm, 12.4 * cm], repeatRows=1)
    ot.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PANEL),
        ("TEXTCOLOR", (0, 0), (-1, 0), AMBAR),
        ("GRID", (0, 0), (-1, -1), 0.3, LINEA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PANEL2, PANEL]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("TEXTCOLOR", (0, 1), (0, -1), ROSAL),
    ]))
    story.append(ot)
    story.append(sp(0.3))

    story.append(Paragraph("Checklist antes de ir", S["h3"]))
    chk = [
        "Comprobar en Google Maps que está \"Abierto\" y con actividad reciente.",
        "Hacer el test del cliente misterioso (buscar web/WhatsApp/reserva y fallar).",
        "Mirar su Instagram: último post, tratamientos que promocionan ahora (para personalizar).",
        "Llevar el dossier impreso + tarjeta/contacto tuyo.",
        "Tener claro el número: pierden ~2.760€/mes; oferta 0€ + mes gratis + 150€/mes fundador.",
        "Mentalidad: no vas a vender, vas a conseguir 15 minutos. Un solo objetivo.",
    ]
    for it in chk:
        story.append(Paragraph(f"&bull;&nbsp; {it}", S["bodyl"]))
    story.append(sp(0.4))

    story.append(hr(GOLD, 2))
    story.append(sp(0.2))
    story.append(Paragraph("No busques la venta perfecta. Busca el primer sí.", S["ptit"]))
    story.append(sp(0.25))
    story.append(Paragraph(
        "Estetic Estil no necesita que le expliques qué es la IA. Necesita dejar de perder "
        "clientas cada noche. Tú tienes la solución y un precio que no tiene excusa. "
        "Lo único que falta es que llames a esa puerta. Hazlo esta semana.", S["pfrase"]))

    doc.build(story, onFirstPage=_bg, onLaterPages=_bg, canvasmaker=Cnv)
    print(f"OK -> {OUTPUT}")


if __name__ == "__main__":
    build()
