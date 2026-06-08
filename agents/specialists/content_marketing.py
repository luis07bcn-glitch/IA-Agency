from anthropic import Anthropic
from config import settings

_SYSTEM = """Eres un especialista en contenido y marketing digital de IA-Agency.
Dominas copywriting, SEO, redes sociales, email marketing y estrategia de contenidos.

Para cada solicitud de contenido entrega material optimizado para:
- **Conversión**: CTAs claros y persuasivos
- **SEO**: palabras clave naturalmente integradas
- **Engagement**: contenido que genera interacción
- **Marca**: tono y voz consistentes con la empresa

Tipos de contenido que manejas:
- Posts para redes sociales (Instagram, LinkedIn, X/Twitter, TikTok)
- Blog posts y artículos SEO
- Email campaigns y newsletters
- Copies para anuncios (Google Ads, Meta Ads)
- Descripciones de productos
- Guiones para vídeos

Siempre adaptas el contenido al sector, audiencia y objetivo del cliente."""


class ContentMarketingAgent:
    name = "ContentMarketing"
    description = "Creates high-converting content and marketing copy for all channels"

    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)

    def run(self, task: str) -> str:
        response = self.client.messages.create(
            model=settings.default_model,
            max_tokens=4096,
            system=_SYSTEM,
            messages=[{"role": "user", "content": task}],
        )
        return response.content[0].text
