# -*- coding: utf-8 -*-
"""Genera el manual PDF de parámetros del bot Polymarket BTC Up/Down.

Uso:
    venv\\Scripts\\python.exe polymarket-bot\\generar_manual_parametros.py
"""
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
    TableStyle,
)

SALIDA = Path(__file__).resolve().parent / "manual_parametros_bot.pdf"

INK = HexColor("#111827")       # texto principal
ACCENT = HexColor("#5b21b6")    # violeta MerakIA
ACCENT_SOFT = HexColor("#ede9fe")
GRIS = HexColor("#6b7280")
LINEA = HexColor("#d1d5db")
VERDE = HexColor("#065f46")
ROJO = HexColor("#991b1b")
FONDO_CODIGO = HexColor("#f3f4f6")

ss = getSampleStyleSheet()

st_titulo = ParagraphStyle("titulo", parent=ss["Title"], fontName="Helvetica-Bold",
                           fontSize=26, leading=31, textColor=INK, spaceAfter=4)
st_sub = ParagraphStyle("sub", parent=ss["Normal"], fontName="Helvetica",
                        fontSize=13, leading=17, textColor=GRIS)
st_h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold",
                       fontSize=16, leading=20, textColor=ACCENT,
                       spaceBefore=18, spaceAfter=8)
st_h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold",
                       fontSize=12.5, leading=16, textColor=INK,
                       spaceBefore=12, spaceAfter=4)
st_p = ParagraphStyle("p", parent=ss["Normal"], fontName="Helvetica",
                      fontSize=10.2, leading=14.5, textColor=INK,
                      spaceAfter=6, alignment=4)  # justificado
st_peq = ParagraphStyle("peq", parent=st_p, fontSize=9, leading=12.5,
                        textColor=GRIS, alignment=0)
st_celda = ParagraphStyle("celda", parent=st_p, fontSize=9.6, leading=13,
                          spaceAfter=0, alignment=0)
st_celda_b = ParagraphStyle("celdab", parent=st_celda, fontName="Helvetica-Bold")
st_codigo = ParagraphStyle("codigo", parent=st_p, fontName="Courier-Bold",
                           fontSize=10, textColor=ACCENT, alignment=0,
                           spaceAfter=0)
st_valor = ParagraphStyle("valor", parent=st_p, fontName="Helvetica-Bold",
                          fontSize=10, textColor=INK, alignment=0, spaceAfter=0)


def parrafo(texto, estilo=st_p):
    return Paragraph(texto, estilo)


def bloque_param(nombre, valor, que_es, implicacion, ajuste=None):
    """Bloque visual de un parámetro: cabecera nombre+valor y explicaciones."""
    cab = Table(
        [[Paragraph(nombre, st_codigo), Paragraph(valor, st_valor)]],
        colWidths=[95 * mm, 75 * mm],
    )
    cab.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ACCENT_SOFT),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 1, ACCENT),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("RIGHTPADDING", (1, 0), (1, 0), 8),
    ]))
    filas = [
        [Paragraph("Qué es", st_celda_b), Paragraph(que_es, st_celda)],
        [Paragraph("Qué implica", st_celda_b), Paragraph(implicacion, st_celda)],
    ]
    if ajuste:
        filas.append([Paragraph("Si se ajusta", st_celda_b),
                      Paragraph(ajuste, st_celda)])
    cuerpo = Table(filas, colWidths=[26 * mm, 144 * mm])
    cuerpo.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, LINEA),
    ]))
    return KeepTogether([cab, cuerpo, Spacer(1, 10)])


def concepto(titulo, texto):
    return KeepTogether([Paragraph(titulo, st_h2), Paragraph(texto, st_p)])


story = []

# ---------------------------------------------------------------- portada
story.append(Spacer(1, 30 * mm))
story.append(Paragraph("Manual de parámetros", st_titulo))
story.append(Paragraph("Bot de trading Polymarket - Bitcoin Up/Down 5 minutos",
                       ParagraphStyle("s2", parent=st_sub, fontSize=15,
                                      leading=19, textColor=INK)))
story.append(Spacer(1, 6))
story.append(Paragraph(
    f"Versión de estrategia: v2.3 &nbsp;&nbsp;|&nbsp;&nbsp; "
    f"Documento generado el {date.today().strftime('%d/%m/%Y')}", st_sub))
story.append(Spacer(1, 14))
aviso = Table([[Paragraph(
    "<b>MODO PAPER TRADING.</b> El bot opera con dinero virtual sobre datos "
    "100% reales de Polymarket. No hay un solo euro real en juego. El pase a "
    "dinero real exige, como mínimo: 500 operaciones resueltas en 2 o más "
    "semanas, beneficio positivo tras descontar slippage y un modelo bien "
    "calibrado.", st_celda)]], colWidths=[170 * mm])
aviso.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), ACCENT_SOFT),
    ("BOX", (0, 0), (-1, -1), 1, ACCENT),
    ("TOPPADDING", (0, 0), (-1, -1), 8),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
]))
story.append(aviso)
story.append(PageBreak())

# ------------------------------------------------- cómo funciona el bot
story.append(Paragraph("1. Cómo funciona el bot, en un minuto", st_h1))
story.append(parrafo(
    "Polymarket abre un mercado nuevo cada 5 minutos que pregunta: <b>¿el "
    "precio de Bitcoin al final de esta ventana estará por encima o por "
    "debajo del precio de inicio?</b> Hay dos 'acciones' (shares): la de "
    "<b>Up</b> (sube) y la de <b>Down</b> (baja). Cada share cuesta entre 0 y "
    "1 dólar y, si aciertas, se convierte exactamente en 1 dólar; si fallas, "
    "vale 0. Por eso el precio de cada lado es, a la vez, la probabilidad que "
    "el mercado le da a ese resultado: pagar 0,40 dólares por 'Down' es el "
    "mercado diciendo 'hay un 40% de que baje'."))
story.append(parrafo(
    "El bot hace esto en bucle, cada 5 segundos: (1) calcula su propia "
    "probabilidad de que Bitcoin suba usando un modelo estadístico; (2) mira "
    "los precios reales del mercado; (3) si su probabilidad es suficientemente "
    "mayor que el precio de un lado, compra ese lado (en virtual); y (4) al "
    "acabar la ventana, consulta el resultado oficial de Polymarket y apunta "
    "la ganancia o pérdida. Todo queda registrado en una base de datos para "
    "poder auditar y mejorar la estrategia con datos, no con sensaciones."))
story.append(parrafo(
    "La idea de fondo: <b>no se trata de adivinar hacia dónde va Bitcoin, "
    "sino de detectar cuándo el precio de un lado está mal puesto</b>. Se "
    "puede ganar dinero acertando menos del 50% de las veces si lo que se "
    "compra está sistemáticamente más barato de lo que vale."))

# ------------------------------------------------- conceptos clave
story.append(Paragraph("2. Conceptos clave (léelos antes de los parámetros)", st_h1))

story.append(concepto(
    "Probabilidad implícita (el precio ES una probabilidad)",
    "En estos mercados, precio y probabilidad son la misma cosa. Si la share "
    "de 'Up' cuesta 0,42 dólares, el mercado está diciendo que Bitcoin subirá "
    "el 42% de las veces en esa situación. Comprarla solo es buen negocio si "
    "la probabilidad real es mayor que 42%. Esta equivalencia es la regla de "
    "oro de todo el sistema."))

story.append(concepto(
    "p_modelo (la opinión del bot)",
    "Es la probabilidad que el bot calcula por su cuenta para cada lado, "
    "usando estadística: mira dónde está el precio de Bitcoin respecto a la "
    "apertura de la ventana, cuánto suele moverse por minuto (volatilidad) y "
    "cuánto tiempo queda. Con eso estima, mediante la campana de Gauss, la "
    "probabilidad de que la ventana cierre en 'Up'. Después la mezcla con la "
    "opinión del mercado (ver 'prior de mercado') para no fiarse ciegamente "
    "de sí mismo."))

story.append(concepto(
    "Edge (la ventaja): el concepto más importante del documento",
    "El edge es la diferencia entre lo que el bot cree que vale un lado y lo "
    "que cuesta comprarlo: <b>edge = p_modelo - precio de compra</b>. Ejemplo: "
    "si el bot estima que 'Down' tiene un 56% de probabilidad (0,56) y el "
    "mercado lo vende a 0,48, el edge es +0,08: en teoría estás comprando por "
    "48 céntimos algo que vale 56. Un edge positivo y sostenido es la única "
    "fuente de beneficio a largo plazo; sin edge, operar es tirar una moneda "
    "pagando comisión en forma de spread. Importante: el edge es una "
    "<i>estimación</i> del bot, no una verdad; puede estar equivocado, y por "
    "eso existen los filtros que siguen."))

story.append(concepto(
    "Selección adversa (por qué un edge enorme es una trampa)",
    "Si el mercado te 'regala' 20 o 30 céntimos de edge, lo más probable no "
    "es que todos los demás sean tontos: es que ellos ven algo que tú no ves "
    "(un movimiento de precio de hace 2 segundos, el dato oficial de "
    "Chainlink, mejor latencia). Los datos de este bot lo confirmaron: las "
    "operaciones con edge aparente mayor de 0,12 perdieron dinero en "
    "conjunto, mientras que las de edge moderado fueron las rentables. Por "
    "eso el bot rechaza los 'chollos' demasiado buenos: cuando el desacuerdo "
    "con el mercado es enorme, quien suele tener razón es el mercado."))

story.append(concepto(
    "Orderbook, bid y ask",
    "El orderbook es la lista de órdenes de compra y venta reales del "
    "mercado. El <b>ask</b> es el precio más barato al que alguien te vende "
    "ahora mismo (lo que pagas tú al comprar); el <b>bid</b> es lo más alto "
    "que alguien paga por comprarte a ti. La diferencia entre ambos (spread) "
    "es un coste oculto de cada operación. El bot siempre calcula el edge "
    "contra el ask real, no contra un precio teórico."))

story.append(concepto(
    "Criterio de Kelly (cuánto apostar)",
    "Fórmula clásica para decidir qué fracción del capital arriesgar cuando "
    "crees tener ventaja: apostar más cuanto mayor es la ventaja y más barato "
    "el precio, y nada si no hay ventaja. Kelly puro es agresivo y castiga "
    "mucho los errores de estimación, así que el bot usa solo un 25% de lo "
    "que Kelly sugiere, y además lo limita a un máximo del 2% del capital "
    "por operación. Es la diferencia entre una mala racha incómoda y una "
    "ruina."))

story.append(concepto(
    "Volatilidad realizada (sigma)",
    "Cuánto se mueve Bitcoin por minuto últimamente, medido sobre las velas "
    "de 1 minuto de las últimas 2 horas. Es el termómetro del modelo: con "
    "volatilidad alta, estar 30 dólares por debajo de la apertura no dice "
    "casi nada (da tiempo de sobra a recuperarlo); con volatilidad baja, esos "
    "mismos 30 dólares hacen 'Down' casi seguro. El modelo convierte la "
    "distancia a la apertura en probabilidad usando este termómetro."))

story.append(concepto(
    "Resolución oficial vs. proxy",
    "El resultado oficial de cada ventana lo decide Polymarket con el stream "
    "de datos Chainlink BTC/USD. El bot consulta ese resultado oficial vía "
    "API y solo si no llega en 15 minutos recurre a su propia medición "
    "(mediana de Binance, Coinbase y Kraken) como plan B. Se comprobó en la "
    "práctica que la medición propia puede discrepar de la oficial (~4% de "
    "las ventanas): otra razón para exigir edges con margen."))

story.append(PageBreak())

# ------------------------------------------------- parámetros
story.append(Paragraph("3. Parámetros, uno a uno", st_h1))
story.append(parrafo(
    "Valores vigentes en <b>bot/config.py</b> (versión v2.3). Cada bloque "
    "explica qué es el parámetro, qué efecto tiene en la operativa y qué "
    "pasaría al modificarlo."))

story.append(Paragraph("3.1 El mercado y el ritmo del bot", st_h2))

story.append(bloque_param(
    "window_seconds", "300 segundos (5 minutos)",
    "Duración de cada ventana de mercado 'Bitcoin Up or Down'. Lo fija "
    "Polymarket, no es una elección nuestra: cada 5 minutos nace un mercado "
    "nuevo con su apertura y su cierre.",
    "Define el ciclo completo de vida de una operación: como máximo hay una "
    "oportunidad de trade cada 5 minutos, y toda posición se resuelve sola "
    "en menos de 5 minutos más la liquidación. No existen posiciones "
    "colgadas días.",
    "No debe tocarse: está atado al producto de Polymarket. Existen ventanas "
    "de 1 hora si algún día se quisiera operar más despacio."))

story.append(bloque_param(
    "tick_seconds", "5 segundos",
    "Cada cuánto se despierta el bot para mirar el mercado: precios, "
    "orderbook, señales, resoluciones pendientes.",
    "Marca la 'velocidad de reflejos'. Con 5 segundos, el bot ve el mercado "
    "unas 60 veces por ventana; suficiente para paper trading, lentísimo "
    "comparado con los bots profesionales que operan en milisegundos. Es una "
    "de las razones de ser prudentes con los edges aparentes.",
    "Bajarlo daría reflejos más rápidos a costa de más llamadas a las APIs "
    "(con riesgo de bloqueo por exceso de peticiones). Subirlo ahorraría "
    "llamadas pero perdería oportunidades."))

story.append(Paragraph("3.2 Capital y gestión del riesgo", st_h2))

story.append(bloque_param(
    "bankroll_start", "1.000 $ (virtuales)",
    "Capital inicial del simulador. Solo se usa la primera vez; después el "
    "capital evoluciona con las ganancias y pérdidas y se guarda en la base "
    "de datos entre sesiones.",
    "Es la vara de medir del experimento: todos los porcentajes de riesgo "
    "(como el 2% por operación) se calculan sobre el capital vivo, así que "
    "las apuestas se encogen solas tras las pérdidas y crecen tras las "
    "ganancias.",
    "Cambiarlo no altera la estrategia, solo la escala. Reiniciarlo "
    "requeriría borrar la base de datos."))

story.append(bloque_param(
    "min_edge", "0,08 (8 céntimos) - subido en v2.3",
    "Ventaja mínima exigida para operar. Si el edge calculado no llega a 8 "
    "céntimos por share, el bot no compra, aunque sea positivo.",
    "Es el filtro de calidad principal. Un edge pequeño se lo comen los "
    "costes invisibles: el spread, el retraso de nuestros datos (segundos "
    "frente a milisegundos) y el ruido entre nuestras fuentes de precio y el "
    "dato oficial de Chainlink. El valor original era 0,05, pero la autopsia "
    "del 07/07/2026 (84 trades) fue contundente: la banda de edge 0,05-0,08 "
    "perdió dinero de forma consistente (39% de aciertos necesitando 43% "
    "para no perder, -120 $), mientras que la banda 0,08-0,12 ganó con "
    "significancia estadística (54% de aciertos vs 36,5% necesario, +244 $, "
    "z=+2,2). Subirlo a 0,08 es apostar por selectividad: menos operaciones, "
    "solo en el nicho con esperanza demostrada.",
    "Bajarlo = más operaciones pero de peor calidad media (el histórico dice "
    "que las de 0,05-0,08 pierden). Subirlo más estrecharía demasiado la "
    "banda operable (0,08-0,12). Cualquier ajuste, siempre desde la "
    "autopsia."))

story.append(bloque_param(
    "max_edge", "0,12 (12 céntimos) - 'bandera roja'",
    "Ventaja máxima aceptada. Si el edge aparente supera los 12 céntimos, el "
    "bot NO opera y lo anota como bandera roja.",
    "Es la defensa contra la selección adversa explicada en la sección 2. "
    "Un desacuerdo enorme con el mercado casi siempre significa que el "
    "mercado sabe algo que nosotros no (movimiento reciente que nuestras "
    "fuentes aún no reflejan, dato de Chainlink distinto). Los datos propios "
    "lo confirmaron: los trades con edge mayor de 0,12 perdieron dinero en "
    "conjunto. En resumen: el bot solo opera en la banda de edge entre 0,08 "
    "y 0,12 - ni migajas ni chollos sospechosos.",
    "Subirlo dejaría entrar los 'chollos' (histórico: malos). Bajarlo "
    "estrecharía la banda de oportunidades. Cualquier cambio debe salir de "
    "la autopsia de datos, no de la intuición."))

story.append(bloque_param(
    "max_stake_pct", "0,02 (2% del capital)",
    "Tope absoluto de lo que se arriesga en una sola operación, como "
    "porcentaje del capital vivo. Con 1.000 $, máximo 20 $ por trade.",
    "Es el seguro de vida del capital. Garantiza que ninguna operación, ni "
    "una racha mala, pueda hacer un agujero serio: 10 pérdidas seguidas al "
    "2% dejan aún el 82% del capital. También hace los resultados "
    "estadísticamente comparables entre sí, porque todas las apuestas pesan "
    "parecido.",
    "Subirlo acelera tanto las ganancias como la ruina; es lo último que se "
    "debe tocar y solo con un modelo ya validado. Bajarlo hace el "
    "experimento más lento pero más seguro."))

story.append(bloque_param(
    "kelly_fraction", "0,25 (un cuarto de Kelly)",
    "Fracción del tamaño 'óptimo' de Kelly que realmente se apuesta (ver "
    "concepto en la sección 2).",
    "Kelly puro asume que tu probabilidad es exacta; la nuestra es una "
    "estimación con error. Apostar solo el 25% de lo que Kelly sugiere "
    "protege de sobreapostar cuando el modelo se equivoca, que es lo normal. "
    "En la práctica: el tamaño final de cada apuesta es el menor entre 'un "
    "cuarto de Kelly' y 'el 2% del capital'.",
    "Valores típicos prudentes van de 0,1 a 0,5. Subirlo solo tendría "
    "sentido con un modelo demostradamente bien calibrado."))

story.append(bloque_param(
    "max_open_per_window", "1 operación por ventana",
    "Máximo de trades que el bot abre dentro de una misma ventana de 5 "
    "minutos.",
    "Evita que el bot se 'emborrache' con una sola idea: sin este límite, "
    "una señal persistente le haría comprar una y otra vez el mismo lado de "
    "la misma ventana, concentrando el riesgo en un único resultado de "
    "moneda al aire. Una ventana = una opinión = una apuesta.",
    "Subirlo multiplicaría el volumen de datos recogidos por hora, pero "
    "concentraría riesgo. Si algún día se sube, convendría exigir que las "
    "operaciones extra sean a mejor precio que la primera."))

story.append(bloque_param(
    "min_book_size", "50 shares en el mejor ask",
    "Liquidez mínima exigida: cuántas shares debe haber a la venta al mejor "
    "precio para que el bot considere operar contra él.",
    "Un precio sin volumen detrás es un espejismo: 3 shares a 0,40 no "
    "sostienen una operación real. Exigir 50 shares asegura que el precio "
    "contra el que calculamos el edge es un precio al que de verdad se "
    "podría ejecutar el tamaño de nuestra apuesta (~20 $ / precio medio 0,4 "
    "= ~50 shares).",
    "Subirlo haría las señales más realistas de ejecutar pero descartaría "
    "mercados finos. Es especialmente importante de revisar antes de pasar "
    "a real."))

story.append(bloque_param(
    "fee", "0,0 (sin comisión)",
    "Comisión por operación que se descuenta del edge antes de decidir.",
    "Polymarket no cobra comisión de trading en estos mercados a día de "
    "hoy, así que está a cero. El coste real de operar está en el spread y "
    "el slippage, no en comisiones.",
    "Si Polymarket introdujera comisiones, bastaría poner aquí su valor y "
    "todo el sistema las descontaría automáticamente de cada edge."))

story.append(bloque_param(
    "stop_after_losses", "5 pérdidas seguidas (kill-switch)",
    "Freno de emergencia: si el bot encadena 5 operaciones perdidas dentro "
    "de la sesión, deja de abrir posiciones nuevas.",
    "Una racha de 5 pérdidas seguidas puede ser mala suerte (pasa ~3% de "
    "las veces con un 50% de acierto), pero también puede señalar que el "
    "mercado ha cambiado de régimen y el modelo está desfasado. El "
    "kill-switch corta la hemorragia en ese segundo caso a cambio de perder "
    "un poco de actividad en el primero. Las posiciones ya abiertas se "
    "liquidan con normalidad; solo se frena abrir nuevas.",
    "Bajarlo lo hace más nervioso (salta con rachas normales); subirlo lo "
    "hace más tolerante. Cinco es un compromiso razonable para el tamaño de "
    "apuesta actual."))

story.append(bloque_param(
    "killswitch_cooldown_sec", "1.800 segundos (30 minutos)",
    "Cuánto tiempo permanece en pausa el bot después de saltar el "
    "kill-switch, antes de reanudar solo.",
    "La primera versión del freno bloqueaba el bot hasta que un humano lo "
    "reiniciara - incompatible con dejarlo trabajando desatendido (pasó en "
    "la práctica: estuvo horas parado sin que nadie lo supiera). Ahora "
    "descansa 30 minutos, tiempo de sobra para que el 'régimen raro' del "
    "mercado pase, y vuelve a operar con el contador de racha a cero.",
    "Más tiempo = más prudencia tras las rachas malas; menos = más "
    "actividad. Treinta minutos son 6 ventanas completas de distancia del "
    "episodio malo."))

story.append(bloque_param(
    "market_prior_weight", "0,3 (30% mercado, 70% modelo)",
    "Peso que se da a la opinión del mercado al calcular la probabilidad "
    "final. La probabilidad con la que decide el bot es una mezcla: 70% lo "
    "que dice su modelo estadístico + 30% lo que dice el precio medio del "
    "mercado.",
    "Es institucionalizar la humildad: el histórico demostró que el mercado "
    "acierta más que nuestro modelo en los desacuerdos grandes. Mezclar "
    "encoge automáticamente los edges extremos (los sospechosos) y apenas "
    "toca los moderados. Ejemplo: si el modelo dice 60% y el mercado 40%, "
    "la probabilidad final es 0,7 x 60 + 0,3 x 40 = 54% - el edge aparente "
    "de 20 se queda en 14.",
    "A 0 el bot se fía solo de sí mismo; a 1 sería un espejo del mercado "
    "(nunca vería edge y no operaría). El valor óptimo debe salir de "
    "comparar la calibración de modelo y mercado en la autopsia."))

story.append(PageBreak())
story.append(Paragraph("3.3 El modelo estadístico", st_h2))

story.append(bloque_param(
    "vol_lookback_min", "120 minutos (2 horas)",
    "Ventana de histórico con la que se mide la volatilidad realizada: la "
    "desviación típica de los movimientos de Bitcoin minuto a minuto en las "
    "últimas 2 horas.",
    "Es el termómetro central del modelo (ver sección 2): convierte 'Bitcoin "
    "está 25 $ por debajo de la apertura y quedan 3 minutos' en una "
    "probabilidad concreta. Dos horas de histórico equilibran estabilidad "
    "(no bailar con cada vela) y actualidad (enterarse cuando el mercado se "
    "acelera).",
    "Más corto = termómetro más nervioso y reactivo; más largo = más "
    "estable pero lento en detectar cambios de régimen de volatilidad."))

story.append(bloque_param(
    "vol_refresh_sec", "60 segundos",
    "Cada cuánto se recalcula la volatilidad (y el drift) descargando velas "
    "nuevas.",
    "La volatilidad de 2 horas cambia despacio: recalcularla cada minuto es "
    "más que suficiente y evita castigar las APIs públicas en cada tick de "
    "5 segundos.",
    "Sin impacto real en la operativa salvo valores extremos."))

story.append(bloque_param(
    "drift_lookback_min", "30 minutos",
    "Ventana con la que se mediría la tendencia reciente (drift): el "
    "movimiento medio por minuto de la última media hora.",
    "Hoy es un parámetro dormido, porque el peso de la tendencia está a "
    "cero (ver el siguiente). Se conserva medido y registrado para que la "
    "autopsia pueda estudiar si alguna definición de tendencia aporta valor "
    "en algún régimen concreto.",
    "Irrelevante mientras drift_weight sea 0."))

story.append(bloque_param(
    "drift_weight", "0,0 (tendencia DESACTIVADA en v2.2)",
    "Cuánto influye la tendencia de los últimos 30 minutos en la "
    "probabilidad del modelo. A cero, el modelo asume que, a 5 minutos "
    "vista, subir y bajar parten de probabilidades simétricas alrededor del "
    "precio actual.",
    "Esta es la cicatriz de la lección más cara del proyecto. La versión "
    "v2/v2.1 usaba la tendencia con peso 0,5 y la autopsia de 35 trades "
    "reveló un sesgo brutal: las apuestas 'Up' ganaban solo el 26% (-154 $) "
    "mientras las 'Down' ganaban el 56% (+63 $). El momentum de 30 minutos "
    "no se sostenía a 5 minutos vista: Bitcoin revertía más de lo que "
    "continuaba, y el modelo compraba sistemáticamente el lado equivocado. "
    "Se desactivó en v2.2 (un solo cambio, medible) y sigue desactivada en "
    "v2.3.",
    "Reactivarlo (por ejemplo a 0,2-0,3, o con otra definición de "
    "tendencia) solo si la autopsia con muestra suficiente lo respalda. La "
    "autopsia de v2.2 (07/07/2026) confirmó que sin tendencia el sesgo por "
    "lado desapareció: Up y Down quedaron equilibrados (48% / 40% de "
    "aciertos, ambos sobre su breakeven)."))

story.append(Paragraph("3.4 Tiempos dentro de cada ventana", st_h2))

story.append(bloque_param(
    "open_capture_max_delay", "12 segundos",
    "Margen máximo, desde que empieza una ventana, para capturar el precio "
    "de apertura de Bitcoin. Si el bot no llega a tiempo (estaba apagado, "
    "el PC dormía, la red falló), marca la ventana como 'no operable' y la "
    "salta entera.",
    "Todo el modelo gira alrededor de la pregunta '¿cerrará por encima o "
    "por debajo de la apertura?'. Con una apertura capturada tarde, esa "
    "referencia es falsa y cualquier probabilidad calculada sobre ella, "
    "basura. Por eso el bot prefiere no operar una ventana a operarla con "
    "datos malos - es la razón de los mensajes 'sin open (inicio perdido)' "
    "del log al arrancar a mitad de ventana.",
    "Más margen = más ventanas operables pero con referencia menos fiel. "
    "Doce segundos permiten hasta 2 ticks de retraso."))

story.append(bloque_param(
    "no_trade_last_sec", "45 segundos finales",
    "El bot no abre operaciones nuevas en los últimos 45 segundos de cada "
    "ventana.",
    "Al final de la ventana los precios se vuelven extremos (0,05 / 0,95) y "
    "el resultado depende de segundos y de céntimos de diferencia entre "
    "nuestras fuentes y el dato oficial de Chainlink. En esa zona, nuestro "
    "retraso de datos de varios segundos es letal: creeríamos ver gangas "
    "que son solo información vieja. Mejor dejar pasar el final de la "
    "película.",
    "Ampliarlo recorta oportunidades legítimas de mitad de ventana; "
    "reducirlo expone al ruido del cierre."))

story.append(Paragraph("3.5 Resolución de las operaciones", st_h2))

story.append(bloque_param(
    "settle_poll_sec", "30 segundos",
    "Cada cuánto pregunta el bot a la API de Polymarket si una ventana "
    "terminada ya tiene resultado oficial.",
    "Tras cerrar una ventana, Polymarket tarda 1-4 minutos en publicar la "
    "liquidación oficial (oráculo Chainlink). El bot pregunta cada 30 "
    "segundos hasta obtenerla, y solo entonces convierte la posición en "
    "ganancia o pérdida. Por eso una operación puede verse 'abierta' hasta "
    "8-9 minutos con total normalidad: 5 de ventana + la liquidación.",
    "Sin impacto en resultados; solo en cuánto tarda el marcador en "
    "actualizarse y en el volumen de llamadas a la API."))

story.append(bloque_param(
    "settle_timeout_sec", "900 segundos (15 minutos)",
    "Tiempo máximo de espera por la liquidación oficial. Superado, el bot "
    "resuelve con su plan B: comparar la apertura y el cierre que él mismo "
    "midió (mediana de Binance, Coinbase y Kraken).",
    "Garantiza que ninguna posición quede colgada para siempre si la API "
    "oficial falla. El plan B es menos fiable que el dato oficial (se ha "
    "medido ~4% de discrepancia en ventanas muy ajustadas), por eso es "
    "último recurso y queda marcado en la base de datos como 'proxy' para "
    "poder auditarlo.",
    "En la práctica solo actúa cuando hay problemas de red o de API; con "
    "funcionamiento normal, la liquidación oficial llega mucho antes."))

story.append(PageBreak())

# ------------------------------------------------- ejemplo completo
story.append(Paragraph("4. Una operación de ejemplo, de principio a fin", st_h1))
story.append(parrafo(
    "<b>21:15:00</b> - Empieza la ventana. El bot captura la apertura: "
    "Bitcoin a 61.602,84 $. (Si hubiera llegado más de 12 segundos tarde, "
    "saltaría la ventana entera.)"))
story.append(parrafo(
    "<b>21:15:17</b> - Bitcoin cae a 61.601,70 $. El modelo calcula: con "
    "esta volatilidad y 4,7 minutos restantes, P(Down) = 56,5%. Mezcla con "
    "el mercado (30%): la probabilidad final queda en ~55%. El mejor ask de "
    "'Down' está a 0,49 con 580 shares disponibles (pasa el filtro de "
    "liquidez). Edge = 0,555 - 0,49 = +0,065: dentro de la banda válida "
    "vigente entonces (0,05 a 0,12; con la banda actual de v2.3, 0,08 a "
    "0,12, este trade ya no se abriría - la autopsia demostró que su banda "
    "perdía dinero). Kelly sugiere arriesgar el 3,2% del capital; el 25% de "
    "eso es 0,8%... pero se aplica el menor entre eso y el tope del 2%: "
    "apuesta 18,21 $ y recibe 37,2 shares. Queda registrado: probabilidad, "
    "edge, precios, todo."))
story.append(parrafo(
    "<b>21:20:00</b> - Cierra la ventana. Bitcoin: 61.501,38 $, por debajo "
    "de la apertura. Todavía no se apunta nada: falta el dato oficial."))
story.append(parrafo(
    "<b>21:24:39</b> - La API de Polymarket publica la liquidación oficial: "
    "'Down' (método: gamma, no proxy). Las 37,2 shares comparadas a 0,49 se "
    "convierten en 37,2 $: beneficio de +18,95 $ sobre 18,21 $ arriesgados. "
    "El capital se actualiza y la operación queda cerrada como 'won' en la "
    "base de datos, lista para la próxima autopsia."))

# ------------------------------------------------- aprendizaje y versiones
story.append(Paragraph("5. Cómo aprende el sistema (y qué no hace)", st_h1))
story.append(parrafo(
    "Además de las operaciones, el bot guarda <b>todas las señales que "
    "evalúa</b>, también las que rechaza y por qué (edge insuficiente, "
    "bandera roja, kill-switch...). Como cada ventana acaba teniendo "
    "resultado, se puede medir después qué habría pasado con otros filtros: "
    "es el análisis contrafactual que hace el script de autopsia "
    "(autopsy.py). La autopsia mide la calibración del modelo frente al "
    "mercado, los sesgos por lado y por banda de edge, y <b>solo propone</b> "
    "cambios cuando hay muestra suficiente (30 o más casos y significancia "
    "estadística); nunca los aplica sola. El protocolo acordado: cada "
    "versión corre intacta hasta acumular 30-50 operaciones, autopsia, y "
    "UN cambio cada vez."))

story.append(parrafo(
    "<b>Historia de versiones hasta hoy:</b> v1 (modelo sin tendencia) "
    "compraba sistemáticamente el lado barato contra la tendencia: 1 ganada "
    "de 7. v2 añadió la tendencia de 30 minutos y brilló una noche (11/15), "
    "pero la muestra grande de v2.1 destapó que ese brillo era del régimen "
    "de mercado, no del modelo: el momentum generaba un sesgo sistemático "
    "hacia 'Up' que perdía dinero. v2.1 añadió la banda de edge, el prior "
    "de mercado y el kill-switch (los tres validados por los datos). v2.2 "
    "desactivó la tendencia y equilibró los lados, pero su autopsia (84 "
    "trades) reveló dos cosas: que el modelo en global aún no supera al "
    "mercado (Brier 0,2157 vs 0,2141) y que todo el beneficio se concentraba "
    "en la banda de edge 0,08-0,12 (+244 $, z=+2,2) mientras la banda "
    "0,05-0,08 perdía (-120 $). v2.3, la actual, subió min_edge a 0,08: "
    "selectividad antes que actividad. Criterio de parada acordado: si con "
    "la banda buena el modelo sigue sin aportar sobre el mercado en la "
    "próxima muestra, se replantea el experimento entero."))

story.append(Paragraph("6. Las reglas que no se negocian", st_h1))
story.append(parrafo(
    "1) <b>Paper trading hasta que los datos manden lo contrario</b>: "
    "mínimo 500 operaciones resueltas en 2 o más semanas, beneficio "
    "positivo tras descontar ~1-2 céntimos de slippage por operación, y "
    "winrate real coherente con las probabilidades del modelo "
    "(calibración). 2) <b>Un cambio por iteración</b>, siempre motivado por "
    "la autopsia, nunca por una racha corta. 3) <b>El mercado es el rival a "
    "respetar</b>: si el bot cree ver un regalo enorme, se asume que el "
    "equivocado es el bot. 4) Pasar a dinero real exigiría además wallet en "
    "Polygon con USDC, integración de órdenes reales y revisar las "
    "restricciones jurisdiccionales de Polymarket - es una decisión "
    "separada y consciente, no un deslizamiento gradual."))

story.append(Spacer(1, 8))
story.append(Paragraph(
    "Generado automáticamente desde bot/config.py (v2.3). Si los valores "
    "del código cambian, regenerar con: venv\\Scripts\\python.exe "
    "polymarket-bot\\generar_manual_parametros.py", st_peq))


def pie(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRIS)
    canvas.drawString(20 * mm, 12 * mm,
                      "Bot Polymarket BTC Up/Down - Manual de parámetros (v2.3)")
    canvas.drawRightString(190 * mm, 12 * mm, f"Pág. {doc.page}")
    canvas.setStrokeColor(LINEA)
    canvas.line(20 * mm, 16 * mm, 190 * mm, 16 * mm)
    canvas.restoreState()


doc = SimpleDocTemplate(
    str(SALIDA), pagesize=A4,
    leftMargin=20 * mm, rightMargin=20 * mm,
    topMargin=18 * mm, bottomMargin=22 * mm,
    title="Manual de parámetros - Bot Polymarket BTC Up/Down",
    author="MerakIA",
)
doc.build(story, onFirstPage=pie, onLaterPages=pie)
print(f"OK -> {SALIDA}")
