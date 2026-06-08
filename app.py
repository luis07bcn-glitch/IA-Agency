"""MerakIA — Panel de control web (Streamlit)."""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("PYTHONUTF8", "1")

import streamlit as st

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MerakIA · Panel de Agentes",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Gradient header */
  .merakia-header {
    background: linear-gradient(135deg, #7C3AED, #A855F7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 1.8rem;
    font-weight: 800;
    letter-spacing: -0.5px;
  }
  /* Agent result box */
  .result-box {
    background: #1E293B;
    border: 1px solid rgba(124,58,237,0.3);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-top: 0.8rem;
  }
  /* Metric cards */
  div[data-testid="metric-container"] {
    background: #1E293B;
    border: 1px solid rgba(124,58,237,0.25);
    border-radius: 10px;
    padding: 0.8rem 1rem;
  }
  /* Sidebar title */
  .sidebar-brand {
    font-size: 1.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #7C3AED, #A855F7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem;
  }
  /* Hide Streamlit branding */
  #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-brand">🤖 MerakIA</div>', unsafe_allow_html=True)
    st.caption("Agencia de Inteligencia Artificial")
    st.divider()

    page = st.radio(
        "Navegación",
        options=["🏠 Dashboard", "💬 Chat", "📋 Project Manager", "🌐 Web Developer",
                 "📣 Contenido & Marketing", "🤖 Chatbot Specialist", "⚡ Agente Autónomo"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("v1.0 · Claude Sonnet 4.6")


# ─── Helper ───────────────────────────────────────────────────────────────────
def stream_write(text: str, container=None) -> None:
    """Simula efecto de escritura progresiva."""
    target = container or st
    words = text.split(" ")
    result = ""
    placeholder = target.empty()
    for word in words:
        result += word + " "
        placeholder.markdown(result + "▌")
        time.sleep(0.008)
    placeholder.markdown(result.strip())


def download_button(content: str, filename: str) -> None:
    st.download_button(
        label=f"⬇️ Descargar {filename}",
        data=content.encode("utf-8"),
        file_name=filename,
        mime="text/plain",
    )


# ══════════════════════════════════════════════════════════════════════════════
#  PAGES
# ══════════════════════════════════════════════════════════════════════════════

# ─── Dashboard ────────────────────────────────────────────────────────────────
if page == "🏠 Dashboard":
    st.markdown('<div class="merakia-header">MerakIA · Panel de Agentes IA</div>',
                unsafe_allow_html=True)
    st.markdown("**Inteligencia Artificial que impulsa tu negocio**")
    st.divider()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Agentes activos", "6")
    col2.metric("Workflows", "2")
    col3.metric("Herramientas", "4")
    col4.metric("Modelo", "Sonnet 4.6")

    st.divider()
    st.subheader("🚀 Agentes disponibles")

    agents_info = [
        ("💬", "Chat", "Asistente conversacional con memoria de sesión"),
        ("📋", "Project Manager", "Orquesta el equipo completo para proyectos de cliente"),
        ("🌐", "Web Developer", "Genera landing pages y código web listo para producción"),
        ("📣", "Contenido & Marketing", "Copy, posts, emails y estrategia de contenidos"),
        ("🤖", "Chatbot Specialist", "Diseña chatbots personalizados para negocios"),
        ("⚡", "Autónomo", "Ejecuta tareas complejas con herramientas (calc, fecha, archivos)"),
    ]

    cols = st.columns(3)
    for i, (icon, name, desc) in enumerate(agents_info):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="result-box">
              <b>{icon} {name}</b><br>
              <small style="color:#94A3B8">{desc}</small>
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.info("👈 Selecciona un agente en el menú lateral para empezar.", icon="ℹ️")


# ─── Chat ─────────────────────────────────────────────────────────────────────
elif page == "💬 Chat":
    st.subheader("💬 Chat con IA")

    # Config
    with st.expander("⚙️ Configuración del chatbot", expanded=False):
        bot_name = st.text_input("Nombre del asistente", value="Asistente MerakIA")
        system_prompt = st.text_area(
            "System prompt",
            value="Eres un asistente de IA profesional de MerakIA. Eres útil, preciso y conciso.",
            height=80,
        )
        if st.button("🔄 Reiniciar conversación"):
            st.session_state.chat_history = []
            st.session_state.chat_agent = None
            st.rerun()

    # Init agent & history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_agent" not in st.session_state:
        st.session_state.chat_agent = None

    # Display history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])

    # Input
    if prompt := st.chat_input("Escribe tu mensaje..."):
        # Lazy-load agent
        if st.session_state.chat_agent is None:
            from agents.chatbot_agent import ChatbotAgent
            st.session_state.chat_agent = ChatbotAgent(
                name=bot_name, system_prompt=system_prompt
            )

        # Show user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

        # Get response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Pensando..."):
                reply = st.session_state.chat_agent.chat(prompt)
            st.markdown(reply)

        st.session_state.chat_history.append({"role": "assistant", "content": reply})


# ─── Project Manager ──────────────────────────────────────────────────────────
elif page == "📋 Project Manager":
    st.subheader("📋 Project Manager Agent")
    st.caption("Describe el proyecto del cliente — el PM analiza, asigna tareas y entrega el resultado.")

    request = st.text_area(
        "Solicitud del cliente",
        placeholder='Ej: "Quiero un chatbot para mi restaurante italiano en Barcelona que gestione reservas y responda preguntas sobre la carta"',
        height=120,
    )

    if st.button("🚀 Ejecutar proyecto", type="primary", disabled=not request.strip()):
        from agents.pm_agent import ProjectManagerAgent

        pm = ProjectManagerAgent()
        progress = st.progress(0, text="Analizando requisitos...")

        with st.spinner("El equipo está trabajando..."):
            progress.progress(20, text="PM analizando y planificando...")
            result = pm.run(request, verbose=False)
            progress.progress(100, text="¡Completado!")

        # Plan table
        if result["plan"] and result["plan"].get("tasks"):
            st.divider()
            st.markdown("**📊 Plan del proyecto**")
            plan = result["plan"]
            if plan.get("timeline"):
                st.caption(f"⏱️ Estimación: {plan['timeline']}")

            cols = st.columns([1, 3])
            cols[0].markdown("**Agente**")
            cols[1].markdown("**Tarea**")
            for task in plan["tasks"]:
                c1, c2 = st.columns([1, 3])
                c1.markdown(f"`{task['agent']}`")
                c2.markdown(task["task"][:120] + ("..." if len(task["task"]) > 120 else ""))

        # Delivery
        st.divider()
        st.markdown("**📄 Entrega final al cliente**")
        st.markdown(result["final_delivery"])
        st.divider()
        download_button(result["final_delivery"], "entrega_cliente.md")


# ─── Web Developer ────────────────────────────────────────────────────────────
elif page == "🌐 Web Developer":
    st.subheader("🌐 Web Developer Agent")
    st.caption("Genera código web listo para producción — landing pages, componentes, APIs.")

    task = st.text_area(
        "¿Qué necesitas desarrollar?",
        placeholder='Ej: "Landing page moderna para academia de yoga online con sección hero, servicios y formulario de contacto"',
        height=120,
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        output_file = st.text_input("Nombre de archivo (opcional)", placeholder="landing.html")
    with col2:
        max_tokens = st.selectbox("Tamaño output", [8000, 16000, 32000], index=1)

    if st.button("⚡ Generar código", type="primary", disabled=not task.strip()):
        from agents.specialists.web_developer import WebDeveloperAgent
        from tools.file_tool import save_to_file

        with st.spinner("Desarrollando... puede tardar 30-60s para páginas completas"):
            result = WebDeveloperAgent().run(task, max_tokens=max_tokens)

        # Strip markdown fences if present
        if result.strip().startswith("```"):
            lines = result.splitlines()
            result = "\n".join(l for l in lines if not l.strip().startswith("```"))

        st.success("✅ Código generado")

        tab1, tab2 = st.tabs(["📄 Código", "👁️ Preview"])
        with tab1:
            st.code(result, language="html" if "html" in task.lower() else "text")
        with tab2:
            if "html" in result.lower()[:50]:
                st.components.v1.html(result, height=600, scrolling=True)
            else:
                st.info("Preview disponible solo para HTML completo.")

        if output_file:
            info = save_to_file(output_file, result)
            st.caption(f"💾 Guardado en `{info['saved']}`")

        download_button(result, output_file or "output.html")


# ─── Content & Marketing ──────────────────────────────────────────────────────
elif page == "📣 Contenido & Marketing":
    st.subheader("📣 Content & Marketing Agent")
    st.caption("Copy, posts, emails, artículos SEO y estrategia de contenidos.")

    content_type = st.selectbox(
        "Tipo de contenido",
        ["Post Instagram", "Post LinkedIn", "Email marketing", "Blog post SEO",
         "Copy para anuncio", "Guión para vídeo", "Descripción de producto", "Otro"],
    )

    brief = st.text_area(
        "Brief del contenido",
        placeholder='Ej: "3 posts de Instagram para una cafetería de especialidad en Madrid, tono cercano y moderno, enfocados en el proceso del café"',
        height=120,
    )

    tone = st.select_slider(
        "Tono",
        options=["Muy formal", "Formal", "Neutro", "Cercano", "Muy cercano/divertido"],
        value="Cercano",
    )

    if st.button("✍️ Generar contenido", type="primary", disabled=not brief.strip()):
        from agents.specialists.content_marketing import ContentMarketingAgent

        full_brief = f"Tipo: {content_type}. Tono: {tone}. {brief}"
        with st.spinner("Creando contenido..."):
            result = ContentMarketingAgent().run(full_brief)

        st.divider()
        st.markdown(result)
        st.divider()
        download_button(result, "contenido.md")


# ─── Chatbot Specialist ───────────────────────────────────────────────────────
elif page == "🤖 Chatbot Specialist":
    st.subheader("🤖 Chatbot Specialist Agent")
    st.caption("Diseña chatbots personalizados para cualquier negocio o sector.")

    col1, col2 = st.columns(2)
    with col1:
        business_name = st.text_input("Nombre del negocio", placeholder="La Dolce Vita")
        sector = st.selectbox(
            "Sector",
            ["Restaurante / Bar", "E-commerce", "Salud / Clínica", "Inmobiliaria",
             "Educación", "Servicios profesionales", "Hotel / Turismo", "Otro"],
        )
    with col2:
        objectives = st.multiselect(
            "Objetivos del chatbot",
            ["Gestión de reservas", "Atención al cliente", "FAQ / Información",
             "Generación de leads", "Soporte técnico", "Ventas", "Seguimiento de pedidos"],
            default=["Atención al cliente", "FAQ / Información"],
        )
        tone_bot = st.select_slider(
            "Personalidad del bot",
            options=["Muy formal", "Profesional", "Amigable", "Cercano", "Divertido"],
            value="Amigable",
        )

    extra = st.text_area("Contexto adicional (opcional)",
                         placeholder="Horarios, servicios especiales, información relevante...",
                         height=80)

    if st.button("🤖 Diseñar chatbot", type="primary", disabled=not business_name.strip()):
        from agents.specialists.chatbot_specialist import ChatbotSpecialist

        brief = (
            f"Negocio: {business_name} | Sector: {sector} | "
            f"Objetivos: {', '.join(objectives)} | Personalidad: {tone_bot}. "
            f"{extra}"
        )
        with st.spinner("Diseñando chatbot..."):
            result = ChatbotSpecialist().run(brief)

        st.divider()
        st.markdown(result)
        st.divider()
        download_button(result, f"chatbot_{business_name.lower().replace(' ', '_')}.md")


# ─── Autonomous Agent ─────────────────────────────────────────────────────────
elif page == "⚡ Agente Autónomo":
    st.subheader("⚡ Agente Autónomo")
    st.caption("Ejecuta tareas complejas de forma independiente usando herramientas.")

    with st.expander("🛠️ Herramientas disponibles"):
        t1, t2, t3, t4 = st.columns(4)
        t1.info("📅 **get_current_datetime**\nFecha y hora actual")
        t2.info("🔢 **calculate**\nOperaciones matemáticas")
        t3.info("💾 **save_to_file**\nGuardar en outputs/")
        t4.info("📂 **read_from_file**\nLeer de outputs/")

    task = st.text_area(
        "Tarea para el agente",
        placeholder='Ej: "¿Qué día es hoy? Calcula el 21% de IVA de 3500€ y guarda el resultado en iva_calculo.txt"',
        height=100,
    )

    if st.button("🚀 Ejecutar tarea", type="primary", disabled=not task.strip()):
        from agents.autonomous_agent import AutonomousAgent

        with st.spinner("Agente trabajando..."):
            result = AutonomousAgent().run(task)

        st.divider()
        st.markdown("**Resultado:**")
        st.markdown(result)
        st.divider()
        download_button(result, "resultado_autonomo.txt")
