"""
Genera el Dossier de Venta para Restaurantes y Bares (PDF 2 páginas).
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
ORANGE       = colors.HexColor("#C0550A")
ORANGE_LIGHT = colors.HexColor("#E07830")
ORANGE_BG    = colors.HexColor("#FFF4EC")
DARK         = colors.HexColor("#1A1A2E")
GRAY         = colors.HexColor("#CCCCCC")
GRAY_BG      = colors.HexColor("#F8F8F8")
GREEN        = colors.HexColor("#27AE60")
GREEN_BG     = colors.HexColor("#E8F8F0")
WHITE        = colors.white
TABLE_HEAD   = colors.HexColor("#7A3008")

styles = getSampleStyleSheet()
def s(name, **kw): return ParagraphStyle(name, parent=styles["Normal"], **kw)
ST = {
    "h1":     s("h1",   fontName="Helvetica-Bold", fontSize=22, textColor=ORANGE, alignment=TA_CENTER, spaceAfter=4),
    "sub":    s("sub",  fontName="Helvetica", fontSize=11, textColor=ORANGE_LIGHT, alignment=TA_CENTER, spaceAfter=4),
    "h2":     s("h2",   fontName="Helvetica-Bold", fontSize=13, textColor=ORANGE, spaceBefore=10, spaceAfter=5),
    "body":   s("body", fontName="Helvetica", fontSize=10, textColor=DARK, leading=15, alignment=TA_JUSTIFY, spaceAfter=5),
    "bullet": s("bul",  fontName="Helvetica", fontSize=10, textColor=DARK, leading=14, leftIndent=14, firstLineIndent=-14, spaceAfter=4),
    "cap":    s("cap",  fontName="Helvetica-Oblique", fontSize=10, textColor=ORANGE, alignment=TA_CENTER, leading=15),
    "big":    s("big",  fontName="Helvetica-Bold", fontSize=17, textColor=GREEN, alignment=TA_CENTER),
    "footer": s("ftr",  fontName="Helvetica", fontSize=8, textColor=colors.HexColor("#888888"), alignment=TA_CENTER),
}

def hr(): return HRFlowable(width="100%", thickness=1.5, color=ORANGE, spaceAfter=8, spaceBefore=4)
def bullet(t, b=None): return Paragraph(f"• <b>{b}</b> {t}" if b else f"• {t}", ST["bullet"])

def box(text, bg=ORANGE_BG, border=ORANGE_LIGHT, stl="cap"):
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
    c.drawString(2*cm, H-1.3*cm, "MerakIA • Solución para Restaurantes y Bares")
    c.drawRightString(W-2*cm, H-1.3*cm, "Propuesta")
    c.setStrokeColor(GRAY); c.setLineWidth(0.5); c.line(2*cm, H-1.5*cm, W-2*cm, H-1.5*cm)
    c.drawCentredString(W/2, 1*cm, "MerakIA — Inteligencia Artificial con Alma")
    c.restoreState()


def build():
    story = []

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("MERAKIA", ST["h1"]))
    story.append(Paragraph("Más reservas, mejor reputación y mesas llenas — con IA, sin ampliar equipo", ST["sub"]))
    story.append(hr())
    story.append(Spacer(1, 0.2*cm))
    story.append(box(
        "Cada reseña sin responder aleja a un cliente nuevo.\n"
        "Cada llamada perdida es una mesa que va al restaurante de al lado.\n"
        "Nosotros cerramos esas fugas — automáticamente."
    ))

    story.append(Paragraph("El problema que probablemente ya conoces", ST["h2"]))
    story.append(Paragraph(
        "Tu restaurante o bar genera experiencias increíbles. El problema es que la gente "
        "no lo sabe, o lo descubre demasiado tarde. Las reservas se gestionan por teléfono "
        "en medio del servicio, Instagram se actualiza cuando hay tiempo (que nunca hay), "
        "y las reseñas negativas quedan sin respuesta durante semanas.", ST["body"]))
    for t in [
        "El 88% de los consumidores lee reseñas antes de elegir restaurante. Una reseña negativa sin responder disuade al 70%.",
        "Los restaurantes con Instagram activo y coherente facturan de media un 23% más en reservas online.",
        "El 40% de las llamadas a restaurantes se producen fuera del horario de servicio — y nadie coge el teléfono.",
    ]:
        story.append(bullet(t))

    story.append(Paragraph("Lo que MerakIA pone a trabajar para ti", ST["h2"]))
    serv = [
        ("Gestor de Reseñas IA",
         "Monitoriza Google, TripAdvisor y TheFork cada pocas horas. Alerta inmediata ante "
         "reseñas negativas y respuestas personalizadas generadas con IA, listas para publicar "
         "con un clic. Tu reputación online siempre cuidada."),
        ("Content Engine — Instagram & Redes",
         "30 días de contenido listo para publicar: fotos de platos, historias del chef, "
         "promociones especiales y posts de temporada con copy apetecible. "
         "Tú solo apruebas y programas."),
        ("Chatbot para reservas (web y WhatsApp)",
         "Gestiona reservas, informa del menú del día, confirma disponibilidad y responde "
         "dudas a cualquier hora. Incluso cuando estás en pleno servicio."),
        ("Agente de Voz IA",
         "Atiende las llamadas fuera de horario y en hora punta. Toma reservas, informa "
         "del menú y gestiona grupos. Sin perder ni una llamada."),
    ]
    for nombre, desc in serv:
        story.append(bullet(desc, b=nombre + " —"))

    story.append(Spacer(1, 0.3*cm))
    roi_data = [[
        Paragraph("+18<br/><font size=8>reservas/mes nuevas*</font>", ST["big"]),
        Paragraph("4.6★<br/><font size=8>media Google en 90 días</font>", ST["big"]),
        Paragraph("+40%<br/><font size=8>engagement en Instagram</font>", ST["big"]),
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
        "*Estimación para un restaurante con 30-50 cubiertos. Los resultados varían según cada caso.",
        ST["footer"]))

    # PÁGINA 2
    story.append(PageBreak())
    story.append(Paragraph("Cómo se traduce en euros", ST["h2"]))
    story.append(Paragraph(
        "Con solo recuperar las llamadas perdidas y mejorar la reputación online, "
        "el retorno cubre con creces la inversión desde el primer mes:", ST["body"]))

    calc = [
        ["Concepto", "Cantidad", "Valor"],
        ["Reservas nuevas captadas (llamadas fuera de horario)", "12", "—"],
        ["Ticket medio por mesa (2 personas, comida+bebida)", "—", "45€"],
        ["Reservas captadas vía chatbot web/WhatsApp", "6", "≈ 270€/mes"],
        ["Mejora de reputación → más visitas orgánicas Google", "estimado", "≈ 400€/mes"],
        ["Inversión MerakIA (paquete recomendado)", "—", "347€/mes"],
        ["RETORNO NETO ESTIMADO", "—", "+850€/mes"],
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
        "Diagnóstico gratuito: auditamos tu presencia en Google, reseñas e Instagram. Sin coste, sin compromiso.",
        "Configuramos el gestor de reseñas y el chatbot con el menú y datos reales de tu local.",
        "Lo pruebas durante 30 días. Si no notas más reservas o mejor reputación, te devolvemos el dinero.",
        "Cuando funciona — y funciona — seguimos creciendo juntos.",
    ], 1):
        story.append(Paragraph(f"<b>{i}.</b> {t}", ST["bullet"]))

    story.append(Spacer(1, 0.3*cm))
    story.append(box(
        "Garantía de 30 días. Si en un mes no notas la diferencia, no pagas.\n"
        "Empieza con un diagnóstico gratuito — sin compromiso, sin letra pequeña.",
        bg=GREEN_BG, border=GREEN, stl="cap"
    ))

    story.append(Spacer(1, 0.6*cm))
    story.append(Paragraph("¿Hablamos?", ST["h2"]))
    story.append(Paragraph(
        "MerakIA — Inteligencia Artificial con Alma para tu restaurante<br/>"
        "📧 luis82.bcn@hotmail.com · 📱 [tu WhatsApp] · 🌐 [tu web]", ST["cap"]))

    story.append(Spacer(1, 0.8*cm))
    story.append(Paragraph(
        f"Documento preparado el {datetime.date.today().strftime('%d de %B de %Y')}. "
        "Cifras orientativas basadas en restaurantes tipo; los resultados varían según cada caso.",
        ST["footer"]))
    return story


def generar_pdf(destino) -> None:
    doc = SimpleDocTemplate(
        destino, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=2.2*cm, bottomMargin=2*cm,
        title="MerakIA — Solución para Restaurantes", author="MerakIA",
    )
    doc.build(build(), onFirstPage=page_deco, onLaterPages=page_deco)


def generar_pdf_bytes() -> bytes:
    import io
    buf = io.BytesIO(); generar_pdf(buf); return buf.getvalue()


if __name__ == "__main__":
    import os
    os.makedirs("outputs", exist_ok=True)
    out = "outputs/MerakIA_Dossier_Restaurantes.pdf"
    generar_pdf(out)
    print(f"PDF generado: {out}")
