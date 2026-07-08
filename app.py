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

    _nav_options = [
        "🏠 Dashboard", "💬 Chat", "📋 Project Manager", "🌐 Web Developer",
        "📣 Contenido & Marketing", "🤖 Chatbot Specialist", "🎙️ Agente de Voz",
        "🔔 Recordatorios & Fidelización", "⭐ Gestor de Reseñas", "📅 Content Engine",
        "📄 Generador de PDFs", "⚡ Agente Autónomo", "🎬 VideoStudio",
        "🚀 Pipeline Completo", "🎯 ProspectorIA", "🏛️ Gestorías", "📊 Base de Datos",
    ]
    # Navegación programática: si un botón del Dashboard pidió ir a otra página,
    # aplicarlo ANTES de instanciar el radio (Streamlit lo permite vía session_state).
    if "_goto" in st.session_state:
        st.session_state.main_nav = st.session_state.pop("_goto")

    page = st.radio(
        "Navegación",
        options=_nav_options,
        label_visibility="collapsed",
        key="main_nav",
    )
    st.divider()
    st.caption("v2.0 · MerakIA · 9 servicios activos")


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

# ─── Dashboard / Centro de Mando ──────────────────────────────────────────────
if page == "🏠 Dashboard":
    st.markdown('<div class="merakia-header">MerakIA · Centro de Mando</div>',
                unsafe_allow_html=True)
    st.markdown("**Inteligencia Artificial con alma para negocios locales — todo en un clic.**")
    st.divider()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Servicios activos", "9")
    col2.metric("Agentes IA", "12")
    col3.metric("Workflows n8n", "4")
    col4.metric("Modelo", "Sonnet 4.6")

    st.divider()

    def _go(destino):
        st.session_state._goto = destino
        st.rerun()

    # ── Servicios para clientes ────────────────────────────────────────────────
    st.subheader("💼 Servicios para clientes")
    servicios = [
        ("🎯", "ProspectorIA", "Encuentra negocios, analiza sus dolores y genera ofertas", "🎯 ProspectorIA"),
        ("🌐", "Web Developer", "Webs a medida por sector con reservas y dashboards", "🌐 Web Developer"),
        ("📅", "Content Engine", "Calendario editorial de 30 días listo para publicar", "📅 Content Engine"),
        ("🤖", "Chatbot IA", "Chatbots personalizados para web, WhatsApp e Instagram", "🤖 Chatbot Specialist"),
        ("🎙️", "Agente de Voz", "Recepcionista IA que atiende llamadas y agenda citas 24/7", "🎙️ Agente de Voz"),
        ("🔔", "Recordatorios", "Anti-no-show y fidelización automática por WhatsApp", "🔔 Recordatorios & Fidelización"),
        ("⭐", "Gestor de Reseñas", "Monitoriza Google y responde reseñas con IA", "⭐ Gestor de Reseñas"),
        ("📣", "Contenido & Marketing", "Copy, posts, emails y piezas sueltas al momento", "📣 Contenido & Marketing"),
        ("🎬", "VideoStudio", "Guion + voz + clips + edición + subtítulos", "🎬 VideoStudio"),
    ]
    cols = st.columns(3)
    for i, (icon, name, desc, destino) in enumerate(servicios):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="result-box" style="min-height:104px">
              <b>{icon} {name}</b><br>
              <small style="color:#94A3B8">{desc}</small>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Abrir {name}", key=f"go_{i}", use_container_width=True):
                _go(destino)

    st.divider()

    # ── Herramientas internas ──────────────────────────────────────────────────
    st.subheader("🛠️ Herramientas internas")
    internas = [
        ("📋", "Project Manager", "Orquesta el equipo completo para un proyecto de cliente", "📋 Project Manager"),
        ("📄", "Generador de PDFs", "Catálogo de servicios y estrategia de captación", "📄 Generador de PDFs"),
        ("💬", "Chat", "Asistente conversacional con memoria", "💬 Chat"),
        ("⚡", "Agente Autónomo", "Tareas complejas con herramientas (cálculo, fechas, archivos)", "⚡ Agente Autónomo"),
        ("🚀", "Pipeline Completo", "Tema → vídeo listo en un solo paso", "🚀 Pipeline Completo"),
        ("📊", "Base de Datos", "Histórico de prospecciones y resultados", "📊 Base de Datos"),
    ]
    cols2 = st.columns(3)
    for i, (icon, name, desc, destino) in enumerate(internas):
        with cols2[i % 3]:
            st.markdown(f"""
            <div class="result-box" style="min-height:92px">
              <b>{icon} {name}</b><br>
              <small style="color:#94A3B8">{desc}</small>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Abrir {name}", key=f"goint_{i}", use_container_width=True):
                _go(destino)

    st.divider()

    # ── Otras plataformas MerakIA ──────────────────────────────────────────────
    st.subheader("🌐 Otras plataformas del ecosistema")
    st.caption("Apps independientes que se lanzan en su propio puerto (usa `start_all.ps1` para arrancarlas todas).")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**🍽️ ChefMenu AI**")
        st.caption("Generador de menús para restaurantes")
        st.link_button("Abrir (:8503)", "http://localhost:8503", use_container_width=True)
    with c2:
        st.markdown("**📈 Financial Analyzer**")
        st.caption("Sistema macro-financiero y alertas")
        st.link_button("Abrir (:8504)", "http://localhost:8504", use_container_width=True)
    with c3:
        st.markdown("**✨ Web pública MerakIA**")
        st.caption("La web de la agencia (Next.js)")
        st.link_button("Abrir (:3860)", "http://localhost:3860", use_container_width=True)


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
    from agents.specialists.web_sector_templates import (
        SECTORES, ESTILOS_VISUALES, construir_brief,
    )

    st.subheader("🌐 Web Developer Agent")
    st.caption("Genera webs y landing pages a medida del sector — con calendario de reservas, catálogos, dashboards...")

    if "web_resultado" not in st.session_state:
        st.session_state.web_resultado = ""
    if "web_nombre_archivo" not in st.session_state:
        st.session_state.web_nombre_archivo = "web.html"

    modo = st.radio(
        "Modo de creación",
        ["🎯 Asistido por sector", "✍️ Prompt libre"],
        horizontal=True,
    )

    # ── MODO ASISTIDO POR SECTOR ───────────────────────────────────────────────
    if modo == "🎯 Asistido por sector":
        col1, col2 = st.columns(2)
        with col1:
            sector_key = st.selectbox("Tipo de negocio", list(SECTORES.keys()))
            web_nombre = st.text_input("Nombre del negocio", placeholder="Restaurante La Brasa")
            web_ciudad = st.text_input("Ciudad / zona", placeholder="Barcelona")

        sector = SECTORES[sector_key]

        with col2:
            # Pre-seleccionar el estilo sugerido del sector
            estilos_list = list(ESTILOS_VISUALES.keys())
            idx_estilo = estilos_list.index(sector["estilo_sugerido"]) if sector["estilo_sugerido"] in estilos_list else 0
            web_estilo = st.selectbox("Estilo visual", estilos_list, index=idx_estilo)
            st.caption(f"💡 {ESTILOS_VISUALES[web_estilo]}")
            web_paleta = st.text_input("Paleta de colores (opcional)", placeholder=sector["paleta"])

        st.markdown(f"**Secciones de la web** — recomendadas para {sector_key}:")
        secciones_elegidas = []
        cols_sec = st.columns(2)
        for i, sec in enumerate(sector["secciones"]):
            with cols_sec[i % 2]:
                if st.checkbox(sec, value=True, key=f"sec_{i}"):
                    secciones_elegidas.append(sec)

        st.markdown("**Funcionalidades interactivas:**")
        func_elegidas = []
        cols_func = st.columns(2)
        for i, func in enumerate(sector["funcionalidades"]):
            with cols_func[i % 2]:
                if st.checkbox(func, value=True, key=f"func_{i}"):
                    func_elegidas.append(func)

        web_detalles = st.text_area(
            "Detalles adicionales (opcional)",
            placeholder="Ej: queremos destacar el menú del día, tenemos terraza y aceptamos mascotas, el color corporativo es verde botella...",
            height=90,
        )

        with st.expander("🔌 Integraciones sugeridas para este sector"):
            st.write(sector["integraciones"])

        col_a, col_b = st.columns([3, 1])
        with col_b:
            max_tokens = st.selectbox("Tamaño", [16000, 32000, 64000], index=1, key="mt_sector")

        if st.button("⚡ Generar web a medida", type="primary", use_container_width=True):
            brief = construir_brief(
                sector_key=sector_key,
                nombre_negocio=web_nombre,
                ciudad=web_ciudad,
                estilo=web_estilo,
                secciones_elegidas=secciones_elegidas,
                funcionalidades_elegidas=func_elegidas,
                detalles_extra=web_detalles,
                paleta_custom=web_paleta,
            )
            from agents.specialists.web_developer import WebDeveloperAgent
            with st.spinner("Diseñando tu web a medida... puede tardar 60-90s para webs completas"):
                result = WebDeveloperAgent().run(brief, max_tokens=int(max_tokens))
            if result.strip().startswith("```"):
                lines = result.splitlines()
                result = "\n".join(l for l in lines if not l.strip().startswith("```"))
            st.session_state.web_resultado = result
            slug = (web_nombre or sector_key).replace(" ", "_").replace("/", "")
            st.session_state.web_nombre_archivo = f"{slug}.html"

    # ── MODO PROMPT LIBRE ──────────────────────────────────────────────────────
    else:
        task = st.text_area(
            "¿Qué necesitas desarrollar?",
            placeholder='Ej: "Landing page moderna para academia de yoga online con sección hero, servicios y formulario de contacto"',
            height=120,
        )
        col1, col2 = st.columns([2, 1])
        with col1:
            output_file = st.text_input("Nombre de archivo (opcional)", placeholder="landing.html")
        with col2:
            max_tokens = st.selectbox("Tamaño output", [8000, 16000, 32000, 64000], index=1, key="mt_libre")

        if st.button("⚡ Generar código", type="primary", disabled=not task.strip()):
            from agents.specialists.web_developer import WebDeveloperAgent
            with st.spinner("Desarrollando... puede tardar 30-90s para páginas completas"):
                result = WebDeveloperAgent().run(task, max_tokens=int(max_tokens))
            if result.strip().startswith("```"):
                lines = result.splitlines()
                result = "\n".join(l for l in lines if not l.strip().startswith("```"))
            st.session_state.web_resultado = result
            st.session_state.web_nombre_archivo = output_file or "web.html"

    # ── RESULTADO (común a ambos modos) ────────────────────────────────────────
    if st.session_state.web_resultado:
        result = st.session_state.web_resultado
        st.success("✅ Web generada")
        tab1, tab2 = st.tabs(["👁️ Preview", "📄 Código"])
        with tab1:
            if "<html" in result.lower() or "<!doctype" in result.lower():
                st.components.v1.html(result, height=700, scrolling=True)
            else:
                st.info("Preview disponible solo para HTML completo.")
        with tab2:
            st.code(result, language="html")

        download_button(result, st.session_state.web_nombre_archivo)


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
    st.caption("Genera un system prompt completo y listo para desplegar, personalizado con la información real del negocio.")

    # ── Datos del negocio ──
    st.markdown("#### 1. Datos del negocio")
    col1, col2 = st.columns(2)
    with col1:
        business_name = st.text_input("Nombre del negocio", placeholder="Clínica Dental Sonrisa")
        sector = st.selectbox(
            "Sector",
            ["Salud / Clínica", "Restaurante / Bar", "E-commerce", "Inmobiliaria",
             "Educación", "Servicios profesionales", "Hotel / Turismo", "Belleza / Estética", "Otro"],
        )
    with col2:
        objectives = st.multiselect(
            "Objetivos del chatbot",
            ["Atención al cliente 24/7", "Gestión de citas / reservas", "FAQ / Información de servicios",
             "Captación de leads", "Información de precios", "Soporte postventa", "Ventas"],
            default=["Atención al cliente 24/7", "FAQ / Información de servicios"],
        )
        tone_bot = st.select_slider(
            "Personalidad del bot",
            options=["Muy formal", "Profesional", "Amigable", "Cercano", "Divertido"],
            value="Profesional",
        )

    extra = st.text_area(
        "Información adicional (horarios, dirección, teléfono, políticas...)",
        placeholder="Ej: Horario L-V 9:00-20:00, Sáb 10:00-14:00. Dirección: Calle Mayor 12, Barcelona. Tel: 932 000 000.",
        height=80,
    )

    # ── Base de conocimiento ──
    st.markdown("#### 2. Base de conocimiento del negocio (opcional pero recomendado)")
    st.caption("Sube los documentos con los servicios, tratamientos, precios, FAQs o cualquier información que el chatbot deba conocer.")

    uploaded_files = st.file_uploader(
        "Arrastra aquí tus archivos (PDF o TXT)",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        help="Ejemplos: catálogo de tratamientos, lista de precios, manual de bienvenida, FAQs internas.",
    )

    # Extraer texto de los archivos subidos
    knowledge_base = ""
    if uploaded_files:
        textos = []
        for f in uploaded_files:
            if f.type == "application/pdf":
                try:
                    from pypdf import PdfReader
                    import io
                    reader = PdfReader(io.BytesIO(f.read()))
                    texto = "\n".join(p.extract_text() or "" for p in reader.pages)
                    textos.append(f"[Archivo: {f.name}]\n{texto.strip()}")
                except Exception as e:
                    st.warning(f"No se pudo leer {f.name}: {e}")
            elif f.type == "text/plain":
                try:
                    texto = f.read().decode("utf-8", errors="ignore")
                    textos.append(f"[Archivo: {f.name}]\n{texto.strip()}")
                except Exception as e:
                    st.warning(f"No se pudo leer {f.name}: {e}")

        if textos:
            knowledge_base = "\n\n---\n\n".join(textos)
            total_chars = len(knowledge_base)
            st.success(f"✅ {len(textos)} archivo(s) cargado(s) — {total_chars:,} caracteres de conocimiento.")
            with st.expander("Vista previa del contenido extraído"):
                st.text(knowledge_base[:2000] + ("..." if total_chars > 2000 else ""))

    st.divider()

    if st.button("🤖 Generar system prompt", type="primary", disabled=not business_name.strip()):
        from agents.specialists.chatbot_specialist import ChatbotSpecialist

        brief_parts = [
            f"NEGOCIO: {business_name}",
            f"SECTOR: {sector}",
            f"OBJETIVOS DEL CHATBOT: {', '.join(objectives)}",
            f"PERSONALIDAD / TONO: {tone_bot}",
        ]
        if extra.strip():
            brief_parts.append(f"INFORMACIÓN ADICIONAL: {extra.strip()}")

        if knowledge_base:
            # Truncar a 12.000 chars para no saturar el contexto
            kb_truncado = knowledge_base[:12000] + ("..." if len(knowledge_base) > 12000 else "")
            brief_parts.append(
                f"\nBASE DE CONOCIMIENTO DEL NEGOCIO (úsala para hacer el system prompt específico):\n"
                f"{'='*60}\n{kb_truncado}\n{'='*60}"
            )
        else:
            brief_parts.append(
                "\nNo se han subido documentos. Genera el system prompt basándote en el sector "
                "y objetivos indicados, con placeholders [SERVICIO], [PRECIO] donde el cliente "
                "deba rellenar su información real."
            )

        brief = "\n".join(brief_parts)

        with st.spinner("Generando system prompt personalizado (~20s)..."):
            result = ChatbotSpecialist().run(brief)

        from agents.specialists.flowise_export import generar_chatflow_json, generar_snippet_base44
        flowise_json = generar_chatflow_json(result, business_name)
        snippet_base44 = generar_snippet_base44("https://tu-flowise.up.railway.app", business_name)
        slug = business_name.lower().replace(" ", "_")

        st.divider()
        tab_sp, tab_fl, tab_b44, tab_guide, tab_doc = st.tabs([
            "📄 System Prompt", "🔧 Flowise JSON", "🌐 Snippet Web", "📋 Guía paso a paso", "📅 Doctoralia + Agenda"
        ])

        with tab_sp:
            st.markdown(result)
            st.divider()
            col_d1, col_d2 = st.columns(2)
            col_d1.download_button("⬇️ Descargar (.md)", data=result,
                                   file_name=f"chatbot_{slug}.md", mime="text/markdown")
            col_d2.download_button("⬇️ Descargar (.txt)", data=result,
                                   file_name=f"chatbot_{slug}.txt", mime="text/plain")

        with tab_fl:
            st.markdown("#### JSON listo para importar en Flowise")
            st.caption("Flowise → **File → Load Chatflow** → selecciona este archivo")
            st.code(flowise_json, language="json")
            st.download_button(
                "⬇️ Descargar chatflow.json",
                data=flowise_json,
                file_name=f"chatflow_{slug}.json",
                mime="application/json",
            )
            st.info(
                "⚠️ Después de importar: ve al nodo **ChatAnthropic** y selecciona tu "
                "credencial de Anthropic. El system prompt ya está incorporado en el nodo "
                "**Conversation Chain**.", icon="ℹ️"
            )

        with tab_b44:
            st.markdown("#### Snippet de integración")
            st.caption("Sustituye `CHATFLOW_ID` y la URL de Railway por los tuyos reales.")
            st.code(snippet_base44, language="html")
            st.download_button(
                "⬇️ Descargar snippet (.html)",
                data=snippet_base44,
                file_name=f"snippet_{slug}.html",
                mime="text/html",
            )

            st.markdown("**¿Dónde encontrar el Chatflow ID?**")
            st.caption("En Flowise → abre el chatflow → la URL contiene el ID: `/chatflows/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`")

            st.divider()
            st.markdown("#### ¿Cómo integrarlo según la plataforma del cliente?")
            plataforma = st.selectbox(
                "Plataforma web del cliente",
                ["WordPress", "Base44", "Wix", "Squarespace", "HTML puro", "Webflow"],
                key="plataforma_snippet",
            )

            if plataforma == "WordPress":
                st.markdown("""
**Opción A — Plugin WPCode** *(recomendada, 5 min, sin tocar código)*
1. En el panel de WordPress → **Plugins → Añadir nuevo**
2. Busca **WPCode** (antes "Insert Headers and Footers") → Instalar → Activar
3. Ve a **Code Snippets → Header & Footer**
4. Pega el snippet en la sección **Footer**
5. Guarda → el chatbot aparece en todas las páginas

**Opción B — Elementor** *(si el cliente usa Elementor)*
1. Edita cualquier página con Elementor
2. Arrastra un bloque **HTML** al final de la página
3. Pega el snippet → guarda

**Opción C — functions.php** *(técnica, para developers)*
```php
function merakia_chatbot() { ?>
  <!-- pega aquí el snippet completo -->
<?php }
add_action('wp_footer', 'merakia_chatbot');
```
Añadir en **Apariencia → Editor de temas → functions.php**
⚠️ Usar un child theme para no perderlo en actualizaciones.
""")
            elif plataforma == "Base44":
                st.markdown("""
1. Abre el proyecto en Base44
2. Añade un bloque **Embed / HTML personalizado** al final de la página
3. Pega el snippet
4. Publica
""")
            elif plataforma == "Wix":
                st.markdown("""
1. Editor de Wix → **Añadir → Embed → HTML personalizado**
2. Pega el snippet
3. Publica el sitio

O bien: **Panel de Wix → Configuración → Código personalizado → Añadir código → Footer** (afecta a todas las páginas)
""")
            elif plataforma == "Squarespace":
                st.markdown("""
1. **Configuración → Avanzado → Inyección de código**
2. Pega el snippet en la sección **Footer**
3. Guarda y publica
""")
            elif plataforma == "HTML puro":
                st.markdown("""
Pega el snippet justo antes del cierre `</body>` en el archivo HTML:
```html
  <!-- resto del contenido -->
  <!-- chatbot -->
  <script type="module">...</script>
</body>
</html>
```
""")
            elif plataforma == "Webflow":
                st.markdown("""
1. **Configuración del proyecto → Custom Code → Footer Code**
2. Pega el snippet
3. Publica el sitio

O por página: abre la página → Settings → Custom Code → Before `</body>` tag
""")

        with tab_guide:
            st.markdown(f"""
#### Guía completa: Flowise + Railway + Base44

**Tiempo estimado: 20-30 min por cliente nuevo**

---

##### 1. Importar en Flowise
1. Abre tu Flowise en Railway
2. Clic en **File → Load Chatflow**
3. Selecciona el archivo `chatflow_{slug}.json` que descargaste
4. En el nodo **ChatAnthropic** → clic en el campo de credencial → selecciona tu API key de Anthropic (si no la tienes, añádela en **Credentials**)
5. Clic en **Save Chatflow** (icono de nube arriba a la derecha)

---

##### 2. Publicar y obtener el Chatflow ID
1. Clic en el botón **</>** (API Endpoint) arriba a la derecha
2. Copia el **Chatflow ID** (un UUID largo)
3. Copia también la **URL base** de tu Railway (ej: `https://tu-flowise.up.railway.app`)

---

##### 3. Configurar el snippet para Base44
1. En la tab **🌐 Snippet Base44**, sustituye:
   - `CHATFLOW_ID` → el UUID del paso anterior
   - `https://tu-flowise.up.railway.app` → tu URL de Railway
2. Descarga el snippet `.html`

---

##### 4. Pegar en Base44
1. Abre el proyecto del cliente en Base44
2. Añade un bloque de **código HTML / Embed**
3. Pega el contenido del snippet
4. Publica la web

---

##### 5. Probar
- Abre la web del cliente → debe aparecer el botón del chat (abajo a la derecha)
- Prueba con preguntas reales del negocio (servicios, precios, horarios)

---

##### Si el catálogo es muy largo (>20 servicios o PDF extenso)
Considera añadir en Flowise un nodo **PDF File Loader + In-Memory Vector Store**
conectado a un **Conversational Retrieval QA Chain** en lugar del ConversationChain básico.
Esto activa RAG real: el bot busca en el documento en vez de leerlo todo en el prompt.
""")

        with tab_doc:
            st.markdown("#### Integración Chatbot + Doctoralia + Google Calendar")
            st.caption("Genera el workflow de n8n que conecta el chatbot con el calendario de Doctoralia para gestionar citas sin solapamientos.")

            st.info(
                "**Cómo funciona:** el chatbot recoge nombre, teléfono, servicio y fecha. "
                "Llama a este workflow vía webhook. n8n descarga el iCal de Doctoralia, "
                "comprueba si el hueco está libre, crea el evento en Google Calendar y "
                "envía la confirmación por email. Si está ocupado, devuelve las 3 próximas franjas libres.",
                icon="ℹ️",
            )

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                ical_url_input = st.text_input(
                    "URL del iCal de Doctoralia",
                    placeholder="https://www.doctoralia.es/ical/XXXXXXXX.ics",
                    help="En Doctoralia → Mi agenda → Sincronizar calendario → Copiar enlace iCal",
                )
                email_clinica_input = st.text_input(
                    "Email de la clínica",
                    placeholder="clinica@ejemplo.com",
                )
            with col_d2:
                gcal_id_input = st.text_input(
                    "Google Calendar ID",
                    value="primary",
                    help="En Google Calendar → Configuración del calendario → ID del calendario (acaba en @group.calendar.google.com o es 'primary')",
                )
                duracion_input = st.number_input(
                    "Duración de la cita (minutos)",
                    min_value=10, max_value=120, value=30, step=5,
                )

            if st.button("⚙️ Generar workflow n8n", type="primary", key="btn_n8n"):
                from agents.specialists.n8n_export import generar_workflow_doctoralia
                n8n_json = generar_workflow_doctoralia(
                    nombre_clinica=business_name or "Clínica",
                    google_calendar_id=gcal_id_input or "primary",
                    ical_url=ical_url_input or "https://www.doctoralia.es/ical/XXXXXXXX.ics",
                    email_clinica=email_clinica_input or "clinica@ejemplo.com",
                    duracion_cita_min=int(duracion_input),
                )
                slug_n8n = (business_name or "clinica").lower().replace(" ", "_")

                st.success("Workflow generado. Impórtalo en n8n desde **File → Import → From JSON**.")
                st.code(n8n_json, language="json")
                st.download_button(
                    "⬇️ Descargar workflow n8n (.json)",
                    data=n8n_json,
                    file_name=f"n8n_doctoralia_{slug_n8n}.json",
                    mime="application/json",
                )

                st.divider()
                st.markdown("""
#### Configuración en n8n tras importar

1. **Credencial Google Calendar**
   - n8n → Credentials → Add → Google Calendar OAuth2
   - Sigue el flujo OAuth con la cuenta Google de la clínica

2. **Credencial Gmail** *(para el email de confirmación)*
   - n8n → Credentials → Add → Gmail OAuth2
   - Misma cuenta Google o una específica para notificaciones

3. **URL del Webhook** *(para conectar con Flowise)*
   - Activa el workflow → clic en el nodo **Webhook Citas** → copia la URL de producción
   - Formato: `https://tu-n8n.railway.app/webhook/doctoralia-cita`

4. **En Flowise** — añade un nodo HTTP Request al final del chatflow:
   - Method: POST
   - URL: la URL del webhook de n8n
   - Body (JSON):
   ```json
   {
     "nombre":    "{{ $vars.nombre_paciente }}",
     "telefono":  "{{ $vars.telefono }}",
     "email":     "{{ $vars.email }}",
     "servicio":  "{{ $vars.servicio }}",
     "fecha_iso": "{{ $vars.fecha_iso }}"
   }
   ```

5. **Obtener el iCal de Doctoralia**
   - Doctoralia → perfil del médico → Agenda → Sincronizar calendario → Copiar enlace iCal
   - El enlace tiene formato: `https://www.doctoralia.es/ical/XXXXXXXX.ics`
""")


# ─── Agente de Voz ───────────────────────────────────────────────────────────
elif page == "🎙️ Agente de Voz":
    st.subheader("🎙️ Agente de Voz con IA")
    st.caption("Crea una recepcionista virtual que atiende llamadas, agenda citas y reduce no-shows. Exporta a Vapi.ai.")

    # ── Formulario de configuración ──────────────────────────────────────────
    with st.form("voice_agent_form"):
        col1, col2 = st.columns(2)
        with col1:
            va_nombre = st.text_input("Nombre del negocio *", placeholder="Clínica Dental Smile")
            va_sector = st.selectbox(
                "Sector *",
                ["Clínica dental", "Clínica estética / medicina estética", "Peluquería / barbería",
                 "Centro de fisioterapia", "Psicología / terapia", "Restaurante / bar",
                 "Despacho profesional (asesoría, abogado)", "Taller mecánico", "Otro"],
            )
            va_nombre_asistente = st.text_input(
                "Nombre de la asistente virtual",
                placeholder="Sofía",
                help="El nombre con el que se presentará la IA al contestar la llamada",
            )
            va_telefono = st.text_input("Teléfono de atención humana (escalado)", placeholder="93 123 45 67")

        with col2:
            va_horario = st.text_area(
                "Horario de atención *",
                placeholder="Lunes a viernes: 9h a 20h\nSábados: 10h a 14h\nDomingos: cerrado",
                height=100,
            )
            va_servicios = st.text_area(
                "Servicios principales con precios (si los hay) *",
                placeholder="Limpieza bucal: 60€\nBlanqueamiento: 250€\nOrtodoncia: consultar\nExtracción: desde 80€",
                height=100,
            )

        va_info_extra = st.text_area(
            "Información adicional (ubicación, aparcamiento, seguros, idiomas, etc.)",
            placeholder="Estamos en Calle Mayor 15, Barcelona. Aceptamos Adeslas y Sanitas. Hablamos inglés y catalán.",
            height=80,
        )

        col3, col4 = st.columns(2)
        with col3:
            va_voz = st.selectbox(
                "Voz del agente",
                options=["mujer_profesional", "mujer_calida", "hombre_profesional", "hombre_jovial"],
                format_func=lambda v: {
                    "mujer_profesional": "Mujer — profesional y clara",
                    "mujer_calida": "Mujer — cálida y empática",
                    "hombre_profesional": "Hombre — profesional y directo",
                    "hombre_jovial": "Hombre — jovial y cercano",
                }[v],
            )
        with col4:
            va_webhook = st.text_input(
                "URL webhook n8n (opcional)",
                placeholder="https://tu-n8n.railway.app/webhook/citas",
                help="Si tienes n8n configurado, el agente enviará los datos de la cita a esta URL",
            )

        va_submit = st.form_submit_button("🎙️ Generar Agente de Voz", type="primary", use_container_width=True)

    # ── Base de conocimiento (fuera del form — limitación Streamlit) ───────────
    st.markdown("#### Documentos del negocio (opcional pero muy recomendado)")
    st.caption(
        "Sube la carta, menú, lista de tratamientos, precios, FAQs, políticas... "
        "Cuanta más información real, más preciso será el agente al contestar llamadas."
    )
    va_uploaded = st.file_uploader(
        "Arrastra aquí los archivos (PDF o TXT)",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        key="va_docs",
        help="Ejemplos: carta del restaurante, catálogo de tratamientos, tarifas, política de cancelación.",
    )

    va_knowledge_base = ""
    if va_uploaded:
        textos = []
        for f in va_uploaded:
            if f.type == "application/pdf":
                try:
                    from pypdf import PdfReader
                    import io as _io
                    reader = PdfReader(_io.BytesIO(f.read()))
                    texto = "\n".join(p.extract_text() or "" for p in reader.pages)
                    textos.append(f"[Documento: {f.name}]\n{texto.strip()}")
                except Exception as e:
                    st.warning(f"No se pudo leer {f.name}: {e}")
            elif f.type == "text/plain":
                try:
                    texto = f.read().decode("utf-8", errors="ignore")
                    textos.append(f"[Documento: {f.name}]\n{texto.strip()}")
                except Exception as e:
                    st.warning(f"No se pudo leer {f.name}: {e}")
        if textos:
            va_knowledge_base = "\n\n---\n\n".join(textos)
            total_chars = len(va_knowledge_base)
            st.success(f"✅ {len(textos)} archivo(s) cargado(s) — {total_chars:,} caracteres de conocimiento.")
            with st.expander("Vista previa del contenido extraído"):
                st.text(va_knowledge_base[:2000] + ("..." if total_chars > 2000 else ""))

    st.divider()

    # ── Generación ─────────────────────────────────────────────────────────────
    if va_submit:
        if not va_nombre or not va_horario or not va_servicios:
            st.error("Rellena al menos: nombre del negocio, horario y servicios.")
        else:
            nombre_asistente = va_nombre_asistente.strip() or "Sofía"

            kb_section = ""
            if va_knowledge_base:
                kb_truncado = va_knowledge_base[:14000] + ("..." if len(va_knowledge_base) > 14000 else "")
                kb_section = f"""

BASE DE CONOCIMIENTO COMPLETA DEL NEGOCIO (documentos reales subidos por el cliente):
--- INICIO DOCUMENTOS ---
{kb_truncado}
--- FIN DOCUMENTOS ---

USA ESTA INFORMACIÓN para completar el system prompt con datos reales:
menú, tratamientos, precios, políticas de cancelación, normas, servicios especiales, etc.
Si el documento tiene precios, úsalos exactamente. Si tiene servicios, nómbralos todos."""

            brief = f"""Negocio: {va_nombre}
Sector: {va_sector}
Nombre de la asistente: {nombre_asistente}
Teléfono de escalado a humano: {va_telefono or "no indicado — siempre escalar si el cliente insiste"}
Horario: {va_horario}
Servicios y precios (resumen manual): {va_servicios}
Información adicional: {va_info_extra or "ninguna"}{kb_section}

Crea el system prompt completo para un agente de voz telefónico para este negocio.
El agente debe presentarse como {nombre_asistente}, recepcionista de {va_nombre}.
El objetivo principal es agendar citas o tomar pedidos según el sector.
Las respuestas deben ser muy cortas y naturales para voz, sin markdown."""

            with st.spinner("Generando agente de voz..."):
                from agents.specialists.voice_agent_specialist import VoiceAgentSpecialist
                specialist = VoiceAgentSpecialist()
                resultado = specialist.run(brief)

            st.session_state["voice_agent_resultado"] = resultado
            st.session_state["voice_agent_nombre"] = va_nombre
            st.session_state["voice_agent_voz"] = va_voz
            st.session_state["voice_agent_webhook"] = va_webhook
            st.session_state["voice_agent_sector"] = va_sector
            st.success("✅ Agente generado")

    # ── Resultado ──────────────────────────────────────────────────────────────
    if st.session_state.get("voice_agent_resultado"):
        resultado = st.session_state["voice_agent_resultado"]
        nombre_neg = st.session_state.get("voice_agent_nombre", "negocio")
        voz_key = st.session_state.get("voice_agent_voz", "mujer_profesional")
        webhook = st.session_state.get("voice_agent_webhook", "")
        slug = nombre_neg.lower().replace(" ", "_")[:30]

        tab_sp, tab_vapi, tab_agenda, tab_guide = st.tabs([
            "📝 System Prompt de Voz",
            "📦 Exportar a Vapi.ai",
            "📅 Agenda en tiempo real",
            "🚀 Guía de Despliegue",
        ])

        with tab_sp:
            st.markdown("#### System prompt optimizado para voz")
            st.caption("Texto completo generado por la IA — incluye flujos, ejemplos y palabras de escalado.")
            st.markdown(resultado)
            st.download_button(
                "⬇️ Descargar system prompt",
                data=resultado,
                file_name=f"voice_agent_{slug}.md",
                mime="text/markdown",
            )

        with tab_vapi:
            st.markdown("#### Configuración para Vapi.ai")
            st.caption("Importa este JSON en dashboard.vapi.ai → Assistants → Import (↑)")

            # Extraer first_message y end_call_message del resultado si están presentes
            import re
            first_msg = f"¡Hola! Has llamado a {nombre_neg}. Soy {st.session_state.get('voice_agent_nombre', 'la asistente')}. ¿En qué puedo ayudarte hoy?"
            end_msg = "Perfecto, muchas gracias por llamar. ¡Hasta pronto!"

            m = re.search(r'##\s*2\.\s*PRIMER MENSAJE.*?\n+(.+?)(?:\n\n|\n##)', resultado, re.DOTALL | re.IGNORECASE)
            if m:
                extracted = m.group(1).strip().strip('"').strip("*").strip()
                if len(extracted) > 10:
                    first_msg = extracted

            m2 = re.search(r'##\s*3\.\s*MENSAJE DE CIERRE.*?\n+(.+?)(?:\n\n|\n##)', resultado, re.DOTALL | re.IGNORECASE)
            if m2:
                extracted2 = m2.group(1).strip().strip('"').strip("*").strip()
                if len(extracted2) > 5:
                    end_msg = extracted2

            from agents.specialists.vapi_export import generar_vapi_assistant, VOCES_ELEVENLABS
            vapi_json = generar_vapi_assistant(
                system_prompt=resultado,
                first_message=first_msg,
                end_call_message=end_msg,
                nombre_negocio=nombre_neg,
                voz_clave=voz_key,
                webhook_url=webhook,
            )

            st.code(vapi_json[:800] + "\n...", language="json")
            st.download_button(
                "⬇️ Descargar vapi_assistant.json",
                data=vapi_json,
                file_name=f"vapi_{slug}.json",
                mime="application/json",
            )

            voz_info = VOCES_ELEVENLABS.get(voz_key, VOCES_ELEVENLABS["mujer_profesional"])
            st.info(f"🎤 Voz seleccionada: **{voz_info['nombre']}** · ElevenLabs ID: `{voz_info['voiceId']}`")

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Modelo LLM", "Claude Haiku 4.5")
            col_b.metric("Transcriptor", "Deepgram nova-2 ES")
            col_c.metric("Max duración", "5 min / llamada")

        with tab_agenda:
            st.markdown("#### Agenda en tiempo real — sin dobles reservas")
            st.caption(
                "El agente consulta el calendario **antes** de proponer una hora. "
                "Solo confirma la cita cuando el paciente dice que sí. "
                "Todo queda en Google Calendar automáticamente."
            )

            st.info(
                "**Cómo funciona:**\n\n"
                "1. El paciente llama y pide cita\n"
                "2. El agente llama a `check_availability` → n8n consulta Google Calendar → devuelve huecos libres\n"
                "3. El agente propone los huecos: *\"Tengo las 10h o las 16h, ¿cuál le va mejor?\"*\n"
                "4. El paciente elige\n"
                "5. El agente pide nombre y teléfono, luego llama a `book_appointment`\n"
                "6. n8n crea el evento en Google Calendar al instante\n"
                "7. El agente confirma verbalmente: *\"Listo, le apunto el martes a las 10h\"*\n\n"
                "El calendario es siempre la fuente de verdad. Nunca hay dobles reservas."
            )

            with st.form("agenda_form"):
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    ag_calendar_id = st.text_input(
                        "ID del Google Calendar *",
                        placeholder="primary   ó   clinica@gmail.com",
                        help="'primary' usa el calendario principal de la cuenta. Para calendarios específicos, copia el ID desde Google Calendar → Ajustes del calendario → ID del calendario.",
                    )
                    ag_duracion = st.number_input(
                        "Duración de cada cita (minutos)",
                        min_value=10, max_value=180, value=30, step=5,
                    )
                    ag_email = st.text_input(
                        "Email del negocio (para notificaciones)",
                        placeholder="clinica@ejemplo.com",
                    )
                with col_a2:
                    ag_hora_inicio = st.number_input("Primera cita del día (hora)", min_value=6, max_value=12, value=9)
                    ag_hora_fin = st.number_input("Última cita posible (hora)", min_value=12, max_value=22, value=20)
                    ag_dias = st.multiselect(
                        "Días laborables",
                        options=[1, 2, 3, 4, 5, 6, 7],
                        default=[1, 2, 3, 4, 5],
                        format_func=lambda d: ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][d-1],
                    )

                ag_submit = st.form_submit_button("⚙️ Generar workflow n8n + tools Vapi", type="primary", use_container_width=True)

            if ag_submit:
                if not ag_calendar_id:
                    st.error("Introduce el ID del Google Calendar.")
                else:
                    dias_str = ",".join(str(d) for d in sorted(ag_dias)) if ag_dias else "1,2,3,4,5"
                    from agents.specialists.n8n_export import generar_workflow_voz_agenda
                    n8n_json = generar_workflow_voz_agenda(
                        nombre_negocio=nombre_neg,
                        google_calendar_id=ag_calendar_id,
                        email_negocio=ag_email or "negocio@ejemplo.com",
                        duracion_cita_min=int(ag_duracion),
                        hora_inicio=int(ag_hora_inicio),
                        hora_fin=int(ag_hora_fin),
                        dias_laborables=dias_str,
                    )
                    st.session_state["voz_n8n_json"] = n8n_json
                    st.success("✅ Workflow generado")

            if st.session_state.get("voz_n8n_json"):
                n8n_json = st.session_state["voz_n8n_json"]
                st.download_button(
                    "⬇️ Descargar workflow n8n (agenda_voz.json)",
                    data=n8n_json,
                    file_name=f"agenda_voz_{slug}.json",
                    mime="application/json",
                    use_container_width=True,
                )
                st.markdown("##### Pasos para activarlo")
                webhook_base = webhook.rstrip("/") if webhook else "https://TU_N8N.railway.app"
                webhook_voz = f"{webhook_base.rsplit('/webhook', 1)[0]}/webhook/voz-agenda" if webhook else "https://TU_N8N.railway.app/webhook/voz-agenda"
                st.markdown(f"""
1. En n8n → **File → Import → From JSON** → sube `agenda_voz_{slug}.json`
2. Ve a **Credentials** y conecta tu cuenta de **Google Calendar**
3. Activa el workflow (toggle **Active**)
4. La URL del webhook será: `{webhook_voz}`
5. Descarga de nuevo el JSON de Vapi (tab "📦 Exportar a Vapi.ai") **con esa URL en el campo webhook** para que los tools queden enlazados
6. Prueba: llama al número de Vapi y pide cita para un día concreto
""")
                with st.expander("Ver JSON del workflow"):
                    st.code(n8n_json[:1500] + "\n...", language="json")

        with tab_guide:
            from agents.specialists.vapi_export import generar_guia_vapi
            sector_guardado = st.session_state.get("voice_agent_sector", "")
            guia = generar_guia_vapi(nombre_neg, webhook, tiene_n8n=bool(webhook), sector=sector_guardado)
            st.markdown(guia)


# ─── Recordatorios & Fidelización ─────────────────────────────────────────────
elif page == "🔔 Recordatorios & Fidelización":
    st.subheader("🔔 Recordatorios, Anti-no-show y Fidelización")
    st.caption("Genera el pack de mensajes automáticos que reducen ausencias y reactivan clientes. Se automatiza con n8n leyendo el calendario.")

    with st.form("retention_form"):
        col1, col2 = st.columns(2)
        with col1:
            rt_nombre = st.text_input("Nombre del negocio *", placeholder="Clínica Dental Smile")
            rt_sector = st.selectbox(
                "Sector *",
                ["Clínica dental", "Clínica estética / medicina estética", "Peluquería / barbería",
                 "Centro de fisioterapia", "Psicología / terapia", "Restaurante / bar",
                 "Gimnasio / centro deportivo", "Farmacia", "Despacho profesional", "Otro"],
            )
            rt_telefono = st.text_input("Teléfono del negocio", placeholder="93 123 45 67")
            rt_tono = st.selectbox("Trato con el cliente", ["Tuteo (cercano)", "Usted (formal)"])
        with col2:
            rt_servicios = st.text_area(
                "Servicios principales / ciclo de visita *",
                placeholder="Limpieza dental (cada 6 meses)\nRevisión anual\nOrtodoncia\nBlanqueamiento",
                height=110,
            )
            rt_incentivo = st.text_input(
                "Incentivo para reactivar (opcional)",
                placeholder="Ej: revisión gratuita, 10% en la próxima visita",
            )
            rt_enlace_resena = st.text_input(
                "Enlace para pedir reseña en Google (opcional)",
                placeholder="https://g.page/r/...",
            )

        rt_submit = st.form_submit_button("🔔 Generar pack de mensajes", type="primary", use_container_width=True)

    if rt_submit:
        if not rt_nombre or not rt_servicios:
            st.error("Rellena al menos: nombre del negocio y servicios.")
        else:
            brief = f"""Negocio: {rt_nombre}
Sector: {rt_sector}
Teléfono del negocio: {rt_telefono or "[teléfono]"}
Trato: {rt_tono}
Servicios y ciclo de visita: {rt_servicios}
Incentivo de reactivación: {rt_incentivo or "ninguno concreto — usa un motivo natural para volver"}
Enlace de reseña: {rt_enlace_resena or "{enlace_resena}"}

Crea el pack completo de mensajes de recordatorio, anti-no-show y fidelización para este negocio,
adaptado a su sector y su ciclo de servicio."""

            with st.spinner("Generando mensajes..."):
                from agents.specialists.retention_specialist import RetentionSpecialist
                resultado = RetentionSpecialist().run(brief)

            st.session_state["retention_resultado"] = resultado
            st.session_state["retention_nombre"] = rt_nombre
            st.session_state["retention_telefono"] = rt_telefono
            st.success("✅ Pack generado")

    if st.session_state.get("retention_resultado"):
        resultado = st.session_state["retention_resultado"]
        nombre_neg = st.session_state.get("retention_nombre", "negocio")
        tel_neg = st.session_state.get("retention_telefono", "")
        slug = nombre_neg.lower().replace(" ", "_")[:30]

        tab_msg, tab_auto, tab_guide = st.tabs([
            "💬 Pack de mensajes",
            "⚙️ Automatización n8n",
            "🚀 Guía de uso",
        ])

        with tab_msg:
            st.markdown("#### Mensajes listos para usar")
            st.caption("Variables como {nombre}, {fecha}, {hora}, {servicio} las rellena el sistema en cada envío.")
            st.markdown(resultado)
            st.download_button(
                "⬇️ Descargar pack de mensajes",
                data=resultado,
                file_name=f"mensajes_retencion_{slug}.md",
                mime="text/markdown",
            )

        with tab_auto:
            st.markdown("#### Workflow de recordatorios automáticos")
            st.caption("Lee el Google Calendar del negocio y envía el recordatorio X horas antes de cada cita.")

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                rt_calendar = st.text_input("Google Calendar ID", value="primary", key="rt_cal")
            with col_b:
                rt_canal = st.selectbox("Canal de envío", ["whatsapp", "email"], key="rt_canal",
                                        format_func=lambda c: "WhatsApp (Twilio)" if c == "whatsapp" else "Email (Gmail)")
            with col_c:
                rt_horas = st.number_input("Horas antes de la cita", min_value=1, max_value=72, value=24, key="rt_horas")

            if st.button("⚙️ Generar workflow n8n", key="rt_gen_n8n"):
                from agents.specialists.n8n_export import generar_workflow_recordatorios
                n8n_json = generar_workflow_recordatorios(
                    nombre_negocio=nombre_neg,
                    google_calendar_id=rt_calendar,
                    canal=rt_canal,
                    horas_antes=int(rt_horas),
                    telefono_negocio=tel_neg,
                )
                st.session_state["retention_n8n"] = n8n_json
                st.success("✅ Workflow generado")

            if st.session_state.get("retention_n8n"):
                st.download_button(
                    "⬇️ Descargar workflow n8n (recordatorios.json)",
                    data=st.session_state["retention_n8n"],
                    file_name=f"recordatorios_{slug}.json",
                    mime="application/json",
                    use_container_width=True,
                )
                with st.expander("Ver JSON del workflow"):
                    st.code(st.session_state["retention_n8n"][:1500] + "\n...", language="json")

        with tab_guide:
            canal_actual = st.session_state.get("rt_canal", "whatsapp")
            credencial = "Twilio (WhatsApp Business)" if canal_actual == "whatsapp" else "Gmail"
            st.markdown(f"""
## Cómo poner en marcha la automatización

### 1. Importa el workflow en n8n
1. n8n → **File → Import → From JSON** → sube `recordatorios_{slug}.json`
2. Conecta la credencial de **Google Calendar** (para leer las citas)
3. Conecta la credencial de **{credencial}** (para enviar los mensajes)

### 2. Cómo funciona
- El workflow se ejecuta **cada hora** automáticamente
- Lee las citas que empiezan dentro de **{st.session_state.get('rt_horas', 24)} horas**
- Extrae nombre, teléfono y servicio del evento del calendario
- Envía el recordatorio personalizado por {('WhatsApp' if canal_actual == 'whatsapp' else 'email')}

> **Importante:** para que funcione, las citas del calendario deben tener el teléfono
> en la descripción (formato `Teléfono: 600123456`). El **Agente de Voz** ya las crea
> así automáticamente — los dos sistemas encajan.

### 3. Las otras secuencias (no-show, win-back, fidelización)
Los mensajes del pack para **recuperación de no-show**, **reactivación de clientes dormidos**
y **post-visita + reseña** se disparan con eventos distintos (una ausencia, X meses sin volver,
fin de la cita). Se montan como workflows adicionales en n8n usando los mismos textos.
Empieza por el recordatorio automático (el de mayor impacto inmediato) y amplía después.

### Argumento de venta para el cliente
> *"Cada no-show es dinero perdido. Este sistema recuerda automáticamente cada cita por
> WhatsApp y recupera a quien no viene. Las clínicas que lo usan reducen las ausencias
> entre un 30% y un 50% sin que nadie del equipo tenga que escribir un solo mensaje."*

**Precio sugerido:** 297-497€ setup + 79-149€/mes gestión.
""")


# ─── Gestor de Reseñas & Reputación ──────────────────────────────────────────
elif page == "⭐ Gestor de Reseñas":
    from agents.specialists.reviews_specialist import ReviewsSpecialist
    from agents.specialists.n8n_export import generar_workflow_resenas

    st.subheader("⭐ Gestor de Reseñas & Reputación")
    st.caption("Analiza tus reseñas de Google, genera respuestas con IA y automatiza la monitorización.")

    if "reviews_resultado" not in st.session_state:
        st.session_state.reviews_resultado = ""
    if "reviews_nombre" not in st.session_state:
        st.session_state.reviews_nombre = ""
    if "reviews_n8n_json" not in st.session_state:
        st.session_state.reviews_n8n_json = ""

    # ── Formulario principal ───────────────────────────────────────────────────
    with st.form("form_reviews"):
        col1, col2 = st.columns(2)
        with col1:
            rev_nombre = st.text_input("Nombre del negocio *", placeholder="Clínica Dental Sonrisa")
            rev_sector = st.selectbox("Sector", [
                "Clínica dental", "Clínica estética / belleza", "Restaurante",
                "Gimnasio / wellness", "Farmacia", "Peluquería", "Fisioterapia / salud",
                "Otro",
            ])
            rev_rating = st.slider("Rating actual en Google (★)", 1.0, 5.0, 4.2, 0.1)
        with col2:
            rev_place_id = st.text_input(
                "Google Place ID (opcional)",
                placeholder="ChIJN1t_tDeuEmsRUsoyG83frY4",
                help="Búscalo en Google Maps → tu negocio → Compartir → enlace. O déjalo vacío para añadirlo después.",
            )
            rev_email = st.text_input("Email del negocio (para alertas)", placeholder="info@clinica.com")
            rev_horas = st.selectbox("Frecuencia de monitorización", [4, 6, 12, 24], index=1,
                                     format_func=lambda h: f"Cada {h} horas")

        st.markdown("**Pega aquí las reseñas reales del negocio** (copia desde Google Maps):")
        rev_resenas = st.text_area(
            "Reseñas",
            height=220,
            placeholder=(
                "★★★★★ — María G. (hace 2 semanas)\n"
                "Increíble atención, me trataron con mucha amabilidad y el resultado fue perfecto.\n\n"
                "★★☆☆☆ — Juan L. (hace 1 mes)\n"
                "Esperé 40 minutos más de lo previsto. El trato fue correcto pero la espera es mejorable.\n\n"
                "★★★★★ — Ana R. (hace 3 semanas)\n"
                "Llevo años viniendo y siempre quedo encantada. Los mejores de la zona sin duda."
            ),
            label_visibility="collapsed",
        )

        rev_tono = st.radio(
            "Tono de las respuestas",
            ["Cálido y cercano", "Profesional y formal", "Dinámico y moderno"],
            horizontal=True,
        )

        submitted = st.form_submit_button("Generar respuestas y análisis", type="primary", use_container_width=True)

    if submitted:
        if not rev_nombre or not rev_resenas:
            st.error("Completa el nombre del negocio y pega al menos una reseña.")
        else:
            with st.spinner("Analizando reseñas y generando respuestas..."):
                specialist = ReviewsSpecialist()
                brief = f"""Negocio: {rev_nombre}
Sector: {rev_sector}
Rating actual en Google: {rev_rating}★
Tono deseado para las respuestas: {rev_tono}

RESEÑAS REALES (copia literal de Google):
{rev_resenas}

Genera las respuestas personalizadas para CADA reseña, el análisis de reputación completo y el plan de acción."""
                resultado = specialist.run(brief)
                st.session_state.reviews_resultado = resultado
                st.session_state.reviews_nombre = rev_nombre

                # Generar workflow n8n
                st.session_state.reviews_n8n_json = generar_workflow_resenas(
                    nombre_negocio=rev_nombre,
                    place_id=rev_place_id,
                    google_api_key="TU_GOOGLE_API_KEY",
                    email_negocio=rev_email or "email@negocio.com",
                    horas_check=int(rev_horas),
                    min_stars_alerta=3,
                )

    if st.session_state.reviews_resultado:
        tabs = st.tabs(["📝 Respuestas & Análisis", "⚙️ Automatización n8n", "📖 Guía de uso"])

        # ── Tab 1: Respuestas y análisis ───────────────────────────────────────
        with tabs[0]:
            st.markdown(st.session_state.reviews_resultado)
            st.download_button(
                "📥 Descargar análisis completo (.txt)",
                data=st.session_state.reviews_resultado,
                file_name=f"resenas_{st.session_state.reviews_nombre.replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        # ── Tab 2: Workflow n8n ────────────────────────────────────────────────
        with tabs[1]:
            st.markdown("### ⚙️ Workflow n8n — Monitorización automática de reseñas")
            st.info(
                "Este workflow revisa tus reseñas de Google cada pocas horas, envía alertas "
                "por email cuando llega una reseña negativa y guarda la respuesta sugerida "
                "por IA en un Google Sheet listo para que la revises y publiques.",
                icon="ℹ️",
            )

            col1, col2 = st.columns(2)
            with col1:
                n8n_place = st.text_input("Google Place ID", placeholder="ChIJN1t_tDeuEmsRUsoyG83frY4",
                                          key="n8n_place_id")
                n8n_sheets = st.text_input("Google Sheets ID", placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
                                           key="n8n_sheets_id")
            with col2:
                n8n_stars = st.selectbox("Alertar si rating ≤", [2, 3, 4], index=1,
                                         format_func=lambda s: f"{s}★ o menos",
                                         key="n8n_stars")
                n8n_horas2 = st.selectbox("Frecuencia", [4, 6, 12, 24], index=1,
                                           format_func=lambda h: f"Cada {h} horas",
                                           key="n8n_horas2")

            if st.button("Regenerar workflow con estos datos", key="btn_regen_n8n_reviews"):
                st.session_state.reviews_n8n_json = generar_workflow_resenas(
                    nombre_negocio=st.session_state.reviews_nombre,
                    place_id=n8n_place,
                    google_api_key="TU_GOOGLE_API_KEY",
                    email_negocio=rev_email or "email@negocio.com",
                    horas_check=int(n8n_horas2),
                    min_stars_alerta=int(n8n_stars),
                )
                st.success("Workflow actualizado.")

            st.download_button(
                "📥 Descargar workflow n8n (.json)",
                data=st.session_state.reviews_n8n_json,
                file_name=f"n8n_resenas_{st.session_state.reviews_nombre.replace(' ', '_')}.json",
                mime="application/json",
                use_container_width=True,
            )

            with st.expander("Ver JSON del workflow"):
                st.code(st.session_state.reviews_n8n_json, language="json")

            st.markdown("""
**Pasos para activarlo en n8n:**
1. Abre n8n → **Workflows → Import from file** → sube el JSON descargado
2. En el nodo **"Obtener reseñas Google"**: añade tu `GOOGLE_API_KEY` y el `Place ID` de tu negocio
3. En el nodo **"Alerta email negativa"**: conecta tu cuenta de Gmail
4. En el nodo **"Guardar en Google Sheets"**: conecta Google Sheets y selecciona tu hoja
5. En el nodo **"Generar respuesta con IA"**: añade tu `ANTHROPIC_API_KEY` en las variables de entorno de n8n
6. Activa el workflow con el toggle → empieza a monitorizar automáticamente

**¿Cómo encontrar el Place ID?**
Busca tu negocio en Google Maps → haz clic derecho en el marcador → "¿Qué hay aquí?" → el ID aparece en la URL o en la tarjeta inferior.
""")

        # ── Tab 3: Guía ───────────────────────────────────────────────────────
        with tabs[2]:
            st.markdown(f"""
## ⭐ Gestor de Reseñas & Reputación — Guía de venta

### ¿Qué hace este servicio?
Monitoriza automáticamente las reseñas de Google del negocio, alerta cuando llega una negativa
y genera respuestas profesionales con IA que el equipo solo tiene que revisar y publicar.

### Por qué es crítico para el negocio local
- **El 87% de los consumidores** lee reseñas antes de elegir un negocio local
- Una reseña negativa sin respuesta → señal de que al negocio no le importa
- Una respuesta bien redactada a una negativa **puede convertirla en positiva**
- Negocios con rating ≥ 4.5★ y respuestas activas reciben **un 35% más de clics** en Google Maps
- Cada 10 nuevas reseñas positivas sube aproximadamente **0.1 puntos el rating**

### Argumentario de venta para {st.session_state.reviews_nombre}
*"¿Sabes cuántas personas leen tus reseñas de Google antes de llamarte?
Con este sistema, cuando alguien te deja una mala reseña, recibes una alerta en el momento
y tienes lista una respuesta profesional en segundos. Y para las buenas, el sistema también
genera un agradecimiento personalizado que muestra que te preocupas por tus clientes.
El resultado: mejor posicionamiento en Google Maps y más confianza antes de que nadie llame."*

### Precio sugerido
- **Setup:** 297-497€ (configuración + primeras respuestas + workflow n8n)
- **Gestión mensual:** 97-197€/mes (monitorización + revisión de respuestas + informe mensual)
""")


# ─── Content Engine ───────────────────────────────────────────────────────────
elif page == "📅 Content Engine":
    import io, csv
    from agents.specialists.content_engine_specialist import ContentEngineSpecialist

    st.subheader("📅 Content Engine — Calendario Editorial 30 días")
    st.caption("Genera el calendario completo con copy listo para publicar en Instagram, Facebook, TikTok y Google Business.")

    if "ce_resultado" not in st.session_state:
        st.session_state.ce_resultado = ""
    if "ce_nombre" not in st.session_state:
        st.session_state.ce_nombre = ""

    with st.form("form_content_engine"):
        col1, col2 = st.columns(2)
        with col1:
            ce_nombre = st.text_input("Nombre del negocio *", placeholder="Clínica Dental Sonrisa")
            ce_sector = st.selectbox("Sector", [
                "Clínica dental", "Clínica estética / medicina estética",
                "Restaurante / bar", "Gimnasio / centro de wellness",
                "Peluquería / salón de belleza", "Farmacia", "Fisioterapia / osteopatía",
                "Psicología / coaching", "Veterinaria", "Centro deportivo",
                "Tienda local / comercio", "Otro",
            ])
            ce_ciudad = st.text_input("Ciudad o zona", placeholder="Barcelona, Gràcia")
            ce_objetivo = st.selectbox("Objetivo principal del mes", [
                "Conseguir más citas / reservas",
                "Aumentar seguidores y visibilidad",
                "Lanzar un servicio nuevo",
                "Fidelizar clientes actuales",
                "Posicionarse como referente local",
                "Campaña de temporada / promoción",
            ])

        with col2:
            ce_plataformas = st.multiselect(
                "Plataformas *",
                ["Instagram", "Facebook", "TikTok", "Google Business Profile"],
                default=["Instagram", "Google Business Profile"],
            )
            ce_tono = st.selectbox("Tono de comunicación", [
                "Cálido y cercano (tuteo, emojis moderados)",
                "Profesional y confiable (tratamiento formal)",
                "Dinámico y moderno (lenguaje joven, mucho humor)",
                "Educativo y experto (datos, consejos, formación)",
            ])
            ce_frecuencia = st.selectbox("Frecuencia de publicación", [
                "3 días/semana (ritmo sostenible)",
                "5 días/semana (ritmo activo)",
                "7 días/semana (ritmo intensivo)",
            ])
            ce_mes = st.selectbox("Mes del calendario", [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
            ], index=5)

        ce_servicios = st.text_area(
            "Servicios o productos principales (uno por línea)",
            height=80,
            placeholder="Limpieza dental — 60€\nBlanqueamiento LED — 290€\nOrtodoncia invisible — desde 2.500€",
        )
        ce_extra = st.text_area(
            "Eventos, promociones o novedades de este mes (opcional)",
            height=60,
            placeholder="Descuento 15% en blanqueamiento todo el mes · Apertura nuevo box de pilates",
        )

        submitted_ce = st.form_submit_button("🚀 Generar calendario editorial", type="primary", use_container_width=True)

    if submitted_ce:
        if not ce_nombre or not ce_plataformas:
            st.error("Completa el nombre del negocio y selecciona al menos una plataforma.")
        else:
            with st.spinner("Creando tu calendario editorial de 30 días... (puede tardar 30-60 segundos)"):
                specialist = ContentEngineSpecialist()
                brief = f"""Negocio: {ce_nombre}
Sector: {ce_sector}
Ciudad/Zona: {ce_ciudad or 'España'}
Mes: {ce_mes}
Objetivo del mes: {ce_objetivo}
Plataformas: {', '.join(ce_plataformas)}
Tono: {ce_tono}
Frecuencia: {ce_frecuencia}
Servicios principales:
{ce_servicios or '(no especificados)'}
Eventos o novedades del mes:
{ce_extra or 'Ninguno en particular'}

Genera el calendario editorial completo de 30 días con copy íntegro de cada post."""
                resultado = specialist.run(brief)
                st.session_state.ce_resultado = resultado
                st.session_state.ce_nombre = ce_nombre

    if st.session_state.ce_resultado:
        tabs = st.tabs(["📅 Calendario completo", "📥 Exportar", "📖 Guía de uso"])

        with tabs[0]:
            st.markdown(st.session_state.ce_resultado)

        with tabs[1]:
            st.markdown("### 📥 Descarga tu calendario")
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "📄 Descargar en Markdown (.md)",
                    data=st.session_state.ce_resultado,
                    file_name=f"calendario_{st.session_state.ce_nombre.replace(' ', '_')}_{ce_mes}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with col2:
                # Generar CSV simple
                lines = st.session_state.ce_resultado.split("\n")
                csv_rows = [["Día", "Plataforma", "Categoría", "Copy", "Hashtags", "Formato", "Hora"]]
                current = {}
                for line in lines:
                    if line.startswith("**Día "):
                        if current.get("dia"):
                            csv_rows.append([
                                current.get("dia", ""),
                                current.get("plataforma", ""),
                                current.get("categoria", ""),
                                current.get("copy", ""),
                                current.get("hashtags", ""),
                                current.get("formato", ""),
                                current.get("hora", ""),
                            ])
                        parts = line.strip("*").split(" — ")
                        current = {
                            "dia": parts[0].replace("Día ", "").strip() if len(parts) > 0 else "",
                            "plataforma": parts[1].strip() if len(parts) > 1 else "",
                            "categoria": parts[2].strip() if len(parts) > 2 else "",
                            "copy": "", "hashtags": "", "formato": "", "hora": "",
                        }
                    elif "#️⃣" in line:
                        current["hashtags"] = line.replace("#️⃣ *Hashtags:*", "").strip()
                    elif "🎬" in line:
                        current["formato"] = line.replace("🎬 *Formato:*", "").strip()
                    elif "⏰" in line:
                        current["hora"] = line.replace("⏰ *Hora recomendada:*", "").strip()

                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerows(csv_rows)
                st.download_button(
                    "📊 Descargar en CSV (para Notion/Sheets)",
                    data=output.getvalue().encode("utf-8"),
                    file_name=f"calendario_{st.session_state.ce_nombre.replace(' ', '_')}_{ce_mes}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            st.info(
                "**Tip:** Importa el CSV en Google Sheets o Notion para gestionar el calendario "
                "con tu equipo y añadir el estado de cada post (Borrador / Programado / Publicado).",
                icon="💡",
            )

        with tabs[2]:
            st.markdown(f"""
## 📅 Content Engine — Guía de venta

### Qué entrega este servicio
Un calendario editorial de 30 días con el copy íntegro de cada post, listo para publicar.
El cliente no tiene que escribir nada — solo revisar, ajustar detalles menores y programar.

### Por qué un negocio local lo necesita
- El **dueño medio de una pyme dedica 4-6 horas al mes** solo a pensar qué publicar
- Los negocios que publican de forma **consistente** (3-5x/semana) generan un **40-80% más de visitas** a su ficha de Google
- El **64% de los consumidores** sigue a negocios locales en redes antes de visitarlos por primera vez
- Sin estrategia editorial: contenido genérico, rachas de inactividad y seguidores que no convierten

### Argumentario para {st.session_state.ce_nombre}
*"¿Cuántas horas lleva tu equipo pensando qué publicar cada semana?
Con Content Engine, recibes el mes entero de contenido de una vez — posts, hashtags, horarios,
ideas de Reels — todo personalizado a tu negocio y listo para copiar y programar.
Tú solo decides si lo publicas o ajustas algo. Nada más."*

### Flujo de trabajo recomendado para el cliente
1. **Día 1 del mes** → genera el calendario en 60 segundos con este módulo
2. **Día 2-3** → el cliente revisa, aprueba y ajusta detalles menores
3. **Día 3-4** → se programa todo en Meta Business Suite, Buffer o Later
4. **Fin de mes** → informe de rendimiento + generación del siguiente mes

### Precio sugerido
- **Por calendario mensual:** 197-297€/mes
- **Retainer trimestral (descuento):** 497-697€/trimestre
- **Setup + primer mes + formación:** 397€ precio de entrada
""")


# ─── Generador de PDFs ────────────────────────────────────────────────────────
elif page == "📄 Generador de PDFs":
    import importlib

    st.subheader("📄 Generador de PDFs comerciales")
    st.caption("Genera y descarga los documentos de MerakIA al momento, siempre con la versión actualizada.")

    docs = {
        "📦 Catálogo de Servicios 2026": {
            "modulo": "generar_catalogo",
            "archivo": "MerakIA_Catalogo_Servicios_2026.pdf",
            "desc": "Los 12 servicios de la agencia con descripción, dolor que resuelven, ROI, "
                    "entregables y tabla comparativa. El documento que enseñas a un cliente para "
                    "que vea todo lo que puedes hacer por su negocio.",
        },
        "🎯 Estrategia de Captación y Marketing 2026": {
            "modulo": "generar_estrategia_captacion",
            "archivo": "MerakIA_Estrategia_Captacion_2026.pdf",
            "desc": "Plan completo para conseguir tus primeros clientes: posicionamiento, cliente "
                    "ideal, plan de 90 días, canales, proceso de venta, scripts, precios y KPIs. "
                    "Tu manual interno de crecimiento — con tu foto en portada.",
        },
    }

    for titulo, info in docs.items():
        with st.container(border=True):
            st.markdown(f"### {titulo}")
            st.write(info["desc"])
            col1, col2 = st.columns([1, 2])
            with col1:
                if st.button("🔄 Generar ahora", key=f"gen_{info['modulo']}", use_container_width=True):
                    with st.spinner("Generando PDF..."):
                        try:
                            mod = importlib.import_module(info["modulo"])
                            importlib.reload(mod)  # asegura la versión más reciente
                            pdf_bytes = mod.generar_pdf_bytes()
                            st.session_state[f"pdf_{info['modulo']}"] = pdf_bytes
                            st.success(f"✅ Generado ({len(pdf_bytes)//1024} KB)")
                        except Exception as e:
                            st.error(f"Error al generar: {e}")
            with col2:
                if f"pdf_{info['modulo']}" in st.session_state:
                    st.download_button(
                        "⬇️ Descargar PDF",
                        data=st.session_state[f"pdf_{info['modulo']}"],
                        file_name=info["archivo"],
                        mime="application/pdf",
                        key=f"dl_{info['modulo']}",
                        use_container_width=True,
                    )

    st.divider()
    st.info(
        "💡 Estos PDFs se generan desde el código, así que siempre reflejan los servicios "
        "y precios actuales. Si añadimos un servicio nuevo a la plataforma, el catálogo se "
        "actualiza solo al regenerarlo.",
        icon="ℹ️",
    )


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


# ─── VideoStudio ──────────────────────────────────────────────────────────────
elif page == "🎬 VideoStudio":
    st.subheader("🎬 VideoStudio — Agentes de Vídeo")
    st.caption("Ejecuta cada agente por separado o usa el Pipeline completo.")

    tab_script, tab_voice, tab_media, tab_edit, tab_sub, tab_pub = st.tabs(
        ["📝 Guión", "🎙️ Voz", "🎞️ Media", "✂️ Edición", "💬 Subtítulos", "📤 Publicar"]
    )

    # ── Tab: Guión ────────────────────────────────────────────────────────────
    with tab_script:
        st.markdown("**ScriptAgent** — genera guiones optimizados para YouTube y TikTok")
        col1, col2, col3 = st.columns(3)
        with col1:
            topic = st.text_input("Tema del vídeo", placeholder="Los 5 hacks de sueño de los CEOs")
            niche = st.selectbox("Nicho", ["biohacking", "finanzas", "motivacion", "tecnologia", "curiosidades"])
        with col2:
            duration = st.slider("Duración (min)", 1, 20, 10)
            platform = st.selectbox("Plataforma", ["both", "youtube", "tiktok"])
        with col3:
            language = st.selectbox("Idioma", ["es", "en"])
            show_narration = st.checkbox("Ver narración completa")

        # ── Documentos de referencia (PDF) ───────────────────────────────────
        st.markdown("##### 📄 Documentos de referencia")
        st.caption("Sube estudios, papers o artículos en PDF. La IA los usará como fuente para dar datos rigurosos y contrastados en el guión.")

        pdf_uploads = st.file_uploader(
            "Arrastra aquí los PDFs (puedes subir varios)",
            type=["pdf"],
            accept_multiple_files=True,
            key="script_pdfs",
            help="El texto extraído se pasará a la IA junto con el tema. Recomendado para biohacking, finanzas o cualquier nicho donde la precisión importa.",
        )

        # Extrae y combina texto de todos los PDFs subidos
        if pdf_uploads:
            from pypdf import PdfReader
            import io as _io
            pdf_texts = []
            for pf in pdf_uploads:
                try:
                    reader = PdfReader(_io.BytesIO(pf.read()))
                    text = "\n".join(p.extract_text() or "" for p in reader.pages).strip()
                    if text:
                        pdf_texts.append(f"[{pf.name}]\n{text}")
                except Exception as e:
                    st.warning(f"No se pudo leer {pf.name}: {e}")
            combined_pdf_text = "\n\n---\n\n".join(pdf_texts)[:8000]
            st.session_state["brief_pdf_text"] = combined_pdf_text

            total_chars = len(combined_pdf_text)
            st.success(f"✅ {len(pdf_texts)} PDF(s) cargado(s) — {total_chars:,} caracteres de referencia")
            with st.expander("👁️ Vista previa del contenido extraído"):
                st.text(combined_pdf_text[:1500] + ("…" if total_chars > 1500 else ""))
        elif "brief_pdf_text" in st.session_state and st.session_state["brief_pdf_text"]:
            st.info(f"PDF cargado en sesión: {len(st.session_state['brief_pdf_text']):,} chars. Sube nuevos PDFs para reemplazarlo.")

        # ── Briefing adicional ────────────────────────────────────────────────
        with st.expander("📋 Directrices adicionales — puntos clave, tono y pistas visuales", expanded=False):
            st.caption("Opcional. Complementa los PDFs con instrucciones específicas para la IA.")

            brief_key_points_raw = st.text_area(
                "Puntos clave a incluir (uno por línea)",
                placeholder="15-20 min de sol por la mañana es suficiente\nEl sol regula el cortisol y la melatonina\nEstudio Harvard 2023: 7% menos riesgo de depresión con exposición diaria",
                height=100,
                key="script_key_points",
            )

            brief_reference_raw = st.text_area(
                "Texto adicional de referencia (complementa los PDFs)",
                placeholder="Pega aquí cualquier texto, cita o dato que quieras añadir y que no esté en los PDFs...",
                height=80,
                key="script_reference",
            )

            brief_cues_raw = st.text_area(
                "Pistas visuales (formato: tema → descripción clip Pexels)",
                placeholder="Warren Buffett → stock market charts warren buffett\nvitamina D → morning sunlight outdoor person",
                height=70,
                key="script_visual_cues",
            )

            brief_avoid_raw = st.text_input(
                "Evitar (temas separados por coma)",
                placeholder="miedo al cáncer, quemaduras solares, bronceado artificial",
                key="script_avoid",
            )

        def _build_brief_from_ui():
            b = {}
            kp = [l.strip() for l in brief_key_points_raw.splitlines() if l.strip()]
            if kp:
                b["key_points"] = kp
            # Combina texto de PDFs + texto manual
            pdf_ref = st.session_state.get("brief_pdf_text", "")
            manual_ref = brief_reference_raw.strip()
            combined_ref = "\n\n".join(filter(None, [pdf_ref, manual_ref]))
            if combined_ref:
                b["reference_text"] = combined_ref[:8000]
            if brief_cues_raw.strip():
                cues = {}
                for line in brief_cues_raw.splitlines():
                    if "→" in line:
                        parts = line.split("→", 1)
                        cues[parts[0].strip()] = parts[1].strip()
                if cues:
                    b["visual_cues"] = cues
                    st.session_state["brief_visual_cues"] = cues
            if brief_avoid_raw.strip():
                b["avoid"] = [a.strip() for a in brief_avoid_raw.split(",") if a.strip()]
            return b if b else None

        if st.button("📝 Generar guión", type="primary", disabled=not topic.strip(), key="btn_script"):
            from agents.specialists.video.script_agent import ScriptAgent
            import json

            brief = _build_brief_from_ui()
            if brief:
                n_kp = len(brief.get("key_points", []))
                n_cues = len(brief.get("visual_cues", {}))
                st.toast(f"Brief activo: {n_kp} puntos · {n_cues} visual cues", icon="📋")

            with st.spinner("Generando guión con IA..."):
                vs = ScriptAgent().run(topic=topic, niche=niche,
                                      duration_minutes=duration, platform=platform, language=language,
                                      brief=brief)

            st.success(f"✅ {vs.youtube_title}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Duración", f"{int(vs.total_duration_seconds//60)}m {int(vs.total_duration_seconds%60)}s")
            c2.metric("Secciones", len(vs.sections))
            c3.metric("CPM estimado", vs.estimated_cpm_range)

            st.divider()
            st.markdown(f"**Thumbnail:** {vs.thumbnail_concept}")
            st.markdown(f"**TikTok caption:** {vs.tiktok_caption}")
            st.markdown(f"**Tags:** {', '.join(vs.youtube_tags[:10])}...")

            # Tabla de secciones
            import pandas as pd
            rows = [{"#": s.section_id, "Sección": s.title,
                     "Duración": f"{int(s.duration_seconds//60)}m{int(s.duration_seconds%60):02d}s",
                     "Keywords": ", ".join(s.visual_keywords[:3])} for s in vs.sections]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            if show_narration:
                st.text_area("Narración completa", vs.full_narration(), height=400)

            # Guardar y descargar
            script_dict = vs.to_dict()
            script_json = json.dumps(script_dict, ensure_ascii=False, indent=2)
            st.session_state["script_data"] = script_dict
            st.session_state["script_json"] = script_json
            st.download_button("⬇️ Descargar guión JSON", script_json,
                               file_name=f"guion_{niche}.json", mime="application/json")

    # ── Tab: Voz ──────────────────────────────────────────────────────────────
    with tab_voice:
        st.markdown("**VoiceAgent** — sintetiza el guión en audio MP3 con timestamps")
        st.info("Carga un guión JSON generado por ScriptAgent o usa el de la sesión actual.", icon="ℹ️")

        uploaded_script = st.file_uploader("Guión JSON (opcional si ya generaste uno arriba)", type="json", key="vu_script")
        tts_provider = st.selectbox("Proveedor TTS", ["edge (gratis)", "elevenlabs (premium)"])
        output_audio_dir = st.text_input("Carpeta de salida", value="outputs/audio/video")

        if st.button("🎙️ Sintetizar audio", type="primary", key="btn_voice"):
            import json, tempfile
            from pathlib import Path
            from agents.specialists.video.voice_agent import VoiceAgent

            if uploaded_script:
                script_data = json.load(uploaded_script)
            elif "script_data" in st.session_state:
                script_data = st.session_state["script_data"]
            else:
                st.error("Primero genera un guión en la pestaña 'Guión'.")
                st.stop()

            provider = "edge" if "edge" in tts_provider else "elevenlabs"
            with st.spinner("Sintetizando audio... (puede tardar 1-2 min)"):
                vo = VoiceAgent().run(script_data=script_data, output_dir=output_audio_dir,
                                     language=script_data.get("language", "es"), provider=provider)

            st.success(f"✅ {vo.voice_name} · {int(vo.total_duration_seconds//60)}m {int(vo.total_duration_seconds%60)}s")
            st.markdown(f"**Audio completo:** `{vo.full_audio_file}`")

            # Guardar en session
            voice_dict = vo.to_dict()
            st.session_state["voice_data"] = voice_dict
            voice_json = json.dumps(voice_dict, ensure_ascii=False, indent=2)
            st.download_button("⬇️ Descargar voice_output.json", voice_json,
                               file_name="voice_output.json", mime="application/json")

    # ── Tab: Media ────────────────────────────────────────────────────────────
    with tab_media:
        st.markdown("**MediaAgent** — descarga clips de Pexels por sección")
        col1, col2 = st.columns(2)
        with col1:
            orientation = st.selectbox("Orientación", ["portrait (9:16)", "landscape (16:9)"])
            clips_per_section = st.slider("Clips por sección", 2, 8, 4)
        with col2:
            output_media_dir = st.text_input("Carpeta de salida", value="outputs/media/video", key="media_out")

        if st.button("🎞️ Descargar clips", type="primary", key="btn_media"):
            import json
            from agents.specialists.video.media_agent import MediaAgent

            script_data = st.session_state.get("script_data")
            voice_data  = st.session_state.get("voice_data")
            if not script_data or not voice_data:
                st.error("Necesitas generar el guión y el audio primero.")
                st.stop()

            orient = "portrait" if "portrait" in orientation else "landscape"
            visual_cues = st.session_state.get("brief_visual_cues")
            if visual_cues:
                st.info(f"Aplicando {len(visual_cues)} pistas visuales del brief", icon="📋")
            with st.spinner("Buscando y descargando clips de Pexels..."):
                mo = MediaAgent().run(script_data=script_data, voice_data=voice_data,
                                     output_dir=output_media_dir, orientation=orient,
                                     clips_per_section=clips_per_section,
                                     visual_cues=visual_cues)

            total_clips = sum(len(s.clips) for s in mo.sections)
            st.success(f"✅ {total_clips} clips descargados en {len(mo.sections)} secciones")

            media_dict = mo.to_dict()
            st.session_state["media_data"] = media_dict
            st.download_button("⬇️ Descargar media_output.json",
                               json.dumps(media_dict, ensure_ascii=False, indent=2),
                               file_name="media_output.json", mime="application/json")

    # ── Tab: Edición ──────────────────────────────────────────────────────────
    with tab_edit:
        st.markdown("**EditorAgent** — ensambla clips + narración + BGM en el MP4 final")
        col1, col2 = st.columns(2)
        with col1:
            output_final_dir = st.text_input("Carpeta de salida", value="outputs/final/video", key="edit_out")
        with col2:
            bgm_vol = st.slider("Volumen BGM", 0.0, 0.3, 0.08, step=0.01)

        if st.button("✂️ Ensamblar vídeo", type="primary", key="btn_edit"):
            from agents.specialists.video.editor_agent import EditorAgent

            script_data = st.session_state.get("script_data")
            voice_data  = st.session_state.get("voice_data")
            media_data  = st.session_state.get("media_data")
            if not all([script_data, voice_data, media_data]):
                st.error("Completa guión, audio y media primero.")
                st.stop()

            with st.spinner("Ensamblando vídeo... puede tardar varios minutos"):
                eo = EditorAgent().run(script_data=script_data, voice_data=voice_data,
                                      media_data=media_data, output_dir=output_final_dir,
                                      bgm_volume=bgm_vol)

            mins, secs = divmod(int(eo.duration_seconds), 60)
            st.success(f"✅ {eo.width}×{eo.height} · {mins}m {secs:02d}s · {eo.file_size_mb} MB")
            st.markdown(f"**Ruta:** `{eo.video_file}`")
            st.session_state["editor_output"] = eo.to_dict()
            st.session_state["final_video"] = eo.video_file

    # ── Tab: Subtítulos ───────────────────────────────────────────────────────
    with tab_sub:
        st.markdown("**SubtitleAgent** — transcribe con Whisper y quema karaoke")
        col1, col2 = st.columns(2)
        with col1:
            whisper_model = st.selectbox("Modelo Whisper", ["tiny", "base", "small", "medium"], index=2)
        with col2:
            words_per_line = st.slider("Palabras por línea", 2, 6, 4)

        if st.button("💬 Quemar subtítulos", type="primary", key="btn_sub"):
            from agents.specialists.video.subtitle_agent import SubtitleAgent
            from pathlib import Path

            eo = st.session_state.get("editor_output")
            vo = st.session_state.get("voice_data")
            if not eo or not vo:
                st.error("Ensambla el vídeo primero.")
                st.stop()

            video_file = eo["video_file"]
            audio_file = vo["full_audio_file"]
            out_dir    = str(Path(video_file).parent)

            st.info(f"Modelo: {whisper_model} — puede tardar 10-20 min en CPU", icon="⏱️")
            with st.spinner("Transcribiendo y quemando subtítulos..."):
                so = SubtitleAgent(whisper_model=whisper_model).run(
                    video_file=video_file, audio_file=audio_file,
                    output_dir=out_dir, words_per_line=words_per_line,
                )

            mins, secs = divmod(int(so.duration_seconds), 60)
            st.success(f"✅ {so.total_words} palabras · {mins}m {secs:02d}s")
            st.markdown(f"**Video final:** `{so.video_with_subs}`")
            st.session_state["final_video"] = so.video_with_subs

    # ── Tab: Publicar ─────────────────────────────────────────────────────────
    with tab_pub:
        st.markdown("**PublishAgent** — sube a YouTube y/o TikTok")

        platforms = st.multiselect("Plataformas", ["youtube", "tiktok"], default=["youtube"])

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**YouTube**")
            yt_secrets = st.text_input("Ruta a client_secrets.json", placeholder="client_secrets.json")
            yt_privacy  = st.selectbox("Privacidad", ["private", "unlisted", "public"])
        with col2:
            st.markdown("**TikTok**")
            tt_token   = st.text_input("TikTok access_token", type="password")
            tt_privacy = st.selectbox("Privacidad TikTok", ["SELF_ONLY", "MUTUAL_FOLLOW_FRIENDS", "PUBLIC_TO_EVERYONE"])

        final_video = st.session_state.get("final_video", "")
        script_data  = st.session_state.get("script_data", {})

        if final_video:
            st.info(f"Video listo: `{final_video}`", icon="🎬")
        else:
            st.warning("Completa el pipeline primero (Guión → Voz → Media → Edición → Subtítulos)", icon="⚠️")

        if st.button("📤 Subir vídeo", type="primary",
                     disabled=not final_video or not platforms, key="btn_pub"):
            from agents.specialists.video.publish_agent import PublishAgent
            from pathlib import Path

            agent = PublishAgent(
                youtube_secrets_file=yt_secrets,
                tiktok_access_token=tt_token,
            )
            with st.spinner("Subiendo vídeo..."):
                result = agent.run(
                    video_file=final_video,
                    script_data=script_data,
                    platforms=platforms,
                    youtube_privacy=yt_privacy,
                    tiktok_privacy=tt_privacy,
                )

            for r in result.results:
                if r.success:
                    st.success(f"✅ {r.platform.upper()}: [{r.url}]({r.url})")
                else:
                    st.error(f"❌ {r.platform.upper()}: {r.error}")


# ─── Pipeline Completo ────────────────────────────────────────────────────────
elif page == "🚀 Pipeline Completo":
    st.subheader("🚀 Pipeline Completo — Tema → Vídeo listo")
    st.caption("Ejecuta todos los agentes en secuencia: Guión → Voz → Media → Edición → Subtítulos → (Publicar)")

    col1, col2, col3 = st.columns(3)
    with col1:
        topic    = st.text_input("Tema del vídeo", placeholder="Los 5 hacks de sueño de los CEOs", key="pl_topic")
        niche    = st.selectbox("Nicho", ["biohacking", "finanzas", "motivacion", "tecnologia", "curiosidades"], key="pl_niche")
        duration = st.slider("Duración (min)", 1, 20, 10, key="pl_dur")
    with col2:
        orientation = st.selectbox("Orientación", ["portrait (TikTok 9:16)", "landscape (YouTube 16:9)"], key="pl_orient")
        tts_prov    = st.selectbox("TTS", ["edge (gratis)", "elevenlabs (premium)"], key="pl_tts")
        whisper_m   = st.selectbox("Whisper", ["tiny", "base", "small", "medium"], index=2, key="pl_whisper")
    with col3:
        skip_sub    = st.checkbox("Omitir subtítulos (más rápido)", key="pl_nosub")
        bgm_v       = st.slider("Volumen BGM", 0.0, 0.3, 0.08, step=0.01, key="pl_bgm")
        output_slug = st.text_input("Nombre carpeta", placeholder="mi_video", key="pl_slug")

    # ── Brief creativo ────────────────────────────────────────────────────────
    # ── Documentos de referencia (PDF) ───────────────────────────────────────
    st.markdown("##### 📄 Documentos de referencia")
    st.caption("Sube estudios, papers o artículos en PDF. La IA los usará como fuente para dar datos rigurosos y contrastados.")

    pl_pdf_uploads = st.file_uploader(
        "Arrastra aquí los PDFs (puedes subir varios)",
        type=["pdf"],
        accept_multiple_files=True,
        key="pl_pdfs",
        help="El texto extraído se combina y se pasa a la IA al generar el guión.",
    )

    if pl_pdf_uploads:
        from pypdf import PdfReader
        import io as _io
        pl_pdf_parts = []
        for pf in pl_pdf_uploads:
            try:
                reader = PdfReader(_io.BytesIO(pf.read()))
                text = "\n".join(p.extract_text() or "" for p in reader.pages).strip()
                if text:
                    pl_pdf_parts.append(f"[{pf.name}]\n{text}")
            except Exception as e:
                st.warning(f"No se pudo leer {pf.name}: {e}")
        pl_combined_pdf = "\n\n---\n\n".join(pl_pdf_parts)[:8000]
        st.session_state["pl_brief_pdf_text"] = pl_combined_pdf
        st.success(f"✅ {len(pl_pdf_parts)} PDF(s) — {len(pl_combined_pdf):,} caracteres de referencia")
        with st.expander("👁️ Vista previa del contenido extraído"):
            st.text(pl_combined_pdf[:1500] + ("…" if len(pl_combined_pdf) > 1500 else ""))
    elif st.session_state.get("pl_brief_pdf_text"):
        st.info(f"PDF en sesión: {len(st.session_state['pl_brief_pdf_text']):,} chars")

    with st.expander("📋 Directrices adicionales — puntos clave, tono y pistas visuales", expanded=False):
        st.caption("Opcional. Complementa los PDFs con instrucciones específicas para la IA.")

        pl_key_points_raw = st.text_area(
            "Puntos clave (uno por línea)",
            placeholder="15 min de sol matutino es suficiente\nRegula el cortisol y la melatonina",
            height=100,
            key="pl_key_points",
        )
        pl_reference_raw = st.text_area(
            "Texto adicional (complementa los PDFs)",
            height=80,
            key="pl_reference",
        )
        pl_cues_raw = st.text_area(
            "Pistas visuales (tema → descripción clip Pexels)",
            placeholder="Warren Buffett → stock market charts warren buffett\nvitamina D → morning sunlight outdoor person",
            height=70,
            key="pl_visual_cues",
        )
        pl_avoid_raw = st.text_input(
            "Evitar (separado por comas)",
            key="pl_avoid",
        )

    st.divider()
    st.markdown("**Publicar al terminar (opcional)**")
    pub_platforms = st.multiselect("Plataformas", ["youtube", "tiktok"], key="pl_platforms")
    col4, col5 = st.columns(2)
    with col4:
        pl_yt_secrets = st.text_input("client_secrets.json", key="pl_yt_sec")
        pl_yt_privacy = st.selectbox("Privacidad YT", ["private", "unlisted", "public"], key="pl_yt_priv")
    with col5:
        pl_tt_token   = st.text_input("TikTok token", type="password", key="pl_tt")

    st.divider()

    if st.button("🚀 Iniciar pipeline completo", type="primary",
                 disabled=not topic.strip(), key="btn_pipeline"):
        import json
        from pathlib import Path
        from agents.specialists.video.script_agent   import ScriptAgent
        from agents.specialists.video.voice_agent    import VoiceAgent
        from agents.specialists.video.media_agent    import MediaAgent
        from agents.specialists.video.editor_agent   import EditorAgent
        from agents.specialists.video.subtitle_agent import SubtitleAgent

        slug = output_slug.strip() or topic[:30].lower().replace(" ", "_")
        slug = "".join(c for c in slug if c.isalnum() or c == "_")
        orient = "portrait" if "portrait" in orientation else "landscape"
        provider = "edge" if "edge" in tts_prov else "elevenlabs"
        base = Path("outputs")

        # Construir brief desde UI del pipeline
        _pl_brief = {}
        _pl_kp = [l.strip() for l in pl_key_points_raw.splitlines() if l.strip()]
        if _pl_kp:
            _pl_brief["key_points"] = _pl_kp
        _pl_pdf_ref = st.session_state.get("pl_brief_pdf_text", "")
        _pl_manual_ref = pl_reference_raw.strip()
        _pl_ref = "\n\n".join(filter(None, [_pl_pdf_ref, _pl_manual_ref]))
        if _pl_ref:
            _pl_brief["reference_text"] = _pl_ref[:8000]
        _pl_cues = {}
        for _line in pl_cues_raw.splitlines():
            if "→" in _line:
                _parts = _line.split("→", 1)
                _pl_cues[_parts[0].strip()] = _parts[1].strip()
        if _pl_cues:
            _pl_brief["visual_cues"] = _pl_cues
        if pl_avoid_raw.strip():
            _pl_brief["avoid"] = [a.strip() for a in pl_avoid_raw.split(",") if a.strip()]
        pl_brief = _pl_brief if _pl_brief else None
        pl_visual_cues = _pl_cues if _pl_cues else None

        progress = st.progress(0)
        status   = st.empty()

        # 1. Script
        status.info("📝 Paso 1/5 — Generando guión...")
        progress.progress(5)
        vs = ScriptAgent().run(topic=topic, niche=niche, duration_minutes=duration,
                               platform="both", language="es", brief=pl_brief)
        script_data = vs.to_dict()
        (base / f"{slug}.json").parent.mkdir(parents=True, exist_ok=True)
        with open(base / f"{slug}.json", "w", encoding="utf-8") as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)
        progress.progress(15)
        st.success(f"✅ Guión: {vs.youtube_title[:60]}")

        # 2. Voice
        status.info("🎙️ Paso 2/5 — Sintetizando audio...")
        audio_dir = str(base / "audio" / slug)
        vo = VoiceAgent().run(script_data=script_data, output_dir=audio_dir,
                              language="es", provider=provider)
        voice_data = vo.to_dict()
        with open(Path(audio_dir) / "voice_output.json", "w", encoding="utf-8") as f:
            json.dump(voice_data, f, ensure_ascii=False, indent=2)
        progress.progress(30)
        mins_v = int(vo.total_duration_seconds // 60)
        st.success(f"✅ Audio: {vo.voice_name} · {mins_v}m")

        # 3. Media
        status.info("🎞️ Paso 3/5 — Descargando clips Pexels...")
        media_dir = str(base / "media" / slug)
        mo = MediaAgent().run(script_data=script_data, voice_data=voice_data,
                              output_dir=media_dir, orientation=orient, clips_per_section=4,
                              visual_cues=pl_visual_cues)
        media_data = mo.to_dict()
        with open(Path(media_dir) / "media_output.json", "w", encoding="utf-8") as f:
            json.dump(media_data, f, ensure_ascii=False, indent=2)
        total_clips = sum(len(s.clips) for s in mo.sections)
        progress.progress(50)
        st.success(f"✅ Media: {total_clips} clips descargados")

        # 4. Editor
        status.info("✂️ Paso 4/5 — Ensamblando vídeo...")
        final_dir = str(base / "final" / slug)
        eo = EditorAgent().run(script_data=script_data, voice_data=voice_data,
                               media_data=media_data, output_dir=final_dir,
                               orientation=orient, bgm_volume=bgm_v)
        mins_e, secs_e = divmod(int(eo.duration_seconds), 60)
        progress.progress(70)
        st.success(f"✅ Vídeo: {eo.width}×{eo.height} · {mins_e}m {secs_e:02d}s · {eo.file_size_mb} MB")

        # 5. Subtítulos
        final_video = eo.video_file
        if not skip_sub:
            status.info(f"💬 Paso 5/5 — Subtítulos Whisper {whisper_m} (puede tardar 10-20 min)...")
            so = SubtitleAgent(whisper_model=whisper_m).run(
                video_file=eo.video_file,
                audio_file=vo.full_audio_file,
                output_dir=final_dir,
            )
            sub_mb = round(Path(so.video_with_subs).stat().st_size / 1_048_576, 1) if Path(so.video_with_subs).exists() else 0
            progress.progress(90)
            st.success(f"✅ Subtítulos: {so.total_words} palabras · {sub_mb} MB")
            final_video = so.video_with_subs

        # Publicar
        if pub_platforms:
            from agents.specialists.video.publish_agent import PublishAgent
            status.info("📤 Publicando...")
            pub = PublishAgent(youtube_secrets_file=pl_yt_secrets, tiktok_access_token=pl_tt_token)
            pr  = pub.run(video_file=final_video, script_data=script_data,
                          platforms=pub_platforms, youtube_privacy=pl_yt_privacy)
            for r in pr.results:
                if r.success:
                    st.success(f"✅ {r.platform.upper()}: {r.url}")
                else:
                    st.error(f"❌ {r.platform.upper()}: {r.error}")

        progress.progress(100)
        status.empty()
        st.balloons()
        st.success(f"🎉 Pipeline completado — {final_video}")


# ─── ProspectorIA ─────────────────────────────────────────────────────────────
elif page == "🎯 ProspectorIA":
    import pandas as pd
    from agents.specialists.prospector import ProspectorAgent, CRM, ESTADOS, ESTADO_COLORS
    from agents.specialists.prospector.models import ProspectorResult
    from config.settings import settings

    # ── CSS ───────────────────────────────────────────────────────────────────
    st.markdown("""<style>
    .step-header {
        display:flex; align-items:center; gap:10px;
        padding:10px 14px; border-radius:10px; margin-bottom:6px;
    }
    .step-active  { background:rgba(124,58,237,0.12); border:1px solid rgba(124,58,237,0.4); }
    .step-done    { background:rgba(16,185,129,0.10); border:1px solid rgba(16,185,129,0.35); }
    .step-locked  { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); opacity:.5; }
    .step-num     { width:28px;height:28px;border-radius:50%;display:flex;align-items:center;
                    justify-content:center;font-weight:800;font-size:13px;flex-shrink:0; }
    .num-active   { background:#7C3AED; color:#fff; }
    .num-done     { background:#10b981; color:#fff; }
    .num-locked   { background:rgba(255,255,255,0.1); color:#64748b; }
    .step-title   { font-weight:700; font-size:15px; }
    .chip { display:inline-block;padding:2px 9px;border-radius:12px;font-size:11px;font-weight:700;margin:2px; }
    .chip-alta  { background:rgba(239,68,68,.15);color:#ef4444;border:1px solid #ef4444; }
    .chip-media { background:rgba(245,158,11,.15);color:#f59e0b;border:1px solid #f59e0b; }
    .chip-baja  { background:rgba(16,185,129,.15);color:#10b981;border:1px solid #10b981; }
    </style>""", unsafe_allow_html=True)

    # ── Session state ─────────────────────────────────────────────────────────
    for k, v in [
        ("ps_paso", 1),
        ("ps_tipo", ""), ("ps_ciudad", ""), ("ps_agencia", "MerakIA"),
        ("ps_negocios", []), ("ps_resultados", []), ("ps_sel_idx", 0),
    ]:
        if k not in st.session_state:
            st.session_state[k] = v

    # Normalizar resultados antiguos en sesión: si se analizaron antes de añadir
    # campos nuevos (competitive, tech_stack, etc.), rellenarlos para que la UI no
    # falle con AttributeError. Lista de campos a mano (no depende de que el módulo
    # models esté recargado, que es justo lo que causaba el fallo).
    _CAMPOS_NUEVOS = {
        "scorecard": None, "win_probability": None,
        "tech_stack": None, "pagespeed": None, "competitive": None, "automation": None, "gbp_audit": None,
        "ticket_promedio": None, "leads_mensuales": None, "conversion_actual": None,
        "roi_data": None, "perdida_total_mes": None,
        "servicios_recomendados": list, "perdidas": list, "paquetes": list,
        "secuencia_seguimiento": list,
        "propuesta_texto": None, "demo_prompt": None, "landing_prompt": None,
        "presentacion_prompt": None,
    }
    for _r in st.session_state.get("ps_resultados", []):
        for _name, _default in _CAMPOS_NUEVOS.items():
            if not hasattr(_r, _name):
                setattr(_r, _name, _default() if _default is list else _default)

    paso = st.session_state.ps_paso

    # ── Barra de progreso superior ────────────────────────────────────────────
    PASOS = [
        (1, "Nicho & Ciudad"),
        (2, "Negocios"),
        (3, "Análisis"),
        (4, "Dolores"),
        (5, "Pricing & ROI"),
        (6, "Arsenal de venta"),
        (7, "CRM"),
    ]

    st.markdown('<div class="merakia-header">🎯 ProspectorIA</div>', unsafe_allow_html=True)
    st.caption("Plataforma de venta: nicho → análisis → dolor → precio → propuesta → cierre")
    st.divider()

    # Progress chips
    cols_p = st.columns(len(PASOS))
    for i, (n, label) in enumerate(PASOS):
        with cols_p[i]:
            if n < paso:
                st.markdown(f'<div style="text-align:center"><span class="chip chip-baja">✓ {n}</span><br><small style="color:#64748b">{label}</small></div>', unsafe_allow_html=True)
            elif n == paso:
                st.markdown(f'<div style="text-align:center"><span class="chip chip-alta">● {n}</span><br><small style="color:#fff;font-weight:600">{label}</small></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="text-align:center"><span class="chip" style="background:rgba(255,255,255,.05);color:#475569;border:1px solid rgba(255,255,255,.1)">{n}</span><br><small style="color:#475569">{label}</small></div>', unsafe_allow_html=True)

    st.divider()

    # ── Configuración (sidebar colapsable) ───────────────────────────────────
    with st.expander("⚙️ Configuración — API Keys y agencia", expanded=(paso == 1)):
        col_cfg1, col_cfg2 = st.columns(2)
        with col_cfg1:
            gkey = st.text_input(
                "Google Places API Key",
                value=settings.google_places_api_key,
                type="password",
                help="console.cloud.google.com — gratis hasta $200/mes",
            )
            if gkey:
                settings.google_places_api_key = gkey
        with col_cfg2:
            agencia_input = st.text_input("Nombre de tu agencia", value=st.session_state.ps_agencia)
            st.session_state.ps_agencia = agencia_input

    # ══════════════════════════════════════════════════════════════════════════
    # PASO 1 — Seleccionar nicho y ciudad  /  o entrar un negocio concreto
    # ══════════════════════════════════════════════════════════════════════════
    if paso >= 1:
        with st.container():
            st.markdown("### 1️⃣ ¿Cómo quieres empezar?")

            tab_nicho, tab_manual = st.tabs(["🔍 Buscar por nicho", "✏️ Negocio específico"])

            # ── Tab A: búsqueda por nicho (flujo original) ──────────────────
            with tab_nicho:
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    NICHOS = [
                        "clínica dental", "clínica estética", "fisioterapia", "veterinaria",
                        "restaurante", "bar", "cafetería", "gimnasio", "peluquería",
                        "inmobiliaria", "taller mecánico", "farmacia", "óptica",
                        "academia de idiomas", "otro",
                    ]
                    tipo_sel = st.selectbox("Tipo de negocio", NICHOS, key="ps_tipo_sel")
                    tipo = st.text_input(
                        "O escribe el nicho libre",
                        value=tipo_sel if tipo_sel != "otro" else "",
                        placeholder="Ej: clínica de podología",
                        key="ps_tipo_libre",
                    )
                    tipo = tipo.strip() or tipo_sel

                with col2:
                    ciudad = st.text_input(
                        "Ciudad o localidad",
                        placeholder="Barcelona, Vilanova i la Geltrú, Madrid...",
                        key="ps_ciudad_input",
                    )

                with col3:
                    limite = st.number_input("Resultados", 5, 50, 15, 5, key="ps_limite")

                btn_buscar = st.button(
                    "🔍 Buscar negocios →",
                    type="primary",
                    disabled=not (tipo and ciudad),
                    key="ps_btn_buscar",
                )

                if btn_buscar:
                    try:
                        with st.spinner(f"Buscando '{tipo}' en {ciudad}..."):
                            agent = ProspectorAgent(nombre_agencia=st.session_state.ps_agencia)
                            negocios = agent.buscar_negocios(tipo=tipo, ciudad=ciudad, limite=limite)
                        st.session_state.ps_negocios = negocios
                        st.session_state.ps_resultados = []
                        st.session_state.ps_tipo = tipo
                        st.session_state.ps_ciudad = ciudad
                        st.session_state.ps_paso = 2
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ {e}")

            # ── Tab B: negocio específico (entrada manual) ───────────────────
            with tab_manual:
                st.caption("Introduce un negocio concreto. Buscaremos su ficha en Google Places para traer rating y reseñas; si no lo encontramos, usamos los datos que pongas aquí.")

                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    m_nombre = st.text_input(
                        "Nombre del negocio *",
                        placeholder="Ej: Clínica Dental Sorriso",
                        key="ps_m_nombre",
                    )
                    m_ciudad = st.text_input(
                        "Ciudad *",
                        placeholder="Ej: Vilanova i la Geltrú",
                        key="ps_m_ciudad",
                    )
                with col_m2:
                    m_tipo = st.text_input(
                        "Tipo / sector",
                        placeholder="Ej: clínica dental",
                        key="ps_m_tipo",
                    )
                    m_url = st.text_input(
                        "URL de la web (opcional)",
                        placeholder="https://www.clinicasorriso.com",
                        key="ps_m_url",
                    )

                btn_manual = st.button(
                    "🎯 Analizar este negocio →",
                    type="primary",
                    disabled=not (m_nombre and m_ciudad),
                    key="ps_btn_manual",
                )

                if btn_manual:
                    from agents.specialists.prospector.scraper import GooglePlacesScraper
                    from agents.specialists.prospector.models import Business as BizModel
                    import uuid

                    tipo_m = m_tipo.strip() or "negocio local"
                    url_limpia = m_url.strip() or None

                    biz = None
                    # Intentar encontrarlo en Places por nombre + ciudad
                    if settings.google_places_api_key:
                        try:
                            with st.spinner(f"Buscando '{m_nombre}' en Google Places..."):
                                scraper = GooglePlacesScraper(settings.google_places_api_key)
                                candidatos = scraper.buscar_negocios(
                                    tipo=m_nombre, ciudad=m_ciudad, limite=5
                                )
                            # Buscar el que más se parezca al nombre
                            nombre_lower = m_nombre.lower()
                            for c in candidatos:
                                if nombre_lower in c.nombre.lower() or c.nombre.lower() in nombre_lower:
                                    biz = c
                                    break
                            if biz is None and candidatos:
                                biz = candidatos[0]  # el más relevante según Places
                            if biz:
                                # Si el usuario dio URL, tiene prioridad
                                if url_limpia:
                                    biz.web = url_limpia
                                    biz.tiene_web = True
                                biz.tipo = tipo_m
                                st.success(f"✅ Encontrado en Google Places: **{biz.nombre}** · {biz.rating}⭐ · {biz.total_resenas} reseñas")
                        except Exception as e:
                            st.warning(f"No se pudo buscar en Places ({e}). Continuando con datos manuales.")

                    # Si Places no devolvió nada, crear el objeto a mano
                    if biz is None:
                        biz = BizModel(
                            place_id=f"manual_{uuid.uuid4().hex[:8]}",
                            nombre=m_nombre,
                            tipo=tipo_m,
                            ciudad=m_ciudad,
                            direccion=m_ciudad,
                            web=url_limpia,
                            tiene_web=bool(url_limpia),
                        )
                        st.info("No encontrado en Google Places — se analizará solo la web.")

                    # Saltar directamente al análisis (paso 3), sin pasar por el listado
                    st.session_state.ps_negocios = [biz]
                    st.session_state.ps_negocios_analizar = [biz]
                    st.session_state.ps_resultados = []
                    st.session_state.ps_tipo = tipo_m
                    st.session_state.ps_ciudad = m_ciudad
                    st.session_state.ps_paso = 3
                    st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # PASO 2 — Negocios encontrados
    # ══════════════════════════════════════════════════════════════════════════
    if paso >= 2 and st.session_state.ps_negocios:
        st.divider()
        negocios = st.session_state.ps_negocios
        tipo_act = st.session_state.ps_tipo
        ciudad_act = st.session_state.ps_ciudad

        st.markdown(f"### 2️⃣ {len(negocios)} negocios encontrados — *{tipo_act}* en **{ciudad_act}**")
        st.caption("Marca los que quieres analizar (por defecto los 3 primeros) y pulsa el botón.")

        df_neg = pd.DataFrame([{
            "✓": i < 3,
            "#": i + 1,
            "Nombre": n.nombre,
            "Dirección": n.direccion[:55] + "…" if len(n.direccion) > 55 else n.direccion,
            "Rating": f"{n.rating} ⭐" if n.rating else "—",
            "Reseñas": n.total_resenas or 0,
        } for i, n in enumerate(negocios)])

        edited = st.data_editor(
            df_neg,
            use_container_width=True,
            hide_index=True,
            column_config={
                "✓": st.column_config.CheckboxColumn("Analizar", width="small"),
                "#": st.column_config.NumberColumn("#", width="small"),
            },
            disabled=["#", "Nombre", "Dirección", "Rating", "Reseñas"],
            key="ps_neg_editor",
        )

        seleccionados_idx = [i for i, row in edited.iterrows() if row["✓"]]
        n_sel = len(seleccionados_idx)

        col_b1, col_b2 = st.columns([1, 3])
        if col_b1.button("← Nueva búsqueda", key="ps_back1"):
            st.session_state.ps_paso = 1
            st.rerun()

        btn_label = (
            f"📊 Analizar {n_sel} seleccionado{'s' if n_sel != 1 else ''} →"
            if n_sel > 0 else "Selecciona al menos uno"
        )
        if col_b2.button(btn_label, type="primary", key="ps_btn_analizar", disabled=(n_sel == 0)):
            # guardar solo los negocios marcados para el análisis
            st.session_state.ps_negocios_analizar = [negocios[i] for i in seleccionados_idx]
            st.session_state.ps_paso = 3
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # PASO 3 — Análisis masivo (web + reseñas + score)
    # ══════════════════════════════════════════════════════════════════════════
    if paso >= 3:
        st.divider()
        # usar solo los negocios seleccionados en el paso 2 (o todos si no hay selección guardada)
        negocios = st.session_state.get("ps_negocios_analizar") or st.session_state.ps_negocios
        resultados = st.session_state.ps_resultados

        st.markdown("### 3️⃣ Análisis web + reseñas + score de oportunidad")

        if not resultados:
            st.info(
                f"Se analizarán {len(negocios)} negocio{'s' if len(negocios) != 1 else ''}: "
                "web (15 puntos), reseñas Google, velocidad de carga y señales de dolor.",
                icon="🔬",
            )
            if st.button("⚡ Iniciar análisis masivo", type="primary", key="ps_btn_run_analisis"):
                agent = ProspectorAgent(nombre_agencia=st.session_state.ps_agencia)
                pb = st.progress(0)
                st_status = st.empty()
                results_tmp = []
                for i, neg in enumerate(negocios):
                    st_status.markdown(
                        f"🔬 Analizando **{neg.nombre}** ({i+1}/{len(negocios)})…"
                    )
                    pb.progress((i + 1) / len(negocios))
                    try:
                        r = agent.analizar_negocio(neg, generar_outreach=False)
                        results_tmp.append(r)
                    except Exception as e:
                        results_tmp.append(
                            ProspectorResult(business=neg, resumen_oportunidad=f"Error: {e}")
                        )
                # Benchmark de nicho + win probability (necesita todo el lote)
                agent.finalizar_lote(results_tmp)
                # Re-persistir con el percentil y win probability ya calculados
                for r in results_tmp:
                    try:
                        agent.crm.guardar(r)
                    except Exception:
                        pass
                results_tmp.sort(key=lambda r: r.score_oportunidad, reverse=True)
                st.session_state.ps_resultados = results_tmp
                pb.empty()
                st_status.empty()
                st.session_state.ps_paso = 4
                st.rerun()
        else:
            # Ya analizado — ranking por probabilidad de cierre
            def _win(r):
                return (r.win_probability or {}).get("score", 0)
            ranking = sorted(resultados, key=_win, reverse=True)

            NIVEL_WIN_ICO = {"muy alta": "🟢", "alta": "🟢", "media": "🟡", "baja": "🔴"}
            rows_df = []
            for r in ranking:
                b = r.business
                cl = r.web_checklist
                wp = r.win_probability or {}
                sc = r.scorecard or {}
                madurez = sc.get("score_global")
                pct = sc.get("percentil_nicho")
                rows_df.append({
                    "Win %": wp.get("score", 0),
                    "Cierre": NIVEL_WIN_ICO.get(wp.get("nivel", ""), "⚪") + " " + wp.get("nivel", "—").upper(),
                    "Nombre": b.nombre,
                    "Madurez digital": f"{madurez:.0f}/100" if madurez is not None else "—",
                    "vs nicho": f"percentil {pct}" if pct is not None else "—",
                    "Rating": f"{b.rating} ⭐" if b.rating else "—",
                    "Dolor principal": (r.pains[0].descripcion[:55] + "…") if r.pains else "—",
                })
            st.dataframe(
                pd.DataFrame(rows_df), use_container_width=True, hide_index=True,
                column_config={
                    "Win %": st.column_config.ProgressColumn(
                        "Win %", min_value=0, max_value=100, format="%d",
                    ),
                },
            )
            st.caption(
                f"✅ {len(resultados)} negocios analizados, ordenados por **probabilidad de cierre**. "
                "Menor madurez digital + más por detrás de su nicho = más fácil de vender."
            )

            if st.button("← Volver a resultados de búsqueda", key="ps_back3"):
                st.session_state.ps_paso = 2
                st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # PASO 4 — Seleccionar negocio y ver dolores detectados
    # ══════════════════════════════════════════════════════════════════════════
    if paso >= 4 and st.session_state.ps_resultados:
        st.divider()
        resultados = st.session_state.ps_resultados
        st.markdown("### 4️⃣ Selecciona un negocio y examina sus dolores")

        # Selector con score visible
        opciones = [
            f"[{r.score_oportunidad}] {r.business.nombre}"
            for r in resultados
        ]
        sel_label = st.selectbox(
            "Negocio (ordenados de mayor oportunidad a menor)",
            opciones,
            index=st.session_state.ps_sel_idx,
            key="ps_sel_negocio",
        )
        st.session_state.ps_sel_idx = opciones.index(sel_label)
        sel = resultados[st.session_state.ps_sel_idx]
        b = sel.business
        cl = sel.web_checklist
        nivel = cl.oportunidad() if cl else ("alta" if not b.tiene_web else "media")
        COLOR_OPT = {"alta": "🔴", "media": "🟡", "baja": "🟢"}

        # ── Cabecera del negocio ───────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Score oportunidad", f"{sel.score_oportunidad}/100")
        c2.metric("Rating Google", f"{b.rating} ⭐" if b.rating else "—")
        c3.metric("Análisis web", f"{cl.score()}/15" if cl else "Sin web")
        c4.metric("Nivel", COLOR_OPT.get(nivel, "") + " " + nivel.upper())

        info_cols = st.columns(3)
        info_cols[0].markdown(f"📍 {b.direccion}")
        if b.telefono:
            info_cols[1].markdown(f"📞 {b.telefono}")
        if b.web:
            info_cols[2].markdown(f"🌐 [{b.web}]({b.web})")

        if b.nombre_propietario:
            st.success(f"👤 Propietario detectado: **{b.nombre_propietario}** — el email irá personalizado")

        if sel.resumen_oportunidad:
            st.info(f"💡 {sel.resumen_oportunidad}")

        # ── Scorecard de Madurez Digital + Win Probability + Benchmark ──────
        # ── Auditoría Google Business Profile ────────────────────────────────
        gb = sel.gbp_audit if hasattr(sel, "gbp_audit") else None
        if gb:
            st.divider()
            st.markdown("#### 📍 Ficha de Google Business Profile")
            gbp_score = gb.get("completitud", 0)
            gbp_nivel = gb.get("nivel", "")
            color_gbp = "#16a34a" if gbp_score >= 75 else ("#eab308" if gbp_score >= 50 else ("#f97316" if gbp_score >= 25 else "#dc2626"))
            cg1, cg2, cg3, cg4 = st.columns(4)
            cg1.metric("Completitud GBP", f"{gbp_score}/100", delta=gbp_nivel)
            cg2.metric("Fotos", f"{gb.get('num_fotos', 0)}", delta="✅" if gb.get("tiene_fotos") else "❌ Sin fotos")
            cg3.metric("Horario", "✅ Sí" if gb.get("tiene_horario") else "❌ No publicado")
            cg4.metric("Descripción", "✅ Sí" if gb.get("tiene_descripcion") else "❌ Falta")
            if gb.get("senales_falta"):
                with st.expander(f"⚠️ {len(gb['senales_falta'])} punto(s) de mejora en Google"):
                    for s in gb["senales_falta"]:
                        st.markdown(f"- {s}")
            if gb.get("senales_ok"):
                with st.expander(f"✅ {len(gb['senales_ok'])} punto(s) bien cubiertos"):
                    for s in gb["senales_ok"]:
                        st.markdown(f"- {s}")
            if gb.get("categoria"):
                st.caption(f"Categoría Google: **{gb['categoria']}** · Maps: {gb.get('maps_uri', '—')}")
            st.markdown(f"<small style='color:#64748b'>{gb.get('oportunidad','')}</small>", unsafe_allow_html=True)

        # ── Sistemas autónomos / IA (el sello de MerakIA — lo primero) ─────
        au = sel.automation or {}
        if au:
            st.divider()
            st.markdown("#### 🤖 Sistemas autónomos / IA")
            es_auto = au.get("es_autonomo")
            nivel_a = au.get("nivel", "ninguno")
            if not es_auto:
                st.error(
                    f"**NO tiene ningún sistema autónomo** (nivel: {nivel_a}). "
                    "🎯 Oportunidad estrella para MerakIA: agente IA + chatbot 24/7.",
                    icon="🚨",
                )
            else:
                st.success(
                    f"Ya tiene automatización (nivel: **{nivel_a}**). "
                    "Ángulo: optimizar, integrar canales y añadir IA de seguimiento.",
                    icon="✅",
                )
            ca1, ca2, ca3 = st.columns(3)
            def _si_no(v, etiqueta_si, etiqueta_no):
                return f"✅ {etiqueta_si}" if v else f"❌ {etiqueta_no}"
            ca1.markdown(_si_no(au.get("tiene_chatbot_ia"), "Chatbot/agente IA web", "Sin chatbot IA"))
            ca2.markdown(_si_no(au.get("tiene_whatsapp_automatizado"), "WhatsApp automatizado", "WhatsApp sin automatizar"))
            ca3.markdown(_si_no(au.get("tiene_reservas_24_7"), "Reservas 24/7", "Sin reservas 24/7"))
            if au.get("sistemas_detectados"):
                st.caption("Sistemas detectados: " + " · ".join(f"`{s}`" for s in au["sistemas_detectados"]))
            if au.get("oportunidad"):
                st.markdown(f"<small style='color:#94a3b8'>{au['oportunidad']}</small>", unsafe_allow_html=True)

        sc = sel.scorecard or {}
        wp = sel.win_probability or {}
        if sc:
            st.divider()
            st.markdown("#### 📈 Scorecard de Madurez Digital")

            head1, head2, head3 = st.columns([1, 1, 1])
            mad = sc.get("score_global", 0)
            nivel_mad = sc.get("nivel_global", "—")
            color_mad = "🟢" if mad >= 75 else "🟡" if mad >= 50 else "🟠" if mad >= 25 else "🔴"
            head1.metric("Madurez digital", f"{mad:.0f}/100", help="0 = sin presencia digital, 100 = totalmente optimizado")
            head1.markdown(f"{color_mad} **{nivel_mad.upper()}**")

            pct = sc.get("percentil_nicho")
            media = sc.get("score_medio_nicho")
            n_muestra = sc.get("tamano_muestra_nicho")
            if pct is not None and media is not None:
                por_encima = 100 - pct
                head2.metric(
                    "Posición en su nicho",
                    f"percentil {pct}",
                    delta=f"{mad - media:+.0f} vs media ({media:.0f})",
                    delta_color="normal",
                )
                head2.caption(f"El {por_encima}% de su competencia en {n_muestra} negocios lo hace mejor")

            win = wp.get("score", 0)
            nivel_win = wp.get("nivel", "—")
            color_win = "🟢" if win >= 60 else "🟡" if win >= 40 else "🔴"
            head3.metric("Probabilidad de cierre", f"{win}/100")
            head3.markdown(f"{color_win} **{nivel_win.upper()}**")

            if wp.get("explicacion"):
                st.caption(f"🎯 {wp['explicacion']}")

            # Barras por dimensión
            st.markdown("**Desglose por dimensión** (rojo = oportunidad de venta)")
            dims = sc.get("dimensiones", [])
            dcol1, dcol2 = st.columns(2)
            for idx, d in enumerate(dims):
                target = dcol1 if idx % 2 == 0 else dcol2
                dscore = d.get("score", 0)
                barcolor = "#22c55e" if dscore >= 75 else "#eab308" if dscore >= 50 else "#f97316" if dscore >= 25 else "#ef4444"
                falta = d.get("senales_falta", [])
                tip = (" · ".join(falta[:3])) if falta else "Todo cubierto ✓"
                target.markdown(
                    f"<div style='margin-bottom:.5rem'>"
                    f"<div style='display:flex;justify-content:space-between;font-size:.85rem'>"
                    f"<span>{d.get('icono','')} {d.get('nombre','')}</span>"
                    f"<span style='color:{barcolor};font-weight:600'>{dscore:.0f}</span></div>"
                    f"<div style='background:rgba(255,255,255,.08);border-radius:4px;height:7px;overflow:hidden'>"
                    f"<div style='width:{dscore}%;background:{barcolor};height:7px'></div></div>"
                    f"<div style='font-size:.72rem;color:#94a3b8;margin-top:2px'>{tip}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        # ── Battle Card competitivo (vs su nicho real) ─────────────────────
        comp = sel.competitive
        if comp:
            st.divider()
            st.markdown("#### ⚔️ Análisis competitivo — vs su nicho real")
            if comp.get("es_lider"):
                st.success(
                    f"🏆 **{b.nombre} lidera su nicho** "
                    f"(posición {comp['posicion']}/{comp['total']}, media del nicho {comp['media_nicho']:.0f}). "
                    "Argumento: vender mejora marginal y defensa de su ventaja."
                )
            else:
                st.markdown(
                    f"Posición **{comp['posicion']}/{comp['total']}** en madurez digital · "
                    f"líder: **{comp['lider_nombre']}** ({comp['lider_score']:.0f}/100) · "
                    f"media del nicho: {comp['media_nicho']:.0f}/100"
                )
                if comp.get("battle_card"):
                    st.markdown("**🗡️ Battle card — lo que la competencia tiene y él no:**")
                    for linea in comp["battle_card"]:
                        st.markdown(f"- {linea}")
            if comp.get("ventajas"):
                st.caption("✅ Ventajas a defender: " + " · ".join(comp["ventajas"]))

        # ── Datos duros: Tech stack + PageSpeed real ───────────────────────
        st.divider()
        st.markdown("#### 🔬 Datos duros")
        dd1, dd2 = st.columns(2)

        with dd1:
            st.markdown("**🧩 Stack tecnológico detectado**")
            tech = sel.tech_stack
            if not b.tiene_web:
                st.caption("Sin web — no hay stack que detectar.")
            elif tech:
                for cat, tools in tech.items():
                    st.markdown(f"<small style='color:#94a3b8'>{cat}</small>  \n{' · '.join(f'`{t}`' for t in tools)}", unsafe_allow_html=True)
            else:
                st.caption("No se detectaron tecnologías conocidas (web muy básica o bloqueada).")

        with dd2:
            st.markdown("**⚡ Rendimiento real (Google PageSpeed)**")
            ps = sel.pagespeed
            if not b.tiene_web:
                st.caption("Sin web — no aplica.")
            elif ps:
                pscore = ps.get("performance_score", 0)
                pcol = "🟢" if pscore >= 90 else "🟡" if pscore >= 50 else "🔴"
                st.markdown(f"{pcol} **{pscore}/100** ({ps.get('estrategia','mobile')})")
                metr = []
                if ps.get("lcp_s") is not None:
                    metr.append(f"LCP {ps['lcp_s']:.1f}s")
                if ps.get("cls") is not None:
                    metr.append(f"CLS {ps['cls']:.2f}")
                if ps.get("fcp_s") is not None:
                    metr.append(f"FCP {ps['fcp_s']:.1f}s")
                if ps.get("tbt_ms") is not None:
                    metr.append(f"TBT {ps['tbt_ms']:.0f}ms")
                st.caption(" · ".join(metr))
                if ps.get("lcp_s") and ps["lcp_s"] > 2.5:
                    st.markdown(f"<small style='color:#ef4444'>⚠️ LCP {ps['lcp_s']:.1f}s — Google penaliza por encima de 2,5s</small>", unsafe_allow_html=True)
            else:
                st.caption("Pulsa el botón para medir el rendimiento real (~10s).")
                if st.button("⚡ Medir PageSpeed real", key="ps_btn_pagespeed"):
                    with st.spinner("Ejecutando Lighthouse en la web (~10s)…"):
                        ag = ProspectorAgent(nombre_agencia=st.session_state.ps_agencia)
                        ag.analizar_pagespeed(sel)
                    if sel.pagespeed:
                        st.rerun()
                    else:
                        st.warning(
                            "No se pudo medir. Lo más habitual: falta habilitar **PageSpeed "
                            "Insights API** en tu proyecto de Google Cloud y permitir que tu "
                            "API key la use (igual que hiciste con Places API New). "
                            "También puede ser web caída o muy lenta.",
                            icon="⚠️",
                        )

            if ps and ps.get("screenshot"):
                st.image(ps["screenshot"], caption="Captura real (PageSpeed)", width=180)

        st.divider()

        # ── Dos columnas: análisis web | reseñas ──────────────────────────
        col_web, col_rev = st.columns(2)

        with col_web:
            st.markdown("**🌐 Análisis de la web**")
            if not b.tiene_web:
                st.error("❌ SIN SITIO WEB — Lead Tier 1 (máxima oportunidad)")
            elif cl:
                if sel.tiempo_carga and sel.tiempo_carga < 99:
                    color_t = "🟢" if sel.tiempo_carga < 3 else "🔴"
                    st.caption(f"⏱️ Carga: {color_t} {sel.tiempo_carga:.1f}s")
                items_web = [
                    ("Formulario de contacto", cl.tiene_formulario),
                    ("Chat / WhatsApp widget", cl.tiene_chat_whatsapp),
                    ("Carga rápida <3s", cl.carga_rapida),
                    ("Mobile responsive", cl.es_mobile_responsive),
                    ("HTTPS activo", cl.tiene_https),
                    ("CTA de reserva claro", cl.tiene_cta_reserva),
                    ("Reserva online", cl.tiene_reserva_online),
                    ("Testimonios visibles", cl.tiene_testimonios),
                    ("Vídeo presentación", cl.tiene_video),
                    ("Blog / contenido SEO", cl.tiene_blog),
                    ("Píxel de remarketing", cl.tiene_pixel_tracking),
                    ("Captura de emails", cl.tiene_captura_email),
                ]
                for label, ok in items_web:
                    st.markdown(f"{'✅' if ok else '❌'} {label}")

        with col_rev:
            st.markdown("**⭐ Reseñas Google**")
            if not sel.resenas:
                st.caption("No hay reseñas disponibles en este análisis.")
            else:
                negs = [r for r in sel.resenas if r.rating <= 3]
                poss = [r for r in sel.resenas if r.rating >= 4]
                st.caption(f"🟢 {len(poss)} positivas   🔴 {len(negs)} negativas")
                for r in sorted(sel.resenas, key=lambda x: x.rating)[:5]:
                    stars = "⭐" * r.rating
                    cat = f"  `{r.categoria_dolor}`" if r.categoria_dolor else ""
                    with st.expander(f"{stars} {r.autor}{cat}", expanded=(r.rating <= 2)):
                        st.write(r.texto or "_Sin texto_")

        st.divider()

        # ── Dolores priorizados ────────────────────────────────────────────
        st.markdown("**💊 Dolores detectados — ordenados de mayor a menor impacto en ventas**")
        if not sel.pains:
            st.info("Sin dolores críticos detectados para este negocio.")
        else:
            for i, pain in enumerate(sel.pains):
                urg_ico = "🔴" if pain.urgencia >= 8 else "🟡" if pain.urgencia >= 5 else "🟢"
                with st.expander(
                    f"{urg_ico} #{i+1}  {pain.descripcion[:75]}…  — urgencia {pain.urgencia}/10",
                    expanded=(i == 0),
                ):
                    st.markdown(f"**Servicio recomendado:** {pain.servicio}")
                    st.markdown(f"**Evidencia encontrada:** _{pain.evidencia}_")

        col_b4a, col_b4b = st.columns(2)
        if col_b4a.button("← Volver al análisis masivo", key="ps_back4"):
            st.session_state.ps_paso = 3
            st.rerun()
        if col_b4b.button("💰 Calcular precios & ROI →", type="primary", key="ps_goto5"):
            st.session_state.ps_paso = 5
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # PASO 5 — Pricing & ROI (motor de ventas)
    # ══════════════════════════════════════════════════════════════════════════
    if paso >= 5 and st.session_state.ps_resultados:
        from agents.specialists.prospector import PricingCalculator
        st.divider()
        resultados = st.session_state.ps_resultados
        sel = resultados[st.session_state.ps_sel_idx]
        b = sel.business
        pc = PricingCalculator()

        st.markdown(f"### 5️⃣ Pricing & ROI — **{b.nombre}**")
        st.caption("Qué venderle, a qué precio, y cuánto ganará el cliente. Ajusta los valores y todo se recalcula al instante.")

        # Valores de partida (sugeridos por nicho, editables)
        ticket_def = sel.ticket_promedio or pc.ticket_sugerido(b.tipo)
        leads_def = sel.leads_mensuales or 200
        conv_def = sel.conversion_actual or 25.0

        col_p1, col_p2, col_p3 = st.columns(3)
        ticket = col_p1.number_input(
            "💶 Ticket medio por cliente (€)", min_value=10, max_value=10000,
            value=int(ticket_def), step=10, key="ps_ticket",
            help="Cuánto factura el negocio por cada cliente/venta. Pre-rellenado según el nicho.",
        )
        leads = col_p2.number_input(
            "📥 Leads/contactos al mes", min_value=10, max_value=10000,
            value=int(leads_def), step=10, key="ps_leads",
            help="Cuántas personas contactan o entran al mes (estimación).",
        )
        conv = col_p3.number_input(
            "🎯 Conversión actual (%)", min_value=1.0, max_value=100.0,
            value=float(conv_def), step=1.0, key="ps_conv",
            help="Qué % de esos contactos acaba comprando.",
        )

        # Guardar en el resultado
        sel.ticket_promedio = float(ticket)
        sel.leads_mensuales = int(leads)
        sel.conversion_actual = float(conv)

        # ── Dinero sobre la mesa: lo que pierde HOY ────────────────────────
        perdidas = pc.calcular_perdidas(sel, float(ticket), float(leads), float(conv))
        total_perdida = pc.total_perdidas(perdidas)
        sel.perdidas = [p.to_dict() for p in perdidas]
        sel.perdida_total_mes = total_perdida

        if perdidas:
            # Formatear números aparte (evita romper el CSS con .replace de comas)
            mes_txt = f"{total_perdida:,.0f}".replace(",", ".")
            ano_txt = f"{total_perdida * 12:,.0f}".replace(",", ".")
            st.markdown("#### 🩸 Dinero que está perdiendo HOY")
            st.markdown(
                "<div style='background:linear-gradient(90deg,rgba(239,68,68,.15),rgba(239,68,68,.03));"
                "border-left:4px solid #ef4444;border-radius:8px;padding:14px 18px;margin-bottom:10px'>"
                "<span style='font-size:.85rem;color:#94a3b8'>Pérdida estimada total</span><br>"
                f"<span style='font-size:2rem;font-weight:700;color:#ef4444'>−{mes_txt} €/mes</span> "
                f"<span style='color:#94a3b8'>· {ano_txt} €/año</span>"
                "</div>",
                unsafe_allow_html=True,
            )
            for p in perdidas:
                p_txt = f"{p.euros_mes:,.0f}".replace(",", ".")
                st.markdown(
                    "<div style='display:flex;justify-content:space-between;padding:6px 0;"
                    "border-bottom:1px solid rgba(255,255,255,.06)'>"
                    f"<span>🔻 <b>{p.concepto}</b><br>"
                    f"<small style='color:#94a3b8'>{p.explicacion}</small></span>"
                    f"<span style='color:#ef4444;font-weight:600;white-space:nowrap;"
                    f"margin-left:12px'>−{p_txt} €/mes</span>"
                    "</div>",
                    unsafe_allow_html=True,
                )
            st.caption("Estimación conservadora (techo del 45% de los ingresos) basada en las carencias reales detectadas. Es el argumento de apertura más potente.")
            st.divider()

        # Recomendación de servicios + precios
        recs = pc.recomendar(sel, float(ticket))

        st.markdown("#### 🛠️ Servicios recomendados (según sus dolores reales)")
        st.caption("Marca los que quieras incluir en la propuesta. El ROI se recalcula con tu selección.")

        seleccionados = []
        for i, r in enumerate(recs):
            cols = st.columns([0.5, 4, 2, 3])
            incluir = cols[0].checkbox("", value=(i < 3), key=f"ps_svc_{i}",
                                       label_visibility="collapsed")
            cols[1].markdown(f"**{r.servicio.nombre}**  \n<small style='color:#94a3b8'>{r.motivo}</small>", unsafe_allow_html=True)
            precio_txt = f"{r.setup:.0f}€ setup"
            if r.mensual > 0:
                precio_txt += f" + {r.mensual:.0f}€/mes"
            cols[2].markdown(f"<div style='text-align:right'><b>{precio_txt}</b></div>", unsafe_allow_html=True)
            # Impacto específico + evidencia estructurada
            impacto = getattr(r, "impacto_especifico", "") or r.servicio.kpi
            cols[3].markdown(f"<small style='color:#10b981'>📈 {impacto}</small>", unsafe_allow_html=True)
            # Expandible con la evidencia estructurada
            ev_v = getattr(r, "evidencia_verificada", [])
            ev_e = getattr(r, "evidencia_estimada", [])
            if ev_v or ev_e:
                with st.expander("🔍 Ver evidencia", expanded=False):
                    if ev_v:
                        st.markdown("**Datos verificados** *(medidos directamente)*")
                        for e in ev_v:
                            st.markdown(f"- 🔵 {e}")
                    if ev_e:
                        st.markdown("**Datos estimados** *(proyección con supuestos del sector)*")
                        for e in ev_e:
                            st.markdown(f"- 🟡 {e}")
            if incluir:
                seleccionados.append(r)

        if not seleccionados:
            st.warning("Selecciona al menos un servicio para calcular el ROI.")
        else:
            roi = pc.proyectar_roi(float(leads), float(conv), float(ticket), seleccionados)

            # Guardar para la propuesta
            sel.servicios_recomendados = [{
                "nombre": s.servicio.nombre, "setup": s.setup,
                "mensual": s.mensual, "kpi": s.servicio.kpi, "motivo": s.motivo,
            } for s in seleccionados]
            sel.roi_data = roi.to_dict()

            st.markdown("#### 💰 Lo que tú cobras")
            tot_setup = sum(s.setup for s in seleccionados)
            tot_mensual = sum(s.mensual for s in seleccionados)
            cc1, cc2, cc3 = st.columns(3)
            cc1.metric("Setup inicial", f"{tot_setup:,.0f} €".replace(",", "."))
            cc2.metric("Recurrente", f"{tot_mensual:,.0f} €/mes".replace(",", "."))
            cc3.metric("Primer año", f"{tot_setup + tot_mensual * 12:,.0f} €".replace(",", "."))

            st.markdown("#### 📊 Lo que gana el cliente — Sin vs Con automatización")
            df_roi = pd.DataFrame({
                "Métrica": ["Leads/mes", "Conversión", "Ventas/mes", "Ingresos/mes"],
                "❌ Ahora": [
                    f"{roi.leads_mes:.0f}",
                    f"{roi.conversion_actual:.0f}%",
                    f"{roi.ventas_actual:.0f}",
                    f"{roi.ingresos_actual:,.0f} €".replace(",", "."),
                ],
                "✅ Con MerakIA": [
                    f"{roi.leads_nuevo:.0f}",
                    f"{roi.conversion_nueva:.0f}%",
                    f"{roi.ventas_nuevo:.0f}",
                    f"{roi.ingresos_nuevo:,.0f} €".replace(",", "."),
                ],
            })
            st.dataframe(df_roi, use_container_width=True, hide_index=True)

            rc1, rc2, rc3, rc4 = st.columns(4)
            rc1.metric("💸 Ingreso extra", f"+{roi.ingreso_extra_mes:,.0f} €/mes".replace(",", "."))
            payback_txt = f"{roi.payback_meses:.1f} meses" if roi.payback_meses < 99 else "—"
            rc2.metric("⏱️ Recuperación", payback_txt)
            rc3.metric("📈 ROI 6 meses", f"{roi.roi_6m:.0f}%")
            rc4.metric("📈 ROI 12 meses", f"{roi.roi_12m:.0f}%")

            if roi.ingreso_extra_mes > tot_mensual:
                st.success(
                    f"💎 Argumento de cierre: por **{tot_mensual:.0f}€/mes** el cliente "
                    f"gana **{roi.ingreso_extra_mes:,.0f}€/mes** extra".replace(",", ".") +
                    f" — se paga solo en {payback_txt}.",
                )

        # ── Paquetes good/better/best + simulador de escenarios ────────────
        st.divider()
        st.markdown("#### 📦 Paquetes & Simulador de escenarios")
        st.caption(
            "Presenta 3 niveles (sube tu ticket medio) y ajusta el optimismo de la "
            "proyección. El recomendado es el de mejor ROI para *este* negocio."
        )

        ESC = {"Conservador": 0.6, "Realista": 1.0, "Optimista": 1.4}
        esc_label = st.radio(
            "Escenario de proyección",
            list(ESC.keys()), index=1, horizontal=True, key="ps_escenario",
        )
        factor = ESC[esc_label]

        paquetes = pc.cotizar_paquetes(sel, float(ticket), float(leads), float(conv), factor)
        sel.paquetes = [pq.to_dict() for pq in paquetes]

        NIVEL_BADGE = {1: "🥉 BÁSICO", 2: "🥈 RECOMENDADO", 3: "🥇 PREMIUM"}
        cols_pak = st.columns(3)
        for pq, col in zip(paquetes, cols_pak):
            with col:
                borde = "#22c55e" if pq.recomendado else "rgba(255,255,255,.12)"
                badge_bg = "#22c55e" if pq.recomendado else "#475569"
                desc_txt = f" · −{pq.paquete.descuento_pct:.0f}%" if pq.paquete.descuento_pct else ""
                extra_txt = f"{pq.roi.ingreso_extra_mes:,.0f}".replace(",", ".")
                setup_txt = f"{pq.setup:,.0f}".replace(",", ".")
                mens_txt = f"{pq.mensual:,.0f}".replace(",", ".")
                payback_p = f"{pq.roi.payback_meses:.1f} meses" if pq.roi.payback_meses < 99 else "—"
                st.markdown(
                    f"<div style='border:2px solid {borde};border-radius:10px;padding:14px;min-height:90px'>"
                    f"<span style='background:{badge_bg};color:#fff;font-size:.7rem;font-weight:700;"
                    f"padding:2px 8px;border-radius:10px'>{NIVEL_BADGE[pq.paquete.nivel]}</span>"
                    f"<div style='font-weight:700;margin-top:8px'>{pq.paquete.nombre.split('—')[0].strip()}</div>"
                    f"<div style='font-size:.78rem;color:#94a3b8;min-height:34px'>{pq.paquete.tagline}</div>"
                    f"<div style='font-size:1.3rem;font-weight:700;margin-top:6px'>{setup_txt}€ "
                    f"<span style='font-size:.8rem;color:#94a3b8'>setup{desc_txt}</span></div>"
                    f"<div style='color:#94a3b8;font-size:.85rem'>+ {mens_txt}€/mes</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"<small style='color:#10b981'>Cliente gana <b>+{extra_txt}€/mes</b></small>", unsafe_allow_html=True)
                st.caption(f"Payback {payback_p} · ROI 12m {pq.roi.roi_12m:.0f}%")
                with st.expander("Incluye"):
                    for s in pq.servicios:
                        st.markdown(f"- {s.servicio.nombre}")

        # Tabla comparativa de escenarios para el paquete recomendado
        reco = next((p for p in paquetes if p.recomendado), paquetes[1])
        st.markdown(f"**Simulador — {reco.paquete.nombre.split('—')[0].strip()} en los 3 escenarios:**")
        filas = []
        for etq, fo in ESC.items():
            paks_e = pc.cotizar_paquetes(sel, float(ticket), float(leads), float(conv), fo)
            pr = next((p for p in paks_e if p.paquete.clave == reco.paquete.clave), None)
            if pr:
                filas.append({
                    "Escenario": etq + (" ◀" if etq == esc_label else ""),
                    "Ingreso extra cliente": f"+{pr.roi.ingreso_extra_mes:,.0f} €/mes".replace(",", "."),
                    "Payback": f"{pr.roi.payback_meses:.1f} m" if pr.roi.payback_meses < 99 else "—",
                    "ROI 12m": f"{pr.roi.roi_12m:.0f}%",
                })
        st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
        st.caption("Proyección estimada. Presenta el escenario *Conservador* en la reunión: si los números cierran ahí, cierran seguro.")

        st.divider()
        col_b5a, col_b5b = st.columns(2)
        if col_b5a.button("← Volver a dolores", key="ps_back5"):
            st.session_state.ps_paso = 4
            st.rerun()
        if col_b5b.button("📣 Generar arsenal de venta →", type="primary", key="ps_goto6"):
            st.session_state.ps_paso = 6
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # PASO 6 — Arsenal de venta (outreach + assets)
    # ══════════════════════════════════════════════════════════════════════════
    if paso >= 6 and st.session_state.ps_resultados:
        st.divider()
        resultados = st.session_state.ps_resultados
        sel = resultados[st.session_state.ps_sel_idx]
        b = sel.business

        st.markdown(f"### 6️⃣ Arsenal de venta — **{b.nombre}**")
        st.caption("Todo personalizado con los datos reales del negocio y el ROI calculado.")

        negativas = [r for r in sel.resenas if r.rating <= 3 and r.texto]

        # Resumen del ROI + pérdida actual para alimentar propuesta/presentación
        roi_resumen = ""
        if sel.perdida_total_mes:
            roi_resumen += (
                f"PÉRDIDA ACTUAL ESTIMADA: −{sel.perdida_total_mes:.0f}€/mes "
                f"({sel.perdida_total_mes * 12:.0f}€/año) por las carencias detectadas. "
            )
        if sel.automation and not sel.automation.get("es_autonomo"):
            roi_resumen += (
                "NO tiene ningún sistema autónomo (sin chatbot IA ni WhatsApp automatizado): "
                "el servicio estrella a proponer es un agente IA + chatbot 24/7. "
            )
        if sel.scorecard:
            sc = sel.scorecard
            roi_resumen += f"Madurez digital {sc.get('score_global', 0):.0f}/100"
            if sc.get("percentil_nicho") is not None:
                roi_resumen += f" (percentil {sc['percentil_nicho']} de su nicho)"
            roi_resumen += ". "
        if sel.pagespeed:
            ps = sel.pagespeed
            roi_resumen += f"PageSpeed real {ps.get('performance_score')}/100"
            if ps.get("lcp_s"):
                roi_resumen += f" (LCP {ps['lcp_s']:.1f}s)"
            roi_resumen += ". "
        if sel.competitive and not sel.competitive.get("es_lider"):
            cmp = sel.competitive
            roi_resumen += (
                f"Va por detrás de su nicho (puesto {cmp.get('posicion')}/{cmp.get('total')}, "
                f"líder {cmp.get('lider_nombre')}). "
            )
        if sel.roi_data:
            rd = sel.roi_data
            roi_resumen += (
                f"Inversión {rd['inversion_setup']:.0f}€ setup + {rd['inversion_mensual']:.0f}€/mes; "
                f"ingreso extra estimado +{rd['ingreso_extra_mes']:.0f}€/mes; "
                f"recuperación en {rd['payback_meses']:.1f} meses; ROI 12m {rd['roi_12m']:.0f}%."
            )
        if sel.paquetes:
            reco_pak = next((p for p in sel.paquetes if p.get("recomendado")), None)
            if reco_pak:
                roi_resumen += (
                    f" PAQUETE RECOMENDADO: {reco_pak['nombre']} "
                    f"({reco_pak['setup']:.0f}€ setup + {reco_pak['mensual']:.0f}€/mes), "
                    f"incluye: {', '.join(reco_pak['servicios'])}."
                )

        col_cfg_o1, col_cfg_o2, col_cfg_o3 = st.columns(3)
        nombre_agencia_o = col_cfg_o1.text_input(
            "Tu agencia", value=st.session_state.ps_agencia, key="ps_agencia_o"
        )
        nombre_dest = col_cfg_o2.text_input(
            "Nombre propietario",
            value=b.nombre_propietario or "",
            placeholder="Si lo conoces, el email irá personalizado",
            key="ps_dest_nombre",
        )
        contacto_o = col_cfg_o3.text_input(
            "Tu contacto (informe)",
            placeholder="email · teléfono · web",
            key="ps_contacto_o",
        )

        # ── Informe de diagnóstico white-label (el caballo de Troya) ───────
        from agents.specialists.prospector import generar_informe_html
        falta_pricing = not (sel.scorecard or sel.perdidas or sel.paquetes)
        with st.container():
            ci1, ci2 = st.columns([3, 2])
            ci1.markdown(
                "**📄 Informe de diagnóstico white-label** — documento profesional con "
                "tu marca, sus datos reales, lo que pierde y la solución con ROI. "
                "Para enviar antes de la reunión o llevar impreso."
            )
            if falta_pricing:
                ci2.caption("Pasa por el paso 5 (Pricing) para incluir solución y ROI en el informe.")
            html_informe = generar_informe_html(
                sel, agencia=nombre_agencia_o, contacto=contacto_o
            )
            ci2.download_button(
                "⬇️ Descargar informe (HTML)",
                data=html_informe.encode("utf-8"),
                file_name=f"diagnostico_{b.nombre.replace(' ', '_')[:30]}.html",
                mime="text/html",
                type="primary",
                key="ps_dl_informe",
                help="Ábrelo en el navegador y Ctrl+P para guardarlo como PDF.",
            )

        (tab_email, tab_wa, tab_llamada, tab_propuesta,
         tab_demo, tab_landing, tab_present, tab_secuencia) = st.tabs(
            ["📧 Email", "💬 WhatsApp", "📞 Script", "📄 Propuesta",
             "🎁 Demo", "🖥️ Landing", "📊 Presentación", "🔁 Secuencia"]
        )

        def _agent_o():
            return ProspectorAgent(nombre_agencia=nombre_agencia_o)

        # ── Email ─────────────────────────────────────────────────────────
        with tab_email:
            if not sel.email_asunto:
                st.info(
                    "El email citará reseñas reales, cuantificará el coste del dolor "
                    "y terminará con un CTA de 15 minutos.", icon="✍️"
                )
                if st.button("📧 Generar email emocional", type="primary", key="ps_gen_email"):
                    with st.spinner("Redactando con framework PAS (Problem → Agitate → Solution)…"):
                        ag = _agent_o()
                        asunto, cuerpo = ag.offer_gen.generar_email(
                            b, sel.pains, negativas, nombre_dest or None
                        )
                    sel.email_asunto = asunto
                    sel.email_cuerpo = cuerpo
                    ag.crm.guardar(sel)
                    st.rerun()
            else:
                st.markdown(f"**Asunto:** `{sel.email_asunto}`")
                st.text_area("Cuerpo", value=sel.email_cuerpo or "", height=320, key="ps_email_txt")
                col_dl, col_regen = st.columns(2)
                col_dl.download_button(
                    "⬇️ Descargar .txt",
                    data=f"ASUNTO: {sel.email_asunto}\n\n{sel.email_cuerpo}",
                    file_name=f"email_{b.nombre[:25].replace(' ','_')}.txt",
                )
                if col_regen.button("🔄 Regenerar", key="ps_regen_email"):
                    sel.email_asunto = None
                    sel.email_cuerpo = None
                    st.rerun()

        # ── WhatsApp ──────────────────────────────────────────────────────
        with tab_wa:
            if not sel.whatsapp_mensaje:
                st.info("Mensaje directo de 5-6 líneas, hook específico, dolor en euros.", icon="💬")
                if st.button("💬 Generar WhatsApp", type="primary", key="ps_gen_wa"):
                    with st.spinner("Escribiendo…"):
                        ag = _agent_o()
                        sel.whatsapp_mensaje = ag.offer_gen.generar_whatsapp(
                            b, sel.pains, negativas
                        )
                        ag.crm.guardar(sel)
                    st.rerun()
            else:
                st.text_area("Mensaje", value=sel.whatsapp_mensaje, height=200, key="ps_wa_txt")
                col_dl2, col_regen2 = st.columns(2)
                col_dl2.download_button(
                    "⬇️ Descargar .txt",
                    data=sel.whatsapp_mensaje,
                    file_name=f"wa_{b.nombre[:25].replace(' ','_')}.txt",
                )
                if col_regen2.button("🔄 Regenerar", key="ps_regen_wa"):
                    sel.whatsapp_mensaje = None
                    st.rerun()

        # ── Script llamada ────────────────────────────────────────────────
        with tab_llamada:
            if not sel.script_llamada:
                st.info("Guión completo: apertura + gancho + cualificación + propuesta + cierre + objeciones.", icon="📞")
                if st.button("📞 Generar guión cold call", type="primary", key="ps_gen_script"):
                    with st.spinner("Construyendo guión…"):
                        ag = _agent_o()
                        sel.script_llamada = ag.offer_gen.generar_script_llamada(
                            b, sel.pains, negativas
                        )
                        ag.crm.guardar(sel)
                    st.rerun()
            else:
                st.text_area("Guión", value=sel.script_llamada, height=450, key="ps_script_txt")
                col_dl3, col_regen3 = st.columns(2)
                col_dl3.download_button(
                    "⬇️ Descargar .txt",
                    data=sel.script_llamada,
                    file_name=f"guion_{b.nombre[:25].replace(' ','_')}.txt",
                )
                if col_regen3.button("🔄 Regenerar", key="ps_regen_script"):
                    sel.script_llamada = None
                    st.rerun()

        # ── Propuesta completa ────────────────────────────────────────────
        with tab_propuesta:
            if not sel.propuesta_texto:
                st.info(
                    "Documento estructurado: diagnóstico · soluciones · cómo trabajamos · "
                    "inversión y ROI (los del paso 5) · siguiente paso.",
                    icon="📄",
                )
                if st.button("📄 Generar propuesta completa", type="primary", key="ps_gen_propuesta"):
                    with st.spinner("Redactando propuesta…"):
                        ag = _agent_o()
                        resumen = sel.resumen_oportunidad
                        if roi_resumen:
                            resumen = f"{resumen}\n\nNúmeros para la propuesta: {roi_resumen}"
                        sel.propuesta_texto = ag.offer_gen.generar_propuesta_texto(
                            b, sel.pains, resumen
                        )
                        ag.crm.guardar(sel)
                    st.rerun()
            else:
                st.text_area("Propuesta", value=sel.propuesta_texto, height=480, key="ps_propuesta_txt")
                col_dlp, col_regp = st.columns(2)
                col_dlp.download_button(
                    "⬇️ Descargar propuesta .txt",
                    data=sel.propuesta_texto,
                    file_name=f"propuesta_{b.nombre[:25].replace(' ','_')}.txt",
                )
                if col_regp.button("🔄 Regenerar", key="ps_regen_propuesta"):
                    sel.propuesta_texto = None
                    st.rerun()

        # ── Demo (caballo de Troya) ────────────────────────────────────────
        with tab_demo:
            st.caption("Genera el prompt para montar un agente DEMO que atienda como si fuera este negocio. Llegar a la reunión con la demo viva es lo que más cierra.")
            col_d1, col_d2 = st.columns(2)
            tipo_demo = col_d1.selectbox("Canal de la demo", ["WhatsApp", "Voz (llamada)", "Chat web"], key="ps_demo_canal")
            objetivo_demo = col_d2.selectbox(
                "Objetivo del agente",
                ["agendar citas", "responder y cualificar leads", "reservar mesa/servicio", "dar información y captar contacto"],
                key="ps_demo_obj",
            )
            if not sel.demo_prompt:
                if st.button("🎁 Generar prompt de demo", type="primary", key="ps_gen_demo"):
                    with st.spinner("Construyendo el agente demo…"):
                        ag = _agent_o()
                        sel.demo_prompt = ag.offer_gen.generar_demo_prompt(
                            b, sel.pains, tipo_demo, objetivo_demo
                        )
                        ag.crm.guardar(sel)
                    st.rerun()
            else:
                st.text_area("Prompt del agente demo", value=sel.demo_prompt, height=420, key="ps_demo_txt")
                col_dld, col_regd = st.columns(2)
                col_dld.download_button(
                    "⬇️ Descargar prompt .txt",
                    data=sel.demo_prompt,
                    file_name=f"demo_{b.nombre[:25].replace(' ','_')}.txt",
                )
                if col_regd.button("🔄 Regenerar", key="ps_regen_demo"):
                    sel.demo_prompt = None
                    st.rerun()

        # ── Landing ────────────────────────────────────────────────────────
        with tab_landing:
            st.caption("Prompt listo para Base44 / Framer / Lovable / v0: estructura, copy y diseño de una landing de alta conversión para este negocio.")
            if not sel.landing_prompt:
                if st.button("🖥️ Generar prompt de landing", type="primary", key="ps_gen_landing"):
                    with st.spinner("Diseñando la landing…"):
                        ag = _agent_o()
                        sel.landing_prompt = ag.offer_gen.generar_landing_prompt(
                            b, sel.pains, sel.resumen_oportunidad
                        )
                        ag.crm.guardar(sel)
                    st.rerun()
            else:
                st.text_area("Prompt de landing", value=sel.landing_prompt, height=420, key="ps_landing_txt")
                col_dll, col_regl = st.columns(2)
                col_dll.download_button(
                    "⬇️ Descargar prompt .txt",
                    data=sel.landing_prompt,
                    file_name=f"landing_{b.nombre[:25].replace(' ','_')}.txt",
                )
                if col_regl.button("🔄 Regenerar", key="ps_regen_landing"):
                    sel.landing_prompt = None
                    st.rerun()

        # ── Presentación (Gamma) ───────────────────────────────────────────
        with tab_present:
            st.caption("Prompt para Gamma que crea la presentación de la reunión: diagnóstico, dolor en euros, solución y ROI.")
            if not sel.presentacion_prompt:
                if st.button("📊 Generar prompt de presentación", type="primary", key="ps_gen_present"):
                    with st.spinner("Preparando la presentación…"):
                        ag = _agent_o()
                        sel.presentacion_prompt = ag.offer_gen.generar_presentacion_prompt(
                            b, sel.pains, sel.resumen_oportunidad, roi_resumen
                        )
                        ag.crm.guardar(sel)
                    st.rerun()
            else:
                st.text_area("Prompt para Gamma", value=sel.presentacion_prompt, height=420, key="ps_present_txt")
                col_dlpr, col_regpr = st.columns(2)
                col_dlpr.download_button(
                    "⬇️ Descargar prompt .txt",
                    data=sel.presentacion_prompt,
                    file_name=f"presentacion_{b.nombre[:25].replace(' ','_')}.txt",
                )
                if col_regpr.button("🔄 Regenerar", key="ps_regen_present"):
                    sel.presentacion_prompt = None
                    st.rerun()

        # ── Secuencia de seguimiento ───────────────────────────────────────
        with tab_secuencia:
            st.caption("Cadencia de 5 toques en 14 días tras el primer email. Cada toque aporta valor, no solo '¿lo viste?'.")
            if not sel.secuencia_seguimiento:
                if st.button("🔁 Generar secuencia de seguimiento", type="primary", key="ps_gen_secuencia"):
                    with st.spinner("Diseñando la cadencia de seguimiento…"):
                        ag = _agent_o()
                        sel.secuencia_seguimiento = ag.offer_gen.generar_secuencia(b, sel.pains, negativas)
                        ag.crm.guardar(sel)
                    st.rerun()
            else:
                CANAL_ICO = {"WhatsApp": "💬", "Email": "📧", "Llamada": "📞", "LinkedIn": "🔗"}
                for t in sel.secuencia_seguimiento:
                    ico = CANAL_ICO.get(t.get("canal", ""), "•")
                    with st.expander(f"📅 Día {t.get('dia','?')} · {ico} {t.get('canal','')} — {t.get('titulo','')}", expanded=False):
                        st.write(t.get("mensaje", ""))
                # Exportar toda la secuencia
                texto_sec = "\n\n".join(
                    f"DÍA {t.get('dia')} · {t.get('canal')} — {t.get('titulo')}\n{t.get('mensaje')}"
                    for t in sel.secuencia_seguimiento
                )
                col_dls, col_regs = st.columns(2)
                col_dls.download_button(
                    "⬇️ Descargar secuencia .txt",
                    data=texto_sec.encode("utf-8"),
                    file_name=f"secuencia_{b.nombre[:25].replace(' ','_')}.txt",
                )
                if col_regs.button("🔄 Regenerar", key="ps_regen_secuencia"):
                    sel.secuencia_seguimiento = []
                    st.rerun()

        st.divider()
        col_b6a, col_b6b = st.columns(2)
        if col_b6a.button("← Volver a Pricing & ROI", key="ps_back6"):
            st.session_state.ps_paso = 5
            st.rerun()
        if col_b6b.button("📋 Registrar en CRM →", type="primary", key="ps_goto7"):
            st.session_state.ps_paso = 7
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # PASO 7 — CRM & Seguimiento
    # ══════════════════════════════════════════════════════════════════════════
    if paso >= 7:
        st.divider()
        st.markdown("### 7️⃣ CRM — Registra el estado y haz el seguimiento")

        crm = CRM()

        # ── Estado del negocio actual ──────────────────────────────────────
        if st.session_state.ps_resultados:
            sel = st.session_state.ps_resultados[st.session_state.ps_sel_idx]
            b = sel.business
            st.markdown(f"**Negocio activo:** {b.nombre}")

            col_s1, col_s2 = st.columns([1, 2])
            nuevo_estado = col_s1.selectbox(
                "Estado",
                ESTADOS,
                index=ESTADOS.index(sel.estado) if sel.estado in ESTADOS else 0,
                format_func=lambda e: f"{ESTADO_COLORS.get(e,'')} {e.upper()}",
                key="ps_crm_estado",
            )
            nuevas_notas = col_s2.text_area(
                "Notas", value=sel.notas or "", height=80, key="ps_crm_notas"
            )
            if st.button("💾 Guardar estado", key="ps_crm_save"):
                crm.actualizar_estado(b.place_id, nuevo_estado, nuevas_notas)
                sel.estado = nuevo_estado
                sel.notas = nuevas_notas
                st.success(f"✅ {ESTADO_COLORS.get(nuevo_estado,'')} {nuevo_estado.upper()} guardado")

            if st.button("✉️ Analizar otro negocio", key="ps_otro_negocio"):
                st.session_state.ps_paso = 4
                st.rerun()

        st.divider()

        # ── Tabla CRM completa ─────────────────────────────────────────────
        st.markdown("**Todos los prospectos en el CRM**")

        col_f1, col_f2, col_f3 = st.columns(3)
        filtro_ciudad_crm = col_f1.text_input("Ciudad", key="crm2_ciudad")
        filtro_estado_crm = col_f2.selectbox(
            "Estado", ["todos"] + ESTADOS, key="crm2_estado",
            format_func=lambda e: "Todos" if e == "todos" else f"{ESTADO_COLORS.get(e,'')} {e.upper()}",
        )
        filtro_opt_crm = col_f3.selectbox("Oportunidad", ["todas", "alta", "media", "baja"], key="crm2_opt")

        rows_crm = crm.listar(
            ciudad=filtro_ciudad_crm or None,
            estado=filtro_estado_crm if filtro_estado_crm != "todos" else None,
            oportunidad=filtro_opt_crm if filtro_opt_crm != "todas" else None,
        )

        stats = crm.stats()
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Total", stats["total"])
        mc2.metric("Alta oportunidad", stats["alta_oportunidad"])
        mc3.metric("Clientes", stats["por_estado"].get("cliente", 0))
        mc4.metric("Propuestas", stats["por_estado"].get("propuesta", 0))

        if rows_crm:
            COLOR_OPT_C = {"alta": "🔴", "media": "🟡", "baja": "🟢"}
            df_crm = pd.DataFrame([{
                "Score": r["score_oportunidad"] or 0,
                "Oportunidad": COLOR_OPT_C.get(r["oportunidad_nivel"] or "", "⚪") + " " + (r["oportunidad_nivel"] or "").upper(),
                "Estado": ESTADO_COLORS.get(r["estado"], "") + " " + (r["estado"] or "").upper(),
                "Nombre": r["nombre"],
                "Ciudad": r["ciudad"],
                "Web": "❌" if not r["tiene_web"] else "✅",
                "Rating": f"{r['rating']} ⭐" if r["rating"] else "—",
                "Teléfono": r["telefono"] or "—",
                "Contactado": (r["fecha_contacto"] or "")[:10],
            } for r in rows_crm])
            st.dataframe(df_crm, use_container_width=True, hide_index=True)

            csv_data = crm.exportar_csv()
            if csv_data:
                st.download_button(
                    "⬇️ Exportar todo el CRM a CSV",
                    data=csv_data.encode("utf-8"),
                    file_name="prospectos_crm.csv",
                    mime="text/csv",
                )
        else:
            st.info("Sin prospectos en el CRM todavía.", icon="ℹ️")

        if st.button("🔄 Empezar nueva búsqueda", key="ps_nueva_busqueda"):
            for k in ["ps_paso", "ps_negocios", "ps_resultados", "ps_sel_idx", "ps_tipo", "ps_ciudad"]:
                if k == "ps_paso":
                    st.session_state[k] = 1
                elif k in ["ps_negocios", "ps_resultados"]:
                    st.session_state[k] = []
                elif k == "ps_sel_idx":
                    st.session_state[k] = 0
                else:
                    st.session_state[k] = ""
            st.rerun()


# ─── Gestorías (nicho back-office) ─────────────────────────────────────────────
elif page == "🏛️ Gestorías":
    import pandas as pd
    import json as _json
    from pathlib import Path as _Path
    import generar_prospectos_gestorias as gest
    from config.settings import settings

    st.markdown("""<style>
    .chip { display:inline-block;padding:2px 9px;border-radius:12px;font-size:11px;font-weight:700;margin:2px; }
    .chip-alta  { background:rgba(239,68,68,.15);color:#ef4444;border:1px solid #ef4444; }
    .chip-media { background:rgba(245,158,11,.15);color:#f59e0b;border:1px solid #f59e0b; }
    .chip-baja  { background:rgba(16,185,129,.15);color:#10b981;border:1px solid #10b981; }
    </style>""", unsafe_allow_html=True)

    st.markdown('<div class="merakia-header">🏛️ Gestorías & Asesorías</div>',
                unsafe_allow_html=True)
    st.caption("Nicho de back-office: vendemos horas recuperadas (automatizar papeleo), "
               "no marketing. Listado propio con scoring distinto al de ProspectorIA.")
    st.divider()

    JSON_PATH = _Path("outputs/prospector/prospectos_gestorias_vng.json")
    PLAYBOOK = _Path("docs/prospeccion_gestorias_playbook.md")

    # ── Aviso de enfoque (para no confundir con ProspectorIA) ─────────────────
    st.info(
        "**Ojo — aquí el buen prospecto es el contrario que en ProspectorIA.** "
        "Allí premiamos el dolor digital visible (sin web, mala reputación) porque "
        "vendemos marketing. Aquí premiamos al despacho **establecido y grande** "
        "(mucha reseña = mucha clientela = mucho papeleo = mucha saturación), que "
        "es a quien le vendemos automatizar el back-office.",
        icon="🧭",
    )

    # ── Configuración / regenerar ─────────────────────────────────────────────
    with st.expander("⚙️ Configuración y regeneración del listado", expanded=False):
        gkey = st.text_input(
            "Google Places API Key",
            value=settings.google_places_api_key or (gest.load_key() or ""),
            type="password",
            help="Solo hace falta para regenerar el listado. El listado ya guardado se lee sin key.",
        )
        col_z1, col_z2 = st.columns(2)
        with col_z1:
            ciudad_foco = st.text_input(
                "Ciudad foco (va primero en el ranking)",
                value="Vilanova i la Geltrú",
                key="gest_ciudad_foco",
            )
        with col_z2:
            limite_gest = st.number_input("Máx. prospectos", 10, 60, 40, 5, key="gest_limite")

        queries_txt = st.text_area(
            "Búsquedas (una por línea)",
            value="\n".join(gest.DEFAULT_QUERIES),
            height=160,
            key="gest_queries",
            help="Edita para cambiar de zona o tipo de despacho.",
        )

        if st.button("🔄 Regenerar listado (consume API)", type="primary", key="gest_regen"):
            key = gkey.strip() or gest.load_key()
            if not key:
                st.error("Falta la API Key de Google Places.")
            else:
                queries = [q.strip() for q in queries_txt.splitlines() if q.strip()]
                foco = (ciudad_foco or "Vilanova i la Geltr").replace("ú", "").strip() or "Vilanova i la Geltr"
                log_box = st.empty()
                logs = []

                def _log(msg):
                    logs.append(str(msg))
                    log_box.code("\n".join(logs[-12:]))

                try:
                    with st.spinner("Buscando en Google Places..."):
                        prospectos = gest.recopilar(
                            key=key, queries=queries, ciudad_foco=foco,
                            limite=int(limite_gest), log=_log,
                        )
                        gest.guardar(prospectos)
                    st.success(f"✅ {len(prospectos)} prospectos regenerados y guardados.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # DEMO EN VIVO — Lector de facturas (el "producto" que vendemos)
    # ══════════════════════════════════════════════════════════════════════════
    st.subheader("🔎 Demo en vivo — Lector de facturas")
    st.caption("Esto es lo que vendes: sube facturas (PDF o foto) y mira cómo se "
               "leen solas. La máquina extrae, marca lo dudoso, y el humano valida.")

    up = st.file_uploader(
        "Sube una o varias facturas",
        type=["png", "jpg", "jpeg", "webp", "pdf"],
        accept_multiple_files=True,
        key="gest_facturas_up",
    )
    col_d1, col_d2 = st.columns([1, 3])
    with col_d1:
        usar_muestra = st.button("📄 Usar factura de ejemplo", key="gest_demo_muestra")
    with col_d2:
        leer = st.button("🚀 Leer facturas →", type="primary",
                         disabled=not up, key="gest_demo_leer")

    # Construir la lista de (nombre, bytes) a procesar
    a_procesar = []
    if leer and up:
        a_procesar = [(f.name, f.getvalue()) for f in up]
    elif usar_muestra:
        muestra = _Path("gestorias/demo_facturas/factura_muestra.png")
        if muestra.exists():
            a_procesar = [(muestra.name, muestra.read_bytes())]
        else:
            st.error("No encuentro la factura de ejemplo. Genérala con "
                     "`gestorias/_generar_factura_muestra.py`.")

    if a_procesar:
        try:
            from gestorias.extractor_facturas import (
                extraer_factura_bytes, png_preview_bytes, a_csv, SCHEMA,
            )
            import anthropic as _anthropic

            client = _anthropic.Anthropic(api_key=settings.anthropic_api_key)
            filas = []
            prog = st.progress(0.0, text="Leyendo facturas...")
            for i, (nombre, data_bytes) in enumerate(a_procesar):
                prog.progress(i / len(a_procesar), text=f"Leyendo {nombre}...")
                try:
                    res = extraer_factura_bytes(data_bytes, nombre, client)
                except Exception as e:
                    res = {"_archivo": nombre, "_error": str(e)}
                filas.append((nombre, data_bytes, res))
            prog.progress(1.0, text="Hecho.")
            prog.empty()

            _ETIQUETAS = {
                "emisor_nombre": "Emisor", "emisor_cif": "CIF emisor",
                "cliente_nombre": "Cliente", "cliente_cif": "CIF cliente",
                "numero_factura": "Nº factura", "fecha": "Fecha",
                "fecha_vencimiento": "Vencimiento", "base_imponible": "Base imponible",
                "tipo_iva": "Tipo IVA %", "cuota_iva": "Cuota IVA",
                "retencion_irpf": "Retención IRPF", "total": "TOTAL", "moneda": "Moneda",
            }

            for nombre, data_bytes, res in filas:
                st.divider()
                col_img, col_dat = st.columns([1, 1.3])
                with col_img:
                    try:
                        st.image(png_preview_bytes(data_bytes, nombre),
                                 caption=nombre, use_container_width=True)
                    except Exception:
                        st.caption(f"({nombre} — sin previsualización)")
                with col_dat:
                    if res.get("_error"):
                        st.error(f"No se pudo leer: {res['_error']}")
                        continue
                    conf = res.get("_confianza")
                    color = "chip-baja" if (conf or 0) >= 85 else "chip-media" if (conf or 0) >= 60 else "chip-alta"
                    st.markdown(f'<span class="chip {color}">Confianza {conf}%</span>',
                                unsafe_allow_html=True)
                    filas_tab = [{"Campo": _ETIQUETAS.get(k, k), "Valor": res.get(k)}
                                 for k in SCHEMA.keys()]
                    st.dataframe(pd.DataFrame(filas_tab), hide_index=True,
                                 use_container_width=True)
                    avisos = res.get("_avisos") or []
                    if avisos:
                        st.warning("**⚠️ Revisar (el humano valida esto):**\n\n"
                                   + "\n".join(f"- {a}" for a in avisos))
                    else:
                        st.success("Sin avisos: lectura limpia.")

            # CSV combinado listo para importar/revisar
            solo_datos = [r for _, _, r in filas if not r.get("_error")]
            if solo_datos:
                import tempfile as _tmp
                tmp_csv = _Path(_tmp.gettempdir()) / "facturas_extraidas.csv"
                a_csv(solo_datos, tmp_csv)
                st.download_button(
                    "⬇️ Descargar CSV (listo para el programa de gestión)",
                    data=tmp_csv.read_bytes(),
                    file_name="facturas_extraidas.csv",
                    mime="text/csv",
                )
        except Exception as e:
            st.error(f"Error en la demo: {e}")

    st.divider()

    # ── Cargar listado guardado ───────────────────────────────────────────────
    st.subheader("📇 Listado de prospectos")
    if not JSON_PATH.exists():
        st.warning(
            "Aún no hay listado generado. Abre **⚙️ Configuración** arriba y pulsa "
            "**Regenerar listado**.",
            icon="📭",
        )
        st.stop()

    data = _json.loads(JSON_PATH.read_text(encoding="utf-8"))
    df = pd.DataFrame(data)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total = len(df)
    icp1 = int((df["tipo"] == "gestoria/asesoria").sum())
    con_web = int((df["web"].astype(str).str.len() > 0).sum())
    con_tel = int((df["telefono"].astype(str).str.len() > 0).sum())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Prospectos", total)
    c2.metric("ICP primario", icp1, help="Gestoría/asesoría fiscal-laboral (el resto es secundario)")
    c3.metric("Con web (email localizable)", con_web)
    c4.metric("Con teléfono", con_tel)

    st.divider()

    # ── Filtros ───────────────────────────────────────────────────────────────
    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    with col_f1:
        tipos = ["(todos)"] + sorted(df["tipo"].dropna().unique().tolist())
        f_tipo = st.selectbox("Tipo", tipos, index=(tipos.index("gestoria/asesoria")
                              if "gestoria/asesoria" in tipos else 0), key="gest_f_tipo")
    with col_f2:
        f_texto = st.text_input("Buscar por nombre", key="gest_f_texto", placeholder="Ej: assessors")
    with col_f3:
        solo_foco = st.checkbox("Solo ciudad foco", value=True, key="gest_f_foco")

    view = df.copy()
    if f_tipo != "(todos)":
        view = view[view["tipo"] == f_tipo]
    if solo_foco and "en_foco" in view.columns:
        view = view[view["en_foco"] == True]  # noqa: E712
    if f_texto.strip():
        view = view[view["nombre"].str.contains(f_texto.strip(), case=False, na=False)]

    view = view.sort_values("score_prospecto", ascending=False).reset_index(drop=True)

    st.caption(f"Mostrando **{len(view)}** de {total} prospectos.")

    # ── Top 10 listos para contactar ──────────────────────────────────────────
    st.subheader("🎯 Top para contactar esta semana")
    st.caption("Máx. 10 por semana con personalización real (ver playbook). "
               "Copia el email/teléfono y escribe desde tu cuenta.")

    top = view.head(10)
    for _, row in top.iterrows():
        web = str(row.get("web") or "")
        tel = str(row.get("telefono") or "")
        maps = str(row.get("maps") or "")
        rating = row.get("rating")
        resenas = row.get("resenas")
        links = []
        if web:
            links.append(f'<a href="{web}" target="_blank">🌐 Web</a>')
        if maps:
            links.append(f'<a href="{maps}" target="_blank">📍 Maps</a>')
        links_html = " &nbsp;·&nbsp; ".join(links)
        st.markdown(f"""
        <div class="result-box" style="margin-bottom:8px">
          <b>{row['nombre']}</b>
          <span class="chip chip-baja">score {int(row['score_prospecto'])}</span>
          <span class="chip" style="background:rgba(255,255,255,.06);color:#94A3B8;border:1px solid rgba(255,255,255,.1)">{row['tipo']}</span>
          <br>
          <small style="color:#94A3B8">
            ⭐ {rating if rating is not None else '—'} ({resenas} reseñas)
            &nbsp;·&nbsp; ☎️ {tel or '—'} &nbsp;·&nbsp; {links_html}
          </small>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── Tabla completa + descarga ─────────────────────────────────────────────
    st.subheader("📋 Listado completo")
    cols_show = ["nombre", "tipo", "telefono", "web", "rating", "resenas",
                 "score_prospecto", "en_foco", "motivos"]
    cols_show = [c for c in cols_show if c in view.columns]
    st.dataframe(view[cols_show], use_container_width=True, hide_index=True)

    csv_bytes = view[cols_show].to_csv(index=False, sep=";").encode("utf-8-sig")
    st.download_button(
        "⬇️ Descargar CSV filtrado",
        data=csv_bytes,
        file_name="gestorias_filtrado.csv",
        mime="text/csv",
    )

    # ── Playbook ──────────────────────────────────────────────────────────────
    if PLAYBOOK.exists():
        with st.expander("📖 Playbook de contacto (emails, guion de llamada, objeciones)"):
            st.markdown(PLAYBOOK.read_text(encoding="utf-8"))


# ─── Base de Datos ─────────────────────────────────────────────────────────────
elif page == "📊 Base de Datos":
    import pandas as pd
    from agents.specialists.prospector import CRM, ESTADOS, ESTADO_COLORS
    import json as _json

    st.title("📊 Base de Datos de Negocios")
    st.caption("Todos los prospectos analizados con ProspectorIA. Filtra, edita y exporta.")

    crm_db = CRM()
    stats_db = crm_db.stats()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total negocios", stats_db["total"])
    k2.metric("Alta oportunidad 🔴", stats_db["alta_oportunidad"])
    k3.metric("Clientes 🟢", stats_db["por_estado"].get("cliente", 0))
    k4.metric("Propuestas 🟣", stats_db["por_estado"].get("propuesta", 0))
    k5.metric("Reuniones 🟠", stats_db["por_estado"].get("reunion", 0))

    st.divider()

    # ── Filtros ───────────────────────────────────────────────────────────────
    with st.expander("🔎 Filtros", expanded=True):
        fc1, fc2, fc3, fc4 = st.columns(4)
        f_nombre = fc1.text_input("Buscar nombre", placeholder="Ej: Dental", key="db_f_nombre")
        f_ciudad = fc2.text_input("Ciudad", placeholder="Ej: Barcelona", key="db_f_ciudad")
        f_estado = fc3.selectbox(
            "Estado", ["todos"] + ESTADOS, key="db_f_estado",
            format_func=lambda e: "Todos" if e == "todos" else f"{ESTADO_COLORS.get(e,'')} {e.upper()}",
        )
        f_opt = fc4.selectbox("Oportunidad", ["todas", "alta", "media", "baja"], key="db_f_opt")

    rows_db = crm_db.listar(
        ciudad=f_ciudad or None,
        estado=f_estado if f_estado != "todos" else None,
        oportunidad=f_opt if f_opt != "todas" else None,
    )

    # Filtro por nombre (en memoria)
    if f_nombre:
        rows_db = [r for r in rows_db if f_nombre.lower() in (r["nombre"] or "").lower()]

    if not rows_db:
        st.info("No hay negocios que coincidan con los filtros.", icon="ℹ️")
    else:
        COLOR_OPT_DB = {"alta": "🔴", "media": "🟡", "baja": "🟢"}

        st.caption(f"{len(rows_db)} negocio{'s' if len(rows_db) != 1 else ''} encontrado{'s' if len(rows_db) != 1 else ''}")

        # ── Tabla resumen ──────────────────────────────────────────────────
        df_db = pd.DataFrame([{
            "Win %": r.get("win_probability") or 0,
            "Estado": ESTADO_COLORS.get(r["estado"], "") + " " + (r["estado"] or "").upper(),
            "Nombre": r["nombre"],
            "Ciudad": r["ciudad"] or "—",
            "Tipo": r["tipo"] or "—",
            "Madurez": f"{r['madurez_digital']:.0f}" if r.get("madurez_digital") is not None else "—",
            "Percentil": r.get("percentil_nicho") if r.get("percentil_nicho") is not None else "—",
            "Pérdida €/mes": f"−{r['perdida_mes']:,.0f}".replace(",", ".") if r.get("perdida_mes") else "—",
            "Web": "✅" if r["tiene_web"] else "❌",
            "Rating": f"{r['rating']} ⭐" if r["rating"] else "—",
            "Tel.": r["telefono"] or "—",
            "Guardado": (r["fecha_creacion"] or "")[:10],
        } for r in rows_db])
        df_db = df_db.sort_values("Win %", ascending=False)

        st.dataframe(
            df_db, use_container_width=True, hide_index=True,
            column_config={
                "Win %": st.column_config.ProgressColumn(
                    "Win %", min_value=0, max_value=100, format="%d",
                    help="Probabilidad de cierre",
                ),
            },
        )

        # ── Exportar ───────────────────────────────────────────────────────
        csv_db = crm_db.exportar_csv()
        if csv_db:
            st.download_button(
                "⬇️ Exportar CSV completo",
                data=csv_db.encode("utf-8"),
                file_name="negocios_merakia.csv",
                mime="text/csv",
            )

        st.divider()

        # ── Detalle expandible por negocio ─────────────────────────────────
        st.markdown("#### Ver / editar detalle")

        nombres_lista = [f"{ESTADO_COLORS.get(r['estado'],'')} {r['nombre']} · {r['ciudad'] or ''}" for r in rows_db]
        sel_db_idx = st.selectbox("Selecciona un negocio", range(len(rows_db)),
                                  format_func=lambda i: nombres_lista[i], key="db_sel")
        rec = rows_db[sel_db_idx]

        col_d1, col_d2 = st.columns([2, 1])

        with col_d1:
            st.markdown(f"### {rec['nombre']}")
            st.markdown(f"**Tipo:** {rec['tipo'] or '—'} &nbsp;|&nbsp; **Ciudad:** {rec['ciudad'] or '—'}")
            if rec["web"]:
                st.markdown(f"**Web:** [{rec['web']}]({rec['web']})")
            if rec["telefono"]:
                st.markdown(f"**Teléfono:** {rec['telefono']}")
            st.markdown(f"**Rating:** {rec['rating']} ⭐ ({rec['total_resenas']} reseñas)" if rec["rating"] else "**Rating:** —")
            st.markdown(f"**Score web:** {rec['score_web']}/15 &nbsp;|&nbsp; **Score oportunidad:** {rec['score_oportunidad']}/100")

            # Métricas persuasivas
            if rec.get("win_probability") is not None or rec.get("madurez_digital") is not None:
                m1, m2, m3, m4 = st.columns(4)
                if rec.get("win_probability") is not None:
                    m1.metric("Win %", f"{rec['win_probability']}/100")
                if rec.get("madurez_digital") is not None:
                    m2.metric("Madurez digital", f"{rec['madurez_digital']:.0f}/100")
                if rec.get("percentil_nicho") is not None:
                    m3.metric("Percentil nicho", rec["percentil_nicho"])
                if rec.get("perdida_mes"):
                    m4.metric("Pérdida estimada", f"−{rec['perdida_mes']:,.0f} €/mes".replace(",", "."))

            if rec["resumen"]:
                st.info(rec["resumen"], icon="💡")

            # Desglose de pérdidas
            if rec.get("perdidas_json"):
                try:
                    perds = _json.loads(rec["perdidas_json"])
                except Exception:
                    perds = []
                if perds:
                    with st.expander(f"🩸 Dinero que pierde — desglose ({len(perds)} conceptos)"):
                        for p in perds:
                            eur_txt = f"{p.get('euros_mes', 0):,.0f}".replace(",", ".")
                            st.markdown(
                                f"🔻 **{p.get('concepto','')}** — "
                                f"<span style='color:#ef4444'>−{eur_txt} €/mes</span>"
                                f"<br><small style='color:#94a3b8'>{p.get('explicacion','')}</small>",
                                unsafe_allow_html=True,
                            )

        with col_d2:
            st.markdown("**Gestión del pipeline**")
            nuevo_estado_db = st.selectbox(
                "Estado",
                ESTADOS,
                index=ESTADOS.index(rec["estado"]) if rec["estado"] in ESTADOS else 0,
                format_func=lambda e: f"{ESTADO_COLORS.get(e,'')} {e.upper()}",
                key="db_edit_estado",
            )
            nuevas_notas_db = st.text_area("Notas", value=rec["notas"] or "", height=100, key="db_edit_notas")
            if st.button("💾 Guardar cambios", key="db_save_estado", type="primary"):
                crm_db.actualizar_estado(rec["id"], nuevo_estado_db, nuevas_notas_db)
                st.success("✅ Guardado")
                st.rerun()

        # ── Datos duros: tech stack + PageSpeed + battle card ──────────────
        dd_cols = st.columns(3)
        if rec.get("tech_stack_json"):
            try:
                tech_db = _json.loads(rec["tech_stack_json"])
            except Exception:
                tech_db = {}
            if tech_db:
                with dd_cols[0]:
                    st.markdown("**🧩 Stack**")
                    for cat, tools in tech_db.items():
                        st.caption(f"{cat}: {', '.join(tools)}")
        if rec.get("pagespeed_json"):
            try:
                ps_db = _json.loads(rec["pagespeed_json"])
            except Exception:
                ps_db = {}
            if ps_db:
                with dd_cols[1]:
                    pscore = ps_db.get("performance_score", 0)
                    pcol = "🟢" if pscore >= 90 else "🟡" if pscore >= 50 else "🔴"
                    st.markdown(f"**⚡ PageSpeed** {pcol} {pscore}/100")
                    if ps_db.get("lcp_s"):
                        st.caption(f"LCP {ps_db['lcp_s']:.1f}s · CLS {ps_db.get('cls','—')}")
        if rec.get("competitive_json"):
            try:
                comp_db = _json.loads(rec["competitive_json"])
            except Exception:
                comp_db = {}
            if comp_db and comp_db.get("battle_card"):
                with dd_cols[2]:
                    st.markdown(f"**⚔️ Puesto {comp_db.get('posicion')}/{comp_db.get('total')}**")
                    st.caption(f"Líder: {comp_db.get('lider_nombre')}")

        # ── Dolores detectados ─────────────────────────────────────────────
        if rec.get("pains_json"):
            pains_db = _json.loads(rec["pains_json"])
            if pains_db:
                st.markdown("**Dolores detectados**")
                for p in sorted(pains_db, key=lambda x: x.get("urgencia", 0), reverse=True):
                    urg = p.get("urgencia", 0)
                    color = "#ef4444" if urg >= 7 else "#f59e0b" if urg >= 4 else "#6b7280"
                    st.markdown(
                        f'<span style="color:{color};font-weight:600">[{urg}/10]</span> '
                        f'**{p.get("categoria","").replace("_"," ").title()}** — {p.get("descripcion","")}',
                        unsafe_allow_html=True,
                    )

        # ── Email generado ─────────────────────────────────────────────────
        if rec.get("email_cuerpo"):
            with st.expander("✉️ Email generado"):
                st.markdown(f"**Asunto:** {rec.get('email_asunto','')}")
                st.text_area("Cuerpo", value=rec["email_cuerpo"], height=200,
                             key="db_email_body", disabled=True)

        # ── WhatsApp / Script ──────────────────────────────────────────────
        col_wa, col_sc = st.columns(2)
        if rec.get("whatsapp_mensaje"):
            with col_wa.expander("💬 WhatsApp"):
                st.text_area("Mensaje", value=rec["whatsapp_mensaje"], height=150,
                             key="db_wa", disabled=True)
        if rec.get("script_llamada"):
            with col_sc.expander("📞 Script llamada"):
                st.text_area("Script", value=rec["script_llamada"], height=150,
                             key="db_script", disabled=True)
