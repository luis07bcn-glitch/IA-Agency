"""
Genera el Dossier de Venta para Clínicas Dentales (PDF de 2 páginas).
El documento que dejas o envías tras la primera reunión con una clínica.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import datetime

W, H = A4
PURPLE       = colors.HexColor("#6B2D8B")
PURPLE_LIGHT = colors.HexColor("#9B59B6")
PURPLE_BG    = colors.HexColor("#F3E8FF")
DARK         = colors.HexColor("#1A1A2E")
GRAY         = colors.HexColor("#CCCCCC")
GRAY_BG      = colors.HexColor("#F8F8F8")
GREEN        = colors.HexColor("#27AE60")
GREEN_BG     = colors.HexColor("#E8F8F0")
WHITE        = colors.white
TABLE_HEAD   = colors.HexColor("#4A1A6E")

styles = getSampleStyleSheet()
def s(name, **kw): return ParagraphStyle(name, parent=styles["Normal"], **kw)
ST = {
    "h1":   s("h1",   fontName="Helvetica-Bold", fontSize=24, textColor=PURPLE, alignment=TA_CENTER, spaceAfter=4),
    "sub":  s("sub",  fontName="Helvetica", fontSize=12, textColor=PURPLE_LIGHT, alignment=TA_CENTER, spaceAfter=4),
    "h2":   s("h2",   fontName="Helvetica-Bold", fontSize=14, textColor=PURPLE, spaceBefore=12, spaceAfter=6),
    "body": s("body", fontName="Helvetica", fontSize=10, textColor=DARK, leading=15, alignment=TA_JUSTIFY, spaceAfter=6),
    "bullet": s("bul", fontName="Helvetica", fontSize=10, textColor=DARK, leading=14, leftIndent=14, firstLineIndent=-14, spaceAfter=4),
    "cap":  s("cap",  fontName="Helvetica-Oblique", fontSize=10, textColor=PURPLE, alignment=TA_CENTER, leading=15),
    "big":  s("big",  fontName="Helvetica-Bold", fontSize=18, textColor=GREEN, alignment=TA_CENTER),
    "biglbl": s("biglbl", fontName="Helvetica", fontSize=8.5, textColor=DARK, alignment=TA_CENTER, leading=11),
    "footer": s("ftr", fontName="Helvetica", fontSize=8, textColor=colors.HexColor("#888888"), alignment=TA_CENTER),
}

def hr(): return HRFlowable(width="100%", thickness=1.5, color=PURPLE, spaceAfter=8, spaceBefore=4)
def bullet(t, b=None): return Paragraph(f"• <b>{b}</b> {t}" if b else f"• {t}", ST["bullet"])

def box(text, bg=PURPLE_BG, border=PURPLE_LIGHT, stl="cap"):
    t = Table([[Paragraph(text, ST[stl])]], colWidths=[16*cm])
    t.setStyle(TableStyle([
        ("BOX",(0,0),(-1,-1),1,border), ("BACKGROUND",(0,0),(-1,-1),bg),
        ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10),
        ("LEFTPADDING",(0,0),(-1,-1),14),("RIGHTPADDING",(0,0),(-1,-1),14),
    ]))
    return t

def page_deco(c, doc):
    c.saveState()
    c.setFont("Helvetica", 8); c.setFillColor(colors.HexColor("#888888"))
    c.drawString(2*cm, H-1.3*cm, "MerakIA • Solución para Clínicas Dentales")
    c.drawRightString(W-2*cm, H-1.3*cm, "Propuesta")
    c.setStrokeColor(GRAY); c.setLineWidth(0.5); c.line(2*cm, H-1.5*cm, W-2*cm, H-1.5*cm)
    c.drawCentredString(W/2, 1*cm, "MerakIA — Inteligencia Artificial con Alma")
    c.restoreState()


def build():
    story = []
    # PÁGINA 1
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("MERAKIA", ST["h1"]))
    story.append(Paragraph("La recepción que nunca cierra para tu clínica", ST["sub"]))
    story.append(hr())
    story.append(Spacer(1, 0.2*cm))
    story.append(box(
        "Cada llamada que tu clínica no contesta es un paciente que llama al de al lado.\n"
        "Nosotros hacemos que eso deje de pasar — con inteligencia artificial, sin ampliar tu equipo."
    ))

    story.append(Paragraph("El problema que probablemente ya conoces", ST["h2"]))
    story.append(Paragraph(
        "Tu recepción no puede estar en todo. Cuando hay un paciente en el sillón, cuando es la hora de comer, "
        "cuando ya habéis cerrado… el teléfono sigue sonando. Y el paciente que busca dentista no deja "
        "un mensaje: cuelga y llama al siguiente de Google.", ST["body"]
    ))
    for t in [
        "El 30-40% de las llamadas a clínicas se pierden fuera de horario o en hora punta.",
        "Los no-shows (pacientes que no aparecen) dejan huecos del 10-25% de la agenda.",
        "Las reseñas negativas sin responder ahuyentan a nuevos pacientes en Google.",
    ]:
        story.append(bullet(t))

    story.append(Paragraph("Lo que MerakIA pone a trabajar para ti", ST["h2"]))
    serv = [
        ("Agente de Voz IA",
         "Atiende el teléfono 24/7 con voz natural. Informa de tratamientos y precios, y agenda "
         "la primera visita directamente en tu calendario. Se conecta a tu número actual."),
        ("Recordatorios anti-no-show",
         "Mensajes automáticos por WhatsApp 24h y 2h antes de cada cita, con confirmación en un clic. "
         "Reduce las ausencias drásticamente."),
        ("Chatbot para web y WhatsApp",
         "Responde dudas y capta pacientes mientras tú trabajas. Cualifica y agenda solo."),
        ("Gestor de Reseñas",
         "Vigila tus reseñas de Google, te avisa de las negativas al instante y redacta las respuestas con IA."),
    ]
    for nombre, desc in serv:
        story.append(bullet(desc, b=nombre + " —"))

    story.append(Spacer(1, 0.3*cm))
    # ROI destacado
    roi_data = [[
        Paragraph("+14<br/><font size=8>citas/mes recuperadas*</font>", ST["big"]),
        Paragraph("−70%<br/><font size=8>en no-shows</font>", ST["big"]),
        Paragraph("24/7<br/><font size=8>atención al paciente</font>", ST["big"]),
    ]]
    roi_t = Table(roi_data, colWidths=[5.3*cm, 5.3*cm, 5.3*cm])
    roi_t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),GREEN_BG), ("BOX",(0,0),(-1,-1),1,GREEN),
        ("INNERGRID",(0,0),(-1,-1),0.5,GREEN), ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10),
    ]))
    story.append(roi_t)
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph(
        "*Estimación para una clínica que pierde ~20 llamadas/mes fuera de horario con una conversión del 30%.",
        ST["footer"]))

    # PÁGINA 2
    story.append(PageBreak())
    story.append(Paragraph("Cómo se traduce en euros", ST["h2"]))
    story.append(Paragraph(
        "No es un gasto de marketing, es una palanca de ingresos. Un solo tratamiento recuperado "
        "al mes ya cubre con creces la inversión:", ST["body"]
    ))
    calc = [
        ["Concepto", "Cantidad", "Valor"],
        ["Citas recuperadas al mes (agente de voz)", "14", "—"],
        ["Valor medio de una primera visita que cierra tratamiento", "—", "300€"],
        ["Conversión conservadora a tratamiento (1 de cada 4)", "3-4", "≈ 1.000€/mes"],
        ["No-shows evitados al mes", "8-12", "≈ 500€/mes"],
        ["Inversión MerakIA (paquete recomendado)", "—", "397€/mes"],
        ["RETORNO NETO ESTIMADO", "—", "+1.100€/mes"],
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
        "Diagnóstico gratuito: analizamos tu presencia online y tus llamadas perdidas. Sin coste, sin compromiso.",
        "Configuramos el agente de voz y los recordatorios con los datos reales de tu clínica.",
        "Lo pruebas durante 30 días. Si no ves resultados, te devolvemos el dinero.",
        "Cuando funciona (y funciona), seguimos creciendo juntos.",
    ], 1):
        story.append(Paragraph(f"<b>{i}.</b> {t}", ST["bullet"]))

    story.append(Spacer(1, 0.3*cm))
    story.append(box(
        "Garantía de 30 días. Si en un mes no notas la diferencia, no pagas.\n"
        "Empezar es tan fácil como decir «sí» a un diagnóstico gratuito.",
        bg=GREEN_BG, border=GREEN, stl="cap"
    ))

    story.append(Spacer(1, 0.6*cm))
    story.append(Paragraph("¿Hablamos?", ST["h2"]))
    story.append(Paragraph(
        "MerakIA — Inteligencia Artificial con Alma para tu clínica<br/>"
        "📧 luis82.bcn@hotmail.com · 📱 [tu WhatsApp] · 🌐 [tu web]", ST["cap"]
    ))

    story.append(Spacer(1, 0.8*cm))
    story.append(Paragraph(
        f"Documento preparado el {datetime.date.today().strftime('%d de %B de %Y')}. "
        "Cifras orientativas basadas en clínicas dentales tipo; los resultados varían según cada caso.",
        ST["footer"]))
    return story


def generar_pdf(destino) -> None:
    doc = SimpleDocTemplate(
        destino, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=2.2*cm, bottomMargin=2*cm,
        title="MerakIA — Solución para Clínicas Dentales", author="MerakIA",
    )
    doc.build(build(), onFirstPage=page_deco, onLaterPages=page_deco)


def generar_pdf_bytes() -> bytes:
    import io
    buf = io.BytesIO(); generar_pdf(buf); return buf.getvalue()


if __name__ == "__main__":
    import os
    os.makedirs("outputs", exist_ok=True)
    out = "outputs/MerakIA_Dossier_Clinicas_Dentales.pdf"
    generar_pdf(out)
    print(f"PDF generado: {out}")
