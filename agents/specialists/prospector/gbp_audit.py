"""
Auditoría de la ficha de Google Business Profile (GBP).

Para un negocio LOCAL, la ficha de Google pesa más que la web para captar
clientes: es lo primero que ve quien busca en Google Maps. Esta auditoría
mide la completitud de la ficha con datos que ya descargamos de Places API
(New) — fotos, horario, teléfono, web vinculada, descripción, categoría,
accesibilidad — y los convierte en dolores concretos y vendibles.

100% determinista (sin IA, sin coste de tokens). La mayoría de los campos
ya vienen en la respuesta de Places que pedimos para las reseñas, así que es
precisión prácticamente gratis.
"""
from dataclasses import dataclass, field
from typing import List, Optional


def _nivel(score: float) -> str:
    if score >= 75:
        return "fuerte"
    if score >= 50:
        return "aceptable"
    if score >= 25:
        return "débil"
    return "crítico"


@dataclass
class PerfilGBP:
    completitud: int                       # 0-100
    nivel: str                             # crítico / débil / aceptable / fuerte
    tiene_fotos: bool
    num_fotos: int                         # nº de fotos detectadas (la API limita ~10)
    muchas_fotos: bool                     # alcanza el tope → probablemente bien surtida
    tiene_horario: bool
    tiene_telefono: bool
    tiene_web_vinculada: bool
    tiene_descripcion: bool
    categoria: Optional[str]
    operativo: bool                        # businessStatus OPERATIONAL
    tiene_accesibilidad: bool
    maps_uri: Optional[str]
    senales_ok: List[str] = field(default_factory=list)
    senales_falta: List[str] = field(default_factory=list)
    oportunidad: str = ""

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def analizar_gbp(gbp_raw: Optional[dict], negocio=None) -> PerfilGBP:
    """
    Construye el perfil de la ficha de Google a partir de los campos crudos
    de Places API (New). `gbp_raw` es el dict de la respuesta de detalles;
    si es None, devuelve un perfil vacío marcado como crítico.
    """
    g = gbp_raw or {}

    fotos = g.get("photos") or []
    num_fotos = len(fotos)
    tiene_fotos = num_fotos > 0
    muchas_fotos = num_fotos >= 10  # la API satura ~10 → seguramente hay más

    horario = g.get("regularOpeningHours") or {}
    tiene_horario = bool(horario.get("weekdayDescriptions"))

    tiene_telefono = bool(
        g.get("nationalPhoneNumber") or g.get("internationalPhoneNumber")
        or (negocio and getattr(negocio, "telefono", None))
    )
    tiene_web_vinculada = bool(
        g.get("websiteUri") or (negocio and getattr(negocio, "web", None))
    )

    desc = g.get("editorialSummary") or {}
    tiene_descripcion = bool(desc.get("text"))

    categoria = (g.get("primaryTypeDisplayName") or {}).get("text") if isinstance(
        g.get("primaryTypeDisplayName"), dict
    ) else g.get("primaryTypeDisplayName")

    estado = g.get("businessStatus", "OPERATIONAL")
    operativo = estado == "OPERATIONAL"

    acc = g.get("accessibilityOptions") or {}
    tiene_accesibilidad = bool(acc)

    # ── Señales ponderadas ────────────────────────────────────────────────
    senales = [
        # (peso, presente, etiqueta_ok, etiqueta_falta)
        (2.5, tiene_fotos,
         f"{num_fotos}+ fotos en la ficha" if muchas_fotos else f"{num_fotos} foto(s) en la ficha",
         "Sin fotos en Google — las fichas con fotos reciben 42% más solicitudes de cómo llegar"),
        (1.2, muchas_fotos,
         "Galería de fotos bien surtida",
         "Pocas fotos — añadir fotos de local, equipo y servicios sube las visitas a la ficha"),
        (2.0, tiene_horario,
         "Horario de apertura publicado",
         "Sin horario en Google — los clientes no saben cuándo estás abierto y muchos no llaman"),
        (1.5, tiene_telefono,
         "Teléfono visible en la ficha",
         "Sin teléfono en la ficha — fricción para contactar"),
        (1.5, tiene_web_vinculada,
         "Web vinculada desde Google",
         "Sin web vinculada en Google — se pierde tráfico hacia el sitio"),
        (1.5, tiene_descripcion,
         "Descripción del negocio en Google",
         "Sin descripción en Google — la ficha no explica qué ofreces ni te diferencia"),
        (1.0, bool(categoria),
         f"Categoría definida ({categoria})" if categoria else "Categoría definida",
         "Categoría principal sin optimizar — clave para aparecer en las búsquedas correctas"),
        (1.0, operativo,
         "Ficha activa y operativa",
         "Ficha marcada como cerrada o temporalmente cerrada en Google"),
        (0.5, tiene_accesibilidad,
         "Atributos de accesibilidad",
         "Sin atributos rellenados (accesibilidad, servicios) — ficha incompleta"),
    ]

    total = sum(p for p, *_ in senales) or 1
    logrado = sum(p for p, presente, *_ in senales if presente)
    completitud = round(logrado / total * 100)

    senales_ok = [ok for _, presente, ok, _ in senales if presente]
    senales_falta = [falta for _, presente, _, falta in senales if not presente]

    nivel = _nivel(completitud)
    if completitud < 50:
        oportunidad = (
            "Ficha de Google muy incompleta: es la palanca de captación local más "
            "rápida y barata de arreglar. Optimizarla suele subir las visitas y "
            "llamadas en semanas, sin tocar la web."
        )
    elif completitud < 75:
        oportunidad = (
            "La ficha tiene huecos que cuestan visibilidad local. Completarla y "
            "optimizar fotos, categoría y descripción mejora el posicionamiento en el mapa."
        )
    else:
        oportunidad = (
            "Ficha bien cuidada. El siguiente paso es mantenimiento activo: fotos "
            "nuevas, publicaciones y responder reseñas para seguir liderando el mapa."
        )

    return PerfilGBP(
        completitud=completitud,
        nivel=nivel,
        tiene_fotos=tiene_fotos,
        num_fotos=num_fotos,
        muchas_fotos=muchas_fotos,
        tiene_horario=tiene_horario,
        tiene_telefono=tiene_telefono,
        tiene_web_vinculada=tiene_web_vinculada,
        tiene_descripcion=tiene_descripcion,
        categoria=categoria,
        operativo=operativo,
        tiene_accesibilidad=tiene_accesibilidad,
        maps_uri=g.get("googleMapsUri"),
        senales_ok=senales_ok,
        senales_falta=senales_falta,
        oportunidad=oportunidad,
    )
