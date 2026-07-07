# -*- coding: utf-8 -*-
"""
Premortem — MerakIA Agency & ChefMenu AI
Genera premortem_merakia_chefmenu.pdf (informe visual oscuro, escaneable).

Metodologia Gary Klein: asumimos que es enero de 2027, ambos proyectos han
fracasado, y trabajamos hacia atras para explicar por que murieron.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle,
    Spacer, HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from pathlib import Path

# ── Paleta premortem (oscuro forense) ───────────────────────────────────────
FONDO    = colors.HexColor("#0a0e1a")   # azul noche
PANEL    = colors.HexColor("#121829")   # panel
PANEL2   = colors.HexColor("#0f1422")   # panel alterno
LINEA    = colors.HexColor("#26304a")
TEXTO    = colors.HexColor("#cdd6e8")
TENUE    = colors.HexColor("#8a96b0")
BLANCO   = colors.white

ROJO     = colors.HexColor("#ef4444")   # peligro / alta
AMBAR    = colors.HexColor("#f5a623")   # probable / media
VERDE    = colors.HexColor("#34d399")   # bajo / ok
CYAN     = colors.HexColor("#2de2e6")   # marca agencia
VIOLETA  = colors.HexColor("#8b5cf6")
GOLD     = colors.HexColor("#e4b85c")   # marca

# acentos por tarjeta
ACENTOS = [colors.HexColor("#ef4444"), colors.HexColor("#f5a623"),
           colors.HexColor("#2de2e6"), colors.HexColor("#8b5cf6"),
           colors.HexColor("#34d399"), colors.HexColor("#ec4899")]

OUTPUT = Path(__file__).parent / "premortem_merakia_chefmenu.pdf"
W = 17 * cm


def _draw_bg(cnv, doc):
    """Fondo oscuro a pagina completa. Se ejecuta ANTES de los flowables
    (via onFirstPage/onLaterPages), de modo que el contenido queda encima."""
    pw, ph = A4
    cnv.saveState()
    cnv.setFillColor(FONDO)
    cnv.rect(0, 0, pw, ph, fill=1, stroke=0)
    cnv.restoreState()


class FondoCanvas(canvas.Canvas):
    """Pasada diferida: solo dibuja el pie (encima del contenido) con el
    total de paginas. El fondo lo pinta _draw_bg, no esta clase."""
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
        pw, ph = A4
        if self._pageNumber <= 1:
            return
        self.saveState()
        self.setFillColor(TENUE)
        self.setFont("Helvetica", 6.5)
        self.drawString(2 * cm, 0.9 * cm,
                        "Premortem — MerakIA Agency & ChefMenu AI · Confidencial")
        self.drawRightString(pw - 2 * cm, 0.9 * cm, f"{self._pageNumber} / {n}")
        self.setStrokeColor(LINEA)
        self.setLineWidth(0.5)
        self.line(2 * cm, 1.15 * cm, pw - 2 * cm, 1.15 * cm)
        self.restoreState()


def build():
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4,
        topMargin=1.6 * cm, bottomMargin=1.6 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title="Premortem — MerakIA Agency & ChefMenu AI",
        author="Analisis estrategico",
    )
    base = getSampleStyleSheet()

    def stl(name, **kw):
        return ParagraphStyle(name, parent=base["Normal"], **kw)

    S = {
        "ptit":  stl("ptit", fontSize=30, textColor=BLANCO, fontName="Helvetica-Bold",
                     alignment=TA_CENTER, leading=34),
        "psub":  stl("psub", fontSize=12.5, textColor=GOLD, fontName="Helvetica-Bold",
                     alignment=TA_CENTER, spaceAfter=4),
        "pdesc": stl("pdesc", fontSize=9.5, textColor=TENUE, alignment=TA_CENTER, leading=14),
        "h1":    stl("h1", fontSize=18, textColor=BLANCO, fontName="Helvetica-Bold",
                     spaceBefore=2, spaceAfter=4, leading=22),
        "h1n":   stl("h1n", fontSize=9, textColor=GOLD, fontName="Helvetica-Bold",
                     spaceAfter=2),
        "h2":    stl("h2", fontSize=12.5, textColor=BLANCO, fontName="Helvetica-Bold",
                     spaceBefore=10, spaceAfter=4, leading=16),
        "h3":    stl("h3", fontSize=10.5, textColor=GOLD, fontName="Helvetica-Bold",
                     spaceBefore=6, spaceAfter=3, leading=14),
        "body":  stl("body", fontSize=9, leading=13.5, textColor=TEXTO, alignment=TA_JUSTIFY),
        "bodyl": stl("bodyl", fontSize=9, leading=13.5, textColor=TEXTO),
        "lead":  stl("lead", fontSize=10, leading=15, textColor=TEXTO, alignment=TA_JUSTIFY),
        "tc":    stl("tc", fontSize=8, leading=11.5, textColor=TEXTO),
        "tcb":   stl("tcb", fontSize=8, leading=11.5, textColor=BLANCO, fontName="Helvetica-Bold"),
        "tch":   stl("tch", fontSize=8, leading=11, textColor=BLANCO, fontName="Helvetica-Bold"),
        "card_t":stl("card_t", fontSize=11, textColor=BLANCO, fontName="Helvetica-Bold", leading=14),
        "card_h":stl("card_h", fontSize=7.5, textColor=TENUE, fontName="Helvetica-Bold"),
        "card_b":stl("card_b", fontSize=8.5, leading=12.5, textColor=TEXTO, alignment=TA_JUSTIFY),
        "badge": stl("badge", fontSize=7.5, textColor=BLANCO, fontName="Helvetica-Bold",
                     alignment=TA_CENTER),
        "kpi":   stl("kpi", fontSize=19, textColor=GOLD, fontName="Helvetica-Bold",
                     alignment=TA_CENTER),
        "kpil":  stl("kpil", fontSize=7, textColor=TENUE, alignment=TA_CENTER, leading=9),
        "quote": stl("quote", fontSize=11, leading=16, textColor=BLANCO,
                     fontName="Helvetica-Bold", alignment=TA_CENTER),
        "mini":  stl("mini", fontSize=7.5, textColor=TENUE, leading=10),
        "chip":  stl("chip", fontSize=6.8, textColor=BLANCO, fontName="Helvetica-Bold",
                     alignment=TA_CENTER, leading=8),
    }

    def sp(h=0.3):
        return Spacer(1, h * cm)

    def hr(color=LINEA, t=1):
        return HRFlowable(width="100%", thickness=t, color=color, spaceAfter=4)

    def P(txt, s="tc"):
        return Paragraph(txt, S[s])

    # badge de nivel (ALTA/MEDIA/BAJA) ---------------------------------------
    def badge(nivel):
        col = {"ALTA": ROJO, "MEDIA": AMBAR, "BAJA": VERDE,
               "MUY ALTA": ROJO, "CRITICO": ROJO}.get(nivel, AMBAR)
        t = Table([[Paragraph(nivel, S["badge"])]], colWidths=[2.0 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), col),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("ROUNDEDCORNERS", [3, 3, 3, 3]),
        ]))
        return t

    # tabla generica ---------------------------------------------------------
    def tabla(data, widths, header_bg=PANEL, head_color=GOLD):
        wrapped = []
        for ri, row in enumerate(data):
            nr = []
            for cell in row:
                if isinstance(cell, (Table, Paragraph)):
                    nr.append(cell)
                elif ri == 0:
                    nr.append(Paragraph(str(cell), S["tch"]))
                else:
                    nr.append(Paragraph(str(cell), S["tc"]))
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

    def caja(texto, border=GOLD, bg=PANEL, s="body"):
        t = Table([[Paragraph(texto, S[s])]], colWidths=[W])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("BOX", (0, 0), (-1, -1), 1.2, border),
            ("LEFTPADDING", (0, 0), (-1, -1), 11),
            ("RIGHTPADDING", (0, 0), (-1, -1), 11),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ]))
        return t

    def kpi_row(kpis, border=LINEA):
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

    def seccion(num, titulo):
        return [PageBreak(),
                Paragraph(f"// {num}", S["h1n"]),
                Paragraph(titulo, S["h1"]),
                hr(GOLD, 2), sp(0.2)]

    # tarjeta de modo de fallo ----------------------------------------------
    def tarjeta_fallo(codigo, titulo, prob, impacto, acento,
                      historia, supuesto, senales):
        # cabecera: codigo + titulo
        cab = Table([[Paragraph(f'<b>{codigo}</b>', S["card_t"]),
                      Paragraph(titulo, S["card_t"])]],
                    colWidths=[1.4 * cm, W - 1.4 * cm])
        cab.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), acento),
            ("BACKGROUND", (1, 0), (1, -1), PANEL),
            ("TEXTCOLOR", (0, 0), (0, -1), FONDO),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (1, 0), (1, -1), 9),
        ]))
        # fila prob / impacto
        pi = Table([[Paragraph("PROBABILIDAD", S["card_h"]), badge(prob),
                     Paragraph("IMPACTO", S["card_h"]), badge(impacto)]],
                   colWidths=[3.0 * cm, 2.3 * cm, 2.0 * cm, 2.3 * cm])
        pi.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (0, -1), 0),
        ]))
        # cuerpo
        cuerpo_rows = [
            [Paragraph("LA HISTORIA DEL FALLO", S["card_h"])],
            [Paragraph(historia, S["card_b"])],
            [Paragraph("EL SUPUESTO QUE LO HIZO POSIBLE", S["card_h"])],
            [Paragraph(supuesto, S["card_b"])],
            [Paragraph("SEÑALES DE ALERTA TEMPRANA", S["card_h"])],
            [Paragraph(senales, S["card_b"])],
        ]
        cuerpo = Table(cuerpo_rows, colWidths=[W])
        cuerpo.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PANEL2),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (0, 0), 7),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
            ("LINEBELOW", (0, 1), (-1, 1), 0.4, LINEA),
            ("LINEBELOW", (0, 3), (-1, 3), 0.4, LINEA),
        ]))
        cont = Table([[cab], [pi], [cuerpo]], colWidths=[W])
        cont.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LINEABOVE", (0, 1), (-1, 1), 0.4, LINEA),
            ("BACKGROUND", (0, 1), (-1, 1), PANEL),
            ("LEFTPADDING", (0, 1), (-1, 1), 9),
            ("BOX", (0, 0), (-1, -1), 1.2, acento),
        ]))
        return KeepTogether([cont, sp(0.4)])

    story = []

    # ═══════════════ PORTADA ═══════════════
    story.append(sp(2.2))
    story.append(Paragraph("PREMORTEM", S["psub"]))
    story.append(sp(0.15))
    story.append(Paragraph("Por qué fracasaron", S["ptit"]))
    story.append(Paragraph("MerakIA &amp; ChefMenu AI", S["ptit"]))
    story.append(sp(0.35))
    story.append(hr(GOLD, 2.5))
    story.append(sp(0.25))
    story.append(Paragraph(
        "Un análisis forense del futuro. Asumimos que es enero de 2027, "
        "ambos proyectos han fracasado, y trabajamos hacia atrás para entender "
        "por qué — antes de que ocurra.", S["pdesc"]))
    story.append(sp(1.0))
    port = [
        ["Método", "Premortem de Gary Klein (retrospectiva prospectiva)"],
        ["Objeto", "Agencia MerakIA + SaaS ChefMenu AI, antes de lanzar"],
        ["Fecha de análisis", "27 de junio de 2026"],
        ["Horizonte simulado", "Enero de 2027 (+6 meses)"],
        ["Modos de fallo detectados", "13 (6 agencia · 6 ChefMenu · 1 transversal)"],
    ]
    tp = Table([[Paragraph(r[0], S["tcb"]), Paragraph(r[1], S["tc"])] for r in port],
               colWidths=[4.5 * cm, 12.5 * cm])
    tp.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), PANEL),
        ("BACKGROUND", (1, 0), (1, -1), PANEL2),
        ("TEXTCOLOR", (0, 0), (0, -1), GOLD),
        ("GRID", (0, 0), (-1, -1), 0.5, LINEA),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(tp)
    story.append(sp(0.9))
    story.append(caja(
        "<b>Por qué este informe es incómodo (y por eso útil).</b> Un premortem "
        "no busca razones para que tu plan funcione: asume que ya murió y te obliga "
        "a explicar cómo. No está suavizado. Si algo aquí te molesta, probablemente "
        "es justo donde debes mirar.", border=ROJO, bg=PANEL))

    # ═══════════════ 00 CÓMO LEER ═══════════════
    story += seccion("00", "Cómo leer este informe")
    story.append(Paragraph(
        "Este documento aplica la técnica del <b>premortem</b>: en lugar de preguntar "
        "\"¿es buen plan?\" (lo que genera respuestas complacientes), declara el plan "
        "muerto y reconstruye la autopsia. El psicólogo Gary Klein lo publicó en "
        "Harvard Business Review; Daniel Kahneman lo llamó su técnica favorita para "
        "tomar decisiones. Google y Goldman Sachs lo usan antes de apuestas grandes.", S["body"]))
    story.append(sp(0.2))
    story.append(Paragraph("Estructura", S["h3"]))
    story.append(Paragraph(
        "<b>1. Síntesis ejecutiva</b> — lo único que tienes que leer si solo tienes 5 minutos: "
        "el fallo más probable, el más peligroso y el supuesto oculto de cada proyecto.<br/>"
        "<b>2. Mapa de los 13 modos de fallo</b> — panorama de un vistazo con su gravedad.<br/>"
        "<b>3. MerakIA Agency</b> — fortalezas/debilidades + 6 tarjetas de fallo + plan revisado.<br/>"
        "<b>4. ChefMenu AI</b> — fortalezas/debilidades + 6 tarjetas de fallo + plan revisado.<br/>"
        "<b>5. El riesgo transversal</b> — el hallazgo que conecta ambos fracasos.<br/>"
        "<b>6. Plan de acción 30/60/90 días</b> — qué hacer esta semana.", S["bodyl"]))
    story.append(sp(0.3))
    story.append(Paragraph("Cómo leer cada tarjeta de fallo", S["h3"]))
    story.append(Paragraph(
        "Cada modo de fallo lleva dos medidores: <b>PROBABILIDAD</b> (qué tan posible es) "
        "e <b>IMPACTO</b> (cuánto daño haría). Debajo: la historia de cómo se desarrolló, "
        "el supuesto que lo hizo posible, y las señales de alerta que podrías vigilar para "
        "detectarlo a tiempo.", S["body"]))

    # ═══════════════ 01 SÍNTESIS ═══════════════
    story += seccion("01", "Síntesis ejecutiva")
    story.append(caja(
        "<b>EL HALLAZGO CENTRAL.</b> Ni MerakIA ni ChefMenu mueren por un defecto técnico. "
        "Mueren por la misma causa: <b>un fundador único repartido entre 7 proyectos "
        "\"terminados\" y 0 clientes que pagan.</b> Tienes una capacidad de construir "
        "excepcional y un motor de distribución y venta inexistente. El cuello de botella "
        "no es el código — ya tienes de sobra. Es conseguir que alguien pague.",
        border=ROJO, bg=colors.HexColor("#1a0f12"), s="lead"))
    story.append(sp(0.35))

    story.append(Paragraph("Diagnóstico rápido por proyecto", S["h2"]))
    sint = [
        ["", "MerakIA Agency", "ChefMenu AI"],
        ["Fallo más probable",
         "Construir sin vender: 9 servicios definidos, web online, pero 0 clientes "
         "y 0 casos de éxito que mostrar.",
         "El chef de menú del día no paga ni lo usa más allá de la novedad. "
         "Churn brutal tras el trial."],
        ["Fallo más peligroso",
         "Un agente de voz falla en una clínica real: citas perdidas, cliente "
         "furioso, mala reseña pública justo cuando vives del boca a boca.",
         "Error de la IA en un alérgeno + reacción de un comensal. "
         "Responsabilidad legal y fin del producto."],
        ["Supuesto oculto",
         "Que el cuello de botella es construir el producto. El cuello real "
         "es la distribución y la confianza.",
         "Que existe un dolor agudo de planificación que el chef quiere pagar "
         "por resolver. En menú del día ese dolor es tenue."],
    ]
    story.append(tabla(sint, [3.0 * cm, 7.0 * cm, 7.0 * cm]))
    story.append(sp(0.35))

    story.append(Paragraph("La única revisión más importante", S["h2"]))
    story.append(caja(
        "<b>Elige UN solo proyecto para los próximos 90 días</b> y pon los otros seis en "
        "modo mantenimiento (congelados, sin tocar). Para el elegido, <b>invierte el ratio "
        "de tu tiempo: 80% distribución y venta, 20% producto.</b> Y redefine \"éxito\": "
        "no es \"producto terminado\", es <b>\"el primer cliente que paga con su tarjeta\".</b> "
        "Hasta que eso ocurra, ningún proyecto está realmente \"completo\".",
        border=GOLD, bg=colors.HexColor("#1a1500"), s="lead"))
    story.append(sp(0.3))
    story.append(Paragraph(
        "El resto del informe sostiene esta conclusión con 13 modos de fallo concretos y un "
        "plan revisado para cada proyecto. Si solo actúas sobre una cosa, que sea la de arriba.",
        S["body"]))

    # ═══════════════ 02 MAPA DE FALLOS ═══════════════
    story += seccion("02", "Mapa de los 13 modos de fallo")
    story.append(Paragraph(
        "Panorama completo de un vistazo. Cada celda es un modo de fallo con su gravedad "
        "(combinación de probabilidad e impacto). Las tarjetas detalladas vienen después.", S["body"]))
    story.append(sp(0.25))

    def chip_grid(items, titulo, color):
        story.append(Paragraph(titulo, S["h3"]))
        rows = []
        row = []
        for i, (cod, txt, sev) in enumerate(items):
            sevcol = {"ALTA": ROJO, "MEDIA": AMBAR, "BAJA": VERDE}[sev]
            cell = Table([[Paragraph(f"<b>{cod}</b>", S["chip"])],
                          [Paragraph(txt, S["chip"])],
                          [Paragraph(sev, S["chip"])]],
                         colWidths=[(W - 0.6 * cm) / 3])
            cell.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), PANEL),
                ("BACKGROUND", (0, 2), (-1, 2), sevcol),
                ("BOX", (0, 0), (-1, -1), 1, color),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            row.append(cell)
            if len(row) == 3:
                rows.append(row)
                row = []
        if row:
            while len(row) < 3:
                row.append("")
            rows.append(row)
        g = Table(rows, colWidths=[(W) / 3] * 3)
        g.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(g)
        story.append(sp(0.3))

    chip_grid([
        ("A1", "Construir en vez de vender", "ALTA"),
        ("A2", "Web que no convierte (contacto placeholder)", "ALTA"),
        ("A3", "Cero prueba social / casos de éxito", "ALTA"),
        ("A4", "La entrega no escala con un fundador", "MEDIA"),
        ("A5", "Comoditización: no-code más barato", "MEDIA"),
        ("A6", "Fallo en producción daña la reputación", "ALTA"),
    ], "MerakIA Agency — 6 modos", CYAN)

    chip_grid([
        ("C1", "Brecha MVP→SaaS subestimada (meses, no semanas)", "ALTA"),
        ("C2", "El chef no paga ni percibe el dolor", "ALTA"),
        ("C3", "La IA no encaja con cómo se cocina de verdad", "ALTA"),
        ("C4", "CAC > LTV: las cuentas no salen", "ALTA"),
        ("C5", "Riesgo legal de alérgenos", "MEDIA"),
        ("C6", "Dos productos en uno: foco diluido", "MEDIA"),
    ], "ChefMenu AI — 6 modos", VERDE)

    chip_grid([
        ("T1", "Fundador único entre 7 proyectos: ninguno alcanza masa crítica", "ALTA"),
    ], "Transversal — el hallazgo maestro", GOLD)

    # ═══════════════ 03 MERAKIA ═══════════════
    story += seccion("03", "MerakIA Agency")
    story.append(Paragraph(
        "<b>Qué es:</b> agencia de IA para pymes españolas. Vende agentes de voz, chatbots 24/7, "
        "recordatorios/anti no-show, gestión de reseñas, webs y automatización (ticket objetivo "
        "1.500–4.500 €/mes). Web pública desplegada en merakia-web.vercel.app con chat de captación. "
        "Nichos diana: clínicas dentales/estética, inmobiliarias y restaurantes.<br/>"
        "<b>Cómo se ve el éxito:</b> cartera de clientes recurrentes que pagan miles de euros al mes "
        "por servicios entregados y mantenidos.", S["body"]))
    story.append(sp(0.3))

    story.append(Paragraph("Fortalezas reales", S["h3"]))
    story.append(tabla([
        ["Fortaleza", "Por qué importa"],
        ["Velocidad de construcción",
         "Puedes montar productos (ProspectorIA, agente WhatsApp, web) que a otras agencias les "
         "llevaría meses y un equipo. Es una ventaja genuina de oferta."],
        ["Herramientas propias de prospección",
         "ProspectorIA (scorecard, benchmark de nicho, pérdida en €/mes) es un activo de venta "
         "real: llegas a la reunión con un diagnóstico cuantificado que casi nadie lleva."],
        ["Análisis de nicho hecho",
         "Tienes mapeados dolores, tickets y argumentarios por sector. La materia prima comercial "
         "ya existe."],
        ["Posicionamiento emocional diferenciado",
         "\"Poner el alma en la IA\" destaca en un mar de agencias técnicas frías — si se respalda "
         "con resultados."],
    ], [4.3 * cm, 12.7 * cm]))
    story.append(sp(0.25))
    story.append(Paragraph("Debilidades estructurales", S["h3"]))
    story.append(tabla([
        ["Debilidad", "Consecuencia si no se corrige"],
        ["0 clientes y 0 casos de éxito",
         "Vendes \"ROI demostrable\" sin nada que demostrar. El CAC se dispara y el ciclo se alarga."],
        ["Web con datos placeholder",
         "Contacto y métricas sin rellenar = el visitante no puede confiar ni convertir."],
        ["Entrega dependiente de una sola persona",
         "Cada cliente nuevo te consume horas de implementación y soporte. Saturación a los 2-3 clientes."],
        ["Oferta demasiado amplia",
         "9 servicios = ningún mensaje afilado. \"Hacemos de todo\" no posiciona."],
        ["Sin proceso de ventas repetible",
         "Sin pipeline, sin cadencia de seguimiento, sin meta semanal de prospección, no hay flujo de leads."],
    ], [4.3 * cm, 12.7 * cm], head_color=ROJO))
    story.append(sp(0.3))
    story.append(Paragraph("Los 6 modos de fallo en detalle", S["h2"]))
    story.append(sp(0.1))

    tarjetas_agencia = [
        ("A1", "Construyes producto en vez de vender", "ALTA", "ALTA", ACENTOS[0],
         "Durante seis meses la energía se fue donde es más cómoda y gratificante: construir. "
         "Saliste de cada semana con una feature nueva, un nicho más analizado, una web más pulida. "
         "Pero la venta —incómoda, llena de \"no\", lenta— se pospuso siempre para \"cuando el producto "
         "esté listo\". El producto nunca estuvo \"listo\" porque siempre había algo más que mejorar. "
         "En enero de 2027 la agencia tiene nueve servicios impecables y cero facturas emitidas.",
         "Que vender es la recompensa de construir, cuando en realidad es al revés: construir solo "
         "tiene sentido cuando hay alguien esperando para pagar.",
         "Pasan semanas sin una sola conversación de venta agendada. Tu métrica de progreso es "
         "\"features enviadas\", no \"reuniones con prospectos\" ni \"propuestas enviadas\"."),
        ("A2", "La web no genera confianza ni convierte", "ALTA", "MEDIA", ACENTOS[1],
         "La web salió a producción con el chat funcionando, pero la sección de contacto seguía con "
         "datos de relleno y las métricas eran números aspiracionales inventados. Los pocos visitantes "
         "que llegaron no encontraron un teléfono real, ni un caso verificable, ni un nombre con cara. "
         "El chat captó algún lead suelto, pero como no había un proceso para atenderlos en minutos, "
         "se enfriaron. La web parecía un escaparate de algo que aún no existe.",
         "Que tener la web \"online\" equivale a tener la web \"funcionando como canal de captación\". "
         "Publicar no es convertir.",
         "Los datos de contacto siguen siendo placeholder semanas después del despliegue. Nadie revisa "
         "ni responde los leads del chat el mismo día. Analytics muestra visitas pero 0 contactos."),
        ("A3", "Cero prueba social en un negocio de pura confianza", "ALTA", "ALTA", ACENTOS[2],
         "Cada prospecto hizo la misma pregunta —\"¿con quién habéis trabajado?\"— y la respuesta honesta "
         "era \"con nadie todavía\". En servicios B2B donde el cliente entrega su atención al cliente y su "
         "reputación a un tercero, sin un solo testimonio real la venta se vuelve cuesta arriba. "
         "Los descuentos para compensar la falta de confianza erosionaron el margen, y aun así los cierres "
         "no llegaban. El boca a boca, tu canal más barato, nunca arrancó porque no había un primer cliente "
         "satisfecho que lo iniciara.",
         "Que un buen producto y un buen discurso bastan para cerrar. En confianza B2B, la prueba social "
         "de terceros pesa más que cualquier demo.",
         "En las reuniones, la objeción recurrente es \"enséñame un caso\". Tu material de venta usa "
         "métricas genéricas del sector, no resultados tuyos con nombre y apellido."),
        ("A4", "La entrega no escala con un solo fundador", "MEDIA", "ALTA", ACENTOS[3],
         "Los primeros clientes llegaron —y ahí empezó el problema real. Cada agente de voz requería "
         "configurar integraciones, conectar el calendario, ajustar el guion, probar casos límite y luego "
         "mantenerlo. Con dos o tres cuentas activas, el día se llenó de soporte y configuración, y no "
         "quedó tiempo para vender. El crecimiento se frenó solo: para conseguir más clientes hacía falta "
         "tiempo que la entrega devoraba. Contratar requería ingresos que aún no existían.",
         "Que vender y entregar son fases separadas. Para un fundador solo, compiten por las mismas horas "
         "desde el primer cliente.",
         "Tras cerrar 2-3 clientes, tus semanas se llenan de incidencias y onboarding. La prospección "
         "cae a cero sin que lo decidas. Empiezas a temer cerrar el siguiente cliente."),
        ("A5", "Comoditización: compites contra no-code más barato", "MEDIA", "MEDIA", ACENTOS[4],
         "El prospecto medio ya había oído hablar de chatbots y agentes de voz. Algunos habían probado "
         "ManyChat, Voiceflow o Synthflow por su cuenta, o conocían a otra agencia más barata. Tu "
         "diferenciador —\"alma en la IA\"— sonaba bonito pero no respondía a \"¿por qué tú y no la "
         "herramienta de 30 €/mes?\". Sin un resultado medible y propio que enseñar, la conversación "
         "derivó a precio, y en precio no puedes ganar siendo artesanal.",
         "Que el cliente compra tecnología de IA. En realidad compra un resultado de negocio; la "
         "tecnología es un commodity y el \"alma\" no es defendible si no produce números.",
         "Los prospectos mencionan herramientas que ya usan o agencias más baratas. La conversación gira "
         "hacia el precio antes que hacia el resultado. Te piden rebajas para cerrar."),
        ("A6", "Un fallo en producción destruye la reputación", "ALTA", "ALTA", ACENTOS[5],
         "El agente de voz de una clínica dental dejó de coger llamadas un sábado por un cambio en una API "
         "de terceros. Durante el fin de semana se perdieron citas y nadie lo detectó hasta el lunes. El "
         "cliente —que te había confiado su primera impresión ante sus pacientes— se dio de baja furioso y "
         "lo contó en su grupo de hosteleros/dentistas. En un negocio que depende del boca a boca, una sola "
         "historia de terror pesó más que diez promesas. La responsabilidad de un sistema \"que trabaja "
         "mientras duermes\" recayó sobre ti 24/7, sin guardia ni respaldo.",
         "Que \"funciona en la demo\" es \"funciona en producción\". Los sistemas autónomos fallan en "
         "silencio y el daño reputacional es asimétrico: un fallo borra muchos aciertos.",
         "No tienes monitorización ni alertas de caída de los agentes en cliente. No hay SLA escrito ni "
         "plan de contingencia. Dependes de APIs de terceros sin fallback."),
    ]
    for t in tarjetas_agencia:
        story.append(tarjeta_fallo(*t))

    story.append(Paragraph("Plan revisado — MerakIA", S["h2"]))
    story.append(tabla([
        ["Cambio concreto", "Ataca"],
        ["Rellena HOY contacto real (teléfono, email, LinkedIn, cara) y quita métricas inventadas. "
         "Sin esto, todo lo demás es inútil.", "A2"],
        ["Consigue 1 cliente ANCLA gratis o casi gratis a cambio de un caso de éxito documentado "
         "(vídeo + métricas antes/después) antes de gastar 1 € en ads.", "A1, A3"],
        ["Reduce la oferta a UN nicho (clínicas dental/estética) y UN servicio estrella "
         "(anti no-show / recordatorios: el de ROI más fácil de demostrar). Vende eso, no nueve cosas.",
         "A5"],
        ["Productiza la entrega: oferta fija, instalable en X días, precio cerrado, checklist de "
         "onboarding repetible. Así puedes entregar sin morir y, más tarde, delegar.", "A4"],
        ["Antes de poner un agente en producción: monitorización + alertas de caída, SLA por escrito, "
         "fallback humano y plan de contingencia. Nunca un cliente sin red.", "A6"],
        ["Fija una meta semanal de prospección (p.ej. 20 contactos / 5 reuniones) y mídela como "
         "tu North Star, por encima de cualquier feature.", "A1"],
    ], [13.5 * cm, 3.5 * cm], head_color=CYAN))
    story.append(sp(0.3))
    story.append(Paragraph("Checklist pre-lanzamiento — MerakIA", S["h3"]))
    story.append(caja(
        "☐ Datos de contacto reales y verificables en la web (no placeholder).<br/>"
        "☐ Al menos 1 caso de éxito real con métricas y permiso para publicarlo.<br/>"
        "☐ Un nicho y un servicio elegidos, con un argumentario y un precio cerrados.<br/>"
        "☐ Proceso de entrega documentado (checklist) que un tercero podría seguir.<br/>"
        "☐ Monitorización + SLA + plan de contingencia para cualquier sistema en cliente.",
        border=CYAN, bg=PANEL, s="bodyl"))

    # ═══════════════ 04 CHEFMENU ═══════════════
    story += seccion("04", "ChefMenu AI")
    story.append(Paragraph(
        "<b>Qué es:</b> SaaS que genera el menú del día con IA, controla el food cost (escandallo), "
        "gestiona alérgenos y aprovecha la despensa. Hoy es un MVP en Streamlit + SQLite + Claude API "
        "(monousuario, sin login ni billing). Tiers planeados: Básico 29 € · Pro 59 € · Chain 199 € · "
        "Gourmet 249 €.<br/>"
        "<b>Cómo se ve el éxito (según tu plan):</b> 500 restaurantes de pago y ~25.000 €/mes de MRR "
        "en 12 meses; break-even operativo el mes 9.", S["body"]))
    story.append(sp(0.3))

    story.append(Paragraph("Fortalezas reales", S["h3"]))
    story.append(tabla([
        ["Fortaleza", "Por qué importa"],
        ["Conocimiento del dominio",
         "Vienes de hostelería: entiendes escandallo, mermas, alérgenos y la realidad de una cocina. "
         "Eso se nota en el producto y en la venta."],
        ["MVP funcional ya construido",
         "Puedes hacer demos reales hoy. No vendes humo: el generador, el escandallo y las fichas existen."],
        ["Plan de negocio detallado",
         "Tienes pricing, fases, KPIs y canales pensados. La mayoría lanza sin nada de esto."],
        ["Ángulo legal como gancho",
         "El cumplimiento de alérgenos (Reg. UE 1169/2011) es un dolor real y obligatorio: buena cuña "
         "de entrada... si se gestiona con cuidado (ver C5)."],
    ], [4.3 * cm, 12.7 * cm]))
    story.append(sp(0.25))
    story.append(Paragraph("Debilidades estructurales", S["h3"]))
    story.append(tabla([
        ["Debilidad", "Consecuencia si no se corrige"],
        ["Distancia enorme MVP → SaaS vendible",
         "Sin multi-tenant, login ni billing no hay producto que cobrar. Y eso son meses, no semanas."],
        ["Cliente de bajo ARPU y poco digital",
         "El bar de menú del día paga poco y se resiste al software. Unit economics frágiles."],
        ["Valor de la IA aún no validado con pago",
         "Generar menús \"óptimos\" gusta en demo; falta probar que un chef lo use y pague cada mes."],
        ["Dos públicos en un solo producto",
         "Menú del día (29 €) y alta cocina (249 €) son negocios distintos. Perseguir ambos diluye foco."],
        ["Promesa de alérgenos demasiado absoluta",
         "\"Garantiza el cumplimiento\" es una afirmación peligrosa si la IA se equivoca."],
    ], [4.3 * cm, 12.7 * cm], head_color=ROJO))
    story.append(sp(0.3))
    story.append(Paragraph("Los 6 modos de fallo en detalle", S["h2"]))
    story.append(sp(0.1))

    tarjetas_chef = [
        ("C1", "La brecha MVP→SaaS estaba subestimada", "ALTA", "ALTA", ACENTOS[0],
         "El plan decía \"3-4 semanas\" para pasar de Streamlit a un SaaS de verdad. Pero multi-tenancy, "
         "login, aislamiento de datos por restaurante, integración de Stripe, recuperación de contraseña, "
         "gestión de tiers y un hosting que no se caiga son, para una sola persona, dos a cuatro meses de "
         "trabajo serio. El lanzamiento se retrasó mes tras mes, la novedad se enfrió, otros proyectos "
         "reclamaron atención, y el SaaS nunca llegó a producción. El MVP siguió siendo una demo bonita "
         "que nadie podía comprar.",
         "Que la distancia entre \"funciona en mi máquina para mí\" y \"lo usan y pagan 100 desconocidos a "
         "la vez\" es pequeña. Es la parte más cara del producto.",
         "El plazo de \"lanzar el SaaS\" se desliza repetidamente. Sigues sin login ni cobro semanas "
         "después de la fecha objetivo. Empiezas a tocar otro proyecto \"mientras tanto\"."),
        ("C2", "El chef de menú del día no paga ni percibe el dolor", "ALTA", "ALTA", ACENTOS[1],
         "Los pilotos probaron la app, asintieron en la demo… y cuando llegó el momento de poner la tarjeta, "
         "la mayoría no lo hizo. El dueño de un bar de menú del día improvisa con lo que hay en la cámara y "
         "con lo que sabe hacer; no vive la planificación como un dolor que justifique 29-59 €/mes. "
         "\"Ya lo tengo en la cabeza, gratis\" fue la objeción que no supiste vencer. La conversión de "
         "trial a pago se quedó muy por debajo del 25% planeado y el churn devoró la base.",
         "Que el dolor que tú ves (food cost, rotación, tiempo) lo siente con la misma intensidad el "
         "segmento más informal y de menor ticket. No es así.",
         "En los pilotos, alta participación en la demo pero baja disposición a introducir tarjeta. "
         "Te piden que sea gratis. La retención en la semana 4 cae por debajo del 40%."),
        ("C3", "La IA no encaja con cómo se cocina de verdad", "ALTA", "ALTA", ACENTOS[2],
         "En la demo, el menú generado impresionaba. En la cocina real, el chef cocina con SUS proveedores, "
         "SU carta, SU criterio y lo que hay HOY en la cámara. Un menú \"óptimo\" que propone platos que él "
         "no hace, con ingredientes que no tiene, se percibió como un juguete, no como una herramienta de "
         "trabajo. Tras la novedad de las primeras semanas, dejaron de abrir la app: seguía siendo más "
         "rápido decidir el menú como siempre. El uso semanal —tu North Star— se desplomó.",
         "Que el chef quiere que la IA decida el menú. En realidad quiere una herramienta que respete su "
         "criterio y le quite trabajo mecánico (escandallo, fichas, alérgenos), no que le diga qué cocinar.",
         "El uso cae tras la 2ª-3ª semana. El feedback dice \"está guay pero no lo uso\". Las funciones más "
         "usadas son las utilitarias (escandallo, fichas), no la generación de menús."),
        ("C4", "Las cuentas no salen: CAC mayor que LTV", "ALTA", "ALTA", ACENTOS[3],
         "Para crecer hiciste lo que decía el plan: Meta y Google Ads. Pero con un coste por lead de "
         "10-15 €, una conversión baja a pago y un cliente que paga 40 €/mes y se va en dos o tres meses, "
         "cada cliente costaba más de lo que dejaba. Gastar 500-800 €/mes en ads para adquirir cuentas que "
         "no se amortizan fue quemar caja. Sin ese gasto, el crecimiento se paró. Con él, la pérdida se "
         "aceleró. El modelo no tenía una vía rentable de adquisición.",
         "Que un ARPU bajo se compensa con volumen. Con churn alto y CAC de pago, el volumen agrava la "
         "pérdida en vez de arreglarla.",
         "El coste de adquirir un cliente supera 2-3 meses de su cuota. El churn mensual se mantiene por "
         "encima del 8-10%. El payback por cliente nunca baja del año."),
        ("C5", "Un error de alérgenos con consecuencias legales", "MEDIA", "MUY ALTA", ACENTOS[4],
         "El material decía que ChefMenu \"garantiza el cumplimiento de alérgenos\". Un día la IA etiquetó "
         "mal un plato —omitió las trazas de frutos secos— y un comensal con alergia tuvo una reacción "
         "grave. De pronto la conversación no era de software sino de responsabilidad civil: el restaurante "
         "señaló a la herramienta en la que confió, y la palabra \"garantiza\" en tu web se convirtió en "
         "una prueba en tu contra. Sin seguro ni disclaimers férreos, un único incidente bastó para "
         "terminar con el producto y abrir un frente legal.",
         "Que la IA puede asumir una responsabilidad que es legalmente del restaurador. La IA puede "
         "asistir, nunca \"garantizar\".",
         "Tu copy usa verbos absolutos (\"garantiza\", \"asegura\") sobre alérgenos. No hay disclaimer de "
         "validación humana ni términos de servicio que limiten responsabilidad. No tienes seguro."),
        ("C6", "Dos productos en uno diluyen el foco", "MEDIA", "MEDIA", ACENTOS[5],
         "Intentaste servir a la vez al bar de menú del día (Básico 29 €) y a la bistronomía/alta cocina "
         "(Gourmet 249 €, escandallo de degustación). Son dos compradores distintos, con dolores, lenguaje "
         "y canales distintos. La web, las demos y los anuncios intentaron hablarle a ambos y no calaron en "
         "ninguno. Cada euro de marketing y cada hora de producto se repartió entre dos batallas, y ninguna "
         "se ganó. La promesa quedó borrosa: \"¿esto para quién es exactamente?\".",
         "Que un mismo producto con tiers cubre dos mercados. Distintos compradores necesitan distinto "
         "producto, mensaje y distribución.",
         "Tu mensaje necesita explicar a dos públicos a la vez. Las demos se adaptan demasiado según con "
         "quién hablas. No sabrías decir en una frase para quién es ChefMenu."),
    ]
    for t in tarjetas_chef:
        story.append(tarjeta_fallo(*t))

    story.append(Paragraph("Plan revisado — ChefMenu", S["h2"]))
    story.append(tabla([
        ["Cambio concreto", "Ataca"],
        ["NO construyas el SaaS todavía. Primero valida el PAGO con el MVP actual operado en modo "
         "concierge (tú metes los datos). Objetivo: 5 restaurantes que paguen de verdad antes de invertir "
         "meses en multi-tenant.", "C1, C2"],
        ["Haz una prueba de humo de precio: ofrece el producto a 10-15 chefs reales a 39-59 €/mes y mide "
         "cuántos sacan la tarjeta. Si menos de 3, el problema es la demanda, no el producto.", "C2, C4"],
        ["Reposiciona el valor: vende la herramienta que QUITA trabajo mecánico (escandallo, fichas, "
         "alérgenos) y respeta el criterio del chef — no la que \"decide el menú\".", "C3"],
        ["Elige UN segmento. Recomendación: aquel al que tengas acceso directo y conozcas mejor. "
         "Un producto, un comprador, un mensaje.", "C6"],
        ["Cambia \"garantiza alérgenos\" por \"asistente que sugiere; el chef valida\". Añade disclaimer "
         "de validación humana y términos de servicio que limiten responsabilidad. Valora un seguro.", "C5"],
        ["Recalcula la unit economics con churn realista (8-10% mensual) ANTES de gastar en ads. "
         "Si el CAC supera 3 meses de cuota, el canal de pago no es viable: prioriza orgánico/referido.", "C4"],
    ], [13.5 * cm, 3.5 * cm], head_color=VERDE))
    story.append(sp(0.3))
    story.append(Paragraph("Checklist pre-lanzamiento — ChefMenu", S["h3"]))
    story.append(caja(
        "☐ 5 restaurantes que YA pagan con el MVP en modo concierge (prueba de demanda real).<br/>"
        "☐ Retención de uso > 40% en la semana 4 de los pilotos (no solo altas).<br/>"
        "☐ Un solo segmento objetivo definido en una frase.<br/>"
        "☐ Copy de alérgenos revisado: nada de \"garantiza\"; disclaimer + validación humana.<br/>"
        "☐ Unit economics con churn realista que demuestren LTV > 3× CAC antes de invertir en ads.",
        border=VERDE, bg=PANEL, s="bodyl"))

    # ═══════════════ 05 TRANSVERSAL ═══════════════
    story += seccion("05", "El riesgo transversal: el fundador único")
    story.append(caja(
        "<b>T1 — El hallazgo maestro.</b> Tienes siete proyectos construidos —MerakIA, ChefMenu, "
        "ProspectorIA, VideoStudio, Financial Analyzer, Alertas/Trading y Agente WhatsApp Citas— "
        "y, hasta donde refleja todo el material, <b>cero ingresos recurrentes de clientes.</b> "
        "Este no es un detalle: es el patrón que explica por qué ambos proyectos fracasan en la "
        "simulación.", border=GOLD, bg=colors.HexColor("#1a1500"), s="lead"))
    story.append(sp(0.3))
    story.append(tarjeta_fallo(
        "T1", "Siete proyectos, ningún cliente: la dispersión", "ALTA", "MUY ALTA", GOLD,
        "Cada proyecto, por separado, fue una buena decisión: aprendiste, construiste algo real y "
        "ampliaste tu abanico. Pero sumados consumieron el único recurso que de verdad escaseaba: tu "
        "atención sostenida. Ninguno recibió los meses ininterrumpidos de venta, iteración con clientes "
        "y pulido comercial que hacen falta para cruzar de \"terminado\" a \"alguien paga\". A los seis "
        "meses tenías siete activos al 80% y ninguno al 100% con caja. La sensación de productividad "
        "—commits, features, demos— enmascaró la ausencia del único indicador que importa: ingresos. "
        "Cada vez que un proyecto se ponía difícil (la parte de vender), había otro proyecto nuevo y "
        "limpio al que saltar.",
        "Que tener muchos proyectos \"terminados\" reduce el riesgo por diversificación. En realidad lo "
        "multiplica: divide el foco, que es el recurso escaso, y retrasa el único aprendizaje que "
        "importa —si alguien paga— en todos a la vez.",
        "Tu lista de proyectos crece más rápido que tu lista de clientes. Mides progreso en features, no "
        "en facturas. Cuando un proyecto llega a la fase de vender, sientes el tirón de empezar uno nuevo."),
    )
    story.append(Paragraph("La decisión que lo cambia todo", S["h2"]))
    story.append(caja(
        "<b>Secuencia, no paralelo.</b> Elige UNO para los próximos 90 días. Criterio sugerido: el que "
        "tenga el camino más corto a un cliente que paga, dado tu acceso y tu red. Los otros seis se "
        "congelan: cero desarrollo, sin culpa. No los abandonas; los aparcas para volver con foco cuando "
        "el primero genere caja.", border=GOLD, bg=PANEL, s="lead"))
    story.append(sp(0.25))
    story.append(Paragraph("¿Cuál elegir primero? Un marco de decisión", S["h3"]))
    story.append(tabla([
        ["Criterio", "MerakIA Agency", "ChefMenu AI"],
        ["Tiempo hasta el primer pago", "Corto: puedes facturar un servicio sin construir SaaS",
         "Largo: necesita SaaS o venta concierge primero"],
        ["Ticket / valor por cliente", "Alto (1.500–4.500 €/mes)", "Bajo (29–59 €/mes)"],
        ["Esfuerzo de entrega por cliente", "Alto y manual", "Bajo una vez hecho el SaaS"],
        ["Tu ventaja personal", "Herramientas de prospección propias", "Conocimiento de hostelería"],
        ["Veredicto", "Mejor para caja rápida con pocos clientes",
         "Mejor a largo plazo, pero valida pago primero"],
    ], [3.6 * cm, 6.7 * cm, 6.7 * cm], head_color=GOLD))
    story.append(sp(0.2))
    story.append(Paragraph(
        "<b>Recomendación:</b> si necesitas validar que puedes generar ingresos cuanto antes, "
        "<b>MerakIA con un nicho y un servicio</b> es el camino más corto a la primera factura "
        "(ticket alto, sin SaaS que construir). ChefMenu es una apuesta válida a más largo plazo, "
        "pero solo después de probar con dinero real que los chefs pagan. Sea cual sea tu elección, "
        "lo decisivo es que sea <b>una</b>.", S["body"]))

    # ═══════════════ 06 PLAN 30/60/90 ═══════════════
    story += seccion("06", "Plan de acción — 30 / 60 / 90 días")
    story.append(Paragraph(
        "Concreto y secuenciado. Asume que eliges UN proyecto (el marco anterior te ayuda). "
        "Este plan está escrito para el camino MerakIA; si eliges ChefMenu, sustituye \"vender servicio\" "
        "por \"validar pago concierge\" en los mismos plazos.", S["body"]))
    story.append(sp(0.25))

    story.append(Paragraph("Días 1–30 · Quitar excusas y conseguir el primer SÍ", S["h3"]))
    story.append(caja(
        "1. Congela formalmente los otros 6 proyectos (una nota a ti mismo cuenta).<br/>"
        "2. Arregla la web: contacto real, fuera métricas inventadas.<br/>"
        "3. Elige 1 nicho + 1 servicio estrella. Escribe la oferta en una frase y un precio.<br/>"
        "4. Usa ProspectorIA para generar una lista de 40 prospectos de ese nicho.<br/>"
        "5. Cierra 1 cliente ancla (gratis/casi gratis) a cambio de caso de éxito documentado.",
        border=GOLD, bg=PANEL, s="bodyl"))
    story.append(sp(0.15))
    story.append(Paragraph("Días 31–60 · Convertir el caso en máquina de venta", S["h3"]))
    story.append(caja(
        "6. Documenta el resultado del cliente ancla (vídeo + métricas antes/después).<br/>"
        "7. Productiza la entrega: checklist de onboarding repetible y SLA por escrito.<br/>"
        "8. Fija meta semanal de prospección (p.ej. 20 contactos / 5 reuniones) y mídela.<br/>"
        "9. Monta monitorización + alertas para cualquier sistema que pongas en cliente.<br/>"
        "10. Objetivo: 2-3 clientes de pago con la oferta ya cerrada.",
        border=GOLD, bg=PANEL, s="bodyl"))
    story.append(sp(0.15))
    story.append(Paragraph("Días 61–90 · Estabilizar antes de ampliar", S["h3"]))
    story.append(caja(
        "11. Revisa unit economics reales: ¿cuánto cuesta y cuánto deja cada cliente?<br/>"
        "12. Decide: ¿escalar este servicio, añadir un segundo, o delegar entrega?<br/>"
        "13. Solo si hay caja recurrente estable, plantéate descongelar un 2º proyecto.<br/>"
        "14. Revisa este premortem: ¿qué señales de alerta se han activado?",
        border=GOLD, bg=PANEL, s="bodyl"))
    story.append(sp(0.35))

    story.append(Paragraph("La métrica que lo gobierna todo", S["h2"]))
    story.append(caja(
        "<b>North Star: número de clientes que pagan.</b> No commits, no features, no proyectos "
        "\"completos\". Si esta semana ese número no se movió ni tuviste 5 conversaciones de venta, "
        "la semana fue de construcción cómoda, no de negocio. El premortem entero se resume en mover "
        "ese número de 0 a 1, y luego de 1 a 3.",
        border=ROJO, bg=colors.HexColor("#1a0f12"), s="lead"))

    # ── CIERRE ──
    story.append(PageBreak())
    story.append(sp(3))
    story.append(Paragraph("No tienes un problema de producto.", S["quote"]))
    story.append(sp(0.3))
    story.append(Paragraph("Tienes un problema de foco y de venta.", S["quote"]))
    story.append(sp(0.5))
    story.append(hr(GOLD, 2))
    story.append(sp(0.4))
    story.append(Paragraph(
        "Y esa es, con diferencia, la mejor clase de problema que un constructor puede tener: "
        "significa que la parte difícil —saber hacer cosas— ya la dominas. Ahora elige una, "
        "y véndela hasta que alguien pague.", S["pdesc"]))
    story.append(sp(0.8))
    story.append(Paragraph(
        "Premortem generado el 27 de junio de 2026 · Método Gary Klein · "
        "Documento de trabajo confidencial", S["mini"]))

    doc.build(story, onFirstPage=_draw_bg, onLaterPages=_draw_bg,
              canvasmaker=FondoCanvas)
    print(f"OK -> {OUTPUT}")


if __name__ == "__main__":
    build()
