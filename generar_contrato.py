"""
Genera el Contrato de Prestación de Servicios MerakIA (PDF 2 páginas).
Documento editable: campos entre [ ] para rellenar antes de firmar.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
import datetime

W, H = A4
PURPLE       = colors.HexColor("#6B2D8B")
PURPLE_LIGHT = colors.HexColor("#9B59B6")
PURPLE_BG    = colors.HexColor("#F3E8FF")
DARK         = colors.HexColor("#1A1A2E")
GRAY         = colors.HexColor("#CCCCCC")
GRAY_BG      = colors.HexColor("#F8F8F8")
WHITE        = colors.white
FIELD_BG     = colors.HexColor("#FFFDE7")
FIELD_BORDER = colors.HexColor("#F0C040")

styles = getSampleStyleSheet()
def s(name, **kw): return ParagraphStyle(name, parent=styles["Normal"], **kw)
ST = {
    "h1":     s("h1",   fontName="Helvetica-Bold", fontSize=20, textColor=PURPLE, alignment=TA_CENTER, spaceAfter=4),
    "sub":    s("sub",  fontName="Helvetica", fontSize=10, textColor=PURPLE_LIGHT, alignment=TA_CENTER, spaceAfter=2),
    "h2":     s("h2",   fontName="Helvetica-Bold", fontSize=12, textColor=PURPLE, spaceBefore=14, spaceAfter=5),
    "body":   s("body", fontName="Helvetica", fontSize=9.5, textColor=DARK, leading=14, alignment=TA_JUSTIFY, spaceAfter=4),
    "field":  s("fld",  fontName="Helvetica-Oblique", fontSize=9.5, textColor=colors.HexColor("#7B6000"), leading=14, spaceAfter=4),
    "clause": s("cls",  fontName="Helvetica-Bold", fontSize=9.5, textColor=DARK, spaceBefore=8, spaceAfter=3),
    "footer": s("ftr",  fontName="Helvetica", fontSize=7.5, textColor=colors.HexColor("#888888"), alignment=TA_CENTER),
    "sign":   s("sgn",  fontName="Helvetica", fontSize=9, textColor=DARK, alignment=TA_CENTER),
}

def hr(): return HRFlowable(width="100%", thickness=1, color=PURPLE, spaceAfter=6, spaceBefore=4)
def field(label, value=""):
    txt = f"<b>{label}:</b>  {value if value else '[                                                    ]'}"
    t = Table([[Paragraph(txt, ST["field"])]], colWidths=[16.5*cm])
    t.setStyle(TableStyle([
        ("BOX",(0,0),(-1,-1),0.8,FIELD_BORDER),
        ("BACKGROUND",(0,0),(-1,-1),FIELD_BG),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),10),
    ]))
    return t

def page_deco(c, doc):
    c.saveState()
    c.setFont("Helvetica", 7.5); c.setFillColor(colors.HexColor("#888888"))
    c.drawString(2*cm, H-1.2*cm, "MerakIA — Contrato de Servicios  |  Confidencial")
    c.drawRightString(W-2*cm, H-1.2*cm, f"Página {doc.page}")
    c.setStrokeColor(GRAY); c.setLineWidth(0.4); c.line(2*cm, H-1.4*cm, W-2*cm, H-1.4*cm)
    c.drawCentredString(W/2, 0.8*cm, "MerakIA · luis82.bcn@hotmail.com · Barcelona")
    c.restoreState()

SERVICIOS = [
    ("Meraki Soul Audit", "Diagnóstico IA completo + Meraki Score + roadmap 90 días"),
    ("Content Engine", "Calendario editorial 30 días con copy íntegro para RRSS"),
    ("Chatbot IA 24/7", "Chatbot personalizado para web / WhatsApp / Instagram"),
    ("Agente de Voz IA", "Recepcionista IA telefónica 24/7 con agendado automático"),
    ("Recordatorios & Fidelización", "Sistema anti-no-show + win-back automático"),
    ("Gestor de Reseñas", "Monitorización Google + respuestas IA + alertas"),
    ("Webs & Landing Pages", "Diseño, desarrollo y publicación de web o landing"),
    ("Automatización Interna", "Flujos automatizados de tareas operativas internas"),
    ("Meraki Team (Human+IA)", "Acceso completo + estratega senior mensual"),
]

def build():
    story = []

    # CABECERA
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("MERAKIA", ST["h1"]))
    story.append(Paragraph("Contrato de Prestación de Servicios de Inteligencia Artificial", ST["sub"]))
    story.append(hr())
    story.append(Spacer(1, 0.2*cm))

    # PARTES
    story.append(Paragraph("1. PARTES CONTRATANTES", ST["h2"]))
    story.append(Paragraph(
        "<b>PRESTADOR:</b> Luis — MerakIA, con domicilio en Barcelona, email luis82.bcn@hotmail.com "
        "(en adelante, «MerakIA»).", ST["body"]))
    story.append(Spacer(1, 0.2*cm))
    story.append(field("Nombre / Razón social del cliente"))
    story.append(field("NIF / CIF"))
    story.append(field("Domicilio"))
    story.append(field("Email de contacto"))
    story.append(field("Teléfono"))
    story.append(Spacer(1, 0.1*cm))

    # OBJETO
    story.append(Paragraph("2. OBJETO DEL CONTRATO", ST["h2"]))
    story.append(Paragraph(
        "MerakIA se compromete a prestar al cliente los servicios de inteligencia artificial "
        "marcados a continuación, en las condiciones descritas en el presente contrato:", ST["body"]))

    chk_data = []
    for nom, desc in SERVICIOS:
        chk_data.append([
            Paragraph("☐", ParagraphStyle("chk", parent=styles["Normal"], fontSize=11, textColor=PURPLE)),
            Paragraph(f"<b>{nom}</b> — {desc}", ST["body"]),
        ])
    chk_t = Table(chk_data, colWidths=[0.6*cm, 15.9*cm])
    chk_t.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("LEFTPADDING",(0,0),(-1,-1),2),
    ]))
    story.append(chk_t)

    # PRECIO
    story.append(Paragraph("3. PRECIO Y FORMA DE PAGO", ST["h2"]))
    story.append(field("Precio mensual (IVA no incluido)"))
    story.append(field("Forma de pago", "Transferencia bancaria / domiciliación SEPA"))
    story.append(field("Día de facturación", "Día 1 de cada mes"))
    story.append(Paragraph(
        "El primer mes se factura íntegro al inicio. Los meses sucesivos se facturan "
        "por adelantado el día 1. El impago de dos mensualidades consecutivas faculta a MerakIA "
        "a suspender el servicio sin necesidad de preaviso.", ST["body"]))

    # DURACIÓN
    story.append(Paragraph("4. DURACIÓN Y RENOVACIÓN", ST["h2"]))
    story.append(field("Fecha de inicio del contrato"))
    story.append(Paragraph(
        "El contrato tiene una duración mínima de <b>3 meses</b>. Transcurrido ese período, "
        "se renueva automáticamente por períodos mensuales salvo que cualquiera de las partes "
        "comunique su voluntad de no renovar con un preaviso mínimo de <b>15 días naturales</b> "
        "por escrito.", ST["body"]))

    # PÁGINA 2
    story.append(PageBreak())

    # OBLIGACIONES
    story.append(Paragraph("5. OBLIGACIONES DE LAS PARTES", ST["h2"]))
    story.append(Paragraph("<b>MerakIA se compromete a:</b>", ST["clause"]))
    for t in [
        "Configurar y mantener los servicios contratados según las especificaciones acordadas.",
        "Entregar los primeros entregables en un plazo máximo de 7 días laborables desde el inicio.",
        "Atender las incidencias del cliente en un plazo máximo de 24 horas en días laborables.",
        "Mantener la confidencialidad de toda la información del negocio del cliente.",
    ]:
        story.append(Paragraph(f"• {t}", ST["body"]))

    story.append(Paragraph("<b>El cliente se compromete a:</b>", ST["clause"]))
    for t in [
        "Facilitar la información necesaria para la configuración de los agentes (servicios, precios, FAQ, accesos).",
        "Revisar y aprobar los entregables en un plazo máximo de 5 días laborables.",
        "Abonar las facturas en el plazo acordado.",
        "No compartir ni revender los entregables generados por MerakIA a terceros sin autorización expresa.",
    ]:
        story.append(Paragraph(f"• {t}", ST["body"]))

    # PROPIEDAD INTELECTUAL
    story.append(Paragraph("6. PROPIEDAD INTELECTUAL", ST["h2"]))
    story.append(Paragraph(
        "Los entregables generados durante la vigencia del contrato (contenidos, system prompts, "
        "automatizaciones, webs) son propiedad del cliente una vez satisfecho el pago íntegro "
        "del período en curso. MerakIA podrá utilizar resultados anonimizados como referencia "
        "en su portfolio, salvo indicación expresa del cliente.", ST["body"]))

    # CONFIDENCIALIDAD
    story.append(Paragraph("7. CONFIDENCIALIDAD", ST["h2"]))
    story.append(Paragraph(
        "Ambas partes se obligan a mantener en estricta confidencialidad toda la información "
        "comercial, técnica o de negocio que accedan en virtud de este contrato, durante su "
        "vigencia y por un período de 2 años tras su finalización.", ST["body"]))

    # PROTECCIÓN DE DATOS
    story.append(Paragraph("8. PROTECCIÓN DE DATOS (RGPD)", ST["h2"]))
    story.append(Paragraph(
        "El tratamiento de datos personales se realizará conforme al Reglamento (UE) 2016/679 "
        "(RGPD) y la LOPDGDD. MerakIA actúa como encargado del tratamiento de los datos que "
        "el cliente (responsable) facilite para la prestación del servicio. Los datos no serán "
        "cedidos a terceros salvo obligación legal.", ST["body"]))

    # RESOLUCIÓN
    story.append(Paragraph("9. RESOLUCIÓN ANTICIPADA", ST["h2"]))
    story.append(Paragraph(
        "Cualquiera de las partes podrá resolver el contrato de forma anticipada, una vez "
        "superado el período mínimo de 3 meses, con un preaviso de 15 días naturales por "
        "escrito. MerakIA podrá resolver de forma inmediata en caso de impago o uso indebido "
        "de los servicios.", ST["body"]))

    # JURISDICCIÓN
    story.append(Paragraph("10. LEY APLICABLE Y JURISDICCIÓN", ST["h2"]))
    story.append(Paragraph(
        "El presente contrato se rige por la legislación española. Para cualquier controversia, "
        "las partes se someten a los Juzgados y Tribunales de la ciudad de Barcelona, "
        "con renuncia expresa a cualquier otro fuero.", ST["body"]))

    # FIRMAS
    story.append(Spacer(1, 0.6*cm))
    story.append(hr())
    story.append(Paragraph(
        f"En Barcelona, a     de                    de {datetime.date.today().year}", ST["body"]))
    story.append(Spacer(1, 0.4*cm))

    firma_data = [[
        Paragraph("Por MerakIA\n\n\n\n_______________________\nLuis — Fundador\nluis82.bcn@hotmail.com", ST["sign"]),
        Paragraph("Por el cliente\n\n\n\n_______________________\n[Nombre y cargo]\n[Email]", ST["sign"]),
    ]]
    firma_t = Table(firma_data, colWidths=[8*cm, 8*cm])
    firma_t.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("TOPPADDING",(0,0),(-1,-1),8),
        ("LEFTPADDING",(0,0),(-1,-1),10),
    ]))
    story.append(firma_t)

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        "Documento generado por MerakIA · Confidencial · Para uso exclusivo de las partes firmantes",
        ST["footer"]))
    return story


def generar_pdf(destino) -> None:
    doc = SimpleDocTemplate(
        destino, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=1.8*cm,
        title="MerakIA — Contrato de Servicios", author="MerakIA",
    )
    doc.build(build(), onFirstPage=page_deco, onLaterPages=page_deco)


def generar_pdf_bytes() -> bytes:
    import io
    buf = io.BytesIO(); generar_pdf(buf); return buf.getvalue()


if __name__ == "__main__":
    import os
    os.makedirs("outputs", exist_ok=True)
    out = "outputs/MerakIA_Contrato_Servicios.pdf"
    generar_pdf(out)
    print(f"PDF generado: {out}")
