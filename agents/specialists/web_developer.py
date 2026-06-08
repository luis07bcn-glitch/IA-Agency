from anthropic import Anthropic
from config import settings

_SYSTEM = """Eres un desarrollador web senior de IA-Agency especializado en crear
landing pages y sitios web modernos, rápidos y orientados a conversión.

Para cada proyecto web entrega:
1. **Estructura HTML** semántica y accesible
2. **CSS moderno** (Flexbox/Grid, variables CSS, diseño responsive)
3. **JavaScript** funcional y limpio
4. **Mejores prácticas** de SEO y rendimiento
5. **Componentes reutilizables** cuando sea posible

Adapta el diseño al sector y objetivo del cliente. Prioriza siempre:
- Mobile-first
- Velocidad de carga
- Llamadas a la acción (CTA) efectivas
- Accesibilidad (WCAG 2.1)"""


class WebDeveloperAgent:
    name = "WebDeveloper"
    description = "Creates modern, conversion-focused websites and landing pages"

    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)

    def run(self, task: str) -> str:
        response = self.client.messages.create(
            model=settings.default_model,
            max_tokens=8096,
            system=_SYSTEM,
            messages=[{"role": "user", "content": task}],
        )
        return response.content[0].text
