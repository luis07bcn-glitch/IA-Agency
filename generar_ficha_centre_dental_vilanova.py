# -*- coding: utf-8 -*-
"""
Ficha de venta — Centre Dental Vilanova
Genera ficha_centre_dental_vilanova.pdf a partir de
outputs/prospector/diagnostico_centre_dental_vilanova.json
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
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas

ROOT = Path(__file__).parent
IN = ROOT / "outputs" / "prospector" / "diagnostico_centre_dental_vilanova.json"
OUTPUT = ROOT / "ficha_centre_dental_vilanova.pdf"

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
        self.drawString(2 * cm, 0.9 * cm, "MerakIA — Ficha de venta · Centre Dental Vilanova")
        self.drawRightString(pw - 2 * cm, 0.9 * cm, f"{self._pageNumber} / {n}")
        self.setStrokeColor(LINEA)
        self.setLineWidth(0.5)
        self.line(2 * cm, 1.15 * cm, pw - 2 * cm, 1.15 * cm)
        self.restoreState()


def build():
    d = json.loads(IN.read_text(encoding="utf-8"))
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, topMargin=1.6 * cm, bottomMargin=1.6 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title="MerakIA — Ficha de venta: Centre Dental Vilanova", author="MerakIA Agency")
    base = getSampleStyleSheet()

    def stl(n, **kw):
        return ParagraphStyle(n, parent=base["Normal"], **kw)

    S = {
        "ptit": stl("ptit", fontSize=23, textColor=BLANCO, fontName="Helvetica-Bold",
                    alignment=TA_CENTER, leading=27),
        "psub": stl("psub", fontSize=11.5, textColor=CYAN, fontName="Helvetica-Bold",
                    alignment=TA_CENTER, spaceAfter=4),
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
        "alerta": stl("alerta", fontSize=8.6, leading=12.5, textColor=colors.HexColor("#fca5a5")),
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
    sc = d.get("scorecard") or {}
    win = d.get("win_probability") or {}

    # ---- PORTADA ----
    story.append(sp(1.4))
    story.append(Paragraph("FICHA DE VENTA", S["psub"]))
    story.append(sp(0.1))
    story.append(Paragraph("Centre Dental Vilanova", S["ptit"]))
    story.append(sp(0.2))
    story.append(Paragraph("Vilanova i la Geltrú · Clínica dental · +20 años", S["psub"]))
    story.append(sp(0.25))
    story.append(hr(CYAN, 2))
    story.append(sp(0.3))

    story.append(kpi_box([
        (f"{d.get('rating')}★", f"RATING GOOGLE ({d.get('total_resenas')} reseñas)", VERDE),
        (f"{sc.get('score_global', 0):.0f}/100", "MADUREZ DIGITAL", AMBAR),
        (f"{win.get('score','-')}", f"PROB. CIERRE ({limpia(win.get('nivel',''))})", VERDE),
        (f"{d.get('ticket','-')}€", "TICKET MEDIO EST.", GOLD),
    ], border=CYAN))
    story.append(sp(0.35))

    story.append(Paragraph("⚠ Verificar antes de llamar", S["h3"]))
    story.append(Paragraph(
        "Google Places marca este negocio como <b>CLOSED_TEMPORARILY</b>. No hay ningún "
        "indicio de cierre real ni denuncias (a diferencia del caso OralStudio): 4.8★ con "
        "349 reseñas es un volumen de actividad muy alto, tienen CIF activo, y la dirección "
        "que da Google difiere de la de su web antigua — todo apunta a un traslado de local "
        "mal sincronizado en la ficha, no a un cierre. <b>Aun así, confirma en Google Maps "
        "que aparece \"Abierto ahora\" con horario correcto antes de invertir tiempo en la "
        "llamada.</b>", S["alerta"]))
    story.append(sp(0.3))

    story.append(Paragraph("Diagnóstico", S["h2"]))
    story.append(Paragraph(px(d.get("resumen_oportunidad", "")), S["body"]))
    story.append(sp(0.25))

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
        story.append(sp(0.25))

    servicios = d.get("servicios_recomendados") or []
    if servicios:
        story.append(Paragraph("Qué ofrecerle", S["h2"]))
        srows = [[Paragraph("Servicio", S["tch"]), Paragraph("Setup", S["tch"]),
                  Paragraph("€/mes", S["tch"]), Paragraph("Impacto", S["tch"])]]
        for s in servicios[:4]:
            srows.append([Paragraph(px(s["nombre"]), S["tcb"]),
                          Paragraph(f'{s["setup"]:.0f}€', S["tc"]),
                          Paragraph(f'{s["mensual"]:.0f}€' if s["mensual"] else "—", S["tc"]),
                          Paragraph(px(s.get("impacto") or s.get("motivo") or ""), S["tc"])])
        st_ = Table(srows, colWidths=[4.6 * cm, 1.8 * cm, 1.8 * cm, 8.8 * cm], repeatRows=1)
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

    # ---- TEXTOS ----
    story.append(PageBreak())
    story.append(Paragraph("Textos listos para usar — copiar y pegar", S["h2"]))
    story.append(sp(0.2))
    if d.get("whatsapp_mensaje"):
        story.extend(copy_box("Primer contacto", d["whatsapp_mensaje"], VERDE, "WhatsApp"))
    if d.get("email_cuerpo"):
        asunto = d.get("email_asunto") or ""
        cuerpo = (f"Asunto: {asunto}\n\n" if asunto else "") + d["email_cuerpo"]
        story.extend(copy_box("Email de prospección", cuerpo, CYAN, "Email"))
    if d.get("script_llamada"):
        story.extend(copy_box("Guion de llamada en frío + objeciones", d["script_llamada"], AMBAR, "Llamada"))

    doc.build(story, onFirstPage=_bg, onLaterPages=_bg, canvasmaker=Cnv)
    print(f"OK -> {OUTPUT}")


if __name__ == "__main__":
    build()
