"""
Genera un KIT DEMO completo de una clínica dental ficticia para enseñar a clientes.
Crea: web de ejemplo + system prompt de chatbot + config de agente de voz.

Material de venta tangible para la primera reunión: "esto es lo que tendrías".
"""
import os
from agents.specialists.web_sector_templates import SECTORES, construir_brief
from agents.specialists.web_developer import WebDeveloperAgent
from agents.specialists.chatbot_specialist import ChatbotSpecialist
from agents.specialists.voice_agent_specialist import VoiceAgentSpecialist

# ── Datos de la clínica ficticia ────────────────────────────────────────────────
NOMBRE = "Clínica Dental Sonrisa Plena"
CIUDAD = "Barcelona, Eixample"
SECTOR = "🦷 Clínica Dental"

INFO_NEGOCIO = """Clínica Dental Sonrisa Plena — Barcelona (Eixample)
Equipo: Dra. Marta Ruiz (directora, ortodoncia), Dr. Javier Soler (implantología), 2 higienistas.
Horario: Lunes a Viernes 9:00-20:00, Sábados 9:00-14:00.
Teléfono: 93 123 45 67.

Servicios y precios:
- Primera visita y revisión: GRATIS
- Limpieza bucal (higiene): 55€
- Empaste: desde 45€
- Blanqueamiento LED: 290€
- Ortodoncia invisible (Invisalign): desde 2.900€ (financiable hasta 24 meses sin intereses)
- Implante dental: desde 950€
- Endodoncia: desde 140€

Política: financiación sin intereses disponible. Primera visita siempre gratuita y sin compromiso.
Urgencias dentales atendidas el mismo día.
Diferencial: trato cercano, tecnología 3D, más de 15 años de experiencia, 4.7★ en Google con 230 reseñas."""

OUT_DIR = "outputs/demo_clinica_dental"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Generando KIT DEMO — {NOMBRE}\n")

    # ── 1. WEB ──────────────────────────────────────────────────────────────────
    print("[1/3] Generando web de ejemplo... (60-90s)")
    sector = SECTORES[SECTOR]
    brief = construir_brief(
        sector_key=SECTOR,
        nombre_negocio=NOMBRE,
        ciudad=CIUDAD,
        estilo="Clásico y profesional",
        secciones_elegidas=sector["secciones"],
        funcionalidades_elegidas=sector["funcionalidades"],
        detalles_extra=INFO_NEGOCIO,
    )
    web = WebDeveloperAgent().run(brief, max_tokens=32000)
    if web.strip().startswith("```"):
        web = "\n".join(l for l in web.splitlines() if not l.strip().startswith("```"))
    with open(f"{OUT_DIR}/web_clinica_dental.html", "w", encoding="utf-8") as f:
        f.write(web)
    print(f"   OK -> {OUT_DIR}/web_clinica_dental.html ({len(web)//1024} KB)\n")

    # ── 2. CHATBOT ──────────────────────────────────────────────────────────────
    print("[2/3] Generando system prompt del chatbot...")
    chatbot_brief = f"""Crea el chatbot para esta clínica dental:

{INFO_NEGOCIO}

El chatbot va en la web y WhatsApp. Debe: responder dudas sobre tratamientos y precios,
agendar primera visita gratuita, informar de financiación, y derivar urgencias al teléfono."""
    chatbot = ChatbotSpecialist().run(chatbot_brief)
    with open(f"{OUT_DIR}/chatbot_clinica_dental.md", "w", encoding="utf-8") as f:
        f.write(chatbot)
    print(f"   OK -> {OUT_DIR}/chatbot_clinica_dental.md ({len(chatbot)//1024} KB)\n")

    # ── 3. AGENTE DE VOZ ────────────────────────────────────────────────────────
    print("[3/3] Generando agente de voz...")
    voz_brief = f"""Crea el agente de voz telefónico para esta clínica dental:

{INFO_NEGOCIO}

El agente atiende las llamadas fuera de horario y cuando recepción está ocupada.
Objetivo: agendar primera visita gratuita, informar de tratamientos y precios,
y tomar nota de urgencias para devolver la llamada."""
    voz = VoiceAgentSpecialist().run(voz_brief)
    with open(f"{OUT_DIR}/agente_voz_clinica_dental.md", "w", encoding="utf-8") as f:
        f.write(voz)
    print(f"   OK -> {OUT_DIR}/agente_voz_clinica_dental.md ({len(voz)//1024} KB)\n")

    print("=" * 50)
    print(f"KIT DEMO COMPLETO en: {OUT_DIR}/")
    print("  - web_clinica_dental.html      (abrir en navegador)")
    print("  - chatbot_clinica_dental.md")
    print("  - agente_voz_clinica_dental.md")


if __name__ == "__main__":
    main()
