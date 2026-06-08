from agents.specialists import ChatbotSpecialist, WebDeveloperAgent, ContentMarketingAgent


def build_chatbot_package(business_name: str, sector: str, description: str) -> dict:
    """Full chatbot package: design + web widget + launch copy."""
    prompt_base = f"Negocio: {business_name} | Sector: {sector} | Descripción: {description}"

    chatbot = ChatbotSpecialist()
    design = chatbot.run(
        f"Diseña un chatbot completo para este negocio. {prompt_base}"
    )

    webdev = WebDeveloperAgent()
    widget = webdev.run(
        f"Crea un widget de chatbot en HTML/CSS/JS para incrustar en una web. "
        f"Debe ser moderno y adaptado a: {prompt_base}"
    )

    marketing = ContentMarketingAgent()
    copy = marketing.run(
        f"Escribe el copy de lanzamiento del chatbot para redes sociales y email. "
        f"{prompt_base}"
    )

    return {"chatbot_design": design, "web_widget": widget, "launch_copy": copy}


def build_landing_page_package(business_name: str, sector: str, goal: str) -> dict:
    """Full landing page: code + SEO copy + social media launch."""
    prompt_base = f"Negocio: {business_name} | Sector: {sector} | Objetivo: {goal}"

    webdev = WebDeveloperAgent()
    landing = webdev.run(
        f"Crea una landing page completa y moderna optimizada para conversión. {prompt_base}"
    )

    marketing = ContentMarketingAgent()
    copy = marketing.run(
        f"Escribe el copy SEO para la landing page y posts de lanzamiento. {prompt_base}"
    )

    return {"landing_page": landing, "seo_copy": copy}
