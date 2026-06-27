"""
Anexo estrategico -- Extension de ChefMenu AI a Alta Cocina
Genera anexo_alta_cocina_chefmenu.pdf
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle,
    Spacer, HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER
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
MORADO   = colors.HexColor("#6a1b9a")

OUTPUT = Path(__file__).parent / "anexo_alta_cocina_chefmenu.pdf"
W = 17 * cm


class FooterCanvas(canvas.Canvas):
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
        self.drawString(2 * cm, 0.38 * cm, "ChefMenu AI -- Anexo de Extension a Alta Cocina")
        self.setFillColor(colors.HexColor("#90a4ae"))
        self.drawRightString(pw - 2 * cm, 0.38 * cm, f"Pag. {self._pageNumber} / {n}")
        self.restoreState()


def build():
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title="ChefMenu AI -- Anexo Alta Cocina",
        author="MerakIA Agency",
    )

    base = getSampleStyleSheet()

    def st(name, **kw):
        return ParagraphStyle(name, parent=base["Normal"], **kw)

    S = {
        "ptit":   st("ptit", fontSize=30, textColor=BLANCO, fontName="Helvetica-Bold",
                     alignment=TA_CENTER, leading=34),
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
        "kpi":    st("kpi", fontSize=20, textColor=DORADO, fontName="Helvetica-Bold",
                     alignment=TA_CENTER),
        "kpi_l":  st("kpil", fontSize=7.5, textColor=colors.HexColor("#90a4ae"),
                     alignment=TA_CENTER, leading=10),
        "alerta": st("alert", fontSize=8.8, textColor=DORADO, fontName="Helvetica-Bold",
                     leading=13),
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

    def caja(texto, bg=GRIS_OSC, border=VERDE):
        data = [[Paragraph(texto, S["alerta"])]]
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
            ("BOX", (0, 0), (-1, -1), 1, DORADO),
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

    # ── PORTADA ──────────────────────────────────────────────────────────────
    story.append(sp(3))
    story.append(Paragraph("ChefMenu AI", S["ptit"]))
    story.append(sp(0.4))
    story.append(hr(DORADO, 3))
    story.append(sp(0.2))
    story.append(Paragraph("ANEXO ESTRATEGICO -- EXTENSION A ALTA COCINA", S["psub"]))
    story.append(sp(0.3))
    story.append(Paragraph(
        "Como llevar ChefMenu AI del menu del dia a la cocina gastronomica y de estrella Michelin: "
        "segmentacion, reposicionamiento del producto, nuevos modulos, pricing y captacion.",
        S["pdesc"]))
    story.append(sp(1.5))

    port_data = [
        ["Tesis", "La IA cambia de rol: de CREAR menus a AUDITAR costes y margen"],
        ["Dolor diana", "Escandallo real con merma de producto caro + coste de menu degustacion"],
        ["Mercado de entrada", "Bistronomiia / gastrobar (8.000-12.000 locales), no la estrella pura"],
        ["Rol de la estrella", "Prestigio de marca, no volumen de ingresos"],
        ["Estado", "Modulo Alta Cocina ya construido en el MVP"],
        ["Documento", "Anexo 1.0 -- complementa el Plan de Lanzamiento -- Junio 2025"],
    ]
    tp = Table([[_pb(r[0]), _p(r[1])] for r in port_data],
               colWidths=[4 * cm, 13 * cm])
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
    story.append(Paragraph("MerakIA Agency -- Confidencial", S["pdesc"]))

    # ── 01 LA TESIS ──────────────────────────────────────────────────────────
    story += seccion("01", "LA TESIS: MISMO MOTOR, ROL INVERTIDO DE LA IA")
    story.append(Paragraph(
        "ChefMenu AI nacio para el menu del dia, donde el chef quiere que la IA <b>le quite trabajo</b>: "
        "que genere el menu por el. En alta cocina ese planteamiento no encaja -- el menu degustacion "
        "es la identidad y la firma del chef, su obra. La IA no debe inventarlo.", S["body"]))
    story.append(sp(0.2))
    story.append(caja(
        "El insight que lo cambia todo: en alta cocina la IA no CREA, AUDITA. El chef pone su arte; "
        "ChefMenu AI controla el food cost pase a pase, calcula la merma del producto caro, valida "
        "la progresion del menu y senala exactamente donde se pierde el margen. Mismo motor, rol invertido.",
        bg=colors.HexColor("#1a1500"), border=DORADO))
    story.append(sp(0.3))
    story.append(Paragraph("Por que el dolor es mas agudo aqui que en ningun otro restaurante", S["h2"]))
    story.append(tabla(
        [
            ["Factor", "Menu del dia", "Alta cocina", "Implicacion"],
            ["Coste de producto", "Bajo / estable", "Alto y volatil",
             "Un error de escandallo cuesta mucho mas que en el menu del dia"],
            ["Merma del producto", "Moderada", "Brutal (40-65%)",
             "El rendimiento real define el margen; ignorarlo destruye la rentabilidad"],
            ["Numero de pases", "3", "8-16",
             "El coste se acumula pase a pase y es dificil de controlar sin herramienta"],
            ["Margen por error", "Centimos", "Euros por pase",
             "Sin control de costes se pierde la rentabilidad del negocio rapidamente"],
            ["Ficha tecnica", "Opcional", "Obligatoria",
             "Ya la hacen hoy en Excel complejo; ChefMenu AI lo automatiza"],
        ],
        [3 * cm, 2.8 * cm, 2.8 * cm, 8.4 * cm], header_bg=AZUL))

    # ── 02 SEGMENTACION ──────────────────────────────────────────────────────
    story += seccion("02", "SEGMENTACION: DONDE ESTA REALMENTE EL DINERO")
    story.append(Paragraph(
        "Atacar directamente las estrellas Michelin es un error estrategico: el mercado es diminuto "
        "y el ciclo de venta lentisimo. El valor real esta en el segmento intermedio -- numeroso, "
        "con el mismo dolor y sin pudor ante la tecnologia.", S["body"]))
    story.append(sp(0.25))
    story.append(tabla(
        [
            ["Segmento", "Tamano Espana", "Ticket / pax", "Dolor coste", "Encaje producto"],
            ["Estrella Michelin", "~250-300", "120-300 EUR", "Maximo",
             "Prestigio de marca, no volumen de ingresos"],
            ["Bistronomiia / gastrobar", "8.000-12.000", "35-80 EUR", "Muy alto",
             "LA DIANA PRINCIPAL -- volumen + dolor + tecnologia sin tabues"],
            ["Carta media-alta / autor", "15.000+", "25-50 EUR", "Alto",
             "Volumen + dolor claro en escandallo"],
            ["Hoteles, catering, eventos", "Miles", "Menus cerrados", "Alto a escala",
             "Escandallo a volumen, integracion con banquetes"],
        ],
        [3.5 * cm, 2.8 * cm, 2.3 * cm, 2.3 * cm, 6.1 * cm],
        row_colors=[(2, colors.HexColor("#1b3a1b"))]))
    story.append(sp(0.25))
    story.append(kpi_row([
        ("~300", "estrellas Michelin\n(prestigio)"),
        ("8-12k", "bistronomiia\n(diana real)"),
        ("15k+", "carta de autor\n(volumen)"),
        ("249 EUR", "precio tier\nGourmet/mes"),
    ]))
    story.append(sp(0.25))
    story.append(caja(
        "Regla de oro del go-to-market: vende a la bistronomiia para crecer, consigue 2-3 estrellas "
        "para tener prestigio de marca. Una sola cocina con estrella usando ChefMenu AI te da "
        "credibilidad para venderle a las 12.000 de abajo. La estrella es marketing; la bistronomiia es caja."))

    # ── 03 NUEVOS MODULOS ────────────────────────────────────────────────────
    story += seccion("03", "REPOSICIONAMIENTO DEL PRODUCTO: NUEVOS MODULOS")
    story.append(Paragraph(
        "El tier Gourmet activa funciones que ya estan construidas en el MVP mas una hoja de ruta de "
        "mejoras. Todas comparten la misma filosofia: la IA como copiloto analitico, no como creador.",
        S["body"]))
    story.append(sp(0.2))
    story.append(Paragraph("Ya construido en el MVP", S["h2"]))
    story.append(tabla(
        [
            ["Modulo", "Que hace", "Por que lo quieren"],
            ["Escandallo con rendimiento/merma",
             "Cada producto parte de precio en bruto y porcentaje de rendimiento. Calcula el coste "
             "sobre el peso NETO aprovechable y el sobrecoste oculto por merma.",
             "Es el coste REAL. Donde Excel falla y el margen se evapora sin que el chef lo vea."],
            ["Costeo de menu degustacion",
             "Estima el coste por comensal pase a pase (8-16 pases), food cost global y margen bruto.",
             "Controlar la rentabilidad de un degustacion es casi imposible sin herramienta."],
            ["Auditoria de progresion gastronomica",
             "Valida la curva del menu: intensidad, alternancia de temperaturas y texturas, "
             "equilibrio de proteinas.",
             "Segunda mirada experta sobre el equilibrio del menu antes del servicio."],
            ["Deteccion de pases criticos",
             "Senala que pases comprometen el margen y propone ajustes que no degradan la experiencia.",
             "Optimiza el margen sin tocar la calidad percibida ni el concepto del chef."],
            ["Mermas nobles + version vegetariana",
             "Sugiere aprovechamiento de mermas (carcasas, recortes) y evalua viabilidad de la "
             "version vegetariana del menu.",
             "Desperdicio cero de producto caro y respuesta a la demanda creciente de menu veggie."],
        ],
        [3.8 * cm, 6.6 * cm, 6.6 * cm]))
    story.append(sp(0.3))
    story.append(Paragraph("Hoja de ruta (Fase 2-3 del tier Gourmet)", S["h2"]))
    story.append(tabla(
        [
            ["Mejora futura", "Valor para la cocina gastronomica"],
            ["Escalado de receta por numero de comensales",
             "Mise en place exacto del degustacion para el servicio del dia"],
            ["Historico de precio de producto por temporada",
             "Alertas automaticas cuando sube el coste de un producto clave (gamba, trufa, wagyu)"],
            ["Ficha tecnica de pase con foto de emplatado",
             "Estandariza el pase entre turnos y cocineros; imprescindible en cocinas con plantilla"],
            ["Carta de alergenos por menu completo",
             "Respuesta perfecta en sala a comensales con alergias; cumplimiento Reglamento UE"],
            ["Integracion con proveedores / albaranes",
             "Coste real automatico desde el precio de compra del dia, sin entrada manual de datos"],
        ],
        [6.5 * cm, 10.5 * cm], header_bg=MORADO))

    # ── 04 PRICING ───────────────────────────────────────────────────────────
    story += seccion("04", "PRICING: EL TIER GOURMET")
    story.append(Paragraph(
        "No se saca un producto separado: se anade un cuarto tier premium al pricing existente. "
        "El cliente de alta cocina tiene mayor capacidad de pago y el valor entregado -- "
        "control de margen sobre producto caro -- lo justifica con holgura.", S["body"]))
    story.append(sp(0.25))
    story.append(tabla(
        [
            ["",                          "PRO",         "CHAIN",        "GOURMET (nuevo)"],
            ["Precio/mes",                "59 EUR",      "199 EUR",      "249 EUR"],
            ["Publico objetivo",          "Menu del dia","Cadenas",      "Bistronomiia y alta cocina"],
            ["Escandallo con merma",      "No",          "No",           "Si"],
            ["Menu degustacion multipase","No",          "No",           "Si"],
            ["Auditoria de progresion",   "No",          "No",           "Si"],
            ["Fichas tecnicas de pase",   "Basica",      "Si",           "Si Premium + foto"],
            ["Carta alergenos por menu",  "No",          "Si",           "Si"],
            ["Soporte",                   "Email + chat","Account Mgr",  "Asesor gastronomico dedicado"],
        ],
        [4.5 * cm, 3.5 * cm, 3.5 * cm, 5.5 * cm],
        row_colors=[(3, colors.HexColor("#1a1500")), (4, colors.HexColor("#1a1500"))],
        header_bg=colors.HexColor("#1a1500")))
    story.append(sp(0.25))
    story.append(Paragraph(
        "<b>Justificacion del precio:</b> 249 EUR/mes equivale a una fraccion de lo que un solo error "
        "de escandallo en un menu degustacion cuesta a lo largo de un mes. Para un restaurante que "
        "sirve 30 comensales/noche a 120 EUR, un descuadre del 4% de food cost supone ~430 EUR/mes "
        "perdidos. El tier se paga solo con que evite un error al mes.", S["body"]))
    story.append(sp(0.3))
    story.append(Paragraph("Proyeccion del tier Gourmet", S["h2"]))
    story.append(tabla(
        [
            ["Hito", "Clientes Gourmet", "MRR Gourmet", "Comentario"],
            ["Mes 6",  "8",   "1.992 EUR",
             "Pilotos de bistronomiia convertidos tras demo de escandallo con merma"],
            ["Mes 12", "30",  "7.470 EUR",
             "Boca a boca en el gremio gastronomico; primeras referencias con estrella"],
            ["Mes 18", "60",  "14.940 EUR",
             "1-2 cocinas con estrella activas como casos de prestigio de marca"],
            ["Mes 24", "100", "24.900 EUR",
             "Segmento premium consolidado, contribuye al 40% del MRR total"],
        ],
        [2.5 * cm, 2.8 * cm, 2.8 * cm, 9 * cm],
        row_colors=[(3, colors.HexColor("#1b3a1b"))]))

    # ── 05 CAPTACION ─────────────────────────────────────────────────────────
    story += seccion("05", "ESTRATEGIA DE CAPTACION")
    story.append(Paragraph(
        "El gremio gastronomico es pequeno, endogamico y se mueve por prestigio y recomendacion. "
        "La venta no es por anuncios: es por credibilidad y boca a boca entre chefs.", S["body"]))
    story.append(sp(0.25))
    story.append(tabla(
        [
            ["Canal", "Accion concreta", "Por que funciona"],
            ["Bistronomiia (puerta fria premium)",
             "Demo presencial de 15 min con el escandallo de merma de SU plato estrella, "
             "calculado en vivo delante del chef.",
             "Ver el sobrecoste oculto de su propio producto les impacta de forma inmediata."],
            ["Escuelas de alta cocina",
             "Basque Culinary Center, CETT, escuelas de referencia: licencia educativa "
             "gratuita o muy reducida.",
             "Los futuros chefs entran al mercado ya usando ChefMenu AI como herramienta habitual."],
            ["Chefs influyentes (prestigio)",
             "Ceder acceso gratuito a 2-3 cocinas con estrella a cambio de poder citarlas "
             "como referencia en materiales comerciales.",
             "Una estrella Michelin = credibilidad ante todo el gremio gastronomico del pais."],
            ["Congresos gastronomicos",
             "Madrid Fusion, San Sebastian Gastronomika: stand o demo en vivo en ponencia.",
             "Es donde esta todo el sector concentrado en dos o tres dias al ano."],
            ["Asociaciones y guias",
             "Eurotoques, Jeunes Restaurateurs, soles Repsol: partnership de distribucion.",
             "Acceso directo al segmento gastronomico ya agrupado y con comunidad activa."],
        ],
        [3.8 * cm, 7 * cm, 6.2 * cm]))
    story.append(sp(0.25))
    story.append(caja(
        "Demo que cierra en alta cocina: pidele el escandallo de su producto mas caro "
        "(la gamba, el pichon, el bogavante). Introduce el rendimiento real. Muestrale el sobrecoste "
        "por merma que NO estaba contando. Ese numero -- dinero que pierde cada servicio sin saberlo "
        "-- es el cierre de la venta.",
        bg=colors.HexColor("#1a1500"), border=DORADO))

    # ── 06 MENSAJE COMERCIAL ─────────────────────────────────────────────────
    story += seccion("06", "MENSAJE COMERCIAL Y POSICIONAMIENTO")
    story.append(Paragraph("Lo que NO se debe decir vs. lo que SI", S["h2"]))
    story.append(tabla(
        [
            ["NUNCA (lenguaje menu del dia)", "SIEMPRE (lenguaje alta cocina)"],
            ["Genera tu menu con IA",
             "Controla el margen de tu menu degustacion, pase a pase"],
            ["Te ahorra pensar el menu",
             "Tu creatividad intacta; tu rentabilidad bajo control"],
            ["Menus automaticos en 30 segundos",
             "El escandallo real de tu producto, con merma y rendimiento incluidos"],
            ["Rapido y facil para cualquier bar",
             "Rigor de controller financiero integrado en tu cocina"],
            ["Para cualquier restaurante",
             "Pensado especificamente para cocina de producto y menu degustacion"],
        ],
        [8.5 * cm, 8.5 * cm], header_bg=GRIS_OSC))
    story.append(sp(0.3))
    story.append(Paragraph(
        "<b>Tagline del segmento:</b> Tu cocina es arte. Tu margen, ciencia.<br/>"
        "ChefMenu AI no toca lo primero y se encarga de lo segundo.", S["body"]))
    story.append(sp(0.35))
    story.append(Paragraph("Resumen de la recomendacion estrategica", S["h2"]))
    story.append(tabla(
        [
            ["Num.", "Accion estrategica"],
            ["1", "No sacar producto separado: anadir tier Gourmet (249 EUR/mes) al pricing actual"],
            ["2", "Reposicionar la IA de creadora a analista/controller en materiales de alta cocina"],
            ["3", "Atacar primero la bistronomiia (8-12k locales), no la estrella pura"],
            ["4", "Usar 2-3 cocinas con estrella como prestigio de marca, no como motor de ingresos"],
            ["5", "Demo basada en escandallo de merma del producto mas caro del propio chef"],
            ["6", "Crecer via congresos gastronomicos, escuelas de alta cocina y boca a boca del gremio"],
        ],
        [1.2 * cm, 15.8 * cm],
        row_colors=[(1, colors.HexColor("#1b3a1b"))]))

    # ── CIERRE ───────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(sp(3))
    story.append(Paragraph("ChefMenu AI", S["ptit"]))
    story.append(sp(0.4))
    story.append(hr(DORADO, 2))
    story.append(sp(0.4))
    story.append(Paragraph("Tu cocina es arte. Tu margen, ciencia.", S["psub"]))
    story.append(sp(0.4))
    story.append(Paragraph(
        "Anexo estrategico de extension a alta cocina -- complementa el Plan de Lanzamiento Comercial.<br/>"
        "MerakIA Agency -- Confidencial -- Junio 2025", S["pdesc"]))

    doc.multiBuild(story, canvasmaker=FooterCanvas)
    print(f"PDF generado: {OUTPUT}")


if __name__ == "__main__":
    build()
