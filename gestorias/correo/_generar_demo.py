# -*- coding: utf-8 -*-
"""
Genera la bandeja de demo: .eml realistas en gestorias/demo_correo/ con el
escenario "trimestre": 4 negocios de la cartera mandan sus facturas por email
(Meraki, Taller Pepe, Peluquería Loli, Centro Estética Manolita), más
notificaciones de la administración, consultas y spam.

    venv\\Scripts\\python.exe gestorias\\correo\\_generar_demo.py
"""
from __future__ import annotations

import io
import sys
from email.message import EmailMessage
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

OUT = Path(__file__).resolve().parent.parent / "demo_correo"
OUT.mkdir(parents=True, exist_ok=True)


def _font(size, bold=False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    p = Path(r"C:\Windows\Fonts") / name
    return ImageFont.truetype(str(p), size) if p.exists() else ImageFont.load_default()


def factura_png(emisor: str, cif: str, numero: str, fecha: str,
                cliente: str, cliente_cif: str,
                lineas: list[tuple[str, str, str, str]],
                base: str, iva: str, total: str, irpf: str = "") -> bytes:
    W, H = 1240, 1400
    BLUE, GRAY, LINE = (23, 55, 94), (90, 90, 90), (200, 200, 200)
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    d.rectangle([0, 0, W, 12], fill=BLUE)
    d.text((60, 60), emisor, font=_font(30, True), fill=BLUE)
    d.text((60, 105), f"CIF: {cif}", font=_font(22), fill=GRAY)
    d.text((820, 60), "FACTURA", font=_font(46, True), fill=BLUE)
    d.text((820, 130), f"Nº: {numero}", font=_font(24, True), fill=(0, 0, 0))
    d.text((820, 165), f"Fecha: {fecha}", font=_font(22), fill=(0, 0, 0))

    d.line([60, 230, W - 60, 230], fill=LINE, width=2)
    d.text((60, 250), "CLIENTE", font=_font(20, True), fill=GRAY)
    d.text((60, 280), cliente, font=_font(24, True), fill=(0, 0, 0))
    d.text((60, 315), f"CIF: {cliente_cif}", font=_font(20), fill=GRAY)

    top = 400
    d.rectangle([60, top, W - 60, top + 44], fill=BLUE)
    for x, t in ((80, "Descripcion"), (720, "Cant."), (850, "Precio"), (1030, "Importe")):
        d.text((x, top + 10), t, font=_font(21, True), fill="white")
    y = top + 44
    for desc, cant, precio, imp in lineas:
        d.line([60, y, W - 60, y], fill=LINE, width=1)
        d.text((80, y + 12), desc, font=_font(21), fill=(0, 0, 0))
        d.text((730, y + 12), cant, font=_font(21), fill=(0, 0, 0))
        d.text((850, y + 12), precio + " EUR", font=_font(21), fill=(0, 0, 0))
        d.text((1030, y + 12), imp + " EUR", font=_font(21), fill=(0, 0, 0))
        y += 50

    y += 30
    d.text((850, y), "Base imponible:", font=_font(22), fill=(0, 0, 0))
    d.text((1050, y), base + " EUR", font=_font(22), fill=(0, 0, 0))
    y += 40
    d.text((850, y), "IVA (21%):", font=_font(22), fill=(0, 0, 0))
    d.text((1050, y), iva + " EUR", font=_font(22), fill=(0, 0, 0))
    if irpf:
        y += 40
        d.text((850, y), "Retencion IRPF:", font=_font(22), fill=(0, 0, 0))
        d.text((1050, y), irpf + " EUR", font=_font(22), fill=(0, 0, 0))
    y += 48
    d.rectangle([840, y, W - 60, y + 50], fill=BLUE)
    d.text((850, y + 12), "TOTAL:", font=_font(24, True), fill="white")
    d.text((1030, y + 12), total + " EUR", font=_font(24, True), fill="white")

    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


# --- Los 4 negocios de la cartera demo ---------------------------------------

MERAKI = ("MERAKIA STUDIO, S.L.", "B-66123123")
PEPE = ("TALLER PEPE, S.L.", "B-64789456")
LOLI = ("PELUQUERIA LOLI", "38765412-K")
MANOLITA = ("CENTRE ESTETICA MANOLITA, S.C.P.", "J-08991122")


def _f(emisor, cif, numero, fecha, negocio, lineas, base, iva, total, irpf=""):
    return factura_png(emisor, cif, numero, fecha, negocio[0], negocio[1],
                       lineas, base, iva, total, irpf)


FACTURAS = {
    # Meraki (3)
    "meraki_hosting.png": _f("CLOUDCAT SERVEIS DIGITALS, S.L.", "B-67411220", "CC-2026-3311", "05/06/2026",
        MERAKI, [("Hosting cloud (2T)", "3", "89,00", "267,00")], "267,00", "56,07", "323,07"),
    "meraki_publicidad.png": _f("MITJANS PENEDES PUBLICITAT, S.L.", "B-62999887", "MP-0788", "18/06/2026",
        MERAKI, [("Campanya anuncis (juny)", "1", "450,00", "450,00")], "450,00", "94,50", "544,50"),
    "meraki_material.png": _f("OFIMATERIAL VILANOVA, S.L.", "B-61558802", "OV-26-1204", "27/06/2026",
        MERAKI, [("Material oficina", "1", "182,30", "182,30")], "182,30", "38,28", "220,58"),
    # Taller Pepe (4)
    "pepe_recambios.png": _f("RECANVIS GARRAF, S.A.", "A-58771002", "RG-2026-8812", "02/06/2026",
        PEPE, [("Pastillas freno (juego)", "12", "34,20", "410,40"),
               ("Filtros aceite", "20", "7,80", "156,00")], "566,40", "118,94", "685,34"),
    "pepe_aceites.png": _f("LUBRICANTS PENEDES, S.L.", "B-63220145", "LP-0455", "10/06/2026",
        PEPE, [("Aceite 5W30 (garrafa 20L)", "8", "96,00", "768,00")], "768,00", "161,28", "929,28"),
    "pepe_electricidad.png": _f("ENERGIA DEL GARRAF COMERCIALIZADORA, S.A.", "A-58122334", "EG-2026-119332", "30/06/2026",
        PEPE, [("Suministro electrico taller (2T)", "1", "612,40", "612,40")], "612,40", "128,60", "741,00"),
    "pepe_grua.png": _f("GRUES I ASSISTENCIA VNG, S.C.C.L.", "F-08662210", "GA-260/112", "22/06/2026",
        PEPE, [("Servicios grua (junio)", "5", "70,00", "350,00")], "350,00", "73,50", "423,50"),
    # Peluquería Loli (3)
    "loli_productos.png": _f("DISTRIBUCIONS COSMETIQUES BCN, S.L.", "B-60441123", "DC-26-7741", "08/06/2026",
        LOLI, [("Tintes y productos capilares", "1", "324,50", "324,50")], "324,50", "68,15", "392,65"),
    "loli_alquiler.png": _f("INMOBLES RAMBLA PRINCIPAL, S.L.", "B-59120334", "IR-2026-06", "01/06/2026",
        LOLI, [("Alquiler local c/ Sant Gregori (junio)", "1", "850,00", "850,00")],
        "850,00", "178,50", "867,00", irpf="-161,50"),
    "loli_luz.png": _f("ENERGIA DEL GARRAF COMERCIALIZADORA, S.A.", "A-58122334", "EG-2026-120100", "30/06/2026",
        LOLI, [("Suministro electrico local (2T)", "1", "198,20", "198,20")], "198,20", "41,62", "239,82"),
    # Manolita (3 + 1 rezagada)
    "manolita_aparatologia.png": _f("ESTETIC SUPPLIES IBERIA, S.L.", "B-65002218", "ES-26-0912", "04/06/2026",
        MANOLITA, [("Consumibles aparatologia", "1", "441,00", "441,00")], "441,00", "92,61", "533,61"),
    "manolita_lenceria.png": _f("TEXTILS PROFESSIONALS TARRACO, S.L.", "B-55889034", "TT-3320", "15/06/2026",
        MANOLITA, [("Toallas y lenceria cabina", "1", "156,80", "156,80")], "156,80", "32,93", "189,73"),
    "manolita_formacion.png": _f("ACADEMIA BELLESA CATALANA", "40221876-T", "AB-2026-77", "20/06/2026",
        MANOLITA, [("Curso tecnico (2 plazas)", "2", "190,00", "380,00")],
        "380,00", "79,80", "402,80", irpf="-57,00"),
    "manolita_rezagada.png": _f("PERFUMS I ESSENCIES DEL MARESME, S.L.", "B-62110987", "PM-26-449", "29/06/2026",
        MANOLITA, [("Esencias y aceites masaje", "1", "127,40", "127,40")], "127,40", "26,75", "154,15"),
    # Remitente NO registrado en la cartera (para enseñar el flujo "sin asignar")
    "jmarti_mantenimiento.png": _f("JOAN MARTI SERVEIS INFORMATICS", "46722810-Z", "2026-031", "30/06/2026",
        ("FUSTERIA SOLER, S.L.", "B-61002288"),
        [("Mantenimiento informatico (2T)", "1", "540,00", "540,00")],
        "540,00", "113,40", "572,40", irpf="-81,00"),
}


def _eml(nombre: str, de: str, asunto: str, cuerpo: str,
         adjuntos: list[str] | None = None) -> None:
    msg = EmailMessage()
    msg["From"] = de
    msg["To"] = "despacho@gestoriaejemplo.es"
    msg["Subject"] = asunto
    msg["Date"] = "Mon, 13 Jul 2026 09:30:00 +0200"
    msg.set_content(cuerpo)
    for filename in (adjuntos or []):
        msg.add_attachment(FACTURAS[filename], maintype="image", subtype="png",
                           filename=filename)
    (OUT / nombre).write_bytes(bytes(msg))
    print("  ", nombre)


def main() -> None:
    # limpiar bandeja anterior
    for viejo in OUT.glob("*.eml"):
        viejo.unlink()

    print(f"Generando bandeja demo en {OUT}")
    _eml("01_meraki_facturas_2T.eml",
         "MerakIA Studio <administracion@meraki.studio>",
         "Facturas 2T",
         "Buenas, os adjunto las facturas del trimestre. Un saludo!",
         ["meraki_hosting.png", "meraki_publicidad.png", "meraki_material.png"])
    _eml("02_taller_pepe_facturas.eml",
         "Taller Pepe <taller.pepe@gmail.com>",
         "facturas para el iva del trimestre",
         "hola son las facturas del taller de este trimestre, dime si falta algo. pepe",
         ["pepe_recambios.png", "pepe_aceites.png", "pepe_electricidad.png", "pepe_grua.png"])
    _eml("03_loli_facturas.eml",
         "Loli <loli.pelu@hotmail.com>",
         "Facturas peluquería",
         "Hola guapa, te paso las facturas de la pelu. El alquiler lleva retención "
         "como siempre. Besos, Loli",
         ["loli_productos.png", "loli_alquiler.png", "loli_luz.png"])
    _eml("04_manolita_facturas.eml",
         "Centre Estètica Manolita <manolita.estetica@gmail.com>",
         "Facturas del centro - 2o trimestre",
         "Buenos días, adjuntamos las facturas del segundo trimestre del centro.",
         ["manolita_aparatologia.png", "manolita_lenceria.png", "manolita_formacion.png"])
    _eml("05_manolita_rezagada.eml",
         "Centre Estètica Manolita <manolita.estetica@gmail.com>",
         "Se me olvidó esta!",
         "Perdona, esta se me quedó en el correo. ¿Llega a tiempo para el trimestre?",
         ["manolita_rezagada.png"])
    _eml("06_desconocido_factura.eml",
         "Joan Marti <joan@jmserveis.cat>",
         "Fra. mantenimiento Fusteria Soler",
         "Bon dia, us passo la factura del manteniment informàtic de Fusteria Soler "
         "perquè la tingueu per al trimestre. Salut!",
         ["jmarti_mantenimiento.png"])
    _eml("07_notificacion_aeat.eml",
         "Notificaciones AEAT <no-reply@correo.aeat.es>",
         "Puesta a disposicion de notificacion electronica",
         "Se ha puesto a su disposición una nueva notificación electrónica en la "
         "Sede Electrónica de la Agencia Tributaria para el NIF B-64789456. "
         "Dispone de 10 días naturales para acceder a su contenido.")
    _eml("08_requerimiento_tgss.eml",
         "Seguridad Social <noreply@seg-social.es>",
         "TGSS - Comunicacion importante sobre cuota de autonomos",
         "Le informamos de una regularización en la cuota de autónomos del "
         "período 01/2026-06/2026 conforme a los rendimientos comunicados. "
         "Acceda a Import@ss para consultar el detalle.")
    _eml("09_consulta_nomina.eml",
         "Pere Soler <pere.soler@fusteriasoler.cat>",
         "Duda con la nómina de julio",
         "Hola Marta, el nuevo carpintero empieza el día 20. ¿Cómo lo hacemos con "
         "la nómina de este mes, la prorrateamos?")
    _eml("10_spam_software.eml",
         "SoftAsesor Pro <marketing@softasesorpro.com>",
         "⚡ Última oportunidad: 50% dto. en tu software de asesoría",
         "¿Todavía gestionas tu despacho con Excel? Solo esta semana, 50% de "
         "descuento. Date de baja aquí.")

    # cartera demo en BD (solo si está vacía)
    from gestorias import clientes as cartera
    conn = cartera.get_conn()
    cartera.seed_demo(conn)
    conn.close()
    print("Cartera demo verificada en BD")
    print("OK")


if __name__ == "__main__":
    main()
