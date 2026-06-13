"""
Buscador de negocios locales usando Google Places API (New).
Requiere GOOGLE_PLACES_API_KEY con $200/mes de crédito gratuito.
Coste aproximado: ~0.03€ por búsqueda de 20 resultados.
"""
import requests
from typing import List, Tuple

from .models import Business

PLACES_BASE = "https://places.googleapis.com/v1"

SEARCH_FIELDS = ",".join([
    "places.id", "places.displayName", "places.formattedAddress",
    "places.rating", "places.userRatingCount", "places.location",
    "nextPageToken",
])

DETAILS_FIELDS = ",".join([
    "nationalPhoneNumber", "internationalPhoneNumber", "websiteUri",
    "rating", "userRatingCount", "reviews",
])


class GooglePlacesScraper:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def buscar_negocios(self, tipo: str, ciudad: str, limite: int = 20) -> List[Business]:
        """Busca negocios por tipo y ciudad. Devuelve lista básica sin detalles."""
        url = f"{PLACES_BASE}/places:searchText"
        headers = {
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": SEARCH_FIELDS,
            "Content-Type": "application/json",
        }
        body = {
            "textQuery": f"{tipo} en {ciudad}",
            "languageCode": "es",
            "pageSize": min(limite, 20),
        }
        negocios: List[Business] = []

        while len(negocios) < limite:
            resp = requests.post(url, headers=headers, json=body, timeout=15)
            data = resp.json()

            if resp.status_code != 200:
                err = data.get("error", {})
                raise RuntimeError(
                    f"Google Places API error: {err.get('status', resp.status_code)} — "
                    f"{err.get('message', '')}"
                )

            for p in data.get("places", []):
                loc = p.get("location", {})
                negocio = Business(
                    place_id=p["id"],
                    nombre=p.get("displayName", {}).get("text", ""),
                    tipo=tipo,
                    ciudad=ciudad,
                    direccion=p.get("formattedAddress", ""),
                    rating=p.get("rating"),
                    total_resenas=p.get("userRatingCount", 0),
                    lat=loc.get("latitude"),
                    lng=loc.get("longitude"),
                )
                negocios.append(negocio)
                if len(negocios) >= limite:
                    break

            next_token = data.get("nextPageToken")
            if not next_token or len(negocios) >= limite:
                break
            body["pageToken"] = next_token

        return negocios[:limite]

    def enriquecer_negocio(self, negocio: Business) -> Tuple[Business, List[dict]]:
        """
        Añade teléfono, web y reseñas.
        Devuelve (negocio_enriquecido, lista_resenas_raw) en formato
        compatible con review_miner (author_name, rating, text, ...).
        """
        url = f"{PLACES_BASE}/places/{negocio.place_id}"
        headers = {
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": DETAILS_FIELDS,
        }
        resp = requests.get(url, headers=headers, params={"languageCode": "es"}, timeout=15)
        if resp.status_code != 200:
            return negocio, []

        result = resp.json()
        negocio.telefono = (
            result.get("nationalPhoneNumber") or result.get("internationalPhoneNumber")
        )
        negocio.web = result.get("websiteUri")
        negocio.tiene_web = bool(negocio.web)

        # Normalizar reseñas de la API nueva al formato clásico que consume review_miner
        resenas_raw = []
        for r in result.get("reviews", []):
            texto = r.get("text", {})
            resenas_raw.append({
                "author_name": r.get("authorAttribution", {}).get("displayName", "Anónimo"),
                "rating": r.get("rating", 3),
                "text": texto.get("text", "") if isinstance(texto, dict) else str(texto or ""),
                "relative_time_description": r.get("relativePublishTimeDescription"),
            })

        return negocio, resenas_raw

    def _detectar_propietario(self, resenas_raw: List[dict]) -> str | None:
        """La API nueva no expone respuestas del propietario en reseñas."""
        return None
