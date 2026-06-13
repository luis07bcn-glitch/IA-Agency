"""
Analiza websites con requests + BeautifulSoup.
No requiere Playwright — funciona con HTML estático (suficiente para el 90% de casos).
"""
import time
import re
import requests
from bs4 import BeautifulSoup
from typing import Tuple, Optional, Dict, List

from .models import ChecklistWeb
from .techstack import detectar_tech_stack

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class WebAnalyzer:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def analizar(
        self, url: str
    ) -> Tuple[ChecklistWeb, float, Optional[str], Dict[str, List[str]]]:
        """
        Analiza una URL y devuelve
        (ChecklistWeb, tiempo_carga_seg, nombre_propietario_detectado, tech_stack).
        Si la web no responde, devuelve ChecklistWeb vacío con tiempo=99.
        """
        if not url:
            return ChecklistWeb(), 99.0, None, {}

        if not url.startswith("http"):
            url = "https://" + url

        t0 = time.time()
        try:
            resp = requests.get(
                url, headers=HEADERS, timeout=self.timeout,
                allow_redirects=True
            )
            tiempo_carga = time.time() - t0
            html = resp.text
            final_url = resp.url
            resp_headers = dict(resp.headers)
        except Exception:
            return ChecklistWeb(), 99.0, None, {}

        soup = BeautifulSoup(html, "lxml")
        html_lower = html.lower()

        checklist = ChecklistWeb(
            tiene_https=final_url.startswith("https://"),
            carga_rapida=tiempo_carga < 3.0,
            es_mobile_responsive=bool(soup.find("meta", attrs={"name": "viewport"})),
            tiene_formulario=self._check_formulario(soup),
            tiene_chat_whatsapp=self._check_chat(html_lower),
            tiene_cta_reserva=self._check_cta(soup),
            tiene_reserva_online=self._check_booking(html_lower),
            tiene_testimonios=self._check_testimonios(soup, html_lower),
            tiene_video=self._check_video(soup),
            tiene_galeria=len(soup.find_all("img")) > 6,
            tiene_blog=self._check_blog(soup, final_url),
            tiene_pixel_tracking="fbq(" in html or "gtag(" in html or "_gaq.push" in html,
            tiene_captura_email=bool(soup.find("input", attrs={"type": "email"})),
            tiene_gmb="maps.google" in html_lower or "g.page" in html_lower or "goo.gl/maps" in html_lower,
            tiene_resenas_visibles=self._check_resenas(soup, html_lower),
        )

        propietario = self._detectar_propietario(soup, html)
        tech_stack = detectar_tech_stack(html, resp_headers, final_url)
        return checklist, tiempo_carga, propietario, tech_stack

    # ── Checks individuales ────────────────────────────────────────────────────

    def _check_formulario(self, soup) -> bool:
        if soup.find("form"):
            return True
        # Algunos sitios usan inputs sueltos sin <form>
        inputs = soup.find_all("input", attrs={"type": ["text", "tel", "email"]})
        return len(inputs) >= 2

    def _check_chat(self, html_lower: str) -> bool:
        patterns = [
            "whatsapp", "wa.me", "wa.link", "api.whatsapp",
            "tawk.to", "tawkto", "crisp.chat", "intercom",
            "tidio", "livechat", "chaport", "zendesk",
            "messenger.com", "m.me/", "hubspot", "drift",
        ]
        return any(p in html_lower for p in patterns)

    def _check_cta(self, soup) -> bool:
        cta_words = [
            "reserva", "reservar", "pedir cita", "pide cita", "pide tu cita",
            "solicitar cita", "agendar", "book now", "book an appointment",
            "contratar", "solicitar", "solicita", "presupuesto",
        ]
        # Buscar en botones, anchors y headings
        for tag in soup.find_all(["button", "a", "h1", "h2", "h3"]):
            text = tag.get_text().lower()
            if any(w in text for w in cta_words):
                return True
        return False

    def _check_booking(self, html_lower: str) -> bool:
        booking_patterns = [
            "calendly.com", "doctolib", "doctoralia", "treatwell",
            "booksy", "planity", "setmore", "acuityscheduling",
            "simplybook", "reservio", "mindbody", "glofox",
            "thefork", "covermanager", "restoo", "resy",
            "zocdoc", "practicefusion", "jane.app",
        ]
        return any(p in html_lower for p in booking_patterns)

    def _check_testimonios(self, soup, html_lower: str) -> bool:
        test_class_patterns = ["testimon", "review", "opinion", "valoracion", "reseña", "client"]
        for tag in soup.find_all(class_=True):
            classes = " ".join(tag.get("class", [])).lower()
            if any(p in classes for p in test_class_patterns):
                return True
        # Buscar en texto
        test_text_patterns = [
            "lo que dicen", "nuestros clientes dicen", "opiniones de",
            "testimonios", "⭐", "★★", "basado en",
        ]
        text = soup.get_text().lower()
        return any(p in text for p in test_text_patterns)

    def _check_video(self, soup) -> bool:
        if soup.find("video"):
            return True
        for iframe in soup.find_all("iframe"):
            src = iframe.get("src", "")
            if "youtube" in src or "vimeo" in src or "loom" in src:
                return True
        return False

    def _check_blog(self, soup, final_url: str) -> bool:
        url_lower = final_url.lower()
        if "/blog" in url_lower or "/noticias" in url_lower or "/articulos" in url_lower:
            return True
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            if "blog" in href or "noticias" in href or "articulos" in href:
                return True
        return False

    def _check_resenas(self, soup, html_lower: str) -> bool:
        patterns = [
            "google.com/maps", "trustpilot", "tripadvisor",
            "verified review", "reseña verificada",
        ]
        return any(p in html_lower for p in patterns)

    def _detectar_propietario(self, soup, html: str) -> Optional[str]:
        """Intenta detectar el nombre del propietario desde schema.org o meta tags."""
        # Schema.org Person
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                import json
                data = json.loads(script.string or "")
                if isinstance(data, list):
                    data = data[0]
                owner = data.get("founder") or data.get("owner")
                if owner and isinstance(owner, dict):
                    name = owner.get("name")
                    if name:
                        return name
                if owner and isinstance(owner, str):
                    return owner
            except Exception:
                pass

        # Buscar patrones "Dr./Dra./Director/Propietario: Nombre Apellido"
        patterns = [
            r"(?:Dr\.|Dra\.|Director[a]?[:\s]+|Propietario[:\s]+|Fundador[a]?[:\s]+)([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+)",
        ]
        text = soup.get_text()
        for pattern in patterns:
            m = re.search(pattern, text)
            if m:
                return m.group(1).strip()

        return None
