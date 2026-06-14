"""
Análisis de sistemas autónomos / IA — el sello distintivo de MerakIA.

Determina en profundidad si el negocio YA tiene algún sistema autónomo
(chatbot con IA, agente de WhatsApp automatizado, reservas 24/7) o si, por el
contrario, todo depende de una persona en horario de oficina. Si no lo tiene,
es la oportunidad estrella: vender automatización + agentes IA.

Distingue tres cosas que NO son lo mismo:
  - Enlace de WhatsApp (wa.me)  → canal HUMANO, no automatiza nada
  - Chat/widget humano          → atiende una persona, no 24/7
  - Chatbot IA / WhatsApp API    → autónomo de verdad (lo que ofrece MerakIA)
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .models import ChecklistWeb

# Herramientas de la categoría "Automatización / IA" que implican IA real.
_IA_REAL = {
    "ManyChat", "Landbot", "Voiceflow", "Botpress", "Chatfuel", "Dialogflow",
    "Chatbase", "Botsonic", "Intercom (Fin AI)", "Ada", "Cliengo", "Callbell",
    "Wati (WhatsApp API)", "360dialog (WhatsApp API)", "Respond.io", "Gupshup",
    "Twilio", "Vapi (voz IA)", "Tidio (con IA)", "Chatbot/Asistente IA",
}
# Herramientas de WhatsApp con automatización/API (vs simple enlace wa.me).
_WA_AUTO = {
    "ManyChat", "Wati (WhatsApp API)", "360dialog (WhatsApp API)", "Respond.io",
    "Gupshup", "Twilio", "Callbell", "Cliengo",
}


@dataclass
class PerfilAutomatizacion:
    es_autonomo: bool                 # ¿tiene algún sistema autónomo real?
    nivel: str                        # "ninguno" / "básico" / "avanzado"
    tiene_chatbot_ia: bool
    tiene_whatsapp_humano: bool       # solo enlace wa.me (canal humano)
    tiene_whatsapp_automatizado: bool
    tiene_reservas_24_7: bool
    sistemas_detectados: List[str]    # nombres concretos hallados
    oportunidad: str                  # frase de venta lista para usar

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def analizar_automatizacion(
    tech_stack: Optional[Dict[str, List[str]]],
    checklist: Optional[ChecklistWeb],
    tiene_web: bool = True,
) -> PerfilAutomatizacion:
    """Construye el perfil de automatización a partir del stack y el checklist."""
    tech = tech_stack or {}
    cl = checklist or ChecklistWeb()

    ia_tools = tech.get("Automatización / IA", [])
    chat_tools = tech.get("Chat / Atención", [])

    tiene_chatbot_ia = len(ia_tools) > 0
    tiene_whatsapp_automatizado = any(t in _WA_AUTO for t in ia_tools)
    # WhatsApp "humano": aparece como canal de chat pero sin herramienta de automatización
    tiene_whatsapp_humano = ("WhatsApp" in chat_tools) and not tiene_whatsapp_automatizado
    tiene_reservas_24_7 = bool(cl.tiene_reserva_online)

    es_autonomo = tiene_chatbot_ia or tiene_whatsapp_automatizado

    if tiene_chatbot_ia and (tiene_whatsapp_automatizado or tiene_reservas_24_7):
        nivel = "avanzado"
    elif es_autonomo or tiene_reservas_24_7:
        nivel = "básico"
    else:
        nivel = "ninguno"

    sistemas = list(dict.fromkeys(ia_tools))  # sin duplicados, preserva orden
    if tiene_reservas_24_7:
        reservas = tech.get("Reservas / Citas", [])
        sistemas += [f"Reservas: {r}" for r in reservas] or ["Reservas online"]

    # Frase de venta
    if not tiene_web:
        oportunidad = (
            "Sin web ni ningún sistema autónomo: el negocio depende 100% del teléfono. "
            "Oportunidad estrella — montar un agente IA de WhatsApp 24/7 como primera "
            "presencia digital."
        )
    elif nivel == "ninguno":
        canal = "Solo tiene un enlace de WhatsApp que atiende una persona en horario." if tiene_whatsapp_humano else "No tiene chatbot, agente IA ni reservas automáticas."
        oportunidad = (
            f"NO tiene ningún sistema autónomo. {canal} "
            "Cada consulta fuera de horario se pierde. Servicio estrella a proponer: "
            "chatbot IA en la web + agente de WhatsApp 24/7 que cualifica y agenda solo."
        )
    elif nivel == "básico":
        oportunidad = (
            "Tiene automatización básica pero incompleta. Hay margen para un agente IA "
            "que unifique web + WhatsApp, cualifique leads y agende sin intervención humana."
        )
    else:
        oportunidad = (
            "Ya tiene automatización avanzada. Ángulo: optimizar, integrar canales y "
            "añadir seguimiento/fidelización con IA."
        )

    return PerfilAutomatizacion(
        es_autonomo=es_autonomo,
        nivel=nivel,
        tiene_chatbot_ia=tiene_chatbot_ia,
        tiene_whatsapp_humano=tiene_whatsapp_humano,
        tiene_whatsapp_automatizado=tiene_whatsapp_automatizado,
        tiene_reservas_24_7=tiene_reservas_24_7,
        sistemas_detectados=sistemas,
        oportunidad=oportunidad,
    )
