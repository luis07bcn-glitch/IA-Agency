"""
Detección de stack tecnológico (estilo BuiltWith) sin APIs de pago.

Analiza el HTML y las cabeceras que YA descarga el web_analyzer para detectar
qué CMS, analítica, chat, reservas y marketing usa el negocio. Vale para dos
cosas en la venta:
  1. Saber qué tiene → qué upsellearle (ej. "usan WordPress y Mailchimp pero
     no tienen píxel ni reservas online").
  2. Hablar su idioma en la reunión (genera credibilidad técnica instantánea).
"""
import re
from typing import Dict, List, Optional

# categoria -> {nombre_legible: [patrones en html/headers (lower)]}
_FIRMAS: Dict[str, Dict[str, List[str]]] = {
    "CMS / Constructor": {
        "WordPress": ["wp-content", "wp-includes", "wp-json", "/wp-"],
        "Wix": ["wix.com", "wixstatic.com", "_wix", "x-wix"],
        "Squarespace": ["squarespace.com", "static1.squarespace", "squarespace-cdn"],
        "Shopify": ["cdn.shopify.com", "myshopify.com", "shopify"],
        "Webflow": ["webflow.io", "assets.website-files.com", "wf-"],
        "Joomla": ["/components/com_", "joomla"],
        "Drupal": ["sites/default/files", "drupal"],
        "GoDaddy Builder": ["godaddy", "websitebuilder"],
        "Jimdo": ["jimdo"],
        "Weebly": ["weebly"],
        "Framer": ["framerusercontent", "framer.com"],
    },
    "E-commerce": {
        "WooCommerce": ["woocommerce", "wp-content/plugins/woocommerce"],
        "Shopify": ["cdn.shopify.com", "myshopify.com"],
        "PrestaShop": ["prestashop"],
        "Magento": ["magento", "mage/"],
    },
    "Analítica / Tracking": {
        "Google Analytics 4": ["gtag/js?id=g-", "gtag('config', 'g-", "gtag(\"config\", \"g-"],
        "Universal Analytics": ["google-analytics.com/analytics.js", "ua-"],
        "Google Tag Manager": ["googletagmanager.com/gtm.js", "gtm-"],
        "Meta Pixel": ["fbq(", "connect.facebook.net", "facebook.com/tr"],
        "TikTok Pixel": ["analytics.tiktok.com", "ttq."],
        "Hotjar": ["hotjar.com", "hjid"],
        "Microsoft Clarity": ["clarity.ms"],
        "LinkedIn Insight": ["snap.licdn.com"],
    },
    "Chat / Atención": {
        "WhatsApp": ["wa.me", "api.whatsapp", "wa.link", "whatsapp"],
        "Tawk.to": ["tawk.to"],
        "Intercom": ["intercom"],
        "Crisp": ["crisp.chat"],
        "Tidio": ["tidio"],
        "Zendesk": ["zendesk", "zopim"],
        "Drift": ["drift.com"],
        "Messenger": ["m.me/", "messenger.com"],
    },
    "Reservas / Citas": {
        "Calendly": ["calendly.com"],
        "Doctoralia": ["doctoralia"],
        "Doctolib": ["doctolib"],
        "Booksy": ["booksy"],
        "Treatwell": ["treatwell"],
        "Planity": ["planity"],
        "Acuity": ["acuityscheduling"],
        "TheFork": ["thefork"],
        "CoverManager": ["covermanager"],
        "Mindbody": ["mindbody"],
    },
    "Email / Marketing / CRM": {
        "HubSpot": ["hubspot", "hs-scripts", "hsforms"],
        "Mailchimp": ["mailchimp", "list-manage.com", "mc.us"],
        "ActiveCampaign": ["activehosted.com", "activecampaign"],
        "Klaviyo": ["klaviyo"],
        "Brevo / Sendinblue": ["sendinblue", "brevo"],
    },
    # Sistemas AUTÓNOMOS / IA — el sello de MerakIA. Distinguir esto de un simple
    # enlace de WhatsApp (que es un canal humano, no automatización).
    "Automatización / IA": {
        "ManyChat": ["manychat"],
        "Landbot": ["landbot"],
        "Voiceflow": ["voiceflow"],
        "Botpress": ["botpress"],
        "Chatfuel": ["chatfuel"],
        "Dialogflow": ["dialogflow"],
        "Chatbase": ["chatbase"],
        "Botsonic": ["botsonic"],
        "Intercom (Fin AI)": ["intercom"],
        "Ada": ["ada.cx", "ada.support"],
        "Cliengo": ["cliengo"],
        "Callbell": ["callbell"],
        "Wati (WhatsApp API)": ["wati.io", "clare.ai"],
        "360dialog (WhatsApp API)": ["360dialog"],
        "Respond.io": ["respond.io"],
        "Gupshup": ["gupshup"],
        "Twilio": ["twilio"],
        "Vapi (voz IA)": ["vapi.ai"],
        "Tidio (con IA)": ["tidio"],
        "Chatbot/Asistente IA": ["chatbot", "chat-bot", "openai", "gpt-", "assistant-widget"],
    },
}

# Detecciones por cabecera HTTP
_FIRMAS_HEADERS = {
    "CDN / Hosting": {
        "Cloudflare": ["cloudflare"],
        "Vercel": ["vercel"],
        "Netlify": ["netlify"],
        "Amazon AWS": ["amazons3", "cloudfront"],
    },
}


def detectar_tech_stack(
    html: str,
    headers: Optional[dict] = None,
    final_url: str = "",
) -> Dict[str, List[str]]:
    """Devuelve {categoria: [herramientas detectadas]}. Solo categorías con hits."""
    blob = (html or "").lower() + " " + (final_url or "").lower()
    resultado: Dict[str, List[str]] = {}

    for categoria, firmas in _FIRMAS.items():
        encontrados = []
        for nombre, patrones in firmas.items():
            if any(p in blob for p in patrones):
                encontrados.append(nombre)
        if encontrados:
            resultado[categoria] = encontrados

    # Cabeceras (server, via, x-powered-by, cf-ray, etc.)
    if headers:
        blob_h = " ".join(f"{k}:{v}" for k, v in headers.items()).lower()
        for categoria, firmas in _FIRMAS_HEADERS.items():
            encontrados = []
            for nombre, patrones in firmas.items():
                if any(p in blob_h for p in patrones):
                    encontrados.append(nombre)
            # cf-ray es señal fuerte de Cloudflare
            if "cf-ray" in blob_h and "Cloudflare" not in encontrados:
                encontrados.append("Cloudflare")
            if encontrados:
                resultado[categoria] = encontrados

        # X-Powered-By suele revelar el backend
        xpb = headers.get("X-Powered-By") or headers.get("x-powered-by")
        if xpb:
            resultado.setdefault("Backend", []).append(xpb)

    return resultado


def resumen_oportunidad_tech(tech: Dict[str, List[str]]) -> List[str]:
    """
    A partir del stack detectado, sugiere ángulos de venta concretos.
    Devuelve frases listas para usar en la reunión / propuesta.
    """
    sugerencias = []
    tiene_analitica = "Analítica / Tracking" in tech
    tiene_pixel = tiene_analitica and any(
        "Pixel" in t for t in tech.get("Analítica / Tracking", [])
    )
    tiene_chat = "Chat / Atención" in tech
    tiene_reservas = "Reservas / Citas" in tech
    tiene_crm = "Email / Marketing / CRM" in tech

    if not tiene_analitica:
        sugerencias.append("No miden nada (sin analítica): imposible optimizar lo que no se mide.")
    if not tiene_pixel:
        sugerencias.append("Sin píxel de remarketing: no pueden reimpactar a quien ya les visitó.")
    if not tiene_reservas:
        sugerencias.append("Sin sistema de reservas/citas: dependen del teléfono.")
    if not tiene_chat:
        sugerencias.append("Sin chat: no captan al visitante en el momento de máximo interés.")
    if not tiene_crm:
        sugerencias.append("Sin herramienta de email/CRM: no fidelizan ni reactivan clientes.")
    return sugerencias
