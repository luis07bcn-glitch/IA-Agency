# -*- coding: utf-8 -*-
"""
Dossier de Prospeccion — MerakIA · Clinicas dentales/estetica de Vilanova i la Geltru
Genera dossier_prospeccion_vng.pdf a partir de
outputs/prospector/diagnosticos_top.json (salida de diagnosticar_prospectos.py).

Una ficha por clinica: diagnostico (madurez digital, win probability, dolor),
perdida en EUR/mes desglosada, servicios recomendados y los 3 textos listos para
usar (WhatsApp, email y guion de llamada).
"""
import json
import html
import re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, HRFlowable,
    PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas

ROOT = Path(__file__).parent
IN = ROOT / "outputs" / "prospector" / "diagnosticos_top.json"
OUTPUT = ROOT / "dossier_prospeccion_vng.pdf"

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
VIOLETA= colors.HexColor("#8b5cf6")
GOLD   = colors.HexColor("#e4b85c")
ROSA   = colors.HexColor("#ec4899")
ACENTOS = [CYAN, VERDE, AMBAR, VIOLETA, ROSA, GOLD]
W = 17 * cm


def limpia(t):
    """Quita emojis / chars fuera de cp1252 (Helvetica no los soporta)."""
    if not t:
        return ""
    return t.encode("cp1252", "ignore").decode("cp1252")


def px(t):
    """Texto seguro para Paragraph: limpio, escapado y con <br/>."""
    t = limpia(str(t))
    t = html.escape(t)
    return t.replace("\n", "<br/>")


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
                        "MerakIA — Dossier de Prospeccion · Clinicas Vilanova i la Geltru")
        self.drawRightString(pw - 2 * cm, 0.9 * cm, f"{self._pageNumber} / {n}")
        self.setStrokeColor(LINEA)
        self.setLineWidth(0.5)
        self.line(2 * cm, 1.15 * cm, pw - 2 * cm, 1.15 * cm)
        self.restoreState()


def build():
    diags = json.loads(IN.read_text(encoding="utf-8"))
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, topMargin=1.6 * cm, bottomMargin=1.6 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title="MerakIA — Dossier de Prospeccion (Vilanova i la Geltru)",
        author="MerakIA Agency")
    base = getSampleStyleSheet()

    def stl(n, **kw):
        return ParagraphStyle(n, parent=base["Normal"], **kw)

    S = {
        "ptit": stl("ptit", fontSize=27, textColor=BLANCO, fontName="Helvetica-Bold",
                    alignment=TA_CENTER, leading=31),
        "psub": stl("psub", fontSize=12, textColor=CYAN, fontName="Helvetica-Bold",
                    alignment=TA_CENTER, spaceAfter=4),
        "pdesc": stl("pdesc", fontSize=9.5, textColor=TENUE, alignment=TA_CENTER, leading=14),
        "h1": stl("h1", fontSize=16, textColor=BLANCO, fontName="Helvetica-Bold", leading=20),
        "h2": stl("h2", fontSize=11.5, textColor=BLANCO, fontName="Helvetica-Bold",
                  spaceBefore=8, spaceAfter=3),
        "h3": stl("h3", fontSize=8, textColor=GOLD, fontName="Helvetica-Bold", spaceAfter=2),
        "body": stl("body", fontSize=9, leading=13, textColor=TEXTO, alignment=TA_JUSTIFY),
        "tc": stl("tc", fontSize=8, leading=11.5, textColor=TEXTO),
        "tcb": stl("tcb", fontSize=8, leading=11.5, textColor=BLANCO, fontName="Helvetica-Bold"),
        "tch": stl("tch", fontSize=7.5, leading=10, textColor=BLANCO, fontName="Helvetica-Bold"),
        "kpi": stl("kpi", fontSize=17, textColor=CYAN, fontName="Helvetica-Bold", alignment=TA_CENTER),
        "kpil": stl("kpil", fontSize=6.8, textColor=TENUE, alignment=TA_CENTER, leading=8.5),
        "copy": stl("copy", fontSize=8.5, leading=12.5, textColor=colors.HexColor("#d7e0f0")),
        "copyh": stl("copyh", fontSize=8.8, leading=12.5, textColor=GOLD, fontName="Helvetica-Bold"),
        "copygap": stl("copygap", fontSize=3, leading=4, textColor=PANEL2),
        "fname": stl("fname", fontSize=12.5, textColor=BLANCO, fontName="Helvetica-Bold", leading=15),
        "fmeta": stl("fmeta", fontSize=8, textColor=TENUE, leading=11),
        "mini": stl("mini", fontSize=7.5, textColor=TENUE, leading=10, alignment=TA_CENTER),
        "num": stl("num", fontSize=15, textColor=FONDO, fontName="Helvetica-Bold", alignment=TA_CENTER),
    }

    def sp(h=0.3):
        return Spacer(1, h * cm)

    def hr(c=LINEA, t=1):
        return HRFlowable(width="100%", thickness=t, color=c, spaceAfter=4)

    def nivel_color(nivel):
        n = (nivel or "").lower()
        if any(k in n for k in ("muy alta", "alta", "fuerte")):
            return VERDE
        if any(k in n for k in ("media", "aceptable")):
            return AMBAR
        return ROJO

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
        s = re.sub(r"__(.+?)__", r"<b>\1</b>", s)
        return s

    def copy_box(titulo, texto, border, canal):
        """Bloque copiar-y-pegar que PUEDE partirse entre paginas. Convierte
        markdown basico (#, **, >, -, ---) a formato legible y colapsa vacios."""
        base = html.escape(limpia(texto))
        rows = [[Paragraph(f'{canal} — {titulo}', S["tch"])]]
        blank = False
        for raw in base.split("\n"):
            st = raw.strip()
            if not st:
                if not blank:
                    rows.append([Paragraph("&nbsp;", S["copygap"])])
                    blank = True
                continue
            if set(st) <= set("-=*_~ "):     # linea separadora markdown
                continue
            blank = False
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

    # ── PORTADA ──
    story.append(sp(2.2))
    story.append(Paragraph("DOSSIER DE PROSPECCIÓN", S["psub"]))
    story.append(sp(0.15))
    story.append(Paragraph("10 clínicas listas para llamar", S["ptit"]))
    story.append(sp(0.3))
    story.append(hr(CYAN, 2.5))
    story.append(sp(0.25))
    story.append(Paragraph(
        "Diagnóstico individual, dinero que pierde cada una al mes y los textos "
        "personalizados (WhatsApp, email y guion de llamada) listos para copiar y "
        "pegar. Generado con ProspectorIA sobre datos reales de Google.", S["pdesc"]))
    story.append(sp(0.8))

    # tabla resumen / ranking
    story.append(Paragraph("Resumen — a quién llamar y con qué argumento", S["h2"]))
    head = ["#", "Clínica", "Teléfono", "Madurez", "Cierre", "Pierde/mes"]
    rows = [[Paragraph(h, S["tch"]) for h in head]]
    for i, d in enumerate(diags, 1):
        sc = d.get("scorecard") or {}
        win = d.get("win_probability") or {}
        mad = sc.get("score_global")
        perd = d.get("perdida_total_mes") or 0
        winsc = win.get("score")
        winniv = win.get("nivel", "")
        rows.append([
            Paragraph(str(i), S["tc"]),
            Paragraph(px(d["nombre"]), S["tcb"]),
            Paragraph(px(d.get("telefono") or "-"), S["tc"]),
            Paragraph(f"{mad:.0f}/100" if mad is not None else "-", S["tc"]),
            Paragraph(f'<font color="{nivel_color(winniv).hexval().replace("0x","#")}">'
                      f'{winsc if winsc is not None else "-"} ({limpia(winniv)})</font>', S["tc"]),
            Paragraph(f"~{perd:,.0f} €".replace(",", "."), S["tcb"]),
        ])
    t = Table(rows, colWidths=[0.8 * cm, 5.6 * cm, 2.6 * cm, 2.0 * cm, 3.2 * cm, 2.8 * cm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PANEL),
        ("TEXTCOLOR", (0, 0), (-1, 0), CYAN),
        ("GRID", (0, 0), (-1, -1), 0.3, LINEA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PANEL2, PANEL]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(sp(0.3))
    story.append(Paragraph(
        "<b>Madurez</b> = score de presencia digital (0-100; bajo = más margen de mejora). "
        "<b>Cierre</b> = probabilidad de venta estimada. <b>Pierde/mes</b> = dinero estimado "
        "que se le escapa hoy (supuestos conservadores: 120 contactos/mes, 25% conversión; "
        "ajústalo en la reunión con sus números reales).", S["mini"]))

    # ── FICHAS ──
    for i, d in enumerate(diags, 1):
        acento = ACENTOS[(i - 1) % len(ACENTOS)]
        sc = d.get("scorecard") or {}
        win = d.get("win_probability") or {}
        story.append(PageBreak())

        # cabecera
        num = Table([[Paragraph(str(i), S["num"])]], colWidths=[1.1 * cm])
        num.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), acento),
                                 ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                 ("TOPPADDING", (0, 0), (-1, -1), 6),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        web = d.get("web")
        meta = f"{limpia(d.get('telefono') or 'sin teléfono')}  ·  "
        meta += (limpia(web) if web else "SIN WEB")
        rat = d.get("rating")
        meta += f"  ·  {rat}★·{d.get('total_resenas',0)}" if rat is not None else f"  ·  {d.get('total_resenas',0)} reseñas"
        info = Table([[Paragraph(px(d["nombre"]), S["fname"])],
                      [Paragraph(px(meta), S["fmeta"])],
                      [Paragraph(px(d.get("direccion", "")), S["fmeta"])]], colWidths=[W - 1.1 * cm])
        info.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 9),
                                  ("TOPPADDING", (0, 0), (0, 0), 3),
                                  ("BOTTOMPADDING", (0, -1), (-1, -1), 3),
                                  ("BACKGROUND", (0, 0), (-1, -1), PANEL)]))
        cab = Table([[num, info]], colWidths=[1.1 * cm, W - 1.1 * cm])
        cab.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                 ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                 ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                 ("TOPPADDING", (0, 0), (-1, -1), 0),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                                 ("BOX", (0, 0), (-1, -1), 1, acento)]))
        story.append(cab)
        story.append(sp(0.25))

        # KPIs
        mad = sc.get("score_global")
        perc = sc.get("percentil_nicho")
        winsc = win.get("score")
        perd = d.get("perdida_total_mes") or 0
        ticket = d.get("ticket")
        story.append(kpi_box([
            (f"{mad:.0f}" if mad is not None else "-", "MADUREZ DIGITAL\n(0-100)".replace("\n", " "), nivel_color(sc.get("nivel_global"))),
            (f"{winsc}" if winsc is not None else "-", f"PROB. CIERRE ({limpia(win.get('nivel',''))})", nivel_color(win.get("nivel"))),
            (f"~{perd:,.0f}€".replace(",", "."), "PIERDE AL MES", ROJO),
            (f"{ticket:.0f}€" if ticket else "-", "TICKET MEDIO EST.", GOLD),
        ], border=acento))
        story.append(sp(0.25))

        # diagnóstico breve
        resumen = d.get("resumen_oportunidad")
        if resumen:
            story.append(Paragraph("Diagnóstico", S["h2"]))
            story.append(Paragraph(px(resumen), S["body"]))
            story.append(sp(0.2))

        # dónde está el dolor (dimensiones más débiles)
        dims = sc.get("dimensiones") or []
        debiles = sorted([x for x in dims if x.get("score", 0) < 50], key=lambda x: x.get("score", 0))[:4]
        if debiles:
            story.append(Paragraph("Dónde pierde terreno (huecos digitales)", S["h3"]))
            drows = []
            for dim in debiles:
                falta = "; ".join(dim.get("senales_falta", [])[:2]) or "—"
                drows.append([Paragraph(px(dim["nombre"]), S["tcb"]),
                              Paragraph(f'{dim.get("score",0):.0f}/100', S["tc"]),
                              Paragraph(px(falta), S["tc"])])
            dt = Table(drows, colWidths=[4.6 * cm, 1.6 * cm, 10.8 * cm])
            dt.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), PANEL2),
                ("GRID", (0, 0), (-1, -1), 0.3, LINEA),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("TEXTCOLOR", (1, 0), (1, -1), ROJO),
            ]))
            story.append(dt)
            story.append(sp(0.2))

        # pérdida desglosada
        perdidas = d.get("perdidas") or []
        if perdidas:
            story.append(Paragraph(f"Dinero que pierde hoy — ~{perd:,.0f} €/mes".replace(",", "."), S["h2"]))
            prows = [[Paragraph("Concepto", S["tch"]), Paragraph("€/mes", S["tch"]),
                      Paragraph("Por qué", S["tch"])]]
            for p in perdidas:
                prows.append([Paragraph(px(p["concepto"]), S["tcb"]),
                              Paragraph(f'{p["euros_mes"]:,.0f}'.replace(",", "."), S["tcb"]),
                              Paragraph(px(p["explicacion"]), S["tc"])])
            pt = Table(prows, colWidths=[4.2 * cm, 1.8 * cm, 11.0 * cm], repeatRows=1)
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
            story.append(sp(0.2))

        # servicios recomendados
        servicios = d.get("servicios_recomendados") or []
        if servicios:
            story.append(Paragraph("Qué ofrecerle", S["h2"]))
            srows = [[Paragraph("Servicio", S["tch"]), Paragraph("Setup", S["tch"]),
                      Paragraph("€/mes", S["tch"]), Paragraph("Impacto", S["tch"])]]
            for s in servicios[:3]:
                srows.append([Paragraph(px(s["nombre"]), S["tcb"]),
                              Paragraph(f'{s["setup"]:.0f}€', S["tc"]),
                              Paragraph(f'{s["mensual"]:.0f}€' if s["mensual"] else "—", S["tc"]),
                              Paragraph(px(s.get("impacto") or s.get("motivo") or ""), S["tc"])])
            st_ = Table(srows, colWidths=[4.4 * cm, 1.7 * cm, 1.7 * cm, 9.2 * cm], repeatRows=1)
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
            story.append(sp(0.25))

        # textos listos para usar
        story.append(Paragraph("Textos personalizados — copiar y pegar", S["h2"]))
        if d.get("whatsapp_mensaje"):
            story.extend(copy_box("Primer contacto", d["whatsapp_mensaje"], VERDE, "WhatsApp"))
        if d.get("email_cuerpo"):
            asunto = d.get("email_asunto") or ""
            cuerpo = (f"Asunto: {asunto}\n\n" if asunto else "") + d["email_cuerpo"]
            story.extend(copy_box("Email de prospección", cuerpo, CYAN, "Email"))
        if d.get("script_llamada"):
            story.extend(copy_box("Guion de llamada en frío", d["script_llamada"], AMBAR, "Llamada"))

    story.append(PageBreak())
    story.append(sp(3))
    story.append(Paragraph("Ahora marca el #1.", S["ptit"]))
    story.append(sp(0.4))
    story.append(hr(CYAN, 2))
    story.append(sp(0.4))
    story.append(Paragraph(
        "Cada ficha es una conversación esperando a ocurrir. No las perfecciones: úsalas. "
        "El objetivo de esta semana es agendar 3 reuniones-diagnóstico.", S["pdesc"]))

    doc.build(story, onFirstPage=_bg, onLaterPages=_bg, canvasmaker=Cnv)
    print(f"OK -> {OUTPUT}")


if __name__ == "__main__":
    build()
