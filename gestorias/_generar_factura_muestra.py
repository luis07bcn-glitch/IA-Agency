# -*- coding: utf-8 -*-
"""
Genera una factura de muestra (PNG) con aspecto realista para DEMOSTRAR el
extractor. En produccion las facturas las trae el cliente; esto es solo para
la demo interna / la reunion con el gestor.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent / "demo_facturas" / "factura_muestra.png"
OUT.parent.mkdir(parents=True, exist_ok=True)


def _font(size, bold=False):
    # Fuentes estandar de Windows
    name = "arialbd.ttf" if bold else "arial.ttf"
    for base in (r"C:\Windows\Fonts",):
        p = Path(base) / name
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


W, H = 1240, 1754  # A4 a ~150dpi
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)

BLUE = (23, 55, 94)
GRAY = (90, 90, 90)
LINE = (200, 200, 200)

# Cabecera emisor
d.rectangle([0, 0, W, 12], fill=BLUE)
d.text((60, 60), "SUMINISTROS INDUSTRIALES GARRAF, S.L.", font=_font(30, True), fill=BLUE)
d.text((60, 105), "CIF: B-61234567", font=_font(22), fill=GRAY)
d.text((60, 135), "C/ del Ferro, 24 - Pol. Ind. Masia Nova", font=_font(20), fill=GRAY)
d.text((60, 162), "08800 Vilanova i la Geltru (Barcelona)", font=_font(20), fill=GRAY)
d.text((60, 189), "Tel. 938 15 44 20 - admin@suministrosgarraf.es", font=_font(20), fill=GRAY)

# Titulo FACTURA
d.text((820, 60), "FACTURA", font=_font(46, True), fill=BLUE)
d.text((820, 130), "Nº: FA-2026/0417", font=_font(24, True), fill=(0, 0, 0))
d.text((820, 165), "Fecha: 30/06/2026", font=_font(22), fill=(0, 0, 0))
d.text((820, 197), "Vencimiento: 30/07/2026", font=_font(22), fill=GRAY)

# Cliente
d.line([60, 250, W - 60, 250], fill=LINE, width=2)
d.text((60, 275), "CLIENTE", font=_font(20, True), fill=GRAY)
d.text((60, 305), "TALLERES MECANICS RIBES, S.C.P.", font=_font(24, True), fill=(0, 0, 0))
d.text((60, 340), "CIF: J-08765432", font=_font(21), fill=GRAY)
d.text((60, 370), "Av. de Garraf, 112 - 08810 Sant Pere de Ribes", font=_font(21), fill=GRAY)

# Tabla lineas
top = 460
d.rectangle([60, top, W - 60, top + 44], fill=BLUE)
d.text((80, top + 10), "Descripcion", font=_font(21, True), fill="white")
d.text((720, top + 10), "Cant.", font=_font(21, True), fill="white")
d.text((850, top + 10), "Precio", font=_font(21, True), fill="white")
d.text((1030, top + 10), "Importe", font=_font(21, True), fill="white")

lineas = [
    ("Rodamiento SKF 6205-2RS", "20", "8,40", "168,00"),
    ("Aceite hidraulico ISO 46 (garrafa 20L)", "6", "62,50", "375,00"),
    ("Filtro de aire referencia AF-2231", "12", "14,75", "177,00"),
    ("Mano de obra montaje (horas)", "8", "35,00", "280,00"),
]
y = top + 44
for desc, cant, precio, imp in lineas:
    d.line([60, y, W - 60, y], fill=LINE, width=1)
    d.text((80, y + 12), desc, font=_font(21), fill=(0, 0, 0))
    d.text((730, y + 12), cant, font=_font(21), fill=(0, 0, 0))
    d.text((850, y + 12), precio + " EUR", font=_font(21), fill=(0, 0, 0))
    d.text((1030, y + 12), imp + " EUR", font=_font(21), fill=(0, 0, 0))
    y += 50

# Totales
y += 30
d.text((850, y), "Base imponible:", font=_font(22), fill=(0, 0, 0))
d.text((1030, y), "1.000,00 EUR", font=_font(22), fill=(0, 0, 0))
y += 40
d.text((850, y), "IVA (21%):", font=_font(22), fill=(0, 0, 0))
d.text((1030, y), "210,00 EUR", font=_font(22), fill=(0, 0, 0))
y += 40
d.text((850, y), "Retencion IRPF (-15%):", font=_font(22), fill=(0, 0, 0))
d.text((1030, y), "-150,00 EUR", font=_font(22), fill=(0, 0, 0))
y += 48
d.rectangle([840, y, W - 60, y + 50], fill=BLUE)
d.text((850, y + 12), "TOTAL FACTURA:", font=_font(24, True), fill="white")
d.text((1030, y + 12), "1.060,00 EUR", font=_font(24, True), fill="white")

# Pie
d.text((60, y + 120), "Forma de pago: Transferencia bancaria", font=_font(20), fill=GRAY)
d.text((60, y + 150), "IBAN: ES91 2100 0418 4502 0005 1332", font=_font(20), fill=GRAY)

img.save(OUT, "PNG")
print("Factura de muestra guardada en:", OUT)
