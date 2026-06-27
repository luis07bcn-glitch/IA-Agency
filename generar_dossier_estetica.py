"""
Genera el Dossier de Venta para Centros de Estética y Belleza (PDF 2 páginas).
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import datetime

W, H = A4
PURPLE       = colors.HexColor("#6B2D8B")
PURPLE_LIGHT = colors.HexColor("#9B59B6")
PURPLE_BG    = colors.HexColor("#F3E8FF")
ROSE         = colors.HexColor("#C0397A")
ROSE_LIGHT   = colors.HexColor("#E8678A")
ROSE_BG      = colors.HexColor("#FFF0F6")
DARK         = colors.HexColor("#1A1A2E")
GRAY         = colors.HexColor("#CCCCCC")
GRAY_BG      = colors.HexColor("#F8F8F8")
GREEN        = colors.HexColor("#27AE60")
GREEN_BG     = colors.HexColor("#E8F8F0")
WHITE        = colors.white
TABLE_HEAD   = colors.HexColor("#7B1F4E")

styles = getSampleStyleSheet()
def s(name, **kw): return ParagraphStyle(name, parent=styles["Normal"], **kw)
ST = {
    "h1":     s("h1",   fontName="Helvetica-Bold", fontSize=22, textColor=ROSE, alignment=TA_CENTER, spaceAfter=4),
    "sub":    s("sub",  fontName="Helvetica", fontSize=11, textColor=PURPLE_LIGHT, alignment=TA_CENTER, spaceAfter=4),
    "h2":     s("h2",   fontName="Helvetica-Bold", fontSize=13, textColor=ROSE, spaceBefore=10, spaceAfter=5),
    "body":   s("body", fontName="Helvetica", fontSize=10, textColor=DARK, leading=15, alignment=TA_JUSTIFY, spaceAfter=5),
    "bullet": s("bul",  fontName="Helvetica", fontSize=10, textColor=DARK, leading=14, leftIndent=14, firstLineIndent=-14, spaceAfter=4),
    "cap":    s("cap",  fontName="Helvetica-Oblique", fontSize=10, textColor=ROSE, alignment=TA_CENTER, leading=15),
    "big":    s("big",  fontName="Helvetica-Bold", fontSize=17, textColor=GREEN, alignment=TA_CENTER),
    "footer": s("ftr",  fontName="Helvetica", fontSize=8, textColor=colors.HexColor("#888888"), alignment=TA_CENTER),
}

def hr(): return HRFlowable(width="100%", thickness=1.5, color=ROSE, spaceAfter=8, spaceBefore=4)
def bullet(t, b=None): return Paragraph(f"• <b>{b}</b> {t}" if b else f"• {t}", ST["bullet"])

def box(text, bg=ROSE_BG, border=ROSE_LIGHT, stl="cap"):
    t = Table([[Paragraph(text, ST[stl])]], colWidths=[16*cm])
    t.setStyle(TableStyle([
        ("BOX",(0,0),(-1,-1),1,border),("BACKGROUND",(0,0),(-1,-1),bg),
        ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10),
        ("LEFTPADDING",(0,0),(-1,-1),14),("RIGHTPADDING",(0,0),(-1,-1),14),
    ]))
    return t

def page_deco(c, doc):
    c.saveState()
    c.setFont("Helvetica", 8); c.setFillColor(colors.HexColor("#888888"))
    c.drawString(2*cm, H-1.3*cm, "MerakIA • Solución para Centros de Estética y Belleza")
    c.drawRightString(W-2*cm, H-1.3*cm, "Propuesta")
    c.setStrokeColor(GRAY); c.setLineWidth(0.5); c.line(2*cm, H-1.5*cm, W-2*cm, H-1.5*cm)
    c.drawCentredString(W/2, 1*cm, "MerakIA — Inteligencia Artificial con Alma")
    c.restoreState()


def build():
    story = []

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("MERAKIA", ST["h1"]))
    story.append(Paragraph("Tu centro lleno todos los días — con IA, sin contratar más personal", ST["sub"]))
    story.append(hr())
    story.append(Spacer(1, 0.2*cm))
    story.append(box(
        "Cada hueco libre en tu agenda es dinero que no entra.\n"
        "Nosotros lo llenamos — con IA que trabaja mientras tú atiendes a tus clientas."
    ))

    story.append(Paragraph("El problema que probablemente ya conoces", ST["h2"]))
    story.append(Paragraph(
        "Tu centro de estética depende de una agenda siempre llena. Pero entre las cancelaciones "
        "de última hora, los no-shows, Instagram sin actualizar y los mensajes sin contestar "
        "a tiempo, se escapan reservas cada día. Y tú no puedes estar en todo a la vez.", ST["body"]))
    for t in [
        "El 20-35% de las citas se pierden por cancelaciones tardías o ausencias sin aviso.",
        "Los centros con Instagram activo captan hasta 3 veces más clientas nuevas que los que no publican.",
        "El 60% de las personas elige centro basándose en las reseñas de Google antes de llamar.",
    ]:
        story.append(bullet(t))

    story.append(Paragraph("Lo que MerakIA pone a trabajar para ti", ST["h2"]))
    serv = [
        ("Agente de Voz IA",
         "Atiende el teléfono 24/7. Informa de tratamientos y precios, agenda citas directamente "
         "en tu calendario y responde fuera de horario sin que pierdas ni una reserva."),
        ("Recordatorios anti-cancelación",
         "WhatsApp automático 24h y 2h antes de cada cita. La clienta confirma con un clic. "
         "Reducción drástica de no-shows y huecos vacíos de última hora."),
        ("Content Engine — Instagram & Redes",
         "30 días de contenido listo para publicar: posts, carruseles, Reels y stories con copy "
         "persuasivo. Tú solo apruebas y programas. Nunca más el bloqueo del 'qué publico hoy'."),
        ("Chatbot IA para web y WhatsApp",
         "Responde dudas sobre tratamientos, precios y disponibilidad. Agenda citas solas "
         "mientras tú estás con clientas. Activo los 7 días, las 24 horas."),
    ]
    for nombre, desc in serv:
        story.append(bullet(desc, b=nombre + " —"))

    story.append(Spacer(1, 0.3*cm))
    roi_data = [[
        Paragraph("+10<br/><font size=8>citas/mes recuperadas*</font>", ST["big"]),
        Paragraph("−65%<br/><font size=8>en no-shows</font>", ST["big"]),
        Paragraph("×3<br/><font size=8>engagement en Instagram</font>", ST["big"]),
    ]]
    roi_t = Table(roi_data, colWidths=[5.3*cm, 5.3*cm, 5.3*cm])
    roi_t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),GREEN_BG),("BOX",(0,0),(-1,-1),1,GREEN),
        ("INNERGRID",(0,0),(-1,-1),0.5,GREEN),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10),
    ]))
    story.append(roi_t)
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph(
        "*Estimación para un centro con 15-20 ausencias/mes. Los resultados varían según cada caso.",
        ST["footer"]))

    # PÁGINA 2
    story.append(PageBreak())
    story.append(Paragraph("Cómo se traduce en euros", ST["h2"]))
    story.append(Paragraph(
        "Un solo tratamiento de nivel medio recuperado al día ya amortiza la inversión. "
        "El cálculo real es este:", ST["body"]))

    calc = [
        ["Concepto", "Cantidad", "Valor"],
        ["Citas recuperadas al mes (agente de voz + recordatorios)", "10", "—"],
        ["Valor medio de un tratamiento facial/corporal", "—", "65€"],
        ["Clientas nuevas captadas vía redes + chatbot", "4-6", "≈ 325€/mes"],
        ["No-shows evitados (huecos que se llenan de nuevo)", "8-12", "≈ 520€/mes"],
        ["Inversión MerakIA (paquete recomendado)", "—", "297€/mes"],
        ["RETORNO NETO ESTIMADO", "—", "+700€/mes"],
    ]
    ct = Table(calc, colWidths=[9*cm, 2.5*cm, 4.5*cm])
    ct.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),TABLE_HEAD),("TEXTCOLOR",(0,0),(-1,0),WHITE),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),9.5),
        ("FONTNAME",(0,1),(-1,-2),"Helvetica"),
        ("BACKGROUND",(0,6),(-1,6),GREEN_BG),("FONTNAME",(0,6),(-1,6),"Helvetica-Bold"),
        ("TEXTCOLOR",(0,6),(-1,6),GREEN),
        ("ROWBACKGROUNDS",(0,1),(-1,5),[WHITE,GRAY_BG]),
        ("GRID",(0,0),(-1,-1),0.4,GRAY),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("ALIGN",(1,0),(-1,-1),"CENTER"),
        ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
        ("LEFTPADDING",(0,0),(-1,-1),7),
    ]))
    story.append(ct)

    story.append(Paragraph("Cómo empezamos (sin riesgo para ti)", ST["h2"]))
    for i, t in enumerate([
        "Diagnóstico gratuito: analizamos tu Instagram, reseñas de Google y agenda actual. Sin coste.",
        "Configuramos el agente de voz y los recordatorios con el nombre y servicios de tu centro.",
        "Lo pruebas durante 30 días. Si no notas más citas y menos ausencias, te devolvemos el dinero.",
        "Cuando funciona — y funciona — seguimos creciendo juntos.",
    ], 1):
        story.append(Paragraph(f"<b>{i}.</b> {t}", ST["bullet"]))

    story.append(Spacer(1, 0.3*cm))
    story.append(box(
        "Garantía de 30 días. Si en un mes no notas la diferencia, no pagas.\n"
        "El diagnóstico es gratuito y sin compromiso — empezar no te cuesta nada.",
        bg=GREEN_BG, border=GREEN, stl="cap"
    ))

    story.append(Spacer(1, 0.6*cm))
    story.append(Paragraph("¿Hablamos?", ST["h2"]))
    story.append(Paragraph(
        "MerakIA — Inteligencia Artificial con Alma para tu centro<br/>"
        "📧 luis82.bcn@hotmail.com · 📱 [tu WhatsApp] · 🌐 [tu web]", ST["cap"]))

    story.append(Spacer(1, 0.8*cm))
    story.append(Paragraph(
        f"Documento preparado el {datetime.date.today().strftime('%d de %B de %Y')}. "
        "Cifras orientativas basadas en centros de estética tipo; los resultados varían según cada caso.",
        ST["footer"]))
    return story


def generar_pdf(destino) -> None:
    doc = SimpleDocTemplate(
        destino, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=2.2*cm, bottomMargin=2*cm,
        title="MerakIA — Solución para Centros de Estética", author="MerakIA",
    )
    doc.build(build(), onFirstPage=page_deco, onLaterPages=page_deco)


def generar_pdf_bytes() -> bytes:
    import io
    buf = io.BytesIO(); generar_pdf(buf); return buf.getvalue()


if __name__ == "__main__":
    import os
    os.makedirs("outputs", exist_ok=True)
    out = "outputs/MerakIA_Dossier_Estetica_Belleza.pdf"
    generar_pdf(out)
    print(f"PDF generado: {out}")
