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
