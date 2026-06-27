import json
import re
import os
import base64
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

ALERGENOS_ES = {
    "gluten": "Gluten",
    "lactosa": "Lácteos",
    "huevo": "Huevo",
    "pescado": "Pescado",
    "marisco": "Marisco",
    "frutos_secos": "Frutos secos",
    "soja": "Soja",
    "apio": "Apio",
}

DIETAS_ES = {
    "vegano": "Vegano",
    "vegetariano": "Vegetariano",
    "sin_gluten": "Sin gluten",
    "sin_lactosa": "Sin lactosa",
}


def importar_platos_desde_texto(texto: str) -> list[dict]:
    """Extrae platos estructurados desde texto libre (de un PDF/TXT importado)."""

    prompt = f"""Eres un asistente especializado en restaurantes. El chef te ha proporcionado un documento con su carta o lista de platos.

Extrae TODOS los platos que encuentres y devuelve un JSON estructurado.

Para cada plato infiere lo mejor que puedas:
- nombre: nombre del plato
- categoria: "primero", "segundo" o "postre"
- subtipo: tipo específico dentro de la categoría (ej: "ensalada", "pasta", "crema", "sopa", "arroces", "frituras", "plancha", "guiso", "postre_frio", "postre_caliente", etc.)
- proteina: "pollo", "cerdo", "ternera", "cordero", "pescado", "marisco", "huevo", "vegetal", "ninguna"
- coste_racion: coste estimado en euros por ración (si no aparece en el documento, estima según el tipo de plato; menú de restaurante medio en España)
- tiempo_prep: minutos estimados de preparación
- alergenos: lista con los que apliquen: ["gluten","lactosa","huevo","pescado","marisco","frutos_secos","soja","apio"] o ["ninguno"]
- dietas: lista de etiquetas aplicables: ["vegano","vegetariano","sin_gluten","sin_lactosa"] — vacío si ninguna aplica
- descripcion: descripción breve o ingredientes principales

DOCUMENTO DEL CHEF:
---
{texto}
---

Responde ÚNICAMENTE con este JSON (array, sin texto adicional, sin markdown):
[
  {{
    "nombre": "...",
    "categoria": "...",
    "subtipo": "...",
    "proteina": "...",
    "coste_racion": 0.00,
    "tiempo_prep": 20,
    "alergenos": ["..."],
    "dietas": ["..."],
    "descripcion": "..."
  }}
]"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def importar_platos_desde_pdf(pdf_bytes: bytes) -> list[dict]:
    """Extrae platos directamente desde bytes de un PDF usando la API de Claude."""
    import base64

    prompt = """Eres un asistente especializado en restaurantes. El chef te ha subido un documento (carta, lista de platos o recetario).

Extrae TODOS los platos que encuentres y devuelve un JSON estructurado.

Para cada plato infiere lo mejor que puedas:
- nombre, categoria (primero/segundo/postre), subtipo (ensalada/pasta/crema/sopa/arroces/frituras/plancha/guiso/etc.)
- proteina (pollo/cerdo/ternera/cordero/pescado/marisco/huevo/vegetal/ninguna)
- coste_racion en euros (estima si no aparece), tiempo_prep en minutos
- alergenos: lista de ["gluten","lactosa","huevo","pescado","marisco","frutos_secos","soja","apio"] o ["ninguno"]
- dietas: ["vegano","vegetariano","sin_gluten","sin_lactosa"] — vacío si ninguna
- descripcion breve

Responde ÚNICAMENTE con un array JSON, sin texto adicional ni markdown."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": base64.standard_b64encode(pdf_bytes).decode("utf-8"),
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def _historial_txt(historial: list[dict] | None) -> str:
    """Genera el bloque de texto de rotación para el prompt."""
    if not historial:
        return ""
    lineas = ["\nROTACIÓN — MENÚS RECIENTES (EVITAR REPETIR):"]
    for m in historial:
        proteinas = []
        platos_nombres = []
        for categoria in ("primeros", "segundos", "postres"):
            for p in m.get("contenido", {}).get(categoria, []):
                platos_nombres.append(p.get("nombre", ""))
        lineas.append(f"  · {m.get('fecha', '?')} ({m.get('nombre', '')}): {', '.join(platos_nombres)}")
        for p in m.get("contenido", {}).get("segundos", []):
            if p.get("proteina") and p["proteina"] != "ninguna":
                proteinas.append(p["proteina"])
    if proteinas:
        lineas.append(f"  Proteínas recientes en segundos: {', '.join(set(proteinas))}")
    lineas.append("  → Varía las proteínas y evita repetir los mismos platos de las semanas anteriores.")
    return "\n".join(lineas)


def generar_menu(
    platos_disponibles: list[dict],
    despensa: list[dict],
    precio_menu: float,
    num_primeros: int,
    num_segundos: int,
    num_postres: int,
    reglas_extra: str = "",
    plantilla_libre: str = "",
    historial: list[dict] | None = None,
) -> dict:
    """Llama a Claude para generar combinaciones de menú optimizadas."""

    primeros = [p for p in platos_disponibles if p["categoria"] == "primero"]
    segundos = [p for p in platos_disponibles if p["categoria"] == "segundo"]
    postres = [p for p in platos_disponibles if p["categoria"] == "postre"]

    despensa_txt = ""
    if despensa:
        despensa_txt = "\n\nINGREDIENTES EN DESPENSA (prioriza platos que los usen):\n"
        for item in despensa:
            linea = f"- {item['ingrediente']}"
            if item.get("cantidad"):
                linea += f" ({item['cantidad']} {item.get('unidad', '')})"
            if item.get("caducidad"):
                linea += f" [caduca: {item['caducidad']}]"
            if item.get("nota"):
                linea += f" — {item['nota']}"
            despensa_txt += linea + "\n"

    def plato_txt(p):
        alergenos = json.loads(p.get("alergenos", "[]"))
        dietas = json.loads(p.get("dietas", "[]"))
        subtipo = p.get("subtipo", "") or ""
        return (
            f"  - ID{p['id']} | {p['nombre']} | subtipo: {subtipo if subtipo else '—'} | proteína: {p.get('proteina','ninguna')} | "
            f"coste: {p['coste_racion']}€ | alérgenos: {','.join(alergenos) if alergenos and alergenos[0]!='ninguno' else 'ninguno'} | "
            f"dietas: {','.join(dietas) if dietas else 'ninguna'}"
        )

    primeros_txt = "\n".join(plato_txt(p) for p in primeros) or "No hay primeros disponibles."
    segundos_txt = "\n".join(plato_txt(p) for p in segundos) or "No hay segundos disponibles."
    postres_txt = "\n".join(plato_txt(p) for p in postres) or "No hay postres disponibles."

    estructura_txt = ""
    if plantilla_libre:
        estructura_txt = f"""
ESTRUCTURA PERSONALIZADA DEL CHEF (PRIORIDAD MÁXIMA):
{plantilla_libre}

Respeta exactamente los tipos y cantidades que el chef ha indicado. El campo "subtipo" de cada plato te indica a qué tipo pertenece.
"""
    else:
        estructura_txt = f"""
ESTRUCTURA DEL MENÚ:
- Número de opciones de primero: {num_primeros}
- Número de opciones de segundo: {num_segundos}
- Número de opciones de postre: {num_postres}
"""

    prompt = f"""Eres un chef profesional y experto en nutrición. Debes crear UN menú del día completo para un restaurante.

PRECIO DEL MENÚ: {precio_menu}€
{estructura_txt}

PLATOS DISPONIBLES:
PRIMEROS:
{primeros_txt}

SEGUNDOS:
{segundos_txt}

POSTRES:
{postres_txt}
{despensa_txt}

REGLAS OBLIGATORIAS:
1. El coste medio por comensal NO puede superar el {int(precio_menu * 0.35)}% del precio del menú = {precio_menu * 0.35:.2f}€ (margen food cost máximo 35%)
2. No repetir la misma proteína más de 1 vez entre los segundos seleccionados
3. Intentar incluir al menos 1 opción apta para celíacos (sin_gluten) en primeros Y en segundos
4. Intentar incluir al menos 1 opción vegana o vegetariana
5. Equilibrar texturas y temperaturas (no 3 cremas, no 3 platos fritos, etc.)
6. Priorizar ingredientes de la despensa si los hay (especialmente los que caducan pronto)
{f'7. {reglas_extra}' if reglas_extra else ''}
{_historial_txt(historial)}

RESPONDE ÚNICAMENTE con este JSON (sin texto adicional, sin markdown):
{{
  "primeros": [
    {{"id": <ID del plato>, "nombre": "<nombre>", "coste": <coste>, "dietas": ["..."], "alergenos": ["..."]}}
  ],
  "segundos": [
    {{"id": <ID del plato>, "nombre": "<nombre>", "coste": <coste>, "dietas": ["..."], "alergenos": ["..."]}}
  ],
  "postres": [
    {{"id": <ID del plato>, "nombre": "<nombre>", "coste": <coste>, "dietas": ["..."], "alergenos": ["..."]}}
  ],
  "coste_medio_estimado": <float>,
  "margen_estimado": <float en %>,
  "notas_chef": "<explicación breve de las decisiones tomadas, máx 3 líneas>",
  "alertas": ["<lista de alertas si no se pudo cumplir alguna regla>"]
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    # Limpiar si viene con ```json
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def analizar_escandallo(nombre_plato: str, ingredientes_txt: str, precio_menu: float) -> dict:
    """Analiza si un plato encaja en el food cost del menú."""

    prompt = f"""Eres un experto en gestión de costes de restaurante.

Analiza este escandallo:
- Plato: {nombre_plato}
- Precio del menú: {precio_menu}€
- Food cost objetivo: máximo 35% = {precio_menu * 0.35:.2f}€ por ración

Ingredientes proporcionados por el cocinero:
{ingredientes_txt}

Responde ÚNICAMENTE con este JSON:
{{
  "coste_estimado": <float>,
  "encaja_en_menu": <true/false>,
  "margen": "<X%>",
  "sugerencias": "<máx 2 líneas con consejos para ajustar el coste si no encaja>",
  "desglose": [
    {{"ingrediente": "<nombre>", "coste_estimado": <float>}}
  ]
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def analizar_foto_despensa(imagen_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    """Analiza una foto de nevera/despensa y devuelve lista de ingredientes detectados."""

    prompt = """Eres un chef profesional con 20 años de experiencia en control de inventario de restaurante.
Analiza esta foto del frigorífico, cámara o despensa.
Lista todos los ingredientes visibles de forma clara.

Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:

{
  "ingredientes": [
    {
      "ingrediente": "Bacalao fresco",
      "cantidad": "2.5 kg",
      "nota": "Hay que gastarlo esta semana"
    }
  ]
}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": base64.standard_b64encode(imagen_bytes).decode("utf-8"),
                    },
                },
            ],
        }],
    )

    texto = response.content[0].text.strip()
    json_match = re.search(r'\{[\s\S]*\}', texto)
    if json_match:
        return json.loads(json_match.group())
    return {"ingredientes": []}


def modo_escandalo(
    sobras: list[dict],
    precio_menu: float,
    num_platos: int = 3,
    estilo: str = "libre",
) -> dict:
    """A partir de sobras e ingredientes a punto de caducar, genera platos de aprovechamiento creativos."""

    sobras_txt = "\n".join(
        f"- {s['ingrediente']} ({s.get('cantidad', '?')}) — {s.get('nota', '')}"
        for s in sobras
    )

    estilos = {
        "libre": "Cualquier tipo de plato, máxima creatividad.",
        "tapas": "Tapas y platillos pequeños, presentación informal.",
        "fusion": "Cocina fusión, combinaciones atrevidas e inesperadas.",
        "tradicional": "Recetas de cocina tradicional española, de abuela.",
    }
    estilo_desc = estilos.get(estilo, estilos["libre"])

    prompt = f"""Eres un chef estrella Michelin especializado en cocina de aprovechamiento y desperdicio cero.

El restaurante tiene estos ingredientes sobrantes o a punto de caducar:
{sobras_txt}

MISIÓN: Crear {num_platos} platos ORIGINALES y APETECIBLES usando principalmente estos ingredientes.
Estilo: {estilo_desc}
Precio del menú objetivo: {precio_menu}€ (food cost máximo 35% = {precio_menu * 0.35:.2f}€/ración)

REGLAS:
- Los platos deben ser atractivos y vendibles, no "plato de restos"
- Pon nombres creativos y apetecibles a cada plato
- Usa las sobras como ingrediente estrella, no como relleno
- Estima el coste por ración siendo realista

Responde ÚNICAMENTE con este JSON:
{{
  "platos": [
    {{
      "nombre": "<nombre creativo del plato>",
      "descripcion": "<descripción apetecible de 1-2 líneas>",
      "ingredientes_usados": ["<ingrediente de la lista de sobras>"],
      "ingredientes_extra": ["<ingredientes básicos que habría que añadir>"],
      "categoria": "primero|segundo|postre",
      "coste_estimado": <float>,
      "tiempo_prep": <minutos>,
      "wow_factor": "<por qué este plato va a sorprender al cliente, 1 línea>"
    }}
  ],
  "ahorro_estimado": "<texto breve: cuánto desperdicio se evita>",
  "consejo_chef": "<consejo profesional sobre aprovechamiento, máx 2 líneas>"
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def _parse_raw(raw: str) -> dict:
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def generar_briefing(
    menu_hoy: dict,
    despensa: list,
    num_cubiertos: int,
    fecha: str,
    hora_servicio: str = "mediodía",
) -> dict:
    """Genera el briefing diario de cocina: mise en place, tareas y alertas."""

    primeros = [p["nombre"] for p in menu_hoy.get("primeros", [])]
    segundos = [p["nombre"] for p in menu_hoy.get("segundos", [])]
    postres = [p["nombre"] for p in menu_hoy.get("postres", [])]

    despensa_txt = ""
    if despensa:
        despensa_txt = "\nDESPENSA DISPONIBLE:\n"
        for d in despensa:
            linea = f"- {d['ingrediente']}"
            if d.get("cantidad"):
                linea += f" ({d['cantidad']} {d.get('unidad','')})"
            if d.get("caducidad") and d["caducidad"] != "None":
                linea += f" [caduca: {d['caducidad']}]"
            despensa_txt += linea + "\n"

    prompt = (
        "Eres el jefe de cocina mas organizado del mundo. "
        "Genera el briefing diario completo para el equipo de cocina.\n\n"
        f"DATOS DEL SERVICIO:\n"
        f"- Fecha: {fecha}\n"
        f"- Servicio: {hora_servicio}\n"
        f"- Cubiertos esperados: {num_cubiertos}\n\n"
        f"MENU DEL DIA:\n"
        f"- Primeros: {', '.join(primeros) if primeros else 'No definido'}\n"
        f"- Segundos: {', '.join(segundos) if segundos else 'No definido'}\n"
        f"- Postres: {', '.join(postres) if postres else 'No definido'}\n"
        f"{despensa_txt}\n"
        f"Genera un briefing profesional. Para el mise en place calcula cantidades REALES para {num_cubiertos} cubiertos.\n\n"
        'Responde UNICAMENTE con este JSON:\n'
        '{\n'
        '  "resumen_servicio": "<1 frase motivadora para el equipo>",\n'
        '  "mise_en_place": [\n'
        '    {\n'
        '      "ingrediente": "<nombre>",\n'
        f'      "cantidad_total": "<cantidad exacta para {num_cubiertos} cubiertos>",\n'
        '      "para_plato": "<nombre del plato>",\n'
        '      "prioridad": "alta|media|baja",\n'
        '      "tiempo_prep": "<estimacion>",\n'
        '      "tecnica": "<corte, coccion o temperatura clave>"\n'
        '    }\n'
        '  ],\n'
        '  "orden_tareas": [\n'
        '    {\n'
        '      "hora": "<hora sugerida, ej: 08:00>",\n'
        '      "tarea": "<descripcion concreta>",\n'
        '      "responsable": "partida fría|caliente|postres|general",\n'
        '      "duracion_min": 20\n'
        '    }\n'
        '  ],\n'
        '  "alertas": ["<alerta importante>"],\n'
        '  "consejo_servicio": "<consejo profesional para hoy, 1-2 lineas>"\n'
        '}'
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_raw(response.content[0].text.strip())


def generar_ficha_tecnica(plato: dict) -> dict:
    """Genera la ficha técnica completa de un plato."""

    alergenos = json.loads(plato.get("alergenos", "[]"))
    dietas = json.loads(plato.get("dietas", "[]"))
    alergenos_str = ', '.join(alergenos) if alergenos and alergenos[0] != 'ninguno' else 'Ninguno'
    dietas_str = ', '.join(dietas) if dietas else 'Sin restricciones especiales'

    prompt = (
        "Eres un chef tecnico experto en fichas de cocina profesionales.\n\n"
        "Genera la ficha tecnica completa para este plato:\n"
        f"- Nombre: {plato['nombre']}\n"
        f"- Categoria: {plato['categoria']}\n"
        f"- Proteina principal: {plato.get('proteina', 'ninguna')}\n"
        f"- Coste registrado: {plato['coste_racion']}EUR/racion\n"
        f"- Tiempo de preparacion: {plato.get('tiempo_prep', 20)} min\n"
        f"- Alergenos: {alergenos_str}\n"
        f"- Apto para: {dietas_str}\n"
        f"- Descripcion base: {plato.get('descripcion', 'No especificada')}\n\n"
        "Crea una receta realista y coherente. Cantidades para 1 racion y para 10 raciones.\n\n"
        "Responde UNICAMENTE con un JSON con estas claves:\n"
        "nombre, categoria, descripcion_comercial, ingredientes (array con nombre/cantidad_1/cantidad_10/precio_unitario/coste_1),\n"
        "elaboracion (array de pasos), presentacion, temperatura_servicio, tiempo_total_prep (int minutos),\n"
        "coste_total_1_racion (float), precio_venta_sugerido_30pct (float), precio_venta_sugerido_35pct (float),\n"
        f"alergenos {json.dumps(alergenos)}, dietas {json.dumps(dietas)}, conservacion, consejo_chef."
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_raw(response.content[0].text.strip())



def escandallo_avanzado(nombre_plato: str, ingredientes_txt: str, precio_venta: float) -> dict:
    """Escandallo de alta cocina con rendimiento/merma por producto.

    A diferencia del escandallo simple, aquí cada ingrediente parte de un precio de
    compra en bruto y un % de rendimiento (lo aprovechable tras limpiar, desespinar,
    deshuesar...). El coste real se calcula sobre el producto NETO, que es lo que de
    verdad sangra el margen en cocina de producto caro.
    """

    prompt = f"""Eres un jefe de cocina de un restaurante gastronómico (nivel estrella Michelin) y experto en control de costes de producto de alta gama.

Analiza el escandallo REAL de este plato teniendo en cuenta el RENDIMIENTO de cada producto (la merma de limpieza, desespinado, deshuesado, reducción, etc.). El coste real se calcula sobre el peso NETO aprovechable, no sobre el peso de compra.

- Plato: {nombre_plato}
- Precio de venta del plato / del pase en carta: {precio_venta}€

Ingredientes proporcionados por el cocinero (producto, cantidad neta necesaria en el plato, precio de compra y rendimiento aproximado si lo indica):
{ingredientes_txt}

Para cada ingrediente:
- Si te da un rendimiento (%), úsalo. Si no, estima un rendimiento realista según el producto (ej: pescado entero ~45-55%, solomillo limpio ~85%, verdura de hoja ~70%, marisco con cáscara ~35-40%).
- Calcula la cantidad BRUTA a comprar = cantidad neta / rendimiento.
- Calcula el coste real = cantidad bruta × precio de compra.

Después evalúa el food cost del plato (coste real / precio de venta) y da recomendaciones profesionales de optimización SIN bajar la calidad percibida (aprovechamiento de mermas nobles para fondos/guarniciones, ajuste de gramaje, producto de temporada, etc.).

Responde ÚNICAMENTE con este JSON (sin texto adicional, sin markdown):
{{
  "desglose": [
    {{
      "ingrediente": "<nombre>",
      "cantidad_neta": "<cantidad usada en el plato>",
      "rendimiento_pct": <int>,
      "cantidad_bruta": "<cantidad a comprar>",
      "precio_compra": "<€/kg o €/ud>",
      "coste_real": <float>,
      "merma_coste": <float>
    }}
  ],
  "coste_total_real": <float>,
  "coste_total_sin_merma": <float>,
  "sobrecoste_por_merma": <float>,
  "food_cost_pct": <float>,
  "margen_bruto": <float>,
  "valoracion": "<excelente|correcto|ajustado|critico>",
  "mermas_aprovechables": ["<merma noble y para qué usarla>"],
  "recomendaciones": ["<recomendación concreta de optimización sin perder calidad>"],
  "precio_venta_sugerido_30pct": <float>
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_raw(response.content[0].text.strip())


def costear_menu_degustacion(
    nombre_menu: str,
    pases_txt: str,
    precio_menu: float,
    num_comensales_servicio: int = 30,
    maridaje_incluido: bool = False,
) -> dict:
    """Costea un menú degustación multipase y la IA actúa como ANALISTA, no como creadora.

    En alta cocina el chef NO quiere que la IA invente su menú: quiere que le controle el
    food cost pase por pase, le valide la progresión (intensidad, texturas, temperaturas)
    y le diga dónde se le va el margen. Ese es el rol aquí.
    """

    maridaje_txt = (
        "El precio incluye maridaje de vinos: considera ~30-35% del coste como bebida."
        if maridaje_incluido else
        "El precio es solo de comida (sin maridaje)."
    )

    prompt = f"""Eres el director gastronómico y controller de un restaurante de alta cocina (nivel estrella Michelin).
NO debes reinventar ni sustituir el menú del chef: tu trabajo es ANALIZARLO con rigor de costes y de sala.

MENÚ DEGUSTACIÓN: {nombre_menu}
- Precio de venta del menú por comensal: {precio_menu}€
- {maridaje_txt}
- Comensales por servicio (para compra y mise en place): {num_comensales_servicio}

PASES DEL MENÚ (el chef indica cada pase y, cuando puede, sus ingredientes y coste aproximado):
{pases_txt}

Tu análisis debe:
1. Estimar el coste de materia prima por comensal de CADA pase (sé realista con producto de alta gama y su merma).
2. Sumar el coste total del menú y calcular el food cost (coste/precio). En alta cocina el food cost objetivo suele ser 28-35%.
3. Evaluar la PROGRESIÓN gastronómica: arranque, subida de intensidad, equilibrio de proteínas, alternancia de temperaturas y texturas, transición a postre.
4. Señalar los pases que más comprometen el margen y proponer ajustes que NO degraden la experiencia (gramaje, mermas nobles, producto de temporada, sustitución de guarnición cara).
5. Detectar riesgos de alérgenos y huecos para una versión vegetariana del menú (clave en alta cocina hoy).

Responde ÚNICAMENTE con este JSON (sin texto adicional, sin markdown):
{{
  "pases": [
    {{
      "orden": <int>,
      "nombre": "<nombre del pase>",
      "tipo": "<aperitivo|snack|entrante|mar|tierra|principal|prepostre|postre|petit four>",
      "coste_comensal": <float>,
      "intensidad": "<baja|media|alta>",
      "temperatura": "<frio|templado|caliente>",
      "observacion": "<nota breve de coste o técnica>"
    }}
  ],
  "coste_total_comensal": <float>,
  "food_cost_pct": <float>,
  "margen_bruto_comensal": <float>,
  "valoracion_margen": "<excelente|correcto|ajustado|critico>",
  "analisis_progresion": "<2-4 líneas sobre el equilibrio y la curva del menú>",
  "pases_criticos": ["<pase que compromete margen y por qué>"],
  "recomendaciones": ["<ajuste concreto sin perder nivel>"],
  "alertas_alergenos": ["<alérgeno transversal a vigilar en sala>"],
  "nota_menu_vegetariano": "<viabilidad y sugerencia para versión vegetariana>"
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_raw(response.content[0].text.strip())


def ficha_a_pdf(ficha: dict, nombre_restaurante: str = "Mi Restaurante", logo_path: str = None) -> bytes:
    """Genera PDF profesional de ficha tecnica con QR, alergenos destacados y tabla de margenes."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Table, TableStyle,
                                    Spacer, HRFlowable, Image as RLImage, KeepTogether)
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from reportlab.graphics.shapes import Drawing, Rect, String
    import io as _io
    import qrcode
    import qrcode.image.pil

    # Paleta
    VERDE = colors.HexColor("#1b5e20")
    VERDE_MED = colors.HexColor("#2e7d32")
    VERDE_CLARO = colors.HexColor("#e8f5e9")
    VERDE_BORDE = colors.HexColor("#a5d6a7")
    GRIS_OSCURO = colors.HexColor("#263238")
    GRIS_CLARO = colors.HexColor("#f5f5f5")
    NARANJA = colors.HexColor("#e65100")
    ROJO_ALERG = colors.HexColor("#b71c1c")
    ROJO_CLARO = colors.HexColor("#ffcdd2")
    DORADO = colors.HexColor("#f9a825")
    BLANCO = colors.white

    buffer = _io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            topMargin=1.2*cm, bottomMargin=1.5*cm,
                            leftMargin=1.8*cm, rightMargin=1.8*cm)

    styles = getSampleStyleSheet()
    nombre_style = ParagraphStyle("nomb", parent=styles["Title"],
                                  textColor=VERDE, fontSize=24, spaceAfter=2, leading=26)
    resto_style = ParagraphStyle("resto", parent=styles["Normal"],
                                 textColor=DORADO, fontSize=11, spaceAfter=0)
    desc_style = ParagraphStyle("desc", parent=styles["Normal"],
                                textColor=colors.HexColor("#546e7a"), fontSize=10,
                                leading=14, spaceAfter=8, fontName="Helvetica-Oblique")
    seccion_style = ParagraphStyle("sec", parent=styles["Heading2"],
                                   textColor=VERDE_MED, fontSize=11, spaceBefore=10,
                                   spaceAfter=4, borderPad=2)
    normal = ParagraphStyle("nor", parent=styles["Normal"], fontSize=9, leading=13)
    small = ParagraphStyle("sml", parent=styles["Normal"], fontSize=8, leading=11,
                            textColor=colors.HexColor("#546e7a"))
    pie_style = ParagraphStyle("pie", parent=styles["Normal"], fontSize=7,
                               textColor=colors.grey, alignment=TA_CENTER)

    story = []

    # ── CABECERA con QR ──────────────────────────────────────────────────────
    qr_data = (
        f"FICHA TECNICA: {ficha.get('nombre','')}\n"
        f"Categoria: {ficha.get('categoria','')}\n"
        f"Temp. servicio: {ficha.get('temperatura_servicio','')}\n"
        f"Alergenos: {', '.join(ficha.get('alergenos', []))}\n"
        f"Coste/racion: {ficha.get('coste_total_1_racion', 0):.2f}EUR\n"
        f"Generado por ChefMenu AI"
    )
    qr_img = qrcode.make(qr_data)
    qr_buffer = _io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    qr_rl = RLImage(qr_buffer, width=2.5*cm, height=2.5*cm)

    header_left = [
        [Paragraph(nombre_restaurante, resto_style)],
        [Paragraph(ficha.get("nombre", ""), nombre_style)],
        [Paragraph(
            f"<b>{ficha.get('categoria','').upper()}</b> &nbsp;|&nbsp; "
            f"Tiempo: <b>{ficha.get('tiempo_total_prep','?')} min</b> &nbsp;|&nbsp; "
            f"Temp.: <b>{ficha.get('temperatura_servicio','?')}</b>",
            normal
        )],
    ]
    header_table_data = [[
        Table(header_left, colWidths=[13*cm]),
        qr_rl,
    ]]
    ht = Table(header_table_data, colWidths=[13.5*cm, 3*cm])
    ht.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    story.append(ht)
    story.append(HRFlowable(width="100%", thickness=2.5, color=VERDE_MED))
    story.append(Spacer(1, 0.2*cm))

    if ficha.get("descripcion_comercial"):
        story.append(Paragraph(f'"{ficha["descripcion_comercial"]}"', desc_style))

    # ── INGREDIENTES ─────────────────────────────────────────────────────────
    story.append(Paragraph("INGREDIENTES", seccion_style))
    tabla_data = [["Ingrediente", "1 ración", "10 raciones", "Precio unit.", "Coste/ración"]]
    for ing in ficha.get("ingredientes", []):
        tabla_data.append([
            Paragraph(ing.get("nombre", ""), normal),
            ing.get("cantidad_1", ""),
            ing.get("cantidad_10", ""),
            ing.get("precio_unitario", ""),
            f"{ing.get('coste_1', 0):.2f}€",
        ])
    coste = ficha.get("coste_total_1_racion", 0)
    tabla_data.append([
        Paragraph("<b>COSTE TOTAL MATERIA PRIMA</b>", normal),
        "", "", "",
        Paragraph(f"<b>{coste:.2f}€</b>", normal),
    ])

    t = Table(tabla_data, colWidths=[5.8*cm, 2.3*cm, 2.8*cm, 2.3*cm, 2.3*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE_MED),
        ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [BLANCO, GRIS_CLARO]),
        ("BACKGROUND", (0, -1), (-1, -1), VERDE_CLARO),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, VERDE_BORDE),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (0, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.3*cm))

    # ── PRECIOS CON SEMAFORO DE MARGENES ────────────────────────────────────
    story.append(Paragraph("ANÁLISIS DE MÁRGENES Y PRECIO DE VENTA", seccion_style))

    pvp_28 = round(coste / 0.28, 2)
    pvp_30 = round(coste / 0.30, 2)
    pvp_32 = round(coste / 0.32, 2)
    pvp_35 = round(coste / 0.35, 2)

    margen_data = [
        ["Food Cost %", "PVP sugerido", "Margen bruto", "Recomendación"],
        ["28%", f"{pvp_28:.2f}€", f"{pvp_28 - coste:.2f}€", "Excelente — margen alto"],
        ["30%", f"{pvp_30:.2f}€", f"{pvp_30 - coste:.2f}€", "Ideal — estándar sector"],
        ["32%", f"{pvp_32:.2f}€", f"{pvp_32 - coste:.2f}€", "Aceptable — margen ajustado"],
        ["35%", f"{pvp_35:.2f}€", f"{pvp_35 - coste:.2f}€", "Limite — revisar costes"],
    ]
    colores_fila = [
        colors.HexColor("#1b5e20"),  # header
        colors.HexColor("#e8f5e9"),  # 28% verde
        colors.HexColor("#f1f8e9"),  # 30% verde claro
        colors.HexColor("#fff8e1"),  # 32% amarillo
        colors.HexColor("#fbe9e7"),  # 35% naranja claro
    ]
    tm = Table(margen_data, colWidths=[2.5*cm, 3.5*cm, 3.5*cm, 7*cm])
    tm_style = [
        ("BACKGROUND", (0, 0), (-1, 0), VERDE_MED),
        ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.4, VERDE_BORDE),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
        # Fondo recomendado (30%)
        ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#c8e6c9")),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
    ]
    for i, color in enumerate(colores_fila[1:], 1):
        if i != 2:
            tm_style.append(("BACKGROUND", (0, i), (-1, i), color))
    tm.setStyle(TableStyle(tm_style))
    story.append(tm)
    story.append(Paragraph(
        "★ <b>PVP recomendado (30% food cost): " + f"{pvp_30:.2f}€</b> — margen bruto: {pvp_30 - coste:.2f}€",
        ParagraphStyle("rec", parent=styles["Normal"], fontSize=10, textColor=VERDE,
                       fontName="Helvetica-Bold", spaceBefore=4)
    ))
    story.append(Spacer(1, 0.3*cm))

    # ── ELABORACION ──────────────────────────────────────────────────────────
    story.append(Paragraph("ELABORACIÓN", seccion_style))
    for i, paso in enumerate(ficha.get("elaboracion", []), 1):
        story.append(Paragraph(f"<b>{i}.</b> {paso}", normal))
    story.append(Spacer(1, 0.3*cm))

    # ── PRESENTACION + CONSERVACION ──────────────────────────────────────────
    datos_extra = [
        [Paragraph("<b>PRESENTACIÓN</b>", normal), Paragraph("<b>CONSERVACIÓN</b>", normal)],
        [Paragraph(ficha.get("presentacion", "-"), normal),
         Paragraph(ficha.get("conservacion", "-"), normal)],
    ]
    t2 = Table(datos_extra, colWidths=[8.5*cm, 8.5*cm])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GRIS_CLARO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t2)
    story.append(Spacer(1, 0.3*cm))

    # ── ALERGENOS DESTACADOS ─────────────────────────────────────────────────
    story.append(Paragraph("ALÉRGENOS Y PERFIL DIETÉTICO", seccion_style))

    ALERG_ICONOS = {
        "gluten": "🌾 Gluten", "lactosa": "🥛 Lacteos", "huevo": "🥚 Huevo",
        "pescado": "🐟 Pescado", "marisco": "🦐 Marisco", "frutos_secos": "🥜 Frutos secos",
        "soja": "🫘 Soja", "apio": "🌿 Apio",
    }
    DIETA_ICONOS = {
        "vegano": "🌱 Vegano", "vegetariano": "🥗 Vegetariano",
        "sin_gluten": "✅ Sin gluten", "sin_lactosa": "✅ Sin lactosa",
    }

    alergenos = ficha.get("alergenos", [])
    dietas = ficha.get("dietas", [])

    alerg_presentes = [ALERG_ICONOS.get(a, a) for a in alergenos if a and a != "ninguno"]
    dietas_presentes = [DIETA_ICONOS.get(d, d) for d in dietas]

    alerg_row = []
    for nombre_a in alerg_presentes:
        alerg_row.append(Paragraph(nombre_a, ParagraphStyle(
            "al", parent=styles["Normal"], fontSize=8, textColor=ROJO_ALERG,
            fontName="Helvetica-Bold", alignment=TA_CENTER)))

    dieta_row = []
    for nombre_d in dietas_presentes:
        dieta_row.append(Paragraph(nombre_d, ParagraphStyle(
            "di", parent=styles["Normal"], fontSize=8, textColor=VERDE,
            fontName="Helvetica-Bold", alignment=TA_CENTER)))

    alerg_label = "SIN ALÉRGENOS DECLARADOS" if not alerg_presentes else f"Contiene: {', '.join(alerg_presentes)}"
    dieta_label = "Sin etiquetas dietéticas" if not dietas_presentes else f"Apto para: {', '.join(dietas_presentes)}"

    alerg_table_data = [
        [Paragraph(f"<b>⚠ ALÉRGENOS:</b> {alerg_label}", ParagraphStyle(
            "alh", parent=styles["Normal"], fontSize=9,
            textColor=ROJO_ALERG if alerg_presentes else VERDE))],
        [Paragraph(f"<b>✓ DIETAS:</b> {dieta_label}", ParagraphStyle(
            "dih", parent=styles["Normal"], fontSize=9, textColor=VERDE))],
    ]
    ta = Table(alerg_table_data, colWidths=[16.5*cm])
    ta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ROJO_CLARO if alerg_presentes else VERDE_CLARO),
        ("BACKGROUND", (0, 1), (-1, 1), VERDE_CLARO),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(ta)

    # ── CONSEJO DEL CHEF ─────────────────────────────────────────────────────
    if ficha.get("consejo_chef"):
        story.append(Spacer(1, 0.3*cm))
        consejo_data = [[
            Paragraph(f"<b>Consejo del chef</b><br/><i>{ficha['consejo_chef']}</i>", normal)
        ]]
        tc = Table(consejo_data, colWidths=[16.5*cm])
        tc.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff8e1")),
            ("LEFTBORDERPADDING", (0, 0), (-1, -1), 10),
            ("BOX", (0, 0), (-1, -1), 1.5, DORADO),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(tc)

    # ── PIE ──────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph(
        f"Ficha técnica generada por <b>ChefMenu AI</b> &nbsp;|&nbsp; {nombre_restaurante} &nbsp;|&nbsp; "
        "Escanea el QR para ver info completa del plato",
        pie_style
    ))

    doc.build(story)
    return buffer.getvalue()

